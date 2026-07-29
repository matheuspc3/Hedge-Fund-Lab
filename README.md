# Hedge-Fund-Lab

Laboratório Quantitativo de Backtesting baseado em Sistemas Multiagentes.

Pipeline ETL que baixa dados financeiros (via yfinance), calcula indicadores
técnicos (SMA, Bollinger Bands, RSI, MACD) e carrega em PostgreSQL. Inclui
um dashboard web com **5 estratégias de backtesting**, gráficos de drawdown
comparativo e scatter plot risco × retorno.

<img width="1883" height="887" alt="image" src="https://github.com/user-attachments/assets/09975b86-897d-459e-b3f2-5b98372ff1e4" />
<img width="1884" height="693" alt="image" src="https://github.com/user-attachments/assets/0f2d84cb-8405-4c77-817d-cd8fe7a23b41" />
<img width="1891" height="901" alt="image" src="https://github.com/user-attachments/assets/2e2201ac-b637-4028-aeea-03be82b2bedb" />


## Stack & Padrões Ouro

- **Python ≥ 3.11** — core da aplicação
- **Poetry** — gerenciamento determinístico de dependências e ambientes virtuais
- **Justfile** — automação de comandos cross-platform (PowerShell / Bash)
- **yfinance** — download de cotações históricas
- **SQLAlchemy 2.0** — ORM com suporte a upsert (`ON CONFLICT DO NOTHING`)
- **PostgreSQL 16** — persistência principal em container Docker (porta `5435`)
- **Prefect 2** — orquestração do pipeline ETL
- **Ruff & Pyright** — linting, formatação e checagem estática de tipos
- **Chart.js** — dashboard web interativo

---

## ⚡ Comandos Rápidos (`just`)

Utilize a ferramenta `just` no seu terminal (PowerShell ou Bash):

```powershell
just run           # 🚀 Executa TUDO: carga incremental + backtests + abre o dashboard
just install       # Instala o ambiente e dependências via Poetry
just db-up         # Sobe o container PostgreSQL 16 via Docker (porta 5435)
just db-down       # Encerra o container do banco de dados
just run-pipeline  # Executa apenas o pipeline ETL (yfinance -> PostgreSQL)
just generate-data # Roda os 5 backtests e gera o dashboard/data.json
just dashboard     # Inicia o servidor web do dashboard (http://localhost:8081)
just test          # Roda a suíte de 245 testes automatizados com Pytest
just lint          # Verifica estilo e qualidade do código com Ruff
just format        # Formata automaticamente o código conforme o Padrão Ouro
```

---

## Estrutura do Projeto

```
├── src/
│   ├── config.py             # Config via pydantic-settings (.env)
│   ├── logger.py             # Configuração centralizada de logging
│   ├── db/
│   │   ├── connection.py     # Engine SQLAlchemy + session factory
│   │   └── models.py         # ORM: Ativo, CotacaoDiaria, IndicadorTecnico (UniqueConstraints)
│   ├── pipeline/
│   │   ├── extract.py        # Download yfinance com cache e retry (+1d inclusive end)
│   │   ├── transform.py      # Indicadores técnicos (SMA, BB, RSI, MACD)
│   │   ├── load.py           # Inserção e Upsert incremental no PostgreSQL
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
├── tests/                    # 245 Testes automatizados com Pytest
├── docker-compose.yml        # PostgreSQL 16 (Porta 5435)
├── justfile                  # Automação de comandos
├── pyproject.toml            # Especificação Poetry e regras do Ruff
└── .env                      # Variáveis de ambiente da aplicação
```

---

## Setup do Ambiente

### 1. Pré-requisitos
- **Python 3.11+**
- **Poetry** (`pip install poetry`)
- **Just** (`cargo install just` ou `choco install just` / `scoop install just`)
- **Docker Desktop** (para o PostgreSQL)

### 2. Instalação das Dependências

```powershell
just install
```

### 3. Configuração das Variáveis de Ambiente (`.env`)

Crie ou edite o arquivo `.env` na raiz do projeto:

```ini
DATABASE_URL=postgresql://postgres:password@127.0.0.1:5435/hedgefundlab
DEFAULT_TICKERS=["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "ABEV3.SA", "WEGE3.SA", "CMIG4.SA", "RENT3.SA", "SUZB3.SA"]
START_DATE=2016-01-01
END_DATE=2026-07-21
BATCH_SIZE=1000
CACHE_DIR=data/raw
LOG_LEVEL=INFO
LOG_FILE=data/logs/hedgefund.log
```

### 4. Inicializar o Banco de Dados (PostgreSQL no Docker)

```powershell
just db-up
```
> O container `hedgefundlab-db` rodará exposto na porta **`5435`** (evitando conflitos com serviços locais do Postgres no Windows).

---

## 🚀 Como Rodar

### Execução em Comando Único

Para rodar todo o pipeline (Carga Incremental → Cálculo dos Backtests → Servidor do Dashboard):

```powershell
just run
```

Acesse o dashboard em: **[http://localhost:8081](http://localhost:8081)**
Logs em tempo real: **[http://localhost:8081/logs](http://localhost:8081/logs)**

---

## Estratégias de Backtesting

### Single-Asset (3 estratégias)

| Estratégia | Descrição |
|------------|-----------|
| **Buy & Hold** | Compra no primeiro dia e mantém até o fim |
| **SMA Cross (50/200)** | Compra no golden cross (SMA 50 cruza acima da SMA 200); vende no death cross (SMA 50 cruza abaixo) |
| **Bollinger Bands (20,2)** | Compra quando o preço toca a banda inferior; vende quando toca a banda superior |

### Portfólio Multi-Ativo (2 estratégias)

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
---

## Qualidade de Código & Testes

```powershell
# Executa os 245 testes unitários
just test

# Executa a checagem estática de estilo (Linter)
just lint
```
