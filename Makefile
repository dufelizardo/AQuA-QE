.PHONY: help dev test test-unit test-int test-api lint db-upgrade db-migrate db-reset clean

help:
	@echo ""
	@echo "  AQuA-QE — comandos disponíveis"
	@echo "  make dev          Inicia API (reload)"
	@echo "  make test         Suite completa"
	@echo "  make test-unit    Apenas unitários"
	@echo "  make test-int     Apenas integração"
	@echo "  make test-api     Apenas API HTTP"
	@echo "  make lint         Ruff check"
	@echo "  make db-upgrade   Aplica migrations"
	@echo "  make db-migrate   Gera migration (MSG=desc)"
	@echo "  make db-reset     Reseta banco"
	@echo "  make clean        Remove cache"
	@echo ""

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test: test-unit test-int test-api
	@echo "✓ Suite completa OK"

test-unit:
	ANTHROPIC_API_KEY=mock OPENAI_API_KEY=mock \
	python -m pytest tests/unit/ -v --tb=short

test-int:
	ANTHROPIC_API_KEY=mock OPENAI_API_KEY=mock \
	python -m pytest tests/integration/ -v --tb=short

test-api:
	ANTHROPIC_API_KEY=mock OPENAI_API_KEY=mock \
	python -m pytest tests/api/ -v --tb=short

lint:
	ruff check .

db-upgrade:
	alembic upgrade head

db-migrate:
	@[ "$(MSG)" ] || (echo "Uso: make db-migrate MSG='descrição'" && exit 1)
	alembic revision --autogenerate -m "$(MSG)"

db-reset:
	rm -f aqua_qe.db
	alembic upgrade head

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .pytest_cache .mypy_cache .ruff_cache 2>/dev/null; true
	@echo "✓ Cache limpo"
