"""
AthleteIQ - 综合恢复-应激防线评分 (0-100)
整合 ACWR、RSSI、疲劳、心理、营养 5 个维度
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CompositeRiskResult:
    risk_score: float          # 0-100 (higher = more risk)
    risk_level: str            # "低风险" / "中等风险" / "高风险"
    acwr_contribution: float
    rssi_contribution: float
    fatigue_contribution: float
    mental_contribution: float
    nutrition_contribution: float
    recommendations: List[str]


def calculate_composite_risk(
    acwr: float = 0,
    acwr_risk_zone: str = "安全区",
    rssi_score: Optional[float] = 0,
    fatigue_scores: Optional[List[float]] = None,
    mental_scores: Optional[List[float]] = None,
    nutrition_risk: bool = False,
) -> CompositeRiskResult:
    rssi_score = rssi_score or 0
    acwr = acwr or 0
    """
    Weighted composite risk scoring:
    - ACWR zone: 30%
    - RSSI score: 25%
    - Fatigue (recent avg): 20%
    - Mental (recent avg): 15%
    - Nutrition risk: 10%
    """

    # 1. ACWR contribution (0-30)
    if acwr_risk_zone == "高风险区":
        acwr_contrib = 25
    elif acwr_risk_zone == "谨慎区":
        acwr_contrib = 15
    else:
        acwr_contrib = max(0, min(25, (acwr - 0.8) / 0.7 * 25)) if acwr > 0.8 else 0

    # 2. RSSI contribution (0-25)
    if rssi_score >= 70:
        rssi_contrib = 22
    elif rssi_score >= 50:
        rssi_contrib = 16
    elif rssi_score >= 30:
        rssi_contrib = 10
    else:
        rssi_contrib = 3

    # 3. Fatigue contribution (0-20)
    if fatigue_scores:
        valid = [f for f in fatigue_scores if f is not None]
        if valid:
            avg_fatigue = sum(valid) / len(valid)
            fatigue_contrib = (avg_fatigue / 5) * 20
        else:
            fatigue_contrib = 5
    else:
        fatigue_contrib = 5

    # 4. Mental contribution (0-15)
    if mental_scores:
        valid = [m for m in mental_scores if m is not None]
        if valid:
            avg_mental = sum(valid) / len(valid)
            mental_contrib = (1 - (avg_mental / 5)) * 15
        else:
            mental_contrib = 5
    else:
        mental_contrib = 5

    # 5. Nutrition contribution (0-10)
    nutrition_contrib = 8 if nutrition_risk else 3

    total = acwr_contrib + rssi_contrib + fatigue_contrib + mental_contrib + nutrition_contrib
    total = max(0, min(100, total))

    if total >= 70:
        risk_level = "高风险"
    elif total >= 30:
        risk_level = "中等风险"
    else:
        risk_level = "低风险"

    recommendations = []
    if acwr_contrib >= 20:
        recommendations.append("训练负荷过高，建议立即减量 30-50%，增加恢复日")
    if rssi_contrib >= 16:
        recommendations.append("恢复-应激状态恶化，监控晨起心率和 HRV，考虑减量")
    if fatigue_contrib >= 15:
        recommendations.append("主观疲劳评分偏高，增加主动恢复和睡眠时间")
    if mental_contrib >= 10:
        recommendations.append("心理状态下降，考虑调整训练节奏，增加多样化训练")
    if nutrition_contrib >= 8:
        recommendations.append("营养摄入不足，关注蛋白质补充和训练后补能")

    return CompositeRiskResult(
        risk_score=round(total, 1),
        risk_level=risk_level,
        acwr_contribution=round(acwr_contrib, 1),
        rssi_contribution=round(rssi_contrib, 1),
        fatigue_contribution=round(fatigue_contrib, 1),
        mental_contribution=round(mental_contrib, 1),
        nutrition_contribution=round(nutrition_contrib, 1),
        recommendations=recommendations,
    )
