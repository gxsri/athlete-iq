"""
API endpoint to generate 15 journal-based test athletes with 120+ days of data.
POST /api/journal/generate-all
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import Athlete, TrainingLog, DailyMetric, WellnessQuestionnaire
from app.api.journal_data_generator import (
    ATHLETE_DEFINITIONS, generate_daily_data, DISCIPLINE_FACTORS, get_level_summary,
)

router = APIRouter(prefix="/api/journal", tags=["期刊数据生成"])


@router.post("/generate-all")
async def generate_all_journal_athletes(
    total_days: int = Query(130, ge=90, le=365, description="每名运动员的训练天数"),
    include_wellness: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """
    一键生成15名期刊数据运动员 + 每人 total_days 天训练数据。

    生成内容：
    - 15名运动员（MS/MD/WS/WD/XD × elite/first_grade/second_grade）
    - 每人 total_days 天的 DailyMetric（含所有身体数据 + 风险计算）
    - 每7天一条 WellnessQuestionnaire
    - 附文献依据的参数配置
    """
    results = []
    today = date.today()
    start_date = today - timedelta(days=total_days)

    for athlete_def in ATHLETE_DEFINITIONS:
        # Check if athlete already exists
        existing = await db.execute(
            select(Athlete).where(Athlete.name == athlete_def["name"])
        )
        athlete = existing.scalar_one_or_none()

        if not athlete:
            athlete = Athlete(
                name=athlete_def["name"],
                date_of_birth=date.fromisoformat(athlete_def["date_of_birth"]),
                gender=athlete_def["gender"],
                sport=athlete_def["sport"],
                athlete_type="test",
                training_years=athlete_def["training_years"],
                position_or_event=athlete_def["discipline"],
                hand_dominance="右",
                dominant_foot="右",
            )
            db.add(athlete)
            await db.flush()
            created_new = True
        else:
            created_new = False

        aid = str(athlete.id)

        # Generate daily data
        discipline_factor = DISCIPLINE_FACTORS[athlete_def["discipline"]]
        days_created = 0
        days_skipped = 0

        for day_offset in range(total_days):
            current_date = start_date + timedelta(days=day_offset)

            # Check existing
            existing_metric = await db.execute(
                select(DailyMetric).where(
                    DailyMetric.athlete_id == athlete.id,
                    DailyMetric.metric_date == current_date,
                )
            )
            if existing_metric.scalar_one_or_none():
                days_skipped += 1
                continue

            # Taper week every 5th week (依据[14]比赛密集后减量)
            week_num = day_offset // 7
            is_taper = (week_num % 5 == 4)

            # Competition day: every ~21 days (比赛期模拟 [12])
            is_comp_day = (day_offset % 21 == 10)

            data = generate_daily_data(
                athlete_def, current_date,
                day_seed=hash(f"{athlete_def['name']}_{current_date}"),
                is_competition_day=is_comp_day,
                is_taper_week=is_taper,
            )

            metric = DailyMetric(
                athlete_id=athlete.id,
                metric_date=current_date,
                training_load=data["training_load"],
                injury_risk=data["injury_risk"],
                fatigue=data["fatigue"],
                sleep_quality=data["sleep_quality"],
                rpe=data["rpe"],
                energy_level=data["energy_level"],
                muscle_soreness=data["muscle_soreness"],
                completion_rate=data["completion_rate"],
                training_content=data["description"],
                technical_notes=data["technical_notes"],
                smash_count_today=data["smash_count_today"],
                smash_7d_avg=data["smash_7d_avg"],
                overhead_week_total=data["overhead_week_total"],
                max_smash_30d=data["max_smash_30d"],
                external_rotation_ratio=data["external_rotation_ratio"],
                arm_pain_vas=data["arm_pain_vas"],
                total_impacts_7d=data["total_impacts_7d"],
                jump_landing_quality=data["jump_landing_quality"],
                quad_hamstring_ratio=data["quad_hamstring_ratio"],
                footwork_score=data["footwork_score"],
                leg_pain_vas=data["leg_pain_vas"],
                reaction_time_ms=data["reaction_time_ms"],
                has_knee_pain_history=data["has_knee_pain_history"],
                shoulder_overuse_risk=data["shoulder_overuse_risk"],
                shoulder_acute_risk=data["shoulder_acute_risk"],
                knee_overuse_risk=data["knee_overuse_risk"],
                knee_acute_risk=data["knee_acute_risk"],
            )
            db.add(metric)
            days_created += 1

            # Wellness every 7 days
            if include_wellness and day_offset % 7 == 0:
                wl = WellnessQuestionnaire(
                    athlete_id=athlete.id,
                    record_date=current_date,
                    morning_heart_rate=int(55 + data["fatigue"] * 0.15),
                    hrv_lnrmssd=round(max(30, 75 - data["fatigue"] * 0.3), 2),
                    sleep_duration_hours=data["sleep_quality"],
                    sleep_quality=int(max(1, min(5, data["sleep_quality"] / 2))),
                    fatigue_score=int(max(1, min(5, data["fatigue"] / 20))),
                    muscle_soreness=int(max(1, min(5, data["arm_pain_vas"] / 3))),
                    stress_score=int(max(1, min(5, data["fatigue"] / 20 + 1))),
                    mood_score=int(max(1, min(5, 5 - data["fatigue"] / 25))),
                    source="auto_journal",
                )
                db.add(wl)

            # Commit every 30 days to avoid huge transactions
            if day_offset % 30 == 0:
                await db.commit()

        await db.commit()

        results.append({
            "name": athlete_def["name"],
            "discipline": athlete_def["discipline"],
            "level": athlete_def["level"],
            "athlete_id": aid,
            "created_new": created_new,
            "days_created": days_created,
            "days_skipped": days_skipped,
            "factor": discipline_factor,
        })

    # Count totals
    total_created = sum(r["days_created"] for r in results)
    total_skipped = sum(r["days_skipped"] for r in results)
    total_athletes_new = sum(1 for r in results if r["created_new"])

    logger.info(f"Journal generator: {len(results)} athletes, {total_created} new days, {total_skipped} skipped")

    return {
        "status": "success",
        "athletes_count": len(results),
        "athletes_new": total_athletes_new,
        "total_days_per_athlete": total_days,
        "total_data_points": total_created,
        "total_skipped": total_skipped,
        "date_range": f"{start_date} ~ {today}",
        "discipline_factors": DISCIPLINE_FACTORS,
        "level_params": get_level_summary(),
        "athletes": results,
        "message": f"成功生成 {len(results)} 名运动员数据（{total_created} 条日数据）",
    }
