"""
AthleteIQ - 训练计划偏差分析模块
对比计划训练负荷与实际执行负荷，检测训练偏差
"""
from __future__ import annotations
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ExerciseDeviation:
    exercise_name: str
    planned_load: float
    actual_load: float
    load_deviation_pct: float
    planned_reps: Optional[int] = None
    actual_reps: Optional[int] = None
    planned_sets: Optional[int] = None
    actual_sets: Optional[int] = None
    planned_weight: Optional[float] = None
    actual_weight: Optional[float] = None


@dataclass
class SessionDeviationResult:
    plan_load: float
    actual_load: float
    deviation_pct: float
    is_over_threshold: bool
    exercise_deviations: List[ExerciseDeviation] = field(default_factory=list)
    summary: str = ""


def calculate_exercise_load(weight: float, reps: int, sets: int, rpe: int = 5) -> float:
    """Calculate exercise load using volume × intensity formula.
    For bodyweight exercises (weight=0), uses sets × reps × (RPE/10) × 10.
    For weighted exercises, adds weight × sets factor.
    """
    if weight is None:
        weight = 0
    if reps is None:
        reps = 0
    if sets is None:
        sets = 0
    if rpe is None:
        rpe = 5
    # Base load from volume and intensity
    base_load = sets * reps * (rpe / 10.0) * 10
    # Additional load from external weight
    weight_load = weight * sets * 0.5
    return round(base_load + weight_load, 2)


def calculate_deviation(
    planned_exercises: List[Dict],
    actual_exercises: List[Dict],
    threshold_pct: float = 20.0,
) -> SessionDeviationResult:
    """
    计算计划与实际训练之间的偏差

    Args:
        planned_exercises: [{"exercise_name": str, "weight": float, "reps": int, "sets": int}, ...]
        actual_exercises: [{"exercise_name": str, "weight": float, "reps": int, "sets": int}, ...]
        threshold_pct: 偏差阈值百分比，超过此值标记为 over_threshold

    Returns:
        SessionDeviationResult with load comparisons and per-exercise details
    """
    plan_total = 0.0
    actual_total = 0.0
    deviations = []

    actual_map = {}
    for ae in actual_exercises:
        name = ae.get("exercise_name", ae.get("name", ""))
        actual_map[name] = ae

    for pe in planned_exercises:
        name = pe.get("exercise_name", pe.get("name", ""))
        p_weight = pe.get("weight", pe.get("target_weight_kg", 0)) or 0
        p_reps = pe.get("reps", pe.get("target_reps", 0)) or 0
        p_sets = pe.get("sets", pe.get("target_sets", 0)) or 0
        planned_load = calculate_exercise_load(p_weight, p_reps, p_sets)
        plan_total += planned_load

        ae = actual_map.get(name, {})
        a_weight = ae.get("weight", ae.get("actual_weight_kg", 0)) or 0
        a_reps = ae.get("reps", ae.get("actual_reps", 0)) or 0
        a_sets = ae.get("sets", ae.get("actual_sets", 0)) or 0
        actual_load = calculate_exercise_load(a_weight, a_reps, a_sets)
        actual_total += actual_load

        if planned_load > 0:
            load_dev = ((actual_load - planned_load) / planned_load) * 100
        else:
            load_dev = 0.0

        deviations.append(ExerciseDeviation(
            exercise_name=name,
            planned_load=planned_load,
            actual_load=actual_load,
            load_deviation_pct=round(load_dev, 1),
            planned_reps=int(p_reps) if p_reps else None,
            actual_reps=int(a_reps) if a_reps else None,
            planned_sets=int(p_sets) if p_sets else None,
            actual_sets=int(a_sets) if a_sets else None,
            planned_weight=float(p_weight) if p_weight else None,
            actual_weight=float(a_weight) if a_weight else None,
        ))

    # 处理仅在实际执行中出现的练习 (未计划的)
    planned_names = {pe.get("exercise_name", pe.get("name", "")) for pe in planned_exercises}
    for ae in actual_exercises:
        name = ae.get("exercise_name", ae.get("name", ""))
        if name not in planned_names:
            a_weight = ae.get("weight", ae.get("actual_weight_kg", 0)) or 0
            a_reps = ae.get("reps", ae.get("actual_reps", 0)) or 0
            a_sets = ae.get("sets", ae.get("actual_sets", 0)) or 0
            actual_load = calculate_exercise_load(a_weight, a_reps, a_sets)
            actual_total += actual_load
            deviations.append(ExerciseDeviation(
                exercise_name=f"(未计划) {name}",
                planned_load=0,
                actual_load=actual_load,
                load_deviation_pct=100.0,
                actual_reps=int(a_reps) if a_reps else None,
                actual_sets=int(a_sets) if a_sets else None,
                actual_weight=float(a_weight) if a_weight else None,
            ))

    if plan_total > 0:
        deviation_pct = round(((actual_total - plan_total) / plan_total) * 100, 1)
    elif actual_total > 0:
        deviation_pct = 100.0
    else:
        deviation_pct = 0.0

    is_over = abs(deviation_pct) > abs(threshold_pct)

    if deviation_pct > 0:
        summary = f"实际负荷超出计划 {deviation_pct}%"
    elif deviation_pct < 0:
        summary = f"实际负荷低于计划 {abs(deviation_pct)}%"
    else:
        summary = "实际负荷与计划一致"

    return SessionDeviationResult(
        plan_load=round(plan_total, 2),
        actual_load=round(actual_total, 2),
        deviation_pct=deviation_pct,
        is_over_threshold=is_over,
        exercise_deviations=deviations,
        summary=summary,
    )


def should_trigger_deviation_alert(
    deviation_history: List[float],
    days: int = 3,
    threshold: float = 20.0,
) -> bool:
    """
    判断是否应触发偏差预警

    当最近 N 天的训练偏差连续超过阈值时触发

    Args:
        deviation_history: 每日偏差百分比列表 (按日期排序)
        days: 需要连续超过阈值的天数
        threshold: 偏差阈值百分比
    """
    if len(deviation_history) < days:
        return False

    recent = deviation_history[-days:]
    return all(abs(d) > threshold for d in recent)
