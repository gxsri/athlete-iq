"""
Standalone script to generate test data: athletes, planned sessions, exercise logs.
Demonstrates the "Plan → Execute → Monitor → Adjust" closed loop.

Usage:
    cd backend
    python ../scripts/generate_plan_and_logs.py

Or via API:
    curl -X POST http://localhost:8000/api/data-generator/generate?days_before=60&days_after=30&athletes_only=true
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import async_session, engine, Base
from app.models.athlete import (
    Athlete, TrainingLog, PlannedSession, PlannedExercise,
    ExerciseLibrary, ExerciseLog, DailyMetric,
)
from sqlalchemy import select
from datetime import date, timedelta
import random


EXERCISE_PRESETS = [
    {"name": "深蹲", "category": "力量", "description": "杠铃后蹲", "preset_params": {"weight_kg": 80, "reps": 8, "sets": 4, "rpe": 7, "rest_seconds": 120}},
    {"name": "卧推", "category": "力量", "description": "杠铃卧推", "preset_params": {"weight_kg": 60, "reps": 8, "sets": 4, "rpe": 7.5, "rest_seconds": 90}},
    {"name": "硬拉", "category": "力量", "description": "传统硬拉", "preset_params": {"weight_kg": 100, "reps": 5, "sets": 3, "rpe": 8, "rest_seconds": 150}},
    {"name": "弓步走", "category": "力量", "description": "负重弓步", "preset_params": {"weight_kg": 30, "reps": 12, "sets": 3, "rpe": 6, "rest_seconds": 90}},
    {"name": "400m间歇跑", "category": "耐力", "description": "跑道间歇", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 8, "rpe": 8, "rest_seconds": 90}},
    {"name": "跳绳双摇", "category": "速度", "description": "双摇跳绳", "preset_params": {"weight_kg": 0, "reps": 30, "sets": 5, "rpe": 7, "rest_seconds": 60}},
    {"name": "跳箱", "category": "速度", "description": "爆发力跳箱", "preset_params": {"weight_kg": 0, "reps": 6, "sets": 4, "rpe": 7, "rest_seconds": 90}},
    {"name": "多球杀球练习", "category": "羽毛球-技战术", "description": "多球杀球", "preset_params": {"weight_kg": 0, "reps": 40, "sets": 3, "rpe": 8, "rest_seconds": 60}},
    {"name": "米字步法跑位", "category": "羽毛球-技战术", "description": "全场步法", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 5, "rpe": 6, "rest_seconds": 30}},
    {"name": "网前搓球", "category": "羽毛球-技战术", "description": "网前技术", "preset_params": {"weight_kg": 0, "reps": 25, "sets": 2, "rpe": 4, "rest_seconds": 0}},
    {"name": "高远球练习", "category": "羽毛球-技战术", "description": "高远球", "preset_params": {"weight_kg": 0, "reps": 30, "sets": 2, "rpe": 5, "rest_seconds": 0}},
    {"name": "半场对抗", "category": "混合", "description": "半场单打", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 7, "duration_min": 25, "rest_seconds": 0}},
    {"name": "全场对抗", "category": "混合", "description": "全场模拟赛", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 8, "duration_min": 35, "rest_seconds": 0}},
    {"name": "肩部弹力带外旋", "category": "恢复", "description": "肩袖康复", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 4, "rest_seconds": 30}},
    {"name": "泡沫轴放松", "category": "恢复", "description": "筋膜松解", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 2, "duration_min": 15, "rest_seconds": 0}},
    {"name": "静态拉伸", "category": "柔韧", "description": "全身拉伸", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 2, "duration_min": 10, "rest_seconds": 0}},
    {"name": "核心训练", "category": "力量", "description": "核心组合", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 6, "rest_seconds": 30}},
    {"name": "引体向上", "category": "力量", "description": "上肢拉力", "preset_params": {"weight_kg": 0, "reps": 8, "sets": 4, "rpe": 7, "rest_seconds": 90}},
    {"name": "折返跑", "category": "速度", "description": "敏捷训练", "preset_params": {"weight_kg": 0, "reps": 5, "sets": 3, "rpe": 8, "rest_seconds": 90}},
    {"name": "高翻", "category": "力量", "description": "爆发力", "preset_params": {"weight_kg": 50, "reps": 3, "sets": 5, "rpe": 8, "rest_seconds": 150}},
]


async def main():
    async with async_session() as db:
        # 1. Seed exercises
        existing = await db.execute(select(ExerciseLibrary).limit(1))
        if not existing.scalar_one_or_none():
            for ex in EXERCISE_PRESETS:
                db.add(ExerciseLibrary(**ex))
            await db.commit()
            print(f"  [OK] Seeded {len(EXERCISE_PRESETS)} exercises")

        # 2. Get test athletes
        result = await db.execute(select(Athlete).where(Athlete.athlete_type == "test"))
        athletes = result.scalars().all()
        if not athletes:
            result = await db.execute(select(Athlete))
            athletes = result.scalars().all()
        print(f"  [OK] Found {len(athletes)} athletes")

        # 3. Get exercise library
        ex_result = await db.execute(select(ExerciseLibrary))
        exercises = ex_result.scalars().all()
        print(f"  [OK] {len(exercises)} exercises in library")

        # 4. Generate plans and logs for 4 months
        today = date.today()
        start = today - timedelta(days=90)
        end = today + timedelta(days=30)

        session_names = {
            0: "下肢力量日", 1: "上肢力量日", 2: "耐力日",
            3: "技术日", 4: "速度+敏捷", 5: "对抗训练",
        }
        training_types = ["力量", "力量", "耐力", "技战术", "速度", "混合"]

        total_plans = 0
        total_logs = 0

        for athlete in athletes:
            rng = random.Random(hash(str(athlete.id)))
            current = start
            while current <= end:
                weekday = current.weekday()
                if weekday < 6 and rng.random() < 0.75:
                    # Check existing
                    check = await db.execute(
                        select(PlannedSession).where(
                            PlannedSession.athlete_id == athlete.id,
                            PlannedSession.plan_date == current,
                        )
                    )
                    if not check.scalar_one_or_none():
                        num_ex = min(len(exercises), rng.randint(2, 5))
                        selected = rng.sample(exercises, num_ex)

                        session = PlannedSession(
                            athlete_id=athlete.id,
                            plan_date=current,
                            session_name=session_names.get(weekday, "训练课"),
                            training_type=training_types[weekday % 6],
                            planned_load=0,
                            status="completed" if current < today else "scheduled",
                        )
                        db.add(session)
                        await db.flush()

                        total_load = 0.0
                        for i, ex in enumerate(selected):
                            s = rng.randint(3, 5)
                            r = rng.randint(6, 12)
                            rpe = rng.randint(5, 8)
                            w = float(ex.preset_params.get("weight_kg", 0) or 0) if ex.preset_params else 0
                            load = s * r * (rpe / 10.0) * 10 + w * s * 0.5
                            total_load += load

                            pe = PlannedExercise(
                                planned_session_id=session.id,
                                exercise_id=ex.id,
                                order_index=i,
                                target_weight_kg=w if w > 0 else None,
                                target_reps=r,
                                target_sets=s,
                                rest_seconds=ex.preset_params.get("rest_seconds", 60) if ex.preset_params else 60,
                                target_rpe=rpe,
                            )
                            db.add(pe)
                            await db.flush()

                            # Create exercise logs for past dates
                            if current < today:
                                tl_check = await db.execute(
                                    select(TrainingLog).where(
                                        TrainingLog.athlete_id == athlete.id,
                                        TrainingLog.training_date == current,
                                    )
                                )
                                tl = tl_check.scalar_one_or_none()
                                if tl:
                                    comp = rng.uniform(0.7, 1.1)
                                    el = ExerciseLog(
                                        training_log_id=tl.id,
                                        exercise_id=ex.id,
                                        order_index=i,
                                        actual_weight_kg=round(w * rng.uniform(0.9, 1.05), 1) if w > 0 else None,
                                        actual_reps=max(1, round(r * comp)),
                                        actual_sets=max(1, round(s * comp)),
                                        actual_rpe=max(3, min(10, round(rpe * rng.uniform(0.8, 1.2)))),
                                        planned_exercise_id=pe.id,
                                    )
                                    db.add(el)
                                    total_logs += 1

                        session.planned_load = round(total_load, 2)
                        total_plans += 1

                current += timedelta(days=1)

        await db.commit()
        print(f"\n  [DONE] Generated {total_plans} planned sessions, {total_logs} exercise logs")
        print(f"  Date range: {start} ~ {end}")
        print(f"  Athletes: {len(athletes)}")
        print(f"\n  Now visit: http://localhost:5173/planner to see the plans")
        print(f"  Or: http://localhost:5173/athletes/<id> to see the TodayPlanCard")


if __name__ == "__main__":
    asyncio.run(main())
