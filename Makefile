PYTHON = .venv/Scripts/python.exe
UVICORN = .venv/Scripts/uvicorn.exe
PYTEST = .venv/Scripts/pytest.exe
ALEMBIC = .venv/Scripts/alembic.exe

.PHONY: run test migrate seed docker-up docker-down clean openapi worker web-dev web-build web-types

run:
	$(UVICORN) api.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(PYTEST) -v

migrate:
	$(ALEMBIC) upgrade head

seed:
	$(PYTHON) seed.py

openapi:
	$(PYTHON) scripts/export_openapi.py

worker:
	$(PYTHON) -m arq api.worker.WorkerSettings

web-dev:
	pnpm --dir web dev

web-build:
	pnpm --dir web build

web-types: openapi
	pnpm --dir web generate-types

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
