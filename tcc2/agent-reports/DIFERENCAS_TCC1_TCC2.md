# Diferenças entre o TCC 1 e o estado real do TCC 2

> Propósito: impedir que o TCC 2 repita descrições do TCC 1 que não correspondem
> mais ao código/à metodologia. Fonte: `tcc2/source/tcc1/main.tex` vs repositório
> e `docs/`. Auditoria de 2026-11-05.

## 1. Stack e infraestrutura

| Item | TCC 1 (main.tex) | Real (TCC 2) |
|---|---|---|
| Orquestração | Prefect | LangGraph (`src/agents`), grafo linear acíclico |
| Banco | PostgreSQL | SQLite + SQLAlchemy (`src/db`) |
| Servidor | (não detalhado) | `http.server` stdlib |
| Fonte de dados | yfinance | COTAHIST B3 oficial × fator yfinance |
| Frontend | (não detalhado) | vanilla HTML/CSS/JS + Chart.js |

## 2. Universo de ativos

- **TCC 1:** "10 ativos de maior liquidez do Ibovespa".
- **TCC 2:** 5 ativos (PETR4, VALE3, ITUB4, WEGE3, BBAS3), 20% cada (DP-07).

## 3. Janela de dados

- **TCC 1:** "10 anos" para PETR4/WEGE3.
- **TCC 2:** H_real = PETR4.SA 2018-01-12 a 2024-02-28 (`|E|=1519` sessões);
  snapshot corrigido amplia a cobertura bruta a 2016–2026, mas a janela avaliada
  de H_real é a de 2018–2024.

## 4. Hipóteses

Preservadas entre TCC 1 e TCC 2 (devem permanecer idênticas — restrição do
protocolo):

- **H1:** momentum/trend-following superam equal-weight (Sharpe líquido,
  multiasset).
- **H2:** sistema multiagente LLM supera benchmarks (Sharpe líquido primário;
  Sortino, Max Drawdown, turnover complementares).
- **H0:** ausência de diferença estatisticamente significativa.

## 5. Parâmetros de estratégia

- **TCC 1:** SMA 50/200, Bollinger k=2, rebalanceamento trimestral Equal Weight.
- **TCC 2:** controle clássico = SMA + Bollinger + RSI + MACD (score −1/0/+1);
  multiagente = self_consistency (5 analistas, threshold 0.6, require_all_votes).

## 6. Enquadramento metodológico (novo no TCC 2, ausente no TCC 1)

- Calibração de sistema ≠ treinamento (LLM pré-treinado, sem fine-tuning).
- Pseudo-live causal (`close(t)` → `open(t+1)`).
- Gates de qualidade (G-A/G-T/G-I/G-F) e Hardening outcome-blind.
- Âncoras CAL-A/CAL-B/STRESS, FREEZE, VALIDATION/FINAL_TEST ainda `TBD`.

## 7. Estrutura de resultados já antecipada pelo TCC 1

`main.tex` (TCC 1, ~linha 372) já prevê a organização do capítulo de resultados:
tabela de métricas principais, curva de patrimônio e gráfico de drawdown. O TCC 2
deve seguir essa direção, mas **somente** com resultados reais existentes — nunca
mockados.

## 8. Continuidade obrigatória (não é diferença, é contrato)

- Metodologia H2 congelada (`H2_METHODOLOGICAL_FREEZE_V1.md`) não deve ser
  alterada silenciosamente.
- Restrição explícita: **não modificar `tcc2/source/tcc1/`**.
