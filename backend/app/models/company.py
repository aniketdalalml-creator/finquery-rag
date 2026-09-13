"""Company model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ticker: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)

    documents = relationship("Document", back_populates="company", passive_deletes=True)

    __table_args__ = (
        Index(
            "uq_companies_user_ticker_exchange",
            "user_id",
            "ticker",
            "exchange",
            unique=True,
            sqlite_where=text("ticker IS NOT NULL"),
            postgresql_where=text("ticker IS NOT NULL"),
        ),
        Index(
            "uq_companies_user_legal_name_lower",
            "user_id",
            text("(lower(legal_name))"),
            unique=True,
        ),
        Index("ix_companies_ticker", "ticker"),
        Index("ix_companies_display_name_lower", text("(lower(display_name))")),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Company {self.id} {self.ticker or self.legal_name}>"
