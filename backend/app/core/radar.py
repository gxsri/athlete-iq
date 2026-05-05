"""
AthleteIQ - 运动员能力雷达图分析模块
基于 CSCS 体能测试标准，将测试数据映射到雷达图维度
"""
from __future__ import annotations
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import numpy as np


@dataclass
class RadarChartData:
    metric_names: List[str] = field(default_factory=list)
    current_values: List[float] = field(default_factory=list)
    best_values: List[float] = field(default_factory=list)
    norm_low: List[float] = field(default_factory=list)
    norm_high: List[float] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


# 运动项目测试常模 (CSCS 参考值)
SPORT_NORMS: Dict[str, Dict[str, Dict[str, float]]] = {
    "篮球": {
        "squat_1rm_kg": {"low": 100, "high": 160, "unit": "kg"},
        "bench_press_1rm_kg": {"low": 70, "high": 120, "unit": "kg"},
        "deadlift_1rm_kg": {"low": 120, "high": 180, "unit": "kg"},
        "cmj_height_cm": {"low": 45, "high": 65, "unit": "cm"},
        "sprint_30m_sec": {"low": 4.5, "high": 3.9, "unit": "sec"},
        "vo2max_ml_kg_min": {"low": 45, "high": 60, "unit": "ml/kg/min"},
        "rfd_n_per_s": {"low": 3000, "high": 6000, "unit": "N/s"},
        "med_ball_throw_m": {"low": 8, "high": 12, "unit": "m"},
        "standing_long_jump_cm": {"low": 200, "high": 260, "unit": "cm"},
    },
    "足球": {
        "squat_1rm_kg": {"low": 100, "high": 180, "unit": "kg"},
        "bench_press_1rm_kg": {"low": 60, "high": 110, "unit": "kg"},
        "deadlift_1rm_kg": {"low": 120, "high": 200, "unit": "kg"},
        "cmj_height_cm": {"low": 40, "high": 62, "unit": "cm"},
        "sprint_30m_sec": {"low": 4.4, "high": 3.8, "unit": "sec"},
        "vo2max_ml_kg_min": {"low": 50, "high": 65, "unit": "ml/kg/min"},
        "rfd_n_per_s": {"low": 2500, "high": 5500, "unit": "N/s"},
        "med_ball_throw_m": {"low": 6, "high": 10, "unit": "m"},
        "standing_long_jump_cm": {"low": 190, "high": 250, "unit": "cm"},
    },
    "游泳": {
        "squat_1rm_kg": {"low": 80, "high": 140, "unit": "kg"},
        "bench_press_1rm_kg": {"low": 50, "high": 100, "unit": "kg"},
        "deadlift_1rm_kg": {"low": 100, "high": 160, "unit": "kg"},
        "cmj_height_cm": {"low": 35, "high": 55, "unit": "cm"},
        "sprint_30m_sec": {"low": 4.6, "high": 4.1, "unit": "sec"},
        "vo2max_ml_kg_min": {"low": 45, "high": 65, "unit": "ml/kg/min"},
        "rfd_n_per_s": {"low": 2000, "high": 4500, "unit": "N/s"},
    },
    "田径": {
        "squat_1rm_kg": {"low": 110, "high": 200, "unit": "kg"},
        "bench_press_1rm_kg": {"low": 70, "high": 130, "unit": "kg"},
        "deadlift_1rm_kg": {"low": 130, "high": 220, "unit": "kg"},
        "cmj_height_cm": {"low": 45, "high": 70, "unit": "cm"},
        "sprint_30m_sec": {"low": 4.3, "high": 3.7, "unit": "sec"},
        "vo2max_ml_kg_min": {"low": 48, "high": 68, "unit": "ml/kg/min"},
        "rfd_n_per_s": {"low": 3500, "high": 7000, "unit": "N/s"},
    },
    "排球": {
        "squat_1rm_kg": {"low": 90, "high": 150, "unit": "kg"},
        "bench_press_1rm_kg": {"low": 55, "high": 100, "unit": "kg"},
        "deadlift_1rm_kg": {"low": 100, "high": 170, "unit": "kg"},
        "cmj_height_cm": {"low": 45, "high": 70, "unit": "cm"},
        "sprint_30m_sec": {"low": 4.5, "high": 4.0, "unit": "sec"},
        "vo2max_ml_kg_min": {"low": 42, "high": 55, "unit": "ml/kg/min"},
        "rfd_n_per_s": {"low": 3000, "high": 6000, "unit": "N/s"},
    },
}

# 测试指标到雷达维度的映射
METRIC_TO_DIMENSION = {
    "squat_1rm_kg": "力量",
    "bench_press_1rm_kg": "力量",
    "deadlift_1rm_kg": "力量",
    "cmj_height_cm": "爆发力",
    "rfd_n_per_s": "爆发力",
    "med_ball_throw_m": "爆发力",
    "sprint_30m_sec": "速度",
    "standing_long_jump_cm": "爆发力",
    "vo2max_ml_kg_min": "代谢",
    "lactate_threshold_power_w": "代谢",
}

# 雷达维度定义
RADAR_DIMENSIONS = ["力量", "爆发力", "速度", "代谢", "敏捷"]


def _normalize_to_0_100(
    value: float,
    norm_low: float,
    norm_high: float,
    lower_is_better: bool = False,
) -> float:
    """将值标准化到 0-100 范围"""
    if norm_high == norm_low:
        return 50.0
    normalized = ((value - norm_low) / (norm_high - norm_low)) * 100
    normalized = max(0.0, min(100.0, normalized))
    if lower_is_better:
        normalized = 100.0 - normalized
    return round(normalized, 1)


def _aggregate_dimension(
    metrics: Dict[str, float],
    norms: Dict[str, Dict[str, float]],
    dimension: str,
) -> tuple:
    """将多个指标聚合到单一维度分数"""
    dim_metrics = [m for m, d in METRIC_TO_DIMENSION.items() if d == dimension and m in metrics and m in norms]
    if not dim_metrics:
        return 0.0, 0.0, 0.0, 0.0

    scores = []
    norm_lows = []
    norm_highs = []
    for m in dim_metrics:
        val = metrics[m]
        n_low = norms[m]["low"]
        n_high = norms[m]["high"]
        lower_is_better = m == "sprint_30m_sec"
        score = _normalize_to_0_100(val, n_low, n_high, lower_is_better)
        scores.append(score)
        norm_lows.append(n_low)
        norm_highs.append(n_high)

    avg_score = np.mean(scores)
    avg_norm_low = np.mean(norm_lows)
    avg_norm_high = np.mean(norm_highs)

    return round(avg_score, 1), 0.0, round(avg_norm_low, 1), round(avg_norm_high, 1)


def compute_radar_data(
    athlete_id: str,
    sport: str,
    latest_tests: Dict[str, float],
    baselines: Optional[Dict[str, float]] = None,
    norms: Optional[Dict[str, Dict[str, float]]] = None,
) -> RadarChartData:
    """
    计算运动员雷达图数据

    Args:
        athlete_id: 运动员 ID
        sport: 运动项目 (用于查找对应的常模)
        latest_tests: 最新测试数据 {"metric_name": value, ...}
        baselines: 个人基线测试数据 {"metric_name": best_value, ...}
        norms: 自定义常模，为 None 时使用内置 SPORT_NORMS

    Returns:
        RadarChartData with normalized metric values and weakness identification
    """
    if norms is None:
        norms = SPORT_NORMS.get(sport, {})

    if not norms:
        return RadarChartData(
            metric_names=RADAR_DIMENSIONS,
            current_values=[0] * len(RADAR_DIMENSIONS),
            best_values=[0] * len(RADAR_DIMENSIONS),
            norm_low=[0] * len(RADAR_DIMENSIONS),
            norm_high=[0] * len(RADAR_DIMENSIONS),
            weaknesses=[],
        )

    baselines = baselines or {}
    metric_names = RADAR_DIMENSIONS[:]
    current_values = []
    best_values = []
    norm_lows = []
    norm_highs = []
    weaknesses = []

    for dim in metric_names:
        curr, best, n_low, n_high = _aggregate_dimension(latest_tests, norms, dim)
        current_values.append(curr)
        norm_lows.append(n_low)
        norm_highs.append(n_high)

        best = 0.0
        if baselines:
            best, _, _, _ = _aggregate_dimension(baselines, norms, dim)
        best_values.append(best)

        # 弱点判断：当前值低于常模下限 1 SD (约 25% 的标准化范围)
        if curr < 25.0:
            weaknesses.append(dim)

    return RadarChartData(
        metric_names=metric_names,
        current_values=current_values,
        best_values=best_values,
        norm_low=norm_lows,
        norm_high=norm_highs,
        weaknesses=weaknesses,
    )
