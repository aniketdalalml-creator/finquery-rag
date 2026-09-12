"""User model + users-table migration tests.

No password hashing or auth APIs — persistence contract only.
"""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models.user import User

_HASH = "$2b$12$placeholder.hash.not.plaintext"


def test_user_can_be_created(db_session):
    user = User(email="analyst@example.com", hashed_password=_HASH)
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert user.email == "analyst@example.com"
    assert user.hashed_password == _HASH
    assert user.created_at is not None
    assert user.updated_at is not None
    assert "password" not in User.__table__.c
    assert "hashed_password" in User.__table__.c


def test_email_uniqueness_is_enforced(db_session):
    db_session.add(User(email="dup@example.com", hashed_password=_HASH))
    db_session.flush()

    db_session.add(User(email="dup@example.com", hashed_password=_HASH))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_email_uniqueness_is_case_insensitive(db_session):
    db_session.add(User(email="Casey@example.com", hashed_password=_HASH))
    db_session.flush()

    db_session.add(User(email="casey@example.com", hashed_password=_HASH))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_is_active_defaults_to_true(db_session):
    user = User(email="active@example.com", hashed_password=_HASH)
    db_session.add(user)
    db_session.flush()

    db_session.expire(user)
    loaded = db_session.scalar(select(User).where(User.email == "active@example.com"))
    assert loaded is not None
    assert loaded.is_active is True


def test_email_is_required(db_session):
    db_session.add(User(hashed_password=_HASH))  # type: ignore[call-arg]
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_hashed_password_is_required(db_session):
    db_session.add(User(email="nopw@example.com"))  # type: ignore[call-arg]
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_users_table_exists_after_migration(migrated_engine):
    inspector = inspect(migrated_engine)
    assert "users" in inspector.get_table_names()
    columns = {col["name"] for col in inspector.get_columns("users")}
    assert columns == {
        "id",
        "email",
        "hashed_password",
        "is_active",
        "created_at",
        "updated_at",
    }

    from sqlalchemy import text as sql_text

    with migrated_engine.connect() as conn:
        if migrated_engine.dialect.name == "sqlite":
            rows = conn.execute(
                sql_text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='index' AND tbl_name='users'"
                )
            ).fetchall()
            names = {row[0] for row in rows}
            assert "ix_users_email" in names
            assert "uq_users_email_lower" in names
        else:
            indexes = {idx["name"] for idx in inspector.get_indexes("users")}
            assert "ix_users_email" in indexes
            assert "uq_users_email_lower" in indexes
