# Finance RAG — Data & Storage Layer Architecture

## Overview

The data layer follows a strict layered architecture. SQL never appears in API routes,
and business rules never appear in repositories.

```
API layer (app/api/v1/routes/*)        thin HTTP adapters, status codes
    ↓
Service layer (app/services/*)         business rules, validation, provenance checks
    ↓
Repository layer (app/repositories/*)  data-access logic only (queries, no commits)
    ↓
SQLAlchemy ORM (app/models/*)          9 tables
    ↓
Database                               MySQL 8 (current) / SQLite / PostgreSQL via config
```

**Transaction boundary:** `app.db.session.get_db` opens one session per request and
commits atomically on success / rolls back on any exception. Services and repositories
only `flush()`; they never commit.

## Schema

| Table | Purpose | Key constraints |
|---|---|---|
| `companies` | Company master data | unique `(ticker, exchange)` partial index; case-insensitive unique `lower(legal_name)`; ticker/display-name indexes for search |
| `documents` | Filings & reports | FK → companies (CASCADE); partial unique `(company_id, file_hash)` dedupes identical files; period-order CHECK |
| `document_pages` | Per-page raw/cleaned text | unique `(document_id, page_number)`; `page_number >= 1`; indexes on both columns |
| `document_sections` | Hierarchical sections | self-FK `parent_section_id` (CASCADE) enables nesting; page-order CHECK |
| `document_chunks` | Retrieval-ready chunks | unique `(document_id, chunk_index)`; optional FK → sections (SET NULL); JSONB `metadata` column |
| `financial_metrics` | Exact numeric facts | FKs → companies, documents, chunks; indexes for `(company, normalized_name, period)` and `(company, fiscal_year, quarter)` temporal queries; confidence range CHECK |
| `financial_tables` | Extracted tables | headers as JSONB; FK → source chunk; confidence CHECK |
| `financial_table_rows` | Table rows (structure preserved) | `cells` JSONB aligned positionally with headers; unique `(table_id, row_index)` |

### Design decisions

- **No DB enums.** Document/section/chunk/metric types are plain strings validated
  against registries in `app/core/constants.py`. Adding a type = one line, no migration.
- **Financial metrics are separate from chunks.** Numbers need exact filtering
  (company + metric + fiscal period), which vector search cannot provide.
- **Provenance is mandatory.** Every metric requires `document_id` (DB-level FK) plus
  `source_chunk_id` and/or `source_page` (service-level check). Full chain:
  `answer → metric → chunk → page → document → source_url`.
- **PostgreSQL-ready types.** JSON columns use `JSON().with_variant(JSONB, "postgresql")`;
  high-volume PKs use `BigInteger().with_variant(Integer, "sqlite")`. Partial indexes
  declare both `sqlite_where` and `postgresql_where` (the MySQL dialect ignores them and
  creates plain unique indexes — same semantics, since MySQL unique indexes allow
  multiple NULLs).
- **MySQL compatibility.** Current dev database is MySQL 8 (`llm_db`). Portable choices:
  no DB-level enums; CHECK constraints (enforced since MySQL 8.0.16); native JSON;
  functional indexes written as `(lower(col))` (double-parenthesized for MySQL
  functional key parts); ordering uses `col.is_(None)` instead of `NULLS LAST`
  (unsupported on MySQL). Note MySQL DDL is non-transactional — a failed migration can
  leave partial tables behind.
- **Multi-tenancy (future).** Tables carry no tenant columns yet; adding a `tenant_id`
  column per table via migration + repository scoping is the planned path.
- **SQLite dev parity.** `PRAGMA foreign_keys=ON` is registered on SQLite engines so
  CASCADE/SET NULL behave like the server databases during tests.

## Migrations

Alembic manages schema (`backend/alembic/versions/`). The DB URL comes from
`DATABASE_URL` (env) — never from `alembic.ini`.

```bash
cd backend
python migrate.py up            # upgrade to head
python migrate.py down          # downgrade one revision
python migrate.py down --all    # downgrade to base
python migrate.py status        # current revision
python migrate.py revision -m "..." --autogenerate   # new migration
```

Makefile equivalents: `make migrate-up`, `make migrate-down`, `make migrate-status`.

`Base.metadata.create_all()` is used **only** inside the demo seed script as a
convenience; all real schema management goes through Alembic.

## Storage abstraction

`app/storage/interface.py` defines `StorageBackend` with `upload/download/delete/
exists/get_metadata`. `LocalStorageBackend` (filesystem under `STORAGE_PATH`) is the
default; keys are sanitized against traversal. S3/MinIO can be added by registering a
new backend in `app/storage/__init__.py` — no changes above the interface.

`DocumentStorageService` wraps it: deterministic keys (`companies/{id}/{hash12}/{file}`),
SHA-256 hashing for document dedup.

## Switching databases

The URL lives in `DATABASE_URL` (backend/.env or env var). Current: MySQL 8.

```env
# MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/llm_db
# PostgreSQL
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/finance_rag
```

Driver install if needed: `pip install pymysql cryptography` / `pip install psycopg[binary]`,
then `python migrate.py up`. No code changes required.

## Demo data

`python seed_demo.py [--force]` loads public figures from Apple's FY2024 Form 10-K
(SEC EDGAR) — one company, one document, pages, hierarchical sections, chunks,
3 metrics, and one structure-preserving table.

## Testing

- `tests/test_db_models.py` — model creation, relationships, cascade deletes, provenance chain
- `tests/test_repositories.py` — CRUD, search/filtering, company/document scoping
- `tests/test_services.py` — duplicate detection, normalization, provenance enforcement
- `tests/test_api_v1.py` — success paths, 404/409/422 validation, table roundtrip

Tests run on isolated throwaway databases (temp-file/in-memory SQLite) migrated via
Alembic itself, with each test wrapped in a rolled-back transaction (`conftest.py`) —
they never touch `DATABASE_URL` / `llm_db`. The legacy RAG tests are unaffected.
