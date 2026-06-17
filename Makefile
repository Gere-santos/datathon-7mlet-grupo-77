.PHONY: install test lint api mlflow clean data demo

install:
	pip install -e ".[dev]"

test:
	python3 -m pytest tests/ -v

lint:
	python3 -m ruff check src/ tests/

api:
	uvicorn src.datathon_offerexp.app:app --reload --host 0.0.0.0 --port 8000

demo:
	bash scripts/run_demo.sh

data:
	python3 data/synthetic_enrichment/generate_synthetic_data.py

mlflow:
	mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
