"""
AthleteIQ - 每日准备度 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import DailyReadiness, Athlete
from app.schemas.schemas import DailyReadinessCreate, DailyReadinessResponse
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/readiness", tags=["每日准备度"])


@router.post("/", response_model=DailyReadinessResponse, status_code=201)
async def submit_readiness(data: DailyReadinessCreate, db: AsyncSession = Depends(get_db)):
    try:
        athlete = await db.get(Athlete, data.athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        existing = await db.execute(
            select(DailyReadiness).where(
                DailyReadiness.athlete_id == data.athlete_id,
                DailyReadiness.record_date == data.record_date,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="该日期已有准备度记录")

        db_readiness = DailyReadiness(**data.model_dump())
        db.add(db_readiness)
        await db.commit()
        await db.refresh(db_readiness)
        logger.info(f"Created readiness record {db_readiness.id} for athlete {data.athlete_id}")
        return db_readiness
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating readiness: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create readiness record")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/{athlete_id}", response_model=List[DailyReadinessResponse])
async def get_readiness_history(
    athlete_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    query = select(DailyReadiness).where(DailyReadiness.athlete_id == athlete_id)
    if start_date:
        query = query.where(DailyReadiness.record_date >= start_date)
    if end_date:
        query = query.where(DailyReadiness.record_date <= end_date)
    query = query.order_by(DailyReadiness.record_date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{athlete_id}/today")
async def get_today_readiness(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    today = date.today()
    result = await db.execute(
        select(DailyReadiness).where(
            DailyReadiness.athlete_id == athlete_id,
            DailyReadiness.record_date == today,
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        return {
            "athlete_id": str(athlete_id),
            "date": str(today),
            "has_entry": False,
            "readiness_color": "unknown",
            "message": "今日尚未提交准备度问卷",
        }

    return {
        "athlete_id": str(athlete_id),
        "date": str(entry.record_date),
        "has_entry": True,
        "readiness_color": entry.readiness_color,
        "sleep_quality": entry.sleep_quality,
        "muscle_soreness": entry.muscle_soreness,
        "fatigue_level": entry.fatigue_level,
        "stress_motivation": entry.stress_motivation,
        "discomfort_notes": entry.discomfort_notes,
    }
