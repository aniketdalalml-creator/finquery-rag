"""Generic repository helpers. Data-access logic only — no commits here.

The transaction boundary lives in `app.db.session.get_db`, which commits the
request atomically after all services have run.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def _scalar(self, stmt) -> ModelT | None:
        return self.session.scalars(stmt).first()

    def get(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        self.session.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.session.delete(obj)
        self.session.flush()

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return int(self.session.scalar(stmt))
