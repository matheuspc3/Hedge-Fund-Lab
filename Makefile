.PHONY: install install-dev test test-quick lint lint-fix run-pipeline \
        dashboard dashboard-data generate-data db-up db-down db-reset clean help

# ─── Instalação ───────────────────────────────────────────────────

install:           ## Instala dependências de produção
	pip install -e .

install-dev:       ## Instala dependências de produção + dev (testes, lint)
	pip install -e ".[dev]"

# ─── Testes ───────────────────────────────────────────────────────

test:              ## Roda todos os testes com cobertura (mínimo 95%)
	pytest --cov=src --cov-fail-under=95 -v tests/

test-quick:        ## Roda testes sem cobertura (mais rápido)
	pytest -v tests/

# ─── Lint ─────────────────────────────────────────────────────────

lint:              ## Verifica estilo e qualidade do código com ruff
	ruff check src/ tests/

lint-fix:          ## Corrige automaticamente o que o ruff apontar
	ruff check --fix src/ tests/

# ─── Pipeline ─────────────────────────────────────────────────────

run-pipeline:      ## Executa o pipeline ETL completo
	python -m src.pipeline.flows

# ─── Dashboard ────────────────────────────────────────────────────

dashboard:         ## Sobe o servidor do dashboard (http://localhost:8081)
	python dashboard/server.py

dashboard-data:    ## Gera data.json com 10 tickers + portfólio
	python scripts/generate_dashboard_data.py

generate-data: dashboard-data  ## Alias para dashboard-data

# ─── Banco de Dados ───────────────────────────────────────────────

db-up:             ## Sobe o container PostgreSQL
	docker compose up -d

db-down:           ## Para o container PostgreSQL
	docker compose down

db-reset:          ## Destrói e recria o banco (cuidado: perde dados)
	docker compose down -v
	docker compose up -d

# ─── Limpeza ──────────────────────────────────────────────────────

clean:             ## Remove cache, dados temporários e .db local
	rm -rf data/raw/*.csv data/logs/*.log
	rm -f hedgefundlab.db
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__
	rm -rf .ruff_cache

# ─── Help ─────────────────────────────────────────────────────────

help:              ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
