"""
AthleteIQ - Rehab Center API (NASM OPT Model)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta
from uuid import UUID
from typing import List, Optional

from app.database import get_db, logger
from app.models.athlete import (
    Athlete, DailyMetric, RehabExercise, RehabPlan, RehabPlanExercise,
)

router = APIRouter(prefix="/api/rehab", tags=["康复中心"])

# ============ 12 Preset Rehab Exercises (NASM OPT) ============

PRESET_EXERCISES = [
    {"name": "肩部泡沫轴滚动", "target_body_part": "shoulder", "nasm_phase": "inhibit", "purpose": "放松肩袖肌群及上斜方肌筋膜", "difficulty": 1, "equipment_needed": ["泡沫轴"],
     "instructions": "侧卧，泡沫轴置于肩外侧下方。缓慢滚动寻找压痛点，每个痛点停留30秒。从肩峰至肩胛骨外侧缘。", "common_mistakes": "速度过快、未找到真正压痛点、憋气"},
    {"name": "墙角胸肌拉伸", "target_body_part": "shoulder", "nasm_phase": "lengthen", "purpose": "缓解胸大肌/胸小肌紧张，改善肩关节前侧活动度", "difficulty": 1, "equipment_needed": [],
     "instructions": "面对墙角站立，双手前臂贴墙。一脚前跨，身体缓慢前倾，感受胸肌拉伸。保持30秒×3组。", "common_mistakes": "耸肩、腰部过度反弓、头部前伸"},
    {"name": "弹力带肩外旋", "target_body_part": "shoulder", "nasm_phase": "activate", "purpose": "强化肩袖外旋肌群（冈下肌、小圆肌），预防肩峰撞击", "difficulty": 2, "equipment_needed": ["弹力带"],
     "instructions": "站立，肘关节屈曲90度紧贴身体。手持弹力带，缓慢外旋前臂，保持肘部不动。顶峰收缩1-2秒，控制返回。2-3组×12-15次。", "common_mistakes": "耸肩、躯干代偿旋转、肘部离开身体、速度太快"},
    {"name": "YTWL肩胛稳定性训练", "target_body_part": "shoulder", "nasm_phase": "integrate", "purpose": "整合肩胛骨运动控制，改善肩肱节律", "difficulty": 3, "equipment_needed": ["哑铃 1-3kg"],
     "instructions": "俯卧位，双臂依次做Y（上举）、T（侧平举）、W（屈肘后缩）、L（外旋）四个位置。每个位置保持2秒，3组×10次。全程拇指朝上。", "common_mistakes": "下背部过度发力、颈后缩、速度不均匀"},
    {"name": "股四头肌泡沫轴放松", "target_body_part": "knee", "nasm_phase": "inhibit", "purpose": "放松股四头肌及髂胫束，减轻膝关节压力", "difficulty": 1, "equipment_needed": ["泡沫轴"],
     "instructions": "俯卧，泡沫轴置于大腿前侧。缓慢从髋部滚动至膝盖上方。换腿重复。每侧2-3分钟。", "common_mistakes": "直接压在膝盖骨上、速度太快、未覆盖外侧ITB"},
    {"name": "腘绳肌静态拉伸", "target_body_part": "knee", "nasm_phase": "lengthen", "purpose": "增加腘绳肌柔韧性，改善膝后侧软组织延展性", "difficulty": 1, "equipment_needed": ["瑜伽带"],
     "instructions": "仰卧，单腿上举，瑜伽带绕足底，缓慢将腿拉向身体。保持膝盖微屈。每侧30秒×3组。", "common_mistakes": "膝盖完全锁定、骨盆离地、对侧腿弯曲"},
    {"name": "臀桥", "target_body_part": "knee", "nasm_phase": "activate", "purpose": "激活臀大肌，减少膝关节代偿性负荷", "difficulty": 2, "equipment_needed": [],
     "instructions": "仰卧屈膝，双脚与髋同宽。臀部发力上抬至肩-髋-膝成一线。顶峰收缩2秒。3组×15-20次。", "common_mistakes": "腰部过伸代偿、脚跟着地位置不对、下放过快"},
    {"name": "单腿落地控制", "target_body_part": "knee", "nasm_phase": "integrate", "purpose": "改善动态膝关节稳定性和神经肌肉控制", "difficulty": 3, "equipment_needed": ["跳箱 20-30cm"],
     "instructions": "从20-30cm箱上单腿跳下，控制落地时膝关节屈曲约30度，保持膝盖与第二脚趾对齐，维持3秒平衡。每侧3组×6次。", "common_mistakes": "膝盖内扣、落地声音过大（刚性落地）、躯干过度前倾"},
    {"name": "小腿三头肌泡沫轴", "target_body_part": "ankle", "nasm_phase": "inhibit", "purpose": "放松腓肠肌和比目鱼肌，改善踝关节灵活性", "difficulty": 1, "equipment_needed": ["泡沫轴"],
     "instructions": "坐姿，泡沫轴置于小腿下方。从跟腱缓慢滚动至膝窝。每侧2-3分钟。可双腿叠加增加压力。", "common_mistakes": "速度太快、忽略小腿外侧（腓骨长短肌）"},
    {"name": "踝关节背屈拉伸", "target_body_part": "ankle", "nasm_phase": "lengthen", "purpose": "增加踝背屈活动度，改善深蹲和落地姿势", "difficulty": 1, "equipment_needed": [],
     "instructions": "弓步姿势，后腿伸直。前腿膝关节向前平移超过脚尖，保持后脚跟不离地。每侧30秒×3组。", "common_mistakes": "后脚跟抬起（未真正拉伸小腿后侧）、前膝过度内扣"},
    {"name": "弹力带踝外翻", "target_body_part": "ankle", "nasm_phase": "activate", "purpose": "强化腓骨长/短肌（踝外翻肌群），预防崴脚", "difficulty": 2, "equipment_needed": ["弹力带"],
     "instructions": "坐姿，弹力带绕两脚外侧。缓慢将双足外翻（远离中线），顶峰收缩2秒。3组×12-15次。", "common_mistakes": "膝盖外移代偿、动作范围过小、速度太快"},
    {"name": "单腿站立本体感觉训练", "target_body_part": "ankle", "nasm_phase": "integrate", "purpose": "提高踝关节本体感觉和动态稳定性", "difficulty": 3, "equipment_needed": [],
     "instructions": "单腿站立，闭眼保持平衡30秒。进阶：站立在不稳定平面（枕头/平衡垫）。每侧3组。", "common_mistakes": "睁开眼睛、扶墙、另一脚触地"},
    {"name": "鸟狗式核心稳定", "target_body_part": "core", "nasm_phase": "activate", "purpose": "激活深层核心肌群（腹横肌、多裂肌），改善躯干稳定性", "difficulty": 2, "equipment_needed": [],
     "instructions": "四足跪姿，同时抬起右臂和左腿至水平位置。保持核心收紧，骨盆不旋转。每侧交替，3组×10次。", "common_mistakes": "骨盆旋转/倾斜、颈后缩、憋气、动作太快"},
    {"name": "死虫式核心训练", "target_body_part": "core", "nasm_phase": "integrate", "purpose": "整合核心与四肢协调运动，减少能量泄漏", "difficulty": 2, "equipment_needed": [],
     "instructions": "仰卧，双臂上举，双腿屈髋屈膝90度。缓慢放下对侧手臂和腿至接近地面，保持腰部贴地。回起始位，换边。3组×8次/侧。", "common_mistakes": "腰部离地、颈前屈、四肢下放过快"},
]


async def seed_rehab_exercises(db: AsyncSession):
    """Seed preset rehab exercises if table is empty."""
    existing = await db.execute(select(func.count()).select_from(RehabExercise))
    if existing.scalar() == 0:
        for ex in PRESET_EXERCISES:
            db.add(RehabExercise(**ex))
        await db.commit()
        logger.info(f"Seeded {len(PRESET_EXERCISES)} preset rehab exercises")


# ============ Exercise Library ============

@router.get("/exercises")
async def list_exercises(
    body_part: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await seed_rehab_exercises(db)
    query = select(RehabExercise)
    if body_part:
        query = query.where(RehabExercise.target_body_part == body_part)
    if phase:
        query = query.where(RehabExercise.nasm_phase == phase)
    query = query.order_by(RehabExercise.difficulty)
    result = await db.execute(query)
    exercises = result.scalars().all()
    return [{
        "id": str(e.id), "name": e.name, "target_body_part": e.target_body_part,
        "nasm_phase": e.nasm_phase, "purpose": e.purpose, "difficulty": e.difficulty,
        "equipment_needed": e.equipment_needed, "instructions": e.instructions,
        "common_mistakes": e.common_mistakes, "image_url": e.image_url, "video_url": e.video_url,
    } for e in exercises]


@router.get("/exercises/{exercise_id}")
async def get_exercise(exercise_id: UUID, db: AsyncSession = Depends(get_db)):
    ex = await db.get(RehabExercise, exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="动作不存在")
    return ex


# ============ Rehab Plans ============

@router.get("/plans/athlete/{athlete_id}")
async def get_athlete_plans(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RehabPlan).where(RehabPlan.athlete_id == athlete_id).order_by(RehabPlan.created_at.desc())
    )
    plans = result.scalars().all()
    output = []
    for plan in plans:
        pe_result = await db.execute(
            select(RehabPlanExercise).where(RehabPlanExercise.plan_id == plan.id)
        )
        exercises = pe_result.scalars().all()
        completed = sum(1 for e in exercises if e.completed)
        total = len(exercises)
        output.append({
            "id": str(plan.id), "athlete_id": str(plan.athlete_id),
            "name": plan.name, "start_date": str(plan.start_date),
            "end_date": str(plan.end_date), "status": plan.status,
            "notes": plan.notes, "completion_pct": round(completed / max(total, 1) * 100, 1),
            "exercises_count": total, "completed_count": completed,
        })
    return output


@router.post("/plans", status_code=201)
async def create_plan(
    athlete_id: UUID = Query(...),
    name: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")
    plan = RehabPlan(athlete_id=athlete_id, name=name, start_date=start_date, end_date=end_date, notes=notes)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"id": str(plan.id), "name": plan.name, "start_date": str(plan.start_date), "end_date": str(plan.end_date)}


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: UUID, db: AsyncSession = Depends(get_db)):
    plan = await db.get(RehabPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    await db.delete(plan)
    await db.commit()
    return {"status": "deleted"}


# ============ Schedule & Check-in ============

@router.get("/schedule")
async def get_schedule(
    athlete_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(RehabPlan).where(RehabPlan.athlete_id == athlete_id, RehabPlan.status == "active")
    plan_result = await db.execute(query)
    active_plans = plan_result.scalars().all()
    if not active_plans:
        return []

    plan_ids = [p.id for p in active_plans]
    pe_query = select(RehabPlanExercise).where(RehabPlanExercise.plan_id.in_(plan_ids))
    if start_date:
        pe_query = pe_query.where(RehabPlanExercise.scheduled_date >= start_date)
    if end_date:
        pe_query = pe_query.where(RehabPlanExercise.scheduled_date <= end_date)
    pe_query = pe_query.order_by(RehabPlanExercise.scheduled_date, RehabPlanExercise.order_index)
    result = await db.execute(pe_query)
    exercise_slots = result.scalars().all()

    output = []
    for slot in exercise_slots:
        ex = await db.get(RehabExercise, slot.exercise_id)
        output.append({
            "id": str(slot.id), "plan_id": str(slot.plan_id),
            "exercise_id": str(slot.exercise_id), "exercise_name": ex.name if ex else "未知",
            "target_body_part": ex.target_body_part if ex else "",
            "scheduled_date": str(slot.scheduled_date),
            "sets": slot.sets, "reps": slot.reps, "rest_seconds": slot.rest_seconds,
            "completed": slot.completed, "completed_at": str(slot.completed_at) if slot.completed_at else None,
            "instructions": ex.instructions if ex else "",
            "common_mistakes": ex.common_mistakes if ex else "",
            "pain_before": slot.pain_before, "pain_after": slot.pain_after,
        })
    return output


@router.put("/plan-exercises/{pe_id}/complete")
async def complete_exercise(
    pe_id: UUID,
    pain_before: int = Query(0, ge=0, le=10),
    pain_after: int = Query(0, ge=0, le=10),
    db: AsyncSession = Depends(get_db),
):
    slot = await db.get(RehabPlanExercise, pe_id)
    if not slot:
        raise HTTPException(status_code=404, detail="日程不存在")
    slot.completed = True
    slot.completed_at = date.today()
    slot.pain_before = pain_before
    slot.pain_after = pain_after
    await db.commit()
    return {"status": "completed", "pain_before": pain_before, "pain_after": pain_after}


# ============ Auto-Generate Plan (Based on Risk/Pain) ============

@router.post("/generate-plan")
async def auto_generate_plan(
    athlete_id: UUID = Query(...),
    target_body_part: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """自动生成康复计划：基于肩/膝风险值和疼痛评分"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    # Get latest daily metrics
    metric_result = await db.execute(
        select(DailyMetric).where(DailyMetric.athlete_id == athlete_id).order_by(DailyMetric.metric_date.desc()).limit(1)
    )
    metric = metric_result.scalar_one_or_none()

    if not metric:
        raise HTTPException(status_code=400, detail="暂无身体数据，无法生成计划")

    # Determine which body parts need rehab
    parts_to_rehab = []
    if target_body_part:
        parts_to_rehab = [target_body_part]
    else:
        if (metric.shoulder_overuse_risk or 0) > 60 or (metric.arm_pain_vas or 0) > 4:
            parts_to_rehab.append("shoulder")
        if (metric.knee_overuse_risk or 0) > 60 or (metric.leg_pain_vas or 0) > 4:
            parts_to_rehab.append("knee")
        if (metric.jump_landing_quality or 7) <= 5:
            if "knee" not in parts_to_rehab:
                parts_to_rehab.append("knee")
        if not parts_to_rehab:
            parts_to_rehab = ["core"]  # Default to core work

    # Get exercises for target parts, 4 phases × 1 each per part
    nasm_order = ["inhibit", "lengthen", "activate", "integrate"]
    all_exercises_result = await db.execute(
        select(RehabExercise).where(RehabExercise.target_body_part.in_(parts_to_rehab))
    )
    all_ex = all_exercises_result.scalars().all()

    # Sort by NASM phase order
    phase_order = {p: i for i, p in enumerate(nasm_order)}
    all_ex.sort(key=lambda e: phase_order.get(e.nasm_phase, 99))

    # Create plan: 14 days
    today = date.today()
    plan = RehabPlan(
        athlete_id=athlete_id,
        name=f"{'/' .join(parts_to_rehab)}康复计划",
        start_date=today,
        end_date=today + timedelta(days=14),
        notes=f"自动生成：基于肩/膝风险值和疼痛评分。目标部位: {', '.join(parts_to_rehab)}",
    )
    db.add(plan)
    await db.flush()

    created = 0
    used_per_day = {}  # Track which exercises used each day
    for day_offset in range(14):
        scheduled = today + timedelta(days=day_offset)
        day_key = str(scheduled)
        # Pick 3-4 unique exercises per day, rotating through the list
        start_idx = (day_offset * 3) % len(all_ex)
        day_ex = []
        seen = set()
        for i in range(min(4, len(all_ex))):
            idx = (start_idx + i) % len(all_ex)
            ex = all_ex[idx]
            if ex.id not in seen:
                day_ex.append(ex)
                seen.add(ex.id)
                if len(day_ex) >= 4:
                    break
        for idx, ex in enumerate(day_ex):
            db.add(RehabPlanExercise(
                plan_id=plan.id, exercise_id=ex.id,
                scheduled_date=scheduled, order_index=idx,
                sets=3, reps="12-15", rest_seconds=60,
            ))
            created += 1

    await db.commit()
    logger.info(f"Auto-generated rehab plan '{plan.name}' for athlete {athlete_id}: {created} exercise slots")
    return {
        "plan_id": str(plan.id), "plan_name": plan.name,
        "parts_targeted": parts_to_rehab, "days": 14,
        "exercise_slots": created, "start_date": str(today),
    }


# ============ Progress Tracking ============

@router.get("/progress/{athlete_id}")
async def get_rehab_progress(
    athlete_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get rehab plan progress: completion rate and pain trend."""
    plans_result = await db.execute(
        select(RehabPlan).where(RehabPlan.athlete_id == athlete_id).order_by(RehabPlan.created_at.desc())
    )
    plans = plans_result.scalars().all()
    if not plans:
        return {"progress_pct": 0, "pain_trend": [], "message": "暂无康复计划"}

    plan_ids = [p.id for p in plans]
    pe_result = await db.execute(
        select(RehabPlanExercise).where(
            RehabPlanExercise.plan_id.in_(plan_ids),
            RehabPlanExercise.scheduled_date >= date.today() - timedelta(days=days),
        ).order_by(RehabPlanExercise.scheduled_date)
    )
    slots = pe_result.scalars().all()

    completed = sum(1 for s in slots if s.completed)
    progress_pct = round(completed / max(len(slots), 1) * 100, 1)

    # Pain trend: average pain before/after per day
    pain_by_day = {}
    for s in slots:
        if s.completed and s.pain_before is not None:
            d = str(s.scheduled_date)
            if d not in pain_by_day:
                pain_by_day[d] = {"before": [], "after": []}
            pain_by_day[d]["before"].append(s.pain_before)
            if s.pain_after is not None:
                pain_by_day[d]["after"].append(s.pain_after)

    pain_trend = sorted([
        {
            "date": d,
            "avg_pain_before": round(sum(v["before"]) / len(v["before"]), 1),
            "avg_pain_after": round(sum(v["after"]) / len(v["after"]), 1) if v["after"] else 0,
        }
        for d, v in pain_by_day.items()
    ], key=lambda x: x["date"])

    return {
        "progress_pct": progress_pct,
        "total_exercises": len(slots),
        "completed_count": completed,
        "pain_trend": pain_trend,
    }
