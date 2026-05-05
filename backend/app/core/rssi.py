"""
============================================================================
AthleteIQ - RSSI (恢复-应激状态指数) 多维过度训练诊断模块
基于 CPSS 过度训练共识 (Meeusen et al., 2013; NSCA Essentials)

RSSI 综合以下维度:
  1. ACWR > 1.5 持续 ≥ 2 周
  2. 晨起心率持续上升 (高于基线 > 5 bpm 且排除疾病)
  3. HRV 连续 7 日下降趋势 (LnRMSSD 降低超过 20%)
  4. 主观疲劳/睡眠/压力问卷得分恶化
  5. 近期力量/爆发力测试下降 > 5% 且在非减载期

输出等级:
  - 正常: 无明显过度训练迹象
  - 适应性训练 (Functional Overreaching, FOR): 短期负荷超量后预期恢复
  - 功能性过度训练 (Non-Functional Overreaching, NFOR): 需数周恢复
  - 非功能性过度训练 (Overtraining Syndrome, OTS): 需数月恢复+医学评估
============================================================================
"""
from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
import numpy as np
from scipy import stats


class RSSIRiskLevel(str, Enum):
    """RSSI 风险等级"""
    NORMAL = "正常"
    FUNCTIONAL_OR = "适应性训练"        # Functional Overreaching
    NON_FUNCTIONAL_OR = "功能性过度训练"  # Non-Functional Overreaching
    OVERTRAINING = "非功能性过度训练"     # Overtraining Syndrome
    MEDICAL_EVAL = "需医学评估"


@dataclass
class WellnessRecord:
    """每日健康记录"""
    date: date
    morning_heart_rate: Optional[int] = None   # bpm
    hrv_lnrmssd: Optional[float] = None        # ms
    sleep_duration: Optional[float] = None      # hours
    sleep_quality: Optional[int] = None         # 1-5
    fatigue_score: Optional[int] = None         # 1-5
    muscle_soreness: Optional[int] = None       # 1-5
    stress_score: Optional[int] = None          # 1-5
    mood_score: Optional[int] = None            # 1-5
    illness_flag: bool = False


@dataclass
class PerformanceRecord:
    """体能测试记录"""
    date: date
    squat_1rm: Optional[float] = None           # kg
    bench_press_1rm: Optional[float] = None
    deadlift_1rm: Optional[float] = None
    cmj_height: Optional[float] = None          # cm
    sprint_30m: Optional[float] = None          # sec (越小越好)
    vo2max: Optional[float] = None              # ml/kg/min


@dataclass
class RSSIResult:
    """RSSI 计算结果"""
    date: date
    rssi_score: float                           # 0-100, 越高风险越大
    risk_level: RSSIRiskLevel

    # 各子维度得分
    acwr_component: float                       # 0-25
    heart_rate_component: float                 # 0-25
    hrv_component: float                        # 0-25
    fatigue_component: float                    # 0-15
    performance_component: float               # 0-10

    # 诊断详情
    acwr_danger_weeks: int = 0                  # ACWR > 1.5 的连续周数
    hr_trend_pct: float = 0.0                   # 晨起心率变化百分比
    hrv_change_pct: float = 0.0                 # HRV 变化百分比
    fatigue_trend: str = "稳定"                 # 疲劳趋势描述
    performance_change_pct: float = 0.0         # 力量变化百分比

    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RSSICalculator:
    """
    恢复-应激状态指数 (RSSI) 计算器

    使用方法:
        calc = RSSICalculator()
        result = calc.evaluate(acwr_results, wellness, performance, baselines)
    """

    def __init__(self):
        # 各维度权重 (总分 100)
        self.weights = {
            "acwr": 25,          # ACWR 维度
            "heart_rate": 25,    # 晨起心率维度
            "hrv": 25,           # HRV 维度
            "fatigue": 15,       # 主观疲劳维度
            "performance": 10,   # 体能测试维度
        }

        # 阈值
        self.HR_INCREASE_THRESHOLD = 5       # bpm
        self.HRV_DECLINE_THRESHOLD = 0.20    # 20%
        self.PERF_DECLINE_THRESHOLD = 0.05   # 5%
        self.ACWR_DANGER_WEEKS = 2           # 连续周数

    def evaluate(
        self,
        acwr_values: List[Tuple[date, float, str]],  # [(date, acwr, risk_zone), ...]
        wellness_records: List[WellnessRecord],
        performance_records: List[PerformanceRecord],
        hr_baseline: Optional[float] = None,
        hrv_baseline: Optional[float] = None,
        strength_baseline: Optional[Dict[str, float]] = None,
        is_tapering: bool = False,         # 是否在计划减量期
        is_competition_phase: bool = False,  # 是否比赛期
    ) -> RSSIResult:
        """
        综合评估运动员的恢复-应激状态

        Args:
            acwr_values: ACWR 时间序列
            wellness_records: 每日健康记录 (至少7天)
            performance_records: 体能测试记录
            hr_baseline: 晨起心率个人基线
            hrv_baseline: HRV (LnRMSSD) 个人基线
            strength_baseline: 力量测试个人基线
            is_tapering: 是否在计划减量期
            is_competition_phase: 是否在比赛期
        """
        latest_date = (wellness_records[-1].date if wellness_records
                       else performance_records[-1].date if performance_records
                       else date.today())

        # 1. ACWR 维度评分
        acwr_score, acwr_danger_weeks = self._evaluate_acwr(acwr_values)

        # 2. 晨起心率维度评分
        hr_score, hr_trend_pct = self._evaluate_heart_rate(wellness_records, hr_baseline)

        # 3. HRV 维度评分
        hrv_score, hrv_change_pct = self._evaluate_hrv(wellness_records, hrv_baseline)

        # 4. 主观疲劳维度评分
        fatigue_score_total, fatigue_trend = self._evaluate_fatigue(wellness_records)

        # 5. 体能表现维度评分
        perf_score, perf_change_pct = self._evaluate_performance(performance_records, strength_baseline)

        # 加权总分
        total_score = acwr_score + hr_score + hrv_score + fatigue_score_total + perf_score

        # 确定风险等级
        risk_level = self._classify_risk_level(
            total_score, acwr_danger_weeks, hrv_change_pct,
            is_tapering, is_competition_phase,
        )

        # 生成建议
        recommendations, warnings = self._generate_recommendations(
            risk_level, acwr_score, hr_score, hrv_score,
            fatigue_score_total, perf_score, acwr_values,
            hrv_change_pct, hr_trend_pct, perf_change_pct,
        )

        return RSSIResult(
            date=latest_date,
            rssi_score=round(total_score, 2),
            risk_level=risk_level,
            acwr_component=round(acwr_score, 2),
            heart_rate_component=round(hr_score, 2),
            hrv_component=round(hrv_score, 2),
            fatigue_component=round(fatigue_score_total, 2),
            performance_component=round(perf_score, 2),
            acwr_danger_weeks=acwr_danger_weeks,
            hr_trend_pct=round(hr_trend_pct, 1),
            hrv_change_pct=round(hrv_change_pct, 1),
            fatigue_trend=fatigue_trend,
            performance_change_pct=round(perf_change_pct, 1),
            recommendations=recommendations,
            warnings=warnings,
        )

    def _evaluate_acwr(self, acwr_values: List[Tuple[date, float, str]]) -> Tuple[float, int]:
        """评估 ACWR 维度: 0-25 分"""
        if not acwr_values:
            return 0.0, 0

        recent = acwr_values[-14:] if len(acwr_values) >= 14 else acwr_values
        acwr_recent = [v[1] for v in recent if v[1] > 0]

        # 计算连续 ACWR > 1.5 的周数
        danger_weeks = 0
        consecutive_danger_days = 0
        for _, acwr, _ in recent:
            if acwr > 1.5:
                consecutive_danger_days += 1
            else:
                if consecutive_danger_days >= 5:  # 一周大多数训练日
                    danger_weeks += 1
                consecutive_danger_days = 0
        if consecutive_danger_days >= 5:
            danger_weeks += 1

        # 计分
        score = 0
        if acwr_recent:
            # 最近 ACWR 平均值的贡献
            avg_acwr = np.mean(acwr_recent)
            if avg_acwr > 1.5:
                score += 20
            elif avg_acwr > 1.3:
                score += 12
            elif avg_acwr > 1.1:
                score += 5

            # 连续危险周数加分 (最多 +5)
            score += min(danger_weeks * 3, 5)

        return min(score, 25.0), danger_weeks

    def _evaluate_heart_rate(
        self, wellness: List[WellnessRecord], baseline: Optional[float]
    ) -> Tuple[float, float]:
        """评估晨起心率维度: 0-25 分

        基于: Buchheit (2014), Plews et al. (2012)
        晨起心率持续上升 > 5 bpm 是自主神经系统失衡的信号
        """
        hr_records = [(w.date, w.morning_heart_rate) for w in wellness
                      if w.morning_heart_rate is not None and not w.illness_flag]

        if len(hr_records) < 7 or baseline is None:
            return 0.0, 0.0

        # 取最近7天
        recent_7 = hr_records[-7:]
        recent_hr = [r[1] for r in recent_7]

        avg_recent = np.mean(recent_hr)
        hr_change_pct = ((avg_recent - baseline) / baseline) * 100

        score = 0

        # 晨起心率高于基线 > 3 bpm
        if avg_recent > baseline + 3:
            score += 8
        # 高于基线 > 5 bpm (NSCA 关键阈值)
        if avg_recent > baseline + 5:
            score += 12

        # 分析上升趋势 (线性回归)
        x = np.arange(len(recent_hr))
        slope, _, r_value, _, _ = stats.linregress(x, recent_hr)

        if slope > 0.3 and r_value > 0.5:  # 明确上升趋势
            score += 5

        return min(score, 25.0), round(hr_change_pct, 1)

    def _evaluate_hrv(
        self, wellness: List[WellnessRecord], baseline: Optional[float]
    ) -> Tuple[float, float]:
        """评估 HRV 维度: 0-25 分

        基于: Plews et al. (2013), Stanley et al. (2013)
        LnRMSSD 连续下降 > 20% 表明副交感神经活动减弱
        """
        hrv_records = [(w.date, w.hrv_lnrmssd) for w in wellness
                       if w.hrv_lnrmssd is not None]

        if len(hrv_records) < 7 or baseline is None:
            return 0.0, 0.0

        recent_7 = hrv_records[-7:]
        recent_hrv = [r[1] for r in recent_7]

        avg_recent = np.mean(recent_hrv)
        hrv_change_pct = ((avg_recent - baseline) / baseline) * 100

        score = 0

        # HRV 下降超过基线 10%
        if hrv_change_pct < -10:
            score += 8
        # HRV 下降超过基线 20% (CPSS 关键阈值)
        if hrv_change_pct < -20:
            score += 12

        # 连续下降趋势 (线性回归)
        x = np.arange(len(recent_hrv))
        slope, _, r_value, _, _ = stats.linregress(x, recent_hrv)

        if slope < -0.5 and abs(r_value) > 0.5:  # 明确下降趋势
            score += 5

        return min(score, 25.0), round(hrv_change_pct, 1)

    def _evaluate_fatigue(self, wellness: List[WellnessRecord]) -> Tuple[float, str]:
        """评估主观疲劳维度: 0-15 分"""
        if len(wellness) < 3:
            return 0.0, "数据不足"

        recent_7 = wellness[-7:]
        fatigue_scores = [w.fatigue_score for w in recent_7 if w.fatigue_score is not None]
        soreness_scores = [w.muscle_soreness for w in recent_7 if w.muscle_soreness is not None]
        stress_scores = [w.stress_score for w in recent_7 if w.stress_score is not None]
        sleep_quality = [w.sleep_quality for w in recent_7 if w.sleep_quality is not None]

        score = 0
        trend_details = []

        # 疲劳评分 > 3 (偏高)
        if fatigue_scores:
            avg_fatigue = np.mean(fatigue_scores)
            if avg_fatigue >= 4:
                score += 5
                trend_details.append("高疲劳")
            elif avg_fatigue >= 3:
                score += 3
                trend_details.append("中高疲劳")

        # 肌肉酸痛 > 3
        if soreness_scores:
            avg_soreness = np.mean(soreness_scores)
            if avg_soreness >= 4:
                score += 4
                trend_details.append("高酸痛")
            elif avg_soreness >= 3:
                score += 2

        # 压力 > 3
        if stress_scores:
            avg_stress = np.mean(stress_scores)
            if avg_stress >= 4:
                score += 3
                trend_details.append("高压力")

        # 睡眠质量 < 3
        if sleep_quality:
            avg_sleep = np.mean(sleep_quality)
            if avg_sleep <= 2:
                score += 3
                trend_details.append("睡眠差")
            elif avg_sleep <= 3:
                score += 1

        trend = "稳定" if not trend_details else "、".join(trend_details)

        return min(score, 15.0), trend

    def _evaluate_performance(
        self,
        performance: List[PerformanceRecord],
        baseline: Optional[Dict[str, float]],
    ) -> Tuple[float, float]:
        """评估体能表现维度: 0-10 分"""
        if len(performance) < 2 or baseline is None:
            return 0.0, 0.0

        # 取最近一次与上一次测试比较
        latest = performance[-1]
        previous = performance[-2]

        changes = []

        # 检测力量指标下降 (1RM)
        for key in ['squat_1rm', 'bench_press_1rm', 'deadlift_1rm']:
            curr = getattr(latest, key)
            prev = getattr(previous, key)
            base = baseline.get(key)
            if curr and prev and prev > 0:
                pct_change = ((curr - prev) / prev) * 100
                changes.append((key, pct_change))

        # 检测 CMJ 下降
        if latest.cmj_height and previous.cmj_height and previous.cmj_height > 0:
            pct_change = ((latest.cmj_height - previous.cmj_height) / previous.cmj_height) * 100
            changes.append(('cmj_height', pct_change))

        # 检测冲刺时间上升 (变慢)
        if latest.sprint_30m and previous.sprint_30m and previous.sprint_30m > 0:
            pct_change = ((latest.sprint_30m - previous.sprint_30m) / previous.sprint_30m) * 100
            changes.append(('sprint_30m', pct_change))

        if not changes:
            return 0.0, 0.0

        # 找出最大下降幅度
        worst_change = min(changes, key=lambda x: x[1])
        worst_pct = worst_change[1]

        score = 0
        if worst_pct < -5:
            score += 8   # NSCA: >5% 下降视为显著变化
        elif worst_pct < -3:
            score += 5
        elif worst_pct < -2:
            score += 2

        return min(score, 10.0), round(worst_pct, 1)

    def _classify_risk_level(
        self,
        total_score: float,
        acwr_danger_weeks: int,
        hrv_change_pct: float,
        is_tapering: bool,
        is_competition_phase: bool,
    ) -> RSSIRiskLevel:
        """
        综合分类风险等级

        RSSI 评分解释:
          0-30   : 正常
          30-50  : 适应性训练 (FOR) - 短期高负荷的正常反应
          50-70  : 功能性过度训练 (NFOR) - 需要恢复干预
          > 70   : 非功能性过度训练/OTS - 需要长期恢复+医学评估
        """
        if total_score >= 70:
            return RSSIRiskLevel.OVERTRAINING
        elif total_score >= 50:
            return RSSIRiskLevel.NON_FUNCTIONAL_OR
        elif total_score >= 30:
            # 如果在减量/比赛期，FOR 可能正常
            if is_tapering and total_score < 40:
                return RSSIRiskLevel.NORMAL
            return RSSIRiskLevel.FUNCTIONAL_OR

        return RSSIRiskLevel.NORMAL

    def _generate_recommendations(
        self,
        risk_level: RSSIRiskLevel,
        acwr_score: float, hr_score: float, hrv_score: float,
        fatigue_score: float, perf_score: float,
        acwr_values: List,
        hrv_change_pct: float, hr_trend_pct: float, perf_change_pct: float,
    ) -> Tuple[List[str], List[str]]:
        """生成训练建议和预警"""
        recommendations = []
        warnings = []

        if risk_level == RSSIRiskLevel.NORMAL:
            recommendations.append("各项指标正常，可按计划继续训练。")
            return recommendations, warnings

        if risk_level == RSSIRiskLevel.FUNCTIONAL_OR:
            recommendations.append("检测到适应性训练反应（FOR）。短期负荷增加后的正常生理适应。")
            recommendations.append("建议：维持当前强度，但确保 1-2 天高质量恢复。")
            recommendations.append("加强营养摄入（特别是蛋白质和碳水化合物补充）和睡眠管理。")

        elif risk_level == RSSIRiskLevel.NON_FUNCTIONAL_OR:
            warnings.append("⚠ 功能性过度训练（NFOR）预警！需要数周恢复。")
            recommendations.append("立即降低训练容量 30-50%，暂停高强度训练 3-7 天。")
            recommendations.append("增加主动恢复（低强度有氧、拉伸、泡沫轴）。")
            recommendations.append("每日监测晨起心率和 HRV，直至指标回稳。")
            recommendations.append("复查营养和睡眠状况，考虑增加休息日。")

        elif risk_level == RSSIRiskLevel.OVERTRAINING:
            warnings.append("⛔ 非功能性过度训练（OTS）严重预警！")
            warnings.append("建议：立即停止所有高强度训练！联系运动医学专业人员评估。")
            recommendations.append("完全停止竞技训练，仅保留医生允许的轻度活动。")
            recommendations.append("等待全面医学评估后，再制定渐进恢复计划。")
            recommendations.append("恢复期通常需要数周到数月，请保持耐心。")

        # 针对具体维度的建议
        if acwr_score > 15:
            recommendations.append("ACWR 偏高：建议减少本周训练容量 20%，优先降低训练时长。")
            warnings.append(f"ACWR 处于高风险区间持续 {self.ACWR_DANGER_WEEKS} 周以上。")

        if hr_score > 15:
            recommendations.append("晨起心率升高：自主神经系统恢复不足。增加恢复日并监测晨脉。")
            warnings.append(f"晨起心率较基线升高 {hr_trend_pct:.1f}%。")

        if hrv_score > 15:
            recommendations.append(f"HRV 下降 {abs(hrv_change_pct):.1f}%：副交感神经活动减弱，建议增加睡眠时长。")
            warnings.append(f"HRV (LnRMSSD) 较基线下降 {abs(hrv_change_pct):.1f}%，超过 CPSS 预警阈值。")

        if fatigue_score > 8:
            recommendations.append("主观疲劳偏高：检查训练外压力源（学业/工作/生活），考虑心理恢复策略。")

        if perf_score > 5:
            recommendations.append(f"体能测试下降 {abs(perf_change_pct):.1f}%：若非减载期，需评估训练负荷是否过度。")

        return recommendations, warnings
