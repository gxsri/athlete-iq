"""
AthleteIQ - 仪表板与风险分析 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.athlete import (
    Athlete, TrainingLog, WellnessQuestionnaire, PerformanceTest,
    ComputedMetric, AlertEvent, AthleteBaseline, CoachComment,
    DailyReadiness, MentalLog, NutritionLog, DailyMetric,
)
from app.schemas.schemas import (
    DashboardOverview, AthleteRiskStatus, RSSIDetail,
    PerformanceComparison, TrainingRecommendationResponse,
    CoachCommentResponse,
)
from app.core.rssi import RSSICalculator, WellnessRecord, PerformanceRecord
from app.core.acwr import ACWRCalculator, TrainingSession
from app.core.recommendation import TrainingAdvisor, AthleteProfile, CyclePhase
from app.core.statistical import is_significant_change
from app.core.risk_score import calculate_composite_risk
from app.core.standards import get_athlete_level, get_sport_standards, SPORT_STANDARDS, LEVELS

router = APIRouter(prefix="/api/dashboard", tags=["仪表板与风险分析"])


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    coach_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取仪表板总览：团队整体负荷状态、风险运动员列表"""
    # 获取所有运动员
    athletes_result = await db.execute(select(Athlete))
    athletes = athletes_result.scalars().all()

    if not athletes:
        return DashboardOverview(
            total_athletes=0, athletes_at_risk=0, active_alerts=0,
            avg_team_acwr=0, alerts_by_severity={}, athlete_statuses=[],
        )

    # 获取最近 30 天活跃预警
    thirty_days_ago = date.today() - timedelta(days=30)
    alerts_result = await db.execute(
        select(AlertEvent).where(
            AlertEvent.alert_date >= thirty_days_ago,
            AlertEvent.is_resolved == False,
        )
    )
    active_alerts = alerts_result.scalars().all()

    # 按严重程度统计
    severity_counts = {"高": 0, "中": 0, "低": 0, "严重": 0}
    for a in active_alerts:
        if a.severity in severity_counts:
            severity_counts[a.severity] += 1

    # 构建每个运动员的状态
    athlete_statuses = []
    at_risk_count = 0
    acwr_values = []

    for athlete in athletes:
        # 获取最新计算指标
        metric_result = await db.execute(
            select(ComputedMetric)
            .where(ComputedMetric.athlete_id == athlete.id)
            .order_by(ComputedMetric.calc_date.desc())
            .limit(1)
        )
        latest_metric = metric_result.scalar_one_or_none()

        # 获取该运动员的活跃预警数量
        athlete_alerts = sum(1 for a in active_alerts if a.athlete_id == athlete.id)

        acwr_val = latest_metric.acwr if latest_metric else 0
        acwr_zone = (latest_metric.acwr_risk_zone or "安全区") if latest_metric else "安全区"
        rssi_val = (latest_metric.rssi_score or 0) if latest_metric else 0
        rssi_level = (latest_metric.rssi_risk_level or "正常") if latest_metric else "正常"

        if acwr_zone in ("谨慎区", "高风险区") or rssi_level != "正常":
            at_risk_count += 1

        if acwr_val > 0:
            acwr_values.append(acwr_val)

        athlete_statuses.append(AthleteRiskStatus(
            athlete_id=athlete.id,
            athlete_name=athlete.name,
            sport=athlete.sport,
            latest_acwr=round(acwr_val, 3),
            acwr_risk_zone=acwr_zone,
            rssi_score=round(rssi_val, 2),
            rssi_risk_level=rssi_level,
            trend_direction="稳定",
            active_alerts=athlete_alerts,
            last_updated=latest_metric.calc_date if latest_metric else date.today(),
        ))

    avg_team_acwr = round(sum(acwr_values) / len(acwr_values), 3) if acwr_values else 0

    return DashboardOverview(
        total_athletes=len(athletes),
        athletes_at_risk=at_risk_count,
        active_alerts=len(active_alerts),
        avg_team_acwr=avg_team_acwr,
        alerts_by_severity=severity_counts,
        athlete_statuses=athlete_statuses,
    )


@router.get("/athlete/{athlete_id}/rssi", response_model=RSSIDetail)
async def get_athlete_rssi(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    获取运动员的 RSSI（恢复-应激状态指数）详细分析

    RSSI 综合 5 个维度:
      1. ACWR 负荷比 (25分)
      2. 晨起心率变化 (25分)
      3. HRV 心率变异性 (25分)
      4. 主观疲劳问卷 (15分)
      5. 体能测试表现 (10分)
    """
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    # 获取最近 30 天训练日志
    thirty_days_ago = date.today() - timedelta(days=30)
    logs_result = await db.execute(
        select(TrainingLog)
        .where(
            TrainingLog.athlete_id == athlete_id,
            TrainingLog.training_date >= thirty_days_ago,
        )
        .order_by(TrainingLog.training_date.asc())
    )
    logs = logs_result.scalars().all()

    sessions = [
        TrainingSession(date=log.training_date, session_load=log.session_load or 0,
                        training_type=log.training_type or "")
        for log in logs
    ]

    # ACWR 计算
    calc = ACWRCalculator()
    acwr_results = calc.calculate_timeseries(sessions)
    acwr_tuples = [(r.date, r.acwr, r.risk_zone) for r in acwr_results]

    # 获取健康问卷
    wellness_result = await db.execute(
        select(WellnessQuestionnaire)
        .where(
            WellnessQuestionnaire.athlete_id == athlete_id,
            WellnessQuestionnaire.record_date >= thirty_days_ago,
        )
        .order_by(WellnessQuestionnaire.record_date.asc())
    )
    wellness_logs = wellness_result.scalars().all()

    wellness_records = [
        WellnessRecord(
            date=w.record_date,
            morning_heart_rate=w.morning_heart_rate,
            hrv_lnrmssd=w.hrv_lnrmssd,
            sleep_duration=w.sleep_duration_hours,
            sleep_quality=w.sleep_quality,
            fatigue_score=w.fatigue_score,
            muscle_soreness=w.muscle_soreness,
            stress_score=w.stress_score,
            mood_score=w.mood_score,
            illness_flag=w.illness_flag or False,
        )
        for w in wellness_logs
    ]

    # 获取体能测试
    perf_result = await db.execute(
        select(PerformanceTest)
        .where(
            PerformanceTest.athlete_id == athlete_id,
            PerformanceTest.test_date >= date.today() - timedelta(days=90),
        )
        .order_by(PerformanceTest.test_date.asc())
    )
    perf_logs = perf_result.scalars().all()

    perf_records = [
        PerformanceRecord(
            date=p.test_date,
            squat_1rm=p.squat_1rm_kg,
            bench_press_1rm=p.bench_press_1rm_kg,
            deadlift_1rm=p.deadlift_1rm_kg,
            cmj_height=p.cmj_height_cm,
            sprint_30m=p.sprint_30m_sec,
            vo2max=p.vo2max_ml_kg_min,
        )
        for p in perf_logs
    ]

    # 获取基线值
    baselines_result = await db.execute(
        select(AthleteBaseline).where(AthleteBaseline.athlete_id == athlete_id)
    )
    all_baselines = baselines_result.scalars().all()
    baselines_dict = {b.metric_name: b.baseline_value for b in all_baselines}

    hr_baseline = baselines_dict.get("morning_heart_rate")
    hrv_baseline = baselines_dict.get("hrv_lnrmssd")

    # 获取力量基线
    strength_baseline = {k: v for k, v in baselines_dict.items()
                         if k in ("squat_1rm_kg", "bench_press_1rm_kg", "deadlift_1rm_kg", "cmj_height_cm")}

    # 计算 RSSI
    rssi_calc = RSSICalculator()
    rssi_result = rssi_calc.evaluate(
        acwr_values=acwr_tuples,
        wellness_records=wellness_records,
        performance_records=perf_records,
        hr_baseline=hr_baseline,
        hrv_baseline=hrv_baseline,
        strength_baseline=strength_baseline if strength_baseline else None,
    )

    return RSSIDetail(
        date=rssi_result.date,
        rssi_score=rssi_result.rssi_score,
        risk_level=rssi_result.risk_level.value
        if hasattr(rssi_result.risk_level, 'value') else rssi_result.risk_level,
        acwr_component=rssi_result.acwr_component,
        heart_rate_component=rssi_result.heart_rate_component,
        hrv_component=rssi_result.hrv_component,
        fatigue_component=rssi_result.fatigue_component,
        performance_component=rssi_result.performance_component,
        recommendations=rssi_result.recommendations,
        warnings=rssi_result.warnings,
    )


@router.get("/athlete/{athlete_id}/performance-comparison")
async def get_performance_comparison(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取运动员体能测试变化比较（最近一次 vs 上一次 vs 基线）"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    # 获取最近两次测试
    result = await db.execute(
        select(PerformanceTest)
        .where(PerformanceTest.athlete_id == athlete_id)
        .order_by(PerformanceTest.test_date.desc())
        .limit(2)
    )
    tests = result.scalars().all()

    if len(tests) < 2:
        return {"message": "需要至少两次测试数据进行比较", "comparisons": []}

    latest = tests[0]
    previous = tests[1]

    # 获取基线
    baselines_result = await db.execute(
        select(AthleteBaseline).where(AthleteBaseline.athlete_id == athlete_id)
    )
    baselines = {b.metric_name: b for b in baselines_result.scalars().all()}

    metrics = [
        ("深蹲 1RM (kg)", "squat_1rm_kg", latest.squat_1rm_kg, previous.squat_1rm_kg),
        ("卧推 1RM (kg)", "bench_press_1rm_kg", latest.bench_press_1rm_kg, previous.bench_press_1rm_kg),
        ("硬拉 1RM (kg)", "deadlift_1rm_kg", latest.deadlift_1rm_kg, previous.deadlift_1rm_kg),
        ("CMJ 纵跳 (cm)", "cmj_height_cm", latest.cmj_height_cm, previous.cmj_height_cm),
        ("30m冲刺 (sec)", "sprint_30m_sec", latest.sprint_30m_sec, previous.sprint_30m_sec),
        ("立定跳远 (cm)", "standing_long_jump_cm", latest.standing_long_jump_cm, previous.standing_long_jump_cm),
        ("VO₂max (ml/kg/min)", "vo2max_ml_kg_min", latest.vo2max_ml_kg_min, previous.vo2max_ml_kg_min),
    ]

    comparisons = []
    for label, key, curr, prev in metrics:
        if curr is None or prev is None or prev == 0:
            continue

        baseline = baselines.get(key)
        baseline_val = baseline.baseline_value if baseline else None
        cv_pct = baseline.typical_error * 100 / baseline.baseline_value if baseline and baseline.typical_error else 5.0

        change_pct = ((curr - prev) / prev) * 100

        sig = is_significant_change(curr, prev, cv_pct)

        # 判断方向
        lower_is_better = key == "sprint_30m_sec"  # 冲刺时间越小越好
        if lower_is_better:
            is_improvement = change_pct < 0
        else:
            is_improvement = change_pct > 0

        interpretation = ""
        if sig["is_significant"]:
            interpretation = ("显著提升! ✓" if is_improvement else "显著下降! ✗")
        else:
            interpretation = ("轻微提升" if is_improvement else "轻微下降")

        comparisons.append(PerformanceComparison(
            metric=label,
            current_value=round(curr, 2),
            previous_value=round(prev, 2),
            baseline_value=round(baseline_val, 2) if baseline_val else 0,
            change_pct=round(change_pct, 1),
            sport_avg=None,
            is_significant=sig["is_significant"],
            interpretation=interpretation,
        ))

    return {
        "athlete_id": str(athlete_id),
        "athlete_name": athlete.name,
        "latest_test_date": str(latest.test_date),
        "previous_test_date": str(previous.test_date),
        "comparisons": comparisons,
    }


@router.get("/athlete/{athlete_id}/recommendation", response_model=TrainingRecommendationResponse)
async def get_training_recommendation(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    获取个性化训练建议

    基于:
      - 当前训练周期阶段 (准备期/比赛期/过渡期)
      - ACWR 急慢性负荷比
      - RSSI 恢复-应激状态
      - 运动员各素质与项目常模对比
    """
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    # 获取最新训练日志，推测周期阶段
    log_result = await db.execute(
        select(TrainingLog)
        .where(TrainingLog.athlete_id == athlete_id)
        .order_by(TrainingLog.training_date.desc())
        .limit(1)
    )
    latest_log = log_result.scalar_one_or_none()

    cycle_phase_str = latest_log.cycle_phase if latest_log and latest_log.cycle_phase else "准备期"
    cycle_phase_map = {"准备期": CyclePhase.PREPARATION, "比赛期": CyclePhase.COMPETITION, "过渡期": CyclePhase.TRANSITION}
    cycle_phase = cycle_phase_map.get(cycle_phase_str, CyclePhase.PREPARATION)

    # 获取最新 ACWR
    metric_result = await db.execute(
        select(ComputedMetric)
        .where(ComputedMetric.athlete_id == athlete_id)
        .order_by(ComputedMetric.calc_date.desc())
        .limit(1)
    )
    latest_metric = metric_result.scalar_one_or_none()
    acwr_val = latest_metric.acwr if latest_metric else 1.0
    rssi_level = (latest_metric.rssi_risk_level or "正常") if latest_metric else "正常"

    # 获取体能测试数据，用于识别弱点
    perf_result = await db.execute(
        select(PerformanceTest)
        .where(PerformanceTest.athlete_id == athlete_id)
        .order_by(PerformanceTest.test_date.desc())
        .limit(1)
    )
    latest_test = perf_result.scalar_one_or_none()

    strengths = {}
    weaknesses = []
    if latest_test:
        if latest_test.cmj_height_cm:
            strengths["cmj_height_cm"] = latest_test.cmj_height_cm
        if latest_test.vo2max_ml_kg_min:
            strengths["vo2max_ml_kg_min"] = latest_test.vo2max_ml_kg_min
        if latest_test.sprint_30m_sec:
            strengths["sprint_30m_sec"] = latest_test.sprint_30m_sec
        if latest_test.bench_press_1rm_kg:
            strengths["bench_press_1rm_kg"] = latest_test.bench_press_1rm_kg
        if latest_test.squat_1rm_kg:
            strengths["squat_1rm_kg"] = latest_test.squat_1rm_kg

    profile = AthleteProfile(
        sport=athlete.sport,
        training_years=athlete.training_years or 1,
        cycle_phase=cycle_phase,
        recent_acwr=acwr_val,
        rssi_risk=rssi_level,
        strengths=strengths,
        weaknesses=weaknesses,
    )

    advisor = TrainingAdvisor()
    recommendation = advisor.generate(profile)

    return TrainingRecommendationResponse(
        summary=recommendation.summary,
        load_adjustment=recommendation.load_adjustment,
        intensity_recommendation=recommendation.intensity_recommendation,
        volume_recommendation=recommendation.volume_recommendation,
        frequency_recommendation=recommendation.frequency_recommendation,
        priority_areas=recommendation.priority_areas,
        recovery_strategies=recommendation.recovery_strategies,
        weekly_template=recommendation.weekly_template,
        warnings=recommendation.warnings,
    )


@router.get("/athlete/{athlete_id}/report")
async def get_athlete_report(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取运动员综合报告（前端 Reports 页面使用）"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    # 获取 ACWR 历史 (最近 90 天)
    ninety_days_ago = date.today() - timedelta(days=90)
    metric_result = await db.execute(
        select(ComputedMetric)
        .where(
            ComputedMetric.athlete_id == athlete_id,
            ComputedMetric.calc_date >= ninety_days_ago,
        )
        .order_by(ComputedMetric.calc_date.asc())
    )
    metrics = metric_result.scalars().all()
    acwr_history = [
        {"date": str(m.calc_date), "acwr": m.acwr, "risk_zone": m.acwr_risk_zone}
        for m in metrics
    ]
    rssi_history = [
        {"date": str(m.calc_date), "rssi_score": m.rssi_score, "risk_level": m.rssi_risk_level}
        for m in metrics
    ]

    # 获取最近体能测试
    perf_result = await db.execute(
        select(PerformanceTest)
        .where(PerformanceTest.athlete_id == athlete_id)
        .order_by(PerformanceTest.test_date.desc())
        .limit(5)
    )
    perf_tests = perf_result.scalars().all()
    recent_tests = [
        {
            "test_date": str(p.test_date),
            "squat_1rm_kg": p.squat_1rm_kg,
            "bench_press_1rm_kg": p.bench_press_1rm_kg,
            "deadlift_1rm_kg": p.deadlift_1rm_kg,
            "cmj_height_cm": p.cmj_height_cm,
            "vo2max_ml_kg_min": p.vo2max_ml_kg_min,
            "sprint_30m_sec": p.sprint_30m_sec,
        }
        for p in perf_tests
    ]

    # 获取教练评论 (最近 20 条)
    comments_result = await db.execute(
        select(CoachComment)
        .where(CoachComment.athlete_id == athlete_id)
        .order_by(CoachComment.created_at.desc())
        .limit(20)
    )
    coach_comments = comments_result.scalars().all()

    # 生成建议
    log_result = await db.execute(
        select(TrainingLog)
        .where(TrainingLog.athlete_id == athlete_id)
        .order_by(TrainingLog.training_date.desc())
        .limit(1)
    )
    latest_log = log_result.scalar_one_or_none()
    cycle_phase_str = latest_log.cycle_phase if latest_log and latest_log.cycle_phase else "准备期"
    cycle_phase_map = {"准备期": CyclePhase.PREPARATION, "比赛期": CyclePhase.COMPETITION, "过渡期": CyclePhase.TRANSITION}
    cycle_phase = cycle_phase_map.get(cycle_phase_str, CyclePhase.PREPARATION)

    latest_metric_data = metrics[-1] if metrics else None
    acwr_val = latest_metric_data.acwr if latest_metric_data else 1.0
    rssi_level = (latest_metric_data.rssi_risk_level or "正常") if latest_metric_data else "正常"

    strengths = {}
    if perf_tests:
        latest_test = perf_tests[0]
        if latest_test.cmj_height_cm:
            strengths["cmj_height_cm"] = latest_test.cmj_height_cm
        if latest_test.vo2max_ml_kg_min:
            strengths["vo2max_ml_kg_min"] = latest_test.vo2max_ml_kg_min
        if latest_test.bench_press_1rm_kg:
            strengths["bench_press_1rm_kg"] = latest_test.bench_press_1rm_kg
        if latest_test.squat_1rm_kg:
            strengths["squat_1rm_kg"] = latest_test.squat_1rm_kg

    profile = AthleteProfile(
        sport=athlete.sport,
        training_years=athlete.training_years or 1,
        cycle_phase=cycle_phase,
        recent_acwr=acwr_val,
        rssi_risk=rssi_level,
        strengths=strengths,
        weaknesses=[],
    )
    advisor = TrainingAdvisor()
    recommendation = advisor.generate(profile)

    return {
        "athlete": {
            "id": str(athlete.id),
            "name": athlete.name,
            "sport": athlete.sport,
            "date_of_birth": str(athlete.date_of_birth),
            "gender": athlete.gender,
            "position_role": athlete.position_role,
            "training_years": athlete.training_years,
            "hand_dominance": athlete.hand_dominance,
            "dominant_foot": athlete.dominant_foot,
            "coach_notes": athlete.coach_notes,
        },
        "acwr_history": acwr_history,
        "rssi_history": rssi_history,
        "recent_performance_tests": recent_tests,
        "coach_comments": [
            {
                "id": str(c.id),
                "comment_text": c.comment_text,
                "rating": c.rating,
                "created_at": str(c.created_at),
            }
            for c in coach_comments
        ],
        "recommendation": {
            "summary": recommendation.summary,
            "load_adjustment": recommendation.load_adjustment,
            "intensity_recommendation": recommendation.intensity_recommendation,
            "volume_recommendation": recommendation.volume_recommendation,
            "frequency_recommendation": recommendation.frequency_recommendation,
            "priority_areas": recommendation.priority_areas,
            "recovery_strategies": recommendation.recovery_strategies,
            "warnings": recommendation.warnings,
        },
    }

@router.get("/athlete/{athlete_id}/risk-score")
async def get_athlete_risk_score(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取运动员综合恢复-应激防线评分 (0-100)"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    # Get latest ACWR/RSSI from computed metrics
    metric_result = await db.execute(
        select(ComputedMetric)
        .where(ComputedMetric.athlete_id == athlete_id)
        .order_by(ComputedMetric.calc_date.desc())
        .limit(1)
    )
    latest_metric = metric_result.scalar_one_or_none()
    acwr = (latest_metric.acwr or 0) if latest_metric else 0
    acwr_zone = latest_metric.acwr_risk_zone if latest_metric else "安全区"
    rssi = (latest_metric.rssi_score or 0) if latest_metric else 0

    # Recent fatigue from DailyReadiness (last 3 days)
    fatigue_result = await db.execute(
        select(DailyReadiness.fatigue_level)
        .where(DailyReadiness.athlete_id == athlete_id)
        .order_by(DailyReadiness.record_date.desc())
        .limit(3)
    )
    fatigue_scores = [r[0] for r in fatigue_result.fetchall() if r[0] is not None]

    # Recent mental scores (last 3 logs)
    mental_result = await db.execute(
        select(MentalLog.mood_score)
        .where(MentalLog.athlete_id == athlete_id)
        .order_by(MentalLog.log_date.desc())
        .limit(3)
    )
    mental_scores = [r[0] for r in mental_result.fetchall() if r[0] is not None]

    # Nutrition risk check
    nutrition_risk = False
    nutrition_result = await db.execute(
        select(NutritionLog)
        .where(NutritionLog.athlete_id == athlete_id)
        .order_by(NutritionLog.log_date.desc())
        .limit(3)
    )
    nutrition_logs = nutrition_result.scalars().all()
    if nutrition_logs:
        low_protein = sum(1 for n in nutrition_logs if n.protein_sufficient == "否")
        if low_protein >= 2:
            nutrition_risk = True

    result = calculate_composite_risk(
        acwr=acwr,
        acwr_risk_zone=acwr_zone,
        rssi_score=rssi,
        fatigue_scores=fatigue_scores if fatigue_scores else None,
        mental_scores=mental_scores if mental_scores else None,
        nutrition_risk=nutrition_risk,
    )

    return {
        "athlete_id": str(athlete_id),
        "athlete_name": athlete.name,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "acwr_contribution": result.acwr_contribution,
        "rssi_contribution": result.rssi_contribution,
        "fatigue_contribution": result.fatigue_contribution,
        "mental_contribution": result.mental_contribution,
        "nutrition_contribution": result.nutrition_contribution,
        "recommendations": result.recommendations,
    }


@router.get("/athlete/{athlete_id}/training-status")
async def get_training_status(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Determine athlete's current training status (like Coros Training Status)."""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    metric_result = await db.execute(
        select(ComputedMetric)
        .where(ComputedMetric.athlete_id == athlete_id)
        .order_by(ComputedMetric.calc_date.desc())
        .limit(2)
    )
    metrics = metric_result.scalars().all()
    latest = metrics[0] if metrics else None
    previous = metrics[1] if len(metrics) > 1 else None

    if not latest:
        return {
            "athlete_id": str(athlete_id),
            "status": "数据不足",
            "color": "#aeaeb2",
            "description": "需要至少一周的训练数据才能评估训练状态",
            "recommendation": "请先记录训练日志和健康问卷",
            "supporting_metrics": {
                "acwr": 0, "rssi_score": 0, "acute_load": 0,
                "chronic_load": 0, "monotony": 0,
            },
        }

    acwr = latest.acwr or 0
    rssi = latest.rssi_score or 0
    rssi_level = latest.rssi_risk_level or "正常"
    acute_load = latest.acute_load_7d or 0
    chronic_load = latest.chronic_load_28d or 0
    monotony = latest.monotony or 0

    # Determine training status
    if acwr > 1.5 and rssi_level not in ("正常",):
        status, color, desc, rec = (
            "过度训练", "#ff3b30",
            "ACWR 和 RSSI 均处于高风险区间，身体恢复不足",
            "立即减量至原计划的50-70%，增加恢复日，密切监控晨起心率和HRV"
        )
    elif acwr > 1.3:
        status, color, desc, rec = (
            "负荷偏高", "#ff9500",
            "训练负荷快速增长，损伤风险中度升高",
            "建议进入维持周，将负荷降至慢性负荷水平的110%，重点补充睡眠"
        )
    elif acwr < 0.5:
        status, color, desc, rec = (
            "状态下滑", "#ffcc00",
            "训练负荷过低，可能存在去训练效应",
            "如非刻意减量，建议逐步恢复训练至慢性负荷水平的80%以上"
        )
    elif acwr < 0.8 and previous and previous.acwr and previous.acwr > 1.0:
        status, color, desc, rec = (
            "恢复减量", "#5ac8fa",
            "处于减量/恢复周，身体处于超量恢复阶段",
            "保持低强度训练，重点补充营养和睡眠，为下一周期做好准备"
        )
    elif (previous and previous.acwr and acwr >= previous.acwr * 1.1 and
          rssi_level == "正常"):
        status, color, desc, rec = (
            "高效训练", "#34c759",
            "训练负荷稳步提升，恢复状态良好，表现持续进步",
            "继续当前训练计划，适度增加负荷（周增加≤10%），保持恢复习惯"
        )
    elif 0.8 <= acwr <= 1.3:
        status, color, desc, rec = (
            "维持状态", "#007aff",
            "训练负荷稳定在安全区间，各项指标正常",
            "可继续维持当前训练节奏，根据周期目标适时调整强度"
        )
    else:
        status, color, desc, rec = (
            "维持状态", "#007aff",
            "训练负荷和恢复指标处于正常范围",
            "继续监控，根据训练目标调整负荷"
        )

    return {
        "athlete_id": str(athlete_id),
        "status": status,
        "color": color,
        "description": desc,
        "recommendation": rec,
        "supporting_metrics": {
            "acwr": round(acwr, 2),
            "rssi_score": round(rssi, 1),
            "acute_load": round(acute_load, 1),
            "chronic_load": round(chronic_load, 1),
            "monotony": round(monotony, 2),
        },
    }


@router.get("/team/weekly-summary")
async def get_team_weekly_summary(
    weeks: int = Query(12, ge=4, le=52),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated weekly training volume across all athletes from daily_metrics."""
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    # Query daily_metrics (where journal data lives) instead of training_logs
    result = await db.execute(
        select(DailyMetric.metric_date, func.sum(DailyMetric.training_load), func.count(DailyMetric.id))
        .where(
            DailyMetric.metric_date >= start_date,
            DailyMetric.metric_date <= end_date,
        )
        .group_by(DailyMetric.metric_date)
        .order_by(DailyMetric.metric_date)
    )

    weekly_map = {}
    for row in result.all():
        d = row[0]
        load = float(row[1] or 0)
        count = int(row[2] or 1)
        week_start = d - timedelta(days=d.weekday())
        week_key = week_start.isoformat()
        if week_key not in weekly_map:
            weekly_map[week_key] = {"total_load": 0, "count": 0}
        weekly_map[week_key]["total_load"] += load * count  # Aggregate across athletes
        weekly_map[week_key]["count"] += count

    weekly_data = [
        {"week_start": k, "total_load": round(v["total_load"], 1)}
        for k, v in sorted(weekly_map.items())
    ]

    return {"weeks": weeks, "weekly_data": weekly_data}


@router.get("/team/distribution")
async def get_team_training_distribution(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get training load distribution by type across all athletes from daily_metrics + training_logs."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Primary: query training_logs for type breakdown
    result = await db.execute(
        select(TrainingLog.training_type, func.sum(TrainingLog.session_load))
        .where(
            TrainingLog.training_date >= start_date,
            TrainingLog.training_date <= end_date,
        )
        .group_by(TrainingLog.training_type)
    )
    rows = result.all()

    distribution = [
        {"type": row[0] or "未知", "total_load": round(float(row[1] or 0), 1)}
        for row in rows if row[0]
    ]

    # Fallback: if no training_logs, derive from daily_metrics weekday pattern
    if not distribution:
        result2 = await db.execute(
            select(DailyMetric.metric_date, func.sum(DailyMetric.training_load))
            .where(
                DailyMetric.metric_date >= start_date,
                DailyMetric.metric_date <= end_date,
            )
            .group_by(DailyMetric.metric_date)
        )
        type_map = {}
        training_types = ["力量", "耐力", "速度", "技战术", "混合", "力量", "柔韧"]
        for row in result2.all():
            d = row[0]
            load = float(row[1] or 0)
            ttype = training_types[d.weekday() % 7]
            type_map[ttype] = type_map.get(ttype, 0) + load
        distribution = [
            {"type": k, "total_load": round(v, 1)}
            for k, v in sorted(type_map.items(), key=lambda x: -x[1])
        ]

    total = sum(d["total_load"] for d in distribution)
    for d in distribution:
        d["percentage"] = round((d["total_load"] / total * 100), 1) if total > 0 else 0

    return {"days": days, "total_load": round(total, 1), "distribution": distribution}


@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Dashboard KPI summary with 7-day risk trends."""
    today = date.today()
    seven_days_ago = today - timedelta(days=7)

    # All athletes
    athletes_result = await db.execute(select(Athlete))
    athletes = athletes_result.scalars().all()

    # Unresolved alerts
    alerts_result = await db.execute(
        select(AlertEvent).where(AlertEvent.is_resolved == False)
    )
    unresolved_alerts = alerts_result.scalars().all()
    unresolved_count = len(unresolved_alerts)

    # 7-day metrics for risk trends
    metrics_result = await db.execute(
        select(DailyMetric)
        .where(DailyMetric.metric_date >= seven_days_ago)
        .order_by(DailyMetric.metric_date.asc())
    )
    all_metrics = metrics_result.scalars().all()

    # Aggregate by date
    daily_avgs = {}
    for m in all_metrics:
        d = str(m.metric_date)
        if d not in daily_avgs:
            daily_avgs[d] = {
                "shoulder_sum": 0, "knee_sum": 0, "fatigue_sum": 0, "count": 0
            }
        daily_avgs[d]["shoulder_sum"] += (m.shoulder_overuse_risk or 0)
        daily_avgs[d]["knee_sum"] += (m.knee_overuse_risk or 0)
        daily_avgs[d]["fatigue_sum"] += (m.fatigue or 0)
        daily_avgs[d]["count"] += 1

    risk_trend = []
    for d in sorted(daily_avgs.keys()):
        agg = daily_avgs[d]
        n = agg["count"] or 1
        risk_trend.append({
            "date": d,
            "avg_shoulder_risk": round(agg["shoulder_sum"] / n, 1),
            "avg_knee_risk": round(agg["knee_sum"] / n, 1),
            "avg_fatigue": round(agg["fatigue_sum"] / n, 1),
        })

    # Top 10 highest risk athletes from any recent day (last 3 days)
    recent_metrics = [m for m in all_metrics if m.metric_date >= today - timedelta(days=3)]
    athlete_risk_map = {}
    for m in recent_metrics:
        max_risk = max(
            m.shoulder_overuse_risk or 0, m.shoulder_acute_risk or 0,
            m.knee_overuse_risk or 0, m.knee_acute_risk or 0,
        )
        aid = str(m.athlete_id)
        if aid not in athlete_risk_map or max_risk > athlete_risk_map[aid]["max_risk"]:
            athlete_risk_map[aid] = {"athlete_id": aid, "max_risk": round(max_risk, 1)}
    athlete_risks = sorted(athlete_risk_map.values(), key=lambda x: x["max_risk"], reverse=True)
    top10 = athlete_risks[:10]

    # Get athlete names for top10
    athlete_map = {str(a.id): a.name for a in athletes}
    top10_with_names = [
        {**r, "athlete_name": athlete_map.get(r["athlete_id"], "未知")}
        for r in top10
    ]

    # If no recent metrics, get all-time top risks
    if not top10_with_names and all_metrics:
        all_athlete_risk_map = {}
        for m in all_metrics:
            max_risk = max(
                m.shoulder_overuse_risk or 0, m.shoulder_acute_risk or 0,
                m.knee_overuse_risk or 0, m.knee_acute_risk or 0,
            )
            aid = str(m.athlete_id)
            if aid not in all_athlete_risk_map or max_risk > all_athlete_risk_map[aid]["max_risk"]:
                all_athlete_risk_map[aid] = {"athlete_id": aid, "max_risk": round(max_risk, 1)}
        all_athlete_risks = sorted(all_athlete_risk_map.values(), key=lambda x: x["max_risk"], reverse=True)
        top10_with_names = [
            {**r, "athlete_name": athlete_map.get(r["athlete_id"], "未知")}
            for r in all_athlete_risks[:10]
        ]

    # Average fatigue across all athletes (most recent metrics)
    latest_metrics = {}
    for m in all_metrics:
        aid = str(m.athlete_id)
        if aid not in latest_metrics or m.metric_date > latest_metrics[aid].metric_date:
            latest_metrics[aid] = m
    avg_fatigue = round(
        sum(m.fatigue or 0 for m in latest_metrics.values()) / max(len(latest_metrics), 1), 1
    )

    return {
        "high_risk_count": sum(1 for r in top10_with_names if r["max_risk"] > 70),
        "avg_fatigue": avg_fatigue,
        "unresolved_alerts": unresolved_count,
        "risk_trend_7d": risk_trend,
        "top10_risks": top10_with_names,
    }


@router.get("/standards")
async def get_sport_standards_api(sport: str = "篮球"):
    """获取指定项目的中国运动员等级标准"""
    if sport not in SPORT_STANDARDS:
        sport = "其他"
    return {
        "sport": sport,
        "levels": LEVELS,
        "metrics": SPORT_STANDARDS[sport],
    }


@router.get("/athlete/{athlete_id}/level")
async def get_athlete_level_api(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    """评估运动员在各指标上的等级"""
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    result = await db.execute(
        select(PerformanceTest)
        .where(PerformanceTest.athlete_id == athlete_id)
        .order_by(PerformanceTest.test_date.desc())
        .limit(1)
    )
    latest_test = result.scalar_one_or_none()

    assessments = []
    if latest_test:
        metric_map = {
            "深蹲1RM (kg)": latest_test.squat_1rm_kg,
            "卧推1RM (kg)": latest_test.bench_press_1rm_kg,
            "硬拉1RM (kg)": latest_test.deadlift_1rm_kg,
            "CMJ纵跳 (cm)": latest_test.cmj_height_cm,
            "30m冲刺 (s)": latest_test.sprint_30m_sec,
            "VO2max (ml/kg/min)": latest_test.vo2max_ml_kg_min,
            "立定跳远 (cm)": latest_test.standing_long_jump_cm,
        }
        for metric, value in metric_map.items():
            if value is not None:
                level_info = get_athlete_level(metric, value, athlete.gender, athlete.sport)
                assessments.append({
                    "metric": metric,
                    "value": value,
                    **level_info,
                })

    return {
        "athlete_id": str(athlete_id),
        "athlete_name": athlete.name,
        "sport": athlete.sport,
        "gender": athlete.gender,
        "assessments": assessments,
    }
