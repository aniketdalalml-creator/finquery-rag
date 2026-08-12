"""
RAG domain package — implement features one-by-one.

Suggested order:
  1. loader      — load PDF/TXT into documents
  2. chunker     — split documents into chunks
  3. embeddings  — embed + persist in Chroma
  4. retriever   — similarity search
  5. generator   — LLM grounded answers
  6. pipeline    — wire ingest + query

Toggle CHAT_MODE=dummy|rag in .env while building.
"""
