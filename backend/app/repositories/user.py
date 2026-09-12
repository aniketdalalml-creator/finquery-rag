"""UserRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        return self._scalar(stmt)

    def get_by_id(self, user_id: int) -> User | None:
        from sqlalchemy.orm import Session
        from sqlalchemy.orm import Session
        session: Session = object.__dict__.get("_session")  # placeholder
        # Actually we will receive session from dependency; but for now use session.get
        return self.session.get(User, user_id)  # type: ignore
