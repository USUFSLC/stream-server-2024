"""initial migration

Revision ID: aab5d60ead67
Revises: 
Create Date: 2025-09-03 23:56:48.980450

"""
from typing import Optional
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aab5d60ead67'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("starts_at", sa.DateTime, nullable=False),
        sa.Column("ends_at", sa.DateTime, nullable=False),
        sa.Column("location", sa.String(64)),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.String),
        if_not_exists=True
    )

    op.create_table(
        "stream",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime),
        sa.Column("ended_at", sa.DateTime),
        sa.Column("processed_at", sa.DateTime),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("presenter", sa.UUID),
        sa.Column("nonmember_presenter", sa.String(20)),
        sa.Column("description", sa.String),
        sa.Column("token", sa.String, nullable=False),
        sa.Column("event_id", sa.UUID, sa.ForeignKey("event.id", ondelete="SET NULL")),
        if_not_exists=True
    )

def downgrade():
    op.drop_table("event")
    op.drop_table("stream")
