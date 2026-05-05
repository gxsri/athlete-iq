"""
AthleteIQ - Enhanced Alerts API
预警中心：阈值配置、风险评估、预警列表
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from uuid import UUID
from typing import List, Optional

from app.database import get_db, logger
from app.models.athlete import Athlete, DailyMetric, AlertConfig, AlertEvent
from app.schemas.schemas import AlertConfigCreate, AlertConfigResponse, AlertConfigUpdate
from app.core.risk_engine import compute_all_risks

router = APIRouter(prefix="/api/alerts", tags=["预警中心"])


# ============ Alert Config CRUD ============

@router.get("/config/{athlete_id}", response_model=List[AlertConfigResponse])
async def get_alert_configs(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.athlete_id == athlete_id)
    )
    return result.scalars().all()


@router.put("/config", status_code=201)
async def upsert_alert_config(
    data: AlertConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建或更新预警阈值配置"""
    existing = await db.execute(
        select(AlertConfig).where(
            AlertConfig.athlete_id == data.athlete_id,
            AlertConfig.metric_name == data.metric_name,
        )
    )
    config = existing.scalar_one_or_none()

    if config:
        config.threshold = data.threshold
        config.severity = data.severity
        config.notify = data.notify
    else:
        config = AlertConfig(
            athlete_id=data.athlete_id,
            metric_name=data.metric_name,
            threshold=data.threshold,
            severity=data.severity,
            notify=data.notify,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/config/{config_id}")
async def delete_alert_config(config_id: UUID, db: AsyncSession = Depends(get_db)):
    config = await db.get(AlertConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    await db.delete(config)
    await db.commit()
    return {"status": "deleted"}


# ============ Alert Overview ============

@router.get("/overview")
async def get_alerts_overview(
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    获取预警总览。扫描所有运动员的最新 daily_metrics，
    与 alert_config 阈值比较，生成预警记录。
    """
    today = date.today()

    # Get all athletes
    athletes_result = await db.execute(select(Athlete))
    athletes = athletes_result.scalars().all()

    alerts = []
    risk_athlete_count = 0

    for athlete in athletes:
        # Latest daily_metric
        metric_result = await db.execute(
            select(DailyMetric)
            .where(DailyMetric.athlete_id == athlete.id)
            .order_by(DailyMetric.metric_date.desc())
            .limit(1)
        )
        metric = metric_result.scalar_one_or_none()
        if not metric:
            continue

        # Check all four risk values
        risk_checks = [
            ("shoulder_overuse_risk", metric.shoulder_overuse_risk or 0),
            ("shoulder_acute_risk", metric.shoulder_acute_risk or 0),
            ("knee_overuse_risk", metric.knee_overuse_risk or 0),
            ("knee_acute_risk", metric.knee_acute_risk or 0),
        ]

        for metric_name, current_value in risk_checks:
            # Get configured threshold (default 70)
            config_result = await db.execute(
                select(AlertConfig).where(
                    AlertConfig.athlete_id == athlete.id,
                    AlertConfig.metric_name == metric_name,
                )
            )
            config = config_result.scalar_one_or_none()
            threshold = config.threshold if config else 70.0
            sev = config.severity if config else "warning"

            if current_value > threshold:
                # Check if alert already exists for today
                existing_alert = await db.execute(
                    select(AlertEvent).where(
                        AlertEvent.athlete_id == athlete.id,
                        AlertEvent.alert_date == today,
                        AlertEvent.alert_type == metric_name,
                    )
                )
                if not existing_alert.scalar_one_or_none():
                    # Create alert
                    alert = AlertEvent(
                        athlete_id=athlete.id,
                        alert_date=today,
                        alert_type=metric_name,
                        severity=sev,
                        alert_source="risk_engine",
                        current_value=str(current_value),
                        recommended_action=_get_risk_recommendation(metric_name, current_value),
                        is_read=False,
                        is_resolved=False,
                    )
                    db.add(alert)

                risk_athlete_count += 1
                alerts.append({
                    "athlete_id": str(athlete.id),
                    "athlete_name": athlete.name,
                    "sport": athlete.sport,
                    "metric_name": metric_name,
                    "current_value": current_value,
                    "threshold": threshold,
                    "severity": sev,
                    "date": str(today),
                    "recommendation": _get_risk_recommendation(metric_name, current_value),
                })

    await db.commit()

    # Sort by current_value descending
    alerts.sort(key=lambda x: x["current_value"], reverse=True)

    # Filter by severity if requested
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]

    # Get existing unresolved alerts
    existing_alerts_result = await db.execute(
        select(AlertEvent)
        .where(AlertEvent.is_resolved == False)
        .order_by(AlertEvent.alert_date.desc())
        .limit(limit)
    )
    existing_alerts = existing_alerts_result.scalars().all()

    return {
        "risk_athlete_count": risk_athlete_count,
        "active_alerts_count": len(existing_alerts),
        "alerts": alerts[:limit],
        "historical_alerts": [
            {
                "id": str(a.id),
                "athlete_id": str(a.athlete_id),
                "alert_date": str(a.alert_date),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "current_value": a.current_value,
                "recommended_action": a.recommended_action,
                "is_read": a.is_read,
                "is_resolved": a.is_resolved,
            }
            for a in existing_alerts[:20]
        ],
    }


@router.get("/athlete/{athlete_id}")
async def get_athlete_alerts(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取单个运动员的预警历史 + 近7天风险趋势"""
    # Historical alerts
    alerts_result = await db.execute(
        select(AlertEvent)
        .where(AlertEvent.athlete_id == athlete_id)
        .order_by(AlertEvent.alert_date.desc())
        .limit(30)
    )
    alerts = alerts_result.scalars().all()

    # Last 7 days risk trend
    seven_days_ago = date.today() - timedelta(days=7)
    metrics_result = await db.execute(
        select(DailyMetric)
        .where(
            DailyMetric.athlete_id == athlete_id,
            DailyMetric.metric_date >= seven_days_ago,
        )
        .order_by(DailyMetric.metric_date.asc())
    )
    metrics = metrics_result.scalars().all()

    trend = [
        {
            "date": str(m.metric_date),
            "shoulder_overuse_risk": m.shoulder_overuse_risk or 0,
            "shoulder_acute_risk": m.shoulder_acute_risk or 0,
            "knee_overuse_risk": m.knee_overuse_risk or 0,
            "knee_acute_risk": m.knee_acute_risk or 0,
            "training_load": m.training_load or 0,
            "fatigue": m.fatigue or 0,
        }
        for m in metrics
    ]

    return {
        "athlete_id": str(athlete_id),
        "alerts": [
            {
                "id": str(a.id),
                "alert_date": str(a.alert_date),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "current_value": a.current_value,
                "recommended_action": a.recommended_action,
                "is_resolved": a.is_resolved,
            }
            for a in alerts
        ],
        "risk_trend_7d": trend,
    }


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """标记预警已处理"""
    alert = await db.get(AlertEvent, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")
    alert.is_resolved = True
    alert.is_read = True
    alert.resolved_at = date.today()
    await db.commit()
    return {"status": "acknowledged"}


def _get_risk_recommendation(metric_name: str, value: float) -> str:
    """Generate recommendation text based on risk metric."""
    recs = {
        "shoulder_overuse_risk": f"肩部劳损风险 {value:.0f}%，建议减少杀球量30%，增加肩袖稳定性训练（YTW伸展）",
        "shoulder_acute_risk": f"肩部急性风险 {value:.0f}%，建议立即减量，冰敷肩部，暂停高强度过顶动作",
        "knee_overuse_risk": f"膝部劳损风险 {value:.0f}%，建议减少跳跃频次，增加股四头肌离心训练",
        "knee_acute_risk": f"膝部急性风险 {value:.0f}%，建议减少冲击性训练，检查落地技术，如有疼痛立即就医",
    }
    return recs.get(metric_name, f"风险值 {value:.0f}%，请关注")
