"""
============================================================================
AthleteIQ - 统计函数模块
基于 NSCA-CSCS 最小有效差异 (SWC) 和典型误差 (TE)

CV% (变异系数) = (SD / Mean) × 100
典型误差 (TE) = SD_diff / √2

临床重要差异判定:
  - 变化量 > 2×TE 视为 "可能显著变化"
  - 变化量 > SWC 且 > TE 视为 "有价值的变化"
============================================================================
"""
from __future__ import annotations
from typing import List, Optional
import numpy as np


def coefficient_of_variation(data: List[float]) -> float:
    """计算变异系数 (CV%)"""
    if not data or len(data) < 2:
        return 0.0
    mean = np.mean(data)
    if mean == 0:
        return 0.0
    return round((np.std(data, ddof=1) / mean) * 100, 2)


def typical_error(test_retest_values: List[tuple]) -> float:
    """
    计算典型误差 (Typical Error, TE)
    TE = SD_diff / √2

    Args:
        test_retest_values: [(test1, test2), ...] 配对的测试-重测数据
    """
    diffs = [abs(a - b) for a, b in test_retest_values if a is not None and b is not None]
    if len(diffs) < 2:
        return 0.0
    sd_diff = np.std(diffs, ddof=1)
    return round(sd_diff / np.sqrt(2), 3)


def smallest_worthwhile_change(mean_performance: float, cohen_d: float = 0.2) -> float:
    """
    计算最小有效差异 (Smallest Worthwhile Change, SWC)
    基于 Cohen's d = 0.2 (小效果量)

    SWC = 0.2 × between-subject SD
    若无群体 SD，使用 0.5 × CV% × Mean
    """
    # 简化：使用 0.2 × 平均值作为最小效果量
    return round(cohen_d * mean_performance, 2)


def is_significant_change(
    current_value: float,
    baseline_value: float,
    cv_pct: float,
    multiplier: float = 2.0,
) -> dict:
    """
    判断变化是否显著

    基于 Hopkins (2004) 和 NSCA 体能测试指南:
      - 变化量 > multiplier × TE → 可能显著变化
      - multiplier = 1.0: 可能 (possibly)
      - multiplier = 2.0: 很有可能 (very likely)

    Returns:
        dict with: is_significant, change_pct, magnitude, confidence
    """
    if baseline_value == 0:
        return {"is_significant": False, "change_pct": 0, "magnitude": "无法判定", "confidence": "低"}

    change_pct = ((current_value - baseline_value) / baseline_value) * 100
    te = (cv_pct / 100) * baseline_value / np.sqrt(2) if cv_pct > 0 else 0

    if te == 0:
        return {"is_significant": abs(change_pct) > 5, "change_pct": round(change_pct, 1),
                "magnitude": _classify_change(change_pct), "confidence": "中"}

    ratio = abs(current_value - baseline_value) / (multiplier * te)

    is_significant = ratio > 1.0

    if ratio > 2.0:
        confidence = "高"
    elif ratio > 1.0:
        confidence = "中"
    else:
        confidence = "低"

    return {
        "is_significant": is_significant,
        "change_pct": round(change_pct, 1),
        "te": round(te, 3),
        "ratio_to_te": round(ratio, 3),
        "magnitude": _classify_change(change_pct),
        "confidence": confidence,
    }


def _classify_change(pct: float) -> str:
    """分类变化幅度"""
    abs_pct = abs(pct)
    if abs_pct < 0.5:
        return "无变化"
    elif abs_pct < 2.0:
        return "微小变化"
    elif abs_pct < 5.0:
        return "中等变化"
    else:
        return "显著变化" if pct > 0 else "显著下降"


def rolling_average(data: List[float], window: int) -> List[float]:
    """滚动平均值"""
    if len(data) < window:
        return []
    return [np.mean(data[i:i + window]) for i in range(len(data) - window + 1)]


def z_score(value: float, population: List[float]) -> float:
    """计算 Z-Score"""
    if len(population) < 2:
        return 0.0
    mean = np.mean(population)
    std = np.std(population, ddof=1)
    if std == 0:
        return 0.0
    return round((value - mean) / std, 3)


def detect_hrv_suppression(hrv_values: List[float], days: int = 7) -> dict:
    """
    检测 HRV 抑制 (Plews et al., 2013)

    判定标准:
      - LnRMSSD 7日滚动平均低于基线 80% → 副交感神经抑制
      - 连续下降趋势 → 需要恢复
    """
    if len(hrv_values) < days:
        return {"suppressed": False, "trend": "数据不足"}

    recent = hrv_values[-days:]
    baseline = np.mean(hrv_values)

    recent_avg = np.mean(recent)
    ratio = recent_avg / baseline if baseline > 0 else 1.0

    # 趋势检测
    x = np.arange(len(recent))
    slope = np.polyfit(x, recent, 1)[0]

    suppressed = False
    if ratio < 0.80:
        suppressed = True
    elif ratio < 0.90 and slope < 0:
        suppressed = True  # 接近阈值且有下降趋势

    if slope < -0.5:
        trend = "明显下降"
    elif slope < -0.2:
        trend = "轻微下降"
    elif slope > 0.5:
        trend = "明显上升"
    elif slope > 0.2:
        trend = "轻微上升"
    else:
        trend = "稳定"

    return {
        "suppressed": suppressed,
        "trend": trend,
        "recent_avg": round(recent_avg, 2),
        "baseline": round(baseline, 2),
        "ratio_pct": round(ratio * 100, 1),
        "slope": round(slope, 3),
    }
