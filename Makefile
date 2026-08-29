.PHONY: help setup dev backend frontend seed train test docker-up docker-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial project setup
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev: ## Run both backend and frontend in dev mode
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --reload --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev &

backend: ## Run backend only
	cd backend && uvicorn app.main:app --reload --port 8000

frontend: ## Run frontend only
	cd frontend && npm run dev

seed: ## Seed demo data
	cd backend && python -m app.scripts.seed_demo_data

seed-large: ## Seed large dataset (100K transactions)
	cd backend && python -m app.scripts.seed_demo_data --large

train: ## Train ML model
	cd backend && python -m app.ml.train

test: ## Run tests
	cd backend && python -m pytest tests/ -v

test-frontend: ## Run frontend tests
	cd frontend && npm test

docker-up: ## Start all services with Docker
	docker compose up --build -d

docker-down: ## Stop all Docker services
	docker compose down

clean: ## Clean generated files
	rm -f backend/*.db
	rm -rf backend/ml/models/*.joblib
	rm -rf frontend/dist
	rm -rf backend/__pycache__
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
