# Plano de Desenvolvimento: Hedge-fund-lab

> **HISTÓRICO — NÃO USAR COMO PLANEJAMENTO ATIVO OU ESTADO ATUAL.** Este plano
> inicial foi substituído por [`../ROADMAP.md`](../ROADMAP.md). O conteúdo abaixo
> foi preservado para rastreabilidade.

## Contexto

O **Hedge-fund-lab** é um laboratório quantitativo de backtesting baseado em sistemas multiagentes, proposto no TCC de Lucas Pereira da Silva e Matheus Pereira de Carvalho (orientação: Eduardo S. Ogasawara). O repositório atual contém apenas o texto do TCC em LaTeX — **nenhuma linha de código foi escrita ainda**. Este plano organiza a implementação completa do artefato computacional descrito no Capítulo 4 do `main.tex`.

**Objetivo**: Construir um ambiente experimental que integre pipeline de dados (Prefect + PostgreSQL), estratégias clássicas (Buy and Hold, Equal Weight, SMA Cross, Bollinger Bands, Mínima Variância) e um comitê de agentes LLM (LangGraph) para comparar desempenho ajustado ao risco nos ativos PETR4 e WEGE3.

**Time**: Dupla (Matheus + Lucas) — tarefas podem rodar em paralelo.

**Stack**: Python, yfinance, PostgreSQL, Prefect, LangGraph, LLM a definir (interface abstrata para o modelo).

**Filosofia de teste**: TDD sempre que possível. Cada módulo tem cobertura >= 95%. Nenhuma função de IO ou cálculo fica sem teste. Testes rodam em CI a cada push.

**Prazo**: Agosto 2026 – Janeiro 2027 (6 meses, conforme cronograma do TCC).

---

## Fase 0 — Setup do Projeto (1 semana, Agosto)

### 0.1 Estrutura do repositório
```
hedge-fund-lab/
├── pyproject.toml              # Dependências e metadados do projeto
├── .env.example                # Variáveis de ambiente (DB URL, API keys)
├── docker-compose.yml          # PostgreSQL + app (opcional)
├── Makefile (ou taskfile)      # Comandos: test, lint, run-pipeline, run-experiment
├── conftest.py                 # Fixtures globais do pytest
├── data/
│   └── raw/                    # Cache local dos CSVs (fallback)
├── src/
│   ├── __init__.py
│   ├── config.py               # Config centralizada (pydantic-settings)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy ORM (ativos, cotacoes_diarias, indicadores)
│   │   └── connection.py       # Engine e sessão
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── extract.py          # yfinance download com retry
│   │   ├── transform.py        # Limpeza + indicadores (pandas)
│   │   ├── load.py             # Batch insert no PostgreSQL
│   │   └── flows.py            # Prefect flows (orquestração)
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── sma.py
│   │   ├── bollinger.py
│   │   ├── rsi.py
│   │   └── macd.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py             # Interface abstrata de estratégia
│   │   ├── buy_and_hold.py
│   │   ├── equal_weight.py
│   │   ├── sma_cross.py
│   │   ├── bollinger_bands.py
│   │   └── min_variance.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py            # Estado do grafo (typed dict)
│   │   ├── technical_analyst.py
│   │   ├── risk_manager.py
│   │   ├── portfolio_manager.py
│   │   ├── graph.py            # LangGraph (compilação do grafo)
│   │   └── llm_client.py      # Interface abstrata para o LLM
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── engine.py           # Loop principal de backtesting
│   │   ├── metrics.py          # Sharpe, Sortino, MaxDD, Turnover
│   │   └── costs.py            # Modelo de custos de transação
│   └── evaluation/
│       ├── __init__.py
│       ├── experiment.py       # Orchestrador do experimento completo
│       └── experiment_config.py
├── tests/
│   ├── conftest.py             # Fixtures compartilhadas (dados sintéticos, mock DB)
│   ├── indicators/
│   │   ├── conftest.py
│   │   ├── test_sma.py
│   │   ├── test_bollinger.py
│   │   ├── test_rsi.py
│   │   └── test_macd.py
│   ├── strategies/
│   │   ├── conftest.py
│   │   ├── test_buy_and_hold.py
│   │   ├── test_equal_weight.py
│   │   ├── test_sma_cross.py
│   │   ├── test_bollinger_bands.py
│   │   └── test_min_variance.py
│   ├── pipeline/
│   │   ├── test_extract.py
│   │   ├── test_transform.py
│   │   ├── test_load.py
│   │   └── test_flows.py
│   ├── backtesting/
│   │   ├── test_engine.py
│   │   ├── test_metrics.py
│   │   └── test_costs.py
│   ├── agents/
│   │   ├── test_technical_analyst.py
│   │   ├── test_risk_manager.py
│   │   ├── test_portfolio_manager.py
│   │   ├── test_graph.py
│   │   └── test_state.py
│   └── evaluation/
│       ├── test_experiment.py
│       └── test_experiment_config.py
├── notebooks/
│   ├── 01_exploratory.ipynb
│   └── 02_results.ipynb
├── dashboard/                  # Dashboard de validação (prototype)
│   ├── index.html
│   ├── app.js
│   └── style.css
└── scripts/
    ├── run_pipeline.sh
    └── run_experiment.sh
```

### 0.2 Dependências principais (`pyproject.toml`)
- `python >= 3.11`
- `yfinance`
- `pandas`, `numpy`, `scipy`
- `sqlalchemy`, `psycopg2-binary` (ou `asyncpg`)
- `prefect`
- `langgraph`, `langchain-core`
- `pydantic-settings`
- `pytest`, `pytest-cov`, `pytest-mock`
- `hypothesis` (testes baseados em propriedades)
- `responses` (mock de chamadas HTTP)
- `matplotlib`, `seaborn` (visualização)
- `jupyter`
- `httpx` (para servir dashboard local)

### 0.3 Configuração de CI/CD (GitHub Actions)
```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: hedgefundlab_test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src --cov-fail-under=95 tests/
```

### 0.4 Atribuição (dupla)
| Tarefa | Resp. |
|---|---|
| pyproject.toml + dependências | Matheus |
| Docker Compose + GitHub Actions | Lucas |
| conftest.py global + fixtures de dados sintéticos | Matheus |
| Makefile (test, lint, run-*) | Lucas |

---

## Fase 1 — Pipeline de Dados (2 semanas, Agosto)

**Filosofia**: Toda função de IO tem mock nos testes. Nenhuma chamada real a yfinance ou PostgreSQL acontece durante os testes unitários.

### 1.1 Modelagem do Banco

```python
# src/db/models.py
class Ativo(Base):
    __tablename__ = "ativos"
    id: int
    ticker: str          # PETR4, WEGE3
    setor: str
    created_at: datetime

class CotacaoDiaria(Base):
    __tablename__ = "cotacoes_diarias"
    id: int
    ativo_id: int (FK)
    data: date
    abertura: float
    maxima: float
    minima: float
    fechamento: float
    volume: float

class IndicadorTecnico(Base):
    __tablename__ = "indicadores_tecnicos"
    id: int
    ativo_id: int (FK)
    data: date
    sma_50: float | None
    sma_200: float | None
    bb_upper: float | None
    bb_middle: float | None
    bb_lower: float | None
    rsi: float | None
    macd: float | None
    macd_sinal: float | None
```

#### Testes necessários:

**test_models.py** (criar junto com models.py):
- Testar que `Ativo`, `CotacaoDiaria`, `IndicadorTecnico` criam instâncias com campos corretos
- Testar constraints (FK, NOT NULL, unique)
- Testar que `data` é date e não datetime
- Testar que valores negativos em cotacoes levantam erro de validação

### 1.2 Módulo de Extração (`extract.py`)

```python
class DataExtractor:
    def __init__(self, retry_policy: RetryPolicy = RetryPolicy()):
        ...

    def download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        # usa yfinance internamente
        ...
```

#### Testes (`test_extract.py`):
- **Mock completo**: usar `responses` ou `unittest.mock` para mockar `yfinance.download()`. Testar que retorna DataFrame com colunas esperadas
- **Retry**: mockar falha nas 2 primeiras chamadas, sucesso na 3ª. Verificar que `download()` eventualmente retorna dados
- **Falha permanente**: mockar falha em todas as tentativas. Verificar que exceção é levantada
- **Dados mínimos**: verificar que DataFrame com < 252 linhas (1 ano) emite warning
- **Ticker inválido**: verificar erro para ticker inexistente
- **Cache**: testar que salva CSV em `data/raw/` e que chamadas subsequentes usam o cache

### 1.3 Módulo de Transformação (`transform.py`)

```python
class DataTransformer:
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # forward-fill, drop linhas inválidas
        ...

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # SMA, BB, RSI, MACD
        ...
```

#### Testes (`test_transform.py`):
- **Clean**: DataFrame com NaN → forward-fill funciona
- **Clean**: DataFrame com linha toda NaN → linha removida
- **Clean**: DataFrame vazio → retorna vazio (edge case)
- **Clean**: datas fora de ordem → reordena ou levanta erro
- **Indicators**: dados sintéticos (preços conhecidos) → valores de SMA batem com cálculo manual
- **Indicators**: Bollinger Bands com k=2 → banda média = SMA, bandas laterais = SMA ± 2σ
- **Indicators**: RSI com 14 períodos em série monotônica crescente → RSI = 100
- **Indicators**: RSI em série monotônica decrescente → RSI = 0
- **Indicators**: MACD com dados constantes → MACD = 0, sinal = 0
- **Indicators**: MACD com cruzamento conhecido → verificar valor exato
- **Indicators**: dados insuficientes para SMA 200 → SMA = NaN
- **Property-based (hypothesis)**: para qualquer série de entrada, SMA ∈ [min, max], RSI ∈ [0, 100]

### 1.4 Robustez de Serialização JSON

Após calcular indicadores (SMA, BB, RSI, MACD), os DataFrames contêm `NaN` nos períodos de aquecimento (*warm-up*) — por exemplo, SMA 200 só produz valores a partir do 200º pregão. Ao exportar para JSON (seja para o dashboard, uma API ou arquivo), `json.dump()` quebra com `ValueError: Out of range float values are not JSON compliant` se encontrar `NaN` ou `Inf`.

**Solução validada no protótipo:**

```python
# 1. Converte para lista de dicionários
records = df.to_dict(orient="records")

# 2. Sanitiza cada valor
def sanitize(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v

for record in records:
    for k in record:
        record[k] = sanitize(record[k])

# 3. Serializa (agora seguro)
json.dump(records, f, ensure_ascii=False)
```

**⚠️ Armadilhas comuns:**

- `df.replace({np.nan: None})` **não funciona** — pandas converte `None` de volta para `NaN` internamente durante a operação. A lista `records` gerada por `to_dict()` ainda conterá `NaN` como `float('nan')`.
- `df.where(df.notna(), None)` tem o mesmo problema.
- `df.dropna()` remove linhas inteiras, não apenas os campos problemáticos — perde dados válidos na mesma linha.
- A iteração manual com `math.isnan()` + `math.isinf()` é a única abordagem que garante que `NaN` vire `null` no JSON.

**Testes necessários (`test_transform.py`, seção de serialização):**

- DataFrame com `NaN` → saída JSON sem `NaN` (todos os valores são `float`, `None`, ou `int`)
- DataFrame com `float('inf')` → campo convertido para `None`
- DataFrame com todos os valores normais → serialização não altera valores
- DataFrame vazio → array vazio `[]`

### 1.5 Módulo de Carga (`load.py`)

```python
class DataLoader:
    def __init__(self, session_factory: Callable[[], Session]):
        ...

    def batch_insert(self, df: pd.DataFrame, batch_size: int = 1000):
        ...
```

#### Testes (`test_load.py`):
- **Batch insert**: mockar SQLAlchemy session. Verificar que `session.add_all()` é chamado com número correto de batches
- **Batch insert**: DataFrame vazio → nenhuma chamada a `add_all()`
- **Upsert**: inserir registro duplicado → não quebra (ON CONFLICT DO NOTHING)
- **Rollback**: se batch falha no meio → verificar que `session.rollback()` foi chamado
- **Integridade pós-carga**: verificar count de registros inseridos

### 1.6 Orquestração Prefect (`flows.py`)

```python
@flow(name="pipeline-etl", retries=3, retry_delay_seconds=30)
def pipeline_etl(tickers: list[str], start: str, end: str):
    ...
```

#### Testes (`test_flows.py`):
- **Flow completo**: mockar extract, transform, load. Verificar que flow completa sem erro
- **Retry**: mockar extract com falha → verificar que Prefect tenta novamente
- **Logging**: verificar que logs são emitidos em cada etapa
- **Flow parameters**: testar com diferentes tickers, datas

### 1.7 Atribuição (dupla)
| Tarefa | Testes | Resp. |
|---|---|---|
| Models DB + connection | test_models.py | Lucas |
| Extract + cache | test_extract.py | Matheus |
| Transform (clean + indicators) | test_transform.py | Matheus |
| Load + upsert | test_load.py | Lucas |
| Prefect flows | test_flows.py | Lucas |

---

## Fase 2 — Indicadores Técnicos e Estratégias Clássicas (2 semanas, Setembro)

**Filosofia**: Toda função de indicador é pura (input série → output série). Testar contra valores calculados manualmente em planilha. Estratégias são testadas com dados sintéticos onde o sinal esperado é conhecido.

### 2.1 Módulo de Indicadores (`src/indicators/`)

Cada indicador é uma função pura:
```python
def sma(series: pd.Series, window: int) -> pd.Series: ...
def bollinger_bands(series: pd.Series, window: int, k: float) -> tuple[pd.Series, pd.Series, pd.Series]: ...
def rsi(series: pd.Series, period: int) -> pd.Series: ...
def macd(series: pd.Series, fast: int, slow: int, signal: int) -> tuple[pd.Series, pd.Series]: ...
```

#### Testes para cada indicador:

**test_sma.py**:
- SMA de [1,2,3,4,5] com window=3 → [NaN, NaN, 2, 3, 4]
- SMA de série constante → constante
- SMA com window=1 → própria série
- SMA com window maior que a série → tudo NaN
- SMA com window=0 → ValueError
- Property: SMA(window=n) de série constante C = C

**test_bollinger.py**:
- Dados sintéticos: preço = [100]*50 + [150] → BB_middle = SMA, BB_upper > SMA > BB_lower
- k=0 → upper = lower = middle
- k negativo → ValueError
- Se preço está acima de BB_upper → sinal de venda
- Se preço está abaixo de BB_lower → sinal de compra
- Property: para k>0, upper >= middle >= lower sempre

**test_rsi.py**:
- Série crescente pura → RSI = 100 (últimos valores aproximam 100)
- Série decrescente pura → RSI = 0
- Série constante → RSI = 50
- RSI com dados conhecidos do Wilder (ex: livro original) → valor exato
- Property: RSI sempre ∈ [0, 100]

**test_macd.py**:
- Série constante → MACD = 0, Signal = 0
- Série crescente → MACD positivo
- Série decrescente → MACD negativo
- Cruzamento conhecido → data do crossover correta
- Property: MACD com fast > slow → ValueError

### 2.2 Interface Abstrata de Estratégia (`src/strategies/base.py`)

```python
class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Retorna sinais: 1 (comprar), -1 (vender), 0 (manter)"""
        ...

    @abstractmethod
    def get_name(self) -> str: ...
```

#### Testes:
- Estratégia concreta inválida (sem implementar generate_signals) → TypeError ao instanciar
- Estratégia que retorna sinais em índice diferente do input → ValueError

### 2.3 Implementação das Estratégias

| Estratégia | Lógica | Testes-chave |
|---|---|---|
| Buy and Hold | Compra no T0, nunca vende | Sinal = [1, 0, 0, ..., 0]; testar com 0 ativos, 1 ativo, N ativos |
| Equal Weight | Rebalanceamento trimestral (1/N) | Pesos somam 1; testar com 1 ativo (peso=1), N ativos (peso=1/N); testar que rebalanceamento só ocorre nas datas certas |
| SMA Cross | Compra se SMA50 > SMA200, vende se contrário | Sem cruzamento → MANTER; cruzamento para cima → COMPRA; cruzamento para baixo → VENDA |
| Bollinger Bands | Compra se preço < BB_lower, vende se > BB_upper, MANTER no meio | Preço > upper → VENDA; preço < lower → COMPRA; preço entre bandas → MANTER |
| Mínima Variância | Min var com janela rolante | Pesos otimizados somam 1; sem restrição de short → pesos podem ser negativos; com restrição → pesos >= 0 |

#### Testes comuns a todas as estratégias (`test_strategies/conftest.py`):
- Fixture `synthetic_price_data()` — DataFrame com 500 dias de preços sintéticos (senoide + ruído)
- Fixture `empty_data()` — DataFrame vazio
- Fixture `single_row_data()` — DataFrame com 1 linha

#### Testes específicos:
- **Sinal consistente**: mesma entrada → mesma saída (determinismo)
- **NaN handling**: se dados contêm NaN, estratégia não quebra
- **Frequência**: dados diários, semanais, mensais → estratégia adapta
- **Property-based**: para qualquer série de preços, sinais ∈ {-1, 0, 1}

### 2.4 Atribuição (dupla)
| Tarefa | Testes | Resp. |
|---|---|---|
| SMA + Bollinger Bands | test_sma.py, test_bollinger.py | Matheus |
| RSI + MACD | test_rsi.py, test_macd.py | Lucas |
| Buy and Hold + Equal Weight | test_buy_and_hold.py, test_equal_weight.py | Lucas |
| SMA Cross + Bollinger Bands strategy | test_sma_cross.py, test_bollinger_bands.py | Matheus |
| Mínima Variância | test_min_variance.py | Matheus |

---

## Fase 3 — Backtesting Engine (3 semanas, Setembro–Outubro)

**Filosofia**: O motor de backtesting é a peça mais crítica do sistema. Cada caminho de execução deve ser testado. Nenhum viés de look-ahead ou survivor bias passa despercebido.

### 3.1 Motor de Backtesting (`src/backtesting/engine.py`)

```python
@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: list[Trade]
    metrics: Metrics

class BacktestEngine:
    def __init__(self, strategy: Strategy, data: pd.DataFrame,
                 initial_capital: float, cost_model: CostModel):
        ...

    def run(self) -> BacktestResult:
        # Para cada dia t:
        #   1. Atualiza dados disponíveis até t (sem informação futura!)
        #   2. Gera sinal (strategy.generate_signals)
        #   3. Executa trade se sinal mudou
        #   4. Aplica custos de transação
        #   5. Atualiza portfólio
        #   6. Registra equity
        ...
```

#### Testes (`test_engine.py`):

**Testes de corretude**:
- **Look-ahead bias**: executar engine com dados conhecidos. Verificar que o engine não usa `data[t+1]` em nenhum momento. Teste: injetar um spike em t+50 e verificar que a decisão em t=49 não reflete o spike.
- **Ordem de execução**: comprar, depois vender, depois comprar de novo → sequência correta de trades
- **Capital inicial**: começar com R$ 100.000 → equity_curve[0] = 100.000
- **Zero trades**: estratégia que sempre retorna MANTER → equity_curve constante (só com custos)
- **Compra total**: sinal COMPRA com position_size=1.0 → todo capital convertido em ativos
- **Venda total**: sinal VENDA com position_size=1.0 → todos ativos convertidos em cash
- **Venda a descoberto**: (se permitido) → position_size negativo

**Testes de borda**:
- DataFrame vazio → levanta exceção clara
- Dados com apenas 1 linha → execução não quebra
- Capital inicial = 0 → trades não executam
- Estratégia que retorna posição maior que o capital → truncado ou erro
- Preço = 0 → divisão por zero? Trade não executado?

**Testes de integração com estratégias específicas**:
- Buy and Hold em dados sintéticos: equity final = preço_final / preço_inicial * capital_inicial
- Equal Weight com 1 ativo = Buy and Hold
- SMA Cross em tendência clara: deve lucrar

**Testes de custos**:
- CostModel com brokerage=0, spread=0 → retorno líquido = retorno bruto
- CostModel com brokerage=10, spread=0 → cada trade custa R$ 10
- CostModel com spread=50bps → trade de R$ 1000 custa R$ 5
- turnover = 0 → sem custo
- turnover alto → custo alto (estratégias ativas penalizadas)

**Property-based**:
- `equity_curve` é não-crescente apenas se todas as trades perdem
- `max_drawdown` <= 0 (é uma perda)

### 3.2 Métricas (`src/backtesting/metrics.py`)

| Métrica | Função |
|---|---|
| Sharpe Ratio | `sharpe_ratio(returns, rf=0.0, freq=252)` |
| Sortino Ratio | `sortino_ratio(returns, rf=0.0, mar=0.0, freq=252)` |
| Maximum Drawdown | `max_drawdown(equity_curve)` |
| Drawdown Duration | `max_drawdown_duration(equity_curve)` |
| Turnover | `turnover(weights_series)` |
| Retorno Acumulado | `cumulative_return(equity_curve)` |
| Volatilidade Anualizada | `annualized_volatility(returns, freq=252)` |
| Calmar Ratio | `calmar_ratio(returns, max_dd, freq=252)` |

#### Testes (`test_metrics.py`):

**Sharpe Ratio**:
- Retornos constantes = 0 → Sharpe = 0
- Retornos positivos constantes → Sharpe infinito (vol=0) → trata divisão por zero
- Retornos com rf > retorno médio → Sharpe negativo
- Calcular manualmente para 5 retornos conhecidos → bater com função
- Property: Sharpe com rf > max(returns) < Sharpe com rf=0

**Sortino Ratio**:
- Retornos todos positivos → Sortino infinito (downside deviation = 0)
- Retornos simétricos (+x e -x) → Sortino < Sharpe
- Calcular manualmente → bater

**Maximum Drawdown**:
- Série monotônica crescente → drawdown = 0
- Série: [100, 90, 80, 110] → max_drawdown = -20%
- Série: [100, 120, 110, 130] → max_drawdown = max(0, -8.33%) → corrigir: é -8.33% do pico 120
- Série constante → drawdown = 0
- Série vazia → ValueError

**Turnover**:
- Pesos constantes → 0
- De [1,0] para [0,1] → turnover = 2
- De [0.5, 0.5] para [0.5, 0.5] → turnover = 0

### 3.3 Modelo de Custos (`src/backtesting/costs.py`)

```python
@dataclass
class CostModel:
    brokerage_fixed: float       # Corretagem fixa por ordem (R$)
    spread_bps: float            # Spread em basis points
    tax_rate: float              # Emolumentos / impostos (%)

    def apply_buy(self, trade_value: float) -> float:
        """Retorna o custo total de uma compra"""
        ...

    def apply_sell(self, trade_value: float) -> float:
        """Retorna o custo total de uma venda"""
        ...
```

#### Testes (`test_costs.py`):
- CostModel tudo zero → custo = 0
- brokerage_fixed = 10 → compra de R$ 1000 custa R$ 10
- spread_bps = 50 → compra de R$ 1000 custa R$ 5
- tax_rate = 0.03% → compra de R$ 1000 custa R$ 0.30
- Custos combinados (brokerage + spread + tax) → soma correta
- trade_value = 0 → custo = brokerage_fixed apenas
- trade_value negativo → ValueError

### 3.4 Atribuição (dupla)
| Tarefa | Testes | Resp. |
|---|---|---|
| Engine principal + validação anti-look-ahead | test_engine.py | **Matheus** |
| Métricas (Sharpe, Sortino, MaxDD, etc.) | test_metrics.py | **Lucas** |
| Modelo de custos | test_costs.py | **Lucas** |
| Testes de integração (engine + estratégias) | test_engine.py (parte 2) | **Ambos** |

---

## Fase 4 — Sistema Multiagente LangGraph (4 semanas, Outubro)

**Filosofia**: O LLM NUNCA é chamado nos testes unitários. Toda interação com o modelo é mockada com respostas deterministicas. O grafo, o roteamento, o state management e a lógica de decisão são testados exaustivamente com fixtures de input conhecido.

### 4.1 Definição do Estado do Grafo (`src/agents/state.py`)

```python
class TechnicalSignal(TypedDict):
    signal: Literal["COMPRA", "VENDA", "MANTER"]
    justification: str
    confidence: float  # 0.0 a 1.0

class RiskVerdict(TypedDict):
    verdict: Literal["APROVADO", "VETADO"]
    analysis: str
    risk_metrics: dict

class FinalDecision(TypedDict):
    decision: Literal["COMPRA", "VENDA", "MANTER"]
    position_size: float  # 0.0 a 1.0
    reasoning: str

class AgentState(TypedDict):
    ticker: str
    date: str
    indicators: dict           # indicadores técnicos atuais
    cash: float
    position: float            # qtde de ativos em carteira
    current_price: float
    technical_signal: TechnicalSignal | None
    risk_verdict: RiskVerdict | None
    final_decision: FinalDecision | None
    errors: list[str]
```

#### Testes (`test_state.py`):
- AgentState pode ser criado com valores default
- Todos os campos opcionais aceitam None
- technical_signal.signal só aceita "COMPRA", "VENDA", "MANTER" → TypeError se string inválida
- position_size ∈ [0.0, 1.0] → ValueError fora do intervalo
- confidence ∈ [0.0, 1.0] → ValueError fora do intervalo

### 4.2 Abstração do LLM (`src/agents/llm_client.py`)

```python
class LLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None
    ) -> BaseModel | str: ...

class MockLLMClient(LLMClient):
    """Retorna respostas pré-definidas. USADO NOS TESTES."""
    def __init__(self, responses: dict[str, Any]):
        self.responses = responses

    async def generate(self, ...):
        return self.responses.get(user_prompt[:50], "MANTER")
```

Implementações futuras (fora do escopo dos testes unitários):
- `OpenAILLMClient`
- `AnthropicLLMClient`
- `DeepSeekLLMClient`

#### Testes (`test_llm_client.py`):
- `MockLLMClient` retorna resposta configurada
- `MockLLMClient` com resposta não configurada → fallback padrão
- Verificar que `generate()` é async → retorna coroutine

### 4.3 Agente Analista Técnico (`technical_analyst.py`)

```python
def create_technical_analyst_node(llm: LLMClient):
    async def node(state: AgentState) -> dict:
        prompt = build_prompt(state)
        response = await llm.generate(SYSTEM_PROMPT_ANALYST, prompt, TechnicalSignal)
        return {"technical_signal": response}
    return node
```

#### Testes (`test_technical_analyst.py`):
**Sem mock de LLM (apenas lógica auxiliar)**:
- `build_prompt(indicators, price)` → string contendo os valores dos indicadores
- `build_prompt(indicators_vazios)` → string indicando que dados estão ausentes
- `parse_indicators_from_state(state)` → dicionário limpo sem chaves extras

**Com MockLLMClient**:
- Mock retorna COMPRA → state.technical_signal.signal == "COMPRA"
- Mock retorna VENDA → state.technical_signal.signal == "VENDA"
- Mock retorna MANTER → state.technical_signal.signal == "MANTER"
- Mock retorna JSON inválido → state.errors contém erro de parse
- State sem indicadores → agente emite erro e retorna MANTER por segurança
- State com preço ausente → agente emite erro

**Testes de integração do prompt** (sem mock):
- Verificar que o prompt contém "COMPRA, VENDA ou MANTER"
- Verificar que o prompt contém instrução para ignorar notícias externas
- Verificar que o prompt contém os valores numéricos dos indicadores

### 4.4 Agente Gestor de Risco (`risk_manager.py`)

```python
class RiskManager:
    def __init__(self, config: RiskConfig, llm: LLMClient):
        self.config = config
        self.llm = llm

    async def evaluate(self, state: AgentState) -> dict:
        # 1. Verificar regras duras (HARD rules — mesmo sem LLM)
        if self._exceeds_volatility_threshold(state):
            return {"risk_verdict": {"verdict": "VETADO", "analysis": "Volatilidade acima do limite", ...}}
        # 2. Se passou regras duras, consultar LLM para análise qualitativa
        response = await self.llm.generate(...)
        return {"risk_verdict": response}
```

#### Testes (`test_risk_manager.py`):

**Regras duras (sem LLM)**:
- Volatilidade > threshold configurado → VETADO automático
- Drawdown atual > max_drawdown_limite → VETADO automático
- Posição atual + nova posição > limite de concentração → VETADO
- Volatilidade normal → passa para análise LLM
- Thresholds configuráveis via `RiskConfig`

**Com MockLLMClient**:
- LLM retorna APROVADO → state.risk_verdict.verdict == "APROVADO"
- LLM retorna VETADO → state.risk_verdict.verdict == "VETADO"

**Regras duras vs LLM**:
- Volatilidade > threshold + LLM retorna APROVADO → regra dura prevalece (VETADO)
- Testar ordem de avaliação: regras duras primeiro, LLM depois

**Edge cases**:
- state sem dados de volatilidade → VETADO por precaução
- state sem position atual → trata como posição = 0
- Config com limites extremos (threshold=0 ou threshold=inf)

### 4.5 Agente Gestor de Portfólio (`portfolio_manager.py`)

```python
def create_portfolio_manager_node(llm: LLMClient):
    async def node(state: AgentState) -> dict:
        # 1. Calcular position sizing máximo via Kelly (ou fractional Kelly)
        max_size = calculate_kelly_size(state)
        # 2. Consultar LLM para decisão final
        response = await llm.generate(..., {"max_position_size": max_size})
        # 3. Limitar ao Kelly calculado
        final_size = min(response["position_size"], max_size)
        return {"final_decision": {"decision": response["decision"], "position_size": final_size}}
    return node
```

#### Testes (`test_portfolio_manager.py`):

**Cálculo de position sizing (Kelly)**:
- Kelly com probabilidade = 0.6, odds = 1:1 → f* = 0.2
- Kelly com probabilidade = 0.5, odds = 1:1 → f* = 0 (nenhuma vantagem)
- Kelly com probabilidade < 0.5, odds = 1:1 → f* < 0 (não apostar)
- Fractional Kelly (f* / 2) → metade do Kelly cheio
- Kelly com capital pequeno → position_size mínimo respeitado

**Com MockLLMClient**:
- LLM retorna decisão dentro do Kelly → posição = decision.position_size
- LLM retorna position_size = 0.8, Kelly max = 0.5 → posição limitada a 0.5
- LLM retorna MANTER → position_size = 0
- LLM retorna COMPRA com cash = 0 → position_size = 0

**Edge cases**:
- state sem cash → position_size = 0
- state com erro do risk_manager → MANTER forçado
- price ausente → não calcula posição

### 4.6 Compilação do Grafo (`graph.py`)

```python
def build_graph(llm_client: LLMClient) -> CompiledGraph:
    builder = StateGraph(AgentState)
    builder.add_node("technical_analyst", create_technical_analyst_node(llm_client))
    builder.add_node("risk_manager", create_risk_manager_node(llm_client))
    builder.add_node("portfolio_manager", create_portfolio_manager_node(llm_client))
    builder.add_edge("technical_analyst", "risk_manager")
    builder.add_conditional_edges(
        "risk_manager",
        lambda s: "portfolio_manager" if s["risk_verdict"]["verdict"] == "APROVADO" else "__end__",
        {"portfolio_manager": "portfolio_manager", "__end__": "__end__"}
    )
    builder.add_edge("portfolio_manager", "__end__")
    builder.set_entry_point("technical_analyst")
    return builder.compile()
```

#### Testes (`test_graph.py`):

**Roteamento**:
- Analista → Risco → APROVADO → Portfólio → fim: 3 nós visitados
- Analista → Risco → VETADO → fim: apenas 2 nós visitados

**Fluxo completo (com MockLLMClient)**:
- Mock configurado: Analista=COMPRA, Risco=APROVADO, Portfólio=COMPRA → state.final_decision.decision == "COMPRA"
- Mock: Analista=COMPRA, Risco=VETADO → state.final_decision é None
- Mock: Analista=MANTER → Risco processa mesmo assim → Portfólio decide

**State integrity**:
- Após execução, state deve conter todos os campos preenchidos (ou None para os que não foram)
- errors list acumula erros sem quebrar o grafo
- Grafo executa mesmo com indicadores parciais

**Performance**:
- Grafo compila sem erros
- Execução de 100 chamadas com mock < 1 segundo

### 4.7 Testes de Integração dos Agentes

- Rodar grafo completo com dados históricos reais (1 dia) sem mock
- Verificar que output é bem formatado
- Testar com dados de PETR4 em dia de alta volatilidade
- Testar com dados de WEGE3 em tendência

### 4.8 Atribuição (dupla)
| Tarefa | Testes | Resp. |
|---|---|---|
| AgentState + validação | test_state.py | **Lucas** |
| Interface LLM + MockLLMClient | test_llm_client.py | **Matheus** |
| Agente Analista Técnico | test_technical_analyst.py | **Lucas** |
| Agente Gestor de Risco | test_risk_manager.py | **Matheus** |
| Agente Gestor de Portfólio (Kelly) | test_portfolio_manager.py | **Matheus** |
| Grafo LangGraph + roteamento | test_graph.py | **Lucas** |
| Testes de integração (sem mock) | — | **Ambos** |

---

## Fase 5 — Experimento e Avaliação (4 semanas, Novembro)

**Filosofia**: O experimento é um script que orquestra a execução de todas as estratégias + sistema multiagente. Cada etapa do experimento tem saída verificável.

### 5.1 Divisão dos Dados

```python
TRAIN = ("2016-01-01", "2019-12-31")   # 4 anos
VAL   = ("2020-01-01", "2021-12-31")   # 2 anos
TEST  = ("2022-01-01", "2025-12-31")   # 4 anos (out-of-sample)
```

#### Testes:
- Períodos não se sobrepõem
- Períodos cobrem todo o intervalo
- Datas mal formatadas → erro
- train_end <= val_start <= test_start

### 5.2 Orchestrador do Experimento (`src/evaluation/experiment.py`)

```python
@dataclass
class ExperimentResult:
    strategy_name: str
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    turnover: float
    cumulative_return: float
    equity_curve: pd.Series
    trades: list[Trade]

class Experiment:
    def run_all(self) -> list[ExperimentResult]:
        # Para cada estratégia:
        #   1. Treina no período de treino (se aplicável)
        #   2. Valida no período de validação
        #   3. Testa no período de teste
        #   4. Coleta métricas
        ...
```

#### Testes (`test_experiment.py`):
- `run_all()` retorna resultados para todas as estratégias configuradas
- Resultados são comparáveis (mesmo período, mesmas métricas)
- Estratégia não configurada → não entra no resultado
- ExperimentResult contém equity_curve com datas alinhadas

### 5.3 Walk-Forward Analysis

```python
class WalkForwardAnalysis:
    def __init__(self, window_train: int, window_test: int):
        ...

    def run(self, data: pd.DataFrame, strategy: Strategy) -> list[ExperimentResult]:
        # Janela rolante de treino/teste
        ...
```

#### Testes:
- window_train + window_test <= total de dados
- Resultados não usam dados futuros em cada janela
- Número de janelas = floor((total - window_train) / window_test)

### 5.4 Pipeline de Hipóteses

```python
def test_hypothesis_h1(results: pd.DataFrame) -> dict:
    """H1: momentum/trend > equal weight"""
    ...

def test_hypothesis_h2(results: pd.DataFrame) -> dict:
    """H2: multi-agent > all benchmarks"""
    ...
```

#### Testes:
- H1 com dados onde momentum < equal weight → retorna "não rejeita H0"
- H1 com dados onde momentum > equal weight → retorna "evidência a favor de H1"
- H2 com agentes piores que benchmarks → "não rejeita H0"

### 5.5 Tabela de Resultados

Output principal (CSV):
```csv
strategy,sharpe_ratio,sortino_ratio,max_drawdown,turnover,cumulative_return
Buy and Hold,0.45,0.52,-0.35,0.0,1.82
Equal Weight,0.52,0.61,-0.28,0.12,1.95
SMA Cross,0.38,0.44,-0.42,0.45,1.55
Bollinger Bands,0.41,0.48,-0.38,0.52,1.72
Min Variance,0.55,0.63,-0.25,0.08,2.01
Multi-Agent LLM,0.62,0.71,-0.22,0.35,2.15
```

### 5.6 Atribuição (dupla)
| Tarefa | Testes | Resp. |
|---|---|---|
| Experiment orchestrator | test_experiment.py | **Matheus** |
| Walk-forward analysis | (testes no mesmo módulo) | **Lucas** |
| Testes de hipóteses H1/H2 | test_hypotheses.py | **Matheus** |
| Pipeline completo rodando | — | **Ambos** |

---

## Fase 6 — Análise e Visualização (3 semanas, Novembro–Dezembro)

### 6.1 Notebook de Resultados (`notebooks/02_results.ipynb`)
- Tabela principal com todas as métricas por estratégia
- Gráfico de evolução patrimonial líquida (multi-agent vs benchmarks)
- Gráfico de drawdown comparativo
- Gráfico de turnover por estratégia
- Análise de sensibilidade: Sharpe ratio em função do custo de transação

### 6.2 Outputs esperados
```
resultados/
├── tabela_metricas.csv
├── equity_curve.png
├── drawdown.png
├── turnover_comparison.png
└── sensibilidade_custos.png
```

### 6.3 Análise Estatística
- Teste de diferença de Sharpe ratios (Jobson-Korkie ou Ledoit-Wolf)
- Análise de consistência por subperíodos
- Verificação de robustness: variar custos (±50%) e verificar se ranking das estratégias se mantém

### 6.4 Atribuição (dupla)
| Tarefa | Resp. |
|---|---|
| Notebook com gráficos e tabelas | **Lucas** |
| Análise estatística (teste de Sharpe) | **Matheus** |
| Análise de sensibilidade | **Lucas** |
| Relatório de resultados | **Matheus** |

---

## Fase 7 — Escrita e Preparação da Defesa (Dezembro–Janeiro)

### 7.1 Atualização do main.tex
- Substituir seções \verify{} e \remarks{} pelos resultados reais
- Preencher Capítulo 5 com resultados empíricos
- Adicionar tabelas e figuras geradas
- Escrever discussão comparando com literatura

### 7.2 Slides de Defesa
1. Problema e motivação (2 slides)
2. Fundamentação teórica (1 slide)
3. Arquitetura: pipeline de dados (1 slide)
4. Arquitetura: sistema multiagente (2 slides)
5. Resultados: tabela de métricas (1 slide)
6. Resultados: gráficos (2 slides)
7. Discussão e limitações (1 slide)
8. Conclusão e trabalhos futuros (1 slide)

### 7.3 Atribuição (dupla)
| Tarefa | Resp. |
|---|---|
| Atualização do TCC com resultados | **Matheus** (texto), **Lucas** (revisão) |
| Figuras e tabelas | **Lucas** |
| Slides | **Lucas** |
| Preparação da defesa | **Ambos** |

---

## Cronograma Consolidado

| Fase | Atividade | Início | Fim | Semanas |
|---|---|---|---|---|
| 0 | Setup + CI + test infrastructure | 03/ago | 07/ago | 1 |
| 1 | Pipeline de dados (com testes) | 10/ago | 21/ago | 2 |
| 2 | Indicadores + Estratégias (com testes) | 24/ago | 04/set | 2 |
| 3 | Backtesting Engine (com testes) | 07/set | 25/set | 3 |
| 4 | Sistema Multiagente (com testes) | 28/set | 23/out | 4 |
| 5 | Experimento | 26/out | 20/nov | 4 |
| 6 | Análise e visualização | 23/nov | 11/dez | 3 |
| 7 | Escrita + defesa | 14/dez | 29/jan | 6 |

---

## Marcos de Verificação (Milestones)

| # | Checkpoint | O que deve estar pronto | Critério de aceitação | Data |
|---|---|---|---|---|
| M1 | Pipeline OK | Pipeline ETL + testes | `pytest tests/pipeline/ --cov=src.pipeline --cov-fail-under=95` passa | 21/ago |
| M2 | Benchmarks OK | 5 estratégias + indicadores + testes | `pytest tests/indicators/ tests/strategies/ --cov=src.indicators --cov=src.strategies --cov-fail-under=95` | 04/set |
| M3 | Engine validado | Backtest engine + métricas + custos + testes | `pytest tests/backtesting/ --cov=src.backtesting --cov-fail-under=95` | 25/set |
| M4 | Agentes OK | LangGraph + 3 agentes com MockLLM + testes | `pytest tests/agents/ --cov=src.agents --cov-fail-under=95` | 23/out |
| M5 | Experimento completo | Todas estratégias + agentes rodam no período de teste | Script `run_experiment.sh` produz `tabela_metricas.csv` | 20/nov |
| M6 | Resultados consolidados | Tabelas, gráficos e análise estatística | Notebook gera todas as figuras | 11/dez |
| M7 | TCC finalizado | main.tex atualizado, defesa preparada | Entrega do TCC + apresentação | 29/jan |

---

## Riscos e Mitigação

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| LLM API cara ou lenta | Média | Alto | MockLLMClient para testes; cache LRU de respostas; fractional Kelly reduz calls; DeepSeek como fallback barato |
| LangGraph com LLM lento demais para 10 anos | Alta | Médio | Execução paralela de dias independentes; batch de calls; testar com 1 ano primeiro e escalar |
| Overfitting nos prompts do agente | Média | Alto | Período de teste isolado (nunca visto pelos agentes); rodar experimento cego 1x e congelar prompts |
| Dados yfinance inconsistentes | Baixa | Médio | Fallback pra CSV; validação de integridade pós-download; comparar PETR4 com fonte alternativa |
| Complexidade LangGraph + async | Alta | Alto | Prototipar agente single-LLM primeiro (sem grafo); adicionar LangGraph depois |
| Testes quebram no CI | Média | Baixo | Pré-commit hooks (pytest antes de push); CI roda em PR blocker |
| Dupla com ritmos diferentes | Média | Médio | Milestones quinzenais; branches separados por feature; code review aos pares |

---

## Estratégia de Teste — Resumo

| Camada | Tipo de teste | Framework | Cobertura alvo | Mock de IO? |
|---|---|---|---|---|
| Indicadores | Unitário (funções puras) | pytest + hypothesis | 100% | N/A (puras) |
| Estratégias | Unitário + integração | pytest | 100% | Sim (dados sintéticos) |
| Pipeline (extract) | Unitário + integração | pytest + responses | 95% | Sim (mock yfinance) |
| Pipeline (load) | Unitário | pytest + unittest.mock | 95% | Sim (mock SQLAlchemy) |
| Pipeline (flows) | Integração | pytest + Prefect test harness | 90% | Sim (mock extract/load) |
| Backtest Engine | Unitário + property | pytest + hypothesis | 100% | Sim (dados sintéticos) |
| Métricas | Unitário | pytest | 100% | N/A (funções matemáticas) |
| Agent State | Unitário | pytest | 100% | N/A (validação de tipos) |
| Agentes (lógica) | Unitário | pytest | 100% | Sim (MockLLMClient) |
| Agentes (LLM) | Integração | pytest | — | Não (teste manual opcional) |
| Grafo (roteamento) | Unitário | pytest | 100% | Sim (MockLLMClient) |
| Experimento | Integração | pytest | 90% | Sim (mock engine) |

**Regra de ouro**: se uma linha de código faz IO ou contém lógica condicional, ela TEM um teste. Se é uma função pura com math, ela TEM hypothesis-based test. Se é um agente LLM, ele TEM mock. Se é o grafo, ele TEM teste de roteamento.
