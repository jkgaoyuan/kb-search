from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models.category import Category

router = APIRouter(prefix="/api/v1/categories", tags=["分类"])


@router.get("")
def list_categories(
    tree: bool = True,
    session: Session = Depends(get_session)
):
    """分类列表"""
    if tree:
        # 获取所有分类，前端构建树
        stmt = select(Category).order_by(Category.path, Category.sort_order)
        categories = session.exec(stmt).all()

        return {
            "items": [
                {
                    "id": c.id,
                    "name": c.name,
                    "parent_id": c.parent_id,
                    "path": c.path,
                    "sort_order": c.sort_order,
                }
                for c in categories
            ]
        }
    else:
        # 扁平列表
        stmt = select(Category).order_by(Category.sort_order)
        categories = session.exec(stmt).all()
        return {"items": [{"id": c.id, "name": c.name, "parent_id": c.parent_id} for c in categories]}


@router.get("/{category_id}/breadcrumb")
def get_breadcrumb(
    category_id: int,
    session: Session = Depends(get_session)
):
    """面包屑导航"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 根据path解析层级
    path_ids = [int(p) for p in category.path.split(".") if p]

    breadcrumbs = []
    for pid in path_ids:
        cat = session.get(Category, pid)
        if cat:
            breadcrumbs.append({
                "id": cat.id,
                "name": cat.name
            })

    return {
        "category_id": category_id,
        "breadcrumbs": breadcrumbs
    }


@router.post("")
def create_category(
    name: str,
    parent_id: Optional[int] = None,
    sort_order: int = 0,
    session: Session = Depends(get_session)
):
    """创建分类"""
    # 构建path
    if parent_id:
        parent = session.get(Category, parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="父分类不存在")
        path = f"{parent.path}.{parent_id}" if parent.path else str(parent_id)
    else:
        path = ""

    category = Category(
        name=name,
        parent_id=parent_id,
        path=path,
        sort_order=sort_order
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    return {"id": category.id, "name": category.name, "path": category.path}


@router.put("/{category_id}")
def update_category(
    category_id: int,
    name: str = None,
    sort_order: int = None,
    session: Session = Depends(get_session)
):
    """更新分类"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    if name:
        category.name = name
    if sort_order is not None:
        category.sort_order = sort_order

    session.add(category)
    session.commit()
    session.refresh(category)

    return {"id": category.id, "name": category.name, "path": category.path}


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    session: Session = Depends(get_session)
):
    """删除分类（仅限无子分类和无文档）"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查是否有子分类
    children = session.exec(select(Category).where(Category.parent_id == category_id)).all()
    if children:
        raise HTTPException(status_code=400, detail="该分类下有子分类，无法删除")

    # 检查是否有关联文档
    from app.models.document import Document
    docs = session.exec(select(Document).where(Document.category_id == category_id).limit(1)).first()
    if docs:
        raise HTTPException(status_code=400, detail="该分类下有关联文档，无法删除")

    session.delete(category)
    session.commit()

    return {"id": category_id, "message": "分类已删除"}
