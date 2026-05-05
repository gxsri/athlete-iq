"""
AthleteIQ - Recovery Module API
Generate personalized recovery suggestions based on daily metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from uuid import UUID
from typing import List

from app.database import get_db, logger
from app.models.athlete import Athlete, DailyMetric, RecoverySuggestion
from app.schemas.schemas import RecoverySuggestionResponse
from app.core.risk_engine import generate_recovery_suggestions, compute_all_risks

router = APIRouter(prefix="/api/recovery", tags=["恢复建议"])


@router.get("/today/{athlete_id}", response_model=RecoverySuggestionResponse)
async def get_today_recovery(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取今日恢复建议。如果今天已有则返回已有，否则自动生成并保存。"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    today = date.today()

    # Check existing suggestion for today
    existing = await db.execute(
        select(RecoverySuggestion).where(
            RecoverySuggestion.athlete_id == athlete_id,
            RecoverySuggestion.date == today,
        )
    )
    suggestion = existing.scalar_one_or_none()
    if suggestion:
        return suggestion

    # Get today's daily metrics
    metric_result = await db.execute(
        select(DailyMetric).where(
            DailyMetric.athlete_id == athlete_id,
            DailyMetric.metric_date == today,
        )
    )
    metric = metric_result.scalar_one_or_none()

    if not metric:
        raise HTTPException(status_code=404, detail="今日暂无身体数据，请先录入")

    # Recalculate risks from current data
    risks = compute_all_risks(
        smash_7d_avg=metric.smash_7d_avg or 0,
        overhead_week_total=metric.overhead_week_total or 0,
        external_rotation_ratio=metric.external_rotation_ratio or 0.7,
        sleep_hours=metric.sleep_quality or 7,
        today_smash=metric.smash_count_today or 0,
        max_smash_30d=metric.max_smash_30d or 0,
        global_fatigue=metric.fatigue or 50,
        reaction_time_ms=metric.reaction_time_ms or 250,
        total_impacts_7d=metric.total_impacts_7d or 0,
        jump_landing_quality=metric.jump_landing_quality or 7,
        quad_hamstring_ratio=metric.quad_hamstring_ratio or 0.8,
        has_knee_pain_history=metric.has_knee_pain_history or False,
        footwork_score=metric.footwork_score or 7,
    )

    # Update metric with computed risks
    for key, value in risks.items():
        setattr(metric, key, value)
    await db.commit()

    # Generate recovery exercises
    exercises = generate_recovery_suggestions(metric)
    suggestion_text = "基于今日身体数据的个性化恢复方案"

    rec = RecoverySuggestion(
        athlete_id=athlete_id,
        date=today,
        suggestion_text=suggestion_text,
        exercises=exercises,
        status="pending",
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    logger.info(f"Generated recovery for athlete {athlete_id}")
    return rec


@router.post("/complete/{suggestion_id}")
async def complete_suggestion(
    suggestion_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """标记恢复建议为已完成"""
    suggestion = await db.get(RecoverySuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="恢复建议不存在")

    suggestion.status = "completed"
    suggestion.completed_at = date.today()
    await db.commit()
    return {"status": "completed", "suggestion_id": str(suggestion_id)}


@router.get("/history/{athlete_id}", response_model=List[RecoverySuggestionResponse])
async def get_recovery_history(
    athlete_id: UUID,
    limit: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """获取历史恢复建议"""
    result = await db.execute(
        select(RecoverySuggestion)
        .where(RecoverySuggestion.athlete_id == athlete_id)
        .order_by(RecoverySuggestion.date.desc())
        .limit(limit)
    )
    return result.scalars().all()
