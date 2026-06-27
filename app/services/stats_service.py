from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlmodel import Session, select, func
from app.models.document import Document
from app.models.user import User


class StatsService:
    """统计服务"""

    def __init__(self, session: Session):
        self.session = session

    def get_author_ranking(self, limit: int = 10, days: Optional[int] = None) -> List[dict]:
        """作者排行"""
        stmt = select(
            User.id,
            User.username,
            func.count(Document.id).label('doc_count'),
            func.coalesce(func.sum(Document.view_count), 0).label('total_views')
        ).join(Document, User.id == Document.author_id).where(
            Document.status == "published"
        )

        if days:
            since = datetime.now(timezone.utc) - timedelta(days=days)
            stmt = stmt.where(Document.created_at >= since)

        stmt = stmt.group_by(User.id, User.username).order_by(
            func.sum(Document.view_count).desc()
        ).limit(limit)

        results = self.session.exec(stmt).all()
        return [
            {
                "user_id": r[0],
                "username": r[1],
                "document_count": r[2],
                "total_views": r[3]
            }
            for r in results
        ]

    def get_document_heat(self, document_id: int) -> dict:
        """单文档热度"""
        doc = self.session.get(Document, document_id)
        if not doc:
            return {}

        return {
            "document_id": doc.id,
            "title": doc.title,
            "view_count": doc.view_count,
            "created_at": doc.created_at.isoformat(),
            "days_since_created": (datetime.now(timezone.utc) - doc.created_at).days,
        }

    def get_category_stats(self) -> List[dict]:
        """分类统计"""
        from app.models.category import Category

        stmt = select(
            Category.id,
            Category.name,
            func.count(Document.id).label('doc_count')
        ).outerjoin(Document, Category.id == Document.category_id).where(
            Document.status == "published"
        ).group_by(Category.id, Category.name)

        results = self.session.exec(stmt).all()
        return [
            {
                "category_id": r[0],
                "name": r[1],
                "document_count": r[2]
            }
            for r in results
        ]
