"""
AthleteIQ - 心理监测 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import List
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import MentalLog, Athlete
from app.schemas.schemas import MentalLogCreate, MentalLogResponse, MentalWeeklyReport
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/mental", tags=["心理监测"])

RESTQ_SPORT_TEMPLATE = {
    "restq_sport_short": {
        "name": "RESTQ-Sport 简化版 (15题)",
        "description": "基于Kellmann & Kallus (2001) 的运动恢复-应激问卷的简化版本，由教练定期发放。",
        "questions": [
            {"id": 1, "category": "一般应激", "text": "在过去3天中，我感到精神疲惫", "scale": "0(从不) - 6(总是)"},
            {"id": 2, "category": "一般应激", "text": "在过去3天中，我感到情绪低落", "scale": "0(从不) - 6(总是)"},
            {"id": 3, "category": "一般应激", "text": "在过去3天中，我感觉压力很大，难以放松", "scale": "0(从不) - 6(总是)"},
            {"id": 4, "category": "情绪应激", "text": "在过去3天中，我对训练感到焦虑或担忧", "scale": "0(从不) - 6(总是)"},
            {"id": 5, "category": "情绪应激", "text": "在过去3天中，我容易因小事而烦躁", "scale": "0(从不) - 6(总是)"},
            {"id": 6, "category": "情绪应激", "text": "在过去3天中，我对比赛表现感到紧张", "scale": "0(从不) - 6(总是)"},
            {"id": 7, "category": "身体恢复", "text": "在过去3天中，我感到身体充满活力", "scale": "0(从不) - 6(总是)"},
            {"id": 8, "category": "身体恢复", "text": "在过去3天中，我的肌肉感觉恢复良好", "scale": "0(从不) - 6(总是)"},
            {"id": 9, "category": "身体恢复", "text": "在过去3天中，我感觉身体状态良好", "scale": "0(从不) - 6(总是)"},
            {"id": 10, "category": "一般恢复", "text": "在过去3天中，我睡眠质量很好", "scale": "0(从不) - 6(总是)"},
            {"id": 11, "category": "一般恢复", "text": "在过去3天中，我感到心情愉快", "scale": "0(从不) - 6(总是)"},
            {"id": 12, "category": "一般恢复", "text": "在过去3天中，我有足够的休息时间", "scale": "0(从不) - 6(总是)"},
            {"id": 13, "category": "睡眠质量", "text": "在过去3天中，我入睡没有困难", "scale": "0(从不) - 6(总是)"},
            {"id": 14, "category": "睡眠质量", "text": "在过去3天中，我整夜安睡不醒", "scale": "0(从不) - 6(总是)"},
            {"id": 15, "category": "睡眠质量", "text": "在过去3天中，我醒来后感觉精力充沛", "scale": "0(从不) - 6(总是)"},
        ],
    }
}


@router.get("/templates")
async def get_mental_templates():
    """获取心理评估模板"""
    return RESTQ_SPORT_TEMPLATE


@router.post("/", response_model=MentalLogResponse, status_code=201)
async def create_mental_log(
    log: MentalLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """提交每日心理状态记录"""
    try:
        athlete_id = log.athlete_id
        athlete = await db.get(Athlete, athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        existing = await db.execute(
            select(MentalLog).where(
                MentalLog.athlete_id == athlete_id,
                MentalLog.log_date == log.log_date,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="该日期已有心理记录")

        db_log = MentalLog(athlete_id=athlete_id, **log.model_dump())
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)
        logger.info(f"Created mental log {db_log.id} for athlete {athlete_id}")
        return db_log
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating mental log: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create mental log")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/{athlete_id}", response_model=List[MentalLogResponse])
async def get_mental_history(
    athlete_id: UUID,
    start_date: date = Query(None),
    end_date: date = Query(None),
    limit: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """获取心理状态记录历史"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    query = select(MentalLog).where(MentalLog.athlete_id == athlete_id)
    if start_date:
        query = query.where(MentalLog.log_date >= start_date)
    if end_date:
        query = query.where(MentalLog.log_date <= end_date)
    query = query.order_by(MentalLog.log_date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{athlete_id}/weekly-report", response_model=MentalWeeklyReport)
async def get_weekly_report(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取周度心理状态平均值及趋势"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    end_date = date.today()
    start_date = end_date - timedelta(days=14)

    result = await db.execute(
        select(MentalLog)
        .where(
            MentalLog.athlete_id == athlete_id,
            MentalLog.log_date >= start_date,
            MentalLog.log_date <= end_date,
        )
        .order_by(MentalLog.log_date.asc())
    )
    logs = result.scalars().all()

    if not logs:
        return MentalWeeklyReport(
            week_start=start_date,
            avg_mood=0, avg_focus=0, avg_motivation=0, avg_fatigue=0,
            trend="无数据", has_alert=False,
        )

    # 计算最近一周
    one_week_ago = end_date - timedelta(days=7)
    current_week = [l for l in logs if l.log_date > one_week_ago]
    previous_week = [l for l in logs if l.log_date <= one_week_ago and l.log_date > (one_week_ago - timedelta(days=7))]

    def avg_scores(week_logs):
        if not week_logs:
            return {"mood": 0, "focus": 0, "motivation": 0, "fatigue": 0}
        mood = sum(l.mood_score or 0 for l in week_logs) / len(week_logs)
        focus = sum(l.focus_score or 0 for l in week_logs) / len(week_logs)
        motivation = sum(l.motivation_score or 0 for l in week_logs) / len(week_logs)
        fatigue = sum(l.mental_fatigue_score or 0 for l in week_logs) / len(week_logs)
        return {"mood": round(mood, 2), "focus": round(focus, 2), "motivation": round(motivation, 2), "fatigue": round(fatigue, 2)}

    current_avg = avg_scores(current_week)
    previous_avg = avg_scores(previous_week)

    # 趋势判断
    if previous_avg["mood"] == 0 and previous_avg["motivation"] == 0:
        trend = "基线"
    elif (current_avg["mood"] > previous_avg["mood"]
          and current_avg["motivation"] > previous_avg["motivation"]):
        trend = "改善"
    elif (current_avg["mood"] < previous_avg["mood"]
          and current_avg["motivation"] < previous_avg["motivation"]):
        trend = "下降"
    else:
        trend = "稳定"

    has_alert = (current_week and (
        current_avg["mood"] < 2.5 or current_avg["fatigue"] > 4.0
    ))

    return MentalWeeklyReport(
        week_start=one_week_ago + timedelta(days=1),
        avg_mood=current_avg["mood"],
        avg_focus=current_avg["focus"],
        avg_motivation=current_avg["motivation"],
        avg_fatigue=current_avg["fatigue"],
        trend=trend,
        has_alert=has_alert,
    )


@router.get("/{athlete_id}/alert")
async def get_mental_alert(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """检查心理状态预警：2周下降>20% 或 平均<2.5"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    end_date = date.today()
    start_date = end_date - timedelta(days=14)

    result = await db.execute(
        select(MentalLog)
        .where(
            MentalLog.athlete_id == athlete_id,
            MentalLog.log_date >= start_date,
            MentalLog.log_date <= end_date,
        )
        .order_by(MentalLog.log_date.asc())
    )
    logs = result.scalars().all()

    if not logs:
        return {"alert": False, "trigger": None, "message": "无足够数据"}

    one_week_ago = end_date - timedelta(days=7)
    current_week = [l for l in logs if l.log_date > one_week_ago]
    previous_week = [l for l in logs if l.log_date <= one_week_ago]

    def calc_avg(week_logs, field):
        if not week_logs:
            return None
        values = [getattr(l, field) or 0 for l in week_logs]
        return sum(values) / len(values)

    triggers = []

    # 检查2周下降 >20%
    for field, label in [("mood_score", "情绪"), ("motivation_score", "动机")]:
        prev_avg = calc_avg(previous_week, field)
        curr_avg = calc_avg(current_week, field)
        if prev_avg and curr_avg and prev_avg > 0:
            decline = (prev_avg - curr_avg) / prev_avg * 100
            if decline > 20:
                triggers.append(f"{label}2周下降{decline:.0f}%")

    # 检查平均 <2.5
    for field, label in [("mood_score", "情绪"), ("focus_score", "专注力"), ("motivation_score", "动机")]:
        curr_avg = calc_avg(current_week, field)
        if curr_avg is not None and curr_avg < 2.5:
            triggers.append(f"{label}平均{curr_avg:.1f} (<2.5)")

    alert = len(triggers) > 0
    return {
        "alert": alert,
        "trigger": triggers if triggers else None,
        "message": "; ".join(triggers) if triggers else "心理状态正常",
    }
