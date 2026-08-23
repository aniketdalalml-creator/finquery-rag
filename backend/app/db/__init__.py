"""Database package: base, session and ORM model imports."""

from app.db.base import Base  # noqa: F401

# Import models so Base.metadata is fully populated (needed by Alembic).
from app.models import company, document, metric, table  # noqa: F401
