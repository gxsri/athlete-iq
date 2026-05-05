"""
AthleteIQ - 训练日志 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import List
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import TrainingLog, Athlete
from app.schemas.schemas import TrainingLogCreate, TrainingLogResponse, TrainingLogBatch, ACWRTimeSeries
from app.core.acwr import ACWRCalculator, TrainingSession
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/training", tags=["训练日志"])


@router.post("/log", response_model=TrainingLogResponse, status_code=201)
async def create_training_log(log: TrainingLogCreate, db: AsyncSession = Depends(get_db)):
    """提交单条训练日志。自动计算 session_load = duration_minutes × rpe"""
    try:
        athlete = await db.get(Athlete, log.athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        existing = await db.execute(
            select(TrainingLog).where(
                TrainingLog.athlete_id == log.athlete_id,
                TrainingLog.training_date == log.training_date,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="该日期已有训练记录，请使用更新接口")

        session_load = log.duration_minutes * log.rpe
        db_log = TrainingLog(
            athlete_id=log.athlete_id,
            training_date=log.training_date,
            duration_minutes=log.duration_minutes,
            rpe=log.rpe,
            training_type=log.training_type,
            session_load=session_load,
            cycle_phase=log.cycle_phase,
            description=log.description,
            coach_notes=log.coach_notes,
            tags=log.tags or [],
            source=log.source,
        )
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)
        logger.info(f"Created training log {db_log.id} for athlete {log.athlete_id}")
        return db_log
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating training log: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create training log")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/log/batch", status_code=201)
async def batch_create_training_logs(batch: TrainingLogBatch, db: AsyncSession = Depends(get_db)):
    """批量导入训练日志（Excel/CSV 导入）"""
    logger.info(f"Batch import: {len(batch.logs)} logs for athletes")
    try:
        imported = 0
        errors = []

        for log in batch.logs:
            try:
                athlete = await db.get(Athlete, log.athlete_id)
                if not athlete:
                    errors.append({"date": str(log.training_date), "error": "运动员不存在"})
                    continue

                session_load = log.duration_minutes * log.rpe
                db_log = TrainingLog(
                    athlete_id=log.athlete_id,
                    training_date=log.training_date,
                    duration_minutes=log.duration_minutes,
                    rpe=log.rpe,
                    training_type=log.training_type,
                    session_load=session_load,
                    cycle_phase=log.cycle_phase,
                    description=log.description,
                    coach_notes=log.coach_notes,
                    tags=log.tags or [],
                    source=log.source,
                )
                db.add(db_log)
                imported += 1
            except Exception as e:
                errors.append({"date": str(log.training_date), "error": str(e)})

        await db.commit()
        logger.info(f"Batch: {imported} imported, {len(errors)} skipped")
        return {"records_imported": imported, "records_skipped": len(errors), "errors": errors}
    except IntegrityError as e:
        logger.warning(f"IntegrityError in batch import: {e}")
        raise HTTPException(status_code=409, detail=f"批量数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Batch import failed")
        return JSONResponse(status_code=500, content={"detail": f"批量导入失败: {str(e)[:200]}"})


@router.get("/log/{athlete_id}", response_model=List[TrainingLogResponse])
async def get_training_logs(
    athlete_id: UUID,
    start_date: date = Query(None, description="开始日期"),
    end_date: date = Query(None, description="结束日期"),
    training_type: str = Query(None, description="筛选训练类型"),
    limit: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """获取运动员训练日志"""
    query = select(TrainingLog).where(TrainingLog.athlete_id == athlete_id)

    if start_date:
        query = query.where(TrainingLog.training_date >= start_date)
    if end_date:
        query = query.where(TrainingLog.training_date <= end_date)
    if training_type:
        query = query.where(TrainingLog.training_type == training_type)

    query = query.order_by(TrainingLog.training_date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/log/{athlete_id}/acwr", response_model=ACWRTimeSeries)
async def get_acwr_timeseries(
    athlete_id: UUID,
    start_date: date = Query(None),
    end_date: date = Query(None),
    acute_window: int = Query(7, ge=3, le=14),
    chronic_window: int = Query(28, ge=14, le=42),
    db: AsyncSession = Depends(get_db),
):
    """
    获取运动员 ACWR 时间序列

    基于 CPSS 负荷监控标准:
      - 急性负荷 = 7天 (默认) 滚动平均 session load
      - 慢性负荷 = 28天 (默认) 滚动平均 session load
      - ACWR = 急性负荷 / 慢性负荷
      - 风险区间 (NSCA 共识): 0.8-1.3 安全, 1.3-1.5 谨慎, >1.5 高风险
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    result = await db.execute(
        select(TrainingLog)
        .where(
            TrainingLog.athlete_id == athlete_id,
            TrainingLog.training_date >= start_date - timedelta(days=chronic_window),
            TrainingLog.training_date <= end_date,
        )
        .order_by(TrainingLog.training_date.asc())
    )
    logs = result.scalars().all()

    sessions = [
        TrainingSession(date=log.training_date, session_load=log.session_load or 0,
                        training_type=log.training_type or "")
        for log in logs
    ]

    calc = ACWRCalculator(acute_window=acute_window, chronic_window=chronic_window)
    acwr_results = calc.calculate_timeseries(sessions)

    return ACWRTimeSeries(
        dates=[str(r.date) for r in acwr_results],
        acute_load=[r.acute_load for r in acwr_results],
        chronic_load=[r.chronic_load for r in acwr_results],
        acwr=[r.acwr for r in acwr_results],
        risk_zone_thresholds={"sweet_spot_low": 0.8, "sweet_spot_high": 1.3, "danger": 1.5},
    )


@router.get("/log/{athlete_id}/load-summary")
async def get_load_summary(
    athlete_id: UUID,
    weeks: int = Query(12, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
):
    """获取运动员负荷摘要（最近 N 周）"""
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    result = await db.execute(
        select(TrainingLog)
        .where(
            TrainingLog.athlete_id == athlete_id,
            TrainingLog.training_date >= start_date,
            TrainingLog.training_date <= end_date,
        )
        .order_by(TrainingLog.training_date.asc())
    )
    logs = result.scalars().all()

    # 按周汇总
    weekly_data = []
    for log in logs:
        week_start = log.training_date - timedelta(days=log.training_date.weekday())
        week_key = week_start.isoformat()

        found = None
        for w in weekly_data:
            if w["week_start"] == week_key:
                found = w
                break
        if found:
            found["total_load"] += (log.session_load or 0)
            found["sessions"] += 1
        else:
            weekly_data.append({
                "week_start": week_key,
                "total_load": log.session_load or 0,
                "sessions": 1,
            })

    # 计算周平均及负荷变化
    for i, w in enumerate(weekly_data):
        w["avg_session_load"] = round(w["total_load"] / w["sessions"], 1) if w["sessions"] else 0
        if i > 0:
            prev = weekly_data[i - 1]["total_load"]
            if prev > 0:
                w["week_over_week_change_pct"] = round(
                    ((w["total_load"] - prev) / prev) * 100, 1
                )
            else:
                w["week_over_week_change_pct"] = 0
        else:
            w["week_over_week_change_pct"] = 0

    return {
        "athlete_id": str(athlete_id),
        "period": f"{start_date} to {end_date}",
        "total_weeks": len(weekly_data),
        "weekly_data": weekly_data,
    }


@router.get("/log/{athlete_id}/distribution")
async def get_training_distribution(
    athlete_id: UUID,
    days: int = Query(90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get training load distribution by type for the last N days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(TrainingLog.training_type, func.sum(TrainingLog.session_load))
        .where(
            TrainingLog.athlete_id == athlete_id,
            TrainingLog.training_date >= start_date,
            TrainingLog.training_date <= end_date,
        )
        .group_by(TrainingLog.training_type)
    )
    rows = result.all()

    distribution = [
        {"type": row[0] or "未知", "total_load": round(float(row[1] or 0), 1)}
        for row in rows
    ]

    total = sum(d["total_load"] for d in distribution)
    for d in distribution:
        d["percentage"] = round((d["total_load"] / total * 100), 1) if total > 0 else 0

    return {
        "athlete_id": str(athlete_id),
        "days": days,
        "total_load": round(total, 1),
        "distribution": distribution,
    }
