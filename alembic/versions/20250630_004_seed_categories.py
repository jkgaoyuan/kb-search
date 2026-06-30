"""Seed initial categories

Revision ID: 004
Revises: 003
Create Date: 2025-06-30 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert root categories
    op.execute("""
        INSERT INTO categories (name, parent_id, path, sort_order) VALUES
        ('技术', NULL, '', 1),
        ('产品', NULL, '', 2),
        ('运营', NULL, '', 3);
    """)

    # Insert sub-categories under '技术' (id=1)
    op.execute("""
        INSERT INTO categories (name, parent_id, path, sort_order) VALUES
        ('后端', 1, '1', 1),
        ('前端', 1, '1', 2);
    """)


def downgrade() -> None:
    # Remove seeded categories by name (safe even if children were added later)
    op.execute("DELETE FROM categories WHERE name IN ('技术', '产品', '运营', '后端', '前端');")
