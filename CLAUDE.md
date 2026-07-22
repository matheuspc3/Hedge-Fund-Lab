# Hedge-fund-lab — TCC

## O que é

Laboratório Quantitativo de Backtesting baseado em Sistemas Multiagentes.
Pipeline ETL que baixa dados financeiros (yfinance), calcula indicadores
técnicos (SMA, Bollinger, RSI, MACD) e carrega em PostgreSQL.

## Estrutura

| Path | Propósito |
|------|-----------|
| `src/config.py` | Config via pydantic-settings (.env) |
| `src/db/` | Modelos ORM e conexão SQLAlchemy (PostgreSQL) |
| `src/pipeline/` | Pipeline ETL: extract → transform → load |
| `src/pipeline/extract.py` | Download yfinance com cache e retry |
| `src/pipeline/transform.py` | Indicadores técnicos (SMA, BB, RSI, MACD) |
| `src/pipeline/load.py` | Inserção em batch no PostgreSQL |
| `src/pipeline/flows.py` | Orquestração Prefect |
| `dashboard/` | Frontend JS (Chart.js) + servidor HTTP |
| `tests/` | Testes pytest |
| `AGENTS.md` | Regras Ponytail — código mínimo, sem over-engineering |

## Comandos

```bash
# Rodar testes
pytest

# Com coverage
pytest --cov=src

# Subir banco
docker compose up -d

# Rodar pipeline ETL completo (com Prefect)
python -m src.pipeline.flows

# Servir dashboard
python dashboard/server.py
```
