"""
AthleteIQ - 收藏与最近使用 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db, logger
from app.models.athlete import ExerciseFavorite, TemplateFavorite, RecentlyUsed, ExerciseLibrary, PeriodizationTemplate

router = APIRouter(prefix="/api", tags=["收藏与最近使用"])


class FavoriteCreate(BaseModel):
    item_type: str  # "exercise" or "template"
    item_id: UUID


# POST /api/favorites/ — Add favorite
@router.post("/favorites/", status_code=201)
async def add_favorite(data: FavoriteCreate, db: AsyncSession = Depends(get_db)):
    try:
        if data.item_type == "exercise":
            fav = ExerciseFavorite(user_id="default", exercise_id=str(data.item_id))
        elif data.item_type == "template":
            fav = TemplateFavorite(user_id="default", template_id=str(data.item_id))
        else:
            raise HTTPException(status_code=400, detail="item_type 必须为 exercise 或 template")
        db.add(fav)
        await db.commit()
        return {"status": "favorited", "item_type": data.item_type, "item_id": str(data.item_id)}
    except Exception as e:
        logger.warning(f"Failed to add favorite: {e}")
        raise HTTPException(status_code=409, detail="已收藏或添加失败")


# DELETE /api/favorites/{item_type}/{item_id} — Remove favorite
@router.delete("/favorites/{item_type}/{item_id}")
async def remove_favorite(item_type: str, item_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        if item_type == "exercise":
            stmt = delete(ExerciseFavorite).where(
                ExerciseFavorite.user_id == "default",
                ExerciseFavorite.exercise_id == str(item_id),
            )
        elif item_type == "template":
            stmt = delete(TemplateFavorite).where(
                TemplateFavorite.user_id == "default",
                TemplateFavorite.template_id == str(item_id),
            )
        else:
            raise HTTPException(status_code=400, detail="item_type 必须为 exercise 或 template")
        await db.execute(stmt)
        await db.commit()
        return {"status": "unfavorited"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


# GET /api/favorites?item_type=exercise — List favorites
@router.get("/favorites")
async def list_favorites(
    item_type: str = Query("exercise", description="exercise 或 template"),
    db: AsyncSession = Depends(get_db),
):
    if item_type == "exercise":
        result = await db.execute(
            select(ExerciseFavorite, ExerciseLibrary.name)
            .join(ExerciseLibrary, ExerciseFavorite.exercise_id == ExerciseLibrary.id)
            .where(ExerciseFavorite.user_id == "default")
            .order_by(ExerciseFavorite.created_at.desc())
        )
        rows = result.all()
        return [
            {
                "id": row[0].id,
                "item_type": "exercise",
                "item_id": row[0].exercise_id,
                "item_name": row[1],
                "created_at": str(row[0].created_at),
            }
            for row in rows
        ]
    elif item_type == "template":
        result = await db.execute(
            select(TemplateFavorite, PeriodizationTemplate.name)
            .join(PeriodizationTemplate, TemplateFavorite.template_id == PeriodizationTemplate.id)
            .where(TemplateFavorite.user_id == "default")
            .order_by(TemplateFavorite.created_at.desc())
        )
        rows = result.all()
        return [
            {
                "id": row[0].id,
                "item_type": "template",
                "item_id": row[0].template_id,
                "item_name": row[1],
                "created_at": str(row[0].created_at),
            }
            for row in rows
        ]
    else:
        raise HTTPException(status_code=400, detail="item_type 必须为 exercise 或 template")


# GET /api/recents?item_type=exercise — List recently used
@router.get("/recents")
async def list_recents(
    item_type: str = Query("exercise", description="exercise 或 template"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RecentlyUsed)
        .where(RecentlyUsed.user_id == "default", RecentlyUsed.item_type == item_type)
        .order_by(RecentlyUsed.used_at.desc())
        .limit(10)
    )
    items = result.scalars().all()
    results = []
    for item in items:
        name = item.item_id
        if item_type == "exercise":
            ex_result = await db.execute(
                select(ExerciseLibrary.name).where(ExerciseLibrary.id == item.item_id)
            )
            ex_name = ex_result.scalar_one_or_none()
            if ex_name:
                name = ex_name
        elif item_type == "template":
            t_result = await db.execute(
                select(PeriodizationTemplate.name).where(PeriodizationTemplate.id == item.item_id)
            )
            t_name = t_result.scalar_one_or_none()
            if t_name:
                name = t_name
        results.append({
            "item_type": item_type,
            "item_id": item.item_id,
            "item_name": name,
            "used_at": str(item.used_at),
        })
    return results


# POST /api/recents/ — Record usage
@router.post("/recents/", status_code=201)
async def record_usage(data: FavoriteCreate, db: AsyncSession = Depends(get_db)):
    try:
        rec = RecentlyUsed(user_id="default", item_type=data.item_type, item_id=str(data.item_id))
        db.add(rec)
        # Keep only last 20 per type
        count_result = await db.execute(
            select(RecentlyUsed).where(
                RecentlyUsed.user_id == "default",
                RecentlyUsed.item_type == data.item_type,
            )
        )
        all_items = count_result.scalars().all()
        if len(all_items) > 20:
            # Delete oldest
            oldest = all_items[0]
            await db.delete(oldest)
        await db.commit()
        return {"status": "recorded"}
    except Exception:
        await db.rollback()
        return {"status": "skipped"}
