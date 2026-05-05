"""
AthleteIQ - 减量/减载建议模块
基于 NSCA-CSCS 和 CPSS 标准检测需要减量的场景并生成减载周模板
"""
from __future__ import annotations
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import date, timedelta
import numpy as np


@dataclass
class DeloadSuggestion:
    suggestion: bool
    reason: str
    template: List[Dict] = field(default_factory=list)
    restore_days: int = 5
    volume_reduction_pct: float = 40.0
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AthleteDailyData:
    date: date
    acwr: float
    hrv_lnrmssd: Optional[float] = None
    morning_heart_rate: Optional[int] = None
    readiness_score: Optional[float] = None
    fatigue_score: Optional[int] = None
    sleep_quality: Optional[int] = None


def should_suggest_deload(
    athlete_data: List[AthleteDailyData],
    acwr_threshold: float = 1.3,
    acwr_days: int = 14,
    hrv_decline_threshold: float = -10.0,
    readiness_decline_threshold: float = -15.0,
) -> DeloadSuggestion:
    """
    判断是否需要建议减量/减载

    Args:
        athlete_data: 运动员每日数据列表，按日期排序 (最近在前)
        acwr_threshold: ACWR 阈值，超过此值视为负荷过高
        acwr_days: 需要连续超过阈值的天数
        hrv_decline_threshold: HRV 下降百分比阈值 (负值表示下降)
        readiness_decline_threshold: 准备度分数下降百分比阈值

    Returns:
        DeloadSuggestion with suggestion flag, reason, and template
    """
    if not athlete_data or len(athlete_data) < 7:
        return DeloadSuggestion(
            suggestion=False,
            reason="数据不足，需要至少 7 天的数据来评估减量需求",
        )

    data_sorted = sorted(athlete_data, key=lambda x: x.date)

    # 1. 检查 ACWR 是否持续偏高
    recent_acwr = [d.acwr for d in data_sorted[-acwr_days:]]
    acwr_high = all(a > acwr_threshold for a in recent_acwr if a > 0)

    # 2. 检查 HRV 下降趋势
    hrv_values = [d.hrv_lnrmssd for d in data_sorted if d.hrv_lnrmssd is not None]
    hrv_declining = False
    hrv_change_pct = 0.0
    if len(hrv_values) >= 7:
        recent_hrv = hrv_values[-7:]
        baseline_hrv = np.mean(hrv_values)
        if baseline_hrv > 0:
            avg_recent = np.mean(recent_hrv)
            hrv_change_pct = ((avg_recent - baseline_hrv) / baseline_hrv) * 100
            hrv_declining = hrv_change_pct < hrv_decline_threshold

    # 3. 检查准备度分数趋势
    readiness_values = [d.readiness_score for d in data_sorted if d.readiness_score is not None]
    readiness_declining = False
    if len(readiness_values) >= 7:
        recent_readiness = readiness_values[-7:]
        baseline_readiness = np.mean(readiness_values)
        if baseline_readiness > 0:
            avg_recent_r = np.mean(recent_readiness)
            readiness_change_pct = ((avg_recent_r - baseline_readiness) / baseline_readiness) * 100
            readiness_declining = readiness_change_pct < readiness_decline_threshold

    # 4. 主观疲劳检查
    fatigue_scores = [d.fatigue_score for d in data_sorted[-7:] if d.fatigue_score is not None]
    high_fatigue = np.mean(fatigue_scores) >= 4 if fatigue_scores else False

    # 综合判断
    trigger_conditions = []
    if acwr_high:
        trigger_conditions.append(f"ACWR > {acwr_threshold} 已持续 {acwr_days} 天以上")
    if hrv_declining:
        trigger_conditions.append(f"HRV 下降 {abs(hrv_change_pct):.1f}% (超过 {abs(hrv_decline_threshold)}% 阈值)")
    if readiness_declining:
        trigger_conditions.append("准备度分数持续下降")

    should_deload = (acwr_high and (hrv_declining or readiness_declining)) or (acwr_high and high_fatigue)

    if acwr_high and hrv_declining:
        main_reason = f"ACWR 持续偏高 ({acwr_threshold}+) 且 HRV 呈下降趋势。建议安排减载周。"
    elif acwr_high and readiness_declining:
        main_reason = f"ACWR 持续偏高 ({acwr_threshold}+) 且运动员准备度分数下降。建议安排减载周。"
    elif acwr_high and high_fatigue:
        main_reason = f"ACWR 持续偏高 ({acwr_threshold}+) 且运动员主观疲劳较高。建议安排减载周。"
    elif acwr_high:
        main_reason = f"ACWR 持续偏高 ({acwr_threshold}+)，虽无其他指标恶化但仍建议考虑减量。"
        should_deload = True
    else:
        main_reason = "当前指标在可接受范围内，无需强制减量。"

    if not should_deload:
        return DeloadSuggestion(
            suggestion=False,
            reason=main_reason,
            recommendations=["继续监测 ACWR、HRV 和准备度分数。"],
        )

    # 生成减载周模板
    template, recs, warns = _generate_deload_template()

    return DeloadSuggestion(
        suggestion=True,
        reason=main_reason,
        template=template,
        restore_days=7,
        volume_reduction_pct=40.0,
        recommendations=recs + [
            "保持训练强度（重量/RPE），但降低训练容量（组数×次数）40-50%。",
            "每日监测晨起心率和 HRV，确保在减载期间恢复指标回暖。",
            "增加高质量睡眠时间至 8-9 小时。",
        ],
        warnings=warns,
    )


def _generate_deload_template() -> tuple:
    """生成减载周训练模板"""
    template = [
        {"day": "周一", "session_name": "轻量力量维持 (强度保持)", "training_type": "力量",
         "duration_min": 50, "rpe_target": 6, "load_pct": "80-85% 1RM, 组数减半",
         "notes": "保持强度，大幅减少容量。每个动作 2 组代替常规 4 组。"},
        {"day": "周二", "session_name": "低强度有氧恢复", "training_type": "耐力",
         "duration_min": 35, "rpe_target": 3, "load_pct": "< 60% HRmax",
         "notes": "轻松骑行或游泳，促进血液循环。"},
        {"day": "周三", "session_name": "泡沫轴放松 + 核心激活", "training_type": "柔韧",
         "duration_min": 40, "rpe_target": 3, "load_pct": "自重",
         "notes": "全泡沫轴放松 + 15分钟核心训练（平板支撑、鸟狗式）。"},
        {"day": "周四", "session_name": "轻量爆发力维持", "training_type": "力量",
         "duration_min": 45, "rpe_target": 5, "load_pct": "50-60% 1RM, 爆发速度",
         "notes": "低负荷高速度，保持神经肌肉适应性。"},
        {"day": "周五", "session_name": "主动恢复日", "training_type": "柔韧",
         "duration_min": 30, "rpe_target": 2, "load_pct": "恢复",
         "notes": "拉伸 + 冷水浸泡（可选）+ 冥想。"},
        {"day": "周六", "session_name": "轻松交叉训练", "training_type": "混合",
         "duration_min": 45, "rpe_target": 4, "load_pct": "< 60% 最大",
         "notes": "游泳/自行车/散步，享受非竞技运动。"},
        {"day": "周日", "session_name": "完全休息日", "training_type": "柔韧",
         "duration_min": 0, "rpe_target": 0, "load_pct": "完全休息",
         "notes": "无训练，优先睡眠和营养恢复。"},
    ]

    recommendations = [
        "本周训练总容量建议降低 40%，但保持训练强度以维持神经适应。",
        "利用减载周进行额外恢复：运动按摩、充足的蛋白质摄入、高质量睡眠。",
        "下周恢复训练时，负荷增加不超过减载前水平的 80%，然后每周递增 5-10%。",
    ]

    warnings = [
        "减载期间如出现反常疲劳加重或静息心率持续升高，建议进一步降低强度并咨询运动医学专家。",
    ]

    return template, recommendations, warnings
