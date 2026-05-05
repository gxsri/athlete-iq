"""
AthleteIQ - 训练计划管理 API (增强版: 计划负荷计算 / 计划vs实际对比 / 批量生成)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import (
    Athlete, PlannedSession, PlannedExercise,
    ExerciseLibrary, ExerciseLog, TrainingLog, DailyMetric,
)
from app.schemas.schemas import (
    PlannedSessionCreate, PlannedSessionResponse,
    PlannedExerciseCreate, PlannedExerciseResponse,
    ExerciseLogCreate, ExerciseLogResponse,
    AssignSessionRequest, SessionDeviationResponse,
    SessionPlanVsActualResponse, ExercisePlanVsActual,
    BatchSessionCreate, WeekPlanResponse,
)
from app.core.deviation import calculate_deviation, calculate_exercise_load
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/planner", tags=["训练计划"])


def _calc_planned_load(exercises: list) -> float:
    """Calculate planned load from exercise list.
    Formula: Σ(sets * reps * (planned_rpe/10) * 10)
    Simplified model that accounts for volume and intensity.
    """
    total = 0.0
    for ex in exercises:
        sets = getattr(ex, 'target_sets', None) or 0
        reps = getattr(ex, 'target_reps', None) or 0
        rpe = getattr(ex, 'target_rpe', None) or 5
        weight = getattr(ex, 'target_weight_kg', None) or 0
        # Load = volume * intensity_factor * weight_factor
        volume = sets * reps
        intensity = rpe / 10.0
        load = volume * intensity * 10 + weight * sets * 0.5
        total += load
    return round(total, 2)


@router.post("/sessions", response_model=PlannedSessionResponse, status_code=201)
async def create_planned_session(data: PlannedSessionCreate, db: AsyncSession = Depends(get_db)):
    try:
        athlete = await db.get(Athlete, data.athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        # Calculate planned load
        planned_load = _calc_planned_load(data.exercises)

        session = PlannedSession(
            athlete_id=data.athlete_id,
            plan_date=data.plan_date,
            session_name=data.session_name,
            training_type=data.training_type,
            notes=data.notes,
            planned_load=planned_load,
            status="scheduled",
        )
        db.add(session)
        await db.flush()

        for ex_data in data.exercises:
            planned_ex = PlannedExercise(
                planned_session_id=session.id,
                exercise_id=ex_data.exercise_id,
                order_index=ex_data.order_index,
                target_weight_kg=ex_data.target_weight_kg,
                target_reps=ex_data.target_reps,
                target_sets=ex_data.target_sets,
                rest_seconds=ex_data.rest_seconds,
                target_rpe=ex_data.target_rpe,
                notes=ex_data.notes,
            )
            db.add(planned_ex)

        await db.commit()
        await db.refresh(session)
        logger.info(f"Created planned session {session.id} for athlete {data.athlete_id}, load={planned_load}")
        return await _load_session_with_exercises(session.id, db)
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating planned session: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create planned session")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/sessions/batch-create", status_code=201)
async def batch_create_sessions(data: BatchSessionCreate, db: AsyncSession = Depends(get_db)):
    """Batch create sessions for a date range on specified weekdays."""
    try:
        athlete = await db.get(Athlete, data.athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        planned_load = _calc_planned_load(data.exercises)
        created = []
        current = data.start_date
        while current <= data.end_date:
            if current.weekday() in data.weekdays:
                session = PlannedSession(
                    athlete_id=data.athlete_id,
                    plan_date=current,
                    session_name=data.session_name or f"训练课 {current}",
                    training_type=data.training_type or "混合",
                    notes=data.notes,
                    planned_load=planned_load,
                    status="scheduled",
                )
                db.add(session)
                await db.flush()

                for i, ex_data in enumerate(data.exercises):
                    planned_ex = PlannedExercise(
                        planned_session_id=session.id,
                        exercise_id=ex_data.exercise_id,
                        order_index=i,
                        target_weight_kg=ex_data.target_weight_kg,
                        target_reps=ex_data.target_reps,
                        target_sets=ex_data.target_sets,
                        rest_seconds=ex_data.rest_seconds,
                        target_rpe=ex_data.target_rpe,
                        notes=ex_data.notes,
                    )
                    db.add(planned_ex)
                created.append(str(session.id))
            current += timedelta(days=1)

        await db.commit()
        logger.info(f"Batch created {len(created)} sessions for athlete {data.athlete_id}")
        return {"sessions_created": len(created), "session_ids": created}
    except IntegrityError as e:
        logger.warning(f"IntegrityError in batch create: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Batch create failed")
        raise HTTPException(status_code=500, detail=f"批量创建失败: {str(e)[:200]}")


@router.get("/sessions", response_model=List[PlannedSessionResponse])
async def list_planned_sessions(
    athlete_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(PlannedSession)
    if athlete_id:
        query = query.where(PlannedSession.athlete_id == athlete_id)
    if start_date:
        query = query.where(PlannedSession.plan_date >= start_date)
    if end_date:
        query = query.where(PlannedSession.plan_date <= end_date)
    if status:
        query = query.where(PlannedSession.status == status)
    query = query.order_by(PlannedSession.plan_date.asc()).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()

    responses = []
    for s in sessions:
        responses.append(await _load_session_with_exercises(s.id, db))
    return responses


@router.get("/sessions/week", response_model=WeekPlanResponse)
async def get_week_plan(
    athlete_id: UUID = Query(...),
    week_start: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get a full week plan for an athlete with day-by-day sessions."""
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    result = await db.execute(
        select(PlannedSession).where(
            PlannedSession.athlete_id == athlete_id,
            PlannedSession.plan_date >= week_start,
            PlannedSession.plan_date <= week_end,
        ).order_by(PlannedSession.plan_date.asc())
    )
    sessions = result.scalars().all()

    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_sessions = [s for s in sessions if s.plan_date == d]
        days.append({
            "date": str(d),
            "day_name": day_names[i],
            "is_today": d == date.today(),
            "sessions": [
                {
                    "id": str(s.id),
                    "session_name": s.session_name,
                    "training_type": s.training_type,
                    "planned_load": s.planned_load or 0,
                    "status": s.status or "scheduled",
                }
                for s in day_sessions
            ],
        })

    return WeekPlanResponse(week_start=week_start, week_end=week_end, days=days)


@router.get("/sessions/{session_id}", response_model=PlannedSessionResponse)
async def get_session_detail(session_id: UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(PlannedSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="训练计划不存在")
    return await _load_session_with_exercises(session_id, db)


@router.put("/sessions/{session_id}", response_model=PlannedSessionResponse)
async def update_session(
    session_id: UUID,
    data: PlannedSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await db.get(PlannedSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="训练计划不存在")

        session.plan_date = data.plan_date
        session.session_name = data.session_name
        session.training_type = data.training_type
        session.notes = data.notes
        session.planned_load = _calc_planned_load(data.exercises)

        old_exercises = await db.execute(
            select(PlannedExercise).where(PlannedExercise.planned_session_id == session_id)
        )
        for old in old_exercises.scalars().all():
            await db.delete(old)

        for ex_data in data.exercises:
            planned_ex = PlannedExercise(
                planned_session_id=session.id,
                exercise_id=ex_data.exercise_id,
                order_index=ex_data.order_index,
                target_weight_kg=ex_data.target_weight_kg,
                target_reps=ex_data.target_reps,
                target_sets=ex_data.target_sets,
                rest_seconds=ex_data.rest_seconds,
                target_rpe=ex_data.target_rpe,
                notes=ex_data.notes,
            )
            db.add(planned_ex)

        await db.commit()
        await db.refresh(session)
        logger.info(f"Updated planned session {session_id}, load={session.planned_load}")
        return await _load_session_with_exercises(session.id, db)
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating planned session {session_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update planned session {session_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        session = await db.get(PlannedSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="训练计划不存在")
        await db.delete(session)
        await db.commit()
        logger.info(f"Deleted planned session {session_id}")
        return {"status": "deleted", "session_id": str(session_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete planned session {session_id}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)[:200]}")


@router.post("/sessions/{session_id}/assign")
async def assign_session_to_athletes(
    session_id: UUID,
    data: AssignSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        original = await db.get(PlannedSession, session_id)
        if not original:
            raise HTTPException(status_code=404, detail="训练计划不存在")

        existing_exercises = await db.execute(
            select(PlannedExercise).where(PlannedExercise.planned_session_id == session_id)
        )
        original_exercises = existing_exercises.scalars().all()

        created_sessions = []
        for athlete_id in data.athlete_ids:
            if athlete_id == original.athlete_id:
                continue
            athlete = await db.get(Athlete, athlete_id)
            if not athlete:
                continue

            new_session = PlannedSession(
                athlete_id=athlete_id,
                plan_date=original.plan_date,
                created_by=original.created_by,
                session_name=original.session_name,
                training_type=original.training_type,
                notes=original.notes,
                planned_load=original.planned_load,
            )
            db.add(new_session)
            await db.flush()

            for old_ex in original_exercises:
                new_ex = PlannedExercise(
                    planned_session_id=new_session.id,
                    exercise_id=old_ex.exercise_id,
                    order_index=old_ex.order_index,
                    target_weight_kg=old_ex.target_weight_kg,
                    target_reps=old_ex.target_reps,
                    target_sets=old_ex.target_sets,
                    rest_seconds=old_ex.rest_seconds,
                    target_rpe=old_ex.target_rpe,
                    notes=old_ex.notes,
                )
                db.add(new_ex)

            created_sessions.append(str(new_session.id))

        await db.commit()
        logger.info(f"Assigned session {session_id} to {len(created_sessions)} athletes")
        return {"assigned_to": len(created_sessions), "session_ids": created_sessions}
    except IntegrityError as e:
        logger.warning(f"IntegrityError assigning session {session_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to assign session {session_id}")
        raise HTTPException(status_code=500, detail=f"分配失败: {str(e)[:200]}")


@router.get("/athlete/{athlete_id}/today")
async def get_todays_plan(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    today = date.today()
    result = await db.execute(
        select(PlannedSession).where(
            PlannedSession.athlete_id == athlete_id,
            PlannedSession.plan_date == today,
        )
    )
    sessions = result.scalars().all()

    responses = []
    for s in sessions:
        resp = await _load_session_with_exercises(s.id, db)
        # Include exercise names from library
        ex_details = []
        for pe_resp in resp.exercises:
            ex = await db.get(ExerciseLibrary, pe_resp.exercise_id)
            ex_details.append({
                "planned_exercise_id": str(pe_resp.id),
                "exercise_id": str(pe_resp.exercise_id),
                "exercise_name": ex.name if ex else "未知动作",
                "category": ex.category if ex else "",
                "target_sets": pe_resp.target_sets,
                "target_reps": pe_resp.target_reps,
                "target_rpe": pe_resp.target_rpe,
                "target_weight_kg": pe_resp.target_weight_kg,
                "rest_seconds": pe_resp.rest_seconds,
                "order_index": pe_resp.order_index,
            })
        responses.append({
            "session_id": str(resp.id),
            "session_name": resp.session_name,
            "training_type": resp.training_type,
            "planned_load": resp.planned_load,
            "status": resp.status,
            "exercises": ex_details,
        })

    return {
        "athlete_id": str(athlete_id),
        "date": str(today),
        "sessions_count": len(responses),
        "sessions": responses,
    }


@router.get("/sessions/{session_id}/plan-vs-actual", response_model=SessionPlanVsActualResponse)
async def get_plan_vs_actual(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Compare planned session exercises against actual exercise logs."""
    session = await db.get(PlannedSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="训练计划不存在")

    # Get planned exercises
    pe_result = await db.execute(
        select(PlannedExercise).where(
            PlannedExercise.planned_session_id == session_id
        ).order_by(PlannedExercise.order_index)
    )
    planned_exs = pe_result.scalars().all()

    # Get actual exercise logs linked to these planned exercises
    actual_load_total = 0.0
    exercise_comparisons = []

    for pe in planned_exs:
        # Find exercise logs linked to this planned exercise
        el_result = await db.execute(
            select(ExerciseLog).where(
                ExerciseLog.planned_exercise_id == pe.id
            ).order_by(ExerciseLog.order_index)
        )
        exercise_logs = el_result.scalars().all()

        # Get exercise name
        ex_lib = await db.get(ExerciseLibrary, pe.exercise_id)
        ex_name = ex_lib.name if ex_lib else "未知动作"

        planned_load = calculate_exercise_load(
            pe.target_weight_kg or 0, pe.target_reps or 0, pe.target_sets or 0, pe.target_rpe or 5
        )
        actual_load = 0.0
        actual_sets = 0
        actual_reps = 0
        actual_rpe = None
        actual_weight = None

        for el in exercise_logs:
            a_load = calculate_exercise_load(
                el.actual_weight_kg or 0, el.actual_reps or 0, el.actual_sets or 0, el.actual_rpe or pe.target_rpe or 5
            )
            actual_load += a_load
            actual_sets += el.actual_sets or 0
            actual_reps += el.actual_reps or 0
            if el.actual_rpe:
                actual_rpe = el.actual_rpe
            if el.actual_weight_kg:
                actual_weight = el.actual_weight_kg

        actual_load_total += actual_load
        completion_pct = round((actual_load / planned_load * 100), 1) if planned_load > 0 else 0

        exercise_comparisons.append(ExercisePlanVsActual(
            exercise_id=pe.exercise_id,
            exercise_name=ex_name,
            planned_sets=pe.target_sets,
            planned_reps=pe.target_reps,
            planned_rpe=pe.target_rpe,
            planned_weight=pe.target_weight_kg,
            actual_sets=actual_sets if actual_sets > 0 else None,
            actual_reps=actual_reps if actual_reps > 0 else None,
            actual_rpe=actual_rpe,
            actual_weight=actual_weight,
            planned_load=round(planned_load, 2),
            actual_load=round(actual_load, 2),
            completion_pct=completion_pct,
        ))

    total_planned = session.planned_load or 0
    deviation = round(((actual_load_total - total_planned) / total_planned * 100), 1) if total_planned > 0 else 0
    completion_rate = round((actual_load_total / total_planned * 100), 1) if total_planned > 0 else 0

    return SessionPlanVsActualResponse(
        session_id=session.id,
        session_name=session.session_name,
        plan_date=session.plan_date,
        planned_load=total_planned,
        actual_load=round(actual_load_total, 2),
        deviation_pct=deviation,
        completion_rate=completion_rate,
        exercises=exercise_comparisons,
    )


@router.post("/sessions/{session_id}/log-exercise")
async def log_exercise_for_plan(
    session_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Log actual completion for a single planned exercise.
    Creates a TrainingLog if one doesn't exist for this date, then creates an ExerciseLog.
    """
    try:
        session = await db.get(PlannedSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="训练计划不存在")

        planned_exercise_id = data.get("planned_exercise_id")
        pe = await db.get(PlannedExercise, planned_exercise_id)
        if not pe:
            raise HTTPException(status_code=404, detail="计划动作不存在")

        # Find or create a TrainingLog for this date
        tl_result = await db.execute(
            select(TrainingLog).where(
                TrainingLog.athlete_id == session.athlete_id,
                TrainingLog.training_date == session.plan_date,
            )
        )
        training_log = tl_result.scalar_one_or_none()

        if not training_log:
            # Calculate session load from the exercise
            ex_load = calculate_exercise_load(
                data.get("actual_weight_kg", 0) or 0,
                data.get("actual_reps_completed", 0) or 0,
                data.get("actual_sets_completed", 0) or 0,
                data.get("actual_rpe", 6) or 6,
            )
            training_log = TrainingLog(
                athlete_id=session.athlete_id,
                training_date=session.plan_date,
                duration_minutes=data.get("actual_duration_min", 30) or 30,
                rpe=data.get("actual_rpe", 6) or 6,
                training_type=session.training_type or "混合",
                session_load=ex_load,
                description=f"执行计划: {session.session_name or '训练课'}",
                source="planner",
            )
            db.add(training_log)
            await db.flush()

        # Create the exercise log
        ex_log = ExerciseLog(
            training_log_id=training_log.id,
            exercise_id=pe.exercise_id,
            order_index=pe.order_index,
            actual_weight_kg=data.get("actual_weight_kg"),
            actual_reps=data.get("actual_reps_completed"),
            actual_sets=data.get("actual_sets_completed"),
            actual_rpe=data.get("actual_rpe"),
            planned_exercise_id=pe.id,
            notes=data.get("notes"),
        )
        db.add(ex_log)

        # Update session status to completed if all exercises logged
        all_pe_result = await db.execute(
            select(PlannedExercise).where(PlannedExercise.planned_session_id == session_id)
        )
        all_pe = all_pe_result.scalars().all()

        logged_result = await db.execute(
            select(ExerciseLog).where(
                ExerciseLog.planned_exercise_id.in_([p.id for p in all_pe])
            )
        )
        logged_count = len(logged_result.scalars().all())

        if logged_count >= len(all_pe):
            session.status = "completed"

        await db.commit()
        logger.info(f"Logged exercise {pe.id} for session {session_id}")
        return {"status": "logged", "exercise_log_id": str(ex_log.id), "training_log_id": str(training_log.id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to log exercise for session {session_id}")
        raise HTTPException(status_code=500, detail=f"记录失败: {str(e)[:200]}")


@router.post("/sessions/{session_id}/complete")
async def complete_planned_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await db.get(PlannedSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="训练计划不存在")

        existing_exercises = await db.execute(
            select(PlannedExercise).where(PlannedExercise.planned_session_id == session_id)
        )
        planned_exs = existing_exercises.scalars().all()

        if not planned_exs:
            raise HTTPException(status_code=400, detail="该计划没有练习内容")

        session_load = 0
        for pe in planned_exs:
            load = calculate_exercise_load(
                pe.target_weight_kg or 0,
                pe.target_reps or 0,
                pe.target_sets or 0,
                pe.target_rpe or 7,
            )
            session_load += load

        training_log = TrainingLog(
            athlete_id=session.athlete_id,
            training_date=session.plan_date,
            duration_minutes=max(30, len(planned_exs) * 10),
            rpe=7,
            training_type=session.training_type or "混合",
            session_load=session_load,
            description=f"完成计划: {session.session_name or '训练课'}",
            source="planner",
        )
        db.add(training_log)
        await db.flush()

        exercise_logs_created = []
        for pe in planned_exs:
            ex_log = ExerciseLog(
                training_log_id=training_log.id,
                exercise_id=pe.exercise_id,
                order_index=pe.order_index,
                actual_weight_kg=pe.target_weight_kg,
                actual_reps=pe.target_reps,
                actual_sets=pe.target_sets,
                actual_rpe=pe.target_rpe,
                planned_exercise_id=pe.id,
            )
            db.add(ex_log)
            exercise_logs_created.append(str(pe.id))

        session.status = "completed"

        await db.commit()
        logger.info(f"Completed planned session {session_id}")
        return {
            "status": "completed",
            "training_log_id": str(training_log.id),
            "exercises_logged": len(exercise_logs_created),
        }
    except IntegrityError as e:
        logger.warning(f"IntegrityError completing session {session_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to complete session {session_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/athlete/{athlete_id}/plan-vs-actual-trend")
async def get_plan_vs_actual_trend(
    athlete_id: UUID,
    days: int = Query(30, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
):
    """Get daily planned load vs actual load trend for charting."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get all planned sessions in range
    ps_result = await db.execute(
        select(PlannedSession).where(
            PlannedSession.athlete_id == athlete_id,
            PlannedSession.plan_date >= start_date,
            PlannedSession.plan_date <= end_date,
        ).order_by(PlannedSession.plan_date.asc())
    )
    sessions = ps_result.scalars().all()

    # Get all training logs in range
    tl_result = await db.execute(
        select(TrainingLog).where(
            TrainingLog.athlete_id == athlete_id,
            TrainingLog.training_date >= start_date,
            TrainingLog.training_date <= end_date,
        ).order_by(TrainingLog.training_date.asc())
    )
    training_logs = tl_result.scalars().all()

    # Build daily map
    daily_data = {}
    current = start_date
    while current <= end_date:
        daily_data[str(current)] = {"date": str(current), "planned_load": 0, "actual_load": 0, "completion_rate": 0}
        current += timedelta(days=1)

    for s in sessions:
        ds = str(s.plan_date)
        if ds in daily_data:
            daily_data[ds]["planned_load"] += s.planned_load or 0

    for tl in training_logs:
        ds = str(tl.training_date)
        if ds in daily_data:
            daily_data[ds]["actual_load"] += tl.session_load or 0

    # Calculate completion rates
    trend = []
    for entry in daily_data.values():
        if entry["planned_load"] > 0:
            entry["completion_rate"] = round(entry["actual_load"] / entry["planned_load"] * 100, 1)
        trend.append(entry)

    return {
        "athlete_id": str(athlete_id),
        "days": days,
        "trend": trend,
    }


async def _load_session_with_exercises(session_id: UUID, db: AsyncSession):
    session = await db.get(PlannedSession, session_id)
    if not session:
        return None

    ex_result = await db.execute(
        select(PlannedExercise)
        .where(PlannedExercise.planned_session_id == session_id)
        .order_by(PlannedExercise.order_index)
    )
    exercises = ex_result.scalars().all()

    return PlannedSessionResponse(
        id=session.id,
        athlete_id=session.athlete_id,
        plan_date=session.plan_date,
        created_by=session.created_by,
        session_name=session.session_name,
        training_type=session.training_type,
        notes=session.notes,
        planned_load=session.planned_load,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        exercises=[
            PlannedExerciseResponse(
                id=e.id,
                planned_session_id=e.planned_session_id,
                exercise_id=e.exercise_id,
                order_index=e.order_index,
                target_weight_kg=e.target_weight_kg,
                target_reps=e.target_reps,
                target_sets=e.target_sets,
                rest_seconds=e.rest_seconds,
                target_rpe=e.target_rpe,
                notes=e.notes,
            )
            for e in exercises
        ],
    )
