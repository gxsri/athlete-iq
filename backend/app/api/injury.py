"""
AthleteIQ - 伤病管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import (
    Athlete, InjuryRecord, InjuryRehabLog,
    InjuryRestriction, ReturnToPlayChecklist,
)
from app.schemas.schemas import (
    InjuryRecordCreate, InjuryRecordUpdate, InjuryRecordResponse,
    InjuryRehabLogCreate, InjuryRehabLogResponse,
    InjuryRestrictionCreate, InjuryRestrictionResponse,
    ReturnToPlayChecklistCreate, ReturnToPlayChecklistUpdate,
    ReturnToPlayChecklistResponse,
)
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/injury", tags=["伤病管理"])


@router.post("/records", response_model=InjuryRecordResponse, status_code=201)
async def create_injury_record(data: InjuryRecordCreate, db: AsyncSession = Depends(get_db)):
    try:
        athlete = await db.get(Athlete, data.athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        record_data = data.model_dump(exclude={"restrictions", "checklist_items"})
        injury = InjuryRecord(**record_data)
        db.add(injury)
        await db.flush()

        for r in data.restrictions:
            rest = InjuryRestriction(injury_record_id=injury.id, **r.model_dump())
            db.add(rest)

        for c in data.checklist_items:
            check = ReturnToPlayChecklist(injury_record_id=injury.id, **c.model_dump())
            db.add(check)

        await db.commit()
        await db.refresh(injury)
        logger.info(f"Created injury record {injury.id} for athlete {data.athlete_id}")
        return await _load_injury_detail(injury.id, db)
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating injury record: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create injury record")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/records", response_model=List[InjuryRecordResponse])
async def list_injury_records(
    athlete_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, description="活跃/康复中/已恢复"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(InjuryRecord)
    if athlete_id:
        query = query.where(InjuryRecord.athlete_id == athlete_id)
    if status:
        query = query.where(InjuryRecord.status == status)

    query = query.order_by(InjuryRecord.injury_date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    responses = []
    for r in records:
        responses.append(await _load_injury_detail(r.id, db))
    return responses


@router.get("/records/{record_id}", response_model=InjuryRecordResponse)
async def get_injury_record(record_id: UUID, db: AsyncSession = Depends(get_db)):
    injury = await db.get(InjuryRecord, record_id)
    if not injury:
        raise HTTPException(status_code=404, detail="伤病记录不存在")
    return await _load_injury_detail(record_id, db)


@router.put("/records/{record_id}", response_model=InjuryRecordResponse)
async def update_injury_record(
    record_id: UUID,
    data: InjuryRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        injury = await db.get(InjuryRecord, record_id)
        if not injury:
            raise HTTPException(status_code=404, detail="伤病记录不存在")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(injury, key, value)

        if data.status == "已恢复" and not injury.actual_return_date:
            injury.actual_return_date = date.today()

        await db.commit()
        await db.refresh(injury)
        logger.info(f"Updated injury record {record_id}")
        return await _load_injury_detail(record_id, db)
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating injury record {record_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update injury record {record_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/records/{record_id}/rehab-logs", response_model=InjuryRehabLogResponse, status_code=201)
async def add_rehab_log(
    record_id: UUID,
    data: InjuryRehabLogCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        injury = await db.get(InjuryRecord, record_id)
        if not injury:
            raise HTTPException(status_code=404, detail="伤病记录不存在")

        rehab = InjuryRehabLog(injury_record_id=record_id, **data.model_dump())
        db.add(rehab)
        await db.commit()
        await db.refresh(rehab)
        logger.info(f"Added rehab log {rehab.id} to injury record {record_id}")
        return rehab
    except IntegrityError as e:
        logger.warning(f"IntegrityError adding rehab log: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add rehab log to record {record_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/records/{record_id}/restrictions", response_model=InjuryRestrictionResponse, status_code=201)
async def add_restriction(
    record_id: UUID,
    data: InjuryRestrictionCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        injury = await db.get(InjuryRecord, record_id)
        if not injury:
            raise HTTPException(status_code=404, detail="伤病记录不存在")

        restriction = InjuryRestriction(injury_record_id=record_id, **data.model_dump())
        db.add(restriction)
        await db.commit()
        await db.refresh(restriction)
        logger.info(f"Added restriction {restriction.id} to injury record {record_id}")
        return restriction
    except IntegrityError as e:
        logger.warning(f"IntegrityError adding restriction: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add restriction to record {record_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.put("/checklist/{checklist_id}", response_model=ReturnToPlayChecklistResponse)
async def update_checklist_item(
    checklist_id: UUID,
    data: ReturnToPlayChecklistUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await db.get(ReturnToPlayChecklist, checklist_id)
        if not item:
            raise HTTPException(status_code=404, detail="检查清单项不存在")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        if data.is_passed and not item.passed_date:
            item.passed_date = date.today()

        await db.commit()
        await db.refresh(item)
        logger.info(f"Updated checklist item {checklist_id}")
        return item
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating checklist item {checklist_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update checklist item {checklist_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/athlete/{athlete_id}/active-restrictions", response_model=List[InjuryRestrictionResponse])
async def get_active_restrictions(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    athlete = await db.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    result = await db.execute(
        select(InjuryRestriction)
        .join(InjuryRecord)
        .where(
            InjuryRecord.athlete_id == athlete_id,
            InjuryRestriction.is_active == True,
            or_(InjuryRecord.status == "活跃", InjuryRecord.status == "康复中"),
        )
    )
    return result.scalars().all()


async def _load_injury_detail(record_id: UUID, db: AsyncSession):
    injury = await db.get(InjuryRecord, record_id)
    if not injury:
        return None

    # 加载限制
    rest_result = await db.execute(
        select(InjuryRestriction).where(InjuryRestriction.injury_record_id == record_id)
    )
    restrictions = rest_result.scalars().all()

    # 加载清单
    check_result = await db.execute(
        select(ReturnToPlayChecklist).where(ReturnToPlayChecklist.injury_record_id == record_id)
    )
    checklist = check_result.scalars().all()

    # 加载康复日志
    rehab_result = await db.execute(
        select(InjuryRehabLog)
        .where(InjuryRehabLog.injury_record_id == record_id)
        .order_by(InjuryRehabLog.log_date.desc())
    )
    rehab_logs = rehab_result.scalars().all()

    return InjuryRecordResponse(
        id=injury.id,
        athlete_id=injury.athlete_id,
        diagnosis=injury.diagnosis,
        injury_date=injury.injury_date,
        expected_recovery_weeks=injury.expected_recovery_weeks,
        actual_return_date=injury.actual_return_date,
        status=injury.status,
        body_part=injury.body_part,
        severity=injury.severity,
        notes=injury.notes,
        created_at=injury.created_at,
        updated_at=injury.updated_at,
        restrictions=[
            InjuryRestrictionResponse(
                id=r.id,
                injury_record_id=r.injury_record_id,
                restriction_type=r.restriction_type,
                restriction_detail=r.restriction_detail,
                exercise_name_pattern=r.exercise_name_pattern,
                is_active=r.is_active,
            )
            for r in restrictions
        ],
        checklist_items=[
            ReturnToPlayChecklistResponse(
                id=c.id,
                injury_record_id=c.injury_record_id,
                check_item=c.check_item,
                target_value=c.target_value,
                actual_value=c.actual_value,
                unit=c.unit,
                is_passed=c.is_passed,
                passed_date=c.passed_date,
                notes=c.notes,
            )
            for c in checklist
        ],
        rehab_logs=[
            InjuryRehabLogResponse(
                id=rl.id,
                injury_record_id=rl.injury_record_id,
                log_date=rl.log_date,
                pain_score=rl.pain_score,
                rehab_completion_pct=rl.rehab_completion_pct,
                exercises_completed=rl.exercises_completed,
                notes=rl.notes,
            )
            for rl in rehab_logs
        ],
    )
