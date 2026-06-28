# AlfaFuture Hack — project automation
# Run `make` or `make help` to see all available targets.

COMPOSE_FILE := src/docker-compose.yaml
ENV_FILE     := src/backend/.env
DC           := docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE)

BACKEND_DIR  := src/backend
JWT_PRIVATE  := $(BACKEND_DIR)/jwt-private.pem
JWT_PUBLIC   := $(BACKEND_DIR)/jwt-public.pem

.DEFAULT_GOAL := help

.PHONY: help up down build rebuild restart logs ps migrate makemigration \
        shell test eval seed lint fmt keys keys-if-missing clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: keys-if-missing ## Build (if needed) and start all services, then run migrations
	$(DC) up -d --build
	$(MAKE) migrate

down: ## Stop and remove containers
	$(DC) down

build: ## Build all images
	$(DC) build

rebuild: ## Rebuild images from scratch and restart the stack
	$(DC) down
	$(DC) build --no-cache
	$(DC) up -d
	$(MAKE) migrate

restart: ## Restart all services
	$(DC) restart

logs: ## Tail logs of all services
	$(DC) logs -f

ps: ## Show service status
	$(DC) ps

migrate: ## Apply database migrations (alembic upgrade head)
	$(DC) run --rm backend alembic upgrade head

makemigration: ## Create a migration: make makemigration m="your message"
	$(DC) run --rm backend alembic revision --autogenerate -m "$(m)"

shell: ## Open a bash shell inside the backend container
	$(DC) exec backend bash

test: ## Run the backend test suite
	$(DC) run --rm --no-deps backend pytest

eval: ## Run the agent eval suite (LLM-as-judge; writes evals/report.md)
	$(DC) run --rm backend python -m evals.runner

seed: ## Ingest the markdown knowledge base into pgvector
	$(DC) run --rm backend python -m features.rag.ingest

lint: ## Run ruff + black checks on the backend
	$(DC) run --rm --no-deps backend sh -c "ruff check . && black --check ."

fmt: ## Auto-format the backend (ruff --fix + black)
	$(DC) run --rm --no-deps backend sh -c "ruff check --fix . && black ."

keys: ## Generate a fresh RS256 JWT key pair (overwrites existing keys)
	@echo "Generating RS256 JWT key pair..."
	@openssl genrsa -out $(JWT_PRIVATE) 2048
	@openssl rsa -in $(JWT_PRIVATE) -pubout -out $(JWT_PUBLIC)
	@echo "Keys written to $(JWT_PRIVATE) and $(JWT_PUBLIC)"

keys-if-missing: ## Generate JWT keys only if they do not already exist
	@if [ ! -f $(JWT_PRIVATE) ] || [ ! -f $(JWT_PUBLIC) ]; then $(MAKE) keys; fi

clean: ## Stop the stack and DELETE volumes (destroys the database)
	$(DC) down -v
