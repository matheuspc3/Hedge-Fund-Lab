# Hedge-fund-lab

Laboratório Quantitativo de Backtesting baseado em Sistemas Multiagentes.

Pipeline ETL que baixa dados financeiros (via yfinance), calcula indicadores
técnicos (SMA, Bollinger Bands, RSI, MACD) e carrega em PostgreSQL. Inclui
um dashboard web com **5 estratégias de backtesting**, gráficos de drawdown
comparativo e scatter plot risco × retorno.

## Stack

- **Python ≥ 3.11** — core da aplicação
- **yfinance** — download de cotações históricas
- **SQLAlchemy 2.0** — ORM e conexão com banco
- **PostgreSQL 16** — persistência (também compatível com SQLite)
- **Prefect 2** — orquestração do pipeline ETL
- **Chart.js** — dashboard web interativo

## Comandos rápidos (Makefile)

```bash
make install          # Instala dependências de produção
make install-dev      # Instala com dependências de dev (testes)
make test             # Roda testes com cobertura (≥ 95%)
make lint             # Verifica estilo do código (ruff)
make run-pipeline     # Executa o pipeline ETL
make generate-data    # Gera data.json para o dashboard
make dashboard        # Sobe o servidor do dashboard
make db-up            # Sobe o PostgreSQL (Docker)
make db-down          # Para o PostgreSQL
make clean            # Remove cache e dados temporários
make help             # Mostra todos os comandos disponíveis
```

> **Windows**: se não tiver `make`, use [Git Bash](https://git-scm.com),
> [Chocolatey](https://chocolatey.org) (`choco install make`) ou leia os
> comandos equivalentes nas seções abaixo.

## Estrutura

```
├── src/
│   ├── config.py             # Config via pydantic-settings (.env)
│   ├── logger.py             # Configuração centralizada de logging
│   ├── db/
│   │   ├── connection.py     # Engine SQLAlchemy + session factory
│   │   └── models.py         # ORM: Ativo, CotacaoDiaria, IndicadorTecnico
│   ├── pipeline/
│   │   ├── extract.py        # Download yfinance com cache e retry
│   │   ├── transform.py      # Indicadores técnicos (SMA, BB, RSI, MACD)
│   │   ├── load.py           # Inserção em batch no PostgreSQL
│   │   └── flows.py          # Orquestração Prefect
│   ├── backtesting/
│   │   ├── engine.py         # Motor de backtesting single-asset
│   │   ├── portfolio.py      # Motor de backtesting multi-ativo
│   │   ├── metrics.py        # Sharpe, Sortino, Max Drawdown, etc.
│   │   └── cost_model.py     # Modelo de custos de transação
│   └── strategies/
│       ├── buy_and_hold.py   # Estratégia Buy & Hold
│       ├── sma_cross.py      # Estratégia SMA Cross (50/200)
│       └── bollinger_bands.py # Estratégia Bollinger Bands (20,2)
├── scripts/
│   └── generate_dashboard_data.py  # Gera data.json (backtests + agregação)
├── dashboard/
│   ├── server.py             # Servidor HTTP (dashboard + logs SSE)
│   ├── index.html            # Dashboard Chart.js
│   ├── app.js                # Lógica do dashboard
│   ├── style.css             # Estilos
│   └── logs.html             # Visualizador de logs em tempo real
├── tests/                    # Testes pytest
├── docker-compose.yml        # PostgreSQL 16
├── .env.example              # Template de variáveis de ambiente
└── pyproject.toml            # Dependências e metadados
```

## Pré-requisitos

- **Python 3.11+**
- **Docker** (para PostgreSQL — opcional, o projeto roda com SQLite por padrão)
- **Git**

## Setup

### 1. Clone e entre no diretório

```bash
git clone <url-do-repo>
cd hedge-fund-lab
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -e .           # Produção
pip install -e ".[dev]"    # Com dependências de desenvolvimento (testes)
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` conforme necessário. Por padrão, o projeto usa **SQLite**
(`hedgefundlab.db`), que não requer Docker.

### 5. (Opcional) Suba o PostgreSQL com Docker

Caso queira usar PostgreSQL, edite o `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/hedgefundlab
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=hedgefundlab
```

E suba o container:

```bash
docker compose up -d
```

## Como rodar

### Pipeline ETL completo

Baixa cotações, calcula indicadores e persiste no banco:

```bash
python -m src.pipeline.flows
```

Também é possível rodar com o servidor do **Prefect** para acompanhar a
orquestração:

```bash
prefect server start
python -m src.pipeline.flows
```

### Gerar dados do dashboard (com backtests)

Após popular o banco, gere o `data.json` com todos os backtests:

```bash
python scripts/generate_dashboard_data.py
```

Este script:
1. Verifica se o banco tem dados para os 10 tickers; se não, executa o pipeline ETL automaticamente
2. Roda **backtests single-asset** (Buy & Hold, SMA Cross, Bollinger) em **todos os tickers** e agrega os resultados (média ± desvio padrão)
3. Roda **backtests de portfólio** multi-ativo (Equal Weight, Min Variance)
4. Calcula séries de **drawdown** para cada estratégia
5. Gera dados para o **scatter plot** risco × retorno
6. Salva `dashboard/data.json` com toda a estrutura

### Dashboard

```bash
python dashboard/server.py
```

Acesse: **[http://localhost:8081](http://localhost:8081)**

### Logs em tempo real

Com o dashboard rodando, acesse **[http://localhost:8081/logs](http://localhost:8081/logs)**
para acompanhar o arquivo de log via SSE (Server-Sent Events).

### Testes

```bash
pytest

# Com cobertura
pytest --cov=src
```

## Estratégias de Backtesting

### Single-Asset (3 estratégias)

Cada estratégia é executada individualmente nos 10 tickers e os resultados
são agregados (média ± desvio padrão) para comparação justa com portfólios.

| Estratégia | Descrição |
|------------|-----------|
| **Buy & Hold** | Compra no primeiro dia e mantém até o fim |
| **SMA Cross (50/200)** | Compra no golden cross (SMA 50 cruza acima da SMA 200); vende no death cross (SMA 50 cruza abaixo) |
| **Bollinger Bands (20,2)** | Compra quando o preço toca a banda inferior; vende quando toca a banda superior |

### Portfólio Multi-Ativo (2 estratégias)

As estratégias de portfólio operam sobre os 10 ativos simultaneamente,
com rebalanceamento a cada 63 dias úteis (~3 meses).

| Estratégia | Descrição |
|------------|-----------|
| **Equal Weight** | Mantém pesos iguais (10%) em todos os ativos, rebalanceando periodicamente |
| **Min Variance** | Otimiza pesos para minimizar a volatilidade da carteira (sem vendas a descoberto) |

## Dashboard

O dashboard possui duas abas principais:

### 📊 Portfólio Multi-Ativo
- **Cards de métricas**: Sharpe, Sortino, Retorno e Drawdown de cada estratégia
- **Equity Curves**: evolução patrimonial comparativa de todas as 5 estratégias
- **Drawdown Chart**: série de drawdown de cada estratégia
- **Scatter Plot**: risco (volatilidade) × retorno, com Sharpe como indicador de cor
- **Alocação**: gráficos de pizza com os pesos atuais (Equal Weight e Min Variance)
- **Tabela comparativa**: todas as métricas lado a lado

### 📈 Análise por Ativo
- Gráfico de preço com SMA 50/200 e Bandas de Bollinger
- RSI com bandas de sobrecompra (70) e sobrevenda (30)
- MACD com histograma
- Cards de resumo e estatísticas
- Tabela dos últimos 20 pregões

## Configuração (.env)

| Variável            | Padrão                    | Descrição                     |
|---------------------|---------------------------|-------------------------------|
| `DATABASE_URL`      | `sqlite:///hedgefundlab.db` | Connection string do banco    |
| `DEFAULT_TICKERS`   | `PETR4.SA,VALE3.SA,...`   | 10 ativos da B3               |
| `START_DATE`        | `2016-01-01`              | Início do período histórico   |
| `END_DATE`          | `2025-12-31`              | Fim do período histórico      |
| `BATCH_SIZE`        | `1000`                    | Tamanho do batch de inserção  |
| `CACHE_DIR`         | `data/raw`                | Diretório de cache CSV        |
| `LOG_LEVEL`         | `INFO`                    | Nível de log                  |
| `LOG_FILE`          | `data/logs/hedgefund.log` | Arquivo de log                |

### Tickers monitorados

| Ticker   | Empresa               | Setor              |
|----------|-----------------------|--------------------|
| PETR4.SA | Petrobras             | Petróleo & Gás     |
| VALE3.SA | Vale                  | Mineração          |
| ITUB4.SA | Itaú Unibanco         | Bancos             |
| BBDC4.SA | Bradesco              | Bancos             |
| BBAS3.SA | Banco do Brasil       | Bancos             |
| ABEV3.SA | Ambev                 | Bebidas            |
| WEGE3.SA | Weg                   | Bens Industriais   |
| CMIG4.SA | Cemig                 | Energia Elétrica   |
| RENT3.SA | Localiza              | Locação de Veículos|
| SUZB3.SA | Suzano                | Papel & Celulose   |

> **Nota:** PETR4.SA possui dados disponíveis no yfinance apenas a partir de
> 2024 (devido a eventos corporativos). As demais 9 ações cobrem todo o
> período desde 2016.

## Indicadores calculados

| Indicador          | Descrição                                |
|--------------------|------------------------------------------|
| SMA-50             | Média móvel simples de 50 períodos       |
| SMA-200            | Média móvel simples de 200 períodos      |
| Bollinger Bands    | Bandas de Bollinger (20,2)               |
| RSI                | Relative Strength Index (14)             |
| MACD               | Moving Average Convergence Divergence    |
| MACD Sinal         | Linha de sinal do MACD                   |
