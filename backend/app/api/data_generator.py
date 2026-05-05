"""
AthleteIQ - Virtual Data Generator API
Generates 3 months of simulated daily training data for test athletes.
"""
import random
import math
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import get_db, logger, _use_sqlite
from app.models.athlete import Athlete, TrainingLog, WellnessQuestionnaire, DailyMetric, ComputedMetric, TrainingAssignment, TrainingTemplate, PlannedSession, PlannedExercise, ExerciseLibrary, ExerciseLog

router = APIRouter(prefix="/api/data-generator", tags=["虚拟数据生成"])


def _random_seed(athlete_id: str, day_offset: int) -> int:
    """Generate deterministic-ish seed from athlete_id + day, so re-runs give similar data."""
    h = hash(str(athlete_id) + str(day_offset))
    return h


def _generate_daily_data(athlete_id: str, target_date: date, day_offset: int) -> dict:
    """Generate one day of simulated data for a test athlete."""
    rng = random.Random(_random_seed(athlete_id, day_offset))

    # Weekday effect: Mon-Fri higher, Sat-Sun lower
    weekday = target_date.weekday()
    is_weekend = weekday >= 5

    base_load = 40 if is_weekend else 72
    training_load = max(0, min(100, base_load + rng.uniform(-15, 15)))

    # injury_risk correlated with training_load
    injury_risk = max(0, min(100, training_load * 0.6 + rng.uniform(0, 20)))

    # fatigue correlated with training_load
    fatigue = max(0, min(100, training_load * 0.8 + rng.uniform(0, 15)))

    # sleep quality: 4.0-7.0, slightly lower when fatigue is high
    sleep_quality = round(max(4.0, min(7.0, 6.5 - (fatigue / 100) * 2.0 + rng.uniform(-0.5, 0.5))), 1)

    # === 羽毛球专项身体数据 ===
    smash_today = int(max(0, training_load * 1.5 + rng.uniform(-20, 20))) if not is_weekend else int(rng.uniform(0, 30))
    smash_7d_avg = round(smash_today * rng.uniform(0.7, 1.3), 1)
    overhead_week = int(smash_7d_avg * 7 * rng.uniform(1.0, 1.5))
    max_smash_30d = int(max(smash_today, smash_today * rng.uniform(0.8, 1.4)))
    ext_rotation_ratio = round(rng.uniform(0.5, 0.9), 2)
    arm_pain = int(max(0, min(10, (fatigue / 100) * 5 + rng.uniform(-1, 2))))

    total_impacts = int(max(0, training_load * 8 + rng.uniform(-50, 50))) if not is_weekend else int(rng.uniform(0, 100))
    jump_quality = int(max(1, min(10, 8 - (fatigue / 100) * 4 + rng.uniform(-1, 1))))
    quad_ham_ratio = round(rng.uniform(0.5, 1.0), 2)
    footwork = int(max(1, min(10, 7 - (fatigue / 100) * 3 + rng.uniform(-1, 1))))
    leg_pain = int(max(0, min(10, (fatigue / 100) * 4 + rng.uniform(-1, 1))))
    reaction_time = int(max(150, min(400, 250 + fatigue * 0.8 + rng.uniform(-20, 20))))
    has_knee_history = rng.random() < 0.2

    # Compute risks using the risk engine
    from app.core.risk_engine import compute_all_risks
    risks = compute_all_risks(
        smash_7d_avg=smash_7d_avg,
        overhead_week_total=overhead_week,
        external_rotation_ratio=ext_rotation_ratio,
        sleep_hours=sleep_quality,
        today_smash=smash_today,
        max_smash_30d=max_smash_30d,
        global_fatigue=fatigue,
        reaction_time_ms=reaction_time,
        total_impacts_7d=total_impacts,
        jump_landing_quality=jump_quality,
        quad_hamstring_ratio=quad_ham_ratio,
        has_knee_pain_history=has_knee_history,
        footwork_score=footwork,
    )

    return {
        "training_load": round(training_load, 1),
        "injury_risk": round(injury_risk, 1),
        "fatigue": round(fatigue, 1),
        "sleep_quality": sleep_quality,
        # Body data
        "smash_count_today": smash_today,
        "smash_7d_avg": smash_7d_avg,
        "overhead_week_total": overhead_week,
        "max_smash_30d": max_smash_30d,
        "external_rotation_ratio": ext_rotation_ratio,
        "arm_pain_vas": arm_pain,
        "total_impacts_7d": total_impacts,
        "jump_landing_quality": jump_quality,
        "quad_hamstring_ratio": quad_ham_ratio,
        "footwork_score": footwork,
        "leg_pain_vas": leg_pain,
        "reaction_time_ms": reaction_time,
        "has_knee_pain_history": has_knee_history,
        **risks,
    }


def _compute_training_metrics(training_load: float, rpe: int, duration: float) -> dict:
    """Derive RPE and session load from the training load."""
    # Map 0-100 load to RPE 1-10 and duration
    rpe_val = max(1, min(10, int(training_load / 10) + rpe_offset))
    session_load = duration * rpe_val
    return {"rpe": rpe_val, "duration_minutes": duration, "session_load": session_load}


@router.post("/generate")
async def generate_test_data(
    athletes_only: bool = Query(True, description="If True, only generate for athletes with type='test'"),
    days_before: int = Query(45, ge=1, le=180),
    days_after: int = Query(45, ge=0, le=180),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate 3 months of simulated daily data for test athletes.

    Creates: TrainingLog, WellnessQuestionnaire, DailyMetric records.
    Uses upsert logic: skips days that already have data.
    """
    # Find target athletes
    query = select(Athlete)
    if athletes_only:
        query = query.where(Athlete.athlete_type == "test")
    result = await db.execute(query)
    athletes = result.scalars().all()

    if not athletes:
        return {"status": "warning", "message": "没有找到测试运动员。请先创建 type='test' 的运动员，或设置 athletes_only=false", "generated": 0}

    today = date.today()
    start_date = today - timedelta(days=days_before)
    end_date = today + timedelta(days=days_after)

    total_created = {"training_logs": 0, "wellness": 0, "daily_metrics": 0}
    total_skipped = {"training_logs": 0, "wellness": 0, "daily_metrics": 0}

    for athlete in athletes:
        # Get existing data dates to avoid duplicates
        existing_logs_result = await db.execute(
            select(TrainingLog.training_date)
            .where(
                TrainingLog.athlete_id == athlete.id,
                TrainingLog.training_date >= start_date,
                TrainingLog.training_date <= end_date,
            )
        )
        existing_dates = {r[0] for r in existing_logs_result.all()}

        current_date = start_date
        day_offset = 0
        while current_date <= end_date:
            day_offset = (current_date - today).days
            data = _generate_daily_data(str(athlete.id), current_date, day_offset)

            training_load = data["training_load"]

            # Determine training type by day-of-week pattern
            weekday = current_date.weekday()
            training_types = ["力量", "耐力", "速度", "技战术", "混合", "力量", "柔韧"]
            training_type = training_types[weekday % 7]
            cycle_phase = "准备期"

            rpe_val = max(1, min(10, int(training_load / 10) + random.randint(0, 2)))
            duration = max(20, min(180, training_load * 1.5 + random.uniform(-10, 10)))
            session_load = round(duration * rpe_val, 1)

            # Upsert TrainingLog
            if current_date not in existing_dates:
                log = TrainingLog(
                    athlete_id=athlete.id,
                    training_date=current_date,
                    duration_minutes=round(duration, 1),
                    rpe=rpe_val,
                    training_type=training_type,
                    session_load=session_load,
                    cycle_phase=cycle_phase,
                    description=f"自动生成测试数据 - {training_type}训练",
                    source="auto_generated",
                    tags=["test_data"],
                )
                db.add(log)
                total_created["training_logs"] += 1
            else:
                total_skipped["training_logs"] += 1

            # DailyMetrics: always upsert (update if exists)
            existing_metric = await db.execute(
                select(DailyMetric).where(
                    DailyMetric.athlete_id == athlete.id,
                    DailyMetric.metric_date == current_date,
                )
            )
            metric = existing_metric.scalar_one_or_none()
            # New log fields
            rpe_val_log2 = max(1, min(10, int(training_load / 10) + random.randint(-1, 2)))
            energy_val = max(1, min(10, 8 - int(data["fatigue"] / 15) + random.randint(-1, 1)))
            ms = {
                "shoulder": min(10, int(data.get("arm_pain_vas", 0) + random.uniform(-1, 1))),
                "quad": min(10, int(data["fatigue"] / 15 + random.uniform(-1, 1))),
                "calf": min(10, int(data["fatigue"] / 18 + random.uniform(-1, 1))),
                "back": max(0, min(10, int(data["fatigue"] / 20 + random.uniform(-1, 1)))),
            }
            comp_rate = round(random.uniform(70, 110), 1)

            if metric:
                metric.training_load = data["training_load"]
                metric.injury_risk = data["injury_risk"]
                metric.fatigue = data["fatigue"]
                metric.sleep_quality = data["sleep_quality"]
                metric.rpe = rpe_val_log2
                metric.energy_level = energy_val
                metric.muscle_soreness = ms
                metric.completion_rate = comp_rate
                # Body data fields
                for key in ["smash_count_today", "smash_7d_avg", "overhead_week_total",
                           "max_smash_30d", "external_rotation_ratio", "arm_pain_vas",
                           "total_impacts_7d", "jump_landing_quality", "quad_hamstring_ratio",
                           "footwork_score", "leg_pain_vas", "reaction_time_ms",
                           "has_knee_pain_history", "shoulder_overuse_risk",
                           "shoulder_acute_risk", "knee_overuse_risk", "knee_acute_risk"]:
                    if key in data:
                        setattr(metric, key, data[key])
                total_skipped["daily_metrics"] += 1
            else:
                db.add(DailyMetric(
                    athlete_id=athlete.id, metric_date=current_date,
                    training_load=data["training_load"],
                    injury_risk=data["injury_risk"],
                    fatigue=data["fatigue"],
                    sleep_quality=data["sleep_quality"],
                    rpe=rpe_val_log2, energy_level=energy_val,
                    muscle_soreness=ms, completion_rate=comp_rate,
                    smash_count_today=data.get("smash_count_today", 0),
                    smash_7d_avg=data.get("smash_7d_avg", 0),
                    overhead_week_total=data.get("overhead_week_total", 0),
                    max_smash_30d=data.get("max_smash_30d", 0),
                    external_rotation_ratio=data.get("external_rotation_ratio", 0.7),
                    arm_pain_vas=data.get("arm_pain_vas", 0),
                    total_impacts_7d=data.get("total_impacts_7d", 0),
                    jump_landing_quality=data.get("jump_landing_quality", 7),
                    quad_hamstring_ratio=data.get("quad_hamstring_ratio", 0.8),
                    footwork_score=data.get("footwork_score", 7),
                    leg_pain_vas=data.get("leg_pain_vas", 0),
                    reaction_time_ms=data.get("reaction_time_ms", 250),
                    has_knee_pain_history=data.get("has_knee_pain_history", False),
                    shoulder_overuse_risk=data.get("shoulder_overuse_risk", 0),
                    shoulder_acute_risk=data.get("shoulder_acute_risk", 0),
                    knee_overuse_risk=data.get("knee_overuse_risk", 0),
                    knee_acute_risk=data.get("knee_acute_risk", 0),
                ))
                total_created["daily_metrics"] += 1

            # WellnessQuestionnaire: every 7 days
            if day_offset % 7 == 0:
                existing_wellness = await db.execute(
                    select(WellnessQuestionnaire).where(
                        WellnessQuestionnaire.athlete_id == athlete.id,
                        WellnessQuestionnaire.record_date == current_date,
                    )
                )
                if not existing_wellness.scalar_one_or_none():
                    db.add(WellnessQuestionnaire(
                        athlete_id=athlete.id,
                        record_date=current_date,
                        morning_heart_rate=int(55 + training_load * 0.15 + random.uniform(-3, 3)),
                        hrv_lnrmssd=round(max(30, min(80, 75 - training_load * 0.3 + random.uniform(-5, 5))), 2),
                        sleep_duration_hours=round(max(5, min(10, 8 - (data["fatigue"] / 100) * 2 + random.uniform(-1, 1))), 1),
                        sleep_quality=int(max(1, min(5, data["sleep_quality"] / 7 * 5))),
                        fatigue_score=int(max(1, min(5, data["fatigue"] / 20))),
                        muscle_soreness=int(max(1, min(5, training_load / 20))),
                        stress_score=int(max(1, min(5, data["fatigue"] / 20 + random.randint(0, 2)))),
                        mood_score=int(max(1, min(5, 4 - int(data["fatigue"] / 30)))),
                        source="auto_generated",
                    ))
                    total_created["wellness"] += 1
                else:
                    total_skipped["wellness"] += 1

            current_date += timedelta(days=1)

    # === Generate Assignments: randomly assign 2-3 templates per week ===
    templates_result = await db.execute(select(TrainingTemplate).limit(10))
    all_templates = templates_result.scalars().all()
    if all_templates:
        for athlete in athletes:
            cur_date = start_date
            while cur_date <= end_date:
                if cur_date.weekday() in (1, 3, 5):  # Mon, Wed, Fri → assign plans
                    if random.random() < 0.7:  # 70% chance
                        tmpl = all_templates[random.randint(0, len(all_templates) - 1)]
                        existing_assign = await db.execute(
                            select(TrainingAssignment).where(
                                TrainingAssignment.athlete_id == athlete.id,
                                TrainingAssignment.scheduled_date == cur_date,
                            )
                        )
                        if not existing_assign.scalar_one_or_none():
                            db.add(TrainingAssignment(
                                athlete_id=athlete.id,
                                template_id=tmpl.id,
                                scheduled_date=cur_date,
                                overrides={"target_load": int(tmpl.content.get("target_load", 50) * random.uniform(0.8, 1.2))},
                                status="scheduled",
                            ))
                cur_date += timedelta(days=1)

    # === Generate Planned Sessions & Exercise Logs ===
    # Get exercise library for creating planned exercises
    ex_lib_result = await db.execute(select(ExerciseLibrary).limit(20))
    exercise_lib = ex_lib_result.scalars().all()
    if not exercise_lib:
        # seed exercises first
        from app.api.exercise_library import SEED_EXERCISES
        for ex_data in SEED_EXERCISES:
            db.add(ExerciseLibrary(**ex_data))
        await db.flush()
        ex_lib_result = await db.execute(select(ExerciseLibrary).limit(20))
        exercise_lib = ex_lib_result.scalars().all()

    total_plans = 0
    total_exercise_logs = 0

    if exercise_lib:
        for athlete in athletes:
            cur_date = start_date
            while cur_date <= end_date:
                weekday = cur_date.weekday()
                # Generate plans on training days (Mon-Sat)
                if weekday < 6 and random.random() < 0.75:
                    rng = random.Random(hash(str(athlete.id) + str(cur_date) + "plan"))

                    # Check existing plans for this date
                    existing_plan = await db.execute(
                        select(PlannedSession).where(
                            PlannedSession.athlete_id == athlete.id,
                            PlannedSession.plan_date == cur_date,
                        )
                    )
                    if not existing_plan.scalar_one_or_none():
                        # Pick 2-5 random exercises
                        num_ex = min(len(exercise_lib), rng.randint(2, 5))
                        selected_exs = rng.sample(exercise_lib, num_ex)

                        session_names = {
                            0: "下肢力量日", 1: "上肢力量日", 2: "耐力日",
                            3: "技术日", 4: "速度+敏捷", 5: "对抗训练",
                        }
                        session = PlannedSession(
                            athlete_id=athlete.id,
                            plan_date=cur_date,
                            session_name=session_names.get(weekday, "训练课"),
                            training_type=["力量","力量","耐力","技战术","速度","混合"][weekday % 6],
                            planned_load=0,  # calculated below
                            status="scheduled" if cur_date >= date.today() else "completed",
                        )
                        db.add(session)
                        await db.flush()

                        total_load = 0.0
                        for i, ex in enumerate(selected_exs):
                            sets = rng.randint(3, 5)
                            reps = rng.randint(6, 12)
                            rpe = rng.randint(5, 8)
                            weight = float(ex.preset_params.get("weight_kg", 0) or 0) if ex.preset_params else 0
                            load = sets * reps * (rpe / 10.0) * 10 + weight * sets * 0.5
                            total_load += load

                            pe = PlannedExercise(
                                planned_session_id=session.id,
                                exercise_id=ex.id,
                                order_index=i,
                                target_weight_kg=weight if weight > 0 else None,
                                target_reps=reps,
                                target_sets=sets,
                                rest_seconds=ex.preset_params.get("rest_seconds", 60) if ex.preset_params else 60,
                                target_rpe=rpe,
                            )
                            db.add(pe)
                            await db.flush()

                            # Create exercise logs for past dates (linked to training log)
                            if cur_date < date.today():
                                tl_result = await db.execute(
                                    select(TrainingLog).where(
                                        TrainingLog.athlete_id == athlete.id,
                                        TrainingLog.training_date == cur_date,
                                    )
                                )
                                training_log = tl_result.scalar_one_or_none()
                                if training_log:
                                    # Random completion rate 70-110%
                                    comp_rate = rng.uniform(0.7, 1.1)
                                    actual_sets = max(1, round(sets * comp_rate))
                                    actual_reps = max(1, round(reps * comp_rate))
                                    actual_rpe = max(3, min(10, round(rpe * rng.uniform(0.8, 1.2))))
                                    actual_weight = round(weight * rng.uniform(0.9, 1.05), 1) if weight > 0 else None

                                    el = ExerciseLog(
                                        training_log_id=training_log.id,
                                        exercise_id=ex.id,
                                        order_index=i,
                                        actual_weight_kg=actual_weight,
                                        actual_reps=actual_reps,
                                        actual_sets=actual_sets,
                                        actual_rpe=actual_rpe,
                                        planned_exercise_id=pe.id,
                                    )
                                    db.add(el)
                                    total_exercise_logs += 1

                        session.planned_load = round(total_load, 2)
                        total_plans += 1

                cur_date += timedelta(days=1)

    await db.commit()

    total_created_sum = sum(total_created.values())
    total_skipped_sum = sum(total_skipped.values())

    logger.info(f"Data generation complete: {total_created_sum} created, {total_skipped_sum} skipped for {len(athletes)} athletes. Plans: {total_plans}, ExerciseLogs: {total_exercise_logs}")

    return {
        "status": "success",
        "athletes_processed": len(athletes),
        "date_range": f"{start_date} ~ {end_date}",
        "days_total": (end_date - start_date).days,
        "created": total_created,
        "skipped": total_skipped,
        "plans_generated": total_plans,
        "exercise_logs_linked": total_exercise_logs,
        "message": f"成功为 {len(athletes)} 名测试运动员生成了 {total_created_sum} 条数据（跳过 {total_skipped_sum} 条已存在记录）。训练计划: {total_plans} 个课次, 关联日志: {total_exercise_logs} 条",
    }
