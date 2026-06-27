from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database import get_session
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/v1/stats", tags=["统计"])


@router.get("/authors")
def author_ranking(
    limit: int = 10,
    days: int = None,
    session: Session = Depends(get_session)
):
    """作者排行（按总浏览量）"""
    service = StatsService(session)
    return {"items": service.get_author_ranking(limit=limit, days=days)}


@router.get("/documents/{document_id}/heat")
def document_heat(
    document_id: int,
    session: Session = Depends(get_session)
):
    """单文档热度"""
    service = StatsService(session)
    return service.get_document_heat(document_id)


@router.get("/categories")
def category_stats(
    session: Session = Depends(get_session)
):
    """分类统计"""
    service = StatsService(session)
    return {"items": service.get_category_stats()}
