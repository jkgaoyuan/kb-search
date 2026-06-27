"""Fix indexes and constraints

Revision ID: 003
Revises: 002
Create Date: 2025-06-26 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================
    # 1. Documents table: add missing indexes
    # ==========================================

    # GIN index for JSONB tags (supports @> containment operator)
    op.execute("CREATE INDEX idx_documents_tags_gin ON documents USING GIN(tags)")

    # Index for sorting by view_count (hot documents)
    op.create_index('idx_documents_view_count', 'documents', ['view_count'])

    # Index for sorting by updated_at (recent documents)
    op.create_index('idx_documents_updated_at', 'documents', ['updated_at'])

    # Composite index for list queries: filter by status + sort by updated_at
    op.create_index('idx_documents_status_updated_at', 'documents', ['status', sa.text('updated_at DESC')])

    # Composite index for category list queries: filter by category_id + status + sort by updated_at
    op.create_index('idx_documents_category_status_updated', 'documents', ['category_id', 'status', sa.text('updated_at DESC')])

    # Composite index for category list queries: filter by category_id + status + sort by view_count
    op.create_index('idx_documents_category_status_views', 'documents', ['category_id', 'status', sa.text('view_count DESC')])

    # ==========================================
    # 2. Search logs: add composite index for hot searches
    # ==========================================

    # Composite index for time-range + group by query (hot searches)
    op.create_index('idx_search_logs_created_at_query', 'search_logs', ['created_at', 'query'])

    # Index for ip_address analysis (abuse detection, geo stats)
    op.create_index('idx_search_logs_ip_address', 'search_logs', ['ip_address'])

    # ==========================================
    # 3. Categories: path prefix search index (text_pattern_ops)
    # ==========================================

    op.execute("CREATE INDEX idx_categories_path_pattern ON categories USING btree(path text_pattern_ops)")

    # ==========================================
    # 4. Auto-update updated_at trigger for all tables
    # ==========================================

    op.execute("""
        CREATE OR REPLACE FUNCTION auto_update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply to users table
    op.execute("""
        DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION auto_update_updated_at();
    """)

    # Apply to documents table
    op.execute("""
        DROP TRIGGER IF EXISTS trg_documents_updated_at ON documents;
        CREATE TRIGGER trg_documents_updated_at
        BEFORE UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION auto_update_updated_at();
    """)

    # Note: categories and search_logs don't have updated_at in the current schema,
    # so we skip them. If added later, apply the same trigger.


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_documents_updated_at ON documents;")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users;")
    op.execute("DROP FUNCTION IF EXISTS auto_update_updated_at();")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_categories_path_pattern")
    op.drop_index('idx_search_logs_ip_address', table_name='search_logs')
    op.drop_index('idx_search_logs_created_at_query', table_name='search_logs')
    op.drop_index('idx_documents_category_status_views', table_name='documents')
    op.drop_index('idx_documents_category_status_updated', table_name='documents')
    op.drop_index('idx_documents_status_updated_at', table_name='documents')
    op.drop_index('idx_documents_updated_at', table_name='documents')
    op.drop_index('idx_documents_view_count', table_name='documents')
    op.execute("DROP INDEX IF EXISTS idx_documents_tags_gin")
