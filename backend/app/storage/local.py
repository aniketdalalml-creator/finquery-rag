"""Local filesystem storage backend (development default)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from app.storage.interface import (
    ObjectMetadata,
    ObjectNotFoundError,
    StorageBackend,
    StorageError,
)

_RESERVED = {"", ".", ".."}


class LocalStorageBackend(StorageBackend):
    """Stores objects as files under a root directory.

    Keys use forward slashes and are validated to stay inside the root.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        pure = PurePosixPath(key.replace("\\", "/"))
        if pure.is_absolute() or any(part in _RESERVED for part in pure.parts):
            raise StorageError(f"Invalid storage key: {key!r}")
        target = (self._root / pure).resolve()
        if self._root != target and self._root not in target.parents:
            raise StorageError(f"Storage key escapes root: {key!r}")
        return target

    def upload(self, key: str, data: bytes, content_type: str | None = None) -> ObjectMetadata:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return ObjectMetadata(
            key=key,
            size_bytes=len(data),
            content_type=content_type,
            last_modified=datetime.now(timezone.utc),
            etag=hashlib.md5(data).hexdigest(),
        )

    def download(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.is_file():
            raise ObjectNotFoundError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if not path.is_file():
            raise ObjectNotFoundError(key)
        path.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def get_metadata(self, key: str) -> ObjectMetadata:
        path = self._resolve(key)
        if not path.is_file():
            raise ObjectNotFoundError(key)
        stat = path.stat()
        data_hash = hashlib.md5(path.read_bytes()).hexdigest()
        return ObjectMetadata(
            key=key,
            size_bytes=stat.st_size,
            content_type=None,
            last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            etag=data_hash,
        )
