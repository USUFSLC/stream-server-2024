"""add resources

Revision ID: 873329794b00
Revises: 976401935155
Create Date: 2025-11-21 07:48:50.675404

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '873329794b00'
down_revision = '976401935155'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resource",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("create_time", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("filesize", sa.Integer, nullable=False),
        sa.Column("content_hash", sa.LargeBinary, unique=True, nullable=False),
        sa.Column("event_id", sa.UUID, sa.ForeignKey("event.id")),
        sa.Column("stream_id", sa.UUID, sa.ForeignKey("stream.id")),
        sa.CheckConstraint("(event_id IS NULL AND stream_id IS NOT NULL) OR (event_id IS NOT NULL AND stream_id IS NULL)", name="stream_or_event_id")
    )


def downgrade():
    op.drop_table("resource")
