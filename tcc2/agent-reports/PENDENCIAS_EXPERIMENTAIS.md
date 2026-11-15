# Pendências Experimentais — TCC 2

> Itens que precisam ser resolvidos/produzidos antes (ou durante) a redação.
> Marcar com `TODO` no texto quando a evidência ainda não existir; nunca
> preencher com dado mockado.

## 1. Metodologia — decisões ainda `TBD`

1. **Janela de VALIDATION**: proposta v6 `2024-09-02 a 2025-08-29` (05 L84) —
   aguarda aprovação do autor; não tratada como congelada.
2. **Janela de FINAL TEST**: proposta v6 `2025-09-01 a 2026-08-31` (05 L84) —
   aguarda aprovação do autor; não tratada como congelada.
3. **SEQUENTIAL DEVELOPMENT**: RESOLVIDO — `2024-03-01 a 2024-08-30` (05 L84).
4. **Datas de STRESS REPORT**: RESOLVIDO — S1..S4 congeladas (05 L84).
5. **CAL-A**: RESOLVIDO — `risk_max_volatility=0,5`, `volatility_window=21`,
   `risk_max_drawdown=0,25` (05 L34).

## 2. Resultados a obter (não presentes nesta auditoria)

6. **Resultados H1** (momentum/trend-following vs equal-weight, Sharpe líquido
   multiasset) — não auditados. **Bloqueio técnico verificado (2026-11-11):** o
   registry (`src/experiments/participants.py`) expõe apenas dois participantes
   multiasset (`equal_weight`, `min_variance`); todo momentum/trend-following
   (`sma_cross`, `bollinger`, `indicator_family_control`) é single-asset
   (subclasse de `SignalParticipant`, exige `ticker` único, alterna 100%↔caixa
   sobre um ativo). Não existe estratégia multiasset de momentum/trend-following
   implementada — executá-la exigiria código de estratégia novo (decisão
   metodológica do autor + freeze). Falta também materializar o snapshot
   congelado dos 5 ativos (`create_dataset_snapshot`, yfinance
   `auto_adjust=true`): hoje não existe; os dados de produção são ~20 sessões
   de SIMULAÇÃO determinística, não dado científico H1.
7. **Resultados H2** (multiagente LLM vs benchmarks) — dependem de VALIDATION e
   FINAL TEST, ainda `TBD`.
8. **Inferência estatística** (Bootstrap A) aplicada aos resultados reais — ainda
   não aplicável enquanto não houver janela final.
9. **Comparação com benchmarks** (Buy & Hold, equal-weight, controles clássicos) —
   registros históricos existem (Buy & Hold R$ 98.777,70 / Multiagentes
   R$ 99.113,82 em 20/10), mas a comparação científica formal está pendente.

## 3. Bibliografia

10. **RESOLVIDO** `Xia2026` — eprint `2605.19337`, PDF presente em
    `referencia/05_reinforcement_learning/Agentic Trading When LLM Agents Meet Financial Markets.pdf`.
11. **RESOLVIDO** `FinCoT2025` — chave e `year=2025` já corrigidos no `.bib` e nas citações.
12. **RESOLVIDO** `Bailey2017` — chave e ano (JCF 2017) já corrigidos.
13. **RESOLVIDO** — 3 entradas nunca citadas (`Qian2005`, `Sharpe1966`, `Kidd2012`) removidas do `.bib`: `Qian2005` (risk parity, fora de escopo); `Sharpe1966` e `Kidd2012` redundantes com `Sharpe1994` e `Sortino1994`, já citados.

## 4. Limitações / ameaças à validade (obrigatório no TCC 2)

14. **RESOLVIDO** — seção redigida em `05-metodologia.tex` §Ameaças à Validade
    (L107-109): overfitting do pesquisador, validade externa (5 ativos BR),
    custo da inferência paga, single-asset no caminho de agente.
15. **RESOLVIDO** — calibração ≠ treinamento declarada em 05 L78 e L109.

## 5. Conformidade de redação

16. **RESOLVIDO** — `Prefect` e `PostgreSQL` removidos (zero ocorrências nos
    capítulos). `yfinance` permanece **corretamente** como fonte do fator de
    ajuste (Adj Close/Close) em `04-arquitetura.tex` L36 — é a stack real, não leftover.
17. Não apresentar `MockLLMClient` como avaliação financeira real (regra vigente).
18. **RESOLVIDO** — `WRITING_RULES.md` e `PLANO_ESCRITA.md` estão limpos (sem heredoc).

## Ordem sugerida de resolução

Restam: aprovação das janelas de VALIDATION/FINAL TEST (§1 itens 1-2, decisão do
autor) → execução real da inferência e H1 (§2) → conferência de formatação das
referências nunca citadas (§3 item 13). Demais itens já resolvidos.
