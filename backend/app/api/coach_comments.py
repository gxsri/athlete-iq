"""
AthleteIQ - 教练反馈/评论 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import CoachComment, Athlete
from app.schemas.schemas import (
    CoachCommentCreate, CoachCommentUpdate, CoachCommentResponse,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime

router = APIRouter(prefix="/api/coach", tags=["教练反馈"])


@router.post("/comments", response_model=CoachCommentResponse, status_code=201)
async def add_comment(data: CoachCommentCreate, db: AsyncSession = Depends(get_db)):
    try:
        athlete = await db.get(Athlete, data.athlete_id)
        if not athlete:
            raise HTTPException(status_code=404, detail="运动员不存在")

        comment = CoachComment(**data.model_dump())
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        logger.info(f"Created comment {comment.id} for athlete {data.athlete_id}")
        return comment
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating comment: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create comment")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/comments", response_model=List[CoachCommentResponse])
async def list_comments(
    athlete_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(CoachComment)
    if athlete_id:
        query = query.where(CoachComment.athlete_id == athlete_id)
    if start_date:
        query = query.where(CoachComment.created_at >= start_date)
    if end_date:
        query = query.where(CoachComment.created_at <= end_date)

    query = query.order_by(CoachComment.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/comments/{comment_id}", response_model=CoachCommentResponse)
async def get_comment(comment_id: UUID, db: AsyncSession = Depends(get_db)):
    comment = await db.get(CoachComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    return comment


@router.put("/comments/{comment_id}", response_model=CoachCommentResponse)
async def update_comment(
    comment_id: UUID,
    data: CoachCommentUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        comment = await db.get(CoachComment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(comment, key, value)

        await db.commit()
        await db.refresh(comment)
        logger.info(f"Updated comment {comment_id}")
        return comment
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating comment {comment_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update comment {comment_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.post("/comments/{comment_id}/mark-read")
async def mark_comment_read(comment_id: UUID, db: AsyncSession = Depends(get_db)):
    """运动员查看评论后标记已读"""
    comment = await db.get(CoachComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    comment.is_read = True
    comment.read_by_athlete = True
    if not comment.read_at:
        comment.read_at = datetime.utcnow()
    await db.commit()
    return {"status": "read", "comment_id": str(comment_id)}


@router.get("/comments/unread-count/{athlete_id}")
async def unread_comment_count(athlete_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取运动员未读评论数"""
    result = await db.execute(
        select(func.count(CoachComment.id)).where(
            CoachComment.athlete_id == athlete_id,
            CoachComment.read_by_athlete == False,
        )
    )
    count = result.scalar()
    return {"athlete_id": str(athlete_id), "unread_count": count}


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        comment = await db.get(CoachComment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        await db.delete(comment)
        await db.commit()
        logger.info(f"Deleted comment {comment_id}")
        return {"status": "deleted", "comment_id": str(comment_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete comment {comment_id}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)[:200]}")
