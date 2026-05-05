"""
AthleteIQ - 周期化模板 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import (
    PeriodizationTemplate, Athlete, PlannedSession, PlannedExercise,
)
from app.schemas.schemas import (
    PeriodizationTemplateCreate, PeriodizationTemplateResponse,
    ApplyTemplateRequest,
)
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/templates", tags=["周期化模板"])


@router.get("/", response_model=List[PeriodizationTemplateResponse])
async def list_templates(
    template_type: Optional[str] = Query(None, description="线性周期/非线性DUP/板块周期"),
    cycle_phase: Optional[str] = Query(None, description="一般准备期/专项准备期/比赛期/过渡期"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(PeriodizationTemplate)
    if template_type:
        query = query.where(PeriodizationTemplate.template_type == template_type)
    if cycle_phase:
        query = query.where(PeriodizationTemplate.cycle_phase == cycle_phase)

    query = query.order_by(PeriodizationTemplate.is_system.desc(), PeriodizationTemplate.created_at.desc())
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PeriodizationTemplateResponse, status_code=201)
async def create_template(data: PeriodizationTemplateCreate, db: AsyncSession = Depends(get_db)):
    try:
        template = PeriodizationTemplate(**data.model_dump())
        db.add(template)
        await db.commit()
        await db.refresh(template)
        logger.info(f"Created template {template.id}: {template.name}")
        return template
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating template: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create template")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/{template_id}", response_model=PeriodizationTemplateResponse)
async def get_template(template_id: UUID, db: AsyncSession = Depends(get_db)):
    template = await db.get(PeriodizationTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/{template_id}/apply")
async def apply_template(
    template_id: UUID,
    data: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        template = await db.get(PeriodizationTemplate, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        weekly_structure = template.weekly_structure or []

        created_sessions = []

        for athlete_id in data.athlete_ids:
            athlete = await db.get(Athlete, athlete_id)
            if not athlete:
                continue

            current_date = data.start_date
            for week_block in weekly_structure:
                if not isinstance(week_block, dict):
                    continue
                week_num = week_block.get("week", 0)
                sessions = week_block.get("sessions", [])

                for day_idx, sess in enumerate(sessions):
                    if not isinstance(sess, dict):
                        continue

                    plan_date = current_date + timedelta(days=day_idx)

                    planned_session = PlannedSession(
                        athlete_id=athlete_id,
                        plan_date=plan_date,
                        session_name=sess.get("description", sess.get("day", "")),
                        training_type=sess.get("type", "混合"),
                        notes=f"模板: {template.name} - 第{week_num}周",
                    )
                    db.add(planned_session)
                    await db.flush()
                    created_sessions.append(str(planned_session.id))

                current_date = current_date + timedelta(days=7)

        await db.commit()
        logger.info(f"Applied template {template_id} to {len(data.athlete_ids)} athletes")
        return {
            "status": "applied",
            "template_name": template.name,
            "athletes_count": len(data.athlete_ids),
            "sessions_created": len(created_sessions),
        }
    except IntegrityError as e:
        logger.warning(f"IntegrityError applying template {template_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to apply template {template_id}")
        raise HTTPException(status_code=500, detail=f"应用失败: {str(e)[:200]}")
