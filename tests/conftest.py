"""Shared pytest fixtures for FinQuery tests."""
import os
import sys

# Ensure project root is on sys.path so tests can import src.*, api.*, config.*
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from langchain_core.documents import Document


@pytest.fixture
def sample_documents():
    """Return a small list of Documents for chunking/embedding tests."""
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
    """Return a simple paragraph for chunk_text() tests."""
    return (
        "FinQuery is a lightweight RAG project. "
        "It uses Groq for generation and Jina AI for embeddings. "
        "ChromaDB stores the vectors locally."
    )
