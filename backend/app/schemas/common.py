"""Shared schema helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base for request payloads: reject unknown fields, no silent coercion."""

    model_config = ConfigDict(extra="forbid")
