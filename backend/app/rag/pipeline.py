"""End-to-end RAG pipeline: ingest, retrieve, generate."""

from __future__ import annotations

import logging

from app.rag.chunker import DocumentChunker
from app.rag.loader import FinancialDocumentLoader
from app.rag.embeddings import VectorStoreManager
from app.rag.generator import FinancialAnswerGenerator
from app.rag.retriever import FinancialRetriever

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates document loading, chunking, embedding, retrieval, and generation."""

    def __init__(self) -> None:
        self.loader = FinancialDocumentLoader()
        self.chunker = DocumentChunker()
        self.vsm = VectorStoreManager()
        self.retriever = FinancialRetriever(self.vsm)
        self.generator = FinancialAnswerGenerator()
        logger.info("RAG Pipeline ready")

    def ingest_documents(self, file_paths: list | None = None) -> dict:
        """Load, chunk, embed, and store documents."""
        docs = self.loader.load_for_ingest(file_paths)
        chunks = self.chunker.chunk_documents(docs)
        n = self.vsm.add_documents(chunks)
        sources = list({d.metadata.get("source", "") for d in docs if d.metadata.get("source")})
        return {
            "status": "success",
            "chunks_added": n,
            "sources": sources,
            "message": "Documents ingested successfully",
        }

    def query(self, question: str) -> dict:
        """Run full RAG: retrieve → generate → return answer with sources."""
        docs_with_scores = self.retriever.retrieve_with_scores(question)
        result = self.generator.generate_with_sources(question, docs_with_scores)
        return {
            "question": question,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "context_chunks": len(docs_with_scores),
            "model": result["model"],
        }

    def is_ready(self) -> bool:
        return self.vsm.vectorstore_exists()

    def reset(self) -> dict:
        self.vsm.delete_collection()
        return {
            "status": "cleared",
            "message": "Vectorstore cleared. Re-run ingest to use again.",
        }

    def get_stats(self) -> dict:
        return self.vsm.get_collection_stats()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== FinQuery RAG Demo ===")
    pipeline = RAGPipeline()
    print("\nIngesting sample docs...")
    result = pipeline.ingest_documents()
    print("Result:", result)
    print("\nQuerying...")
    for q in [
        "What was Apple total revenue?",
        "What are the risk factors?",
        "How much R&D spend?",
    ]:
        r = pipeline.query(q)
        print(f"\nQ: {q}\nA: {r['answer'][:300]}")
