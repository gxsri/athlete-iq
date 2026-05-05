"""
AthleteIQ - Competition Calendar API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import Athlete, Competition, DailyMetric, TrainingLog
from app.schemas.schemas import (
    CompetitionCreate, CompetitionResponse,
    DailyMetricResponse, DailyMetricUpdate,
    MonthlyRiskResponse, TrainingRecommendationResponse2,
)
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/athletes", tags=["比赛日历"])


# ============ Competition CRUD ============

@router.post("/{athlete_id}/competitions", response_model=CompetitionResponse, status_code=201)
async def create_competition(
    athlete_id: UUID,
    data: CompetitionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a competition for an athlete. Athlete ID in URL is authoritative."""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    try:
        comp = Competition(
            athlete_id=athlete_id,
            name=data.name,
            competition_date=data.competition_date,
            location=data.location,
            notes=data.notes,
        )
        db.add(comp)
        await db.commit()
        await db.refresh(comp)
        logger.info(f"Created competition '{comp.name}' for athlete {athlete_id}")
        return comp
    except IntegrityError:
        raise HTTPException(status_code=409, detail="比赛数据冲突")
    except Exception as e:
        logger.exception("Failed to create competition")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{athlete_id}/competitions", response_model=List[CompetitionResponse])
async def list_competitions(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Competition)
        .where(Competition.athlete_id == athlete_id)
        .order_by(Competition.competition_date.asc())
    )
    return result.scalars().all()


@router.delete("/{athlete_id}/competitions/{competition_id}")
async def delete_competition(
    athlete_id: UUID,
    competition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    comp = await db.get(Competition, competition_id)
    if not comp or comp.athlete_id != athlete_id:
        raise HTTPException(status_code=404, detail="比赛不存在")
    await db.delete(comp)
    await db.commit()
    return {"status": "deleted"}


# ============ Monthly Risk Data (Calendar Heatmap) ============

@router.get("/{athlete_id}/monthly-risks", response_model=List[MonthlyRiskResponse])
async def get_monthly_risks(
    athlete_id: UUID,
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """
    Get daily injury risk + training load for a given month.
    Used by the calendar heatmap component.
    """
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    # Get daily metrics
    result = await db.execute(
        select(DailyMetric)
        .where(
            DailyMetric.athlete_id == athlete_id,
            DailyMetric.metric_date >= start_date,
            DailyMetric.metric_date <= end_date,
        )
        .order_by(DailyMetric.metric_date.asc())
    )
    metrics = {m.metric_date: m for m in result.scalars().all()}

    # Get competitions in this month
    comps_result = await db.execute(
        select(Competition)
        .where(
            Competition.athlete_id == athlete_id,
            Competition.competition_date >= start_date,
            Competition.competition_date <= end_date,
        )
    )
    comps = {c.competition_date: c for c in comps_result.scalars().all()}

    # Build response for all days in month
    days = []
    current = start_date
    while current <= end_date:
        m = metrics.get(current)
        c = comps.get(current)
        days.append(MonthlyRiskResponse(
            date=str(current),
            injury_risk=m.injury_risk if m else 0,
            training_load=m.training_load if m else 0,
            has_competition=c is not None,
            competition_name=c.name if c else None,
        ))
        current += timedelta(days=1)

    return days


# ============ Daily Metrics Read/Write ============

@router.get("/{athlete_id}/daily-metrics", response_model=Optional[DailyMetricResponse])
async def get_daily_metrics(
    athlete_id: UUID,
    metric_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed metrics for a specific day."""
    result = await db.execute(
        select(DailyMetric).where(
            DailyMetric.athlete_id == athlete_id,
            DailyMetric.metric_date == metric_date,
        )
    )
    metric = result.scalar_one_or_none()
    if not metric:
        return None
    return metric


@router.put("/{athlete_id}/daily-metrics", response_model=DailyMetricResponse)
async def update_daily_metrics(
    athlete_id: UUID,
    data: DailyMetricUpdate,
    metric_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Update training arrangement for a specific day (upsert)."""
    result = await db.execute(
        select(DailyMetric).where(
            DailyMetric.athlete_id == athlete_id,
            DailyMetric.metric_date == metric_date,
        )
    )
    metric = result.scalar_one_or_none()

    try:
        if metric:
            if data.training_load is not None:
                metric.training_load = data.training_load
            if data.injury_risk is not None:
                metric.injury_risk = data.injury_risk
            if data.fatigue is not None:
                metric.fatigue = data.fatigue
            if data.sleep_quality is not None:
                metric.sleep_quality = data.sleep_quality
            if data.training_content is not None:
                metric.training_content = data.training_content
            if data.notes is not None:
                metric.notes = data.notes
        else:
            metric = DailyMetric(
                athlete_id=athlete_id,
                metric_date=metric_date,
                training_load=data.training_load or 0,
                injury_risk=data.injury_risk or 0,
                fatigue=data.fatigue or 0,
                sleep_quality=data.sleep_quality or 5.0,
                training_content=data.training_content,
                notes=data.notes,
            )
            db.add(metric)

        await db.commit()
        await db.refresh(metric)

        # Auto-recalculate risks from body data
        from app.core.risk_engine import compute_all_risks
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
        for key, value in risks.items():
            setattr(metric, key, value)
        await db.commit()
        await db.refresh(metric)

        return metric
    except Exception as e:
        logger.exception("Failed to update daily metrics")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Competition Countdown Training Recommendation ============

def _get_training_recommendation(days_until: int) -> dict:
    """Generate training phase recommendation based on days until competition."""
    if days_until > 28:
        return {
            "phase": "基础耐力期",
            "phase_label": "基础期",
            "load_range": "60-70%",
            "description": "重点发展有氧基础、力量耐力和技术动作稳定性。高容量、中低强度。",
            "recommendations": [
                "每周训练 5-6 天，以有氧和力量基础为主",
                "逐步增加训练容量，每周增幅不超过 10%",
                "每 4 周安排 1 周减量（负荷降至 60%）",
                "重点监控 ACWR，保持在 0.8-1.3 安全区间",
                "加入技术动作练习，固化运动模式",
            ],
        }
    elif days_until >= 15:
        return {
            "phase": "专项强度期",
            "phase_label": "强化期",
            "load_range": "75-85%",
            "description": "提升专项运动能力，增加训练强度。模拟比赛节奏和对抗强度。",
            "recommendations": [
                "每周训练 5-6 天，强度为主",
                "加入比赛模拟训练（如对抗、计时赛等）",
                "控制 ACWR 不超过 1.3，避免过度训练",
                "加强营养补给，蛋白质摄入 1.6-2.0g/kg",
                "每周至少 1 天完全休息或低强度恢复",
            ],
        }
    elif days_until >= 7:
        return {
            "phase": "模拟赛期",
            "phase_label": "模拟期",
            "load_range": "80-90%",
            "description": "高强度专项模拟，但密切监控恢复指标。接近比赛强度但减少容量。",
            "recommendations": [
                "训练强度接近比赛水平，但容量降至平时的 70-80%",
                "每日监控晨起心率和 HRV",
                "RSSI 超过 50 分时立即调整训练计划",
                "保证每天 8+ 小时睡眠",
                "心理准备：可视化比赛流程，降低赛前焦虑",
            ],
        }
    elif days_until >= 4:
        return {
            "phase": "减量周",
            "phase_label": "减量期",
            "load_range": "50-60%",
            "description": "系统性减量，消除疲劳积累，让身体进入超量恢复阶段。",
            "recommendations": [
                "训练容量降至平时 50%，强度维持比赛水平",
                "增加碳水和水分摄入",
                "每日睡眠 8-9 小时，可增加午休",
                "避免新动作或高风险训练",
                "轻度拉伸和泡沫轴放松",
            ],
        }
    elif days_until >= 1:
        return {
            "phase": "赛前调整",
            "phase_label": "调整期",
            "load_range": "30-40%",
            "description": "赛前最后调整，以轻度活动和心理准备为主。确保最佳竞技状态。",
            "recommendations": [
                "仅进行轻度热身和专项技术回顾",
                "高碳水饮食（糖原填充法）",
                "检查比赛装备和用品",
                "充分休息，避免熬夜",
                "看比赛录像、战术回顾",
            ],
        }
    else:
        return {
            "phase": "比赛日",
            "phase_label": "比赛日",
            "load_range": "20%",
            "description": "比赛日当天。以热身和准备活动为主，避免消耗过多体力。",
            "recommendations": [
                "赛前 3 小时进食易消化早餐",
                "充分热身 20-30 分钟",
                "比赛过程中少量多次补水",
                "赛后及时补充碳水+蛋白质（3:1）",
                "记录比赛数据和赛后感受",
            ],
        }


@router.get("/{athlete_id}/competitions/{competition_id}/recommendation", response_model=TrainingRecommendationResponse2)
async def get_competition_recommendation(
    athlete_id: UUID,
    competition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get training recommendation based on competition countdown."""
    comp = await db.get(Competition, competition_id)
    if not comp or comp.athlete_id != athlete_id:
        raise HTTPException(status_code=404, detail="比赛不存在")

    today = date.today()
    days_until = (comp.competition_date - today).days

    rec = _get_training_recommendation(days_until)

    return TrainingRecommendationResponse2(
        competition_date=comp.competition_date,
        days_until=days_until,
        phase=rec["phase"],
        phase_label=rec["phase_label"],
        load_range=rec["load_range"],
        description=rec["description"],
        recommendations=rec["recommendations"],
    )
