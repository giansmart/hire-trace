"""rename raw_documents to raw_posts, jobs to job_posts, add application_url

Revision ID: cfbc139ebd3f
Revises: a60ec8377015
Create Date: 2026-09-11 01:22:11.325960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfbc139ebd3f'
down_revision: Union[str, Sequence[str], None] = 'a60ec8377015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('raw_documents', 'raw_posts')
    op.rename_table('jobs', 'job_posts')
    op.alter_column('job_posts', 'raw_document_id', new_column_name='raw_post_id')
    op.add_column('job_posts', sa.Column('application_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('job_posts', 'application_url')
    op.alter_column('job_posts', 'raw_post_id', new_column_name='raw_document_id')
    op.rename_table('job_posts', 'jobs')
    op.rename_table('raw_posts', 'raw_documents')
