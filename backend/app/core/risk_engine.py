"""
AthleteIQ - 羽毛球专项肩/膝劳损及受伤风险计算引擎
"""
import math


def compute_shoulder_overuse_risk(
    smash_7d_avg: float,
    overhead_week_total: float,
    external_rotation_ratio: float,
    sleep_hours: float,
) -> float:
    """近7天平均杀球量, 过顶击球周总量, 外旋/内旋比 (默认0.7), 睡眠时长"""
    risk = smash_7d_avg * 0.15
    risk += 30 if overhead_week_total > 500 else (overhead_week_total / 500) * 30
    risk += max(0, (1.0 - external_rotation_ratio) * 100)  # 外旋比越低风险越高
    risk += max(0, (7 - sleep_hours) * 5)
    return min(100, risk)


def compute_shoulder_acute_risk(
    today_smash: float,
    max_smash_30d: float,
    global_fatigue: float,
    reaction_time_ms: float,
) -> float:
    """今日杀球量, 近30天最大杀球量, 全身疲劳 0-10, 反应时间 ms"""
    risk = 0.0
    if max_smash_30d > 0 and today_smash > max_smash_30d:
        risk += (today_smash / max_smash_30d) * 50
    risk += 30 if global_fatigue >= 8 else global_fatigue * 3
    if reaction_time_ms > 300:
        risk += 20
    return min(100, risk)


def compute_knee_overuse_risk(
    total_impacts_7d: float,
    jump_landing_quality: float,
    quad_hamstring_ratio: float,
    has_knee_pain_history: bool,
) -> float:
    """近7天总冲击次数, 落地质量 1-10, 股四/腘绳比, 是否有膝痛史"""
    risk = (total_impacts_7d / 700) * 40
    risk += max(0, (7 - jump_landing_quality)) * 6
    ratio_deviation = abs(quad_hamstring_ratio - 0.8) / 0.2 * 25
    risk += ratio_deviation
    if has_knee_pain_history:
        risk += 15
    return min(100, risk)


def compute_knee_acute_risk(
    global_fatigue: float,
    jump_landing_quality: float,
    footwork_score: float,
    quad_hamstring_ratio: float,
) -> float:
    """全身疲劳 0-10, 落地质量 1-10, 步法评分 1-10, 股四/腘绳比"""
    risk = 0.0
    if global_fatigue >= 7:
        risk += (global_fatigue - 6) * 20
    if jump_landing_quality <= 4:
        risk += 40
    else:
        risk += max(0, 8 - jump_landing_quality) * 5
    if footwork_score <= 4:
        risk += 30
    else:
        risk += max(0, 7 - footwork_score) * 6
    if quad_hamstring_ratio < 0.5:
        risk += 25
    return min(100, risk)


def compute_all_risks(
    smash_7d_avg: float = 0,
    overhead_week_total: float = 0,
    external_rotation_ratio: float = 0.7,
    sleep_hours: float = 7.0,
    today_smash: float = 0,
    max_smash_30d: float = 0,
    global_fatigue: float = 5.0,
    reaction_time_ms: float = 250,
    total_impacts_7d: float = 0,
    jump_landing_quality: float = 7,
    quad_hamstring_ratio: float = 0.8,
    has_knee_pain_history: bool = False,
    footwork_score: float = 7,
) -> dict:
    """一次性计算全部四个风险值，返回 dict"""
    shoulder_overuse = compute_shoulder_overuse_risk(
        smash_7d_avg, overhead_week_total, external_rotation_ratio, sleep_hours
    )
    shoulder_acute = compute_shoulder_acute_risk(
        today_smash, max_smash_30d, global_fatigue / 10, reaction_time_ms
    )
    knee_overuse = compute_knee_overuse_risk(
        total_impacts_7d, jump_landing_quality, quad_hamstring_ratio, has_knee_pain_history
    )
    knee_acute = compute_knee_acute_risk(
        global_fatigue / 10, jump_landing_quality, footwork_score, quad_hamstring_ratio
    )

    return {
        "shoulder_overuse_risk": round(shoulder_overuse, 1),
        "shoulder_acute_risk": round(shoulder_acute, 1),
        "knee_overuse_risk": round(knee_overuse, 1),
        "knee_acute_risk": round(knee_acute, 1),
    }


def generate_recovery_suggestions(daily_metric) -> list:
    """
    基于每日指标生成个性化恢复建议。
    返回 exercises 列表: [{name, sets, reps, duration_min, notes, category}]
    """
    suggestions = []

    # 提取指标
    arm_pain = getattr(daily_metric, 'arm_pain_vas', 0) or 0
    leg_pain = getattr(daily_metric, 'leg_pain_vas', 0) or 0
    fatigue = getattr(daily_metric, 'fatigue', 50) or 50  # 0-100
    jump_quality = getattr(daily_metric, 'jump_landing_quality', 7) or 7
    shoulder_overuse = getattr(daily_metric, 'shoulder_overuse_risk', 0) or 0
    knee_overuse = getattr(daily_metric, 'knee_overuse_risk', 0) or 0

    if arm_pain >= 5:
        suggestions.append({
            "name": "肩部按摩 + 冰敷",
            "sets": 1, "reps": 1, "duration_min": 15,
            "notes": "对肩袖肌群进行深层按摩，随后冰敷15分钟",
            "category": "recovery",
        })
        suggestions.append({
            "name": "弹力带外旋训练",
            "sets": 3, "reps": 15, "duration_min": 8,
            "notes": "弹力带低阻力外旋，强化肩袖外旋肌群",
            "category": "strength_balance",
        })

    if leg_pain >= 5:
        suggestions.append({
            "name": "大腿泡沫轴放松",
            "sets": 1, "reps": 1, "duration_min": 10,
            "notes": "重点放松股四头肌和髂胫束",
            "category": "recovery",
        })
        suggestions.append({
            "name": "腘绳肌拉伸 + 冷热交替浴",
            "sets": 3, "reps": 1, "duration_min": 20,
            "notes": "每侧拉伸30秒×3组；冷热交替各3分钟×3轮",
            "category": "recovery",
        })

    if fatigue >= 70:
        suggestions.append({
            "name": "主动恢复（慢跑/游泳）",
            "sets": 1, "reps": 1, "duration_min": 30,
            "notes": "低强度有氧，心率控制在最大心率60%以下",
            "category": "active_recovery",
        })
        suggestions.append({
            "name": "延长睡眠",
            "sets": 1, "reps": 1, "duration_min": 0,
            "notes": "今晚比平时早睡1小时，目标睡眠8-9小时",
            "category": "sleep",
        })

    if jump_quality <= 5:
        suggestions.append({
            "name": "Box Jump 落地控制练习",
            "sets": 4, "reps": 6, "duration_min": 12,
            "notes": "从低箱跳下，重点练习软着陆（屈膝缓冲、膝盖不内扣）",
            "category": "technique",
        })

    if shoulder_overuse > 70:
        suggestions.append({
            "name": "YTW 肩袖稳定性伸展",
            "sets": 3, "reps": 10, "duration_min": 10,
            "notes": "俯卧位Y、T、W三个方向各10次，强化肩袖和肩胛稳定肌群。本周减少杀球量30%",
            "category": "strength_balance",
        })
        suggestions.append({
            "name": "减少杀球训练",
            "sets": 1, "reps": 1, "duration_min": 0,
            "notes": "建议将今日杀球量减少30-50%，改为吊球/高远球技术练习",
            "category": "load_management",
        })

    if knee_overuse > 70:
        suggestions.append({
            "name": "股四头肌离心训练",
            "sets": 3, "reps": 12, "duration_min": 10,
            "notes": "慢速下蹲（3秒下），强化股四头肌离心控制能力",
            "category": "strength_balance",
        })
        suggestions.append({
            "name": "低冲击有氧替代",
            "sets": 1, "reps": 1, "duration_min": 25,
            "notes": "用游泳或骑行替代跳跃类训练，减少膝关节冲击",
            "category": "load_management",
        })

    # 默认至少一条恢复建议
    if not suggestions:
        suggestions.append({
            "name": "日常恢复维护",
            "sets": 1, "reps": 1, "duration_min": 15,
            "notes": "全身静态拉伸 + 泡沫轴放松，维持基本柔韧性和肌肉状态",
            "category": "recovery",
        })

    return suggestions
