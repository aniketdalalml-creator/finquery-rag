"""Storage package: backend factory keyed by STORAGE_BACKEND config."""

from __future__ import annotations

from app.core.config import config
from app.storage.interface import StorageBackend
from app.storage.local import LocalStorageBackend

_BACKENDS: dict[str, type[StorageBackend]] = {
    "local": LocalStorageBackend,
}

_instances: dict[str, StorageBackend] = {}


def get_storage() -> StorageBackend:
    """Return the configured storage backend (cached singleton)."""
    name = config.STORAGE_BACKEND
    if name not in _instances:
        try:
            cls = _BACKENDS[name]
        except KeyError:
            raise ValueError(
                f"Unsupported STORAGE_BACKEND {name!r}. Available: {sorted(_BACKENDS)}"
            ) from None
        if issubclass(cls, LocalStorageBackend):
            _instances[name] = cls(config.STORAGE_PATH)
        else:  # future: S3/MinIO backends take their own settings
            _instances[name] = cls()
    return _instances[name]
