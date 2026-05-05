"""
AthleteIQ - 团队分组管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import (
    TeamGroup, TeamGroupMember, Athlete,
    ComputedMetric, InjuryRecord, PerformanceTest,
)
from app.schemas.schemas import (
    TeamGroupCreate, TeamGroupResponse,
    TeamGroupMemberResponse, TeamHeatmapEntry,
    TeamHeatmapResponse, AddMemberRequest,
)
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/groups", tags=["团队分组"])


@router.post("/", response_model=TeamGroupResponse, status_code=201)
async def create_group(data: TeamGroupCreate, db: AsyncSession = Depends(get_db)):
    try:
        group = TeamGroup(name=data.name, coach_id=data.coach_id)
        db.add(group)
        await db.commit()
        await db.refresh(group)
        logger.info(f"Created team group {group.id}: {group.name}")
        return await _load_group_with_members(group.id, db)
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating team group: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create team group")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/", response_model=List[TeamGroupResponse])
async def list_groups(
    coach_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(TeamGroup)
    if coach_id:
        query = query.where(TeamGroup.coach_id == coach_id)
    query = query.order_by(TeamGroup.created_at.desc())
    result = await db.execute(query)
    groups = result.scalars().all()

    responses = []
    for g in groups:
        responses.append(await _load_group_with_members(g.id, db))
    return responses


@router.get("/{group_id}", response_model=TeamGroupResponse)
async def get_group(group_id: UUID, db: AsyncSession = Depends(get_db)):
    group = await db.get(TeamGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return await _load_group_with_members(group_id, db)


@router.put("/{group_id}", response_model=TeamGroupResponse)
async def update_group(
    group_id: UUID,
    data: TeamGroupCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        group = await db.get(TeamGroup, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="分组不存在")
        group.name = data.name
        await db.commit()
        await db.refresh(group)
        logger.info(f"Updated team group {group_id}")
        return await _load_group_with_members(group_id, db)
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating team group {group_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update team group {group_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/{group_id}/members")
async def add_member(
    group_id: UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        group = await db.get(TeamGroup, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="分组不存在")

        athlete = await db.get(Athlete, data.athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        existing = await db.execute(
            select(TeamGroupMember).where(
                TeamGroupMember.group_id == group_id,
                TeamGroupMember.athlete_id == data.athlete_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="该运动员已在分组中")

        member = TeamGroupMember(group_id=group_id, athlete_id=data.athlete_id)
        db.add(member)
        await db.commit()
        logger.info(f"Added athlete {data.athlete_id} to group {group_id}")
        return {"status": "added", "group_id": str(group_id), "athlete_id": str(data.athlete_id)}
    except IntegrityError as e:
        logger.warning(f"IntegrityError adding member to group {group_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add member to group {group_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.delete("/{group_id}/members/{athlete_id}")
async def remove_member(
    group_id: UUID,
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(TeamGroupMember).where(
                TeamGroupMember.group_id == group_id,
                TeamGroupMember.athlete_id == athlete_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="成员不存在")

        await db.delete(member)
        await db.commit()
        logger.info(f"Removed athlete {athlete_id} from group {group_id}")
        return {"status": "removed", "group_id": str(group_id), "athlete_id": str(athlete_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to remove member from group {group_id}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)[:200]}")


@router.get("/{group_id}/heatmap", response_model=TeamHeatmapResponse)
async def get_group_heatmap(group_id: UUID, db: AsyncSession = Depends(get_db)):
    group = await db.get(TeamGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    member_result = await db.execute(
        select(TeamGroupMember).where(TeamGroupMember.group_id == group_id)
    )
    members = member_result.scalars().all()

    if not members:
        return TeamHeatmapResponse(
            group_name=group.name,
            entries=[],
            avg_acwr=0,
            at_risk_pct=0,
        )

    entries = []
    acwr_values = []
    at_risk_count = 0

    for member in members:
        athlete = await db.get(Athlete, member.athlete_id)
        if not athlete:
            continue

        # 获取最新计算指标
        metric_result = await db.execute(
            select(ComputedMetric)
            .where(ComputedMetric.athlete_id == member.athlete_id)
            .order_by(ComputedMetric.calc_date.desc())
            .limit(1)
        )
        latest_metric = metric_result.scalar_one_or_none()

        acwr_val = latest_metric.acwr if latest_metric else 0
        rssi_val = latest_metric.rssi_score if latest_metric else 0
        rssi_level = latest_metric.rssi_risk_level if latest_metric else "正常"

        # ACWR 颜色
        if acwr_val > 1.5:
            acwr_color = "red"
        elif acwr_val > 1.3:
            acwr_color = "yellow"
        else:
            acwr_color = "green"

        if acwr_val > 0:
            acwr_values.append(acwr_val)

        if acwr_val > 1.3 or rssi_level != "正常":
            at_risk_count += 1

        # 活跃伤病例数
        injury_result = await db.execute(
            select(func.count(InjuryRecord.id)).where(
                InjuryRecord.athlete_id == member.athlete_id,
                InjuryRecord.status.in_(["活跃", "康复中"]),
            )
        )
        active_injuries = injury_result.scalar() or 0

        # 最近训练负荷
        seven_days_ago = date.today() - timedelta(days=7)
        load_result = await db.execute(
            select(func.sum(ComputedMetric.acute_load_7d))
            .where(
                ComputedMetric.athlete_id == member.athlete_id,
                ComputedMetric.calc_date >= seven_days_ago,
            )
        )
        recent_load = load_result.scalar()

        entries.append(TeamHeatmapEntry(
            athlete_name=athlete.name,
            acwr=round(acwr_val, 3),
            acwr_color=acwr_color,
            rssi_score=round(rssi_val, 2),
            rssi_level=rssi_level,
            recent_load=round(recent_load, 1) if recent_load else None,
            perf_trend="稳定",
            active_injuries=active_injuries,
        ))

    avg_acwr = round(sum(acwr_values) / len(acwr_values), 3) if acwr_values else 0
    at_risk_pct = round((at_risk_count / len(entries)) * 100, 1) if entries else 0

    return TeamHeatmapResponse(
        group_name=group.name,
        entries=entries,
        avg_acwr=avg_acwr,
        at_risk_pct=at_risk_pct,
    )


async def _load_group_with_members(group_id: UUID, db: AsyncSession):
    group = await db.get(TeamGroup, group_id)
    if not group:
        return None

    member_result = await db.execute(
        select(TeamGroupMember).where(TeamGroupMember.group_id == group_id)
    )
    members = member_result.scalars().all()

    member_responses = []
    for m in members:
        athlete = await db.get(Athlete, m.athlete_id)
        member_responses.append(TeamGroupMemberResponse(
            id=m.id,
            athlete_id=m.athlete_id,
            athlete_name=athlete.name if athlete else None,
        ))

    return TeamGroupResponse(
        id=group.id,
        name=group.name,
        coach_id=group.coach_id,
        created_at=group.created_at,
        members=member_responses,
    )
