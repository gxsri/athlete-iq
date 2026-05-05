"""
AthleteIQ - 自动计划调整 API
当 ACWR 异常时，自动降低未来训练课次的计划负荷
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import (
    Athlete, PlannedSession, PlannedExercise, ComputedMetric,
)
from app.schemas.schemas import AutoAdjustRequest, AutoAdjustResponse, AdjustedSession
from app.core.acwr import ACWRCalculator, TrainingSession
from app.models.athlete import TrainingLog

router = APIRouter(prefix="/api/auto-adjust", tags=["自动调整"])


@router.get("/acwr/{athlete_id}")
async def get_acwr_status(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get current ACWR status and adjustment recommendation for an athlete."""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    # Get latest computed metric
    cm_result = await db.execute(
        select(ComputedMetric).where(
            ComputedMetric.athlete_id == athlete_id
        ).order_by(ComputedMetric.calc_date.desc()).limit(1)
    )
    latest = cm_result.scalar_one_or_none()

    # Get recent training logs for ACWR calculation
    end_date = date.today()
    start_date = end_date - timedelta(days=42)
    tl_result = await db.execute(
        select(TrainingLog).where(
            TrainingLog.athlete_id == athlete_id,
            TrainingLog.training_date >= start_date,
            TrainingLog.training_date <= end_date,
        ).order_by(TrainingLog.training_date.asc())
    )
    logs = tl_result.scalars().all()

    sessions = [
        TrainingSession(date=log.training_date, session_load=log.session_load or 0,
                       training_type=log.training_type or "")
        for log in logs
    ]

    calc = ACWRCalculator(acute_window=7, chronic_window=28)
    results = calc.calculate_timeseries(sessions)
    latest_acwr_result = results[-1] if results else None

    current_acwr = float(latest_acwr_result.acwr) if latest_acwr_result else (float(latest.acwr) if latest else 0.0)
    acute_load = float(latest_acwr_result.acute_load) if latest_acwr_result else 0.0
    chronic_load = float(latest_acwr_result.chronic_load) if latest_acwr_result else 0.0
    risk_zone = str(latest_acwr_result.risk_zone) if latest_acwr_result else "安全区"

    needs_adjustment = bool(current_acwr > 1.3 or current_acwr < 0.8)
    suggestion = ""
    adjustment_pct = 0

    if current_acwr > 1.5:
        suggestion = f"ACWR={current_acwr:.2f} 处于高风险区，建议降低明日及未来计划负荷 25-30%"
        adjustment_pct = -25
    elif current_acwr > 1.3:
        suggestion = f"ACWR={current_acwr:.2f} 处于谨慎区，建议降低明日及未来计划负荷 15-20%"
        adjustment_pct = -15
    elif current_acwr < 0.8:
        suggestion = f"ACWR={current_acwr:.2f} 偏低，训练负荷可能不足，可适度增加 10-15%"
        adjustment_pct = 10
    else:
        suggestion = f"ACWR={current_acwr:.2f} 处于安全区，无需调整"

    # Count future planned sessions
    tomorrow = date.today() + timedelta(days=1)
    future_result = await db.execute(
        select(PlannedSession).where(
            PlannedSession.athlete_id == athlete_id,
            PlannedSession.plan_date >= tomorrow,
            PlannedSession.status == "scheduled",
        )
    )
    future_sessions = future_result.scalars().all()

    return {
        "athlete_id": str(athlete_id),
        "athlete_name": athlete.name,
        "current_acwr": round(current_acwr, 2),
        "acute_load_7d": round(acute_load, 1),
        "chronic_load_28d": round(chronic_load, 1),
        "risk_zone": risk_zone,
        "needs_adjustment": needs_adjustment,
        "suggestion": suggestion,
        "recommended_adjustment_pct": adjustment_pct,
        "future_sessions_count": len(future_sessions),
        "future_total_planned_load": sum(s.planned_load or 0 for s in future_sessions),
    }


@router.post("/plan/{athlete_id}", response_model=AutoAdjustResponse)
async def auto_adjust_plan(
    athlete_id: UUID,
    data: AutoAdjustRequest,
    db: AsyncSession = Depends(get_db),
):
    """Auto-adjust future planned sessions by a given factor.
    Reduces sets/reps/rpe proportionally and recalculates planned_load.
    """
    try:
        athlete = await db.get(Athlete, athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        # Find all future scheduled sessions
        tomorrow = date.today() + timedelta(days=1)
        result = await db.execute(
            select(PlannedSession).where(
                PlannedSession.athlete_id == athlete_id,
                PlannedSession.plan_date >= tomorrow,
                PlannedSession.status == "scheduled",
            ).order_by(PlannedSession.plan_date.asc())
        )
        sessions = result.scalars().all()

        if not sessions:
            return AutoAdjustResponse(
                athlete_id=athlete_id,
                adjustment_factor=data.adjustment_factor,
                sessions_adjusted=0,
                details=[],
                summary="没有找到未来的计划课次需要调整",
            )

        # Apply adjustment as a load multiplier (not per-parameter compounding)
        load_factor = 1 + (data.adjustment_factor / 100.0)  # e.g., -20% → 0.8
        details = []

        for session in sessions:
            original_load = session.planned_load or 0

            # Get planned exercises
            pe_result = await db.execute(
                select(PlannedExercise).where(
                    PlannedExercise.planned_session_id == session.id
                ).order_by(PlannedExercise.order_index)
            )
            exercises = pe_result.scalars().all()

            new_total_load = 0.0
            for pe in exercises:
                s = pe.target_sets or 0
                r = pe.target_reps or 0
                rpe = pe.target_rpe or 5
                w = pe.target_weight_kg or 0

                # Calculate current exercise load
                current_ex_load = s * r * (rpe / 10.0) * 10 + w * s * 0.5

                # Target load after adjustment
                target_ex_load = max(10, round(current_ex_load * load_factor))

                # Only adjust sets to hit target (simplest approach, keeps reps/RPE realistic)
                if s > 1 and current_ex_load > 0:
                    # Back-solve: new_sets = target_load / (r * (rpe/10) * 10 + w * 0.5)
                    per_set_load = r * (rpe / 10.0) * 10 + w * 0.5
                    if per_set_load > 0:
                        new_sets = max(1, round(target_ex_load / per_set_load))
                        pe.target_sets = new_sets

                # Recalculate
                s2 = pe.target_sets or 0
                load = s2 * r * (rpe / 10.0) * 10 + w * s2 * 0.5
                new_total_load += load

            session.planned_load = round(new_total_load, 2)
            change = round(((new_total_load - original_load) / original_load * 100), 1) if original_load > 0 else 0

            details.append(AdjustedSession(
                session_id=session.id,
                plan_date=session.plan_date,
                original_load=original_load,
                adjusted_load=round(new_total_load, 2),
                change_pct=change,
            ))

        await db.commit()
        logger.info(
            f"Auto-adjusted {len(details)} sessions for athlete {athlete_id}, "
            f"factor={data.adjustment_factor}%"
        )

        return AutoAdjustResponse(
            athlete_id=athlete_id,
            adjustment_factor=data.adjustment_factor,
            sessions_adjusted=len(details),
            details=details,
            summary=f"已调整 {len(details)} 个未来课次，负荷变化 {data.adjustment_factor}%"
                    + (f"，原因: {data.reason}" if data.reason else ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to auto-adjust plan for athlete {athlete_id}")
        raise HTTPException(status_code=500, detail=f"自动调整失败: {str(e)[:200]}")
