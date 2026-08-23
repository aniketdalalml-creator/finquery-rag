"""Object-storage abstraction.

Business logic depends on this interface only; swapping local filesystem for
S3/MinIO later requires no changes above this layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ObjectMetadata:
    key: str
    size_bytes: int
    content_type: str | None
    last_modified: datetime | None
    etag: str | None


class StorageError(Exception):
    """Raised when the storage backend cannot complete an operation."""


class ObjectNotFoundError(StorageError):
    def __init__(self, key: str) -> None:
        super().__init__(f"Object not found in storage: {key!r}")
        self.key = key


class StorageBackend(ABC):
    """Contract for object storage implementations.

    Keys are backend-neutral logical paths (e.g. ``documents/10k/acme.pdf``).
    Implementations must reject keys that escape their root or contain
    path traversal segments.
    """

    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str | None = None) -> ObjectMetadata:
        """Store `data` under `key`, creating intermediate prefixes as needed."""

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Return the object bytes. Raises ObjectNotFoundError if missing."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the object. Raises ObjectNotFoundError if missing."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if the object exists."""

    @abstractmethod
    def get_metadata(self, key: str) -> ObjectMetadata:
        """Return object metadata. Raises ObjectNotFoundError if missing."""
