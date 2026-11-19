# Matriz de Evidências — TCC 2

> Rastreabilidade entre afirmações/objetivos e o artefato que as comprova.
> Convenção de status: **VERIFICADO** (lido/confirmado nesta auditoria),
> **HISTÓRICO** (registrado em docs, não reexecutado), **PENDENTE** (sem
> evidência), **TBD** (decisão metodológica não tomada). Nenhum resultado deve
> ser declarado concluído sem apontar o artefato.

## 1. Objetivos e hipóteses

| Afirmação | Evidência | Status |
|---|---|---|
| H1 (momentum > equal-weight) | resultado experimental H1 | PENDENTE (não auditado) |
| H2 (multiagente LLM > benchmarks) | runs H2 de VALIDATION/FINAL_TEST | PENDENTE (janela TBD) |
| H0 (diferença não significativa) | Bootstrap A (`B=5000`, α=0.05) | PENDENTE (não aplicado a resultados) |
| Metodologia H2 congelada | `docs/H2_METHODOLOGICAL_FREEZE_V1.md` | VERIFICADO (texto) |

## 2. Implementação

| Afirmação | Evidência | Status |
|---|---|---|
| Stack = stdlib + SQLite + SQLAlchemy | `src/db`, `dashboard/`, código | VERIFICADO |
| Agentes LangGraph | `src/agents` | VERIFICADO |
| Engine de backtest próprio | `src/backtesting` | VERIFICADO |
| Pipeline COTAHIST oficial | `src/pipeline/b3_official.py` | VERIFICADO |
| Universo 5 ativos 20% | DP-07 (`docs/` direção de produto) | VERIFICADO |
| Fonte de preço = COTAHIST × fator yfinance | PROTOCOL AMENDMENT 1 | VERIFICADO |

## 3. Dados e proveniência

| Afirmação | Evidência | Status |
|---|---|---|
| Conjunto elegível E PETR4.SA: 1519 sessões (12/01/2018 a 28/02/2024); H_real = 4 sessões de diagnóstico (H = 8 H_syn + 4 H_real) | freeze §7 / amendment 1 (sha256) | VERIFICADO (registro) |
| Calendário B3 v2 = 2649 sessões | `docs/evidence/calendar/` | VERIFICADO (registro) |
| `minimum_history_sessions = 504` | EXPERIMENT_PROTOCOL §5.11 | VERIFICADO (texto) |
| `spec_hash`/`snapshot_id`/`manifest`/`LLM trace` | EXPERIMENT_PROTOCOL §5.7 | VERIFICADO (texto) |

## 4. Configuração do sistema (congelada)

| Parâmetro | Evidência | Status |
|---|---|---|
| self_consistency, 5 analistas, 0.6, all_votes | freeze §1 | VERIFICADO |
| gemini-3.8-flash, no fallback | freeze §2 | VERIFICADO |
| temperature/max_tokens/retry/risk limits | freeze §3 | VERIFICADO |
| thinking ladder LOW→HIGH | freeze §4 | VERIFICADO |
| Sharpe H2 congelado (`H2_SCIENTIFIC_SHARPE_DEFINITION_V1`: rf=0, 252, ddof=1, escore 0.0 p/ série degenerada) | `src/backtesting/metrics.py` (Amendment 5) | VERIFICADO (código) |
| Sortino/turnover NÃO congelados como métrica científica | `chapters/05-metodologia.tex` (L61) declara explicitamente | VERIFICADO (decisão documentada) |

## 5. Gates

| Gate | Evidência | Status |
|---|---|---|
| G-A (falha classe A = 0) | freeze §9 | VERIFICADO (definição) |
| G-T (truncamentos = 0) | freeze §9 | VERIFICADO (definição) |
| G-I (hold_rate ≥ 0.90) | freeze §9 | VERIFICADO (definição) |
| G-F (flip_rate > 0.10) | freeze §9 | VERIFICADO (definição) |

## 6. Resultados experimentais históricos

| Afirmação | Evidência | Status |
|---|---|---|
| B0 (baseline estável) PASS | freeze amendment 1 | HISTÓRICO |
| Hardening LOW gates passaram | freeze amendment 1 | HISTÓRICO |
| CAL-A/CAL-B execuções | `docs/ROADMAP.md` (PAPER-02/03) | HISTÓRICO (não reexecutado) |
| Ativação Railway / ciclo diário | `docs/ESTADO_ATUAL.md` | HISTÓRICO |

## 7. Referências bibliográficas (a verificar pelo revisor)

| Chave | Situação |
|---|---|
| `Bailey2017` | RESOLVIDO: chave e ano corrigidos (JCF vol.20 n.4, 2017); citado em 02/03 |
| `Xia2026` | RESOLVIDO: eprint `2605.19337` — PDF em `referencia/05_reinforcement_learning/Agentic Trading When LLM Agents Meet Financial Markets.pdf` |
| `FinCoT2025` | RESOLVIDO: chave e `year=2025` corrigidos; eprint `2506.16123` CONFIRMADO (arXiv cs.CL, v1 2025-06-19; aceito FinNLP-2025/EMNLP, Oral) |
| Demais (Fama1970, Markowitz1952, Sharpe, Sortino, DeMiguel2009, etc.) | canônicas, a conferir formatação |

## 8. Itens sem evidência (não devem ser escritos como conclusão)

- Qualquer resultado numérico de Sharpe/Sortino/MaxDD do H2 (não reauditado).
- Superioridade do agente LLM sobre benchmarks (não demonstrada nesta auditoria).
- Desempenho de `MockLLMClient` como avaliação financeira real (proibido).
