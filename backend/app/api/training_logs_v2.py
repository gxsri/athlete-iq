"""
AthleteIQ - Enhanced Training Logs API v2
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from uuid import UUID
from typing import List, Optional

from app.database import get_db, logger
from app.models.athlete import Athlete, DailyMetric, TrainingAssignment
from app.schemas.schemas import DailyMetricResponse, DailyMetricUpdate, PlanVsActualResponse
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/training-logs", tags=["训练日志v2"])


@router.get("/{athlete_id}", response_model=List[DailyMetricResponse])
async def get_training_logs(
    athlete_id: UUID,
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    limit: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """获取运动员训练日志（含新字段：RPE、精力、肌肉酸痛、完成率等）"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    query = select(DailyMetric).where(DailyMetric.athlete_id == athlete_id)
    if start:
        query = query.where(DailyMetric.metric_date >= start)
    if end:
        query = query.where(DailyMetric.metric_date <= end)
    query = query.order_by(DailyMetric.metric_date.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{athlete_id}", response_model=DailyMetricResponse, status_code=201)
async def create_or_update_log(
    athlete_id: UUID,
    data: DailyMetricUpdate,
    db: AsyncSession = Depends(get_db),
):
    """创建或更新某天训练日志（upsert）"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    metric_date = data.metric_date or date.today()

    try:
        # Check existing
        existing = await db.execute(
            select(DailyMetric).where(
                DailyMetric.athlete_id == athlete_id,
                DailyMetric.metric_date == metric_date,
            )
        )
        metric = existing.scalar_one_or_none()

        if metric:
            # Update
            for field in ["training_load", "rpe", "energy_level", "fatigue", "sleep_quality",
                         "training_content", "technical_notes", "notes", "completion_rate",
                         "plan_vs_actual_diff", "injury_risk",
                         "smash_count_today", "arm_pain_vas", "leg_pain_vas",
                         "jump_landing_quality", "footwork_score"]:
                val = getattr(data, field, None)
                if val is not None:
                    setattr(metric, field, val)
            if data.muscle_soreness is not None:
                metric.muscle_soreness = data.muscle_soreness
            if data.media_urls is not None:
                metric.media_urls = data.media_urls
        else:
            metric = DailyMetric(
                athlete_id=athlete_id,
                metric_date=metric_date,
                training_load=data.training_load or 0,
                rpe=data.rpe,
                energy_level=data.energy_level,
                fatigue=data.fatigue or 0,
                sleep_quality=data.sleep_quality or 5.0,
                training_content=data.training_content,
                technical_notes=data.technical_notes,
                notes=data.notes,
                completion_rate=data.completion_rate,
                plan_vs_actual_diff=data.plan_vs_actual_diff,
                injury_risk=data.injury_risk or 0,
                muscle_soreness=data.muscle_soreness or {},
                media_urls=data.media_urls or [],
            )
            db.add(metric)

        await db.commit()
        await db.refresh(metric)
        logger.info(f"Training log saved for athlete {athlete_id} on {metric_date}")
        return metric

    except IntegrityError:
        raise HTTPException(status_code=409, detail="数据冲突")
    except Exception as e:
        logger.exception("Failed to save training log")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{athlete_id}/compare", response_model=PlanVsActualResponse)
async def compare_plan_vs_actual(
    athlete_id: UUID,
    compare_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """对比计划负荷与实际执行：从 assignments 获取计划，从 daily_metrics 获取实际"""
    # Get planned assignment for date
    assign_result = await db.execute(
        select(TrainingAssignment).where(
            TrainingAssignment.athlete_id == athlete_id,
            TrainingAssignment.scheduled_date == compare_date,
        )
    )
    assignment = assign_result.scalar_one_or_none()

    # Get actual log
    log_result = await db.execute(
        select(DailyMetric).where(
            DailyMetric.athlete_id == athlete_id,
            DailyMetric.metric_date == compare_date,
        )
    )
    actual = log_result.scalar_one_or_none()

    planned_load = 0
    if assignment and assignment.template_id:
        template = await db.get(TrainingTemplate, assignment.template_id)
        if template and template.content:
            planned_load = template.content.get("target_load", 0)
        if assignment.overrides and "target_load" in assignment.overrides:
            planned_load = assignment.overrides["target_load"]

    actual_load = actual.training_load if actual else 0

    if planned_load > 0:
        diff_pct = round(((actual_load - planned_load) / planned_load) * 100, 1)
    else:
        diff_pct = 0

    completion_rate = 0
    if actual and actual.completion_rate:
        completion_rate = actual.completion_rate
    elif planned_load > 0 and actual_load > 0:
        completion_rate = round(min(100, (actual_load / planned_load) * 100), 1)

    # Update the log with computed values
    if actual:
        actual.plan_vs_actual_diff = diff_pct
        actual.completion_rate = completion_rate
        if assignment:
            assignment.status = "completed" if completion_rate >= 70 else "missed"
            assignment.actual_log_id = actual.id
        await db.commit()

    return PlanVsActualResponse(
        scheduled_date=compare_date,
        planned_load=planned_load,
        actual_load=actual_load,
        diff_pct=diff_pct,
        completion_rate=completion_rate,
        status=assignment.status if assignment else "no_plan",
    )
