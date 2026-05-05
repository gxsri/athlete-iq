"""
============================================================================
AthleteIQ - 个性化训练建议生成模块
基于 NSCA-CSCS / CPSS 周期化训练原则

生成逻辑:
  1. 识别当前训练周期阶段 (准备期/比赛期/过渡期)
  2. 评估当前 ACWR、RSSI、机能状态
  3. 对比运动员素质与项目常模
  4. 输出下一阶段训练方向 + 周训练模板
============================================================================
"""
from __future__ import annotations
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum


class CyclePhase(str, Enum):
    PREPARATION = "准备期"
    COMPETITION = "比赛期"
    TRANSITION = "过渡期"


class TrainingStrength(str, Enum):
    STRENGTH = "力量"
    ENDURANCE = "耐力"
    SPEED = "速度"
    TECHNICAL = "技战术"
    FLEXIBILITY = "柔韧"


# CSCS 体能测试常模参考 (示例数据, 实际应使用项目专项数据库)
CSCS_NORMS = {
    "篮球": {
        "cmj_height_cm": {"low": 45, "avg": 55, "high": 65, "unit": "cm"},
        "sprint_30m_sec": {"low": 4.5, "avg": 4.2, "high": 3.9, "unit": "sec"},
        "bench_press_1rm_kg": {"low": 70, "avg": 100, "high": 120, "unit": "kg"},
        "vo2max_ml_kg_min": {"low": 45, "avg": 52, "high": 60, "unit": "ml/kg/min"},
    },
    "足球": {
        "cmj_height_cm": {"low": 40, "avg": 50, "high": 62, "unit": "cm"},
        "sprint_30m_sec": {"low": 4.4, "avg": 4.1, "high": 3.8, "unit": "sec"},
        "squat_1rm_kg": {"low": 100, "avg": 140, "high": 180, "unit": "kg"},
        "vo2max_ml_kg_min": {"low": 50, "avg": 58, "high": 65, "unit": "ml/kg/min"},
    },
    "游泳": {
        "cmj_height_cm": {"low": 35, "avg": 45, "high": 55, "unit": "cm"},
        "bench_press_1rm_kg": {"low": 50, "avg": 80, "high": 100, "unit": "kg"},
        "vo2max_ml_kg_min": {"low": 45, "avg": 55, "high": 65, "unit": "ml/kg/min"},
    },
}


@dataclass
class AthleteProfile:
    """运动员档案摘要"""
    sport: str
    training_years: float
    cycle_phase: CyclePhase
    recent_acwr: float
    rssi_risk: str
    strengths: Dict[str, float]   # e.g. {"cmj_height": 52.3, "vo2max": 55.0}
    weaknesses: List[str]          # e.g. ["力量", "敏捷性"]


@dataclass
class TrainingRecommendation:
    """训练建议"""
    summary: str                           # 总体摘要
    load_adjustment: str                   # 负荷调整建议
    intensity_recommendation: str          # 强度建议
    volume_recommendation: str             # 容量建议
    frequency_recommendation: str          # 频次建议
    priority_areas: List[str]              # 优先发展素质
    recovery_strategies: List[str]         # 恢复策略
    weekly_template: List[Dict]            # 周训练模板
    warnings: List[str] = field(default_factory=list)


@dataclass
class WeeklyTemplate:
    """周训练模板"""
    week_number: int
    microcycle_type: str      # 'loading', 'recovery', 'competition', 'taper'
    sessions: List[Dict]      # [{"day": 1, "type": "力量", "duration_min": 90, "rpe_target": 7}, ...]


class TrainingAdvisor:
    """
    个性化训练建议生成器

    使用方法:
        advisor = TrainingAdvisor()
        recommendation = advisor.generate(profile)
    """

    def generate(self, profile: AthleteProfile) -> TrainingRecommendation:
        """生成训练建议"""
        phase = profile.cycle_phase
        acwr = profile.recent_acwr

        # 1. 总体评估
        summary = self._generate_summary(phase, acwr, profile.rssi_risk)

        # 2. 负荷调整
        load_adj = self._load_adjustment(acwr, profile.rssi_risk)

        # 3. 强度/容量/频次建议
        intensity, volume, freq = self._phase_based_recommendations(phase, acwr)

        # 4. 优先发展素质
        priorities = self._identify_priorities(profile)

        # 5. 恢复策略
        recovery = self._recovery_strategies(acwr, profile.rssi_risk)

        # 6. 周训练模板
        weekly_template = self._generate_weekly_template(phase, acwr, priorities)

        # 7. 预警
        warnings = []
        if acwr > 1.5:
            warnings.append("ACWR 过高，请确认是否为计划内高强度周。若非计划内，建议立即减量。")
        if profile.rssi_risk in ("功能性过度训练", "非功能性过度训练"):
            warnings.append("过度训练风险高，建议暂停高强度训练并就医评估。")

        return TrainingRecommendation(
            summary=summary,
            load_adjustment=load_adj,
            intensity_recommendation=intensity,
            volume_recommendation=volume,
            frequency_recommendation=freq,
            priority_areas=priorities,
            recovery_strategies=recovery,
            weekly_template=weekly_template,
            warnings=warnings,
        )

    def _generate_summary(self, phase: CyclePhase, acwr: float, rssi: str) -> str:
        """生成总体摘要"""
        phase_label = {
            CyclePhase.PREPARATION: "准备期（基础体能建设阶段）",
            CyclePhase.COMPETITION: "比赛期（竞技状态维持阶段）",
            CyclePhase.TRANSITION: "过渡期（恢复与休整阶段）",
        }.get(phase, "未知阶段")

        acwr_status = "良好" if 0.8 <= acwr <= 1.3 else ("偏高" if acwr > 1.3 else "偏低")

        return (f"当前处于{phase_label}。急慢性负荷比 (ACWR) = {acwr:.2f}（{acwr_status}），"
                f"RSSI 风险等级: {rssi}。"
                f"根据 NSCA-CSCS 周期化原则和 CPSS 负荷管理共识提供以下建议。")

    def _load_adjustment(self, acwr: float, rssi: str) -> str:
        """负荷调整建议"""
        if rssi in ("非功能性过度训练", "功能性过度训练"):
            return "立即降低总训练负荷 40-60%，优先消除所有超过 RPE 5 的训练。"

        if acwr > 1.5:
            return "建议本周降低训练容量 25-30%，保持或略微降低强度。避免连续高强度训练日。"
        elif acwr > 1.3:
            return "谨慎增加负荷。若恢复指标（HRV/晨脉/睡眠）正常，可维持当前负荷；否则降低 10-15%。"
        elif acwr < 0.8:
            return "负荷偏低。若是计划内减量（Taper），属正常；否则需逐步恢复负荷，每周增加不超过 10%。"
        else:
            return "当前负荷处于安全区间，可按照周期计划正常推进。每周负荷增量建议不超过 10%。"

    def _phase_based_recommendations(self, phase: CyclePhase, acwr: float) -> tuple:
        """基于周期阶段推荐强度、容量、频次 (NSCA 周期化模型)"""
        if phase == CyclePhase.PREPARATION:
            if acwr < 1.0:
                intensity = "中等强度 (RPE 5-7)，侧重基础力量和一般耐力"
                volume = "高容量（单次 90-120 分钟），逐步建立训练量基础"
                freq = "周训练 5-6 天，含 1 天主动恢复"
            else:
                intensity = "中高强度 (RPE 6-8)，逐步引入专项强度"
                volume = "中高容量（单次 75-105 分钟）"
                freq = "周训练 5-6 天，注意恢复质量"
        elif phase == CyclePhase.COMPETITION:
            if acwr > 1.3:
                intensity = "维持性强度 (RPE 6-7)，赛前减量阶段应降低强度"
                volume = "低中容量（单次 45-75 分钟），确保比赛前充分恢复"
                freq = "周训练 4-5 天，赛前 2-3 天大幅减量"
            else:
                intensity = "高强度专项 (RPE 7-9)，与比赛需求匹配"
                volume = "中容量（单次 60-90 分钟），质量优先于数量"
                freq = "周训练 4-5 天，含比赛日 + 恢复日"
        elif phase == CyclePhase.TRANSITION:
            intensity = "低强度 (RPE 3-5)，以主动恢复为主要目标"
            volume = "低容量（单次 30-60 分钟），允许身体和心理恢复"
            freq = "周训练 3-4 天，以多样化活动为主（交叉训练、娱乐性运动）"
        else:
            intensity, volume, freq = "", "", ""

        return intensity, volume, freq

    def _identify_priorities(self, profile: AthleteProfile) -> List[str]:
        """识别训练优先发展领域"""
        priorities = []

        # 已标注的弱点
        if profile.weaknesses:
            priorities.extend(profile.weaknesses)

        # 与项目常模对比
        norms = CSCS_NORMS.get(profile.sport, {})
        if norms and profile.strengths:
            for metric, value in profile.strengths.items():
                if metric in norms:
                    norm = norms[metric]
                    # 与低标准比较
                    if value <= norm["low"]:
                        metric_name = {
                            "cmj_height_cm": "爆发力（CMJ 纵跳）",
                            "sprint_30m_sec": "短距离速度（30m冲刺）",
                            "bench_press_1rm_kg": "上肢力量（卧推 1RM）",
                            "squat_1rm_kg": "下肢力量（深蹲 1RM）",
                            "vo2max_ml_kg_min": "有氧耐力（VO₂max）",
                        }.get(metric, metric)
                        if metric_name not in priorities:
                            priorities.append(metric_name)

        if not priorities:
            priorities.append("维持当前各项素质的均衡发展，根据周期阶段微调侧重。")

        return priorities

    def _recovery_strategies(self, acwr: float, rssi: str) -> List[str]:
        """推荐恢复策略"""
        strategies = []

        # 基础恢复
        strategies.append("保证每日 7-9 小时高质量睡眠。")
        strategies.append("训练后 30 分钟内补充碳水化合物 + 蛋白质（3:1 比例）。")

        if acwr > 1.3 or "过度训练" in rssi:
            strategies.append("每日进行 15-20 分钟主动恢复（低强度有氧、泡沫轴放松）。")
            strategies.append("每周安排 1 次冷水浸泡 (10-15°C, 10-15分钟) 或冷热交替浴。")
            strategies.append("考虑安排 1 次运动按摩，重点关注紧张肌群。")

        if rssi in ("功能性过度训练", "非功能性过度训练"):
            strategies.append("强烈建议安排 1-2 天完全休息日。")
            strategies.append("进行心理放松练习（冥想、呼吸训练），降低交感神经活性。")

        strategies.append("每日记录晨起心率和 HRV，观察恢复趋势。")

        return strategies

    def _generate_weekly_template(
        self, phase: CyclePhase, acwr: float, priorities: List[str]
    ) -> List[Dict]:
        """生成一周训练模板 (基于运动项目的通用模板)"""
        if phase == CyclePhase.PREPARATION:
            template = self._preparation_template(acwr)
        elif phase == CyclePhase.COMPETITION:
            template = self._competition_template(acwr)
        else:
            template = self._transition_template()

        # 将优先领域嵌入模板备注
        priority_text = "、".join(priorities[:3]) if priorities else "均衡发展"
        for session in template:
            session["focus_notes"] = f"本周重点: {priority_text}"

        return template

    def _preparation_template(self, acwr: float) -> List[Dict]:
        """准备期周模板 (NSCA 线性周期化模型)"""
        load_modifier = 0.7 if acwr > 1.5 else (0.85 if acwr > 1.3 else 1.0)

        return [
            {"day": "周一", "session_name": "力量训练 (下肢主导)", "training_type": "力量",
             "duration_min": int(90 * load_modifier), "rpe_target": 7, "load_pct": "75-80% 1RM"},
            {"day": "周二", "session_name": "有氧耐力", "training_type": "耐力",
             "duration_min": int(60 * load_modifier), "rpe_target": 5, "load_pct": "60-70% HRmax"},
            {"day": "周三", "session_name": "力量训练 (上肢主导) + 核心", "training_type": "力量",
             "duration_min": int(90 * load_modifier), "rpe_target": 7, "load_pct": "75-80% 1RM"},
            {"day": "周四", "session_name": "速度/灵敏训练 + 技术", "training_type": "速度",
             "duration_min": int(75 * load_modifier), "rpe_target": 6, "load_pct": "90-95% 最大速度"},
            {"day": "周五", "session_name": "力量训练 (全身) + 爆发力", "training_type": "力量",
             "duration_min": int(90 * load_modifier), "rpe_target": 8, "load_pct": "80-85% 1RM"},
            {"day": "周六", "session_name": "专项技术 / 实战模拟", "training_type": "技战术",
             "duration_min": int(60 * load_modifier), "rpe_target": 7, "load_pct": "比赛强度 90-95%"},
            {"day": "周日", "session_name": "主动恢复日", "training_type": "柔韧",
             "duration_min": 30, "rpe_target": 3, "load_pct": "低强度恢复"},
        ]

    def _competition_template(self, acwr: float) -> List[Dict]:
        """比赛期周模板 (NSCA 赛前减量 + 维持)"""
        if acwr > 1.3:
            load = 0.6
        elif acwr > 1.1:
            load = 0.8
        else:
            load = 1.0

        return [
            {"day": "周一", "session_name": "轻力量维持", "training_type": "力量",
             "duration_min": int(60 * load), "rpe_target": 5, "load_pct": "60-65% 1RM, 爆发性"},
            {"day": "周二", "session_name": "专项速度 + 技术", "training_type": "速度",
             "duration_min": int(75 * load), "rpe_target": 7, "load_pct": "比赛强度"},
            {"day": "周三", "session_name": "药理学恢复", "training_type": "柔韧",
             "duration_min": 30, "rpe_target": 3, "load_pct": "主动恢复"},
            {"day": "周四", "session_name": "赛前战术演练", "training_type": "技战术",
             "duration_min": int(60 * load), "rpe_target": 8, "load_pct": "比赛强度"},
            {"day": "周五", "session_name": "赛前激活", "training_type": "混合",
             "duration_min": int(40 * load), "rpe_target": 5, "load_pct": "轻量激活"},
            {"day": "周六", "session_name": "🏆 比赛日", "training_type": "技战术",
             "duration_min": 120, "rpe_target": 10, "load_pct": "全力以赴"},
            {"day": "周日", "session_name": "赛后恢复", "training_type": "柔韧",
             "duration_min": 30, "rpe_target": 2, "load_pct": "恢复休息"},
        ]

    def _transition_template(self) -> List[Dict]:
        """过渡期周模板 (主动休息 + 多样化)"""
        return [
            {"day": "周一", "session_name": "休息或轻度拉伸", "training_type": "柔韧",
             "duration_min": 20, "rpe_target": 2, "load_pct": "自主拉伸"},
            {"day": "周二", "session_name": "交叉训练 (游泳/自行车)", "training_type": "耐力",
             "duration_min": 45, "rpe_target": 4, "load_pct": "轻松有氧"},
            {"day": "周三", "session_name": "休息日", "training_type": "柔韧",
             "duration_min": 0, "rpe_target": 0, "load_pct": "完全休息"},
            {"day": "周四", "session_name": "全身轻力量 + 核心", "training_type": "力量",
             "duration_min": 45, "rpe_target": 4, "load_pct": "50-55% 1RM"},
            {"day": "周五", "session_name": "娱乐性运动", "training_type": "混合",
             "duration_min": 60, "rpe_target": 4, "load_pct": "低强度玩耍"},
            {"day": "周六", "session_name": "轻度有氧 + 拉伸", "training_type": "耐力",
             "duration_min": 40, "rpe_target": 3, "load_pct": "< 60% HRmax"},
            {"day": "周日", "session_name": "休息日", "training_type": "柔韧",
             "duration_min": 0, "rpe_target": 0, "load_pct": "完全休息"},
        ]
