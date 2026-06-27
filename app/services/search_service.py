from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select, func, text
from app.models.document import Document
from app.models.search_log import SearchLog
from app.utils.text_utils import generate_summary, highlight_keywords
from app.utils.redis_client import redis_client
from app.services.spell_corrector import SpellCorrector

import re


class SearchService:
    """搜索服务"""

    def __init__(self, session: Session):
        self.session = session
        self.corrector = None  # Lazy init

    def _get_corrector(self) -> SpellCorrector:
        """懒加载搜索纠错器"""
        if self.corrector is None:
            self.corrector = SpellCorrector()
            # 从现有文档标题构建词典
            stmt = select(Document.title).where(Document.status == "published").limit(1000)
            results = self.session.exec(stmt).all()
            for title in results:
                if title:
                    words = re.findall(r'[^\s\p{P}]+', title)
                    self.corrector.add_to_dictionary(words)
            # 从搜索日志构建词典
            log_stmt = select(SearchLog.query).where(
                SearchLog.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
            ).limit(500)
            log_results = self.session.exec(log_stmt).all()
            for query in log_results:
                if query:
                    words = re.findall(r'[^\s\p{P}]+', query)
                    self.corrector.add_to_dictionary(words)
        return self.corrector

    def search(
        self,
        query: str,
        category_id: Optional[int] = None,
        sort_by: str = "relevance",  # relevance | updated_at | view_count
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """
        全文搜索

        Returns:
            (结果列表, 总数量)
        """
        if not query or not query.strip():
            return [], 0

        # 记录搜索日志
        self._log_search(query)

        # 构建查询
        tsquery = func.plainto_tsquery('simple', query)

        # 基础查询
        stmt = select(
            Document,
            func.ts_rank(Document.search_vector, tsquery).label('rank')
        ).where(
            Document.search_vector.op('@@')(tsquery),
            Document.status == "published"
        )

        # 分类过滤
        if category_id:
            stmt = stmt.where(Document.category_id == category_id)

        # 排序
        if sort_by == "relevance":
            stmt = stmt.order_by(text('rank DESC'), Document.updated_at.desc())
        elif sort_by == "updated_at":
            stmt = stmt.order_by(Document.updated_at.desc())
        elif sort_by == "view_count":
            stmt = stmt.order_by(Document.view_count.desc())

        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        results = self.session.exec(stmt).all()

        # 计算总数
        count_stmt = select(func.count(Document.id)).where(
            Document.search_vector.op('@@')(tsquery),
            Document.status == "published"
        )
        if category_id:
            count_stmt = count_stmt.where(Document.category_id == category_id)
        total = self.session.exec(count_stmt).one()

        # 格式化结果
        keywords = self._extract_keywords(query)
        formatted_results = []
        for doc, rank in results:
            formatted_results.append({
                "id": doc.id,
                "title": doc.title,
                "title_highlighted": highlight_keywords(doc.title, keywords),
                "summary": self._generate_search_summary(doc.content, keywords),
                "content_highlighted": highlight_keywords(
                    generate_summary(doc.content, 300),
                    keywords
                ),
                "category_id": doc.category_id,
                "author_id": doc.author_id,
                "tags": doc.tags,
                "view_count": doc.view_count,
                "relevance_score": round(float(rank), 4),
                "updated_at": doc.updated_at.isoformat(),
            })

        return formatted_results, total

    def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """搜索建议 - 基于 Redis 缓存 + 历史搜索前缀匹配"""
        if not prefix or len(prefix) < 2:
            return []

        # 尝试从 Redis 获取缓存建议
        cache_key = f"search:suggest:{prefix.lower()}"
        cached = redis_client.zrange(cache_key, 0, limit - 1)
        if cached:
            return list(cached)

        # 使用 ILIKE 进行前缀匹配
        stmt = select(SearchLog.query).where(
            SearchLog.query.ilike(f"{prefix}%")
        ).group_by(SearchLog.query).order_by(
            func.count(SearchLog.query).desc()
        ).limit(limit)

        results = self.session.exec(stmt).all()
        suggestions = [r for r in results]

        # 写入 Redis 缓存（TTL 10分钟）
        if suggestions:
            pipe = redis_client.pipeline()
            for idx, suggestion in enumerate(suggestions):
                pipe.zadd(cache_key, {suggestion: idx})
            pipe.expire(cache_key, 600)
            pipe.execute()

        return suggestions

    def get_hot_searches(self, limit: int = 10, hours: int = 24) -> List[dict]:
        """获取热门搜索 - 使用 Redis 缓存"""
        cache_key = f"search:hot:{hours}"
        cached = redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = select(
            SearchLog.query,
            func.count(SearchLog.query).label('count')
        ).where(
            SearchLog.created_at >= since
        ).group_by(SearchLog.query).order_by(
            func.count(SearchLog.query).desc()
        ).limit(limit)

        results = self.session.exec(stmt).all()
        hot = [
            {"query": r[0], "count": r[1]}
            for r in results
        ]

        # 写入 Redis 缓存（TTL 1小时）
        if hot:
            import json
            redis_client.setex(cache_key, 3600, json.dumps(hot))

        return hot

    def correct_query(self, query: str) -> dict:
        """搜索纠错"""
        corrector = self._get_corrector()
        return corrector.correct(query)

    def _log_search(self, query: str, user_id: Optional[int] = None, result_count: int = 0):
        """记录搜索日志"""
        log = SearchLog(
            query=query,
            user_id=user_id,
            result_count=result_count
        )
        self.session.add(log)
        self.session.commit()

    def _extract_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词"""
        keywords = re.findall(r'[^\s\p{P}]+', query)
        return [k for k in keywords if len(k) > 1]

    def _generate_search_summary(self, content: str, keywords: List[str]) -> str:
        """生成搜索结果摘要，优先包含关键词的上下文"""
        if not content:
            return ""

        if not keywords:
            return generate_summary(content, 200)

        # 尝试找到包含第一个关键词的位置
        content_lower = content.lower()
        for kw in keywords:
            kw_lower = kw.lower()
            pos = content_lower.find(kw_lower)
            if pos >= 0:
                # 提取关键词前后各100字符
                start = max(0, pos - 100)
                end = min(len(content), pos + len(kw) + 100)
                summary = content[start:end]
                if start > 0:
                    summary = "..." + summary
                if end < len(content):
                    summary = summary + "..."
                return summary

        # 找不到关键词，返回普通摘要
        return generate_summary(content, 200)
