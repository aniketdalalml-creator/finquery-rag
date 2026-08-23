"""DocumentStorageService — file storage tied to document records."""

from __future__ import annotations

import hashlib

from app.storage.interface import StorageBackend


class DocumentStorageService:
    """Uploads/downloads raw files via the StorageBackend abstraction.

    Produces deterministic keys and the content hash used for duplicate
    detection at the database layer.
    """

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage

    def store_document(
        self,
        company_id: int | None,
        filename: str,
        data: bytes,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        """Store bytes, return (storage_key, sha256_hex)."""
        safe_name = _sanitize_filename(filename)
        digest = hashlib.sha256(data).hexdigest()
        prefix = f"companies/{company_id}" if company_id is not None else "unassigned"
        key = f"{prefix}/{digest[:12]}/{safe_name}"
        self._storage.upload(key, data, content_type=content_type)
        return key, digest

    def download(self, key: str) -> bytes:
        return self._storage.download(key)

    def delete(self, key: str) -> None:
        self._storage.delete(key)

    def exists(self, key: str) -> bool:
        return self._storage.exists(key)

    def metadata(self, key: str):
        return self._storage.get_metadata(key)


def _sanitize_filename(name: str) -> str:
    cleaned = name.replace("\\", "/").split("/")[-1].strip()
    cleaned = " ".join(cleaned.split())
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError(f"Invalid filename: {name!r}")
    return cleaned
