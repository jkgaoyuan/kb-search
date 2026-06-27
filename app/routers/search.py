from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.database import get_session
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["搜索"])


@router.get("")
def search(
    q: str = Query(..., description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID过滤"),
    sort: str = Query("relevance", description="排序方式: relevance/updated_at/view_count"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """全文搜索"""
    service = SearchService(session)
    results, total = service.search(
        query=q,
        category_id=category_id,
        sort_by=sort,
        page=page,
        page_size=page_size
    )

    return {
        "query": q,
        "results": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "correction": service.correct_query(q) if q else None
    }


@router.get("/suggest")
def suggest(
    q: str = Query(..., min_length=2, description="搜索前缀"),
    limit: int = Query(10, ge=1, le=20),
    session: Session = Depends(get_session)
):
    """搜索建议/自动补全"""
    service = SearchService(session)
    suggestions = service.suggest(q, limit)

    return {
        "query": q,
        "suggestions": suggestions
    }


@router.get("/hot")
def hot_searches(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    session: Session = Depends(get_session)
):
    """热门搜索排行"""
    service = SearchService(session)
    hot = service.get_hot_searches(limit, hours)

    return {
        "period_hours": hours,
        "searches": hot
    }


@router.get("/correct")
def correct_query(
    q: str = Query(..., description="待纠错的查询"),
    session: Session = Depends(get_session)
):
    """搜索纠错"""
    service = SearchService(session)
    correction = service.correct_query(q)

    return correction
