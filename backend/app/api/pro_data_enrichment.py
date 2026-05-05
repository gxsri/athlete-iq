"""
============================================================================
专业运动员数据填充 — 基于真实文献的模拟数据
为15名期刊运动员填充：体能测试、基线值、比赛日程、伤病记录
============================================================================
References:
- VO2max: 精英男单 58-65, 女单 50-55 mL/kg/min (Faude et al., 2007)
- CMJ: 精英男 45-55cm, 女 35-42cm (Ooi et al., 2009)
- 1RM squat: 精英男 1.5-1.8xBW, 女 1.2-1.4xBW (Cronin et al., 2005)
- Sprint 30m: 精英男 4.0-4.3s, 女 4.3-4.6s (Walklate et al., 2009)
- Bench press 1RM: 精英男 0.9-1.1xBW, 女 0.5-0.7xBW
- Resting HR: 精英 48-55, 一级 52-60, 二级 56-65 bpm
- HRV (LnRMSSD): 精英 65-80, 一级 55-70, 二级 45-60 ms
- Competition: 精英 8-12 tournaments/year, 一级 5-8, 二级 3-5
============================================================================
"""
import random
from datetime import date, timedelta
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, logger
from app.models.athlete import (
    Athlete, PerformanceTest, AthleteBaseline, Competition, InjuryRecord, InjuryRestriction,
)

router = APIRouter(prefix="/api/pro-data", tags=["专业数据填充"])

# =========================================================================
# Level-specific performance norms (literature-based)
# =========================================================================

PERF_NORMS = {
    "elite": {
        "MS": {"vo2max": (58, 65), "cmj": (48, 58), "squat_1rm": (130, 165), "bench_1rm": (75, 100), "deadlift_1rm": (140, 180), "sprint_30m": (4.0, 4.25), "standing_jump": (240, 275)},
        "WS": {"vo2max": (50, 57), "cmj": (35, 44), "squat_1rm": (85, 110), "bench_1rm": (40, 60),  "deadlift_1rm": (90, 120),  "sprint_30m": (4.3, 4.55), "standing_jump": (200, 235)},
        "MD": {"vo2max": (56, 63), "cmj": (50, 60), "squat_1rm": (120, 150), "bench_1rm": (70, 95),  "deadlift_1rm": (130, 170), "sprint_30m": (4.05, 4.30), "standing_jump": (245, 280)},
        "WD": {"vo2max": (48, 55), "cmj": (36, 45), "squat_1rm": (80, 105),  "bench_1rm": (38, 55),  "deadlift_1rm": (85, 115),  "sprint_30m": (4.35, 4.60), "standing_jump": (195, 230)},
        "XD": {"vo2max": (54, 61), "cmj": (45, 55), "squat_1rm": (110, 140), "bench_1rm": (65, 88),  "deadlift_1rm": (120, 155), "sprint_30m": (4.1, 4.35), "standing_jump": (230, 265)},
    },
    "first_grade": {
        "MS": {"vo2max": (52, 58), "cmj": (42, 50), "squat_1rm": (100, 130), "bench_1rm": (60, 80), "deadlift_1rm": (110, 140), "sprint_30m": (4.2, 4.5), "standing_jump": (220, 255)},
        "WS": {"vo2max": (44, 51), "cmj": (30, 38), "squat_1rm": (65, 90),  "bench_1rm": (32, 50),  "deadlift_1rm": (70, 100),  "sprint_30m": (4.5, 4.8), "standing_jump": (175, 215)},
        "MD": {"vo2max": (50, 56), "cmj": (44, 52), "squat_1rm": (95, 120),  "bench_1rm": (55, 78),  "deadlift_1rm": (105, 135), "sprint_30m": (4.25, 4.55), "standing_jump": (225, 260)},
        "WD": {"vo2max": (42, 49), "cmj": (31, 39), "squat_1rm": (60, 85),   "bench_1rm": (30, 45),  "deadlift_1rm": (65, 95),   "sprint_30m": (4.55, 4.85), "standing_jump": (170, 210)},
        "XD": {"vo2max": (48, 55), "cmj": (40, 48), "squat_1rm": (90, 115),  "bench_1rm": (50, 72),  "deadlift_1rm": (100, 130), "sprint_30m": (4.3, 4.6), "standing_jump": (210, 245)},
    },
    "second_grade": {
        "MS": {"vo2max": (46, 52), "cmj": (35, 44), "squat_1rm": (80, 105),  "bench_1rm": (50, 68),  "deadlift_1rm": (90, 115),  "sprint_30m": (4.4, 4.8), "standing_jump": (200, 235)},
        "WS": {"vo2max": (38, 45), "cmj": (26, 33), "squat_1rm": (50, 72),   "bench_1rm": (25, 40),  "deadlift_1rm": (55, 80),   "sprint_30m": (4.7, 5.1), "standing_jump": (155, 190)},
        "MD": {"vo2max": (44, 50), "cmj": (37, 46), "squat_1rm": (75, 100),  "bench_1rm": (45, 62),  "deadlift_1rm": (85, 110),  "sprint_30m": (4.45, 4.85), "standing_jump": (205, 240)},
        "WD": {"vo2max": (36, 43), "cmj": (27, 34), "squat_1rm": (45, 68),   "bench_1rm": (22, 36),  "deadlift_1rm": (50, 75),   "sprint_30m": (4.75, 5.15), "standing_jump": (150, 185)},
        "XD": {"vo2max": (42, 49), "cmj": (34, 43), "squat_1rm": (72, 98),   "bench_1rm": (42, 58),  "deadlift_1rm": (80, 108),  "sprint_30m": (4.5, 4.9), "standing_jump": (195, 230)},
    },
}

# Baseline norms (resting HR, HRV, body weight approximate)
BASELINE_NORMS = {
    "elite":        {"hr_rest": (48, 55), "hrv_lnrmssd": (65, 82), "body_weight_m": (68, 78), "body_weight_f": (55, 65)},
    "first_grade":  {"hr_rest": (52, 60), "hrv_lnrmssd": (55, 70), "body_weight_m": (65, 80), "body_weight_f": (52, 68)},
    "second_grade": {"hr_rest": (56, 65), "hrv_lnrmssd": (42, 58), "body_weight_m": (62, 82), "body_weight_f": (50, 70)},
}

# Competition templates (realistic tournament names + dates)
COMPETITION_TEMPLATES = [
    {"name": "全国羽毛球锦标赛", "location": "北京国家体育馆"},
    {"name": "中国羽毛球公开赛", "location": "常州奥体中心"},
    {"name": "全国大学生羽毛球赛", "location": "武汉体育学院"},
    {"name": "省级羽毛球积分赛·春季站", "location": "广州天河体育中心"},
    {"name": "省级羽毛球积分赛·秋季站", "location": "成都高新体育中心"},
    {"name": "全国羽毛球冠军赛", "location": "福州海峡奥体中心"},
    {"name": "亚洲羽毛球锦标赛选拔赛", "location": "上海东方体育中心"},
    {"name": "市级羽毛球公开赛", "location": "杭州奥体中心"},
    {"name": "高校羽毛球联赛", "location": "南京体育学院"},
    {"name": "全国青少年羽毛球锦标赛", "location": "长沙贺龙体育馆"},
    {"name": "羽毛球俱乐部联赛·决赛", "location": "深圳湾体育中心"},
    {"name": "国际羽毛球挑战赛", "location": "厦门体育中心"},
]

# Injury templates with realistic details
INJURY_TEMPLATES = [
    {"diagnosis": "右肩肩袖肌腱炎 (Grade 1)", "body_part": "右肩", "severity": "轻度", "recovery_weeks": 4,
     "restrictions": [{"type": "禁止动作", "detail": "暂停杀球和过顶击球训练", "pattern": "杀球|过顶"},
                      {"type": "负荷限制", "detail": "上肢负重不超过5kg", "pattern": "卧推|推举"}]},
    {"diagnosis": "左膝髌腱炎 (Jumper's Knee)", "body_part": "左膝", "severity": "中度", "recovery_weeks": 8,
     "restrictions": [{"type": "禁止动作", "detail": "禁止跳跃类训练", "pattern": "跳箱|跳跃"},
                      {"type": "负荷限制", "detail": "下肢训练减量50%", "pattern": "深蹲|硬拉"}]},
    {"diagnosis": "右踝关节扭伤 (Grade 2 ATFL)", "body_part": "右踝", "severity": "中度", "recovery_weeks": 6,
     "restrictions": [{"type": "禁止动作", "detail": "禁止多方向移动训练", "pattern": "折返|步法"}]},
    {"diagnosis": "腰椎间盘突出 (L4-L5, 轻度)", "body_part": "下背", "severity": "中度", "recovery_weeks": 10,
     "restrictions": [{"type": "禁止动作", "detail": "禁止脊柱屈曲负荷动作", "pattern": "硬拉|划船|高翻"}]},
    {"diagnosis": "右肘外上髁炎 (网球肘)", "body_part": "右肘", "severity": "轻度", "recovery_weeks": 3,
     "restrictions": [{"type": "负荷限制", "detail": "上肢拉类动作减量", "pattern": "引体|划船"}]},
    {"diagnosis": "左大腿股二头肌拉伤 (Grade 1)", "body_part": "左大腿", "severity": "轻度", "recovery_weeks": 3,
     "restrictions": [{"type": "负荷限制", "detail": "冲刺速度限制70%", "pattern": "冲刺|折返"}]},
    {"diagnosis": "右肩盂唇撕裂 (SLAP Grade 2)", "body_part": "右肩", "severity": "重度", "recovery_weeks": 16,
     "restrictions": [{"type": "禁止动作", "detail": "严格禁止所有上肢过顶动作", "pattern": "杀球|过顶|发球"},
                      {"type": "负荷限制", "detail": "仅允许被动ROM训练", "pattern": ".*"}]},
]


def _r(rng: random.Random, lo, hi):
    return round(rng.uniform(lo, hi), 1)


@router.post("/enrich-all")
async def enrich_all_athletes(
    tests_per_athlete: int = Query(4, ge=2, le=8, description="每位运动员的体能测试次数"),
    competitions_per_athlete: int = Query(3, ge=1, le=8),
    injury_chance_elite: float = Query(0.25),
    injury_chance_first: float = Query(0.35),
    injury_chance_second: float = Query(0.55),
    db: AsyncSession = Depends(get_db),
):
    """
    为所有现有运动员填充专业数据：体能测试、基线值、比赛日程、伤病记录。

    填充逻辑基于真实文献参考值，按照运动员的项目(MS/WS/MD/WD/XD)和等级(elite/first/second)差异化生成。
    """
    result = await db.execute(select(Athlete))
    athletes = result.scalars().all()

    if not athletes:
        return {"status": "error", "message": "没有运动员。请先运行 /api/journal/generate-all"}

    today = date.today()
    stats = {"performance_tests": 0, "baselines": 0, "competitions": 0, "injuries": 0}

    for athlete in athletes:
        # Determine discipline + level from name convention
        name = athlete.name
        discipline = athlete.position_or_event or "MS"
        level = "elite"
        if "健将" in name:
            level = "elite"
        elif "一级" in name:
            level = "first_grade"
        elif "二级" in name:
            level = "second_grade"

        norms = PERF_NORMS.get(level, {}).get(discipline, PERF_NORMS["first_grade"]["MS"])
        base_norms = BASELINE_NORMS.get(level, BASELINE_NORMS["first_grade"])
        gender = athlete.gender
        rng = random.Random(hash(f"{athlete.id}_enrich"))

        # ===== 1. Performance Tests =====
        existing_tests = await db.execute(
            select(PerformanceTest).where(PerformanceTest.athlete_id == athlete.id)
        )
        existing_count = len(existing_tests.scalars().all())

        if existing_count < tests_per_athlete:
            # Generate tests spread over past months
            for i in range(tests_per_athlete - existing_count):
                test_date = today - timedelta(days=30 * (i + 1) + rng.randint(0, 14))
                # Slight progression over time (earlier tests = slightly lower values)
                progression = 0.92 + (i * 0.03)  # 92% → 98% of norm

                bw = _r(rng, *base_norms["body_weight_m" if gender == "男" else "body_weight_f"])
                db.add(PerformanceTest(
                    athlete_id=athlete.id, test_date=test_date,
                    squat_1rm_kg=_r(rng, *norms["squat_1rm"]) * progression,
                    bench_press_1rm_kg=_r(rng, *norms["bench_1rm"]) * progression,
                    deadlift_1rm_kg=_r(rng, *norms["deadlift_1rm"]) * progression,
                    cmj_height_cm=_r(rng, *norms["cmj"]) * progression,
                    sprint_30m_sec=_r(rng, *norms["sprint_30m"]) * (2 - progression),
                    standing_long_jump_cm=_r(rng, *norms["standing_jump"]) * progression,
                    vo2max_ml_kg_min=_r(rng, *norms["vo2max"]) * progression,
                    test_protocol="标准化体能测试 (NSCA规范)",
                    notes=f"周期体能评估 #{i+1} — {level} {discipline}",
                ))
                stats["performance_tests"] += 1

        # ===== 2. Baseline Values =====
        existing_bl = await db.execute(
            select(AthleteBaseline).where(AthleteBaseline.athlete_id == athlete.id)
        )
        bl_count = len(existing_bl.scalars().all())
        if bl_count == 0:
            bls = [
                ("morning_heart_rate", _r(rng, *base_norms["hr_rest"]), 3.0),
                ("hrv_lnrmssd", _r(rng, *base_norms["hrv_lnrmssd"]), 5.0),
                ("squat_1rm_kg", _r(rng, *norms["squat_1rm"]), 5.0),
                ("bench_press_1rm_kg", _r(rng, *norms["bench_1rm"]), 3.0),
                ("cmj_height_cm", _r(rng, *norms["cmj"]), 2.0),
                ("vo2max_ml_kg_min", _r(rng, *norms["vo2max"]), 2.0),
            ]
            for metric_name, value, te in bls:
                db.add(AthleteBaseline(
                    athlete_id=athlete.id, metric_name=metric_name,
                    baseline_value=value, typical_error=te,
                    swc=round(value * 0.02, 1),
                    established_at=today - timedelta(days=90),
                    notes=f"{level} {discipline} 基线 — 依据体能测试均值",
                ))
                stats["baselines"] += 1

        # ===== 3. Competition Schedule =====
        existing_comps = await db.execute(
            select(Competition).where(Competition.athlete_id == athlete.id)
        )
        comp_count = len(existing_comps.scalars().all())
        need_comps = competitions_per_athlete - comp_count

        # Elite players have more tournaments
        if "健将" in name:
            need_comps = max(need_comps, 5)
        elif "一级" in name:
            need_comps = max(need_comps, 3)

        for i in range(need_comps):
            # Spread across next 6 months
            comp_offset = rng.randint(7, 180)
            comp_date = today + timedelta(days=comp_offset)
            tmpl = COMPETITION_TEMPLATES[i % len(COMPETITION_TEMPLATES)]
            db.add(Competition(
                athlete_id=athlete.id, name=tmpl["name"],
                competition_date=comp_date, location=tmpl["location"],
                notes=f"目标赛事 — {tmpl['name']}",
            ))
            stats["competitions"] += 1

        # ===== 4. Injury Records =====
        existing_injuries = await db.execute(
            select(InjuryRecord).where(InjuryRecord.athlete_id == athlete.id)
        )
        inj_count = len(existing_injuries.scalars().all())

        injury_chance = (
            injury_chance_elite if level == "elite" else
            injury_chance_first if level == "first_grade" else
            injury_chance_second
        )

        if inj_count == 0 and rng.random() < injury_chance:
            tmpl = INJURY_TEMPLATES[rng.randint(0, len(INJURY_TEMPLATES) - 1)]
            injury_date = today - timedelta(days=rng.randint(30, 365))
            is_recovered = injury_date < today - timedelta(days=tmpl["recovery_weeks"] * 7)

            injury = InjuryRecord(
                athlete_id=athlete.id,
                diagnosis=tmpl["diagnosis"],
                injury_date=injury_date,
                expected_recovery_weeks=tmpl["recovery_weeks"],
                actual_return_date=(injury_date + timedelta(weeks=tmpl["recovery_weeks"])) if is_recovered else None,
                status="已恢复" if is_recovered else "康复中",
                body_part=tmpl["body_part"],
                severity=tmpl["severity"],
                notes=f"训练中发生 — {tmpl['diagnosis']}",
            )
            db.add(injury)
            await db.flush()

            for rest in tmpl["restrictions"]:
                db.add(InjuryRestriction(
                    injury_record_id=injury.id,
                    restriction_type=rest["type"],
                    restriction_detail=rest["detail"],
                    exercise_name_pattern=rest["pattern"],
                    is_active=not is_recovered,
                ))
            stats["injuries"] += 1

    await db.commit()
    logger.info(f"Enriched {len(athletes)} athletes: {stats}")

    return {
        "status": "success",
        "athletes_processed": len(athletes),
        **stats,
        "message": f"已为 {len(athletes)} 名运动员填充专业数据：{stats['performance_tests']} 条体能测试、{stats['baselines']} 个基线、{stats['competitions']} 场比赛、{stats['injuries']} 条伤病记录",
        "norms_reference": {
            "vo2max_elite_ms": "58-65 mL/kg/min (Faude et al., 2007)",
            "cmj_elite_ms": "48-58cm (Ooi et al., 2009)",
            "sprint_30m_elite_ms": "4.0-4.25s (Walklate et al., 2009)",
            "hrv_elite": "LnRMSSD 65-82ms",
            "resting_hr_elite": "48-55 bpm",
        },
    }
