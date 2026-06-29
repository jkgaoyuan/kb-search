from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from app.database import get_session
from app.models.document import Document
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/tags", tags=["标签"])


@router.get("")
def list_tags(
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """标签云：统计所有标签出现频率"""
    # 获取所有非空标签
    docs = session.exec(
        select(Document.tags).where(Document.tags.isnot(None))
    ).all()

    tag_counts = {}
    for tag_list in docs:
        if tag_list:
            for tag in tag_list:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # 按频率排序
    sorted_tags = sorted(
        [{"name": k, "count": v} for k, v in tag_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:limit]

    return {"items": sorted_tags, "total": len(sorted_tags)}


@router.get("/documents")
def search_by_tag(
    tag: str = Query(..., description="标签"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """按标签搜索文档"""
    offset = (page - 1) * page_size

    stmt = select(Document).where(
        Document.tags.contains([tag]),
        Document.status == "published"
    ).order_by(Document.updated_at.desc()).offset(offset).limit(page_size)

    docs = session.exec(stmt).all()

    # 总数
    count_stmt = select(func.count(Document.id)).where(
        Document.tags.contains([tag]),
        Document.status == "published"
    )
    total = session.exec(count_stmt).one()

    return {
        "items": [
            {
                "id": d.id,
                "title": d.title,
                "tags": d.tags,
                "view_count": d.view_count,
                "updated_at": d.updated_at.isoformat(),
            }
            for d in docs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/documents/{document_id}")
def add_tags(
    document_id: int,
    tags: list[str],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """为文档添加标签（会去重）"""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权修改此文档")

    existing = set(doc.tags or [])
    existing.update(tags)
    doc.tags = list(existing)

    session.add(doc)
    session.commit()
    session.refresh(doc)

    return {"id": doc.id, "tags": doc.tags, "message": "标签添加成功"}


@router.delete("/documents/{document_id}")
def remove_tags(
    document_id: int,
    tags: list[str],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """移除文档标签"""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权修改此文档")

    existing = set(doc.tags or [])
    for tag in tags:
        existing.discard(tag)
    doc.tags = list(existing)

    session.add(doc)
    session.commit()
    session.refresh(doc)

    return {"id": doc.id, "tags": doc.tags, "message": "标签移除成功"}
