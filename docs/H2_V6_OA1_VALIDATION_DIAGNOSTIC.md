# H2 v6 — Diagnóstico retrospectivo exploratório da Validation provisória OA-1

> **ANÁLISE RETROSPECTIVA EXPLORATÓRIA — POST-VALIDATION H2-V6-OA1.**
> A Validation analisada é provisória, autorizada só pelo autor e **não ratificada
> academicamente** (`AUTHOR_PROVISIONAL_OPERATIONAL — NOT ACADEMICALLY RATIFIED`).
> Este documento **não** é resultado científico. Ele **não** altera protocolo, tratamento,
> parâmetros, artifacts nem hashes, **não** avalia regra alternativa e **não** seleciona
> estratégia. Nenhum achado daqui autoriza tuning, reclassificação ou Final Test, que
> continua bloqueado.

| Item | Valor |
|---|---|
| Objetivo | Explicar, só com os artifacts selados, por que L01–L03 ficaram abaixo do Buy & Hold |
| Data | 2026-10-09 (America/Sao_Paulo); branch `#1-Update`, HEAD `bb9d202` |
| Identidade analisada | plano `2808fe83f2a4…`; manifesto candidato `dc118ce9…`; checkpoint `docs/evidence/h2_v6_provisional/VALIDATION_PROVISIONAL_CHECKPOINT.json` (SHA-256 `b87b9f66…`) |
| Fonte única de dados | `data/runs/h2_v6_provisional/VALIDATION` |
| Verificação reproduzível | [`scripts/h2_v6_oa1_validation_diagnostic.py`](../scripts/h2_v6_oa1_validation_diagnostic.py), somente leitura, cerca de 6 s |

Legenda: **[F]** fato demonstrado pelos artifacts selados (os achados da §1 e das §§5, 6, 8, 9
e 10 são `assert`s ou saídas do script; as demais tabelas citam os arquivos de origem);
**[H]** hipótese ou interpretação não demonstrada; **[L]** limitação de evidência.

## 0. Método e o que não foi feito

- **[F] Integridade.** Os 31 arquivos fixados no checkpoint conferem por SHA-256, e
  `validation_release.json` confere com `validation_release.sha256.json`.
  `evaluation.sqlite` e `provider.sqlite` foram abertos só como `?mode=ro&immutable=1`.
  Os SHA-256 dos 60 arquivos do diretório foram registrados antes e depois da análise e são
  idênticos (§13).
- **Fora do escopo, por instrução:** nenhuma chamada à Gemini, nenhuma reexecução ou replay,
  nenhum participante instanciado. O snapshot **não foi aberto** porque vai até 2026-08-31
  e, portanto, contém o período do Final Test.
- **[F] Preços.** Os fechamentos de 2024-09-03 a 2025-08-29 vêm da curva selada do
  Buy & Hold: `close(t) = (patrimônio_B&H(t) − caixa) / quantidade`, com caixa residual de
  1,4e-12. As aberturas só são conhecidas nos dias com execução (`trades.csv`). Os fechamentos
  derivados coincidem com os implícitos nas curvas B&H de 0/10/20 bps (|Δ| ≤ 7e-15). Com eles,
  as 15 curvas de patrimônio são reconstruídas a partir dos trades com erro relativo < 1e-12,
  e todo custo é exatamente `nocional × (spread + 0,032%)`.
- **Código consultado só para interpretar campos:** `src/agents/{participant,risk_manager,portfolio_manager,technical_analyst,llm_trace}.py`,
  `src/backtesting/{arena,metrics}.py`, `src/experiments/h2_evaluation*.py`.
- **[F] Nota de método.** Ler `equity.csv` com o parser padrão do pandas gera ruído de cerca de
  1e-14 nas métricas. O projeto lê com `float_precision="round_trip"`, e com essa leitura todas
  as igualdades deste documento valem bit a bit.

Mecânica do tratamento, conforme `manifest.json` (PETR4.SA; `long_target_weight=1.0`):
decisão no fechamento de *t* e ordem na abertura de *t+1*. COMPRA leva a 100% do patrimônio,
VENDA a 0% e MANTER não gera ordem. O custo é 5 bps + 0,032% do nocional. Há 5 analistas com
`temperature=1.0` e consenso ≥ 3/5. Risk: `max_volatility=0,50`, `max_drawdown=0,25`,
`max_concentration=1,0`.

## 1. Síntese dos achados

1. **[F] A diferença para o B&H vem toda do calendário de exposição.** Nos dias em que a H2
   esteve comprada, o retorno diário foi idêntico ao do B&H (|Δ| ≤ 4,5e-16, ambos 100%
   investidos). A diferença em log (L01 −0,2059; L02/L03 −0,2400) vem dos **100 pregões
   inteiros em caixa, nos quais o ativo subiu +28,7%** (log +0,2522), com uma compensação
   parcial dos dias de troca (L01 +0,0463; L02/L03 +0,0122). Nos dias comprados o ativo caiu
   −23,7% (L01) e −26,5% (L02/L03). Os custos somaram R$ 866 e R$ 1.007, menos de 1,1% do
   capital.
2. **[F] A H2 comprou depois de altas e vendeu depois de quedas.** L01 fez 6 ciclos e L02/L03
   fizeram 7, com **um único ciclo lucrativo** em cada. Todas as recompras saíram acima do preço
   da venda anterior (+1,2% a +5,4%), e o ativo subiu em todos os períodos com pregões inteiros
   em caixa (+3,3% a +7,4%). Toda compra foi decidida com fechamento acima da SMA50 e toda venda com fechamento
   abaixo dela.
3. **[F] Risk Manager e Portfolio Manager não mudaram nenhuma decisão.** Os únicos vetos foram
   `CONCENTRATION` em COMPRA já no alvo, ou seja, sem efeito (no-op). O Risk LLM aprovou 6/6,
   7/7 e 7/7, e o PM seguiu o consenso em 80/80, 78/78 e 80/80 chamadas. A trajetória é função
   apenas do consenso técnico e do sizing 0%/100%.
4. **[F] L02 e L03 são financeiramente idênticos (mesmos bytes em `equity.csv` e `trades.csv`)
   porque as 10 sessões em que o resultado técnico divergiu não mudam a posição.** Em todas elas
   a divergência foi VENDA×MANTER com a carteira em caixa ou COMPRA×MANTER com a carteira 100%
   comprada. As chamadas são independentes: há 3.963 `responseId` distintos, nenhum envelope
   HTTP se repete entre runs e as janelas de execução não se sobrepõem. A concordância de votos
   L02×L03 (93,5%) é a mesma de L01×L02 (93,4%).
5. **[F] `risk_max_drawdown=0,25` é um limite de veto de COMPRA, não um stop nem um teto
   garantido.** Nenhuma COMPRA ocorreu com drawdown canônico > 0,25, então a regra não foi
   exercitada. O MDD veio de uma queda de −6,15% num único pregão (2025-08-08) com 100% de
   exposição: o drawdown foi de 20,5% para 25,4% em L01 e de 22,1% para 26,9% em L02/L03. A saída
   veio por VENDA 5/5 na abertura seguinte. É o comportamento previsto no contrato; não houve
   violação.
6. **[F] As exposições da H2 e do Bollinger foram quase complementares.** Em 127 pregões a H2
   esteve comprada e o Bollinger em caixa, e o ativo caiu −23,0%. Em 56 pregões (L01) e 57
   (L02/L03) foi o inverso, e o ativo subiu +12,5% e +15,9%. O Bollinger comprou nas mesmas
   aberturas em que a H2 vendeu (2025-03-06 a 29,3903 e 2025-08-11 a 27,3705).
7. **[F] As 9 disposições N/A são divergências legítimas do replay exato.** Reconstruí offline
   o prompt da chamada #67 (Portfolio Manager, 2024-09-18) mudando **apenas**
   `current_drawdown`: 0,068357, 0,069287 e 0,070216 para 0, 10 e 20 bps, contra 0,068822 em
   5 bps. Os 9 SHA-256 resultantes coincidem com os valores `replayed` de `cost_closure.json`.
   O baseline de 5 bps está íntegro.
8. **[F] `summary.json` confere com os arquivos originais.** Comparado com `cost_closure.json`,
   com os manifests e com o recálculo a partir de equity/trades, os 21 blocos de métricas são
   idênticos bit a bit e as estatísticas também. As métricas secundárias diferem no máximo
   1,1e-13. Não há divergência numérica, só duas observações de rotulagem e telemetria (§10).

## 2. Item 1 — Timeline das operações

"Chamadas decisivas" são as sequências de `llm_calls.jsonl` do próprio run: TA são os 5
analistas, RM o Risk LLM (só é chamado em COMPRA com carteira em caixa) e PM o Portfolio
Manager. Os votos estão na ordem COMPRA/VENDA/MANTER. Depois de uma COMPRA o caixa é zero,
porque o alvo é 100% e a arena zera o resíduo.

**L01**

| # | Decisão (fech. t) | Votos C/V/M | Chamadas decisivas | Execução (abert. t+1) | Lado | Preço | Quantidade | Custo | Caixa após | Patrimônio fech. execução |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | 2024-09-02 | 5/0/0 | TA #0–4, RM #5, PM #6 | 2024-09-03 | COMPRA | 30,3391 | 3.293,3781 | 81,93 | 0,00 | 99.248,34 |
| 2 | 2024-09-18 | 0/5/0 | TA #62–66, PM #67 | 2024-09-19 | VENDA | 28,6027 | 3.293,3781 | 77,24 | 94.122,39 | 94.122,39 |
| 3 | 2024-10-02 | 5/0/0 | TA #117–121, RM #122, PM #123 | 2024-10-03 | COMPRA | 29,2832 | 3.211,5781 | 77,12 | 0,00 | 95.301,22 |
| 4 | 2024-10-22 | 0/3/2 | TA #189–193, PM #194 | 2024-10-23 | VENDA | 28,0865 | 3.211,5781 | 73,97 | 90.128,12 | 90.128,12 |
| 5 | 2024-11-12 | 5/0/0 | TA #277–281, RM #282, PM #283 | 2024-11-13 | COMPRA | 28,9000 | 3.116,0704 | 73,84 | 0,00 | 89.883,68 |
| 6 | 2025-03-05 | 0/5/0 | TA #644–648, PM #649 | 2025-03-06 | VENDA | 29,3903 | 3.116,0704 | 75,10 | 91.507,21 | 91.507,21 |
| 7 | 2025-03-21 | 5/0/0 | TA #711–715, RM #716, PM #717 | 2025-03-24 | COMPRA | 30,9861 | 2.950,7543 | 74,97 | 0,00 | 91.556,80 |
| 8 | 2025-04-04 | 0/5/0 | TA #763–767, PM #768 | 2025-04-07 | VENDA | 28,6389 | 2.950,7543 | 69,30 | 84.437,01 | 84.437,01 |
| 9 | 2025-06-13 | 4/0/1 | TA #1034–1038, RM #1039, PM #1040 | 2025-06-16 | COMPRA | 28,9926 | 2.909,9760 | 69,18 | 0,00 | 83.537,90 |
| 10 | 2025-07-18 | 0/5/0 | TA #1156–1160, PM #1161 | 2025-07-21 | VENDA | 27,5310 | 2.909,9760 | 65,69 | 80.048,73 | 80.048,73 |
| 11 | 2025-07-29 | 4/0/1 | TA #1193–1197, RM #1198, PM #1199 | 2025-07-30 | COMPRA | 28,7876 | 2.778,3858 | 65,59 | 0,00 | 81.146,98 |
| 12 | 2025-08-08 | 0/5/0 | TA #1235–1239, PM #1240 | 2025-08-11 | VENDA | 27,3705 | 2.778,3858 | 62,36 | 75.983,55 | 75.983,55 |

**L02**

| # | Decisão (fech. t) | Votos C/V/M | Chamadas decisivas | Execução (abert. t+1) | Lado | Preço | Quantidade | Custo | Caixa após | Patrimônio fech. execução |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | 2024-09-02 | 5/0/0 | TA #0–4, RM #5, PM #6 | 2024-09-03 | COMPRA | 30,3391 | 3.293,3781 | 81,93 | 0,00 | 99.248,34 |
| 2 | 2024-09-18 | 0/5/0 | TA #62–66, PM #67 | 2024-09-19 | VENDA | 28,6027 | 3.293,3781 | 77,24 | 94.122,39 | 94.122,39 |
| 3 | 2024-10-02 | 5/0/0 | TA #116–120, RM #121, PM #122 | 2024-10-03 | COMPRA | 29,2832 | 3.211,5781 | 77,12 | 0,00 | 95.301,22 |
| 4 | 2024-10-22 | 0/4/1 | TA #188–192, PM #193 | 2024-10-23 | VENDA | 28,0865 | 3.211,5781 | 73,97 | 90.128,12 | 90.128,12 |
| 5 | 2024-11-12 | 5/0/0 | TA #276–280, RM #281, PM #282 | 2024-11-13 | COMPRA | 28,9000 | 3.116,0704 | 73,84 | 0,00 | 89.883,68 |
| 6 | 2025-02-13 | 0/3/2 | TA #583–587, PM #588 | 2025-02-14 | VENDA | 30,7665 | 3.116,0704 | 78,61 | 95.792,08 | 95.792,08 |
| 7 | 2025-02-14 | 3/0/2 | TA #589–593, RM #594, PM #595 | 2025-02-17 | COMPRA | 31,7797 | 3.011,7834 | 78,49 | 0,00 | 95.789,88 |
| 8 | 2025-03-05 | 0/5/0 | TA #646–650, PM #651 | 2025-03-06 | VENDA | 29,3903 | 3.011,7834 | 72,58 | 88.444,69 | 88.444,69 |
| 9 | 2025-03-21 | 5/0/0 | TA #713–717, RM #718, PM #719 | 2025-03-24 | COMPRA | 30,9861 | 2.852,0000 | 72,47 | 0,00 | 88.492,62 |
| 10 | 2025-04-04 | 0/5/0 | TA #765–769, PM #770 | 2025-04-07 | VENDA | 28,6389 | 2.852,0000 | 66,98 | 81.611,12 | 81.611,12 |
| 11 | 2025-06-13 | 3/0/2 | TA #1033–1037, RM #1038, PM #1039 | 2025-06-16 | COMPRA | 28,9926 | 2.812,5865 | 66,87 | 0,00 | 80.742,09 |
| 12 | 2025-07-18 | 0/5/0 | TA #1155–1159, PM #1160 | 2025-07-21 | VENDA | 27,5310 | 2.812,5865 | 63,50 | 77.369,70 | 77.369,70 |
| 13 | 2025-07-29 | 3/0/2 | TA #1192–1196, RM #1197, PM #1198 | 2025-07-30 | COMPRA | 28,7876 | 2.685,4002 | 63,39 | 0,00 | 78.431,20 |
| 14 | 2025-08-08 | 0/5/0 | TA #1234–1238, PM #1239 | 2025-08-11 | VENDA | 27,3705 | 2.685,4002 | 60,27 | 73.440,57 | 73.440,57 |

**L03.** As ordens, preços, quantidades, custos e patrimônio são iguais aos de L02. Só mudam
os votos em 2024-10-22 (0/5/0), 2025-02-14 (4/0/1), 2025-06-13 (4/0/1) e 2025-07-29 (5/0/0),
e as sequências das chamadas: PM #6, #67, #123, #194, #283, #589, #596, #652, #720, #771,
#1041, #1162, #1200 e #1241, com o RM uma sequência antes do PM em cada compra.

**Ciclos (entrada → saída)**

| Ciclo | L01: execução | Variação do preço | Resultado líquido (R$) | Pregões | L02 = L03: execução | Variação do preço | Resultado líquido (R$) | Pregões |
|---:|---|---:|---:|---:|---|---:|---:|---:|
| 1 | 2024-09-03 → 09-19 | −5,72% | −5.877,61 | 12 | 2024-09-03 → 09-19 | −5,72% | −5.877,61 | 12 |
| 2 | 2024-10-03 → 10-23 | −4,09% | −3.994,27 | 14 | 2024-10-03 → 10-23 | −4,09% | −3.994,27 | 14 |
| 3 | 2024-11-13 → 2025-03-06 | +1,70% | +1.379,08 | 73 | 2024-11-13 → 2025-02-14 | +6,46% | +5.663,95 | 61 |
| 4 | — | | | | 2025-02-17 → 03-06 | −7,52% | −7.347,39 | 11 |
| 5 | 2025-03-24 → 04-07 | −7,57% | −7.070,20 | 10 | 2025-03-24 → 04-07 | −7,57% | −6.833,57 | 10 |
| 6 | 2025-06-16 → 07-21 | −5,04% | −4.388,28 | 24 | 2025-06-16 → 07-21 | −5,04% | −4.241,42 | 24 |
| 7 | 2025-07-30 → 08-11 | −4,92% | −4.065,18 | 8 | 2025-07-30 → 08-11 | −4,92% | −3.929,13 | 8 |
| | **Total** | | **−24.016,45** (custos 866,29) | | **Total** | | **−26.559,43** (custos 1.007,25) | |

- **[F]** A soma dos ciclos é exatamente o resultado do run: 75.983,55 − 100.000 e
  73.440,57 − 100.000.
- **[F]** Toda ordem nasce de um `ACTION_BUY`/`ACTION_SELL` no pregão anterior, e toda ação
  que mudaria a posição gerou ordem. Os `ACTION_SELL` emitidos com a carteira já em caixa
  (68 em L01, 64 em L02 e 66 em L03) não geram ordem, porque o alvo de 0% já está satisfeito.
- **[F]** Os três runs estão em caixa desde 2025-08-11. O settlement de 2025-08-29 não liquidou
  nada e o patrimônio ficou constante nos últimos 14 pregões.

## 3. Item 2 — Exposição ao mercado

Exposição medida pela posição no fechamento das 247 sessões de decisão:

| Participante | Comprado | Em caixa | Ordens |
|---|---:|---:|---:|
| L01 | 141 (57,1%) | 106 (42,9%) | 12 |
| L02 = L03 | 140 (56,7%) | 107 (43,3%) | 14 |
| Buy & Hold | 246 (99,6%) | 1 | 1 |
| SMA Regime | 161 (65,2%) | 86 | 2 |
| Bollinger Estado | 69 (27,9%) | 178 | 7 |

- **[F]** Duração das posições: L01 tem média de 23,5 pregões e mediana de 13; L02/L03 têm
  média de 20,0 e mediana de 12. Só o ciclo de novembro de 2024 a fevereiro/março de 2025 durou
  mais de 24 pregões.
- **[F] Movimentos perdidos.** A tabela abaixo mostra cada período em caixa: o retorno do ativo
  (B&H) nos pregões inteiros fora do mercado e a diferença entre o preço de recompra e o preço
  da venda anterior.

| Venda (abertura) | Recompra (abertura) | Recompra vs venda | B&H nos pregões inteiros em caixa |
|---|---|---:|---:|
| 2024-09-19 a 28,6027 | 2024-10-03 a 29,2832 | +2,38% | +3,34% (9 pregões) |
| 2024-10-23 a 28,0865 | 2024-11-13 a 28,9000 | +2,90% | +3,56% (14) |
| 2025-02-14 a 30,7665 (só L02/L03) | 2025-02-17 a 31,7797 | +3,29% | — (fim de semana) |
| 2025-03-06 a 29,3903 | 2025-03-24 a 30,9861 | +5,43% | +7,41% (11) |
| 2025-04-07 a 28,6389 | 2025-06-16 a 28,9926 | +1,24% | +3,49% (46) |
| 2025-07-21 a 27,5310 | 2025-07-30 a 28,7876 | +4,56% | +4,48% (6) |
| 2025-08-11 a 27,3705 | — (fim da janela) | — | +3,53% (14) |

- **[F]** Nos 12 maiores movimentos diários do ativo (|variação| ≥ 3,2%):
  - **H2 comprada (6):** 2024-11-22 (+3,98%), 2025-02-27 (−3,53%), 2025-03-05 (−3,65%),
    2025-04-03 (−3,23%), 2025-04-04 (−4,03%) e 2025-08-08 (−6,15%).
  - **H2 vendeu na abertura (1):** 2025-04-07 (−3,97%).
  - **H2 em caixa (5):** 2025-04-08 (−3,56%), 2025-04-09 (+4,06%), 2025-04-10 (−6,22%),
    2025-05-05 (−3,73%) e 2025-06-11 (+3,33%).

  Ou seja, os períodos em caixa também evitaram quedas grandes. O saldo de cada período em
  caixa, porém, foi de alta.
- **[F]** Contexto da janela: o ativo foi de 30,1357 (2024-09-03) a 28,3469 (2025-08-29), ou
  −5,94% de fechamento a fechamento. A máxima foi 32,5058 (2025-02-20) e a mínima 25,6614
  (2025-05-05), uma amplitude de 26,7%. A volatilidade anualizada foi de 22,9%.

## 4. Item 3 — Analistas, consenso, Risk, PM e ordens

| Camada | L01 | L02 | L03 |
|---|---:|---:|---:|
| Votos individuais C/V/M (5 × 247) | 404/359/472 | 417/357/461 | 409/361/465 |
| Sessões unânimes / com maioria de 3 | 210 / 14 | 215 / 16 | 215 / 16 |
| Consenso C/V/M; sem maioria | 82/74/91; 0 | 85/71/91; 0 | 83/73/91; 0 |
| Risk: veto `CONCENTRATION` (= COMPRA já 100% comprado → `BUY_AT_TARGET_NOOP`) | 76 | 78 | 76 |
| Risk: `AUTO_APPROVE` (VENDA/MANTER) | 165 | 162 | 164 |
| Risk LLM (COMPRA em caixa): aprovações | 6/6 | 7/7 | 7/7 |
| Vetos `DRAWDOWN` / `VOLATILITY` / LLM | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| PM chamado / seguiu o sinal / inverteu ou segurou | 80 / 80 / 0 | 78 / 78 / 0 | 80 / 80 / 0 |
| `ACTION_BUY` / `ACTION_SELL` (dos quais em caixa, sem ordem) | 6 / 74 (68) | 7 / 71 (64) | 7 / 73 (66) |
| Ordens executadas | 12 | 14 | 14 |

- **[F] Analistas.** Nos votos de L01, todo voto COMPRA marca `CLOSE_ABOVE_SMA50` como
  `SUPPORTS_COMPRA` (100%), seguido de `MACD_ABOVE_SIGNAL` (94%), `MACD_POSITIVE` (89%) e
  `CLOSE_ABOVE_SMA200` (86%). Todo voto VENDA marca `CLOSE_BELOW_SMA50` como `SUPPORTS_VENDA`
  (100%), seguido de `MACD_NEGATIVE` (96%), `CLOSE_BELOW_SMA200` (90%) e `MACD_BELOW_SIGNAL`
  (82%). O consenso de L01 por estado das features:

  | Estado na sessão | COMPRA | VENDA | MANTER |
  |---|---:|---:|---:|
  | close > SMA50 e MACD > sinal | 76 | 0 | 17 |
  | close > SMA50 e MACD < sinal | 6 | 0 | 39 |
  | close < SMA50 e MACD > sinal | 0 | 14 | 18 |
  | close < SMA50 e MACD < sinal | 0 | 60 | 17 |

  **[F]** Nos três runs, toda compra foi decidida com `sma50_gap > 0` (entre +0,3% e +6,9%) e
  toda venda com `sma50_gap < 0` (entre −0,8% e −6,2%).
- **[F] Consenso → ordem.** Com Risk e PM sem efeito (tabela), o mapa efetivo foi este:
  consenso COMPRA com a carteira em caixa gera compra de 100%; consenso VENDA com a carteira
  comprada gera venda total; qualquer outra combinação não gera ordem.
- **[F] Onde ocorreram as perdas.** Os ciclos 1, 2, 5, 6 e 7 (e também o 4 em L02/L03)
  perderam de −4,1% a −7,6% no preço, entre 8 e 24 pregões cada. As duas maiores perdas foram
  2025-03-24 → 04-07 (−7,57%) e, em L02/L03, 2025-02-17 → 03-06 (−7,52%). O único ganho foi o
  ciclo mais longo, a partir de 2024-11-13.
- **[F] Onde ficaram as oportunidades.** O ativo subiu em todos os períodos em caixa (§3). O
  maior deles foi 2025-03-07 → 03-21 (+7,41%), logo após a venda de 2025-03-06; a recompra de
  2025-03-24 veio 5,43% acima e precedeu o ciclo de −7,57%.
- Nada nesta seção avalia regra alternativa. Os itens descrevem o que as camadas efetivamente
  fizeram.

## 5. Item 4 — Por que L02 e L03 têm curvas e trades idênticos

Resposta: as perguntas feitas aos analistas são as mesmas nos três runs, as respostas foram
amostradas de forma independente, e as divergências entre L02 e L03 caíram só em sessões em
que nenhuma das alternativas muda a posição.

- **[F] Mesmas perguntas, por construção.** As 1.235 requisições técnicas de cada run têm
  `identity_digest` idêntico entre L01, L02 e L03. O prompt técnico é função determinística das
  features. `seed` e `analyst_id` são só metadados e não são transmitidos, e a temperatura é
  fixa em 1,0.
- **[F] Respostas independentes.**
  - 3.963 `provider_response_id` distintos em 3.963 chamadas.
  - 3.963 envelopes HTTP (SHA-256 em `provider_journal.jsonl`) distintos, sem nenhum
    compartilhado entre runs.
  - Ledger de reservas de `provider.sqlite`: 1.321 / 1.320 / 1.322, igual ao número de chamadas
    de cada slot, sem resposta ou registro nulo.
  - Janelas sequenciais sem sobreposição, em UTC: L01 19:09:08–19:31:39Z, L02 19:31:57–19:54:37Z
    e L03 19:54:50–20:14:48Z (16:09–17:14 em Brasília).
  - Mesmo voto técnico em L02×L03 1.155/1.235 (93,5%), L01×L02 1.154 (93,4%) e L01×L03 1.144
    (92,6%). A semelhança entre L02 e L03 não é anômala.
  - As sessões com maioria de 3 votos coincidem em só 5 de 16 entre L02 e L03.
- **[F] Divergências neutras.** Os votos de L02 e L03 diferem em 37 sessões e o resultado
  técnico em 10. Nenhuma das 10 muda a posição:

  | Sessão | L02 (votos C/V/M → causa) | L03 (votos → causa) | Peso observado |
  |---|---|---|---:|
  | 2024-09-20 | 0/1/4 → HOLD | 0/3/2 → SELL sem ordem | 0 |
  | 2024-09-26 | 0/3/2 → SELL sem ordem | 0/1/4 → HOLD | 0 |
  | 2024-09-27 | 0/2/3 → HOLD | 0/4/1 → SELL sem ordem | 0 |
  | 2024-12-16 | 3/0/2 → BUY no alvo | 2/0/3 → HOLD | 1 |
  | 2025-01-02 | 2/0/3 → HOLD | 3/0/2 → BUY no alvo | 1 |
  | 2025-05-22 | 0/0/5 → HOLD | 0/3/2 → SELL sem ordem | 0 |
  | 2025-06-23 | 3/0/2 → BUY no alvo | 0/0/5 → HOLD | 1 |
  | 2025-07-09 | 1/0/4 → HOLD | 3/0/2 → BUY no alvo | 1 |
  | 2025-07-10 | 3/0/2 → BUY no alvo | 1/0/4 → HOLD | 1 |
  | 2025-07-11 | 4/0/1 → BUY no alvo | 2/0/3 → HOLD | 1 |

  Nas 14 sessões que geraram ordem, L02 e L03 chegaram à mesma ação, às vezes por margens
  diferentes: 2024-10-22 (4/5 e 5/5), 2025-02-14 (3/5 e 4/5), 2025-06-13 (3/5 e 4/5) e
  2025-07-29 (3/5 e 5/5). A execução é determinística dadas as mesmas ações (mesmas aberturas e
  mesmos custos), e por isso `equity.csv` e `trades.csv` saem com bytes idênticos.
- **[F] Identidades de execução distintas.** Os manifests de L02 e L03 diferem em 10 campos,
  todos de identidade ou evidência: `run_id`, `run_context.case_id` (`…:L02` e `…:L03`),
  `created_at` (19:54:40Z e 20:14:52Z) e bytes, contagens e SHA-256 de `llm_calls`,
  `decisions` e `provider_journal`. Nenhum campo financeiro difere.
- **[F] Onde L01 diverge de L02/L03.** Só em 2 das 247 sessões, consecutivas e com maioria
  mínima. Esse único episódio de vender e recomprar explica a diferença de −0,034 em log entre
  L01 e L02/L03.
  - **2025-02-13.** Features: `sma50_gap` −1,1%, `sma200_gap` +4,5%, MACD abaixo do sinal.
    - L01: TA #584–588, MANTER 4/5, sem ordem.
    - L02: TA #583–587, VENDA 3/5, PM #588 (`xEPJaqGqE-6mmtkPyfDB2QI`, 19:42:41Z).
    - L03: TA #584–588, VENDA 3/5, PM #589 (`m0jJarysCKjwqtsP1a2GwAE`, 20:03:20Z).

    L02 e L03 venderam em 2025-02-14 a 30,7665.
  - **2025-02-14.** Features: `sma50_gap` +1,9%, MACD ainda abaixo do sinal.
    - L01: MANTER 4/5.
    - L02: COMPRA 3/5, RM #594 (`y0PJav3xOqfQz7IPvaWf2Ac`), PM #595
      (`0UPJauSfH9uAmtkPtsH2iQg`).
    - L03: COMPRA 4/5, RM #595 (`oEjJasDTH_Hoz7IP79ztoQk`), PM #596
      (`o0jJaqaRFq3tz7IP6rGV0AI`).

    L02 e L03 recompraram em 2025-02-17 a 31,7797, 3,29% acima da venda.
- Conclusão: **nenhuma evidência de reutilização indevida.** A igualdade financeira resulta de
  sequências de ações iguais, e a ação só depende do voto nas raras sessões que de fato podem
  mudar a posição.

## 6. Item 5 — `risk_max_drawdown = 0,25` frente aos drawdowns de 25,36% e 26,93%

**Contrato, conforme código e protocolo:**

- O drawdown é medido no fechamento de *t* como `(pico − patrimônio) / pico`. O pico é interno
  ao run e começa no capital inicial
  ([participant.py:1373](../src/agents/participant.py#L1373);
  [H2_METHODOLOGICAL_FREEZE_V1.md:953](H2_METHODOLOGICAL_FREEZE_V1.md)).
- A comparação usa o valor quantizado a 6 casas e é estrita: veta se `> 0,25`
  ([risk_manager.py:148](../src/agents/risk_manager.py#L148)).
- Só COMPRA passa pela regra. VENDA e MANTER são `AUTO_APPROVE`, "não aumentam exposição"
  ([risk_manager.py:119](../src/agents/risk_manager.py#L119);
  [H2_METHODOLOGICAL_FREEZE_V1.md:985](H2_METHODOLOGICAL_FREEZE_V1.md)).
- "Regra não exercitada é limitação de cobertura, não aprovação implícita"
  ([H2_METHODOLOGICAL_FREEZE_V1.md:969](H2_METHODOLOGICAL_FREEZE_V1.md)).

| Conceito | Existe na OA-1? | Como opera | Observado na Validation |
|---|---|---|---|
| **Limite de veto** (`risk_max_drawdown=0,25`) | Sim | Bloqueia COMPRA quando o drawdown canônico em *t* é > 0,25 | **Nunca acionado.** Não houve consenso COMPRA com drawdown > 0,25 |
| **Limite de exposição** | Só `risk_max_concentration=1,0` com alvo fixo `long_target_weight=1,0` | Exposição de 0% ou 100%; nada reduz a exposição conforme o drawdown cresce | Toda posição foi de 100% |
| **Limite garantido de perda** | **Não existe** | Não há stop nem liquidação forçada. A saída depende do consenso VENDA, executado na abertura seguinte | MDD de 25,36% (L01) e 26,93% (L02/L03) |

- **[F]** Os drawdowns enviados nos prompts de Risk e PM (86, 85 e 87) são iguais ao recálculo
  canônico a partir de `equity.csv`.
- **[F]** O maior drawdown numa COMPRA executada foi 0,209711 em L01 e 0,226303 em L02/L03, na
  decisão de 2025-07-29. Ambos estão abaixo de 0,25, e a compra entrou em 2025-07-30.
- **[F]** Em 2025-08-08 o ativo caiu −6,15% (fechamento de 28,9926 para 27,2101) com a H2 100%
  comprada. O drawdown no fechamento passou a 0,253629 em L01 (pico de 101.290,39 em 2025-02-20)
  e a 0,269300 em L02/L03 (pico igual ao capital inicial, nunca superado, daí a duração de
  247). O consenso nesse dia foi VENDA 5/5, com o PM em #1240 (L01, `r0DJasKPCu6mmtkPyfDB2QI`),
  #1239 (L02, `QUbJarjdH63sz7IPqLHXuQM`) e #1241 (L03, `BUvJaqjlGcnOqtsPuZbn2QU`). A venda saiu
  na abertura de 2025-08-11 a 27,3705, e o drawdown final ficou em 24,98% e 26,56%.
- **[F]** De 2025-08-11 a 2025-08-28, L02/L03 passaram 14 sessões de decisão em caixa com
  drawdown > 0,25: 10 VENDA sem ordem e 4 MANTER. Qualquer COMPRA teria sido vetada, mas nenhuma
  ocorreu. Em L01 o drawdown > 0,25 durou só o pregão de 2025-08-08.
- **Conclusão [F]:** não houve violação de contrato. O parâmetro é um limite de veto de entrada,
  e um MDD realizado acima de 25% é compatível com ele numa política 0%/100% sem stop. O nome
  `max_drawdown` pode sugerir um teto, mas o contrato não o define assim.
- **[L]** Como a regra não foi exercitada, a Validation não traz evidência sobre o efeito dela.

## 7. Item 6 — Trajetória da H2 frente ao Buy & Hold e ao Bollinger

**Decomposição exata em log-retorno.** `Σ_t [ln(1+r_H2) − ln(1+r_B&H)] = ln(P_H2(T)/P_B&H(T))`,
porque as duas carteiras partem de 100.000. Cada dia é classificado pelo estado da H2 no dia.

| Estado do dia | L01: Δ (dias; ativo em log) | L02 = L03: Δ (dias; ativo em log) |
|---|---:|---:|
| Comprada o dia inteiro | −0,0000 (135; −0,2711) | +0,0000 (133; −0,3076) |
| Em caixa o dia inteiro | **−0,2522** (100; +0,2522) | **−0,2522** (100; +0,2522) |
| Entrada na abertura | +0,0035 (6) | −0,0027 (7) |
| Saída na abertura | +0,0428 (6) | +0,0149 (7) |
| **Total = ln(P_H2/P_B&H)** | **−0,2059** (razão 0,8139) | **−0,2400** (razão 0,7867) |

- **[F]** Nos dias de troca, Δ é a variação de preço que a H2 não captou mais o custo. Na
  entrada, é o gap entre o fechamento anterior e a abertura. Na saída, é o movimento entre a
  abertura e o fechamento do dia. Os maiores efeitos foram as saídas de 2025-04-07 (+0,0212) e
  2025-03-06 (+0,0151), que evitaram quedas intradiárias, e a saída de 2025-02-14 em L02/L03
  (−0,0279), num dia em que o ativo subiu 3,08%.

**Períodos que mais contribuíram para a diferença** (L02 = L03; |Δ| > 0,005):

| Estado | Período | Pregões | Δ H2 − B&H (log) |
|---|---|---:|---:|
| caixa | 2025-03-07 → 2025-03-21 | 11 | −0,0715 |
| caixa | 2025-07-22 → 2025-07-29 | 6 | −0,0438 |
| caixa | 2024-10-24 → 2024-11-12 | 14 | −0,0350 |
| caixa | 2025-08-12 → 2025-08-29 | 14 | −0,0347 |
| caixa | 2025-04-08 → 2025-06-13 | 46 | −0,0343 |
| caixa | 2024-09-20 → 2024-10-02 | 9 | −0,0328 |
| saída / entrada | 2025-02-14 e 2025-02-17 (só L02/L03) | 2 | −0,0279 e −0,0061 |
| saída | 2025-04-07 | 1 | +0,0212 |
| saída | 2025-03-06 | 1 | +0,0151 |
| saída | 2024-09-19 e 2024-10-23 | 2 | +0,0074 e +0,0062 |

**Por mês** (log-retornos):

| Mês | L01 | L02 = L03 | B&H | Bollinger | L02 − B&H | L02 − Bollinger |
|---|---:|---:|---:|---:|---:|---:|
| 2024-09 | −0,0606 | −0,0606 | −0,0752 | 0,0000 | +0,0146 | −0,0606 |
| 2024-10 | −0,0434 | −0,0434 | −0,0028 | 0,0000 | −0,0406 | −0,0434 |
| 2024-11 | +0,0506 | +0,0506 | +0,0800 | 0,0000 | −0,0294 | +0,0506 |
| 2024-12 | +0,0043 | +0,0043 | +0,0043 | 0,0000 | 0,0000 | +0,0043 |
| 2025-01 | +0,0406 | +0,0406 | +0,0406 | 0,0000 | 0,0000 | +0,0406 |
| 2025-02 | −0,0478 | −0,0819 | −0,0478 | +0,0498 | −0,0340 | −0,1316 |
| 2025-03 | −0,0209 | −0,0209 | +0,0337 | +0,0645 | −0,0545 | −0,0854 |
| 2025-04 | −0,0920 | −0,0920 | −0,1899 | −0,1899 | +0,0979 | +0,0979 |
| 2025-05 | 0,0000 | 0,0000 | +0,0299 | +0,0568 | −0,0299 | −0,0568 |
| 2025-06 | −0,0368 | −0,0368 | +0,0451 | +0,1138 | −0,0819 | −0,1506 |
| 2025-07 | −0,0069 | −0,0069 | +0,0394 | 0,0000 | −0,0463 | −0,0069 |
| 2025-08 | −0,0618 | −0,0618 | −0,0259 | +0,0342 | −0,0359 | −0,0960 |
| **Total** | **−0,2747** | **−0,3087** | **−0,0687** | **+0,1292** | **−0,2400** | **−0,4379** |

**[F] Bollinger: exposição conjunta.** Dias de troca contados pelo estado no fim do dia.

| H2 | Bollinger | Pregões (L01 / L02) | H2 (log) | Bollinger (log) | Ativo (log) |
|---|---|---:|---:|---:|---:|
| comprada | caixa | 127 / 127 | −0,2600 / −0,2600 | −0,0074 / −0,0074 | −0,2616 / −0,2616 |
| caixa | comprado | 56 / 57 | −0,0095 / −0,0070 | +0,0984 / +0,1288 | +0,1174 / +0,1477 |
| caixa | caixa | 50 / 50 | +0,0003 / +0,0003 | +0,0441 / +0,0441 | +0,0828 / +0,0828 |
| comprada | comprado | 14 / 13 | −0,0054 / −0,0420 | −0,0060 / −0,0363 | −0,0073 / −0,0377 |

- **[F]** O Bollinger comprou na abertura de 2025-03-06 a 29,3903 e na de 2025-08-11 a
  27,3705, exatamente as aberturas em que a H2 vendeu. Também vendeu em 2025-02-19 a 32,1765,
  logo depois da recompra de L02/L03 em 2025-02-17 a 31,7797, e comprou em 2025-06-05 a 26,2921
  com a H2 em caixa. Por construção o Bollinger compra com o fechamento na banda inferior ou
  abaixo dela e vende com o fechamento na banda superior ou acima, ou seja, é contrário ao
  estado de tendência (`src/experiments/h2_evaluation.py`, `BollingerStateParticipant`).
- **[F]** Em abril de 2025 a H2 superou o B&H (+0,098 em log) porque saiu na abertura de
  2025-04-07 e ficou fora nas quedas de 04-08 e 04-10. O ganho foi devolvido depois, com 46
  pregões em caixa enquanto o ativo se recuperava.
- Esta seção descreve a trajetória observada e não converte nenhuma observação em estratégia.

## 8. Item 7 — As nove disposições N/A dos spreads alternativos

**Mecanismo [F].** O replay de custo reexecuta o participante consumindo as respostas gravadas
e exige que cada requisição tenha a mesma identidade que a original
([llm_trace.py](../src/agents/llm_trace.py), `ReplayLLMClient`). As chamadas #0–#66 têm
prompts que não dependem do custo:

- **#0–#6 (2024-09-02).** TA, Risk e PM com a carteira em caixa, drawdown 0 e concentração 0.
- **2024-09-03 a 09-17.** Só TA (features de preço); a COMPRA no alvo é vetada por regra dura
  antes de qualquer LLM.
- **#62–#66.** TA de 2024-09-18.

A **#67** (PM, 2024-09-18, primeira VENDA com posição) é o primeiro prompt que carrega uma
métrica dependente do patrimônio após custos, `risk_verdict.risk_metrics.current_drawdown`. Os
três runs gravaram nela a mesma requisição (`identity_digest` `3fed07b4…`, `user_prompt_sha256`
`6f8e5af3…`), porque tinham o mesmo estado e o mesmo consenso: VENDA 5/5 com confiança 0,65. As
respostas foram L01 `JTzJat_tHqjwqtsP1a2GwAE` (19:10:10Z), L02 `oUHJarMGhcCq2w_ulMzRBQ`
(19:33:34Z) e L03 `0EbJaq7vM6jRz7IPmIWjuQI` (19:55:41Z).

**Reconstrução offline [F].** Até 2024-09-18 os três runs mantêm exatamente a posição do B&H
(a mesma COMPRA de 2024-09-03), então o patrimônio sob cada spread é o da curva B&H do mesmo
spread. A reconstrução pega o prompt gravado, troca só `current_drawdown` e serializa com
`json.dumps(sort_keys=True, ensure_ascii=False)`. A concentração continua 1,0.

| Spread | Patrimônio em 2024-09-18 | `current_drawdown` | SHA-256 do prompt reconstruído | Em `cost_closure.json` |
|---|---:|---:|---|---|
| 5 bps (gravado) | 93.117,78 | 0,068822 | `6f8e5af3958e44d8…` | = recorded |
| 0 bps | 93.164,32 | 0,068357 | `39d169f177eb7c9a…` | = replayed em L01, L02 e L03 |
| 10 bps | 93.071,28 | 0,069287 | `0ee4d7e9f9c9fc3e…` | = replayed em L01, L02 e L03 |
| 20 bps | 92.978,43 | 0,070216 | `d4fd23e68a35c3f9…` | = replayed em L01, L02 e L03 |

- **[F]** A mensagem de cada N/A aponta uma única diferença de identidade (`user_prompt_sha256`),
  com `consumed_calls = 67`, ou seja, as chamadas #0–#66 casaram.
- **[F] Fechamento fail-closed.** Os slots `L0x-cost-*` ficaram `STARTED` e nenhum diretório de
  run foi criado para eles. As 9 disposições estão seladas em `evaluation.sqlite` e os 9 selos
  conferem. O total de disposições é 9 N/A, 9 `COMPLETE_DETERMINISTIC` (benchmarks) e 6
  `BASELINE_REUSED`.
- **[F] Baseline de 5 bps íntegro.** Os 6 participantes estão como `BASELINE_REUSED`; os arquivos
  dos runs de 5 bps são os fixados no checkpoint e não mudaram; as métricas de
  `cost_closure.json["5"]` são idênticas às de `summary.json`.
- **[F] Consequência estrutural, não falha de execução.** Sob replay exato, a sensibilidade a
  custo da H2 deixa de ser estimável assim que um prompt de Risk ou PM embute métricas do
  patrimônio após um trade. Isso aconteceu no 13º pregão.
- **[L]** A sensibilidade a custo da H2 continua desconhecida. Para os benchmarks ela foi
  determinística: Bollinger +14,19%, +13,79%, +13,40% e +12,61% e B&H −6,60%, −6,64%, −6,69% e
  −6,78% para 0, 5, 10 e 20 bps.

## 9. Item 8 — `summary.json` frente aos arquivos de equity e trades

| Participante | Retorno total | Sharpe | MDD (duração) | Ordens | Custos (R$) | Recálculo = reportado |
|---|---:|---:|---:|---:|---:|---|
| L01 | −24,02% | −1,6340 | −25,36% (130) | 12 | 866,29 | bit a bit |
| L02 | −26,56% | −1,8887 | −26,93% (247) | 14 | 1.007,25 | bit a bit |
| L03 | −26,56% | −1,8887 | −26,93% (247) | 14 | 1.007,25 | bit a bit |
| Buy & Hold | −6,64% | −0,1912 | −21,06% (130) | 1 | 81,93 | bit a bit |
| SMA Regime | −13,42% | −0,7070 | −19,48% (130) | 2 | 152,99 | bit a bit |
| Bollinger Estado | +13,79% | +0,8874 | −19,32% (106) | 7 | 595,59 | bit a bit |

- **[F]** As 7 métricas de cada um dos 21 blocos reportados são iguais bit a bit em quatro
  fontes: o recálculo independente em numpy, `src.backtesting.metrics.performance_metrics`
  aplicado a `equity.csv` e os campos `metrics` de `manifest.json`, `summary.json` e
  `cost_closure.json`. Os 21 blocos são 6 em `summary.json` e 15 em `cost_closure.json`.
- **[F]** As métricas secundárias (nocional, turnover, custo total e ordens) diferem no máximo
  1,1e-13 por ordem de soma. Os campos `final_equity`, `trade_count`, `total_transaction_cost`,
  `equity_points = 248` e `cost_model.spread_bps` dos manifests conferem.
- **[F]** As estatísticas também são idênticas: ΔSharpe individual −1,4428, −1,6975 e −1,6975;
  Δ médio −1,6126; desvio-padrão entre runs 0,1471. Elas coincidem com o bloco `statistics` do
  checkpoint. O digest do `plan` em `evaluation.sqlite` é igual a `plan_hash`, e os 15 selos de
  slot `COMPLETE` conferem com os arquivos.
- **[F]** `equity.csv` e `trades.csv` são consistentes entre si (reconstrução do §0).
- **Divergências numéricas: nenhuma.** As observações não numéricas estão no §10.

## 10. Observações incidentais (não numéricas)

- **O1 [F] Rótulo `amendment_status`.** `summary.json` traz
  `"amendment_status": "H2_V6 EVALUATION AMENDMENT PROPOSED — AWAITING AUTHOR APPROVAL"` ao
  lado de `"amendment_id": "H2-V6-OA1"`. O valor é a constante herdada `AMENDMENT_STATUS`
  ([h2_evaluation.py:35](../src/experiments/h2_evaluation.py#L35)) e descreve o *evaluation
  amendment* do candidato. A sobrescrita de OA-1
  ([run_h2_v6_provisional.py:251](../scripts/run_h2_v6_provisional.py#L251)) não o substitui.
  Um leitor pode entender "OA-1 aguardando aprovação", embora a autorização esteja commitada
  (`1a0852f`). O arquivo é selado e não foi alterado.
- **O2 [F] Tentativas no trace.** Em L01, a chamada #35 (2024-09-10, analista 4) teve um
  `ConnectionResetError` (WinError 10054) e sucesso na 2ª tentativa. Isso está registrado em
  `provider_journal.jsonl` e no `attempts` de `provider.sqlite` (`TRANSPORT_ERROR`, depois
  `ENVELOPE_DURABLE`), com `attempt_count=2`. Já `llm_calls.jsonl` registra `attempt_count=1`
  e `retry_count=0`, porque o recorder externo só vê a chamada lógica
  ([h2_evaluation_production.py:473](../src/experiments/h2_evaluation_production.py#L473)
  aplica a contagem só ao registro do journal). A requisição e a resposta são as mesmas, sem
  efeito em decisão. O journal é a fonte autoritativa de tentativas de transporte. Essa foi a
  única nova tentativa nos três runs.
- **O3 [F] Trace frente ao journal.** Nas 3.963 chamadas, `llm_calls.jsonl` e os registros do
  journal só diferem em telemetria: `started_at`/`duration_ms` dos recorders externo e interno,
  o sufixo local de `call_id`, `transport_system_prompt_sha256`, e `raw_response`/`token_usage`,
  que aparecem só no journal para Risk e PM. `identity_digest` e `validated_response` são
  iguais em 100%.

## 11. Hipóteses (não demonstradas)

- **H1 [H] Regime da janela.** No período a PETR4 oscilou em faixa, com −5,9% no total,
  amplitude de 26,7% e oscilações de 4% a 8% em 1 a 3 semanas. Num regime assim, entradas
  condicionadas a "fechamento acima da SMA50 e MACD acima do sinal" tendem a ocorrer depois da
  alta e saídas depois da queda. Os fatos dos §§3–4 são consistentes com isso: todas as
  recompras (5 em L01, 6 em L02/L03) acima da venda anterior, 1 ciclo lucrativo em 6 ou 7, e um
  benchmark contrário (Bollinger) com +13,8%. Nada foi demonstrado causalmente: há um só ativo, uma só janela e nenhum teste formal
  de regime.
- **H2 [H] Sensibilidade amostral.** Com temperatura 1,0, 5 analistas e limiar de 3/5, sessões
  com maioria mínima dependem da amostragem. A única divergência de trajetória entre L01 e
  L02/L03 veio de duas sessões assim (fato). Quantificar essa sensibilidade em geral exigiria
  mais que R = 3.
- **H3 [H] Papel das camadas fora desta janela.** Na Validation, Risk e PM não alteraram
  decisões (fato). Se agiriam em outros regimes, por exemplo com drawdown > 25% sob consenso
  COMPRA ou volatilidade > 50%, não se pode afirmar com estes dados.

## 12. Limitações de evidência

- **L1.** Os preços são só fechamentos derivados do B&H (2024-09-03 a 2025-08-29) e aberturas
  nos dias de trade. Não há fechamento de 2024-09-02, OHLC completo nem caminho intradiário,
  porque o snapshot não foi aberto (contém o Final Test).
- **L2.** São só R = 3 execuções, e como L02 = L03 há apenas 2 trajetórias financeiras
  distintas. Toda dispersão aqui é descritiva.
- **L3.** Por desenho não foi calculado nenhum contrafactual, nem com outro parâmetro, outra
  regra ou outro custo. Perguntas do tipo "e se" ficam abertas e não devem ser respondidas com
  esta janela.
- **L4.** O "porquê" de cada voto vem dos códigos de evidência estruturados; o raciocínio
  interno do modelo (thoughts) não está nos artifacts.
- **L5.** A sensibilidade a custo da H2 não é estimável sob replay exato (§8). As regras de
  drawdown e de volatilidade não foram exercitadas.
- **L6.** Esta análise é post-hoc e foi feita depois de observados os resultados. Qualquer
  mudança de tratamento motivada por ela contaminaria a janela de Validation, como o próprio
  OA-1 §4.1 já registra
  ([H2_V6_OPERATIONAL_AMENDMENT_OA1.md](H2_V6_OPERATIONAL_AMENDMENT_OA1.md)).

## 13. Reprodução e integridade desta análise

```powershell
.venv\Scripts\python.exe -B scripts/h2_v6_oa1_validation_diagnostic.py
# termina com "DIAGNÓSTICO: todos os asserts passaram"
```

- O script lê só o diretório selado e o checkpoint. Ele não abre snapshot, não instancia
  participante, não chama provedor e não grava arquivo. O `-B` evita `__pycache__` em `src/`.
- Os SHA-256 dos 60 arquivos de `data/runs/h2_v6_provisional/VALIDATION` foram registrados
  antes e depois e estão inalterados. Os resultados intermediários ficaram fora do repositório.
- Os únicos arquivos novos no repositório são este relatório e o script. A rota OA-1 exige
  árvore limpa (`verify_manifest(clean=True)`), então eles precisam ser commitados ou removidos
  antes de qualquer `preflight` ou `audit`. Nenhum dos dois entra no inventário do manifesto, que
  cobre `src/**/*.py`, quatro scripts nomeados e uma lista fixa de documentos.
