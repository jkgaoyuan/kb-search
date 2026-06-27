from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class SearchLog(SQLModel, table=True):
    __tablename__ = "search_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    query: str = Field(index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    result_count: int = Field(default=0)
    ip_address: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
