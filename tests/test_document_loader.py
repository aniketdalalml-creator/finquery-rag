"""Tests for FinancialDocumentLoader.load_for_ingest routing."""

from __future__ import annotations

from src.document_loader import FinancialDocumentLoader


def test_load_for_ingest_prefers_data_raw(tmp_path, monkeypatch):
    monkeypatch.setattr("config.config.config.RAW_DOCS_PATH", str(tmp_path))
    (tmp_path / "note.txt").write_text("hello from raw", encoding="utf-8")

    loader = FinancialDocumentLoader()
    docs = loader.load_for_ingest(None)

    assert len(docs) == 1
    assert docs[0].page_content == "hello from raw"
    assert docs[0].metadata.get("source") == "note.txt"


def test_load_for_ingest_falls_back_to_sample_when_raw_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("config.config.config.RAW_DOCS_PATH", str(tmp_path))
    assert list(tmp_path.iterdir()) == []

    loader = FinancialDocumentLoader()
    docs = loader.load_for_ingest(None)

    assert len(docs) >= 1
    sources = {d.metadata.get("source") for d in docs}
    assert "apple_10k_summary.txt" in sources


def test_load_for_ingest_explicit_paths(tmp_path, monkeypatch):
    f = tmp_path / "x.txt"
    f.write_text("explicit file", encoding="utf-8")

    loader = FinancialDocumentLoader()
    docs = loader.load_for_ingest([str(f)])

    assert len(docs) == 1
    assert "explicit file" in docs[0].page_content
