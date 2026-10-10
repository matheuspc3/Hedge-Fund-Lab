# Hedge-Fund-Lab

Laboratório Quantitativo de Backtesting baseado em Sistemas Multiagentes.

> **Estado do projeto:** protótipo técnico em evolução. O pipeline, cinco
> benchmarks clássicos, dashboard e uma primeira estratégia LLM de três estágios
> existem. Um runner diário persistente e um calendário B3 local também já
> existem, mas a arena comparável entre clássicos e LLM ainda não; os resultados
> atuais não devem ser tratados como evidência científica.
>
> Comece pela [documentação](docs/README.md), especialmente o
> [estado atual auditado](docs/ESTADO_ATUAL.md), a
> [arquitetura](docs/ARQUITETURA.md), o
> [roadmap canônico](docs/ROADMAP.md) e o
> [protocolo experimental](docs/EXPERIMENT_PROTOCOL.md).

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
- **PostgreSQL 16** — persistência principal em container Docker (porta `5435`), com suporte a SQLite
- **Prefect 2** — orquestração do pipeline ETL
- **Ruff & Pyright** — linting, formatação e checagem estática de tipos
- **LangGraph 1** — coordenação do fluxo multiagente
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
just test          # Roda a suíte automatizada com Pytest
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
│   │   └── costs.py          # Modelo de custos de transação
│   ├── agents/
│   │   ├── state.py          # Contratos Pydantic + estado compartilhado
│   │   ├── llm_client.py     # Interface de LLM + mock determinístico
│   │   ├── technical_analyst.py
│   │   ├── risk_manager.py
│   │   ├── portfolio_manager.py
│   │   └── graph.py          # Analista → Risco → Portfólio
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
├── tests/                    # Testes automatizados com Pytest
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

## Sistema multiagente

A primeira versão do comitê usa um quorum configurável de **30 analistas técnicos**.
Os pareceres são executados em paralelo e uma compra ou venda só avança quando
a supermaioria de 25/30 concorda. Sem supermaioria, ou se algum voto obrigatório
for inválido, o sinal coletivo é `MANTER`. Para exigir unanimidade, configure
`consensus_threshold=1.0`.

As respostas são validadas por Pydantic e as regras duras de volatilidade,
drawdown e concentração são avaliadas antes do parecer qualitativo de risco.
O fluxo completo pode ser executado sem API externa usando o `MockLLMClient`.

```python
import asyncio

from src.agents import (
    AnalystEnsembleConfig,
    FinalDecision,
    MockLLMClient,
    RiskVerdict,
    TechnicalSignal,
    build_graph,
)

llm = MockLLMClient({
    TechnicalSignal: {
        "signal": "COMPRA",
        "justification": "SMA 50 acima da SMA 200",
        "confidence": 0.7,
    },
    RiskVerdict: {
        "verdict": "APROVADO",
        "analysis": "Risco dentro dos limites",
        "risk_metrics": {},
    },
    FinalDecision: {
        "decision": "COMPRA",
        "position_size": 0.2,
        "reasoning": "Consenso do comitê",
    },
})

graph = build_graph(
    llm,
    ensemble_config=AnalystEnsembleConfig(
        analyst_count=30,
        consensus_threshold=5 / 6,
        require_all_votes=True,
    ),
)

result = asyncio.run(graph.ainvoke({
    "ticker": "WEGE3.SA",
    "date": "2025-01-02",
    "indicators": {"sma_50": 50.0, "sma_200": 45.0},
    "cash": 100_000.0,
    "position": 0.0,
    "current_price": 55.0,
    "equity": 100_000.0,
    "recent_volatility": 0.20,
    "current_drawdown": 0.05,
    "payoff_ratio": 1.0,
    "errors": [],
}))
```

Para o experimento, `AgentBacktestEngine` percorre os pregões sequencialmente,
observa os dados no fechamento de `t` e executa uma decisão aprovada somente na
abertura de `t+1`. O motor aplica custos, atualiza caixa e posição e preserva o
histórico completo do consenso, decisão, execução e erros. A auditoria registra
`as_of`, próxima sessão observada, status, data e preço de execução. A última
previsão acionável permanece `PREDICTED` e não entra nas métricas antes de uma
abertura futura.

```python
from src.backtesting import AgentBacktestEngine

backtest = AgentBacktestEngine(graph, data, ticker="WEGE3.SA")
result = backtest.run()
result.save_audit("data/agent_runs/wege3.json")
```

Uma execução demonstrativa de 60 pregões, com respostas simuladas e auditoria
completa, pode ser iniciada com:

```bash
python scripts/run_agent_backtest.py --ticker WEGE3.SA
```

`CachedLLMClient` e `RetryingLLMClient` podem envolver qualquer cliente real
para reutilizar respostas e tratar falhas transitórias. O cache inclui prompt e
schema na chave, evitando misturar respostas de agentes ou contratos diferentes.

Para usar o cliente HTTP OpenAI-compatible configurável, configure `.env` com:

```ini
LLM_PROVIDER=omnirouter
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=<sua-chave>
LLM_MODEL=openai/gpt-4o-mini
```

O cliente implementado usa o formato OpenAI-compatible de `/chat/completions`;
isso, por si só, não comprova compatibilidade oficial com um provedor específico.
No estado atual ele envia `temperature`, `top_p` e `max_tokens`; a `seed` do
quorum é auditada, mas ainda não é encaminhada ao provedor. Consulte o
[estado atual](docs/ESTADO_ATUAL.md) antes de executar chamadas pagas.

O SQLite legado pode ser reparado com o comando abaixo. Ele se recusa a executar
se já existir um backup e sempre cria `hedgefundlab.db.bak` antes da limpeza:

```bash
python scripts/repair_sqlite_database.py hedgefundlab.db
```

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

> **Nota:** cobertura e qualidade devem ser verificadas no snapshot usado em cada
> execução. O banco auditado cobre os dez tickers desde 2016, mas contém uma barra
> final inválida por ticker; não assuma que o intervalo configurado é a cobertura
> efetiva.

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

Em 08/09/2026, a coleta leve da suíte encontrou **312 testes**. Esse número é
uma fotografia do repositório, não uma garantia de que todos foram executados
nesta reorganização documental.

```powershell
# Executa a suíte de testes
just test

# Executa a checagem estática de estilo (Linter)
just lint
```
