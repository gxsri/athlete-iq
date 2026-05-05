"""
AthleteIQ - Training Templates & Assignments API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from uuid import UUID
from typing import List, Optional

from app.database import get_db, logger
from app.models.athlete import (
    Athlete, DailyMetric, TrainingTemplate, TrainingAssignment,
)
from app.schemas.schemas import (
    TrainingTemplateCreate, TrainingTemplateUpdate, TrainingTemplateResponse,
    TrainingAssignmentCreate, TrainingAssignmentResponse,
)

router = APIRouter(prefix="/api", tags=["训练模板与计划"])

# ============ 6 Badminton Preset Templates ============

PRESET_TEMPLATES = [
    {
        "name": "基础耐力日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "中", "target_focus": ["技术", "步法", "耐力"],
        "is_public": True, "description": "技术练习+步法训练+低强度对抗",
        "content": {"target_load": 65, "target_rpe": 6, "target_duration_min": 120,
            "segments": [
                {"name": "热身", "type": "柔韧", "duration_min": 15, "rpe": 3},
                {"name": "步法训练", "type": "技战术", "duration_min": 25, "rpe": 6},
                {"name": "技术练习", "type": "技战术", "duration_min": 30, "rpe": 5},
                {"name": "低强度对抗", "type": "混合", "duration_min": 30, "rpe": 6},
                {"name": "核心训练", "type": "力量", "duration_min": 15, "rpe": 5},
                {"name": "拉伸", "type": "柔韧", "duration_min": 5, "rpe": 2},
            ]},
    },
    {
        "name": "爆发力日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "高", "target_focus": ["爆发力", "杀球", "速度"],
        "is_public": True, "description": "高强度爆发：杀球专项+跳箱+冲刺",
        "content": {"target_load": 85, "target_rpe": 8, "target_duration_min": 105,
            "segments": [
                {"name": "热身", "type": "柔韧", "duration_min": 15, "rpe": 3},
                {"name": "杀球专项", "type": "技战术", "duration_min": 25, "rpe": 8},
                {"name": "跳箱训练", "type": "力量", "duration_min": 15, "rpe": 8},
                {"name": "冲刺训练", "type": "速度", "duration_min": 15, "rpe": 9},
                {"name": "对抗练习", "type": "混合", "duration_min": 25, "rpe": 8},
                {"name": "拉伸+冰敷", "type": "柔韧", "duration_min": 10, "rpe": 2},
            ]},
    },
    {
        "name": "技术日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "低", "target_focus": ["技术", "精准", "分析"],
        "is_public": True, "description": "技术专项：吊球/网前+录像分析",
        "content": {"target_load": 60, "target_rpe": 5, "target_duration_min": 120,
            "segments": [
                {"name": "热身", "type": "柔韧", "duration_min": 10, "rpe": 2},
                {"name": "吊球技术", "type": "技战术", "duration_min": 25, "rpe": 5},
                {"name": "网前技术", "type": "技战术", "duration_min": 25, "rpe": 4},
                {"name": "发球练习", "type": "技战术", "duration_min": 15, "rpe": 3},
                {"name": "录像分析", "type": "混合", "duration_min": 30, "rpe": 2},
                {"name": "轻度核心", "type": "力量", "duration_min": 15, "rpe": 5},
            ]},
    },
    {
        "name": "对抗日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "高", "target_focus": ["实战", "战术", "对抗"],
        "is_public": True, "description": "全场比赛+战术模拟",
        "content": {"target_load": 80, "target_rpe": 7, "target_duration_min": 120,
            "segments": [
                {"name": "热身", "type": "柔韧", "duration_min": 15, "rpe": 3},
                {"name": "战术演练", "type": "技战术", "duration_min": 20, "rpe": 6},
                {"name": "半场对抗", "type": "混合", "duration_min": 25, "rpe": 7},
                {"name": "全场对抗", "type": "混合", "duration_min": 35, "rpe": 8},
                {"name": "体能收尾", "type": "耐力", "duration_min": 15, "rpe": 8},
                {"name": "拉伸", "type": "柔韧", "duration_min": 10, "rpe": 2},
            ]},
    },
    {
        "name": "赛前减量日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "低", "target_focus": ["恢复", "技术", "心理"],
        "is_public": True, "description": "赛前减量：轻量步法+反应训练",
        "content": {"target_load": 35, "target_rpe": 4, "target_duration_min": 75,
            "segments": [
                {"name": "热身", "type": "柔韧", "duration_min": 10, "rpe": 2},
                {"name": "轻量步法", "type": "技战术", "duration_min": 20, "rpe": 4},
                {"name": "反应训练", "type": "速度", "duration_min": 15, "rpe": 5},
                {"name": "技术回顾", "type": "技战术", "duration_min": 20, "rpe": 3},
                {"name": "拉伸", "type": "柔韧", "duration_min": 10, "rpe": 2},
            ]},
    },
    {
        "name": "恢复日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "低", "target_focus": ["恢复", "柔韧", "康复"],
        "is_public": True, "description": "主动恢复：拉伸+游泳/低强度有氧",
        "content": {"target_load": 20, "target_rpe": 2, "target_duration_min": 60,
            "segments": [
                {"name": "动态拉伸", "type": "柔韧", "duration_min": 15, "rpe": 2},
                {"name": "游泳/骑行", "type": "耐力", "duration_min": 30, "rpe": 3},
                {"name": "泡沫轴放松", "type": "柔韧", "duration_min": 15, "rpe": 1},
            ]},
    },
]


async def seed_preset_templates(db: AsyncSession):
    """Seed 6 preset badminton templates if table is empty."""
    existing = await db.execute(select(func.count()).select_from(TrainingTemplate))
    if existing.scalar() == 0:
        for tmpl in PRESET_TEMPLATES:
            db.add(TrainingTemplate(**tmpl))
        await db.commit()
        logger.info(f"Seeded {len(PRESET_TEMPLATES)} preset templates")


# ============ Template CRUD ============

@router.get("/templates", response_model=List[TrainingTemplateResponse])
async def list_templates(
    type: Optional[str] = Query(None),
    focus: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await seed_preset_templates(db)
    query = select(TrainingTemplate)
    if type:
        query = query.where(TrainingTemplate.type == type)
    if focus:
        query = query.where(TrainingTemplate.target_focus.contains([focus]))
    query = query.order_by(TrainingTemplate.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/templates", response_model=TrainingTemplateResponse, status_code=201)
async def create_template(data: TrainingTemplateCreate, db: AsyncSession = Depends(get_db)):
    template = TrainingTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/templates/{template_id}", response_model=TrainingTemplateResponse)
async def update_template(template_id: UUID, data: TrainingTemplateUpdate, db: AsyncSession = Depends(get_db)):
    template = await db.get(TrainingTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    for field in ["name", "type", "intensity_zone", "is_public", "content", "description"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(template, field, val)
    if data.target_focus is not None:
        template.target_focus = data.target_focus
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
async def delete_template(template_id: UUID, db: AsyncSession = Depends(get_db)):
    template = await db.get(TrainingTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    await db.delete(template)
    await db.commit()
    return {"status": "deleted"}


# ============ Assignment CRUD ============

@router.post("/assignments", response_model=TrainingAssignmentResponse, status_code=201)
async def create_assignment(data: TrainingAssignmentCreate, db: AsyncSession = Depends(get_db)):
    athlete = await db.get(Athlete, data.athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")
    template = await db.get(TrainingTemplate, data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    existing = await db.execute(select(TrainingAssignment).where(
        TrainingAssignment.athlete_id == data.athlete_id,
        TrainingAssignment.scheduled_date == data.scheduled_date))
    assignment = existing.scalar_one_or_none()

    if assignment:
        assignment.template_id = data.template_id
        assignment.overrides = data.overrides or {}
        assignment.notes = data.notes
    else:
        assignment = TrainingAssignment(
            athlete_id=data.athlete_id, template_id=data.template_id,
            scheduled_date=data.scheduled_date,
            overrides=data.overrides or {}, notes=data.notes)
        db.add(assignment)

    await db.commit()
    await db.refresh(assignment)
    assignment.template_name = template.name
    assignment.template_content = template.content
    return assignment


@router.get("/assignments/calendar", response_model=List[TrainingAssignmentResponse])
async def get_calendar_assignments(
    athlete_id: UUID = Query(...),
    month: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(TrainingAssignment).where(TrainingAssignment.athlete_id == athlete_id)
    if month:
        year, mon = month.split("-")
        start_date = date(int(year), int(mon), 1)
        if int(mon) == 12:
            end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(int(year), int(mon) + 1, 1) - timedelta(days=1)
        query = query.where(TrainingAssignment.scheduled_date >= start_date,
                           TrainingAssignment.scheduled_date <= end_date)
    query = query.order_by(TrainingAssignment.scheduled_date.asc())
    result = await db.execute(query)
    assignments = result.scalars().all()
    for a in assignments:
        if a.template_id:
            tmpl = await db.get(TrainingTemplate, a.template_id)
            if tmpl:
                a.template_name = tmpl.name
                a.template_content = tmpl.content
    return assignments


@router.post("/assignments/{assignment_id}/complete")
async def complete_assignment(
    assignment_id: UUID,
    actual_log_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.get(TrainingAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="计划不存在")
    assignment.status = "completed"
    if actual_log_id:
        assignment.actual_log_id = actual_log_id
    await db.commit()
    return {"status": "completed"}
