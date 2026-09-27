.PHONY: help backend-install backend-lint backend-format backend-typecheck backend-test backend-migrate backend-run \
	frontend-install frontend-lint frontend-typecheck frontend-test frontend-build frontend-dev \
	up up-demo down config build smoke clean

help:
	@echo "CloudForge AI targets:"
	@echo "  up / up-demo        start full stack (default / demo compose)"
	@echo "  down                stop stack"
	@echo "  config              validate compose config"
	@echo "  build               build container images"
	@echo "  backend-test        run pytest"
	@echo "  frontend-test       run vitest"
	@echo "  smoke               run Playwright smoke test (needs running stack)"
	@echo "  backend-lint        ruff check + format check"
	@echo "  backend-typecheck   mypy"
	@echo "  frontend-lint       next lint"
	@echo "  frontend-typecheck  tsc --noEmit"
	@echo "  frontend-build      next build"

# ---------- backend ----------
backend-install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

backend-lint:
	cd backend && ruff check . && ruff format --check .

backend-typecheck:
	cd backend && mypy app

backend-test:
	cd backend && pytest -q

backend-migrate:
	cd backend && alembic upgrade head

backend-run:
	cd backend && uvicorn app.main:app --reload --port 8000

# ---------- frontend ----------
frontend-install:
	cd frontend && npm ci

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-test:
	cd frontend && npm test

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev

# ---------- containers ----------
up:
	docker compose up --build

up-demo:
	docker compose -f docker-compose.demo.yml up --build

down:
	docker compose -f docker-compose.demo.yml down 2>/dev/null; docker compose down

config:
	docker compose config >/dev/null && docker compose -f docker-compose.demo.yml config >/dev/null && echo "compose config OK"

build:
	docker compose build

smoke:
	cd frontend && npx playwright test tests/e2e/smoke.spec.ts

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	rm -rf backend/.venv backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache frontend/node_modules frontend/.next; \
	echo "cleaned"
