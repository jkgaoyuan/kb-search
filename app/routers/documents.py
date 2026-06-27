import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlmodel import Session, select, func
from app.database import get_session
from app.models.document import Document
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.document_parser import parser
from app.tasks.document_tasks import parse_document_task
from app.config import get_settings

router = APIRouter(prefix="/api/v1/documents", tags=["文档"])
settings = get_settings()


@router.post("")
def upload_document(
    title: str = Form(...),
    category_id: int = Form(...),
    tags: str = Form(""),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """上传文档"""
    # 检测文件类型
    try:
        file_type = parser.detect_file_type(file.filename, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 检查文件大小
    file.file.seek(0, 2)  # 移动到末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 回到开头

    if file_size > settings.max_upload_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 {settings.max_upload_size / 1024 / 1024}MB")

    # 保存原始文件
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(settings.upload_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # 创建文档记录
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    doc = Document(
        title=title,
        category_id=category_id,
        author_id=current_user.id,
        tags=tag_list,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path,
        parse_status="pending"
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    # 发送异步解析任务
    task = parse_document_task.delay(doc.id, file_path, file_type)

    return {
        "id": doc.id,
        "title": doc.title,
        "task_id": task.id,
        "parse_status": doc.parse_status,
        "message": "文档已上传，正在解析中"
    }


@router.get("")
def list_documents(
    category_id: Optional[int] = Query(None),
    status: str = Query("published"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """文档列表"""
    stmt = select(Document).where(Document.status == status)

    if category_id:
        stmt = stmt.where(Document.category_id == category_id)

    # 总数（使用 COUNT 标量子查询，避免加载所有行到内存）
    count_stmt = select(func.count(Document.id)).where(Document.status == status)
    if category_id:
        count_stmt = count_stmt.where(Document.category_id == category_id)
    total = session.exec(count_stmt).one()

    # 分页
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Document.updated_at.desc()).offset(offset).limit(page_size)
    docs = session.exec(stmt).all()

    return {
        "items": [
            {
                "id": d.id,
                "title": d.title,
                "category_id": d.category_id,
                "author_id": d.author_id,
                "tags": d.tags,
                "status": d.status,
                "view_count": d.view_count,
                "parse_status": d.parse_status,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat(),
            }
            for d in docs
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{document_id}")
def get_document(
    document_id: int,
    session: Session = Depends(get_session)
):
    """文档详情"""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 增加浏览量（原子 UPDATE，避免并发丢失更新）
    from sqlalchemy import update
    session.exec(
        update(Document)
        .where(Document.id == document_id)
        .values(view_count=Document.view_count + 1)
    )
    session.commit()

    # 重新获取文档以返回最新数据
    session.refresh(doc)

    return {
        "id": doc.id,
        "title": doc.title,
        "content_html": doc.content_html,
        "content": doc.content,
        "category_id": doc.category_id,
        "author_id": doc.author_id,
        "tags": doc.tags,
        "status": doc.status,
        "view_count": doc.view_count,
        "file_type": doc.file_type,
        "parse_status": doc.parse_status,
        "parse_error": doc.parse_error,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


@router.get("/{document_id}/status")
def get_document_status(
    document_id: int,
    session: Session = Depends(get_session)
):
    """获取文档解析状态"""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    return {
        "id": doc.id,
        "parse_status": doc.parse_status,
        "parse_error": doc.parse_error,
        "content_length": len(doc.content) if doc.content else 0,
    }


@router.put("/{document_id}")
def update_document(
    document_id: int,
    title: Optional[str] = None,
    category_id: Optional[int] = None,
    tags: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """更新文档"""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 权限检查：只有作者或管理员可以修改
    if doc.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权修改此文档")

    if title:
        doc.title = title
    if category_id:
        doc.category_id = category_id
    if tags is not None:
        doc.tags = [t.strip() for t in tags.split(",") if t.strip()]
    if status:
        doc.status = status

    session.add(doc)
    session.commit()
    session.refresh(doc)

    # 更新全文检索向量
    from app.tasks.document_tasks import update_search_vector
    update_search_vector.delay(doc.id)

    return {"id": doc.id, "message": "更新成功"}


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """删除文档"""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除此文档")

    # 软删除：标记为archived
    doc.status = "archived"
    session.add(doc)
    session.commit()

    return {"id": doc.id, "message": "文档已归档"}
