import os
from celery import Celery
from sqlmodel import Session
from app.config import get_settings
from app.database import engine
from app.models.document import Document
from app.services.document_parser import parser

settings = get_settings()

# 初始化Celery
celery_app = Celery(
    "kb_search",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # 每小时清理一次超过 30 天的搜索日志
        "clean-old-search-logs": {
            "task": "app.tasks.document_tasks.clean_old_search_logs",
            "schedule": 3600.0,  # 1小时
        },
        # 每天凌晨清理孤儿上传文件
        "clean-old-uploads": {
            "task": "app.tasks.document_tasks.clean_old_uploads",
            "schedule": 86400.0,  # 24小时
        },
    },
)


@celery_app.task(bind=True, max_retries=3)
def parse_document_task(self, document_id: int, file_path: str, file_type: str):
    """异步解析文档任务"""
    with Session(engine) as session:
        try:
            doc = session.get(Document, document_id)
            if not doc:
                return {"status": "failed", "error": "Document not found"}

            doc.parse_status = "processing"
            session.add(doc)
            session.commit()

            # 解析文档
            plain_text, html_content = parser.parse(file_path, file_type)

            # 更新文档
            doc.content = plain_text
            doc.content_html = html_content
            doc.parse_status = "completed"
            doc.parse_error = None

            session.add(doc)
            session.commit()

            # 触发全文检索向量更新
            update_search_vector.delay(document_id)

            # 解析完成后删除原始文件
            if os.path.exists(file_path):
                os.remove(file_path)

            return {
                "status": "completed",
                "document_id": document_id,
                "content_length": len(plain_text),
            }

        except Exception as exc:
            doc = session.get(Document, document_id)
            if doc:
                doc.parse_status = "failed"
                doc.parse_error = str(exc)
                session.add(doc)
                session.commit()

            raise self.retry(exc=exc, countdown=60)


@celery_app.task
def update_search_vector(document_id: int):
    """更新文档的全文检索向量"""
    from sqlalchemy import text

    with Session(engine) as session:
        sql = text("UPDATE documents SET search_vector = to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, '')) WHERE id = :doc_id")
        session.exec(sql, {"doc_id": document_id})
        session.commit()


@celery_app.task
def clean_old_uploads():
    """清理未关联的孤儿文件"""
    import glob
    from datetime import datetime, timezone, timedelta
    from sqlmodel import select

    upload_dir = settings.upload_dir
    if not os.path.exists(upload_dir):
        return

    with Session(engine) as session:
        stmt = select(Document.file_path).where(Document.file_path.isnot(None))
        valid_paths = set(session.exec(stmt).all())

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    for filepath in glob.glob(os.path.join(upload_dir, "*")):
        if filepath not in valid_paths:
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
                if mtime < cutoff:
                    os.remove(filepath)
            except OSError:
                pass


@celery_app.task
def clean_old_search_logs(retention_days: int = 30):
    """清理超过 retention_days 天的搜索日志，防止表无限膨胀"""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import delete
    from app.models.search_log import SearchLog

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    with Session(engine) as session:
        stmt = delete(SearchLog).where(SearchLog.created_at < cutoff)
        result = session.exec(stmt)
        session.commit()
        deleted_count = result.rowcount if hasattr(result, 'rowcount') else 0

    return {
        "status": "completed",
        "deleted_count": deleted_count,
        "cutoff": cutoff.isoformat(),
    }
