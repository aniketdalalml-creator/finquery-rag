"""Shared runtime state (avoids circular imports between main and routes)."""

from __future__ import annotations

from typing import Any

from app.services.chat import ChatService

pipeline: Any | None = None
chat_service = ChatService(pipeline=None)
