"""normalize column types and names

Revision ID: 976401935155
Revises: aab5d60ead67
Create Date: 2025-09-17 14:05:13.343166

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '976401935155'
down_revision = 'aab5d60ead67'
branch_labels = None
depends_on = None


def upgrade():
    # introduce same limit on stream title as event title
    op.alter_column(
        "stream",
        "title",
        type_=sa.String(128),
        postgresql_using="substring(title FROM 1 FOR 128)"
    )

    # this field should always be 32 characters
    op.alter_column(
        "stream",
        "token",
        type_=sa.String(32),
        postgresql_using="substring(token FROM 1 FOR 32)"
    )

    # make the names of columns more predictable
    # i have no idea why i decided to name them so inconsistently
    op.alter_column("event", "created_at", new_column_name="create_time")
    op.alter_column("event", "starts_at", new_column_name="start_time")
    op.alter_column("event", "ends_at", new_column_name="end_time")
    op.alter_column("stream", "created_at", new_column_name="create_time")
    op.alter_column("stream", "started_at", new_column_name="start_time")
    op.alter_column("stream", "ended_at", new_column_name="end_time")
    op.alter_column("stream", "processed_at", new_column_name="process_time")


def downgrade():
    op.alter_column(
        "stream",
        "title",
        type_=sa.String,
    )

    op.alter_column(
        "stream",
        "token",
        type_=sa.String,
    )

    op.alter_column("event", "create_time", new_column_name="created_at")
    op.alter_column("event", "start_time", new_column_name="starts_at")
    op.alter_column("event", "end_time", new_column_name="ends_at")
    op.alter_column("stream", "create_time", new_column_name="created_at")
    op.alter_column("stream", "start_time", new_column_name="started_at")
    op.alter_column("stream", "end_time", new_column_name="ended_at")
    op.alter_column("stream", "process_time", new_column_name="processed_at")
