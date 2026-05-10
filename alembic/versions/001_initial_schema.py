"""Initial schema from ORM metadata (idempotent create_all pattern)."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import MetaData

from app.models.db_models import Base

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    md: MetaData = Base.metadata
    md.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
