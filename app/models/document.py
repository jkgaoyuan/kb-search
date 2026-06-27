from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy.dialects.postgresql import TSVECTOR


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str = Field(default="")  # 纯文本，用于全文检索
    content_html: str = Field(default="")  # 渲染后的HTML

    category_id: int = Field(foreign_key="categories.id", index=True)
    author_id: int = Field(foreign_key="users.id", index=True)

    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    status: str = Field(default="published")  # draft | published | archived

    view_count: int = Field(default=0)

    # 全文检索向量
    search_vector: Optional[str] = Field(default=None, sa_column=Column(TSVECTOR))

    # 文件信息
    file_type: str = Field(default="markdown")  # markdown | html | docx
    file_size: int = Field(default=0)  # 字节
    file_path: Optional[str] = Field(default=None)  # 原始文件存储路径

    # 解析状态
    parse_status: str = Field(default="pending")  # pending | processing | completed | failed
    parse_error: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
