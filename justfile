set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

# Exibe todos os comandos disponíveis
default:
    @just --list

# Instala todas as dependências do projeto via Poetry
install:
    poetry install

# Inicializa o container PostgreSQL via Docker (abre o Docker Desktop se estiver fechado)
db-up:
    @$dockerRunning = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue; if (-not $dockerRunning) { Write-Host "Iniciando Docker Desktop..."; Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"; Start-Sleep -Seconds 10 }; docker compose up -d

# Para os containers Docker
db-down:
    docker compose down

# Executa o pipeline ETL (download yfinance + indicadores + carga no Postgres)
run-pipeline:
    poetry run python -m src.pipeline.flows

# Roda os backtests e gera o arquivo dashboard/data.json
generate-data:
    poetry run python scripts/generate_dashboard_data.py

# Inicia o servidor web do dashboard (http://localhost:8081)
dashboard:
    poetry run python dashboard/server.py

# Roda a suíte de testes automatizados com pytest
test:
    poetry run pytest

# Executa a verificação estática de estilo e qualidade de código com Ruff
lint:
    poetry run ruff check .

# Formata automaticamente o código conforme o Padrão Ouro do Ruff
format:
    poetry run ruff format .

# Executa a carga incremental, atualiza os backtests e abre o dashboard web
update-all: run-pipeline generate-data dashboard

# Alias curto para rodar o ciclo completo (just run)
run: update-all
