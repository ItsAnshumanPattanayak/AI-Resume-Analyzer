"""add history user created index

Revision ID: 8c21f4d7a9b0
Revises: 4bdfb1a4b3a2
"""

from typing import Sequence, Union

from alembic import op


revision: str = "8c21f4d7a9b0"
down_revision: Union[str, Sequence[str], None] = "4bdfb1a4b3a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_analysis_records_user_created_at",
        "analysis_records",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analysis_records_user_created_at",
        table_name="analysis_records",
    )
