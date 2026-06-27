from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    path: str = Field(default="", index=True)  # 物化路径，如 "1.2.3"
    sort_order: int = Field(default=0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 关系
    children: List["Category"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    parent: Optional["Category"] = Relationship(back_populates="children")
