"""Domain errors. Services raise these; the API layer maps them to HTTP."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected, user-facing errors."""


class NotFoundError(DomainError):
    def __init__(self, entity: str, entity_id: int | str) -> None:
        super().__init__(f"{entity} with id {entity_id} not found")
        self.entity = entity
        self.entity_id = entity_id


class ConflictError(DomainError):
    """Resource already exists / conflicts with existing state."""


class ValidationError(DomainError):
    """Business-rule violation beyond what schema validation catches."""
