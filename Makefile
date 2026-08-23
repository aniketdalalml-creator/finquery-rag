# FinQuery — monorepo
#
#   frontend/   React + Vite UI
#   backend/    FastAPI + RAG

PYTHON ?= python
BACKEND := backend
FRONTEND := frontend

.PHONY: install api frontend ingest test docker-up docker-down clean

install:
	cd $(BACKEND) && $(PYTHON) -m pip install -r requirements.txt
	cd $(FRONTEND) && npm install

api:
	cd $(BACKEND) && PYTHONPATH=. uvicorn app.main:app --reload --port 8000

frontend:
	cd $(FRONTEND) && npm run dev

ingest:
	cd $(BACKEND) && PYTHONPATH=. $(PYTHON) -m app.rag.pipeline

test:
	cd $(BACKEND) && PYTHONPATH=. pytest -v

migrate-up:
	cd $(BACKEND) && PYTHONPATH=. $(PYTHON) migrate.py up

migrate-down:
	cd $(BACKEND) && PYTHONPATH=. $(PYTHON) migrate.py down

migrate-status:
	cd $(BACKEND) && PYTHONPATH=. $(PYTHON) migrate.py status

seed:
	cd $(BACKEND) && PYTHONPATH=. $(PYTHON) seed_demo.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	$(PYTHON) -c "import shutil, pathlib; r=pathlib.Path('backend'); shutil.rmtree(r/'vectorstore/chroma_db', ignore_errors=True); [shutil.rmtree(p, ignore_errors=True) for p in r.rglob('__pycache__') if p.is_dir()]"
