"""
AthleteIQ - 营养监测 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import List
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import NutritionLog, Athlete
from app.schemas.schemas import NutritionLogCreate, NutritionLogResponse, NutritionRiskStatus
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/nutrition", tags=["营养监测"])

NUTRITION_TEMPLATES = {
    "\u5907\u8d5b\u671f": "\u6bcf\u65e5\u86cb\u767d\u8d28 1.6-2.0g/kg\u4f53\u91cd, \u8bad\u7ec3\u540e30\u5206\u949f\u5185\u8865\u5145\u78b3\u6c34+\u86cb\u767d, \u5168\u5929\u996e\u6c34 2.5-3.0L",
    "\u6bd4\u8d5b\u671f": "\u8d5b\u524d3\u5c0f\u65f6\u78b3\u6c34\u52a0\u8f7d, \u8d5b\u4e2d\u7535\u89e3\u8d28\u8865\u5145, \u8d5b\u540e\u7acb\u5373\u8865\u5145\u78b3\u6c34+\u86cb\u767d, \u996e\u6c34 3.0L+",
}


@router.get("/templates")
async def get_nutrition_templates():
    """获取营养指导模板"""
    return {"templates": NUTRITION_TEMPLATES}


@router.post("/", response_model=NutritionLogResponse, status_code=201)
async def create_nutrition_log(
    log: NutritionLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """提交每日营养记录"""
    try:
        athlete_id = log.athlete_id
        athlete = await db.get(Athlete, athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        existing = await db.execute(
            select(NutritionLog).where(
                NutritionLog.athlete_id == athlete_id,
                NutritionLog.log_date == log.log_date,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="该日期已有营养记录")

        db_log = NutritionLog(athlete_id=athlete_id, **log.model_dump())
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)
        logger.info(f"Created nutrition log {db_log.id} for athlete {athlete_id}")
        return db_log
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating nutrition log: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create nutrition log")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/{athlete_id}", response_model=List[NutritionLogResponse])
async def get_nutrition_history(
    athlete_id: UUID,
    start_date: date = Query(None),
    end_date: date = Query(None),
    limit: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """获取营养记录历史"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    query = select(NutritionLog).where(NutritionLog.athlete_id == athlete_id)
    if start_date:
        query = query.where(NutritionLog.log_date >= start_date)
    if end_date:
        query = query.where(NutritionLog.log_date <= end_date)
    query = query.order_by(NutritionLog.log_date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{athlete_id}/risk", response_model=NutritionRiskStatus)
async def get_nutrition_risk(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取营养风险评估（蛋白质不足3天或饮水<1.5L 3天）"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    thirty_days_ago = date.today() - timedelta(days=30)
    result = await db.execute(
        select(NutritionLog)
        .where(
            NutritionLog.athlete_id == athlete_id,
            NutritionLog.log_date >= thirty_days_ago,
        )
        .order_by(NutritionLog.log_date.desc())
    )
    logs = result.scalars().all()

    if not logs:
        return NutritionRiskStatus(has_risk=False, reason="无足够数据", consecutive_days=0)

    # 检查蛋白质连续不足天数
    protein_low_streak = 0
    max_protein_streak = 0
    for log in logs:
        if log.protein_sufficient == "否":
            protein_low_streak += 1
        else:
            protein_low_streak = 0
        if protein_low_streak > max_protein_streak:
            max_protein_streak = protein_low_streak

    # 检查饮水连续不足天数
    water_low_streak = 0
    max_water_streak = 0
    for log in logs:
        if log.water_intake_liters is not None and log.water_intake_liters < 1.5:
            water_low_streak += 1
        else:
            water_low_streak = 0
        if water_low_streak > max_water_streak:
            max_water_streak = water_low_streak

    reasons = []
    if max_protein_streak >= 3:
        reasons.append(f"蛋白质摄入不足连续 {max_protein_streak} 天")
    if max_water_streak >= 3:
        reasons.append(f"饮水量低于1.5L连续 {max_water_streak} 天")

    has_risk = len(reasons) > 0
    return NutritionRiskStatus(
        has_risk=has_risk,
        reason="; ".join(reasons) if reasons else "营养指标正常",
        consecutive_days=max(max_protein_streak, max_water_streak),
    )
