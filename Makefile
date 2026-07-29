.PHONY: dev test test-all test-backend test-frontend test-integration lint build migrate

dev:
	docker compose up --build

test: test-backend test-frontend

test-all: test test-integration

test-backend:
	cd apps/server && uv run pytest -m "not integration"

test-frontend:
	cd apps/web && pnpm test --run

test-integration:
	@docker compose -p aidp_integration up -d --wait postgres; \
	status=0; \
	cd apps/server && AIDP_TEST_POSTGRES_DSN=postgresql://aidp:aidp@localhost:5432/aidp uv run pytest -m integration || status=$$?; \
	cd ../..; \
	docker compose -p aidp_integration down -v; \
	exit $$status

lint:
	cd apps/server && uv run ruff check .
	cd apps/web && pnpm typecheck

build:
	cd apps/web && pnpm build

migrate:
	cd apps/server && uv run alembic upgrade head
