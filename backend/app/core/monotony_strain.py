"""
============================================================================
AthleteIQ - 单调性与训练应变计算模块
基于 NSCA-CSCS / CPSS 标准 (Foster, 1998; Foster et al., 2001)

单调性 (Monotony) = 日均训练负荷 / 负荷标准差
  高单调性 (> 2.0) 意味着训练模式过于单一，与过度训练和疾病风险相关

训练应变 (Strain) = 周总负荷 × 单调性
  高应变值伴随增加的过度训练和受伤风险
============================================================================
"""
from __future__ import annotations
from typing import List
from dataclasses import dataclass
from datetime import date, timedelta
import numpy as np


@dataclass
class MonotonyStrainResult:
    """单调性 & 应变计算结果"""
    period_start: date
    period_end: date
    num_sessions: int
    total_load: float
    mean_daily_load: float
    load_std: float
    monotony: float
    strain: float
    monotony_risk: str      # '正常', '偏高', '需注意'
    strain_risk: str        # '正常', '偏高', '需注意'
    strain_zscore: float    # 与历史基线比较


class MonotonyCalculator:
    """
    训练单调性与应变计算器

    使用方法:
        calc = MonotonyCalculator()
        result = calc.calculate(sessions, period_days=7)
    """

    def __init__(self, monotony_threshold_high: float = 2.0, monotony_threshold_caution: float = 1.5):
        self.monotony_threshold_high = monotony_threshold_high
        self.monotony_threshold_caution = monotony_threshold_caution

    def calculate(
        self,
        daily_loads: List[float],
        period_start: date,
        period_end: date,
        historical_strains: List[float] = None,
    ) -> MonotonyStrainResult:
        """
        计算训练单调性与应变

        Args:
            daily_loads: 每日训练负荷列表
            period_start: 周期开始日期
            period_end: 周期结束日期
            historical_strains: 历史应变值列表，用于计算Z-Score
        """
        daily_loads = [l for l in daily_loads if l > 0]
        n = len(daily_loads)

        if n < 2:
            return MonotonyStrainResult(
                period_start=period_start, period_end=period_end,
                num_sessions=n, total_load=sum(daily_loads),
                mean_daily_load=sum(daily_loads) if n else 0,
                load_std=0, monotony=0, strain=0,
                monotony_risk="正常", strain_risk="正常",
                strain_zscore=0.0,
            )

        total_load = sum(daily_loads)
        mean_load = np.mean(daily_loads)
        load_std = float(np.std(daily_loads, ddof=1))  # 样本标准差

        # 单调性 = 日均负荷 / 负荷标准差 (Foster, 1998)
        if load_std > 0:
            monotony = round(mean_load / load_std, 3)
        else:
            monotony = float('inf') if mean_load > 0 else 0.0

        # 应变 = 总负荷 × 单调性
        strain = round(total_load * monotony, 1) if monotony != float('inf') else float('inf')

        # 单调性风险评估
        if monotony > self.monotony_threshold_high:
            monotony_risk = "需注意"
        elif monotony > self.monotony_threshold_caution:
            monotony_risk = "偏高"
        else:
            monotony_risk = "正常"

        # 应变 Z-Score (与历史数据比较)
        strain_zscore = 0.0
        if historical_strains and len(historical_strains) > 1:
            hist_mean = np.mean(historical_strains)
            hist_std = np.std(historical_strains, ddof=1)
            if hist_std > 0:
                strain_zscore = round((strain - hist_mean) / hist_std, 3)

        # 应变风险评估 (Z-Score > 2 视为异常)
        if strain_zscore > 2.0:
            strain_risk = "需注意"
        elif strain_zscore > 1.0:
            strain_risk = "偏高"
        else:
            strain_risk = "正常"

        return MonotonyStrainResult(
            period_start=period_start, period_end=period_end,
            num_sessions=n, total_load=round(total_load, 1),
            mean_daily_load=round(mean_load, 1),
            load_std=round(load_std, 1),
            monotony=monotony,
            strain=strain,
            monotony_risk=monotony_risk,
            strain_risk=strain_risk,
            strain_zscore=strain_zscore,
        )

    def rolling_strain(
        self,
        daily_loads: List[float],
        dates: List[date],
        window_days: int = 7,
    ) -> List[MonotonyStrainResult]:
        """滚动计算应变值（滑动窗口）"""
        results = []
        for end_idx in range(window_days, len(daily_loads) + 1):
            start_idx = max(0, end_idx - window_days)
            window_loads = daily_loads[start_idx:end_idx]
            result = self.calculate(
                window_loads,
                period_start=dates[start_idx],
                period_end=dates[end_idx - 1],
            )
            results.append(result)
        return results
