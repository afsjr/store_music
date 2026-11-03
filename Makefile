.PHONY: setup ingest index run test lint format examples

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

ingest:
	.venv/bin/python -m scripts.ingest

index:
	.venv/bin/python -m scripts.build_policy_index

run:
	.venv/bin/python -m uvicorn app.main:app --reload --port 8000

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check app scripts tests

format:
	.venv/bin/ruff format app scripts tests

examples:
	.venv/bin/python -m scripts.run_examples
