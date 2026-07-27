# FinQuery RAG — common dev tasks
# Use:  make <target>

PYTHON ?= python
export PYTHONPATH := .

.PHONY: install api ui ingest test docker-up docker-down clean

install:
	$(PYTHON) -m pip install -r requirements.txt

api:
	uvicorn api.main:app --reload --port 8000

ui:
	streamlit run app/streamlit_app.py

ingest:
	$(PYTHON) src/pipeline.py

test:
	pytest -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	$(PYTHON) -c "import shutil, pathlib; r=pathlib.Path('.'); shutil.rmtree(r/'vectorstore/chroma_db', ignore_errors=True); [shutil.rmtree(p, ignore_errors=True) for p in r.rglob('__pycache__') if p.is_dir()]"
