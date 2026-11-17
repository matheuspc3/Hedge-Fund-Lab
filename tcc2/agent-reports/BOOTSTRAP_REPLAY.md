# Inferência Bootstrap A no Replay Contínuo Abril–Novembro 2026

Gerado por `tcc2/scripts/bootstrap_replay.py`, que reutiliza sem alteração `bootstrap(frame)` de `src/experiments/h2_evaluation.py` sobre os 153 retornos diários calculados por `tcc2/scripts/metricas_replay.py` (ver `METRICAS_REPLAY.md`). Vínculo: DP-37 / `REPLAY-01..03`, capítulo de resultados.

> **Ressalva.** O Bootstrap A foi especificado para o protocolo H2 v6 (PETR4, fase Final, três execuções LLM contra Buy & Hold). Aqui o mesmo procedimento é reaplicado ao replay, que não é o teste confirmatório congelado: uma única trajetória de 153 pregões, cinco ativos, reconstrução histórica posterior ao período e uma execução por versão (DP-09, DP-31, DP-37).

## 1. O que a função faz

- **Estatística.** Δ̂ = média do Sharpe das colunas `llm_1..3` − Sharpe da coluna `buy_and_hold`, com a definição congelada `H2_SCIENTIFIC_SHARPE_DEFINITION_V1` (`sharpe_components`, rf = 0, √252).
- **Reamostragem.** *Stationary bootstrap* (Politis–Romano) pareado: B = 5000, NumPy PCG64 com semente 20261008 reiniciada a cada chamada, bloco médio 10 (reinício com probabilidade 0,1), índices circulares. A mesma sequência de índices reamostra todas as colunas do quadro, preservando a correlação diária entre as carteiras comparadas.
- **Centragem e hipótese nula.** Raízes eᵦ = Δᵦ* − Δ̂ (bootstrap *basic* centrado). Teste unilateral de superioridade, H0: Δ ≤ 0 contra H1: Δ > 0.
- **p-valor e limite.** p₊ = (1 + #{eᵦ ≥ Δ̂}) / (B + 1); limite inferior unilateral de 95% L₉₅ = Δ̂ − e₍₄₇₅₁₎ (posto 4751, sem interpolação). A função verifica que p₊ < 0,05 ⇔ L₉₅ > 0.
- **Regra de decisão.** Superioridade (rejeição de H0) somente se a estatística for estimável, Δ̂ > 0, p₊ < 0,05 e L₉₅ > 0. Série ou *draw* degenerado (volatilidade nula) torna o resultado inconclusivo, sem refazer *draws*.

## 2. Montagem do quadro (adaptação)

A função exige exatamente as colunas `buy_and_hold, llm_1, llm_2, llm_3`. Para cada comparação A vs B, a referência B ocupa `buy_and_hold` e a carteira A é repetida nas três colunas `llm_*`; logo Δ̂ = Sharpe(A) − Sharpe(B). A repetição é necessária porque o replay tem uma execução por versão (R = 1): a variabilidade entre chamadas do modelo, coberta parcialmente pelo protocolo com R = 3, não é representada. Nenhum código em `src/` foi alterado.

Como complemento **exploratório** (fora da regra congelada), a função é chamada também com os papéis trocados (B contra A). Isso dá p₋, o p-valor unilateral de inferioridade (H0: Δ ≥ 0), e o limite superior U₉₅ = −L₉₅(B vs A) = Δ̂ − e₍₂₅₀₎. [L₉₅; U₉₅] é um intervalo bilateral de 90%.

## 3. Resultados

Δ = diferença de Sharpe anualizado (A − B), 153 retornos diários pareados. Holm: ajuste de Holm sobre p₊ dentro de cada família de cinco referências.

| Hipótese | A | B | Δ Sharpe | L₉₅ | U₉₅ | p₊ | p₊ Holm | p₋ (explor.) | Decisão (α = 0,05) |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| H1 | SMA 50/200 | Equal Weight 63d | -0,71 | -1,75 | 0,31 | 0,881 | 0,881 | 0,119 | Não rejeita H0 |
| H2 · v1 (pré-especificada) | Multiagentes v1 | Buy & Hold | -0,50 | -1,76 | 0,93 | 0,728 | 1,000 | 0,272 | Não rejeita H0 |
| H2 · v1 (pré-especificada) | Multiagentes v1 | SMA 50/200 | 0,14 | -1,32 | 1,76 | 0,432 | 1,000 | 0,568 | Não rejeita H0 |
| H2 · v1 (pré-especificada) | Multiagentes v1 | Bollinger 20/2 | -2,00 | -4,47 | 0,41 | 0,917 | 1,000 | 0,084 | Não rejeita H0 |
| H2 · v1 (pré-especificada) | Multiagentes v1 | Equal Weight 63d | -0,57 | -1,88 | 0,88 | 0,753 | 1,000 | 0,248 | Não rejeita H0 |
| H2 · v1 (pré-especificada) | Multiagentes v1 | Mínima Variância 252/63 | -0,96 | -2,27 | 0,29 | 0,899 | 1,000 | 0,102 | Não rejeita H0 |
| H2 · v2 (exploratória) | Multiagentes v2 | Buy & Hold | -0,44 | -1,34 | 0,83 | 0,714 | 1,000 | 0,286 | Não rejeita H0 |
| H2 · v2 (exploratória) | Multiagentes v2 | SMA 50/200 | 0,20 | -1,02 | 1,69 | 0,347 | 1,000 | 0,653 | Não rejeita H0 |
| H2 · v2 (exploratória) | Multiagentes v2 | Bollinger 20/2 | -1,94 | -4,27 | 0,31 | 0,917 | 1,000 | 0,083 | Não rejeita H0 |
| H2 · v2 (exploratória) | Multiagentes v2 | Equal Weight 63d | -0,51 | -1,46 | 0,77 | 0,747 | 1,000 | 0,253 | Não rejeita H0 |
| H2 · v2 (exploratória) | Multiagentes v2 | Mínima Variância 252/63 | -0,90 | -1,96 | 0,22 | 0,912 | 1,000 | 0,088 | Não rejeita H0 |
| H2 · v3 (exploratória) | Multiagentes v3 | Buy & Hold | 0,86 | -0,30 | 2,13 | 0,108 | 0,432 | 0,892 | Não rejeita H0 |
| H2 · v3 (exploratória) | Multiagentes v3 | SMA 50/200 | 1,50 | 0,25 | 3,02 | 0,024 | 0,121 | 0,976 | Critério numérico atingido, só descritivo; não após Holm |
| H2 · v3 (exploratória) | Multiagentes v3 | Bollinger 20/2 | -0,64 | -1,79 | 0,59 | 0,812 | 0,812 | 0,188 | Não rejeita H0 |
| H2 · v3 (exploratória) | Multiagentes v3 | Equal Weight 63d | 0,79 | -0,34 | 2,00 | 0,122 | 0,432 | 0,878 | Não rejeita H0 |
| H2 · v3 (exploratória) | Multiagentes v3 | Mínima Variância 252/63 | 0,40 | -1,09 | 1,77 | 0,334 | 0,668 | 0,666 | Não rejeita H0 |

Todas as 16 comparações usaram a mesma sequência de índices (SHA-256 `b488ef5d5a1cd64c…`), nenhuma teve *draw* degenerado.

## 4. Interpretação

- **H1 (SMA 50/200 vs Equal Weight 63d).** Δ̂ = -0,71: o Sharpe do SMA foi menor, não maior. A regra de superioridade não se aplica (Δ̂ < 0, p₊ = 0,881); H0 não é rejeitada. O intervalo de 90% [-1,75; 0,31] contém zero, portanto também não há evidência de inferioridade.
- **H2 · v1 (execução pré-especificada).** Única versão cujas regras foram fixadas antes de observar o período; é a leitura que conta para H2. Nenhuma das cinco comparações atinge superioridade; H0 não é rejeitada, com ou sem Holm.
- **H2 · v2 e v3 (iterações exploratórias).** Desenhadas depois de observar as auditorias da v1 (e da v2) no mesmo período. Seus p-valores são otimistas por construção (seleção dentro da amostra, *garden of forking paths*). A v2 não atinge superioridade em nenhuma comparação. A v3 atinge a regra bruta em uma única comparação, contra o SMA 50/200 (Δ̂ = 1,50, p₊ = 0,024, L₉₅ = 0,25), justamente a referência de pior Sharpe no período; o resultado não sobrevive ao ajuste de Holm na família da v3 (p₊ ajustado = 0,121) e, pela origem exploratória da v3, não constitui evidência confirmatória. Contra Buy & Hold, Equal Weight, Mínima Variância e Bollinger, a v3 nem atinge o critério numérico. Como v2 e v3 não recebem decisão inferencial (Cap. 5), nenhum desses valores rejeita H0.
- **Inferioridade (exploratório, p₋ < 0,05):** nenhuma.
- **Multiplicidade.** A regra primária congelada é unilateral, comparação a comparação, a α = 0,05, e não foi trocada; Holm é mostrado apenas como leitura complementar. Na v1 (família pré-especificada) nenhuma p₊ bruta fica abaixo de 0,05, logo o ajuste não muda nada; o único efeito do Holm é retirar o critério bruto atingido pela v3 contra o SMA. Observe-se que "superior a todas as referências" é um teste de interseção–união, que dispensa ajuste e não é atendido por nenhuma versão; "superior a pelo menos uma" é o caso que exige ajuste.
- **Conclusão.** No replay, os dados não permitem rejeitar H0 para H1 nem para H2 na execução pré-especificada (v1). O único critério bruto atingido (v3 vs SMA 50/200) vem de uma iteração exploratória, é só descritivo e não resiste ao controle de multiplicidade. Não rejeitar H0 não prova igualdade: os intervalos de 90% têm amplitude de 2,1 a 4,9 pontos de Sharpe, e diferenças economicamente grandes não se distinguem de ruído. Sortino, máximo drawdown e giro (`METRICAS_REPLAY.md`) permanecem descritivos; a função não faz inferência sobre eles.

## 5. Limitações

- **Amostra única.** 153 retornos diários de uma única trajetória de mercado e cinco ativos; o bootstrap trata a incerteza amostral dessa série, não a de outros regimes ou períodos. A aproximação supõe estacionariedade e dependência fraca; o bloco 10 não tem optimalidade demonstrada; o *basic* não studentizado não é teste exato.
- **Possível contaminação.** O modelo foi executado depois do fechamento do período e pode conhecer o desfecho (motivo da DP-31; reaberta de forma limitada e exploratória pela DP-37). Mesmo um resultado favorável não seria evidência prospectiva.
- **Iterações dentro da amostra.** v2 e v3 foram projetadas a partir das auditorias da mesma janela; seus resultados não são independentes da v1 nem dos dados usados para avaliá-las.
- **R = 1.** Uma execução por versão; a variabilidade entre chamadas do modelo não entra no intervalo.
- **rf = 0.** Sharpe sem taxa livre de risco, coerente com o caixa não remunerado do replay; com rf > 0 todos os índices cairiam.

## 6. Verificações executadas (asserts do script)

- Asserts de `metricas_replay.py` (dados, referências idênticas, valores do documento mestre) passam na importação.
- Δ̂ da função igual à diferença dos Sharpe de `metricas_replay.py`; estado `ESTIMABLE` e zero *draws* degenerados em todas as execuções.
- Reprodutibilidade: duas chamadas com a mesma semente dão resultados idênticos (incluindo os hashes de índices e raízes); todas as execuções compartilham os mesmos índices; p₊ + p₋ = (B + 2)/(B + 1) a menos de empates; Holm conferido num exemplo manual.
