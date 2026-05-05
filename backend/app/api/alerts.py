"""
AthleteIQ - 预警中心 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import AlertEvent, Athlete
from app.schemas.schemas import AlertResponse, AlertUpdate
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/alerts", tags=["预警中心"])


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    athlete_id: UUID = Query(None),
    severity: str = Query(None, description="低/中/高/严重"),
    is_resolved: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """获取预警列表"""
    query = select(AlertEvent)

    if athlete_id:
        query = query.where(AlertEvent.athlete_id == athlete_id)
    if severity:
        query = query.where(AlertEvent.severity == severity)
    if is_resolved is not None:
        query = query.where(AlertEvent.is_resolved == is_resolved)

    query = query.order_by(AlertEvent.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/unread-count")
async def get_unread_alert_count(
    coach_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取未读预警数量"""
    query = select(func.count(AlertEvent.id)).where(
        AlertEvent.is_read == False,
        AlertEvent.is_resolved == False,
    )
    result = await db.execute(query)
    count = result.scalar()
    return {"unread_count": count}


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    update: AlertUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新预警状态（已读/已解决/添加教练备注）"""
    try:
        alert = await db.get(AlertEvent, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="预警不存在")

        if update.is_read is not None:
            alert.is_read = update.is_read
        if update.is_resolved is not None:
            alert.is_resolved = update.is_resolved
        if update.coach_notes is not None:
            alert.coach_notes = update.coach_notes

        await db.commit()
        await db.refresh(alert)
        logger.info(f"Updated alert {alert_id}")
        return alert
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating alert {alert_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update alert {alert_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    coach_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """快速解决预警"""
    try:
        alert = await db.get(AlertEvent, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="预警不存在")

        alert.is_resolved = True
        alert.coach_notes = coach_notes
        await db.commit()
        logger.info(f"Resolved alert {alert_id}")
        return {"status": "resolved", "alert_id": str(alert_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to resolve alert {alert_id}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)[:200]}")
