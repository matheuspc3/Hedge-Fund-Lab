# Campanha contínua de seis carteiras v2 (`REPLAY-02`) — abril a novembro de 2026

**Identidade:** `HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2` · **Decisão / Item:** DP-37 / `REPLAY-02` (comparação controlada com `REPLAY-01` v1 sob regras operacionais DP-36) · **Natureza:** reconstrução histórica exploratória produzida após o fechamento do período; não constitui evidência prospectiva nem demonstração de superioridade fora desta trajetória.

Período **2026-04-06 a 2026-11-12** (**153 pregões**, **918 estados diários** = 153 × 6 carteiras). Capital inicial independente de **R$ 100.000,00** por carteira, mesma cesta inicial de entrada (`855 BBAS3`, `461 ITUB4`, `415 PETR4`, `239 VALE3`, `397 WEGE3` a preço de referência de 2026-04-02), ações inteiras, custos operacionais posteriores de **0,03%**, proventos líquidos por componente creditados em caixa na data de pagamento, e as cinco carteiras de referência concluídas antes da inferência paga sob `no_network()`.

Na comparação direta de trajetória idêntica com o `v1`, a **Multiagentes v2** encerrou em **R$ 85.743,57 (-14,2564%)**, melhorando **+R$ 3.564,86 (+3,5649 p.p.)** em relação à Multiagentes v1 (**R$ 82.178,71**, **-17,8213%**), com redução de 55,8% no giro (`38` vs `86` operações pós-entrada) e queda de 35,0% nos custos (`R$ 119,87` vs `R$ 184,40`). Ainda assim, permaneceu **R$ 3.047,54 abaixo do Buy & Hold** (`R$ 88.791,11`, `-11,2089%`) e **R$ 19.143,48 abaixo da Bollinger 20/2** (`R$ 104.887,05`, `+4,8870%`), que manteve o maior patrimônio final da campanha. As cinco carteiras de referência reproduziram **paridade exata até o centavo** entre `v1` e `v2`.

---

## 1. Comparação consolidada das seis carteiras (`v1` vs `v2`)

| Carteira | Versão | Patrimônio final R$ | Retorno % | Caixa R$ | Recebíveis R$ | Custos R$ | Operações pós-entrada (C / V) |
|---|---|---:|---:|---:|---:|---:|---:|
| **Multiagentes** | **v2** | **85.743,57** | **-14,2564** | **39.321,44** | **775,13** | **119,87** | **38 (22 C / 16 V)** |
| Multiagentes | v1 | 82.178,71 | -17,8213 | 1.346,54 | 1.459,03 | 184,40 | 86 (50 C / 36 V) |
| **Buy & Hold** | v1 = v2 | 88.791,11 | -11,2089 | 1.418,18 | 583,45 | 0,00 | 0 (0 / 0) |
| **SMA 50/200** | v1 = v2 | 88.866,68 | -11,1333 | 34.912,62 | 579,70 | 32,23 | 6 (2 / 4) |
| **Bollinger 20/2** | v1 = v2 | 104.887,05 | +4,8870 | 1.507,33 | 8,24 | 151,26 | 24 (12 / 12) |
| **Equal Weight (63d)** | v1 = v2 | 89.869,29 | -10,1307 | 1.423,03 | 623,64 | 5,11 | 15 (9 / 6) |
| **Mínima Variância (252/63)** | v1 = v2 | 95.814,84 | -4,1852 | 1.581,00 | 1.058,91 | 27,94 | 14 (8 / 6) |

- **Paridade das 5 referências (`v1 == v2`):** `BUY_HOLD`, `SMA_50_200`, `BOLLINGER_20_2`, `EQUAL_WEIGHT_63` e `MIN_VARIANCE_252_63` são idênticas em patrimônio, caixa, recebíveis, custos e posições finais (`output/auditoria-replay-v2/comparacao_v1_v2.json`).
- **Posição final Multiagentes v2 (2026-11-12):** `PETR4: 455` ações (`R$ 20.338,50`), `WEGE3: 490` ações (`R$ 25.308,50`), `BBAS3: 0`, `ITUB4: 0`, `VALE3: 0`, mais `R$ 39.321,44` em caixa e `R$ 775,13` em recebíveis líquidos.

---

## 2. Desempenho por ativo e episódios de saída/reentrada

| Ativo | PnL v1 (R$) | PnL v2 (R$) | Delta v2 − v1 (R$) | Preço médio Compra v1 → v2 | Preço médio Venda v1 → v2 | Pregões em carteira v1 → v2 | Qtd final v1 → v2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **PETR4** | -1.783,77 | **+1.812,50** | **+3.596,27** | 44,77 → 41,02 | 42,81 → **54,55** | 133 → **153** | 920 → 455 |
| **ITUB4** | -4.527,86 | -3.802,94 | +724,92 | 44,07 → 42,54 | 40,61 → 40,54 | 74 → 93 | 380 → 0 |
| **WEGE3** | -5.443,38 | -4.858,70 | +584,68 | 47,41 → 47,85 | 44,79 → 44,09 | 109 → 107 | 430 → 490 |
| **VALE3** | -4.433,08 | -4.557,04 | -123,96 | 83,46 → 79,00 | 78,85 → 73,90 | 59 → 82 | 0 → 0 |
| **BBAS3** | -1.633,20 | -2.850,25 | -1.217,05 | 20,99 → 22,24 | 21,31 → 20,67 | 76 → 56 | 13 → 0 |
| **Total** | **-17.821,29** | **-14.256,43** | **+3.564,86** | — | — | — | — |

### Episódios de saída integral e reentrada na Multiagentes v2

Enquanto no `v1` `VALE3` ficou **94 pregões zerada** (até 2026-11-12) após sair em 2026-07-01 sem jamais conseguir reentrar por falta de caixa e veto de rebalanceamento, no `v2`:

- **PETR4 (0 saídas totais, 153 pregões em carteira):** nunca zerou; recebeu uma compra pontual (`180` ações a `R$ 41,02` em 2026-07-28) e realizou **dois cortes parciais `Trim-to-Fund`** (`50` ações a `R$ 49,06` em 2026-09-15 e `90` ações a `R$ 57,60` em 2026-10-15), capturando o rali até outubro e reduzindo a exposição antes da correção de novembro (`R$ 44,70` em 2026-11-12). Resultado: único ativo positivo (**+R$ 1.812,50**, melhora de **+R$ 3.596,27** sobre o `v1`).
- **VALE3 (2 saídas / 1 reentrada):** saiu em `2026-07-15`, reentrou em `2026-09-01` (`340` ações a `R$ 77,87`, reduzindo o período zerado de 94 para **34 pregões**) e voltou a sair em `2026-09-21` (`37` pregões zerada até `2026-11-12`).
- **ITUB4 (3 saídas / 2 reentradas):** `2026-05-25 → 2026-07-08` (31 pregões), `2026-08-17 → 2026-09-10` (17 pregões) e saída sob **regra R7** em `2026-10-27` (12 pregões até o fim).
- **BBAS3 (2 saídas / 1 reentrada):** `2026-05-05 → 2026-09-15` (93 pregões zerada) e saída final sob **regra R7** em `2026-11-09` (4 pregões até o fim).
- **WEGE3 (3 saídas / 3 reentradas):** `2026-05-14 → 2026-07-02` (34 pregões), `2026-07-17 → 2026-07-27` (6 pregões) e `2026-10-27 → 2026-11-05` (6 pregões); apesar do corte de giro, continuou comprando recomposições acima dos preços médios de venda (`R$ 47,85` vs `R$ 44,09`).

---

## 3. Avaliação empírica dos 4 gargalos (`v1` → `v2`)

| Achado v1 | Intervenção v2 | Resultado observado no v1 | Resultado observado no v2 | Veredito empírico |
|---|---|---|---|---|
| **Gargalo 1 — Trava de caixa e proibição de reduzir `MANTER`** | `Trim-to-Fund`: permite `SELL` parcial em `MANTER`/`COMPRA` quando `peso_antes > 25%`, `peso_depois >= 15%` e há `BUY` aprovado ou `peso_antes > 30%` | `0` trims executados; `VALE3` 94d zerada | **2 trims em `PETR4`** (`2026-09-15`: `50` un., peso `32,02% → 29,33%`, `R$ 2.453,00`; `2026-10-15`: `90` un., peso `31,69% → 26,46%`, `R$ 5.184,00`). `VALE3` reentrou em `2026-09-01` | Funcionou com precisão em `PETR4`; gerou preço médio de venda de `R$ 54,55` vs `R$ 42,81` no v1 |
| **Gargalo 2 — Concentração extrema (`77,49%`) e compras "poeira" (`< R$ 2.000`)** | `MAX_ASSET_WEIGHT = 30%` na projeção de `BUY` + `MIN_TRADE_BRL = R$ 2.000,00` com clamping determinístico em `compile_proposal_v2(..., strict=False)` | Pico **77,49%** (`VALE3`), **71,40%** (`PETR4`), `101/153` dias com apenas `<= 2` ativos $\ge 2\%$; **7 compras `< R$ 2.000`** (até `3 BBAS3` / `R$ 66,00`) | Máximo em proposta `BUY`: **29,98%**; máximo após deriva de fechamento: **32,23%** (`WEGE3`). Dias com $\ge 3$ ativos $\ge 2\%$: **`99/153`** (vs `52/153` no v1). **0 compras `< R$ 2.000`**. Clamping atuou em **26 ajustes** (`15 MAX_ASSET_WEIGHT_CAP`, `11 MIN_TRADE_BRL`) | Eliminou 100% da concentração anômala e das ordens residuais; efeito colateral: em carteira com apenas 2 ativos comprados, o teto de 30% deixou >= 40% em caixa ocioso |
| **Gargalo 3 — Simetria do veto de risco bloqueando `VENDA` (`R7`)** | `R7`: `risk_verdict == "VETADO"` (`HARD_ASSET_VOLATILITY_RULE` ou `ADVISORY_LLM`) bloqueia **apenas `BUY`** e preserva `recommendation == "VENDA"` quando há posição | `41` ativo-pregões vetados (`40` determinísticos + `1` LLM), `25` com consenso `VENDA`; **`0` vendas executadas sob veto** | `48` ativo-pregões vetados (`40` determinísticos + `8` LLM), `12` com `VENDA` sob veto; **2 vendas totais executadas sob `HARD_ASSET_VOLATILITY_RULE`**: `ITUB4` em `2026-10-27` (`630` un. a `R$ 42,05` = `R$ 26.491,50`; fechamento final `R$ 41,68`) e `BBAS3` em `2026-11-09` (`330` un. a `R$ 17,31` = `R$ 5.712,30`; fechamento final `R$ 15,48`) | As 2 saídas sob veto evitaram ~**R$ 827,34** líquidos de perda adicional até 12/11 (especialmente `-10,6%` extra em `BBAS3`) |
| **Gargalo 4 — Homogeneidade 5×0 no comitê técnico** | `2 Tendência + 2 Reversão (BB/RSI) + 1 Equilíbrio/Regime`, com limiar de consenso `0,60` | `83,01%` unanimidade `5-0` (`635/765`); `120` divergências tendência vs reversão; RSI médio `COMPRA = 63,17` vs `VENDA = 35,07` (`BUY = 60,51` vs `SELL = 36,06`) | **`15,13%`** unanimidade `5-0` (`115/760`); **`632`** divergências tendência vs reversão; `499` votos `3-2` e `85` sem consenso (`MANTER`). RSI médio **`COMPRA = 57,42`** vs **`VENDA = 38,67`** (`BUY = 58,54` vs `SELL = 40,98`) | Quebrou o viés de manada (`-67,88 p.p.` na unanimidade `5-0`), reduziu o RSI médio de compra em `-5,75` pts e elevou o de venda em `+3,60` pts |

---

## 4. Análise do pregão `2026-06-26` (única lacuna: `152/153`) e reconciliação de chamadas/estados

Embora `summary.json` registre `sessions_completed: 153`, `complete_analysis_days: 152` e `gaps: ["2026-06-26"]`, a reconciliação contábil completa atesta **`918` estados diários** (`153 × 6`, `status: "PASS"` em `audit_replay_v2_comparison.py`):

1. **Causa raiz em `sessions/2026-06-26/`:** na referência `2026-06-25`, quatro ativos (`ITUB4`, `PETR4`, `VALE3`, `WEGE3`) concluíram normalmente o comitê e risco (`MANTER`, `APROVADO` via `ADVISORY_LLM`). Em `BBAS3`, os **5 analistas técnicos** completaram seus votos com `status: "ok"` (`4` votos `VENDA` dos analistas `1..4` e `1` voto `MANTER` do analista `5`), mas a chamada subsequente de risco (`stage: "risk_manager"`, `slot: "L01"`, `sequence: 5`) falhou nas **duas tentativas permitidas** (`attempt_count: 2`, `retry_count: 1`, `duration_ms: 1272.65`) por **`ProviderTransportError`**: `[WinError 10054] Foi forçado o cancelamento de uma conexão existente pelo host remoto`.
2. **Semântica *fail-closed* e contagem exata de chamadas (`4702` lógicas / `4701` com trace / `4711` HTTP):**
   - Teto teórico para 153 pregões: `153 × 31 = 4.743` chamadas.
   - Foram suprimidas `40` chamadas de risco por `HARD_ASSET_VOLATILITY_RULE` (idêntico ao `v1`) **e `1` chamada de gestor em `2026-06-26`** (porque a condição `all(o["status"] == "COMPLETED")` foi falsa após `BBAS3` registrar `failure.json`), totalizando **`4.702` chamadas lógicas** (`4.743 - 40 - 1`).
   - Das `4.702` chamadas lógicas, `4.701` possuem `token_usage` reconciliado (`usageMetadata`) e exatamente **1** (`2026-06-26/BBAS3/L01/5`) ficou com `status: "error"` e `token_usage: null`.
   - Ao longo da campanha ocorreram `9` *retries* lógicos (`8` recuperados na tentativa 2 e `1` esgotado em `2026-06-26/BBAS3/L01/5`), resultando em **`4.711` tentativas físicas HTTP** (`4.702 + 9`) e `10` reservas incertas `UNKNOWN_TRANSPORT` (`8 + 2`, `US$ 0,110592` cada = **`US$ 1,105920`**).
3. **Preservação contábil dos `918` estados:** diante da falha em `2026-06-26`, o motor gravou `day.json` com `status: "NO_ANALYSIS"`, `execution_source: null` e `failure: {"stage": "committee", "tickers": ["BBAS3"]}`, preservou integralmente a posição anterior da Multiagentes (`PETR4: 415`, `VALE3: 335`, caixa `R$ 46.945,27` — até porque `BBAS3` já estava zerada desde `2026-05-05`), não fabricou `HOLD` nem enviou ordens, e marcou as 6 carteiras a mercado no fechamento (`equity: R$ 89.167,68` na Multiagentes).

---

## 5. Auditoria de orçamento, tokens e execução (`PASS`)

- **Janela da execução real:** `2026-11-15 18:33:19` a `23:39:54` (horário de São Paulo, ~5h06m contínuas após conclusão prévia das 5 referências em `$0,00`), sem reset e com resumo idempotente.
- **Orçamento agregado (`cap_usd = US$ 34,78`):** `4.711` tentativas físicas para `4.702` chamadas lógicas (`9` retries, máximo `2` tentativas por chamada). Uso conhecido estimado: **`US$ 8,92490025`**; reserva adicional incerta (`10` `UNKNOWN_TRANSPORT`): **`US$ 1,105920`**; exposição final total: **`US$ 10,03082025`** (pico pré-HTTP: `US$ 10,18479150`). Não representa fatura oficial nem saldo promocional.
- **Tokens reconciliados:** `5.416.162` de entrada + `871.426` de saída + `425.315` de *thinking* = **`6.712.903` tokens totais** (`v1`: `5.909.179`, aumento puxado pelo *thinking* e prompts diferenciados das 3 lentes do comitê). Modelo devolvido: `gemini-3.8-flash` (alias não garante checkpoint imutável).

---

## 6. O que ainda separa a Multiagentes v2 do `Buy & Hold` (`-3.047,54`) e da `Bollinger 20/2` (`-19.143,48`)

1. **Arrasto estrutural de caixa (`cash drag`) induzido pelo teto de 30% somado à queda das aprovações `COMPRA`:** a carteira v2 manteve em média **24,69% do patrimônio em caixa** (vs `12,98%` no `v1`), passou **`65/153` pregões com mais de 30% em caixa** (máximo `67,74%`) e terminou com **45,86% em caixa (`R$ 39.321,44`)**. Com apenas 2 ativos mantidos ao final (`PETR4` e `WEGE3`) e teto rígido de 30% por ativo, pelo menos 40% do capital fica estruturalmente ocioso sem render CDI (`caixa não rende`), enquanto o filtro `2+2+1` reduziu sinais `COMPRA` aprovados de `273` (`v1`) para `106` (`v2`, contra `537 MANTER`).
2. **Assimetria de *timing* entre consenso de tendência e reversão pura (`Bollinger 20/2`):** mesmo após reduzir a compra em topos (`RSI` de compra `63,17 → 57,42`), a Multiagentes ainda vendeu após quedas acumuladas (`RSI` médio de venda `38,67` e `SMA50 gap -7,23%`) e recomprou após confirmação de recuperação (`SMA50 gap +5,16%`), gerando prejuízo líquido em `WEGE3` (`-R$ 4.858,70`), `VALE3` (`-R$ 4.557,04`), `ITUB4` (`-R$ 3.802,94`) e `BBAS3` (`-R$ 2.850,25`). Em contraste, `Bollinger 20/2` (`+4,89%`) comprou sistematicamente nas bandas inferiores (`RSI` extremo baixo) e realizou nas superiores com parcelas fixas de 20%, encerrando comprada nos 5 ativos com apenas `R$ 1.507,33` de caixa.
3. **Ausência de orçamento de alocação residual para ativos elegíveis:** quando 2 ou 3 ativos estão fora da carteira ou vetados, o limite fixo de 30% impede redirecionar capital aos demais ativos aprovados (ou a reserva de caixa não remunerada penaliza comparativamente contra carteiras 100% investidas em janelas sem renda fixa).

---

## 7. Limites, preservação e evidências geradas

- **Limites preservados do contrato `DP-36/37`:** dados/fatores/proventos reconstituídos após o fechamento do período sem arquivo *point-in-time*; cutoff de março/2026 não garante ausência de contaminação do modelo; alias `gemini-3.8-flash` não é imutável; `PREABE` é proxy da abertura sem spread/impacto/D+2; caixa não rende; JCP tributado a 15%.
- **Preservação integral do `v1`:** hashes SHA-256 de `data/replays/april-november-2026-flash/exports/explorer.json` (`88c3a0e1...`) e `calls.json` (`b5ef9585...`) verificados intactos, bem como fontes congeladas `v1`.
- **Artefatos e evidências seladas (`REPLAY-02`):**
  - Execução e exportação: `data/cache/continuous-replay/april-november-2026-flash-v2/` e espelho `data/replays/april-november-2026-flash-v2/exports/` (`explorer.json`, `calls.json`, `manifest.json`, `index.html`, `calls-data.js`, `daily.csv`, `operations.csv`, `decisions.csv`, `dividends.csv`, `calls.csv`).
  - Auditoria comparativa: [comparativo em JSON](../output/auditoria-replay-v2/comparacao_v1_v2.json) e tabelas CSV em [output/auditoria-replay-v2/](../output/auditoria-replay-v2/).
  - Pacote selado final: [output/replay-continuo-v2-20261115/](../output/replay-continuo-v2-20261115/) contendo `comparativo_v1_v2.json`, CSVs derivados, `verificacao.json`, `manifest.json`, `explorador_replay_v2_2026-04_2026-11.zip` e cópia idêntica `relatorio.md`.
- **Próxima etapa:** incorporar o comparativo `REPLAY-01 (v1)` vs `REPLAY-02 (v2)` à monografia do TCC (`TCC-02/03`), explicitando que os 4 ajustes corrigiram os gargalos mecânicos/comportamentais (`+3,56 p.p.` e `+R$ 3.596` em `PETR4`, zero poeira, concentração contida e R7 operacional), mas revelaram o *trade-off* de `cash drag` sob teto rígido de 30% em universo de 5 ações.
