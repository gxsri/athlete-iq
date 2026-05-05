"""
AthleteIQ - 运动员管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import Athlete, AthleteBaseline, AlertEvent, InjuryRecord
from app.schemas.schemas import (
    AthleteCreate, AthleteResponse, AthleteUpdate, AthleteBaselineCreate,
)
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/athletes", tags=["运动员管理"])


@router.post("/", response_model=AthleteResponse, status_code=201)
async def create_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    """注册新运动员"""
    try:
        db_athlete = Athlete(**athlete.model_dump())
        db.add(db_athlete)
        await db.commit()
        await db.refresh(db_athlete)
        logger.info(f"Created athlete {db_athlete.id}: {db_athlete.name}")
        return db_athlete
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating athlete: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create athlete")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/", response_model=List[AthleteResponse])
async def list_athletes(
    sport: str = Query(None, description="按运动项目筛选"),
    status: str = Query(None, description="状态筛选: active/injured/alert/all"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """获取运动员列表"""
    if status and status != "all":
        if status == "injured":
            injured_result = await db.execute(
                select(InjuryRecord.athlete_id).where(
                    InjuryRecord.status.in_(["活跃", "康复中"])
                )
            )
            injured_ids = {row[0] for row in injured_result.fetchall()}
            if not injured_ids:
                return []
            query = select(Athlete).where(Athlete.id.in_(injured_ids))
        elif status == "alert":
            alert_result = await db.execute(
                select(AlertEvent.athlete_id).where(
                    AlertEvent.is_resolved == False
                )
            )
            alert_ids = {row[0] for row in alert_result.fetchall()}
            if not alert_ids:
                return []
            query = select(Athlete).where(Athlete.id.in_(alert_ids))
        elif status == "active":
            injured_result = await db.execute(
                select(InjuryRecord.athlete_id).where(
                    InjuryRecord.status.in_(["活跃", "康复中"])
                )
            )
            injured_ids = {row[0] for row in injured_result.fetchall()}
            if injured_ids:
                query = select(Athlete).where(Athlete.id.notin_(injured_ids))
            else:
                query = select(Athlete)
        else:
            query = select(Athlete)
    else:
        query = select(Athlete)

    if sport:
        query = query.where(Athlete.sport == sport)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{athlete_id}", response_model=AthleteResponse)
async def get_athlete(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取运动员详情"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")
    return athlete


@router.put("/{athlete_id}", response_model=AthleteResponse)
async def update_athlete(
    athlete_id: UUID,
    update_data: AthleteUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新运动员信息"""
    try:
        athlete = await db.get(Athlete, athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(athlete, key, value)

        await db.commit()
        await db.refresh(athlete)
        logger.info(f"Updated athlete {athlete_id}")
        return athlete
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating athlete {athlete_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update athlete {athlete_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/{athlete_id}/baseline", status_code=201)
async def set_baseline(
    athlete_id: UUID,
    baseline: AthleteBaselineCreate,
    db: AsyncSession = Depends(get_db),
):
    """设置运动员个人基准值"""
    try:
        athlete = await db.get(Athlete, athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        db_baseline = AthleteBaseline(**baseline.model_dump())
        db.add(db_baseline)
        await db.commit()
        await db.refresh(db_baseline)
        logger.info(f"Set baseline {db_baseline.id} for athlete {athlete_id}")
        return db_baseline
    except IntegrityError as e:
        logger.warning(f"IntegrityError setting baseline: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to set baseline for athlete {athlete_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/{athlete_id}/baselines")
async def get_baselines(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取运动员所有基准值"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    result = await db.execute(
        select(AthleteBaseline).where(AthleteBaseline.athlete_id == athlete_id)
    )
    return result.scalars().all()
