"""
AthleteIQ - Wellness Trends API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from uuid import UUID

from app.database import get_db
from app.models.athlete import WellnessQuestionnaire, Athlete

router = APIRouter(prefix="/api/wellness", tags=["健康趋势"])


@router.get("/{athlete_id}/trends")
async def get_wellness_trends(
    athlete_id: UUID,
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get wellness questionnaire trends (morning HR, HRV, sleep) for an athlete."""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(WellnessQuestionnaire)
        .where(
            WellnessQuestionnaire.athlete_id == athlete_id,
            WellnessQuestionnaire.record_date >= start_date,
        )
        .order_by(WellnessQuestionnaire.record_date.asc())
    )
    records = result.scalars().all()

    trends = [
        {
            "date": str(r.record_date),
            "morning_heart_rate": r.morning_heart_rate,
            "hrv_lnrmssd": float(r.hrv_lnrmssd) if r.hrv_lnrmssd else None,
            "sleep_duration_hours": float(r.sleep_duration_hours) if r.sleep_duration_hours else None,
            "sleep_quality": r.sleep_quality,
            "fatigue_score": r.fatigue_score,
        }
        for r in records
    ]

    return {
        "athlete_id": str(athlete_id),
        "days": days,
        "trends": trends,
    }
