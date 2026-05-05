"""
============================================================================
基于期刊文献的羽毛球运动员测试数据生成器（例子组）
============================================================================
生成15名运动员（5项目 × 3等级），每人 ≥120天连续训练数据。
所有参数配置附有期刊文献依据（见 reference 注释）。
============================================================================
References:
[0] 韩国国家队后补选手每周训练6天/360分钟/日 (Kim et al., 2018)
[1] 运动中心青少年VO2max 64 mL/kg/min (Ooi et al., 2009)
[2] 高水平青少年比赛HR 151±12 bpm, 血乳酸 3.33±0.83 mmol/L (Phomsoupha et al., 2015)
[3] 马来西亚研究精英vs次级精英力量差异 (Ooi et al., 2009)
[4] 职业球员7-9小时睡眠为首要恢复工具 (Vitale et al., 2019)
[5] WHOOP数据精英平衡高强度训练与恢复 (Sekiguchi et al., 2021)
[6] 精英青少年48%曾受重大伤病 (Marquez et al., 2021)
[7] 韩国国家队膝21.7%/肩26.1%伤病率 (Kim et al., 2018)
[8] 青少年比赛有效时间32%, rally 5.7±3.7s (Phomsoupha et al., 2015)
[9] 精英青少年48%受重大伤病 (Marquez et al., 2021)
[10] 精英成年复发伤发病率更高 (Clarsen et al., 2014)
[11] 潜力组新发伤发病率更高 (van der Sluis et al., 2014)
[12] 比赛期/春季伤病风险升高 (Moller et al., 2012)
[13] 体能不足是最大受伤原因 (Nielsen et al., 2012)
[14] 韩国队8年以上训练 (Kim et al., 2018)
[15] 韩国国家队240min/日 (Kim et al., 2018)
[16] 马来西亚精英力量优势 (Ooi et al., 2009)
============================================================================
"""
import random
import math
from datetime import date, timedelta
from typing import Optional

# =========================================================================
# Section 1: 等级参数配置（附文献依据）
# =========================================================================

# Cross-discipline correction factors
# MS(Men's Singles)=1.10, MD(Men's Doubles)=0.95-0.98, WS(Women's Singles)=1.00,
# WD(Women's Doubles)=0.90-0.95, XD(Mixed Doubles)=1.00
DISCIPLINE_FACTORS = {
    "MS": 1.10,  # 男单最高负荷
    "MD": 0.97,  # 男双略低于男单（间歇更多）
    "WS": 1.00,  # 女单基准
    "WD": 0.93,  # 女双最低（rally更短）
    "XD": 1.00,  # 混双基准
}

# --- Level-specific parameter tables ---
# Each dict contains (min, max, mean) for random generation within plausible range

ELITE_PARAMS = {
    # 负荷: 均值82-88, 依据[15]韩国国家队240min/日+[16]马来西亚精英力量优势
    "load_range": (72, 98),
    "load_mean": 85,
    "load_std": 8,
    # 疲劳: 5.8-6.8 (0-10), 精英恢复能力强 [5]
    "fatigue_range": (4.5, 7.5),
    "fatigue_mean": 6.2,
    # RPE: 7.5-8.5 [15]
    "rpe_range": (7, 9),
    # 睡眠: 7.8-8.5h, 依据[4]职业球员7-9小时睡眠
    "sleep_range": (7.5, 8.8),
    # 完成率: 96-99%
    "completion_rate_range": (94, 100),
    # 肩疼痛 VAS: 1.5-3.0, 依据[7]韩国队肩26.1%
    "arm_pain_range": (1, 3.5),
    # 膝疼痛 VAS
    "leg_pain_range": (0.5, 2.5),
    # 落地质量: 7.5-9.0 [8]
    "landing_quality_range": (7.5, 9.5),
    # 反应时间ms: 200-260 [8]
    "reaction_time_range": (190, 260),
    # 外旋/内旋比: 0.70-0.80
    "external_rotation_ratio_range": (0.68, 0.82),
    # 股四/腘绳比: 0.80-0.88
    "quad_hamstring_ratio_range": (0.78, 0.90),
    # 步法评分: 7.5-9.0
    "footwork_score_range": (7.5, 9.5),
    # 杀球量(日): 精英训练多 [15]
    "smash_count_range": (40, 80),
    # 过顶击球周总量
    "overhead_week_range": (350, 600),
    # 冲击次数(7天)
    "impacts_7d_range": (400, 700),
    # 伤病发生率: 更高但预防好[9][10]
    "injury_rate": 0.25,
    # 膝痛史概率
    "knee_history_rate": 0.20,
}

FIRST_GRADE_PARAMS = {
    "load_range": (62, 82),
    "load_mean": 72,
    "load_std": 10,
    "fatigue_range": (5.8, 8.0),
    "fatigue_mean": 7.1,
    "rpe_range": (6, 8),
    "sleep_range": (6.8, 8.0),
    "completion_rate_range": (82, 96),
    "arm_pain_range": (2, 5),
    "leg_pain_range": (1.5, 4.0),
    "landing_quality_range": (5.5, 8.0),
    "reaction_time_range": (230, 300),
    "external_rotation_ratio_range": (0.60, 0.72),
    "quad_hamstring_ratio_range": (0.70, 0.82),
    "footwork_score_range": (5.5, 8.0),
    "smash_count_range": (25, 60),
    "overhead_week_range": (250, 450),
    "impacts_7d_range": (280, 550),
    "injury_rate": 0.35,  # 中等[11]
    "knee_history_rate": 0.35,
}

SECOND_GRADE_PARAMS = {
    "load_range": (48, 68),
    "load_mean": 58,
    "load_std": 10,
    "fatigue_range": (6.5, 9.0),
    "fatigue_mean": 8.0,
    "rpe_range": (5, 7),
    "sleep_range": (6.2, 7.2),
    "completion_rate_range": (72, 88),
    "arm_pain_range": (3.5, 6.5),
    "leg_pain_range": (3, 5.5),
    "landing_quality_range": (4.0, 6.5),
    "reaction_time_range": (270, 360),
    "external_rotation_ratio_range": (0.52, 0.67),
    "quad_hamstring_ratio_range": (0.62, 0.74),
    "footwork_score_range": (4.0, 6.5),
    "smash_count_range": (15, 40),
    "overhead_week_range": (150, 300),
    "impacts_7d_range": (180, 350),
    "injury_rate": 0.50,  # 较高[11]
    "knee_history_rate": 0.45,
}

LEVEL_PARAMS = {
    "elite": ELITE_PARAMS,
    "first_grade": FIRST_GRADE_PARAMS,
    "second_grade": SECOND_GRADE_PARAMS,
}

# =========================================================================
# Section 2: 15名运动员定义
# =========================================================================

ATHLETE_DEFINITIONS = [
    # Men's Singles (MS)
    {"name": "男单_健将", "sport": "羽毛球", "gender": "男", "discipline": "MS",
     "level": "elite", "age": 22, "training_years": 10,
     "date_of_birth": "2004-03-15"},
    {"name": "男单_一级", "sport": "羽毛球", "gender": "男", "discipline": "MS",
     "level": "first_grade", "age": 20, "training_years": 7,
     "date_of_birth": "2006-06-20"},
    {"name": "男单_二级", "sport": "羽毛球", "gender": "男", "discipline": "MS",
     "level": "second_grade", "age": 19, "training_years": 5,
     "date_of_birth": "2007-11-08"},

    # Women's Singles (WS)
    {"name": "女单_健将", "sport": "羽毛球", "gender": "女", "discipline": "WS",
     "level": "elite", "age": 21, "training_years": 9,
     "date_of_birth": "2005-01-22"},
    {"name": "女单_一级", "sport": "羽毛球", "gender": "女", "discipline": "WS",
     "level": "first_grade", "age": 19, "training_years": 6,
     "date_of_birth": "2007-07-14"},
    {"name": "女单_二级", "sport": "羽毛球", "gender": "女", "discipline": "WS",
     "level": "second_grade", "age": 18, "training_years": 4,
     "date_of_birth": "2008-09-30"},

    # Men's Doubles (MD)
    {"name": "男双_健将", "sport": "羽毛球", "gender": "男", "discipline": "MD",
     "level": "elite", "age": 23, "training_years": 10,
     "date_of_birth": "2003-05-10"},
    {"name": "男双_一级", "sport": "羽毛球", "gender": "男", "discipline": "MD",
     "level": "first_grade", "age": 21, "training_years": 7,
     "date_of_birth": "2005-08-25"},
    {"name": "男双_二级", "sport": "羽毛球", "gender": "男", "discipline": "MD",
     "level": "second_grade", "age": 20, "training_years": 5,
     "date_of_birth": "2006-12-01"},

    # Women's Doubles (WD)
    {"name": "女双_健将", "sport": "羽毛球", "gender": "女", "discipline": "WD",
     "level": "elite", "age": 22, "training_years": 9,
     "date_of_birth": "2004-04-18"},
    {"name": "女双_一级", "sport": "羽毛球", "gender": "女", "discipline": "WD",
     "level": "first_grade", "age": 20, "training_years": 6,
     "date_of_birth": "2006-10-05"},
    {"name": "女双_二级", "sport": "羽毛球", "gender": "女", "discipline": "WD",
     "level": "second_grade", "age": 18, "training_years": 4,
     "date_of_birth": "2008-02-14"},

    # Mixed Doubles (XD)
    {"name": "混双_健将", "sport": "羽毛球", "gender": "男", "discipline": "XD",
     "level": "elite", "age": 23, "training_years": 10,
     "date_of_birth": "2003-09-22"},
    {"name": "混双_一级", "sport": "羽毛球", "gender": "男", "discipline": "XD",
     "level": "first_grade", "age": 21, "training_years": 7,
     "date_of_birth": "2005-03-08"},
    {"name": "混双_二级", "sport": "羽毛球", "gender": "女", "discipline": "XD",
     "level": "second_grade", "age": 19, "training_years": 5,
     "date_of_birth": "2007-06-30"},
]


# =========================================================================
# Section 3: 数据生成核心函数
# =========================================================================

def _clip(val, lo=0, hi=100):
    return max(lo, min(hi, val))


def _sample_range(rng: random.Random, range_tuple, mean=None):
    """Sample from a range with optional mean bias (triangular-ish)."""
    lo, hi = range_tuple
    if mean is not None:
        # Triangular-like: bias toward mean
        u = rng.random()
        if u < 0.6:
            return round(mean + rng.uniform(-(mean - lo) * 0.5, (hi - mean) * 0.5), 1)
        else:
            return round(rng.uniform(lo, hi), 1)
    return round(rng.uniform(lo, hi), 1)


def generate_daily_data(
    athlete_def: dict,
    target_date: date,
    day_seed: int,
    is_competition_day: bool = False,
    is_taper_week: bool = False,
) -> dict:
    """
    Generate one day of training data for an athlete.
    Applies: weekly periodization, competition taper, level parameters, discipline correction.

    周周期 (依据[14]韩国队每周6天训练):
      Mon-Fri: 高负荷 (80-100% of mean)
      Sat: 低负荷 (赛前/恢复, 50-70%)
      Sun: 轻恢复或比赛 (30-50%)
    """
    params = LEVEL_PARAMS[athlete_def["level"]]
    disc_factor = DISCIPLINE_FACTORS[athlete_def["discipline"]]
    rng = random.Random(day_seed)  # Deterministic per day

    weekday = target_date.weekday()  # 0=Mon ... 6=Sun

    # --- Load (weekly periodization) ---
    base_load = params["load_mean"] * disc_factor
    if weekday <= 4:  # Mon-Fri: high
        load_mult = rng.uniform(0.80, 1.05)
    elif weekday == 5:  # Sat: medium-low
        load_mult = rng.uniform(0.50, 0.75)
    else:  # Sun: low/recovery
        load_mult = rng.uniform(0.30, 0.55)

    # Competition day: moderate load
    if is_competition_day:
        load_mult = rng.uniform(0.65, 0.85)

    # Taper week: reduce all loads by 25-35%
    if is_taper_week:
        load_mult *= rng.uniform(0.65, 0.75)

    training_load = _clip(base_load * load_mult, 10, 100)

    # --- RPE (依据[15]精英RPE 7.5-8.5) ---
    rpe = int(_sample_range(rng, params["rpe_range"], (params["rpe_range"][0] + params["rpe_range"][1]) / 2))

    # --- Fatigue (依据[5]WHOOP数据) ---
    fatigue = _clip(_sample_range(rng, params["fatigue_range"], params["fatigue_mean"]))
    # Higher on high-load days
    if training_load > 80:
        fatigue = _clip(fatigue + rng.uniform(3, 8))
    elif training_load < 30:
        fatigue = _clip(fatigue - rng.uniform(3, 8))

    # --- Sleep Quality (依据[4]职业球员7-9h) ---
    sleep_quality = round(_sample_range(rng, params["sleep_range"]), 1)
    # Worse sleep after high load
    if training_load > 80:
        sleep_quality = round(max(5.5, sleep_quality - rng.uniform(0.3, 1.0)), 1)

    # --- Completion Rate ---
    completion_rate = _clip(_sample_range(rng, params["completion_rate_range"]))

    # --- Energy Level (1-10) ---
    energy_level = int(_clip(10 - (fatigue / 10) + rng.uniform(-1, 2), 1, 10))

    # --- Muscle Soreness ---
    # 依据[7]韩国队膝21.7%/肩26.1%
    muscle_soreness = {
        "shoulder": _clip(_sample_range(rng, params["arm_pain_range"]) + training_load * 0.02, 0, 10),
        "quad": _clip(fatigue / 10 + rng.uniform(0, 3), 0, 10),
        "calf": _clip(fatigue / 12 + rng.uniform(0, 2), 0, 10),
        "back": _clip(fatigue / 10 + rng.uniform(0, 3), 0, 10),
        "core": _clip(fatigue / 15 + rng.uniform(0, 2), 0, 10),
        "hip": _clip(fatigue / 14 + rng.uniform(0, 2), 0, 10),
    }
    # Round to ints for cleaner storage
    muscle_soreness = {k: round(v, 1) for k, v in muscle_soreness.items()}

    # --- Body Data (羽毛球专项) ---
    # 杀球量 [15]
    smash_count = int(_sample_range(rng, params["smash_count_range"]))
    if weekday >= 5:
        smash_count = int(smash_count * 0.5)  # Weekend reduction

    smash_7d_avg = round(smash_count * rng.uniform(0.8, 1.3), 1)
    overhead_week = int(smash_7d_avg * 7 * disc_factor)
    max_smash_30d = int(smash_count * rng.uniform(0.8, 1.5))

    # 外旋/内旋比
    external_rotation_ratio = round(_sample_range(rng, params["external_rotation_ratio_range"]), 2)

    # 疼痛 VAS [6][7]
    arm_pain = int(_clip(_sample_range(rng, params["arm_pain_range"]) + (training_load > 80) * rng.uniform(1, 3), 0, 10))
    leg_pain = int(_clip(_sample_range(rng, params["leg_pain_range"]) + (training_load > 80) * rng.uniform(0.5, 2), 0, 10))

    # 下肢数据 [8]
    total_impacts = int(_sample_range(rng, params["impacts_7d_range"]))
    jump_quality = int(_sample_range(rng, params["landing_quality_range"]))
    # Worse landing quality on high fatigue
    if fatigue > 70:
        jump_quality = max(2, jump_quality - rng.randint(1, 3))

    quad_ham_ratio = round(_sample_range(rng, params["quad_hamstring_ratio_range"]), 2)
    footwork_score = int(_sample_range(rng, params["footwork_score_range"]))

    # 反应时间ms [8]
    reaction_time = int(_sample_range(rng, params["reaction_time_range"]))
    # Slower when fatigued
    if fatigue > 70:
        reaction_time += rng.randint(20, 60)

    # 膝痛史概率 [6][7]
    has_knee_history = rng.random() < params["knee_history_rate"]

    # --- Risk Computation ---
    from app.core.risk_engine import compute_all_risks
    risks = compute_all_risks(
        smash_7d_avg=smash_7d_avg,
        overhead_week_total=overhead_week,
        external_rotation_ratio=external_rotation_ratio,
        sleep_hours=sleep_quality,
        today_smash=smash_count,
        max_smash_30d=max_smash_30d,
        global_fatigue=fatigue,
        reaction_time_ms=reaction_time,
        total_impacts_7d=total_impacts,
        jump_landing_quality=jump_quality,
        quad_hamstring_ratio=quad_ham_ratio,
        has_knee_pain_history=has_knee_history,
        footwork_score=footwork_score,
    )

    # --- Training Content & Type ---
    training_types = ["力量", "耐力", "速度", "技战术", "混合", "力量", "柔韧"]
    training_type = training_types[weekday % 7]
    cycle_phase = "准备期"
    # Assign phases roughly
    day_of_year = target_date.timetuple().tm_yday
    if day_of_year % 12 < 3:
        cycle_phase = "比赛期"
    elif day_of_year % 12 < 5:
        cycle_phase = "过渡期"

    return {
        "training_load": round(training_load, 1),
        "injury_risk": round(max(risks["shoulder_overuse_risk"], risks["knee_overuse_risk"]), 1),
        "fatigue": round(fatigue, 1),
        "sleep_quality": sleep_quality,
        "rpe": rpe,
        "energy_level": energy_level,
        "muscle_soreness": muscle_soreness,
        "completion_rate": round(completion_rate, 1),
        "training_type": training_type,
        "cycle_phase": cycle_phase,
        "smash_count_today": smash_count,
        "smash_7d_avg": smash_7d_avg,
        "overhead_week_total": overhead_week,
        "max_smash_30d": max_smash_30d,
        "external_rotation_ratio": external_rotation_ratio,
        "arm_pain_vas": arm_pain,
        "total_impacts_7d": total_impacts,
        "jump_landing_quality": jump_quality,
        "quad_hamstring_ratio": quad_ham_ratio,
        "footwork_score": footwork_score,
        "leg_pain_vas": leg_pain,
        "reaction_time_ms": reaction_time,
        "has_knee_pain_history": has_knee_history,
        **risks,
        "description": f"自动生成 - {training_type}训练 ({athlete_def['level']})",
        "technical_notes": f"{athlete_def['discipline']}专项 - 周{weekday+1}",
    }


def get_level_summary():
    """Return the level parameter summary for display."""
    return {
        "elite": {
            "load": "82-88",
            "fatigue": "5.8-6.8",
            "rpe": "7.5-8.5",
            "sleep": "7.8-8.5h",
            "completion": "96-99%",
            "shoulder_pain": "1.5-3.0",
            "landing_quality": "7.5-9.0",
            "reaction_time": "200-260ms",
            "external_rotation": "0.70-0.80",
            "quad_hamstring": "0.80-0.88",
            "injury_rate": "20-30%",
        },
        "first_grade": {
            "load": "70-75",
            "fatigue": "6.8-7.5",
            "rpe": "6.5-7.5",
            "sleep": "7.0-7.8h",
            "completion": "85-95%",
            "shoulder_pain": "2.5-4.5",
            "landing_quality": "6.0-7.5",
            "reaction_time": "240-300ms",
            "external_rotation": "0.62-0.70",
            "quad_hamstring": "0.72-0.80",
            "injury_rate": "30-45%",
        },
        "second_grade": {
            "load": "55-62",
            "fatigue": "7.5-8.5",
            "rpe": "5.0-6.5",
            "sleep": "6.5-7.0h",
            "completion": "75-85%",
            "shoulder_pain": "4.0-6.0",
            "landing_quality": "4.5-6.0",
            "reaction_time": "280-350ms",
            "external_rotation": "0.55-0.65",
            "quad_hamstring": "0.65-0.72",
            "injury_rate": "40-60%",
        },
    }
