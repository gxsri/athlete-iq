"""
============================================================================
AthleteIQ - ACWR (急慢性负荷比) 计算模块
基于 NSCA-CSCS / CPSS 标准

急性负荷: 7天滚动平均 session load
慢性负荷: 28天滚动平均 session load
ACWR = 急性负荷 / 慢性负荷

风险区间 (NSCA 共识, IJSPP 2016; Gabbett 2016):
  0.8 - 1.3 : 安全区 (最佳训练窗口, injury risk minimized)
  1.3 - 1.5 : 谨慎区 (中等风险, 需观察恢复指标)
  > 1.5     : 高风险区 (损伤风险显著升高 2-4x)
  < 0.8     : 显著减量区 (可能训练不足, 或故意减量)
============================================================================
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import date, timedelta
import numpy as np


@dataclass
class TrainingSession:
    """单次训练课"""
    date: date
    session_load: float  # duration_minutes × RPE
    training_type: str


@dataclass
class ACWRResult:
    """ACWR 计算结果"""
    date: date
    acute_load: float       # 7天滚动平均
    chronic_load: float     # 28天滚动平均
    acwr: float
    risk_zone: str          # '安全区' / '谨慎区' / '高风险区'
    risk_description: str
    acute_daily_loads: List[float]  # 急性窗口内的每日负荷
    chronic_daily_loads: List[float]  # 慢性窗口内的每日负荷


class ACWRCalculator:
    """
    急慢性负荷比计算器

    使用方法:
        calc = ACWRCalculator(acute_window=7, chronic_window=28)
        result = calc.calculate(sessions, target_date)
    """

    def __init__(self, acute_window: int = 7, chronic_window: int = 28):
        self.acute_window = acute_window
        self.chronic_window = chronic_window

    def calculate(self, sessions: List[TrainingSession], target_date: date) -> ACWRResult:
        """计算指定日期的 ACWR"""
        acute_start = target_date - timedelta(days=self.acute_window)
        chronic_start = target_date - timedelta(days=self.chronic_window)

        acute_sessions = [
            s for s in sessions
            if acute_start < s.date <= target_date
        ]
        chronic_sessions = [
            s for s in sessions
            if chronic_start < s.date <= target_date
        ]

        acute_loads = [s.session_load for s in acute_sessions]
        chronic_loads = [s.session_load for s in chronic_sessions]

        acute_avg = float(np.mean(acute_loads)) if acute_loads else 0.0
        chronic_avg = float(np.mean(chronic_loads)) if chronic_loads else 0.0

        if chronic_avg > 0:
            acwr = round(float(acute_avg / chronic_avg), 3)
        else:
            acwr = 0.0

        zone, description = self._classify_risk(acwr)

        return ACWRResult(
            date=target_date,
            acute_load=round(float(acute_avg), 1),
            chronic_load=round(float(chronic_avg), 1),
            acwr=float(acwr),
            risk_zone=zone,
            risk_description=description,
            acute_daily_loads=acute_loads,
            chronic_daily_loads=chronic_loads,
        )

    @staticmethod
    def _classify_risk(acwr: float) -> Tuple[str, str]:
        """
        NSCA 共识风险区间划分
        参考: Gabbett TJ (2016). "The training-injury prevention paradox:
        should athletes be training smarter and harder?"
        """
        if acwr == 0:
            return ("安全区", "暂无足够数据评估")
        elif 0.8 <= acwr <= 1.3:
            return ("安全区", "处于最佳训练窗口，损伤风险最低。建议维持当前进度。")
        elif 1.3 < acwr <= 1.5:
            return ("谨慎区", "训练负荷快速增加，损伤风险中度升高（约2倍）。建议密切监控恢复指标，确保睡眠和营养充足。")
        elif acwr > 1.5:
            return ("高风险区", "急性负荷远高于慢性负荷，损伤风险升高4-5倍。建议立即降低训练量或强度。")
        else:  # < 0.8
            return ("高风险区", "负荷显著降低。如果是计划内减量（Taper），属于正常；否则需评估是否训练不足。")

    def calculate_timeseries(self, sessions: List[TrainingSession]) -> List[ACWRResult]:
        """计算完整时间序列的 ACWR"""
        if not sessions:
            return []

        sessions_sorted = sorted(sessions, key=lambda s: s.date)
        unique_dates = sorted(set(s.date for s in sessions_sorted))

        # 需要有足够的数据点来计算（至少需要7天+的数据）
        results = []
        for d in unique_dates:
            # 只计算有至少14天历史数据的日期
            if (d - unique_dates[0]).days >= self.acute_window:
                result = self.calculate(sessions_sorted, d)
                results.append(result)

        return results

    def get_weekly_summary(self, sessions: List[TrainingSession], week_start: date) -> dict:
        """获取一周的 ACWR 摘要"""
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        results = {}
        for d in week_days:
            results[d.isoformat()] = self.calculate(sessions, d)

        acwr_values = [r.acwr for r in results.values() if r.acwr > 0]
        avg_acwr = np.mean(acwr_values) if acwr_values else 0

        return {
            "week_start": week_start.isoformat(),
            "daily_results": {k: {
                "acwr": v.acwr,
                "risk_zone": v.risk_zone
            } for k, v in results.items()},
            "weekly_avg_acwr": round(float(avg_acwr), 3),
            "max_acwr": round(float(max(acwr_values)), 3) if acwr_values else 0,
            "days_in_danger_zone": sum(
                1 for v in results.values() if v.risk_zone in ('谨慎区', '高风险区')
            )
        }
