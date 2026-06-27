"""Init database

Revision ID: 001
Revises:
Create Date: 2025-06-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('auth_type', sa.String(), nullable=False, server_default='local'),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.CheckConstraint("auth_type IN ('local', 'ldap', 'oauth2')", name='ck_users_auth_type')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_external_id', 'users', ['external_id'])

    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(), nullable=False, server_default=''),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL')
    )
    op.create_index('ix_categories_name', 'categories', ['name'])
    op.create_index('ix_categories_parent_id', 'categories', ['parent_id'])
    op.create_index('ix_categories_path', 'categories', ['path'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('content_html', sa.Text(), nullable=False, server_default=''),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(), nullable=False, server_default='published'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('file_type', sa.String(), nullable=False, server_default='markdown'),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('parse_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('parse_error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='RESTRICT'),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name='ck_documents_status'),
        sa.CheckConstraint("parse_status IN ('pending', 'processing', 'completed', 'failed')", name='ck_documents_parse_status'),
        sa.CheckConstraint("file_type IN ('markdown', 'html', 'docx')", name='ck_documents_file_type')
    )
    op.create_index('ix_documents_title', 'documents', ['title'])
    op.create_index('ix_documents_category_id', 'documents', ['category_id'])
    op.create_index('ix_documents_author_id', 'documents', ['author_id'])

    # Create search_logs table
    op.create_table(
        'search_logs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_search_logs_query', 'search_logs', ['query'])
    op.create_index('ix_search_logs_user_id', 'search_logs', ['user_id'])
    op.create_index('ix_search_logs_created_at', 'search_logs', ['created_at'])

    # Create additional indexes for documents (remove duplicate category_id/author_id indexes)
    op.create_index('idx_documents_status', 'documents', ['status'])
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])

    # Create GIN index for full-text search
    op.execute("CREATE INDEX idx_documents_search_vector ON documents USING GIN(search_vector)")


def downgrade() -> None:
    op.drop_table('search_logs')
    op.drop_table('documents')
    op.drop_table('categories')
    op.drop_table('users')
