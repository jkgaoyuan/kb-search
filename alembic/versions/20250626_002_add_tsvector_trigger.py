"""Add tsvector trigger

Revision ID: 002
Revises: 001
Create Date: 2025-06-26 00:01:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create function for auto-updating search_vector (using 'simple' config instead of 'zh_cn')
    op.execute("""
        CREATE OR REPLACE FUNCTION documents_search_vector_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('simple', coalesce(NEW.title, '') || ' ' || coalesce(NEW.content, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        DROP TRIGGER IF EXISTS documents_search_vector_trigger ON documents;
        CREATE TRIGGER documents_search_vector_trigger
        BEFORE INSERT OR UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION documents_search_vector_update();
    """)

    # Initialize existing rows
    op.execute("""
        UPDATE documents SET search_vector = to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, ''));
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS documents_search_vector_trigger ON documents;")
    op.execute("DROP FUNCTION IF EXISTS documents_search_vector_update();")
