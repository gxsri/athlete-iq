"""
Seed comprehensive test data for AthleteIQ dashboard testing.
Creates athletes, training logs, wellness data, daily metrics, plans, and more.
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))

import random, uuid, math
from datetime import date, datetime, timedelta
from sqlalchemy import select, delete
from app.database import async_session, engine, Base
from app.models.athlete import (
    Athlete, TrainingLog, WellnessQuestionnaire, DailyMetric, ComputedMetric,
    ExerciseLibrary, PlannedSession, PlannedExercise, ExerciseLog,
    TrainingTemplate, TrainingAssignment, PeriodizationTemplate,
    AlertEvent, AlertConfig, NutritionLog, MentalLog,
    InjuryRecord, Competition, DailyReadiness, RecoverySuggestion,
)

random.seed(42)

ATHLETES = [
    {"name": "男单_健将", "sport": "羽毛球", "gender": "男", "date_of_birth": date(2000, 3, 15), "training_years": 8, "athlete_type": "test", "position_role": "男子单打", "hand_dominance": "右", "dominant_foot": "右"},
    {"name": "张伟_主力", "sport": "羽毛球", "gender": "男", "date_of_birth": date(2001, 7, 22), "training_years": 6, "athlete_type": "test", "position_role": "男子双打"},
    {"name": "李娜_核心", "sport": "羽毛球", "gender": "女", "date_of_birth": date(2002, 11, 8), "training_years": 5, "athlete_type": "test", "position_role": "女子单打"},
    {"name": "王强_新秀", "sport": "羽毛球", "gender": "男", "date_of_birth": date(2004, 1, 30), "training_years": 3, "athlete_type": "test", "position_role": "男子单打"},
    {"name": "刘洋_老将", "sport": "羽毛球", "gender": "男", "date_of_birth": date(1998, 5, 18), "training_years": 12, "athlete_type": "test", "position_role": "混合双打"},
    {"name": "陈静_稳定", "sport": "羽毛球", "gender": "女", "date_of_birth": date(2003, 9, 2), "training_years": 4, "athlete_type": "test", "position_role": "女子双打"},
    {"name": "赵磊_冲击", "sport": "篮球", "gender": "男", "date_of_birth": date(2000, 12, 10), "training_years": 7, "athlete_type": "test", "position_role": "前锋"},
    {"name": "孙悦_射手", "sport": "篮球", "gender": "女", "date_of_birth": date(2002, 4, 25), "training_years": 5, "athlete_type": "test", "position_role": "后卫"},
    {"name": "周杰_耐力", "sport": "游泳", "gender": "男", "date_of_birth": date(2001, 6, 14), "training_years": 9, "athlete_type": "test", "position_role": "自由泳"},
    {"name": "吴敏_速度", "sport": "田径", "gender": "女", "date_of_birth": date(2003, 2, 28), "training_years": 4, "athlete_type": "test", "position_role": "短跑"},
    {"name": "郑爽_全面", "sport": "足球", "gender": "男", "date_of_birth": date(1999, 8, 5), "training_years": 10, "athlete_type": "test", "position_role": "中场"},
    {"name": "钱峰_技巧", "sport": "排球", "gender": "男", "date_of_birth": date(2002, 10, 20), "training_years": 5, "athlete_type": "test", "position_role": "主攻"},
]

TRAINING_TYPES = ["力量", "耐力", "速度", "技战术", "柔韧", "混合"]
CYCLE_PHASES = ["准备期", "比赛期", "过渡期"]

# Risk profiles per athlete (higher = more risk)
RISK_PROFILES = {
    "男单_健将": {"base_load": 85, "fatigue_factor": 0.9, "injury_chance": 0.15},
    "张伟_主力": {"base_load": 80, "fatigue_factor": 0.8, "injury_chance": 0.12},
    "李娜_核心": {"base_load": 75, "fatigue_factor": 0.7, "injury_chance": 0.08},
    "王强_新秀": {"base_load": 90, "fatigue_factor": 1.0, "injury_chance": 0.25},  # HIGH RISK
    "刘洋_老将": {"base_load": 70, "fatigue_factor": 0.6, "injury_chance": 0.10},
    "陈静_稳定": {"base_load": 60, "fatigue_factor": 0.5, "injury_chance": 0.05},
    "赵磊_冲击": {"base_load": 88, "fatigue_factor": 0.9, "injury_chance": 0.20},  # HIGH RISK
    "孙悦_射手": {"base_load": 72, "fatigue_factor": 0.7, "injury_chance": 0.10},
    "周杰_耐力": {"base_load": 95, "fatigue_factor": 0.95, "injury_chance": 0.18}, # HIGH RISK
    "吴敏_速度": {"base_load": 78, "fatigue_factor": 0.8, "injury_chance": 0.14},
    "郑爽_全面": {"base_load": 82, "fatigue_factor": 0.75, "injury_chance": 0.11},
    "钱峰_技巧": {"base_load": 65, "fatigue_factor": 0.55, "injury_chance": 0.06},
}


def seeded_random(seed_base, *extra):
    r = random.Random(str(seed_base) + str(extra))
    return r


async def seed():
    async with async_session() as db:
        print("Clearing existing test data...")

        # Delete in correct order (children first)
        await db.execute(delete(ExerciseLog))
        await db.execute(delete(PlannedExercise))
        await db.execute(delete(PlannedSession))
        await db.execute(delete(TrainingAssignment))
        await db.execute(delete(AlertEvent))
        await db.execute(delete(AlertConfig))
        await db.execute(delete(ComputedMetric))
        await db.execute(delete(DailyMetric))
        await db.execute(delete(WellnessQuestionnaire))
        await db.execute(delete(TrainingLog))
        await db.execute(delete(NutritionLog))
        await db.execute(delete(MentalLog))
        await db.execute(delete(DailyReadiness))
        await db.execute(delete(RecoverySuggestion))
        await db.execute(delete(Competition))
        await db.execute(delete(InjuryRecord))

        # Delete test athletes
        existing = (await db.execute(select(Athlete).where(Athlete.athlete_type == "test"))).scalars().all()
        for a in existing:
            await db.delete(a)
        await db.flush()
        print("Existing data cleared.")

        # Create athletes
        print("Creating 12 test athletes...")
        athlete_objs = {}
        for a_data in ATHLETES:
            a = Athlete(**a_data)
            db.add(a)
            await db.flush()
            athlete_objs[a.name] = a

        # Seed exercises
        print("Seeding exercise library...")
        EXERCISES = [
            {"name": "深蹲", "category": "力量", "category_l1": "力量", "category_l2": "下肢", "target_muscles": ["股四头肌","臀大肌"], "preset_params": {"sets": 4, "reps": 8, "rest_seconds": 90}},
            {"name": "卧推", "category": "力量", "category_l1": "力量", "category_l2": "上肢", "target_muscles": ["胸大肌","三角肌前束"], "preset_params": {"sets": 4, "reps": 8, "rest_seconds": 90}},
            {"name": "硬拉", "category": "力量", "category_l1": "力量", "category_l2": "全身", "target_muscles": ["竖脊肌","臀大肌"], "preset_params": {"sets": 3, "reps": 6, "rest_seconds": 120}},
            {"name": "弓步蹲", "category": "力量", "category_l1": "力量", "category_l2": "下肢", "target_muscles": ["股四头肌","臀大肌"], "preset_params": {"sets": 3, "reps": 10, "rest_seconds": 60}},
            {"name": "引体向上", "category": "力量", "category_l1": "力量", "category_l2": "上肢", "target_muscles": ["背阔肌","肱二头肌"], "preset_params": {"sets": 3, "reps": 8, "rest_seconds": 60}},
            {"name": "肩部推举", "category": "力量", "category_l1": "力量", "category_l2": "肩部", "target_muscles": ["三角肌"], "preset_params": {"sets": 3, "reps": 10, "rest_seconds": 60}},
            {"name": "400m间歇跑", "category": "耐力", "category_l1": "耐力", "category_l2": "心肺", "target_muscles": ["心肺"], "preset_params": {"sets": 8, "reps": 1, "rest_seconds": 90}},
            {"name": "跳绳双摇", "category": "速度", "category_l1": "速度", "category_l2": "敏捷", "target_muscles": ["小腿","心肺"], "preset_params": {"sets": 5, "reps": 30, "rest_seconds": 45}},
            {"name": "杀球训练", "category": "技战术", "category_l1": "技战术", "category_l2": "专项", "target_muscles": ["肩部","核心"], "preset_params": {"sets": 5, "reps": 20, "rest_seconds": 30}},
            {"name": "平板支撑", "category": "柔韧", "category_l1": "柔韧", "category_l2": "核心", "target_muscles": ["腹直肌"], "preset_params": {"sets": 3, "reps": 1, "rest_seconds": 30}},
            {"name": "波比跳", "category": "混合", "category_l1": "混合", "category_l2": "全身", "target_muscles": ["全身"], "preset_params": {"sets": 3, "reps": 15, "rest_seconds": 45}},
            {"name": "拉伸放松", "category": "柔韧", "category_l1": "柔韧", "category_l2": "恢复", "target_muscles": ["全身"], "preset_params": {"sets": 1, "reps": 1, "rest_seconds": 0}},
        ]
        exercise_objs = []
        for ex_data in EXERCISES:
            ex = ExerciseLibrary(**ex_data, coach_id=None)
            db.add(ex)
            await db.flush()
            exercise_objs.append(ex)

        # Seed templates
        print("Seeding templates...")
        templates = []
        for i in range(6):
            tmpl = TrainingTemplate(
                name=f"模板{i+1}: {['基础力量','专项耐力','速度爆发','技术打磨','恢复调整','比赛模拟'][i]}",
                type=["daily","weekly","periodized"][i % 3],
                sport="羽毛球",
                intensity_zone=["低","中","高","极高"][i % 4],
                target_focus=[["力量"],["耐力"],["速度"],["技战术"]][i % 4],
                is_public=True,
                content={"target_load": [50, 65, 80, 60, 30, 90][i], "exercises_count": [4, 6, 3, 5, 2, 7][i]},
                description=f"自动生成的测试模板 {i+1}",
            )
            db.add(tmpl)
            await db.flush()
            templates.append(tmpl)

        await db.flush()

        # Generate 90 days of data per athlete
        print("Generating 90 days of training data per athlete...")
        today = date.today()
        start_date = today - timedelta(days=90)
        end_date = today + timedelta(days=7)

        total_logs = 0
        total_wellness = 0
        total_metrics = 0
        total_alerts = 0
        total_plans = 0

        for name, athlete in athlete_objs.items():
            profile = RISK_PROFILES[name]
            base_load = profile["base_load"]
            ff = profile["fatigue_factor"]
            ic = profile["injury_chance"]
            rng = seeded_random(athlete.id, "main")

            current = start_date
            while current <= end_date:
                days_offset = (current - start_date).days
                weekday = current.weekday()
                is_weekend = weekday >= 5
                is_rest_day = is_weekend and rng.random() < 0.3

                # Determine training load
                if is_rest_day or rng.random() < 0.05:  # 5% random rest
                    training_load = 0
                else:
                    # Base load with progressive overload (peak mid-cycle)
                    cycle_pos = (days_offset % 28) / 28.0
                    cycle_factor = 1.0 + 0.15 * math.sin(cycle_pos * math.pi)
                    training_load = base_load * cycle_factor * rng.uniform(0.7, 1.3)
                    training_load = max(0, min(100, training_load))
                    if is_weekend:
                        training_load *= 0.6

                # Fatigue: accumulates with load, decays on rest
                fatigue = training_load * 0.8 * ff + rng.uniform(0, 8)
                injury_risk = training_load * 0.5 + fatigue * 0.3 + rng.uniform(0, 5)
                sleep_quality = max(3.0, min(7.0, 6.5 - fatigue * 0.25 + rng.uniform(-0.5, 0.5)))

                # Badminton specific
                smash_today = int(training_load * 1.5 + rng.uniform(-10, 10)) if training_load > 0 else 0
                smash_7d_avg = smash_today * rng.uniform(0.7, 1.3) + 5
                ext_rotation = rng.uniform(0.5, 0.95)
                arm_pain = max(0, min(10, int(fatigue * 0.08 + rng.uniform(-1, 2))))
                impacts = int(training_load * 6 + rng.uniform(-30, 30))
                jump_q = max(1, min(10, int(8 - fatigue * 0.05 + rng.uniform(-1, 1))))
                quad_ham = rng.uniform(0.55, 1.0)
                footwork = max(1, min(10, int(7 - fatigue * 0.04 + rng.uniform(-1, 1))))
                leg_pain = max(0, min(10, int(fatigue * 0.06 + rng.uniform(-1, 1))))
                reaction = int(220 + fatigue * 1.5 + rng.uniform(-15, 15))
                knee_history = rng.random() < 0.15

                shoulder_overuse = min(100, smash_7d_avg * 0.7 + (1 - ext_rotation) * 60 + arm_pain * 5 + rng.uniform(-5, 5))
                shoulder_acute = min(100, smash_today * 1.2 + (1 - ext_rotation) * 40 + rng.uniform(-5, 10))
                knee_overuse = min(100, impacts * 0.4 + (1 - jump_q) * 15 + (1 - quad_ham) * 50 + leg_pain * 6 + rng.uniform(-3, 3))
                knee_acute = min(100, impacts * 0.5 + (1 - jump_q) * 20 + rng.uniform(-5, 5))

                if training_load > 0:
                    rpe_val = max(1, min(10, int(training_load / 10) + rng.randint(0, 2)))
                    duration = max(20, min(180, training_load * 1.3 + rng.uniform(-10, 10)))
                    session_load = round(duration * rpe_val, 1)
                    cycle_phase = CYCLE_PHASES[(days_offset // 30) % 3]

                    log = TrainingLog(
                        athlete_id=athlete.id, training_date=current,
                        duration_minutes=round(duration, 1), rpe=rpe_val,
                        training_type=TRAINING_TYPES[weekday % 6],
                        session_load=session_load, cycle_phase=cycle_phase,
                        description=f"测试数据 - {TRAINING_TYPES[weekday % 6]}训练",
                        source="auto_generated", tags=["test_data"],
                    )
                    db.add(log)
                    total_logs += 1

                # DailyMetric
                dm = DailyMetric(
                    athlete_id=athlete.id, metric_date=current,
                    training_load=round(training_load, 1),
                    injury_risk=round(injury_risk, 1),
                    fatigue=round(fatigue, 1),
                    sleep_quality=round(sleep_quality, 1),
                    rpe=max(1, min(10, int(training_load / 10))) if training_load > 0 else None,
                    energy_level=max(1, min(10, 8 - int(fatigue / 15) + rng.randint(-1, 1))),
                    muscle_soreness={"shoulder": min(10, int(arm_pain + rng.uniform(-1, 1))),
                                      "quad": min(10, int(fatigue / 12 + rng.uniform(-1, 1))),
                                      "calf": min(10, int(fatigue / 15 + rng.uniform(-1, 1)))},
                    completion_rate=round(rng.uniform(70, 115), 1) if training_load > 0 else None,
                    smash_count_today=smash_today, smash_7d_avg=smash_7d_avg,
                    overhead_week_total=int(smash_7d_avg * 7 * rng.uniform(1.0, 1.4)),
                    max_smash_30d=int(max(smash_today * rng.uniform(0.8, 1.3), smash_today)),
                    external_rotation_ratio=ext_rotation, arm_pain_vas=arm_pain,
                    total_impacts_7d=impacts, jump_landing_quality=jump_q,
                    quad_hamstring_ratio=quad_ham, footwork_score=footwork,
                    leg_pain_vas=leg_pain, reaction_time_ms=reaction,
                    has_knee_pain_history=knee_history,
                    shoulder_overuse_risk=round(shoulder_overuse, 1),
                    shoulder_acute_risk=round(shoulder_acute, 1),
                    knee_overuse_risk=round(knee_overuse, 1),
                    knee_acute_risk=round(knee_acute, 1),
                )
                db.add(dm)
                total_metrics += 1

                # Wellness every 7 days
                if days_offset % 7 == 0:
                    mhr = int(52 + training_load * 0.12 + rng.uniform(-3, 3))
                    hrv_val = round(max(30, min(90, 70 - training_load * 0.25 + rng.uniform(-5, 5))), 2)
                    w = WellnessQuestionnaire(
                        athlete_id=athlete.id, record_date=current,
                        morning_heart_rate=mhr, hrv_lnrmssd=hrv_val,
                        sleep_duration_hours=round(max(5, min(10, 7.5 - fatigue * 0.2 + rng.uniform(-1, 1))), 1),
                        sleep_quality=int(max(1, min(5, sleep_quality / 7 * 5))),
                        fatigue_score=int(max(1, min(5, fatigue / 20))),
                        muscle_soreness=int(max(1, min(5, training_load / 20))),
                        stress_score=int(max(1, min(5, fatigue / 20 + rng.randint(0, 2)))),
                        mood_score=int(max(1, min(5, 4 - int(fatigue / 30)))),
                        source="auto_generated",
                    )
                    db.add(w)
                    total_wellness += 1

                # Alerts for high-risk days
                if training_load > 0 and (shoulder_overuse > 70 or knee_overuse > 70 or injury_risk > 65):
                    if rng.random() < ic * 2:
                        alert_type = "shoulder" if shoulder_overuse > 70 else "knee" if knee_overuse > 70 else "general"
                        db.add(AlertEvent(
                            athlete_id=athlete.id, alert_date=current,
                            alert_type=f"{alert_type}_risk",
                            severity="高" if (shoulder_overuse > 80 or knee_overuse > 80) else "中",
                            alert_source="data_generator",
                            current_value=f"肩:{shoulder_overuse:.0f} 膝:{knee_overuse:.0f} 疲劳:{fatigue:.0f}",
                            recommended_action="减少训练负荷至50%，增加恢复日" if shoulder_overuse > 80 else "监测负荷，安排泡沫轴放松",
                            is_read=rng.random() < 0.3, is_resolved=False,
                        ))
                        total_alerts += 1

                # Planned sessions (only for current + future)
                if current >= today - timedelta(days=7) and weekday < 6 and training_load > 0 and rng.random() < 0.7:
                    num_ex = min(len(exercise_objs), rng.randint(2, 4))
                    selected = rng.sample(exercise_objs, num_ex)
                    planned_load = 0
                    session = PlannedSession(
                        athlete_id=athlete.id, plan_date=current,
                        session_name={0: "力量日", 1: "耐力日", 2: "技术日", 3: "速度日", 4: "对抗训练", 5: "恢复日"}.get(weekday, "训练课"),
                        training_type=TRAINING_TYPES[weekday % 6],
                        planned_load=0, status="scheduled" if current > today else "completed",
                    )
                    db.add(session)
                    await db.flush()

                    for j, ex in enumerate(selected):
                        sets = rng.randint(3, 5)
                        reps = rng.randint(6, 12)
                        pe_rpe = rng.randint(5, 9)
                        load = sets * reps * (pe_rpe / 10.0) * 10
                        planned_load += load
                        pe = PlannedExercise(
                            planned_session_id=session.id, exercise_id=ex.id,
                            order_index=j, target_sets=sets, target_reps=reps,
                            target_rpe=pe_rpe, rest_seconds=rng.randint(30, 120),
                        )
                        db.add(pe)
                    session.planned_load = round(planned_load, 2)
                    total_plans += 1

                current += timedelta(days=1)

        # Generate ComputedMetrics (ACWR/RSSI) for past 60 days
        print("Computing ACWR/RSSI metrics...")
        today = date.today()
        for name, athlete in athlete_objs.items():
            profile = RISK_PROFILES[name]
            ff = profile["fatigue_factor"]
            rng = seeded_random(athlete.id, "metrics")

            for days_ago in range(60, -1, -1):
                calc_date = today - timedelta(days=days_ago)
                # Simulate ACWR
                acute_load = rng.uniform(profile["base_load"] * 0.7, profile["base_load"] * 1.3) * ff
                chronic_load = acute_load * rng.uniform(0.7, 1.0)
                acwr = round(acute_load / max(chronic_load, 1), 3)

                if acwr > 1.5:
                    zone = "高风险区"
                elif acwr > 1.3:
                    zone = "谨慎区"
                elif acwr < 0.8:
                    zone = "谨慎区"
                else:
                    zone = "安全区"

                rssi = round(rng.uniform(0, acwr * 50 + ff * 30), 1)
                if rssi > 60: level = "非功能性过度训练"
                elif rssi > 35: level = "功能性过度训练"
                elif rssi > 15: level = "适应性训练"
                else: level = "正常"

                db.add(ComputedMetric(
                    athlete_id=athlete.id, calc_date=calc_date,
                    acute_load_7d=round(acute_load, 1),
                    chronic_load_28d=round(chronic_load, 1),
                    acwr=acwr, acwr_risk_zone=zone,
                    monotony=round(rng.uniform(0.5, 2.5), 2),
                    strain=round(rng.uniform(300, 3000), 1),
                    strain_zscore=round(rng.uniform(-1.5, 2.5), 2),
                    rssi_score=rssi, rssi_risk_level=level,
                ))

        await db.commit()

        # Summary
        print(f"\n{'='*50}")
        print("Data seeding complete!")
        print(f"  Athletes:          {len(athlete_objs)}")
        print(f"  TrainingLogs:      ~{total_logs}")
        print(f"  DailyMetrics:      ~{total_metrics}")
        print(f"  Wellness:          ~{total_wellness}")
        print(f"  ComputedMetrics:   {len(athlete_objs) * 61}")
        print(f"  AlertEvents:       ~{total_alerts}")
        print(f"  PlannedSessions:   ~{total_plans}")
        print(f"  Exercises:         {len(exercise_objs)}")
        print(f"  Templates:         {len(templates)}")
        print(f"{'='*50}")
        print("\nReady to test the dashboard! Start the backend and frontend servers.")
        print("Key athletes to check:")
        for name in ["王强_新秀", "赵磊_冲击", "周杰_耐力"]:
            print(f"  - {name} (HIGH RISK)")
        for name in ["陈静_稳定", "钱峰_技巧"]:
            print(f"  - {name} (LOW RISK)")


if __name__ == "__main__":
    asyncio.run(seed())
