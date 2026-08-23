"""Isolated database fixtures for the finance data-layer tests.

Each test session gets a throwaway SQLite file, migrated to head via Alembic
(same migration path as production), and every test runs inside a transaction
that is rolled back afterwards.
"""

from __future__ import annotations

import os
import sys

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ── legacy RAG fixtures (unchanged) ─────────────────────────────────────────


@pytest.fixture
def sample_documents():
    from langchain_core.documents import Document

    return [
        Document(
            page_content=(
                "Apple Inc. reported total net sales of $394.3 billion in fiscal 2023. "
                "iPhone revenue was $200.6 billion. Services revenue was $85.2 billion. "
                "Research and development expense was $29.9 billion."
            ),
            metadata={"source": "apple_10k_summary.txt", "file_type": "text"},
        ),
        Document(
            page_content=(
                "Risk factors include global supply chain disruption, exposure to the China market, "
                "regulatory pressure across jurisdictions, and intense competition in consumer electronics."
            ),
            metadata={"source": "apple_10k_summary.txt", "file_type": "text"},
        ),
    ]


@pytest.fixture
def sample_text():
    return (
        "FinQuery is a lightweight RAG project. "
        "It uses Groq for generation and Jina AI for embeddings. "
        "ChromaDB stores the vectors locally."
    )


# ── data-layer fixtures ──────────────────────────────────────────────────────


def _alembic_config(db_url: str) -> Config:
    cfg = Config(str(Path(BACKEND_ROOT) / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(BACKEND_ROOT) / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture(scope="session")
def migrated_engine(tmp_path_factory):
    """Session-scoped engine on a fresh DB migrated via Alembic."""
    from app.db.session import register_sqlite_pragmas

    db_path: Path = tmp_path_factory.mktemp("db") / "test_finance.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    register_sqlite_pragmas(engine)
    command.upgrade(_alembic_config(f"sqlite:///{db_path.as_posix()}"), "head")
    yield engine
    engine.dispose()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def db_session(migrated_engine) -> Session:
    """Function-scoped session wrapped in a rolled-back transaction."""
    connection = migrated_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def api_client(db_session):
    """TestClient with get_db overridden to the isolated test session."""
    from app.db.session import get_db
    from app.main import app

    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def memory_engine():
    """In-memory engine for lightweight model-level tests."""
    from app.db.base import Base
    from app.db.session import register_sqlite_pragmas
    import app.models  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    register_sqlite_pragmas(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def company_factory(db_session):
    """Creates companies directly through the repository."""

    def _make(ticker: str, legal_name: str | None = None, **kwargs):
        from app.models.company import Company

        company = Company(
            legal_name=legal_name or f"{ticker} Test Holdings Inc.",
            display_name=ticker,
            ticker=ticker,
            **kwargs,
        )
        db_session.add(company)
        db_session.flush()
        return company

    return _make


@pytest.fixture
def document_factory(db_session):
    """Creates a document (and optionally its company) for tests."""

    def _make(company=None, **kwargs):
        from app.models.document import Document

        if company is None:
            from app.models.company import Company

            company = Company(legal_name="Factory Co", ticker="FCTY")
            db_session.add(company)
            db_session.flush()
        defaults = dict(
            document_type="10-K",
            title="Annual Report",
            filing_date=None,
            processing_status="completed",
        )
        defaults.update(kwargs)
        document = Document(company_id=company.id, **defaults)
        db_session.add(document)
        db_session.flush()
        return document

    return _make
