"""Add chat_document_chunks table for per-chat uploaded-document RAG (pgvector)

Revision ID: c1a2b3d4e5f6
Revises: b7e1f2a3c4d5
Create Date: 2026-06-30 12:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "b7e1f2a3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "chat_document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chats.id"],
            name=op.f("fk_chat_document_chunks_chat_id_chats"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_document_chunks")),
    )
    op.create_index(
        op.f("ix_chat_document_chunks_id"),
        "chat_document_chunks",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_document_chunks_chat_id"),
        "chat_document_chunks",
        ["chat_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_chat_document_chunks_chat_id"), table_name="chat_document_chunks"
    )
    op.drop_index(op.f("ix_chat_document_chunks_id"), table_name="chat_document_chunks")
    op.drop_table("chat_document_chunks")
