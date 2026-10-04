# TrustRAG thin wrappers over the CLI (src/trustrag/cli.py).
# Every command can also be run directly: `python -m trustrag.cli <cmd>`.

PY = python -m trustrag.cli

.PHONY: up down api ui test lint ingest eval bench report demo-small

up:
	docker compose up -d

down:
	docker compose down

api:
	uvicorn trustrag.api.app:app --host 0.0.0.0 --port 8000 --reload

ui:
	streamlit run src/trustrag/ui/app.py

test:
	pytest -q

lint:
	ruff check src tests

ingest:
	$(PY) ingest --n 100000

demo-small:
	$(PY) ingest --n 10000

eval:
	$(PY) eval --mode hybrid --split test --judge non-llm

bench:
	$(PY) bench --mode hybrid --n 100 --no-cache

report:
	$(PY) report
