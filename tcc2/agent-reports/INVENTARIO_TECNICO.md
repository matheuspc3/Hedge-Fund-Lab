# Inventário Técnico — Hedge Fund Lab (TCC 2)

> Fonte: leitura do repositório (`src/`, `dashboard/`, `tests/`, `scripts/`,
> `docs/`) e dos documentos científicos (`docs/EXPERIMENT_PROTOCOL.md`,
> `docs/H2_METHODOLOGICAL_FREEZE_V1.md`, `docs/ROADMAP.md`, `docs/ARQUITETURA.md`).
> Data da auditoria: 2026-11-05. Não houve reexecução de experimentos.

## 1. Stack implementado (fato observado no repositório)

| Camada | Tecnologia observada | Observação |
|---|---|---|
| Servidor HTTP | `http.server` (stdlib) + `BaseHTTPRequestHandler` | **Não** é framework web |
| Frontend | HTML/CSS/JS vanilla + Chart.js (`dashboard/`) | `product.css`, `personal-charts.js`, `platform.html` |
| Persistência | SQLite + SQLAlchemy (`src/db`) | **Não** é PostgreSQL |
| Orquestração/agentes | LangGraph multiagente (`src/agents`) | grafo linear acíclico |
| Backtesting | engine próprio (`src/backtesting`) | `metrics.py` em uso |
| Estratégias | `src/strategies` | clássicas + multiagente |
| Indicadores | `src/indicators` | SMA, BB, RSI, MACD |
| Pipeline de dados | `src/pipeline` (incl. `b3_official.py`) | COTAHIST oficial B3 |
| Experimentos | `src/experiments` (incl. `h2_evaluation_*`) | arena/runner H2 |
| Testes | `pytest` (Poetry) | 96 ativos + checks |

**Divergência material com o TCC 1:** o TCC 1 descreve Prefect + PostgreSQL +
yfinance; o código real usa stdlib + SQLite + SQLAlchemy + COTAHIST B3. Ver
`DIFERENCAS_TCC1_TCC2.md`.

## 2. Universo e dados

- **5 ativos** (DP-07, 20% cada): PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA,
  BBAS3.SA. TCC 1 dizia "10 ativos de maior liquidez do Ibovespa".
- **Fonte de preço científica** (Amendamento 1, 2026-10-04): OHLCV bruto oficial
  da B3 (COTAHIST, mercado à vista) × fator de ajuste por sessão do yfinance
  (`Adj Close / Close`). Representação = retorno total ajustado.
- **H_real** = PETR4.SA, snapshot corrigido `20261004T201258177516Z-b4cf39fc…`,
  `|E| = 1519` sessões (2018-01-12 a 2024-02-28), 2649 barras oficiais, READY.
- **Calendário:** `B3Calendar` v2 (regras históricas, equivale às 2649 sessões
  oficiais). v1 errava 14 datas (feriados SP, fim de ano, 20/nov).

## 3. Motor H2 (multiagente LLM) — configuração congelada

Fonte: `docs/H2_METHODOLOGICAL_FREEZE_V1.md` (CONGELADO, 2026-10-04).

- **Método:** `self_consistency` ensemble; `analyst_count=5`;
  `consensus_threshold=0.6`; `require_all_votes=true`. **Atenção:** 5/0.6 é
  aplicado por override explícito na camada de experimento (`src/experiments/
  hardening.py`); os *defaults* de biblioteca (`technical_analyst.py`,
  `participant.py`) são `analyst_count=30` e `consensus_threshold=5/6≈0.833`.
  Qualquer caminho que não sobrescreva cai silenciosamente em 30/5/6.
- **Runtime:** Gemini nativo (`gemini-3.8-flash`), sem fallback;
  `temperature=1.0`; `max_output_tokens=8192`; `decision_frequency=1`;
  `long_target_weight=1.0`; `risk_max_volatility=0.5`; `volatility_window=21`;
  `risk_max_drawdown=0.25`; `retry_attempts=6`; `retry_base_delay=2.0`.
- **Escada de thinking:** LOW → MEDIUM → HIGH (custo), nunca escolhida por
  retorno/Sharpe.
- **Papéis:** Technical / Risk / Portfolio. Não há debate cíclico, reavaliação
  pelo Risco, memória persistente nem sizing pelo PM (só direção; exposição por
  peso alvo determinístico). Grafo linear acíclico.
- **Controle clássico:** SMA + Bollinger + RSI + MACD, score −1/0/+1; RSI Wilder
  canônico, flat=50.
- **Métrica primária congelada (código, `src/backtesting/metrics.py`):** Sharpe
  H2 = `H2_SCIENTIFIC_SHARPE_DEFINITION_V1` (Amendment 5) — `mean(r − rf/252) /
  std(r, ddof=1) · √252`, rf=0.0; convenção de escore 0.0 quando < 2 retornos
  ou volatilidade amostral < 1e-15/NaN (falha fechado para dado corrompido).
  Sortino, turnover e demais métricas de risco permanecem **defaults técnicos
  não congelados** (docstrings explicitam).

## 4. Gates (qualidade de processo, não métrica financeira)

- **G-A** — falhas finais classe A = 0.
- **G-T** — truncamentos MAX_TOKENS = 0.
- **G-I** — `total_hold_rate >= 0.90` → `DEGENERATE_INACTIVE`.
- **G-F** — `SAME_STATE_FLIP_RATE > 0.10` → `DEGENERATE_UNSTABLE`.

## 5. Desenho experimental (Hardening → Freeze → Validação → Teste)

- **Hardening:** H = 8 H_syn + 4 H_real (S=12 estados), R=5 reps, N=5 amostras
  técnicas, ~300 chamadas, sem métrica financeira/liquidação (outcome-blind).
- **Âncoras (DECIDIDO):** CORE = 30 (CAL-A 20 ∪ CAL-B 10, disjuntos);
  STRESS ≤ 8 adicionais (fora do CORE). Estratos cronológicos contíguos, âncora =
  sessão mediana.
- **Subfases CALIBRATION:** DIAGNOSTIC HARDENING → CAL-A → SEQUENTIAL
  DEVELOPMENT → STRESS REPORT → CAL-B → FREEZE. Ordem fixa, autoridades não
  cumulativas.
- **Pseudo-live causal:** decisão em `close(t)`, execução em `open(t+1)`;
  informação posterior a `t` proibida. `settlement_session` liquida a última
  decisão.
- **Modo histórico v1:** `expanding` (nunca rolling). `minimum_history_sessions
  = 504` (obrigatório, sem default). MACD recursivo (`ewm(adjust=False)`).
- **Proveniência:** `git commit` + `spec_hash` + `snapshot_id` + `manifest` +
  `LLM trace`. `phase`/`case_id` não entram no `spec_hash`.

## 6. Bootstrap A (inferência)

Stationary bootstrap temporal pareado, básico centrado, `B=5000`, `α=0.05`,
seed NumPy PCG64 `20261008`, bloco médio 10, rank 4751.

## 7. Calibração ≠ treinamento

O LLM chega pré-treinado, sem fine-tuning. O ajuste é de configuração de sistema
(prompts, papéis, quórum, parâmetros), capturado por `ExperimentSpec` /
`spec_hash` / `commit`.

## 8. Produto / operação (contexto, fora do escopo científico direto)

- D0 = 13/10/2026; R$ 100k por carteira (DP-10); identidade DP-23; backtest
  só com regras determinísticas (DP-31).
- Ciclo diário autônomo DP-34 (Railway, teto US$ 4/dia), logs, `/agents`
  (voto por agente), `/logs` (Atividade e registros).

## 9. Lacunas técnicas a sinalizar (para o redator não afirmar o que não existe)

- Inferência **paga real** não foi executada nesta auditoria; nenhum resultado
  financeiro de H2 foi reexecutado.
- `MockLLMClient` existe para testes/contrato e **não** é avaliação financeira
  real (restrição explícita).
- Janela de VALIDATION e FINAL TEST ainda `TBD`.
- Resultados de CAL-A/CAL-B/B0 citados em docs são históricos e não re-auditados
  aqui.
- **Drift de defaults H2:** freeze §1 registra `analyst_count=5` /
  `consensus_threshold=0.6`, mas os defaults de biblioteca são `30` / `5/6`.
  O valor congelado só vale porque `hardening.py` sobrescreve; verificar se
  CAL-B/SEQUENTIAL/VALIDATION/FINAL TEST passam o override em todos os pontos
  (risco de execução silenciosa com 30 analistas).
