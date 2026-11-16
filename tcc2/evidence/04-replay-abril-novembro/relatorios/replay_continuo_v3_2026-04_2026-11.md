# Campanha contínua de seis carteiras v3 (`REPLAY-03`) — abril a novembro de 2026

**Identidade:** `HFL-CONTINUOUS-EXPLORATORY-REPLAY-V3` · **Decisão / Item:** DP-37 / `REPLAY-03` (comparação controlada com `REPLAY-01` v1 e `REPLAY-02` v2 sob regras operacionais DP-36) · **Natureza:** reconstrução histórica exploratória produzida após o fechamento do período; não constitui evidência prospectiva nem demonstração de superioridade fora desta trajetória.

Período **2026-04-06 a 2026-11-12** (**153 pregões**, **918 estados diários** = 153 × 6 carteiras). Capital inicial independente de **R$ 100.000,00** por carteira, mesma cesta inicial de entrada (`855 BBAS3`, `461 ITUB4`, `415 PETR4`, `239 VALE3`, `397 WEGE3` a preço de referência de 2026-04-02), ações inteiras, custos operacionais posteriores de **0,03%**, proventos líquidos por componente creditados em caixa na data de pagamento, e as cinco carteiras de referência concluídas antes da inferência paga sob `no_network()`.

Na comparação direta de trajetória idêntica com `v1` e `v2`, a **Multiagentes v3** encerrou em **R$ 100.067,36 (+0,0674%)**, superando a **Multiagentes v1** (`R$ 82.178,71`, `-17,8213%`) em **+R$ 17.888,65 (+17,8887 p.p.)** e a **Multiagentes v2** (`R$ 85.743,57`, `-14,2564%`) em **+R$ 14.323,79 (+14,3238 p.p.)**. A carteira `v3` superou o **Buy & Hold** (`R$ 88.791,11`, `+R$ 11.276,25`), a **SMA 50/200** (`R$ 88.866,68`), o **Equal Weight 63d** (`R$ 89.869,29`) e a **Mínima Variância 252/63** (`R$ 95.814,84`), ficando abaixo apenas da **Bollinger 20/2** (`R$ 104.887,05`, `-R$ 4.819,69`). Pela primeira vez na série, a Multiagentes atingiu **preço médio de venda superior ao preço médio de compra nos 5/5 ativos**, manteve **`0` saídas totais** (todos os 5 ativos $\ge 2\%$ em **153/153 pregões**), capturou **20/20 proventos líquidos** (`R$ 1.425,30`) e inverteu o perfil de execução para **comprar em sobrevenda (`RSI` médio `39,26`) e vender em sobrecompra (`RSI` médio `69,00`)**. As cinco carteiras de referência mantiveram **paridade exata até o centavo** entre `v1`, `v2` e `v3`.

---

## 1. Comparação consolidada das seis carteiras (`v1` vs `v2` vs `v3`)

| Carteira | Versão | Patrimônio final R$ | Retorno % | Caixa R$ | Recebíveis R$ | Custos R$ | Operações pós-entrada (C / V) | Saídas totais |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **Multiagentes** | **v3** | **100.067,36** | **+0,0674** | **751,17** | **283,95** | **120,07** | **81 (29 C / 52 V)** | **0** |
| Multiagentes | v2 | 85.743,57 | -14,2564 | 39.321,44 | 775,13 | 119,87 | 38 (22 C / 16 V) | 10 |
| Multiagentes | v1 | 82.178,71 | -17,8213 | 1.346,54 | 1.459,03 | 184,40 | 86 (50 C / 36 V) | 9 |
| **Buy & Hold** | v1 = v2 = v3 | 88.791,11 | -11,2089 | 1.418,18 | 583,45 | 0,00 | 0 (0 / 0) | 0 |
| **SMA 50/200** | v1 = v2 = v3 | 88.866,68 | -11,1333 | 34.912,62 | 579,70 | 32,23 | 6 (2 / 4) | 4 |
| **Bollinger 20/2** | v1 = v2 = v3 | 104.887,05 | +4,8870 | 1.507,33 | 8,24 | 151,26 | 24 (12 / 12) | 12 |
| **Equal Weight (63d)** | v1 = v2 = v3 | 89.869,29 | -10,1307 | 1.423,03 | 623,64 | 5,11 | 15 (9 / 6) | 0 |
| **Mínima Variância (252/63)** | v1 = v2 = v3 | 95.814,84 | -4,1852 | 1.581,00 | 1.058,91 | 27,94 | 14 (8 / 6) | 1 |

- **Paridade das 5 referências (`v1 == v2 == v3`):** `BUY_HOLD`, `SMA_50_200`, `BOLLINGER_20_2`, `EQUAL_WEIGHT_63` e `MIN_VARIANCE_252_63` são idênticas em patrimônio, caixa, recebíveis, custos e posições finais (`output/auditoria-replay-v3/comparacao_v1_v2_v3.json`).
- **Posição final Multiagentes v3 (2026-11-12):** `BBAS3: 332`, `ITUB4: 166`, `PETR4: 486`, `VALE3: 459`, `WEGE3: 695`, mais `R$ 751,17` em caixa (`0,75%` do patrimônio) e `R$ 283,95` em recebíveis líquidos.

---

## 2. Desempenho por ativo e inversão de preços médios (`v1` → `v2` → `v3`)

| Ativo | PnL v1 (R$) | PnL v2 (R$) | PnL v3 (R$) | Delta v3 − v2 (R$) | Preço médio Compra v2 → v3 | Preço médio Venda v2 → v3 | Pregões em carteira v2 → v3 | Qtd final v3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **PETR4** | -1.783,77 | +1.812,50 | **+3.222,19** | +1.409,69 | 41,02 → 43,18 | 54,55 → **46,43** | 153 → **153** | 486 |
| **WEGE3** | -5.443,38 | -4.858,70 | **+1.991,89** | **+6.850,59** | 47,85 → 48,13 | 44,09 → **48,61** | 107 → **153** | 695 |
| **ITUB4** | -4.527,86 | -3.802,94 | **+1.435,82** | **+5.238,76** | 42,54 → 42,14 | 40,54 → **44,47** | 93 → **153** | 166 |
| **BBAS3** | -1.633,20 | -2.850,25 | -1.997,86 | +852,39 | 22,24 → 20,37 | 20,67 → **21,48** | 56 → **153** | 332 |
| **VALE3** | -4.433,08 | -4.557,04 | -4.584,68 | -27,64 | 79,00 → 75,77 | 73,90 → **81,13** | 82 → **153** | 459 |
| **Total** | **-17.821,29** | **-14.256,43** | **+67,36** | **+14.323,79** | **1/5 > compra** | **5/5 > compra** | **0 saídas totais** | — |

- **Fim dos episódios de saída integral e reentrada tardia:** enquanto `v1` teve `9` saídas totais e `v2` teve `10` (deixando ativos zerados por até 94 pregões e bloqueando recompras), a `v3` registrou **`0` saídas totais** (`episodios_v3.csv` vazio) e manteve **todos os 5 ativos com peso $\ge 2\%$ em `153/153` pregões**.
- **Captura integral de proventos:** por nunca zerar posições antes das datas-com, a Multiagentes v3 recebeu **20/20 eventos de proventos líquidos (`R$ 1.425,30`)**, igualando `BUY_HOLD` e `EQUAL_WEIGHT_63`, contra `9/20` no `v1` (`R$ 567,02`) e `9/20` no `v2` (`R$ 509,28`), elevando o total de eventos de proventos das seis carteiras de `97` (`v1`/`v2`) para `108` (`v3`).
- **Preços médios de venda acima de compra em 5/5 ativos:** o maior salto veio da reversão de `WEGE3` (`-R$ 4.858,70` → `+R$ 1.991,89`, **+R$ 6.850,59**) e `ITUB4` (`-R$ 3.802,94` → `+R$ 1.435,82`, **+R$ 5.238,76**), além de `PETR4` (`+R$ 3.222,19`). Mesmo nos papéis que recuaram no período (`BBAS3` e `VALE3`), o giro tático vendeu mais caro do que recomprou (`R$ 21,48` vs `R$ 20,37` em `BBAS3`; `R$ 81,13` vs `R$ 75,77` em `VALE3`).

---

## 3. Avaliação empírica dos 4 Pilares do `v3` (`v1` → `v2` → `v3`)

| Pilar v3 | Mecanismo implementado | v1 | v2 | v3 | Veredito empírico |
|---|---|---|---|---|---|
| **Pilar 1 — 5 Lentes Especialistas + Guardas de Extremo** | `LENTE_BANDAS_BOLLINGER`, `LENTE_EXAUSTAO_RSI_MACD`, `LENTE_VALOR_RELATIVO_SMA50`, `LENTE_ESTRUTURA_LONGA_SMA200`, `LENTE_ASSIMETRIA_RISCO_RETORNO` + `ANTI_BOTTOM_SELL_GUARD` e `ANTI_TOP_CHASE_GUARD` | Unanimidade `5-0` **83,01%**; `BUY` RSI **60,51** vs `SELL` RSI **36,06** | Unanimidade `5-0` **15,13%**; `BUY` RSI **58,54** vs `SELL` RSI **40,98** | Unanimidade `5-0` **4,03%** (`30/745`); **`715`** divergências; **`BUY` RSI 39,26** vs **`SELL` RSI 69,00**; **`0`** ativações do guarda | Inversão completa do timing: as 5 lentes sozinhas deslocaram `COMPRA` para sobrevenda (`RSI 35,11`, `bb_lower_gap 0,0152`) e `VENDA` para sobrecompra (`RSI 68,96`, `bb_upper_gap -0,0141`), evitando qualquer consenso `3-2` extremo |
| **Pilar 2 — Memória de Posição, Core Floor `8%`, Venda Escalonada `45%` e Anti-Whipsaw `8d`** | `compute_position_memory` no contexto; em `VENDA + APROVADO`, venda máxima `ceil(0,45 * qty)` e piso `>= 8%`; `R7` mantém até `100%` sob `VETADO`; proíbe recompra `<= 8d` acima do último preço de venda | `9` saídas totais; `101/153` dias com $\le 2$ ativos $\ge 2\%$; `9` proventos (`R$ 567,02`) | `10` saídas totais; `99/153` dias com $\ge 3$ ativos $\ge 2\%$; `9` proventos (`R$ 509,28`) | **`0` saídas totais**; **`153/153` dias** com **5/5 ativos** $\ge 2\%$; **`56` ajustes `CORE_FLOOR_STEP_SELL`**; **`20` proventos (`R$ 1.425,30`)** | Impediu liquidação emocional em bloco, manteve a carteira diversificada nos 5 papéis por toda a campanha e transformou `VENDA` em realização escalonada |
| **Pilar 3 — `Trim-on-Strength` & `Trim-to-Fund`** | Permite `SELL` parcial em `MANTER`/`COMPRA` por força (`RSI >= 63` ou `bb_upper_gap >= -0,02`, lucro $\ge 2\%$, peso $> 14\%$, sem exigir `BUY`) ou para financiar `BUY` (`peso > 25%`) | `0` trims; caixa travado | `2` `Trim-to-Fund` em `PETR4` | `0` trims em `MANTER` (`trim_on_strength_executed = []`; `trim_to_fund_executed = []`) | **Descoberta arquitetural:** todas as **52** vendas parciais da `v3` ocorreram já sob consenso técnico **`VENDA` (`APROVADO`, `RSI 69,00`)** dosado por `CORE_FLOOR_STEP_SELL` — o comitê de 5 lentes antecipou a realização antes de precisar do fallback em `MANTER` |
| **Pilar 4 — `Anti-Cash-Drag` (`Dip-Rebalance`) + Limites de Carteira** | Permite `BUY` em `MANTER + APROVADO` descontado até `22%` quando `caixa/PL > 25%`; teto `30%` em `COMPRA`; lote mínimo `R$ 2.000` | Caixa médio `12,98%` (fim `1,64%`); pico `77,49%`; `8` compras `< R$ 2k` | Caixa médio `24,69%` (`65` dias `> 30%`, fim `45,86%`); pico `32,23%`; `0` `< R$ 2k` | Caixa médio **`14,94%`** (`25` dias `> 30%`, fim **`0,75%`**); pico `35,87%`; `0` `< R$ 2k`; **`2` compras `Dip-Rebalance`** (`WEGE3` 17/04, `VALE3` 21/09) + `1` `DIP_REBALANCE_WEIGHT_CAP` | Eliminou o *cash drag* crônico da `v2` (`45,86%` → `0,75%` no fechamento) sem compras residuais (`12 MAX_ASSET_WEIGHT_CAP`, `9 MIN_TRADE_BRL`, `2 INSUFFICIENT_CASH`) |

- **Nota sobre `R7` na `v3`:** dos `46` ativo-pregões com `risk_verdict == "VETADO"`, **`0`** tiveram consenso técnico `VENDA` (`vetoed_venda_technical = 0`, contra `25` no `v1` e `12` no `v2`), pois os picos de volatilidade ocorreram em quedas onde o comitê `v3` deixou de votar `VENDA` no fundo (`BUY` médio `RSI 39,26`).

---

## 4. Análise das 4 lacunas (`2026-07-01`, `2026-09-01`, `2026-10-01`, `2026-10-02`) e integridade das chamadas

Embora `summary.json` registre `sessions_completed: 153`, `complete_analysis_days: 149` e `gaps: ["2026-07-01", "2026-09-01", "2026-10-01", "2026-10-02"]`, **todas as `4.703` chamadas lógicas à API Gemini foram concluídas na primeira tentativa sem erros de transporte** (`retried_logical_calls: 0`, `unknown_attempts: 0`, `calls_with_reconciled_trace_usage: 4703`, todos os `765` pareceres de ativos em `COMPLETED`), e todos os **`918` estados diários** (`153 × 6`) reconciliaram com `status: "PASS"`:

1. **Causa exata em `sessions/<dia>/failure.json` (`stage: "manager_or_execution"`):** as 4 lacunas ocorreram exclusivamente na validação determinística da resposta do LLM gestor em `compile_proposal_v3(..., strict=False)` — após a chamada paga do gestor ter retornado `status: "ok"`:
   - **`2026-07-01`**, **`2026-09-01`** e **`2026-10-02`** (`3` pregões): `manual_portfolio_api.Invalid` (`"Informe um número válido, positivo para preço/quantidade; valores em centavos."`) dentro de `manual.number(a["quantity"], "quantity", units=True)`. Ao constatar que a posição estava abaixo ou próxima do piso do Core Floor de `8%`, o LLM gestor emitiu **`side: "SELL"` com `quantity: "0"`** (em `ITUB4` e `WEGE3` em `2026-07-01`; `PETR4` e `WEGE3` em `2026-09-01`; `PETR4` em `2026-10-02`) em vez de `side: "HOLD", quantity: "0"`. O contrato contábil `b.units("0")` exige inteiro estritamente positivo para `BUY`/`SELL`.
   - **`2026-10-01`** (`1` pregão): `ValueError` (`"manager_complete_unique_universe_required"`). O LLM gestor retornou **duas ações para `PETR4`** (`SELL 58` seguida de `HOLD 0`) e **omitiu `WEGE3`** da lista `actions`.
2. **Semântica *fail-closed* e preservação contábil:** nos 4 pregões, o motor gravou `day.json` com `status: "NO_ANALYSIS"`, `execution_source: null` e `operations: []`, preservando as posições vigentes sem fabricar ordens nem interromper a campanha, e marcou as seis carteiras a mercado no fechamento.
3. **Lição de engenharia para futura `v4`:** em `compile_proposal_v3(..., strict=False)`, normalizar `side in ("BUY", "SELL")` com `quantity == "0"` para `HOLD` antes de `manual.number(..., units=True)` (registrando ajuste `ZERO_QTY_TO_HOLD`) eliminaria `3` das `4` falhas de esquema do gestor.

---

## 5. Auditoria de orçamento, tokens e execução (`PASS`)

- **Janela da execução real:** `2026-11-16 02:59:57` a `08:33:49` (horário de São Paulo; `status.json` finalizado às `08:34:00`, ~5h34m contínuas após conclusão prévia das 5 referências em `$0,00`), sem reset.
- **Orçamento agregado (`cap_usd = US$ 34,78`):** `4.703` tentativas físicas para `4.703` chamadas lógicas (`0` retries, `0` reservas incertas `UNKNOWN_TRANSPORT`). Exposição final = uso conhecido estimado = **`US$ 8,62763550`** (pico pré-HTTP: `US$ 8,78072850`), **US$ 1,40318475 abaixo da exposição do v2** (`US$ 10,03082025`). Não representa fatura oficial nem saldo promocional.
- **Tokens reconciliados:** `5.559.614` de entrada + `808.129` de saída + `380.651` de *thinking* = **`6.748.394` tokens totais** (`v1`: `5.909.179`; `v2`: `6.712.903`). Modelo devolvido: `gemini-3.8-flash` (alias não garante checkpoint imutável).

---

## 6. Limites, preservação e evidências geradas

- **Limites preservados do contrato `DP-36/37`:** dados/fatores/proventos reconstituídos após o fechamento do período sem arquivo *point-in-time*; cutoff de março/2026 não garante ausência de contaminação do modelo; alias `gemini-3.8-flash` não é imutável; `PREABE` é proxy da abertura sem spread/impacto/D+2; caixa não rende; JCP tributado a 15%.
- **Preservação integral de `v1` e `v2`:** hashes SHA-256 verificados intactos para `v1` (`explorer.json` `88c3a0e1...`, `calls.json` `b5ef9585...`) e `v2` (`explorer.json` `4f517224...`, `calls.json` `f5c01345...`), bem como fontes congeladas.
- **Artefatos e evidências seladas (`REPLAY-03`):**
  - Execução e exportação: `data/cache/continuous-replay/april-november-2026-flash-v3/` e espelho `data/replays/april-november-2026-flash-v3/exports/` (`explorer.json` `0df082bd...`, `calls.json`, `manifest.json` `177ed5f6...`, `index.html`, `calls-data.js`, `daily.csv`, `operations.csv`, `decisions.csv`, `dividends.csv`, `calls.csv`).
  - Auditoria comparativa: [comparativo em JSON](../output/auditoria-replay-v3/comparacao_v1_v2_v3.json) e tabelas CSV em [output/auditoria-replay-v3/](../output/auditoria-replay-v3/).
  - Pacote selado final: [output/replay-continuo-v3-20261116/](../output/replay-continuo-v3-20261116/manifest.json) contendo `comparativo_v1_v2_v3.json`, CSVs derivados, `verificacao.json`, `manifest.json`, `explorador_replay_v3_2026-04_2026-11.zip` e cópia idêntica `relatorio.md`.
- **Próxima etapa:** incorporar a evolução empírica `REPLAY-01 (v1)` → `REPLAY-02 (v2)` → `REPLAY-03 (v3)` à monografia do TCC (`TCC-02/03`) e publicar/importar o pacote `v3` no servidor de consulta conforme demanda de Lucas.
