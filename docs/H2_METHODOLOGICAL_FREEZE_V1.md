# H2 METHODOLOGICAL FREEZE V1

```text
STATUS            CONGELADO PELOS AUTORES
TIMESTAMP (UTC)   2026-10-04T19:46:16Z
COMMIT BASE       0e89eb6c96ca9131582c5496df9fe9fdbac6446d
                  (o commit que adiciona este arquivo é o último antes da
                   primeira chamada do Diagnostic Hardening)
OBSERVADO ANTES   nenhum resultado experimental: nenhuma chamada de
                  Hardening, B0, CAL-A, CAL-B, Stress, Sequential
                  Development, Validation ou Final Test foi feita, e nenhuma
                  métrica financeira do participante LLM foi calculada
ORIENTADOR        pode revisar depois; qualquer mudança posterior à primeira
                  chamada do Hardening é PROTOCOL AMENDMENT (seção 17), nunca
                  edição deste arquivo
```

As únicas chamadas reais ao provedor antes deste freeze foram os DEV_SMOKE
técnicos (`docs/evidence/provider_runtime/`): uma chamada por papel sobre um
estado sintético, usadas para qualificar transporte, nunca para escolher nada.

Código: `src/experiments/hardening.py` (`H2_FREEZE_V1_PARAMS`,
`H2_THINKING_LADDER`, `H2_FREEZE_V1_GATES`, `H_REAL_*`) e
`scripts/run_h2_hardening.py`. Se este documento e o código divergirem, o que
rodou é o código do commit do freeze, e a divergência é defeito a registrar
como amendment.

## 1. Método do H2

```text
método                 self_consistency
ensemble técnico       analyst_count = 5
                       consensus_threshold = 0.6
                       require_all_votes = true
prompts                as cinco chamadas recebem o mesmo prompt lógico
analyst_id             só metadado / auditoria, nunca no texto do prompt
agregação              >= 3/5 numa classe    -> classe vencedora
                       divisão 2-2-1         -> TECH_NO_MAJORITY -> MANTER
                       maioria em MANTER     -> TECH_EXPLICIT_HOLD
não usado no H2 v1     Persona Ensemble, memória entre sessões,
                       seed transmitida
```

## 2. Runtime

```text
provedor      gemini
runtime       Gemini API nativa, v1beta generateContent
modelo        gemini-3.8-flash      (id fixo; nunca "latest")
fallback      nenhum. Se gemini-3.8-flash ficar indisponível depois da
              política de retry, a falha é registrada e a fase para. Troca de
              modelo exige amendment explícito e reinício completo da fase
              afetada.
```

## 3. Geração e spec do participante

Todo parâmetro material está escrito na spec, inclusive os iguais ao default
do código (protocolo, seção 5.7):

```text
temperature                 1.0
max_output_tokens           8192
seed                        nenhuma (nunca transmitida)
decision_frequency          1
strict_inputs               true
portfolio_inversion_policy  fail
analyst_count               5
consensus_threshold         0.6
require_all_votes           true
long_target_weight          1.0     já DECIDIDO (protocolo, seção 11)
risk_max_concentration      1.0     já DECIDIDO (protocolo, seção 11)
risk_max_volatility         0.5     valor técnico existente, adotado como
volatility_window           21      baseline B0 ex ante; CAL-A mantém a
                                    autoridade sobre os dois (seção 14)
risk_max_drawdown           0.25    valor técnico existente, baseline B0 ex
                                    ante; Sequential Development mantém a
                                    autoridade
retry_attempts              6       operacional (autoridade do Hardening,
retry_base_delay            2.0     protocolo 5.12); fixado antes da primeira
                                    chamada a partir da taxa de HTTP 503 vista
                                    no DEV_SMOKE; nunca muda o conteúdo de uma
                                    decisão
thinking_level              sai da escada da seção 4, nunca é escolhido
```

Técnico, Risco e Portfólio recebem `temperature`, `thinking_level` e
`max_output_tokens` explicitamente. O preflight científico recusa a spec se
faltar algum deles ou se o par (provedor, modelo, nível) não estiver
qualificado empiricamente.

## 4. Política de thinking: escada, não competição

```text
LOW -> MEDIUM -> HIGH, menor custo primeiro

começa com thinking_level = low (já qualificado em transporte para
gemini / gemini-3.8-flash)

LOW passa em todos os gates         -> LOW fica congelado para o H2 v1;
                                       MEDIUM e HIGH nunca são testados
LOW falha SÓ por G-I e/ou G-F       -> DEV_SMOKE de MEDIUM, qualificado só se o
                                       smoke passar, e H inteiro de novo, do
                                       zero, com MEDIUM
MEDIUM falha SÓ por G-I e/ou G-F    -> o mesmo com HIGH
HIGH falha G-I e/ou G-F             -> H2 STRUCTURAL HARDENING FAILED,
                                       parar antes do B0
falha G-A ou G-T causada por bug
de contrato                         -> PARAR; corrigir o bug de forma geral e
                                       versionada, depois repetir. A escada
                                       nunca mascara bug técnico
```

O nível nunca é escolhido por retorno, Sharpe ou leitura qualitativa das
respostas.

## 5. Falhas do provedor

Erro transitório recuperado pela política de retry (por exemplo HTTP 503) não
é falha G-A. Ele é registrado e entra só nas métricas operacionais descritivas:
contagem de retries, taxa de erro transitório, latência, chamadas e
tentativas. G-A conta apenas a falha final de uma sessão, depois de esgotados
os retries.

## 6. H_syn

`H_SYN_VERSION = 1`, com os 8 digests de payload já congelados em
`H_SYN_PAYLOAD_DIGESTS`. Geradores, parâmetros, features e digests não mudam;
qualquer mudança é `H_SYN_VERSION = 2` mais amendment explícito.

## 7. H_real: seleção mecânica

```text
ticker         PETR4.SA
snapshot       20261004T193839031891Z-6f5e24390ab2bca68131ecfc052b9d23
identidade     6f5e24390ab2bca68131ecfc052b9d2381411aaaad35f0e56640fffcd6e766db
arquivo        data/PETR4.SA.csv
               sha256 a74051447d8473e5cb1501c3a9c204ef5ac7b91a4197392063856034ea222b3f
               yfinance, auto_adjust=true, pedido 2016-01-01..2024-02-28
regra          E = sessões do calendário comum do snapshot (protocolo 5.11)
                   com 2018-01-12 <= s <= 2024-02-28,
                   available_history_sessions >= 504,
                   contrato de entrada estrito satisfeito (8 features +
                   janela de volatilidade completa)
               index_q = floor(q * (len(E) - 1)),  q em {0.20,0.40,0.60,0.80}
|E|            1519   (toda sessão da janela satisfaz o contrato)
sha256 de E    bada89626b03ca440c0e989fdf20bd4c3d4ea83be4faa66264cde655c9a46548
               (datas ISO unidas por "\n")
```

| quantil | índice | sessão | sha256 do payload |
|---:|---:|---|---|
| 0.20 | 303 | 2019-04-08 | `20d95f5a7cf0cccfb74f9cc43330c38065578234b745f6e7984a958946fe5b0e` |
| 0.40 | 607 | 2020-06-29 | `28065db7fc72b97e0098554bc273cae73219465d49ccaaaa85fcdd8a8060be0b` |
| 0.60 | 910 | 2021-09-17 | `c16e53020d2fc6852b1256a664a5c71eeaab5b4e950d9f4c20bde57d3ff9163b` |
| 0.80 | 1214 | 2022-12-07 | `06976959d02c8dc0786ac206fe5b870493f712bbe6bace3df20dc98bdc34c744` |

Nada do mercado foi olhado para escolher essas quatro datas: nenhum retorno,
Sharpe, evento, regime, tendência, volatilidade ou resposta de modelo.

As quatro sessões ficam excluídas de CAL-A, CAL-B, Stress, Sequential
Development e de qualquer outro conjunto experimental. Nenhum outro conjunto
tem datas ainda: H_real foi reservado primeiro, e os conjuntos futuros é que
precisam excluí-lo.

**Notas sobre os dados — registradas, não corrigidas.**

- Nenhuma vintage do yfinance passava no gate de consistência OHLC, por
  resíduos de 1 ulp do ajuste de preço. O gate ganhou uma tolerância técnica
  relativa de 1e-12 no commit `0e89eb6`; nenhum dado é alterado.
- O snapshot está `attention_required` em relação ao `B3Calendar` local:
  - **10 sessões "faltando"** (25/jan, 9/jul e 30/dez em vários anos) são dias
    reais sem pregão na B3 que o calendário local não conhece;
  - **2023-11-20** é pregão real (com volume) que o calendário exclui por
    engano;
  - há **10 barras de preenchimento do provedor com volume zero**: 9 em 2017 e
    2018-01-25.
- 2018-01-25 está dentro da janela e pertence a E pela definição canônica de
  sessão do protocolo (calendário comum do snapshot). Ela não é uma das quatro
  datas selecionadas.
- Os quatro payloads selecionados são idênticos byte a byte com e sem todas as
  barras de volume zero; as barras de preenchimento no warm-up são imateriais.
- Contando só dias com volume > 0, 2018-01-12 teria 503 sessões (< 504). O
  limite da janela, portanto, corresponde à definição canônica usada aqui.
- A divergência de calendário precisa ser resolvida antes de qualquer fase do
  `ExperimentRunner` (o runner recusa `attention_required`). Ela não afeta H,
  que nunca liquida.

## 8. Desenho do Hardening

```text
H = 8 H_syn + 4 H_real                       S = 12 estados
R = 5 repetições independentes por estado    cada uma com participante novo
N = 5 amostras técnicas por tratamento       12 x 5 x 5 = 300 chamadas técnicas
risco e portfólio seguem os ramos normais do grafo
sem liquidação, sem retorno futuro, sem métrica financeira
todo estado começa com carteira zerada (capital em caixa)
```

Isto substitui, antes de qualquer observação, a redação anterior do protocolo
de que o Hardening roda sobre as âncoras de CAL-A (seção 5.12). As datas de
CAL-A não existem, e o H dedicado mantém o Hardening disjunto de todo conjunto
de seleção.

## 9. Gates (congelados)

```text
G-A  falhas classe A finais (depois dos retries) = 0
     provider failure, invalid input, invalid response, provider request
     rejected, qualquer falha técnica que invalide uma decisão.
     Erro transitório recuperado por retry não conta.
G-T  truncamentos MAX_TOKENS / length = 0
     max_output_tokens não é aumentado durante a execução
G-I  sobre sessões elegíveis:
       explicit_hold_rate, no_majority_abstention_rate,
       risk_veto_rate (BUY_AT_TARGET_NOOP excluído), portfolio_hold_rate,
       total_hold_rate
     total_hold_rate >= 0.90  -> DEGENERATE_INACTIVE -> FAIL
     (detecta tratamento quase inerte; nunca serve para preferir quem negocia
      mais)
G-F  SAME_STATE_FLIP_RATE sobre pares de repetições do MESMO estado;
     só pares COMPRA <-> VENDA contam
     SAME_STATE_FLIP_RATE > 0.10 -> DEGENERATE_UNSTABLE -> FAIL
     same_state_disagreement_rate é só descritivo
```

## 10. Saída do Hardening

Tabela de gates, diagnósticos comportamentais (sem retorno financeiro) e
diagnósticos operacionais: chamadas lógicas, tentativas HTTP, retries
recuperados, contagem de 429 e 503, latência, tokens de entrada/saída e custo
quando houver fonte.

## 11. B0

Se, e só se, o Hardening passar, o nível da escada fica congelado e o B0 roda:

- uma passada completa sobre todo o H (R = 1) com a configuração congelada;
- não escolhe parâmetro, não compara configurações e não usa retorno
  financeiro.

O B0 persiste:
- spec, manifest, trace e decisions;
- proveniência de provedor/runtime e versão do modelo;
- a versão de H e as datas de H_real;
- os resultados dos gates do Hardening;
- uso de tokens.

Falha técnica no B0 para tudo antes do CAL-A.

## 12. Controle clássico (metodologia v1)

```text
indicator-family-matched classical control
famílias      SMA 50/200 · Bollinger 20/2.0 · RSI 14 · MACD 12/26/9
cada família  -1 / 0 / +1, evento de cruzamento t-1 -> t
score         SMA + BB + RSI + MACD      (pesos iguais, nada calibrável)
              score > 0 -> COMPRA · score < 0 -> VENDA · score = 0 -> MANTER
regra do RSI  cruza 30 de cima para baixo -> COMPRA
              cruza 70 de baixo para cima -> VENDA
```

A direção da regra do RSI é decisão metodológica dos autores, tomada por
consistência com a regra do Bollinger. Ela **não** é atribuída a Wilder, que
sustenta só o período e as referências 70/30.

## 13. RSI

O RSI científico é o RSI canônico de Wilder, já implementado e verificado
contra a planilha primária da StockCharts; `LLM_FEATURE_SCHEMA_VERSION = 2`.
Para série sem movimento (`avg_gain = 0` e `avg_loss = 0`) o RSI é 50. Essa é
uma **convenção local** explícita, atribuída nem a Wilder nem à StockCharts.

## 14. CAL-A: regra congelada, não executada

CAL-A continua REDUZIDA, com autoridade só sobre `risk_max_volatility` e
`volatility_window`.

Antes de rodar qualquer tratamento ou ver resultado de âncora, vale um gate de
identificabilidade:
1. Usar só configurações candidatas já declaradas no protocolo. Nenhuma grade
   nova pode ser inventada depois do B0.
2. Para cada configuração, calcular de forma determinística o vetor de veto de
   risco das 20 âncoras, usando só informação disponível até `t`.
3. Se as configurações diferirem em **menos de 3 das 20** âncoras, então
   `CAL-A = REMOVED`, e os dois parâmetros passam a ser o baseline ex ante da
   seção 3.
4. Se diferirem em **>= 3 das 20**, então `CAL-A = REDUCED`, executada depois
   conforme o protocolo.

**Estado atual: `CAL_A_CANDIDATE_GRID_UNRESOLVED`.** A seção 5.12 exige um
espaço finito pré-registrado, mas nunca enumera valores candidatos de
`risk_max_volatility` ou `volatility_window`, e as 20 âncoras de CAL-A não têm
datas. CAL-A para aqui. Isso não bloqueia o Hardening nem o B0.

## 15. Enquadramento do TCC

**Contribuição principal.** O Hedge-Fund-Lab como laboratório quantitativo
reproduzível, auditável e extensível.

**Estudo experimental.** O H2 avalia uma instanciação multiagente baseada em
LLM, sob o mesmo ambiente de execução dos controles clássicos. Nenhum resultado
positivo do H2 é prometido.

```text
ROLE                       Technical / Risk / Portfolio
PERSONA / ANALYST PROFILE  estilo dentro do Technical; o H2 v1 não usa nenhum
SC                         o ensemble Technical dentro da arquitetura
                           multiagente maior
```

A implementação **não** tem:
- debate cíclico (o grafo é linear e acíclico);
- pedido de reavaliação pelo Risco;
- memória persistente;
- dimensionamento de posição pelo Portfolio Manager (ele decide só a direção;
  a exposição vem de um peso alvo determinístico).

Os trechos da monografia que afirmavam o contrário foram corrigidos no commit
do freeze (`docs/faculdade/monografia/main.tex`).

## 16. Justificativa

O freeze torna explícito todo grau de liberdade restante do H2 antes de
qualquer observação experimental. Assim o Hardening, o B0 e as fases seguintes
testam uma hipótese fixa, e não uma configuração ajustada ao que foi visto.

## 17. Governança

Qualquer mudança posterior à primeira chamada do Hardening é registrada abaixo
como **PROTOCOL AMENDMENT**, com:
- data;
- razão;
- evidências já observadas;
- impacto sobre a comparabilidade;
- se fases anteriores precisam ser invalidadas ou repetidas.

Este texto de freeze nunca é editado em silêncio.

### Amendments

#### PROTOCOL AMENDMENT 1 — OBJECTIVE HISTORICAL_B3_CALENDAR / DATA_QUALITY CORRECTION

```text
DATA              2026-10-04
TIPO              correção objetiva de calendário e de qualidade de dados
DESCOBERTO        depois do Hardening e do B0 iniciais, antes de qualquer
                  CAL-A; nenhuma performance financeira foi consultada
NÃO MUDA          tratamento, modelo, geração, N, limiar, gates, escada de
                  thinking, política de retry, H_syn, regra de H_real, regras
                  de decisão
```

**Defeitos encontrados (fatos verificáveis).**

1. O `B3Calendar` v1 era uma lista fixa de feriados. Contra os arquivos
   oficiais COTAHIST da B3 (2016-01-04 a 2026-08-31, 2649 sessões) ele errava
   14 datas:
   - abria nos feriados de São Paulo (25/jan, 9/jul) até 2021;
   - abria no último dia útil do ano;
   - fechava 20/nov em 2020 e 2023, anos em que a B3 operou.

   Por isso o snapshot científico ficava `attention_required`. Evidência em
   `docs/evidence/calendar/`.
2. O OHLCV bruto do yfinance diverge do oficial da B3 no PETR4:
   - fechamento diferente em 45 sessões (até 4,6%);
   - abertura diferente em 22 (até 16,8%);
   - máxima/mínima diferentes em cerca de 22 sessões;
   - nenhuma barra válida em 2 sessões oficiais (2017-05-29 com barra
     preenchida de volume zero, 2020-11-20 sem barra);
   - 10 barras de preenchimento em dias de bolsa fechada.

**Correções.**

1. `B3Calendar` v2 com as regras históricas, equivalente às 2649 sessões
   oficiais por teste (commit `41a40e8`).
2. **Fonte de preço científica**, por decisão dos autores em 2026-10-04: o
   OHLCV bruto oficial da B3 (COTAHIST, mercado à vista, lote padrão)
   multiplicado pelo fator de ajuste por sessão do yfinance (`Adj Close /
   Close`). A representação de preço continua "retorno total ajustado pelo
   fator do yfinance" (protocolo, seção 4); muda só a origem do preço bruto.
3. **Semântica de sessão científica:**
   - sessão científica = sessão oficial da B3 em que o PETR4 negociou;
   - barra de preenchimento nunca existe no snapshot, nunca conta para
     `minimum_history_sessions` e nunca alimenta indicador;
   - sessão oficial sem negócio do ativo é lacuna de dado e falha fechado,
     salvo evidência objetiva de suspensão;
   - fator ausente só é herdado da sessão anterior se coincidir (até 1e-6)
     com o da seguinte.
4. A tolerância numérica de 1e-12 do gate OHLC fica como está. É correção
   numérica, não de dado: nenhuma barra é alterada, e inconsistências reais
   (1e-9 ou mais) continuam recusadas.

**Evidência já observada antes deste amendment.**
- A seleção de H_real v1.
- O primeiro Hardening com LOW: gates passaram; só métricas outcome-blind.
- O primeiro B0: PASS.

Nada disso influenciou as correções acima, que são verificáveis contra fonte
oficial.

**Impacto sobre comparabilidade.**
- O snapshot muda, então os payloads de H_real e o histórico de todo estado
  real mudam.
- O Hardening e o B0 iniciais ficam
  **SUPERSEDED BY CALENDAR-CORRECTED REBASELINE**. Eles são preservados (não
  apagados) como evidência de processo, mas deixam de ser o baseline.
- A regra congelada de H_real é reaplicada sem mudança sobre o snapshot
  corrigido.
- O Hardening roda de novo do zero, com a mesma configuração e começando em
  LOW, e o B0 de novo.
- O snapshot anterior (`20261004T193839031891Z-6f5e2439…`) é mantido
  localmente, com identidade registrada na seção 7.

**Única causa da repetição:** correção objetiva de calendário e de qualidade
de dados.

**Reaplicação da regra congelada de H_real (sem mudança de regra).**

```text
snapshot     20261004T201258177516Z-b4cf39fc761f251d2dd18e787008345a
identidade   b4cf39fc761f251d2dd18e787008345aaf02bd9e19f913390c510338b84ee7d4
arquivo      data/PETR4.SA.csv sha256 7b6a0018191028ecea2ee66785c27f771a721aa4a96c4953ca87ac6d688c3ffa
fonte        COTAHIST (OHLCV oficial) x fator yfinance; 2016-01-01..2026-08-31
status       READY: 2649 barras = 2649 sessões oficiais, nenhuma faltando ou sobrando
vs anterior  (até 2024-02-28) +1 sessão: 2020-11-20
             -9 barras de preenchimento em bolsa fechada: 2017-06-15, 2017-09-07, 2017-10-12, 2017-11-02, 2017-11-15, 2017-11-20, 2017-12-25, 2017-12-29, 2018-01-25
             2017-05-29 passa a ser a barra oficial (antes: preenchimento de volume zero)
             0 barras de volume zero
|E|          1519 (de 2018-01-12 a 2024-02-28; 2018-01-12 tem exatamente 504 sessões)
sha256 de E  bad805ba20fdcc9364197a5690ae7cfcf0d83302124c8ea0271256659f013eae
```

| q | índice/sessão antigos | índice/sessão novos | mudou? | sha256 do payload novo |
|---:|---|---|---|---|
| 0.20 | 303 / 2019-04-08 | 303 / 2019-04-09 | sim | `0bd54bbfed6c1acb4952b8a014f45886bec6d65b18a501a892adc1e17b458392` |
| 0.40 | 607 / 2020-06-29 | 607 / 2020-06-30 | sim | `67c37ce000f8a770a68ed6aa965a909bc28fb09d76636b4aa121b9f841287522` |
| 0.60 | 910 / 2021-09-17 | 910 / 2021-09-17 | não (payload mudou) | `03daed6627b7b1cdcaba0d1c0638f5592dc0770cc9aa189582191f9402d519be` |
| 0.80 | 1214 / 2022-12-07 | 1214 / 2022-12-07 | não (payload mudou) | `99be89f0019d862c53ff955cad873042d31251e024a0a5ed2eb0e14b68b5a449` |

Os índices são os mesmos. As datas de q = 0.20 e 0.40 andam uma sessão
porque a barra de preenchimento de 2018-01-25 deixou de existir em E. Todos os
payloads mudam porque o preço bruto agora é o oficial.

#### PROTOCOL AMENDMENT 2 — ÂNCORAS CAL-A/CAL-B E GRADE DE CAL-A

```text
DATA              2026-10-04
TIPO              preenchimento de itens TBD do protocolo por regra mecânica
                  predeclarada pelos autores; nenhuma regra existente muda
OBSERVADO ANTES   Hardening e B0 (outcome-blind, só gates); NENHUM resultado
                  de âncora, nenhum retorno, nenhuma volatilidade de âncora
IMPACTO           CAL-A e CAL-B passam a ter datas; a seção 14 deixa de ser
                  CAL_A_CANDIDATE_GRID_UNRESOLVED; nada anterior é invalidado
```

**Domínio.**
- Sessões PETR4.SA do snapshot corrigido (sessão oficial B3 com barra
  observada), de 2018-01-12 a 2024-02-28, com
  `available_history_sessions >= 504` e contrato causal satisfeito, menos as
  4 sessões de H_real.
- Total: 1515 sessões; sha256 `9dd54e3fdf8e377429e0d87b431600df569ee6cab00f0f30297ac8a289828827`.

**Estratos.**
- 30 blocos cronológicos contíguos, tamanhos tão iguais quanto possível
  (`numpy.array_split`: os primeiros `len % 30` estratos têm uma sessão a mais).
- A âncora é a sessão mediana, de índice `(k - 1) // 2` em base 0, ou seja, a
  mediana inferior quando `k` é par.
- CAL-B = estratos 3, 6, …, 30; CAL-A = os demais.

| estrato | primeira | última | sessões | âncora | conjunto |
|---:|---|---|---:|---|---|
| 1 | 2018-01-12 | 2018-03-28 | 51 | 2018-02-21 | CAL-A |
| 2 | 2018-03-29 | 2018-06-12 | 51 | 2018-05-07 | CAL-A |
| 3 | 2018-06-13 | 2018-08-23 | 51 | 2018-07-19 | CAL-B |
| 4 | 2018-08-24 | 2018-11-07 | 51 | 2018-10-01 | CAL-A |
| 5 | 2018-11-08 | 2019-01-28 | 51 | 2018-12-17 | CAL-A |
| 6 | 2019-01-29 | 2019-04-12 | 51 | 2019-03-07 | CAL-B |
| 7 | 2019-04-15 | 2019-06-27 | 51 | 2019-05-22 | CAL-A |
| 8 | 2019-06-28 | 2019-09-09 | 51 | 2019-08-05 | CAL-A |
| 9 | 2019-09-10 | 2019-11-21 | 51 | 2019-10-15 | CAL-B |
| 10 | 2019-11-22 | 2020-02-06 | 51 | 2020-01-02 | CAL-A |
| 11 | 2020-02-07 | 2020-04-23 | 51 | 2020-03-17 | CAL-A |
| 12 | 2020-04-24 | 2020-07-08 | 51 | 2020-06-01 | CAL-B |
| 13 | 2020-07-09 | 2020-09-18 | 51 | 2020-08-13 | CAL-A |
| 14 | 2020-09-21 | 2020-12-02 | 51 | 2020-10-27 | CAL-A |
| 15 | 2020-12-03 | 2021-02-22 | 51 | 2021-01-13 | CAL-B |
| 16 | 2021-02-23 | 2021-05-05 | 50 | 2021-03-29 | CAL-A |
| 17 | 2021-05-06 | 2021-07-16 | 50 | 2021-06-10 | CAL-A |
| 18 | 2021-07-19 | 2021-09-28 | 50 | 2021-08-20 | CAL-B |
| 19 | 2021-09-29 | 2021-12-10 | 50 | 2021-11-04 | CAL-A |
| 20 | 2021-12-13 | 2022-02-22 | 50 | 2022-01-18 | CAL-A |
| 21 | 2022-02-23 | 2022-05-09 | 50 | 2022-03-31 | CAL-B |
| 22 | 2022-05-10 | 2022-07-19 | 50 | 2022-06-13 | CAL-A |
| 23 | 2022-07-20 | 2022-09-28 | 50 | 2022-08-23 | CAL-A |
| 24 | 2022-09-29 | 2022-12-13 | 50 | 2022-11-04 | CAL-B |
| 25 | 2022-12-14 | 2023-02-24 | 50 | 2023-01-18 | CAL-A |
| 26 | 2023-02-27 | 2023-05-10 | 50 | 2023-03-31 | CAL-A |
| 27 | 2023-05-11 | 2023-07-20 | 50 | 2023-06-15 | CAL-B |
| 28 | 2023-07-21 | 2023-09-29 | 50 | 2023-08-24 | CAL-A |
| 29 | 2023-10-02 | 2023-12-13 | 50 | 2023-11-07 | CAL-A |
| 30 | 2023-12-14 | 2024-02-28 | 50 | 2024-01-22 | CAL-B |

```text
CAL-A (20)  2018-02-21, 2018-05-07, 2018-10-01, 2018-12-17, 2019-05-22, 2019-08-05, 2020-01-02, 2020-03-17, 2020-08-13, 2020-10-27, 2021-03-29, 2021-06-10, 2021-11-04, 2022-01-18, 2022-06-13, 2022-08-23, 2023-01-18, 2023-03-31, 2023-08-24, 2023-11-07
            commitment sha256 253308eaf069bbeb085e79aa1fe36cf510eecfc3d4cd5b5f6762a77bce36a36f
CAL-B (10)  commitment sha256 51d73b2285d4e0e103bfb3fc4f5cd26892a6b96fe7dbe8d43cd1e429937f38c0
            (datas em src/experiments/anchors.py; trancadas no runner por
             CAL_B_AUTHORIZED = False até a fase autorizada; Stress Probing
             não pode usar nenhum estrato de CAL-B)
```

**Auditoria de unidade da volatilidade de risco.**

| item | valor |
|---|---|
| fórmula | desvio-padrão amostral (ddof = 1) dos retornos simples diários close-to-close |
| janela | últimos `volatility_window` retornos até `t` |
| frequência | diária |
| anualização | multiplicada por √252 |
| unidade | decimal (0.50 = 50%) |
| regra | arredondada a 6 casas, veta se `vol > risk_max_volatility` |

É volatilidade anualizada em decimal, como a hipótese de grade supunha.

**Grade de CAL-A congelada** (produto cartesiano, nada pode ser acrescentado):

| config_id | volatility_window | risk_max_volatility | |
|---:|---:|---:|---|
| 1 | 21 | 0.40 | |
| 2 | 21 | 0.50 | baseline |
| 3 | 21 | 0.60 | |
| 4 | 63 | 0.40 | |
| 5 | 63 | 0.50 | |
| 6 | 63 | 0.60 | |

**Justificativa ex ante.**
- 21 sessões ≈ horizonte mensal; 63 sessões ≈ horizonte trimestral.
- 0.50 é o baseline preexistente; 0.40 e 0.60 são perturbações simétricas em
  torno dele.

**Gate de identificabilidade** (regra da seção 14):
- Para cada configuração e cada âncora de CAL-A, calcular a volatilidade só
  com informação até `t` e o veto que ela produziria.
- `distinguishing_anchors` = âncoras em que ao menos duas configurações
  diferem no veto.
- Se `distinguishing_anchors < 3`, `CAL-A = REMOVED`; se `>= 3`,
  `CAL-A = REDUCED`.

#### PROTOCOL AMENDMENT 3 — EXECUÇÃO DE CAL-A (registrada antes da primeira execução)

```text
DATA              2026-10-04
OBSERVADO ANTES   Hardening/B0 (outcome-blind) e o gate de identificabilidade
                  (só vetos até t); NENHUM retorno de âncora
NÃO MUDA          grade, âncoras, modelo, thinking, prompts, gates, custos,
                  fonte de preço, regra de execução, tratamento
```

**Fonte científica conferida.**
- Sessões e OHLCV bruto vêm da B3 (COTAHIST); o Yahoo fornece só o fator de
  ajuste.
- O Yahoo não cria sessão, não substitui OHLC bruto, não preenche barra e não
  decide se houve pregão: o extrator parte do COTAHIST e falha fechado no
  resto.
- Snapshot `20261004T201258177516Z-b4cf39fc…`, identidade
  `b4cf39fc761f251d2dd18e787008345aaf02bd9e19f913390c510338b84ee7d4`, com os
  hashes COTAHIST no manifest.

**Checagem causal do fator.**
- Os proventos posteriores a `t` multiplicam todo o histórico causal
  `[.., t]` pela mesma constante.
- Gaps de SMA, gaps e largura de Bollinger, RSI, razões de MACD e a
  volatilidade de risco são invariantes a esse fator comum:
  - bit a bit para fatores potência de dois;
  - payload canônico idêntico para fatores reais do PETR4.
- Só proventos anteriores a `t` (informação passada legítima) mudam as
  features.
- Teste: `tests/agents/test_causal_adjustment.py`. Nenhum leakage encontrado.

**Configurações.** Os `config_id` 1–6 já congelados no Amendment 2 são usados
como estão (produto `{21, 63} × {0.40, 0.50, 0.60}`, nesta ordem):

| config_id | window | max_vol |
|---:|---:|---:|
| 1 | 21 | 0.40 |
| 2 | 21 | 0.50 (baseline) |
| 3 | 21 | 0.60 |
| 4 | 63 | 0.40 |
| 5 | 63 | 0.50 |
| 6 | 63 | 0.60 |

Consequência declarada: o desempate por menor `config_id` aponta para 1, não
para o baseline. Fixos em todas: `risk_max_drawdown = 0.25`,
`risk_max_concentration = 1.0`, `long_target_weight = 1.0` e todo o freeze v1
com LOW.

**Repetições.** `CAL_A_REPETITIONS = 3`, dentro de R <= 3. O tratamento tem
inferência estocástica sem seed; uma realização favorável ao acaso não pode
escolher configuração.

**Realizações pareadas e banco de chamadas.**
- Dentro de cada repetição, toda chamada é guardada por
  `(repetição, LLMCallRequest.identity_digest)`.
- A primeira chamada com uma identidade vai ao provedor; as seguintes com a
  mesma identidade reproduzem a resposta e a evidência guardadas.
- O prompt técnico não depende da grade, então as 6 configurações de cada
  (âncora, repetição) usam a mesma realização técnica de 5 chamadas: 300
  chamadas técnicas ao vivo, não 1.800.
- Risco e portfólio só compartilham resposta quando a identidade é
  exatamente igual. Janelas diferentes mudam `recent_volatility` no prompt do
  risco e fazem chamadas próprias, por consequência legítima do candidato.

**Ordem.**

```text
for anchor in CAL_A_ANCHORS (cronológica):
    for replicate in 1..3:
        for config_id in 1..6:
            run de âncora do ExperimentRunner com o banco compartilhado
```

São 360 avaliações. Nenhum resultado parcial para, pula, reordena ou muda
nada. Cada avaliação parte do capital inicial em caixa e posição zero e não
herda estado de outra.

**Escore e seleção.**
- `anchor_score[c,a]` = média aritmética do retorno líquido realizado
  (`final_equity / initial_capital − 1`, CostSpec congelado) nas 3
  repetições.
- `S1[c]` = média de `anchor_score[c,a]` nas 20 âncoras.
- Maior S1 vence. Empate exato → menor `config_id`. Todos iguais →
  `CAL_A_DISCRIMINATION = NONE` e o mesmo fallback.
- Sharpe, Sortino, MDD, turnover e win rate não entram na seleção.

**Falhas.** Uma falha técnica final não vira retorno zero nem HOLD: é
registrada e interrompe CAL-A. Nenhuma seleção é feita com conjunto
incompleto. Erro transitório recuperado é só registrado.

**CAL-B.** `CAL_B_AUTHORIZED = False` é exigido antes e depois da execução. O
banco recusa qualquer sessão de CAL-B; o runner recusa janela que a contenha.

#### PROTOCOL AMENDMENT 4 — FALHA DE INFRAESTRUTURA NA PERSISTÊNCIA DA CAL-A (técnico)

```text
DATA              2026-10-04
TIPO              bug objetivo de infraestrutura; nenhuma regra científica muda
O QUE ACONTECEU   a CAL-A parou na avaliação 184/360 (2021-03-29, r1, config 4):
                  o Windows recusou (PermissionError, WinError 5) o rename
                  atômico que publica o diretório do run; tipicamente
                  antivírus/indexador segurando um handle por instantes
CORREÇÃO          rename_with_retry (src/artifacts.py): repete só
                  PermissionError, com espera crescente (até ~64 s), em todo
                  rename atômico (runner e snapshot); outros erros sobem na
                  hora. Não toca decisão, identidade, trace nem resultado
COMPARABILIDADE   a correção é só de persistência: a classe de
                  comparabilidade não muda
```

**Bloco afetado e reexecução** (regra "reexecutar o bloco afetado"):
- No desenho pareado, o bloco é o par (âncora, repetição): as 6
  configurações compartilham uma realização técnica.
- Os 30 blocos completos da execução abortada (180 avaliações, âncoras 1–10)
  continuam válidos e são reaproveitados como estão.
- O bloco parcial (2021-03-29, r1; configurações 1–3 concluídas) é descartado
  inteiro e reexecutado com as 6 configurações.
- As demais avaliações seguem na ordem congelada.

A execução abortada fica preservada em
`docs/evidence/cal_a/run_20261004T203435Z/`, e as 3 avaliações do bloco
descartado ficam lá, fora do escore. Nenhuma seleção foi feita com o conjunto
incompleto.

#### PROTOCOL AMENDMENT 5 — SEQUENTIAL DEVELOPMENT DO H2 E H2_SCIENTIFIC_SHARPE_DEFINITION_V1

```text
DATA              2026-10-04
TIPO              registro pré-execução; decidido pelos autores ANTES de
                  qualquer chamada ao provedor e de qualquer retorno da janela
COMMIT            SEQUENTIAL_DEV_FREEZE_COMMIT = o commit que introduz este
                  amendment (registrado no log de execução abaixo)
```

**H2_SCIENTIFIC_SHARPE_DEFINITION_V1** (`src/backtesting/metrics.py`,
`scientific_sharpe`). Vale para Sequential Development, CAL-B, Validation,
Final Test e toda comparação H2 por Sharpe.

```text
r_t     = equity_t / equity_{t-1} - 1, todos os retornos diários LÍQUIDOS
          (CostSpec congelado) da curva científica da janela, inclusive o
          da sessão de liquidação; dias em caixa (r_t = 0) PERMANECEM
rf      = 0.0 ao ano  (rf_diário = rf / 252)
Sharpe  = mean(r - rf/252) / std(r, ddof = 1) * sqrt(252)
```

Convenção de escore do protocolo (não é propriedade matemática do Sharpe):
- menos de 2 retornos → 0.0;
- desvio-padrão amostral NaN ou < 1e-15 → 0.0. Isso inclui trajetória toda em
  caixa e série constante diferente de zero.

Assim toda trajetória, inclusive a inativa, continua completa e comparável.
Dado inválido (NaN/inf, curva corrompida) não cai na convenção: falha fechado.
Um golden test (`tests/backtesting/test_scientific_sharpe.py`) impede mudança
silenciosa da definição.

**Janela da fase** (`src/experiments/phases.py`).

```text
SEQUENTIAL_DEVELOPMENT_START  2024-03-01  primeira sessão de decisão
última sessão de decisão      2024-08-29  (127 sessões de decisão B3)
SEQUENTIAL_DEVELOPMENT_END    2024-08-30  só liquidação e marcação final
VALIDATION_START              2024-09-02
CAL-A ∩ janela = CAL-B ∩ janela = ∅      (teste)
```

**Invariante `no_order_execution_may_cross_phase_boundary`.**
- Decisão em close(t) executa em open(t+1), então a sessão de liquidação
  precisa estar dentro da mesma fase da janela de decisão.
- O runner recusa, antes de construir o participante, janela que atravessa a
  fronteira ou cuja liquidação cairia na fase seguinte.
- O runner recorta os dados de mercado em `phase.end`: nenhum preço posterior
  a 2024-08-30 chega ao motor.
- A regra vale para toda fronteira declarada em `PHASES`.

**Candidatos.** Só `risk_max_drawdown` é selecionado.
- Base: H2_FREEZE_V1_PARAMS com `thinking_level = low` e a configuração de
  CAL-A (`volatility_window 21`, `risk_max_volatility 0.40`).
- `decision_frequency = 1` e `risk_max_concentration = 1.0` seguem
  congelados. Os autores fecham a proposta "N_seq ≤ 4, R_seq ≤ 2" da seção
  de contenção do protocolo como abaixo.

```text
D01  config_id 1  risk_max_drawdown 0.25   (baseline)
D02  config_id 2  risk_max_drawdown 0.15
D03  config_id 3  risk_max_drawdown 0.35
SEQUENTIAL_DEV_REPETITIONS = 3
```

**Semântica de drawdown** (auditada, não muda):
- `current_drawdown = (peak − equity) / peak`, com equity marcada em
  close(t).
- O pico é interno ao run e começa no capital inicial em `decision_start`.
- Há veto de risco só sobre COMPRA com drawdown canônico > limite.
- O limite veta entrada; não é stop-loss. Já no alvo, uma COMPRA é
  `BUY_AT_TARGET_NOOP`, sem ordem.
- Propriedade de stop persistente: em caixa abaixo do pico a equity é
  constante, então novas COMPRA continuam vetadas até o fim da janela.

**Execução pareada.**

```text
for replicate in 1..3:
    for config in D01, D02, D03:
        run sequencial do ExperimentRunner, 2024-03-01..2024-08-29
```

- O banco de chamadas guarda cada chamada por
  `(repetição, LLMCallRequest.identity_digest)`.
- O Technical SC de cada (sessão, repetição) é chamado uma vez e reproduzido
  byte a byte nas três configurações, porque o prompt técnico não depende da
  grade.
- Risk e Portfolio só reaproveitam resposta com identidade idêntica.
- Os portfólios são independentes e dependentes do caminho: cada run parte de
  R$100.000 em caixa.

**Escore e seleção.**

```text
Sharpe[c, r]  = H2_SCIENTIFIC_SHARPE_DEFINITION_V1 da curva do run (c, r)
S2[c]         = mean(Sharpe[c, 1..3])
maior S2 vence; empate EXATO -> menor config_id
S2 iguais nas três -> SEQUENTIAL_DEV_DISCRIMINATION = NONE,
                      D01 selecionada, basis PROTOCOL_TIE_FALLBACK
senão              -> SEQUENTIAL_DEV_DISCRIMINATION = YES, basis EMPIRICAL_S2
```

Retorno terminal, MDD, Sortino, turnover, trades, tempo em mercado e contagem
de vetos são reportados como **NOT USED FOR SELECTION**. Todos os números da
fase são development evidence, nunca resultado científico.

**Falhas e retomada.**
- Uma falha técnica final não vira retorno zero nem HOLD: interrompe a fase.
- O bloco mínimo reaproveitável é a repetição completa (D01–D03), que
  compartilha uma realização técnica.
- Uma repetição interrompida é descartada inteira e refeita com Technical
  novo.
- Nenhuma seleção é feita com conjunto incompleto.

**Proveniência de CAL-A.** `CAL_A_DISCRIMINATION = NONE` e
`CAL_A_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK`. A configuração
`volatility_window 21 / risk_max_volatility 0.40` veio do desempate pelo
config_id, não de desempenho superior; o protocolo não afirma que ela foi
melhor.

**CAL-B.** `CAL_B_AUTHORIZED = False` é exigido antes e depois. O banco
recusa qualquer sessão de CAL-B.

#### PROTOCOL AMENDMENT 6 — STRESS_PROBING_FREEZE_V1

```text
DATA              2026-10-04
TIPO              registro pré-execução; decidido pelos autores ANTES de
                  calcular qualquer métrica de mercado dos estratos, de
                  selecionar qualquer janela e de qualquer chamada ao provedor
COMMIT            STRESS_FREEZE_COMMIT = o commit que introduz este amendment
OBSERVADO ANTES   Hardening/B0, CAL-A e Sequential Development (já registrados
                  abaixo); nenhuma métrica de Stress, nenhuma resposta do LLM
                  em janela de Stress
NÃO MUDA          modelo, thinking, temperature, prompts, N, limiar, risco,
                  janela de volatilidade, decision_frequency, custos, retry,
                  fonte de preço, regra de execução, Sharpe v1
```

Código: `src/experiments/stress.py` (constantes, métricas, seleção, probes),
`scripts/run_stress.py` (`select` e `run`) e `ExperimentRunner(boundaries=...)`.

**Autoridade: nenhuma.** O Stress tenta falsificar o sistema congelado,
exercita mercado adverso, confere contratos causais e de risco e mede robustez
operacional e comportamental antes de CAL-B/Validation. Não escolhe
`risk_max_drawdown` nem qualquer outro parâmetro, não reabre CAL-A, não altera
modelo, thinking, temperature, prompt ou limiar. Todo resultado financeiro é
`DIAGNOSTIC / DEVELOPMENT EVIDENCE ONLY` e nunca seleciona configuração.

**Divergência registrada em relação ao protocolo (seções 5.5 e 5.12).** O
protocolo previa "≤ 8 âncoras adicionais fora do CORE" e um Stress Probing
durante o Diagnostic Hardening. Fica assim:
- o Stress Probing durante o Hardening nunca rodou (o Hardening usou H, seção
  8); esta é a única passagem de Stress e ocupa o lugar do Stress Report,
  depois do Sequential Development e antes de CAL-B;
- as janelas são **sequenciais** (um estrato completo cada), não âncoras
  isoladas: mercado adverso precisa de caminho (drawdown, gaps, sequência de
  decisões) para exercitar os contratos de risco e de execução;
- são 4 janelas escolhidas mecanicamente **dentro** dos 20 estratos não-CAL-B.
  CAL-A continua com 20 âncoras e já está fechada; as janelas contêm âncoras de
  CAL-A, o que é legítimo porque o Stress pertence a development e não tem
  autoridade;
- `STRESS ∩ CAL-B = ∅` passa a valer no nível do **estrato inteiro**, mais
  forte que no nível da âncora.

**Configuração H2 congelada** (`STRESS_FROZEN_PARAMS`, travada por teste):

```text
runtime        gemini / gemini-3.8-flash, Gemini API nativa
               thinking_level low · temperature 1.0 · max_output_tokens 8192
               seed nenhuma (nunca transmitida)
SC             analyst_count 5 · consensus_threshold 0.6 · require_all_votes true
execução       decision_frequency 1 · strict_inputs true ·
               portfolio_inversion_policy fail
posição        long_target_weight 1.0
risco          volatility_window 21 · risk_max_volatility 0.40 ·
               risk_max_drawdown 0.25 · risk_max_concentration 1.0
operacional    retry_attempts 6 · retry_base_delay 2.0 (inalterados)
custos         CostSpec congelado (spread 5 bps, tax 0.00032) · R$100.000 ·
               fractional_notional
```

**Proveniência das calibrações.**

```text
CAL_A_DISCRIMINATION = NONE             CAL_A_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK
SEQUENTIAL_DEV_DISCRIMINATION = NONE    SEQUENTIAL_DEV_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK
```

`21 / 0.40` e `0.25` são parâmetros congelados por regra protocolar de
desempate. O protocolo não afirma que tiveram desempenho superior.

**Domínio e universo.**
- Domínio: 2018-01-12..2024-02-28, snapshot corrigido
  `20261004T201258177516Z-b4cf39fc…` (o do Amendment 1). Fora: janela do
  Sequential Development, CAL-B, Validation e Final Test.
- Universo de seleção: os 20 estratos não-CAL-B do Amendment 2, com as
  fronteiras exatas daquela tabela (`STRESS_ELIGIBLE_STRATA`).
- Estratos CAL-B (3, 6, …, 30) ficam fora: nenhuma métrica de seleção é
  calculada sobre eles, e nenhuma sessão deles é decisão, liquidação ou
  performance do Stress. Barras anteriores podem aparecer só como warm-up
  causal de indicador. `CAL_B_AUTHORIZED = False` durante toda a tarefa.
- As 4 sessões de H_real caem todas em estratos CAL-B; a seleção recusa estrato
  cujo conjunto de sessões difira do domínio congelado.

**Métricas market-only** (`market_stress_metrics`), só sobre as barras de
**dentro** de cada estrato elegível, preço científico ajustado:

```text
M1 MAX_DRAWDOWN             max(1 - close / cummax(close)), magnitude >= 0
M2 MAX_REALIZED_VOLATILITY  std(r, ddof=1) * sqrt(252), r = retorno simples
                            close-to-close entre sessões do estrato
M3 WORST_DAILY_RETURN       min(r)  (mais negativo = mais adverso)
M4 MAX_ABS_OVERNIGHT_GAP    max |open_t / close_{t-1} - 1|, t da 2ª sessão em
                            diante (testa close(t) -> open(t+1))
```

**Seleção mecânica.** Exatamente 4 janelas, uma por categoria, na ordem fixa
M1, M2, M3, M4. Em cada categoria: ordenar pelo escore adverso (M1, M2 e M4
decrescente; M3 crescente); empate → menor `stratum_id`; escolher o primeiro
estrato ainda não escolhido. Resultado: 4 estratos distintos, sem substituição
manual. Janela é sempre um estrato completo; nenhuma janela manual em torno de
evento, nenhum ajuste de início/fim.

**Compromisso** (commit separado, antes da primeira chamada):
`docs/evidence/stress/selection.json` (métricas dos 20 estratos, rankings
completos, SHA-256 de cada ranking, snapshot, proveniência de preço, regra de
desempate e as 4 janelas), `docs/evidence/stress/risk_probes.json` e
`STRESS_SELECTED_WINDOWS` / `STRESS_FREEZE_COMMIT` em `stress.py`. O `run`
recusa executar se as constantes estiverem vazias, divergirem do arquivo ou se
o arquivo não tiver sido calculado neste commit de freeze. Depois desse commit
as quatro janelas ficam congeladas, mesmo que pareçam pouco estressantes.

**Janela e fronteira.**

```text
decisões     primeira .. penúltima sessão do estrato
liquidação   última sessão do estrato: executa o pendente em open, marca em close
no_order_execution_may_cross_stress_window_boundary
             a janela é passada ao runner como fronteira (boundaries); a regra
             de fase recusa, ANTES de construir o participante, janela cuja
             liquidação caia fora, e corta os dados de mercado na última
             sessão: nenhum preço posterior chega ao motor, à equity, ao
             Sharpe, ao MDD ou à liquidação
             nenhuma ordem pode entrar no estrato seguinte (CAL-B ou não)
```

O cliente do provedor recusa qualquer sessão fora das sessões de decisão da
janela corrente e qualquer sessão de estrato CAL-B.

**Repetições e estado inicial.** `STRESS_REPETITIONS = 3`. Ordem:
S1 r1..r3, S2 r1..r3, S3, S4 — 12 trajetórias, inferência live independente,
sem seed. R não aumenta depois de observar resultado. Cada trajetória começa
com R$100.000 em caixa, posição zero, pico = capital inicial, histórico causal
só para features, mesmos custos e mesmo quantity mode. Nenhuma posição passa de
uma janela ou repetição para outra.

**Sharpe.** `H2_SCIENTIFIC_SHARPE_DEFINITION_V1`, sem mudança; no Stress é
descritivo e não tem threshold.

**Gates (só integridade/contrato).** Não existe threshold de retorno, Sharpe,
Sortino, MDD ou turnover; perder dinheiro é evidência válida.

```text
S-A  falhas técnicas/provedor finais = 0 (retry recuperado não conta) e
     12/12 trajetórias completas
S-T  truncamentos MAX_TOKENS / length = 0
S-C  0 ordem fora da janela, 0 sessão de decisão diferente da janela, curva de
     first a last, liquidação e data_end = última sessão do estrato, 0 sessão de
     trace fora das decisões, 0 sessão em estrato CAL-B, 0 dado >= 2024-03-01
     (Validation/Final), 0 divergência entre drawdown/volatilidade recalculados
     e os enviados ao LLM de risco
S-R  toda COMPRA com volatilidade canônica > 0.40 termina em regra dura
     VOLATILITY, e toda COMPRA com drawdown canônico > 0.25 (volatilidade
     <= 0.40) em regra dura DRAWDOWN, sem chamada ao LLM de risco naquela
     sessão; e nenhuma regra dura dispara sem a violação correspondente
```

Drawdown canônico em close(t) = `(pico − equity) / pico`, pico interno ao run
começando no capital inicial; volatilidade = mesmo caminho do participante
sobre o histórico até t; ambos quantizados a 6 casas (o valor que a regra vê).

**Cobertura.**
- Regra de volatilidade `EXERCISED` se ≥ 1 COMPRA nas 12 trajetórias tiver
  volatilidade canônica > 0.40; senão `NOT_EXERCISED` e
  `HISTORICAL_STRESS_VOLATILITY_RULE_NOT_EXERCISED`.
- Regra de drawdown `EXERCISED` se ≥ 1 COMPRA tiver drawdown canônico > 0.25
  com volatilidade ≤ 0.40 (ramo em que a regra de drawdown decide; a de
  volatilidade vem antes). COMPRA com as duas violações é contada à parte,
  como mascarada. Senão `NOT_EXERCISED` e
  `HISTORICAL_STRESS_DRAWDOWN_RULE_NOT_EXERCISED`.
- COMPRA já no alvo continua passando pela regra dura (fonte HARD_RULE) e é
  classificada `BUY_AT_TARGET_NOOP` (sem ordem).

Regra não exercitada é limitação de cobertura, não aprovação implícita, e não
autoriza criar janela nova depois do resultado.

**Probes determinísticos** (`risk_contract_probes`, sem performance e sem
selecionar nada). Estado válido, sinal COMPRA, demais métricas abaixo dos
limites, LLM de risco contável:

```text
drawdown 0.249999 / 0.250000 -> sem veto de drawdown (LLM consultado)
drawdown 0.250001            -> veto duro DRAWDOWN, LLM não chamado
volatilidade 0.399999 / 0.400000 -> sem veto (LLM consultado)
volatilidade 0.400001            -> veto duro VOLATILITY, LLM não chamado
quantização  0.2499996, 0.2500004 -> canônico 0.250000 -> sem veto
             0.2500006            -> canônico 0.250001 -> veto
             (idem 0.3999996 / 0.4000004 / 0.4000006 na volatilidade)
precedência  COMPRA com as duas violações -> VOLATILITY
VENDA/MANTER com drawdown > 0.25 e/ou volatilidade > 0.40
             -> AUTO_APPROVE, sem LLM de risco (não aumentam exposição)
```

**Diagnósticos por trajetória** (DESCRIPTIVE ONLY): Sharpe científico, retorno
líquido terminal, MDD, Sortino, turnover, trades, tempo em mercado, drawdown e
volatilidade máximos vistos nas decisões, holds técnicos explícitos,
no-majority, vetos duros de volatilidade e drawdown, vetos do LLM de risco,
PORTFOLIO_HOLD, BUY_AT_TARGET_NOOP, retries, tokens e latência. Por janela,
sensibilidade estocástica entre as 3 repetições: sessões com consenso técnico
diferente, sessões com causa final diferente, primeira divergência de
exposição, ação final por repetição e faixas de trades, Sharpe, retorno e MDD.
Nenhum threshold novo.

**Falhas.** Bug objetivo, corrupção de artefato, violação de fronteira ou run
incompleto: parar, sem imputar. Correção técnica exige amendment, commit e a
repetição das **12** trajetórias (nenhum checkpoint é predeclarado). As janelas
não mudam. Erros transitórios (429/5xx/reset/timeout) recuperados pelo retry são
registrados e a execução continua, sem trocar modelo nem política de retry;
falha final é S-A FAIL.

**Sem autoridade de parâmetro.** Depois do Stress é proibido alterar
`risk_max_drawdown`, `risk_max_volatility`, `volatility_window`, N, limiar,
thinking, temperature, modelo, prompts, `decision_frequency` ou custos.
Comportamento economicamente ruim é registrado como resultado/limitação; só bug
objetivo gera amendment técnico.

**Status.** Se S-A, S-T, S-C e S-R passarem e `CAL_B_AUTHORIZED = False`:
`STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL`. Isso não significa que a
estratégia passou economicamente. CAL-B não é executada nesta tarefa.

#### PROTOCOL AMENDMENT 7 — CAL_B_PROTOCOL_FREEZE_V1

```text
DATA              2026-10-04
TIPO              registro pré-execução; decidido pelos autores ANTES de
                  qualquer chamada live sobre uma âncora de CAL-B
COMMIT            CAL_B_FREEZE_COMMIT = o commit que introduz este amendment
                  (contém também a autorização limitada)
OBSERVADO ANTES   Hardening/B0, CAL-A, Sequential Development, Stress (todos
                  registrados abaixo); NENHUMA resposta de modelo em âncora de
                  CAL-B, nenhum resultado de CAL-B
NÃO MUDA          configuração H2, prompts, modelo, thinking, custos, retry,
                  fonte de preço, threshold de degeneração do Hardening
```

Código: `src/experiments/cal_b.py` (gates, taxas de HOLD, pré-filtro léxico,
regra de status), `src/experiments/anchors.py` (`authorize_cal_b`,
`CalBAuthorization`, `CAL_B_STATUS`), `scripts/run_cal_b.py` (`run`, `audit`,
`status`).

**Disclosure do dry-run.** Antes deste commit, o executor foi exercitado
offline com um transporte HTTP falso (sem provedor, todas as respostas
COMPRA) para testar selo, journal, recuperação por replay e auditoria. Esse
ensaio expôs um fato de **entrada**, disponível em `t`: 4 das 10 âncoras têm
volatilidade canônica > 0.40. Nenhuma resposta de modelo e nenhum resultado
foi observado, e nenhuma regra abaixo foi escolhida com base nisso; todas vêm
da especificação da tarefa e de thresholds já congelados.

**Papel.** CAL-B = `ONE-SHOT OUT-OF-SAMPLE SANITY CHECK`. Verifica se a
configuração final de desenvolvimento executa integralmente, respeita o
information set, schemas, quorum e risco duro, produz rationale visível
coerente com os dados fornecidos, não inventa fato material e não degenera.
**Não** testa retorno, Sharpe, accuracy direcional, P&L ou vantagem sobre
benchmark; não tem autoridade de tuning. A primeira avaliação de performance
out-of-sample continua sendo a `PSEUDO-LIVE VALIDATION`.

**Âncoras.** Exatamente as 10 do Amendment 2 — 2018-07-19, 2019-03-07,
2019-10-15, 2020-06-01, 2021-01-13, 2021-08-20, 2022-03-31, 2022-11-04,
2023-06-15, 2024-01-22 —, com o compromisso integral
`51d73b2285d4e0e103bfb3fc4f5cd26892a6b96fe7dbe8d43cd1e429937f38c0`, conferido
antes da execução. Nenhuma data é trocada, movida ou acrescentada.

**Configuração** (`CAL_B_FROZEN_PARAMS` = `STRESS_FROZEN_PARAMS`, travada por
teste): gemini / gemini-3.8-flash, API nativa v1beta generateContent;
thinking low, temperature 1.0, max_output_tokens 8192, sem seed transmitida;
SC 5 × 0.6 com require_all_votes; decision_frequency 1, strict_inputs,
portfolio_inversion_policy fail; long_target_weight 1.0; volatility_window 21,
risk_max_volatility 0.40, risk_max_drawdown 0.25, risk_max_concentration 1.0;
retry 6 × 2.0. `CAL_A_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK` e
`SEQUENTIAL_DEV_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK`: nenhuma
superioridade empírica é afirmada.

**One-shot.** `CAL_B_REPETITIONS = 1`: uma realização live por âncora (com o
SC interno N = 5). Nunca rerodar por HOLD, veto, rationale estranho ou
resultado ruim.

**Independência.** Cada âncora parte de R$100.000 em caixa, posição zero,
pico = capital, participante novo e histórico causal até close(t). Nada passa
de uma âncora a outra (posição, equity, memória, trace, rationale). Respostas
live nunca são compartilhadas entre âncoras; não há call bank entre âncoras.

**Outcome-blind.** Para cada âncora: information set = barras do snapshot até
close(t) (a observação entregue ao participante termina em `t`); o sistema
congelado decide e produz o intent. **Não há execução**: `open(t+1)`,
`close(t+1)` e qualquer preço posterior nunca são lidos; o intent é validado
estruturalmente. Não se calcula retorno, P&L, Sharpe, Sortino, MDD, hit rate,
accuracy nem comparação com Buy&Hold ou controles. Não existe
`CAL_B_FINANCIAL_SCORE`.

**Batch selado.** As 10 âncoras rodam num lote automático, na ordem
comprometida, sem inspeção manual do conteúdo entre âncoras (o progresso só
mostra data e "sealed") e sem mudança de código no meio (retomada exige o
mesmo commit). Cada âncora selada grava `sealed.json` (SHA-256 de cada
artefato); o lote grava `batch.json` com os selos e `BATCH_SEAL.sha256`. Só
depois do selo o pacote comportamental é aberto (`audit` confere todos os
hashes antes).

**Consumo do holdout.**

```text
NÃO CONSUMIDA   falha antes de qualquer resposta live persistida (journal
                vazio): pode rodar de novo (run --resume)
PARCIAL         houve respostas live persistidas antes do crash: elas estão
                CONSUMIDAS. Cada resposta live é gravada (fsync) num journal
                por âncora antes de seguir; a recuperação reaproveita cada uma
                por replay exato da identidade (LLMCallRequest.identity_digest,
                mecanismo equivalente ao ReplayLLMClient), nunca nova
                inferência para substituí-la. Chamada que nunca teve resposta
                pode ser feita na recuperação. Se alguma resposta persistida
                não for reaproveitada exatamente: CAL_B_INVALID — PARTIAL
                HOLDOUT CONSUMED, e parar
CONSUMIDA       decisão/trace/rationale utilizável selado: nunca rerodar
```

**Autorização limitada.** `CAL_B_AUTHORIZED` (unlock global) continua
`False`: o runner e qualquer janela seguem recusando CAL-B. A única porta é
`authorize_cal_b(phase="CAL-B", commitment, as 10 datas na ordem,
repetitions=1)`, que recusa qualquer desvio e só funciona com
`CAL_B_STATUS = "SEALED"`. O cliente do provedor recusa qualquer sessão que
não seja a âncora em execução. Depois do lote, `CAL_B_STATUS = "CONSUMED"`
(commit de status) fecha a porta nesta versão metodológica.

**Gates automáticos.**

```text
CB-A  10/10 âncoras com decisão completa utilizável; 0 falha final de
      provedor/infra (retry recuperado não conta)
CB-S  0 resposta inválida, 0 quorum incompleto (5 técnicas, 5 votos válidos),
      0 violação de schema (revalidação de cada saída), 0 inversão de
      portfólio, 0 input científico faltando, 0 fallback silencioso (errors/
      failures, regras INVALID/MISSING), 0 finish_reason != STOP (inclui
      MAX_TOKENS), modelo resolvido e opções de transporte iguais ao freeze
CB-C  toda chamada na sessão t; histórico termina em t; payload técnico
      idêntico às 8 features recalculadas só com barras até t; métricas do
      prompt de risco idênticas às recalculadas até t (vol, drawdown 0,
      concentração 0); t <= 2024-02-28 (sem Validation/Final)
CB-R  COMPRA com vol > 0.40 termina em regra dura VOLATILITY sem chamada ao
      LLM de risco; regra dura nunca dispara sem violação; veto duro nunca é
      seguido de LLM de risco/portfólio; VENDA/MANTER auto-aprovados
CB-D  total_hold_rate < 0.90 com os códigos HOLD_RATE_CAUSES do Hardening
      (explicit hold, no-majority, vetos de risco, PORTFOLIO_HOLD;
      BUY_AT_TARGET_NOOP fora). Com 10 âncoras, 9 ou mais HOLD = FAIL
```

As taxas `explicit_hold_rate`, `no_majority_abstention_rate`,
`risk_veto_rate` e `portfolio_hold_rate` são reportadas separadamente.

**Rubrica de alucinação material** (só o texto visível dos schemas:
`justification`, `analysis`, `reasoning`; nunca hidden chain-of-thought).
`MATERIAL_UNSUPPORTED_CLAIM` = afirma fato específico, ausente do prompt
(system + user) daquele estágio, usado para justificar/alterar a decisão.
Exemplos de FAIL no Technical: ticker/empresa, data/calendário, preço
absoluto, notícia/balanço/petróleo/juros/política/macro, volume, retorno
futuro. Fato historicamente verdadeiro mas fora do information set continua
unsupported. Informação permitida por papel:
- Technical: as 8 features (sma50_gap, sma200_gap, bb_upper_gap,
  bb_lower_gap, bb_width, rsi, macd_ratio, macd_signal_ratio) e regras
  genéricas de análise técnica;
- Risk: o sinal técnico fornecido, as métricas canônicas fornecidas e regras
  gerais de risco;
- Portfolio: o que está no seu prompt (sinal técnico, veredito de risco) e as
  regras de direção do estágio.

**Coerência rationale/ação.** Technical: o texto não defende COMPRA
retornando VENDA ou vice-versa (MANTER pode vir de neutralidade/incerteza).
Risk: o texto não defende aprovação retornando VETADO, ou o contrário, sem
explicação coerente com as métricas; regras duras têm precedência e são
auditadas estruturalmente. Portfolio: o texto não recomenda direção oposta ao
campo estruturado; inversão estrutural continua fail-closed.

**Pacote comportamental** (`audit_packet.json` / `.md`), aberto só depois do
selo: por âncora, data, payload de features, as 5 saídas técnicas visíveis,
consenso, entrada/saída visível de Risk e Portfolio quando chamados, causa
final e reason codes, com system e user prompt de cada chamada. Sem retorno
t+1, P&L, Sharpe ou qualquer resultado posterior à decisão. O pré-filtro
léxico congelado (`PRESCREEN_LEXICON`) só aponta trechos para os revisores:
não aprova nem reprova.

**Revisão humana.** Os dois autores classificam cada âncora,
independentemente, em `review/AUTHOR_1.json` e `review/AUTHOR_2.json`:
`material_hallucination` e `rationale_action_coherence` = PASS/FAIL. O
sistema não é ajustado durante a revisão. Discordância em qualquer campo →
`CAL_B_REVIEW_DISAGREEMENT`, sem aprovação e sem rerodar âncora. Enquanto as
duas fichas não estiverem completas, o estado é
`CAL_B_AWAITING_HUMAN_REVIEW` (intermediário, não final).

**Regra de status** (`cal_b_status`).

```text
gate automático falhou                 -> CAL_B_FAIL — HOLDOUT CONSUMED
revisões incompletas                   -> CAL_B_AWAITING_HUMAN_REVIEW
revisões divergentes                   -> CAL_B_REVIEW_DISAGREEMENT
ambas concordam e há algum FAIL        -> CAL_B_FAIL — HOLDOUT CONSUMED
ambas concordam, tudo PASS             -> CAL_B_PASS — SANITY CHECK ONLY
recuperação exata impossível           -> CAL_B_INVALID — PARTIAL HOLDOUT CONSUMED
```

`CAL_B_PASS` significa só que a configuração congelada se comportou de forma
íntegra e não degenerada nas 10 âncoras holdout; não é desempenho OOS. Só com
ele: `SYSTEM_CALIBRATION_COMPLETE` e `READY FOR SYSTEM FREEZE`. Com FAIL:
parar e entregar evidência, sem corrigir e rerodar as mesmas 10, relaxar gate,
trocar prompt/parâmetro ou escolher âncoras; uma nova versão metodológica é
decidida fora desta tarefa.

**Evidência operacional.** Chamadas lógicas, tentativas HTTP, retries,
429/5xx/reset, tokens de entrada, saída e thinking, latência; custo monetário
não é calculado sem fonte de preço versionada.

#### PROTOCOL AMENDMENT 8 — H2 TREATMENT VERSION 2 (correção mínima do contrato semântico)

```text
DATA              2026-10-05
TIPO              nova versão do tratamento, dirigida a defeito objetivo;
                  registrada ANTES de qualquer chamada live v2 e antes da
                  seleção da CAL-B2
OBSERVADO ANTES   toda a evidência v1 (Hardening/B0, CAL-A, Sequential Dev,
                  Stress, CAL-B1 consumida) e o post-mortem da CAL-B1
                  (docs/evidence/cal_b_v1/postmortem/); nenhum retorno da CAL-B1
                  foi observado; Validation e Final Test intocados
STATUS v1         H2 V1 FAILED CAL-B1 — CONSUMED. Toda a evidência v1 é
                  preservada como está; as 10 âncoras CAL-B1 são DEVELOPMENT
                  EVIDENCE e nunca voltam a ser holdout
```

Código: `src/experiments/treatment.py` (`H2_TREATMENT_VERSION = 2`,
`SCIENTIFIC_TECHNICAL_PROMPT_VERSION = 2`, regra da CAL-B2),
`src/agents/feature_semantics.py` (contrato semântico, prompt v2, checker),
parâmetro `technical_prompt_version` do `LLMParticipant`.

**Por quê.** A v1 falhou o sanity check da CAL-B1 por degeneração (CB-D,
`total_hold_rate = 0.90`). O post-mortem achou um defeito objetivo, detectável
sem resultado financeiro: o prompt técnico entregava as 8 razões sem definição
nem convenção de sinal, e o modelo afirmava rompimento da banda superior com
`bb_upper_gap < 0` (64% dos votos da CAL-B1, 33–43% nas fases anteriores). A
correção v2 é dirigida pela contradição entre rationale e input, não por
performance.

**Changeset v1 → v2 (único).** O system prompt técnico científico ganha:
- glossário semântico das 8 features (fórmula e convenção de sinal), gerado
  de uma representação canônica única (`FEATURE_SEMANTICS`);
- regra STATE, NOT TRANSITION: o payload é só o estado em `t`, sem `t-1`;
  posições podem ser afirmadas, transições (cruzou, rompeu, reverteu, entrou)
  não.

Ficam idênticos: provider/modelo/API nativa, thinking low, temperature 1.0,
max_output_tokens 8192, sem seed, N = 5, limiar 0.6, require_all_votes,
decision_frequency 1, strict_inputs, portfolio_inversion_policy fail,
long_target_weight 1.0, volatility_window 21, risk_max_volatility 0.40,
risk_max_drawdown 0.25, risk_max_concentration 1.0, CostSpec, fonte de preço,
as 8 features e suas fórmulas (`LLM_FEATURE_SCHEMA_VERSION` continua 2: ele
versiona o conjunto/fórmulas das features, que não mudaram), o user prompt
técnico, o schema de resposta, a semântica de MANTER, o Risk prompt e o
Portfolio prompt. O prompt não ganha nenhuma instrução para operar mais,
evitar MANTER, favorecer direção ou assumir risco. A identidade científica
muda pelo parâmetro `technical_prompt_version = 2` (entra no `spec_hash`) e
pelo hash do system prompt (entra na identidade de cada chamada).

**Checker semântico** (`audit_rationale`, determinístico, só o texto visível
do Technical; nunca reescreve decisão). Afirmações de posição conferidas
contra o payload: preço acima/abaixo da banda superior (`bb_upper_gap > 0` /
`< 0`), abaixo/acima da banda inferior (`bb_lower_gap < 0` / `> 0`), dentro
das bandas (`bb_upper_gap <= 0` e `bb_lower_gap >= 0`), acima/abaixo da
SMA50/SMA200 (`sma*_gap > 0` / `< 0`), MACD acima/abaixo da linha de sinal
(`macd_ratio > / < macd_signal_ratio`) e sinal declarado de cada feature
("sma50_gap positivo"). Linguagem de transição (cruzou, cruzamento, cruzando,
crossover, rompeu, rompimento, ultrapassou, superou, perfurou, reverteu,
reversão, entrou, voltou, acabou de, virada) é
`UNSUPPORTED_TRANSITION_CLAIM`, exceto quando negada ou hipotética (não, sem,
possível, pode, aguardar, risco de, antes de…) ou em "reversão à média". As
regras exatas ficam congeladas no código do commit do contrato, testadas, antes
de qualquer chamada v2.

**CAL-B2 — novo holdout, comprometido antes de qualquer chamada live v2.**
Os mesmos 10 estratos de CAL-B (3, 6, …, 30), uma sessão nova por estrato.

```text
seed       CAL_B2_SELECTION_SEED = SHA256("HEDGE-FUND-LAB|CAL-B2|" +
           CAL_B1_COMMITMENT_HASH), hex
candidatos sessões do estrato (domínio do Amendment 2) menos:
           as âncoras CAL-B1, as sessões H_real (atuais e as do snapshot
           anterior), toda âncora de Hardening/B0/CAL-A, toda sessão de
           decisão de Stress, toda sessão da Sequential Development e toda
           sessão de decisão registrada em qualquer evidência de
           desenvolvimento (varredura de docs/evidence)
digest     SHA256(seed + "|" + stratum_id + "|" + ISO_DATE(d))
vencedor   menor digest (ordem lexicográfica)
persistido número de candidatos, hash do ranking completo, vencedor e o
           compromisso SHA-256 das 10 datas
```

Nenhum retorno, volatilidade, feature, resposta de LLM ou regime entra na
seleção. Depois do commit, CAL-B2 fica selada: o runner e o banco de chamadas
recusam suas datas, e nenhuma fase v2 decide sobre elas. CAL-B2 **não** é
executada nesta tarefa.

**Hardening dirigido ao defeito (v2).** Depois do compromisso da CAL-B2.
Estados: as 10 âncoras CAL-B1 (consumidas, development), histórico até
close(t), carteira zerada. Configuração: a final de desenvolvimento v1 com o
prompt v2. `R = 3` por âncora, N = 5: 150 chamadas técnicas; Risk/Portfolio
seguem o grafo; nenhum retorno, nenhum preço `t+1`.

```text
V2-S1  contradições semânticas objetivas (checker) = 0
V2-S2  afirmações de transição não suportadas (checker) = 0
V2-A   falhas finais = 0
V2-T   truncamentos (MAX_TOKENS / length) = 0
V2-D   total_hold_rate < 0.90 (mesmos códigos HOLD do Hardening)
```

Interpretação congelada: V2-S1 ou V2-S2 falha → `H2_V2_SEMANTIC_FIX FAILED`
(parar; nenhuma outra variável muda). S1/S2 passam e V2-D falha →
`H2_V2 SEMANTICS FIXED — DEGENERACY PERSISTS` (parar; evidência para uma
eventual v3 sobre MANTER, que não é alterado aqui). Tudo passa →
`H2_V2 MINIMAL DEFECT FIX PASSED`.

**Reexecução de development v2 (só se o hardening dirigido passar).** O
prompt é parte do tratamento, então todas as fases de development rodam de
novo, com os MESMOS conjuntos, grades, R, escores, desempates, gates e
fronteiras da v1, sem nova grade, threshold ou data, e com evidência em
diretórios `*_v2` (a v1 nunca é sobrescrita):

```text
Diagnostic Hardening  H = 8 H_syn + 4 H_real, R = 5, gates G-A/G-T/G-I/G-F;
                      thinking low fixo (a escada não sobe na v2: falha de G-I
                      ou G-F para tudo, porque thinking não pode mudar)
B0                    H, R = 1, só se o Hardening v2 passar
CAL-A                 20 âncoras, grade {21,63} x {0.40,0.50,0.60}, R = 3,
                      pareada, S1, desempate menor config_id. O gate de
                      identificabilidade não é refeito: é determinístico, não
                      depende do prompt (7 âncoras distinguíveis, REDUCED)
Sequential Dev        2024-03-01..2024-08-29 (liquidação 08-30), D01/D02/D03,
                      R = 3, S2 com Sharpe v1, mesma fronteira e desempate;
                      base = seleção da CAL-A v2
Stress                as mesmas 4 janelas comprometidas (sem reseleção), R = 3,
                      gates S-A/S-T/S-C/S-R; config = seleções v2
```

Resultados v1 não selecionam nada na v2; cada seleção v2 registra sua
`selection_basis` (EMPIRICAL ou PROTOCOL_TIE_FALLBACK). Ao fim, se tudo passar:
`H2_V2 DEVELOPMENT COMPLETE — READY FOR CAL-B2 PROTOCOL`, e parar.

**Governança para a monografia.** A v1 falhou o sanity check por degeneração;
o post-mortem achou um contrato semântico sub-especificado; nenhum retorno da
CAL-B1 foi observado; a correção v2 foi dirigida pela contradição entre
rationale e input e não escolhida por performance; Validation e Final Test
permaneceram intactos; a v2 é uma nova classe de comparabilidade.

#### PROTOCOL AMENDMENT 9 — CAL_B2_PROTOCOL_FREEZE_V1

```text
DATA              2026-10-06
TIPO              registro pré-execução; decidido pelos autores ANTES de
                  qualquer chamada live sobre uma âncora de CAL-B2
COMMIT            CAL_B2_FREEZE_COMMIT = o commit que introduz este amendment;
                  o commit seguinte traz só a autorização limitada e os guards
                  de versão que o implementam; o batch roda sobre ele
OBSERVADO ANTES   toda a evidência v1 e v2 de development (registro abaixo),
                  CAL-B1 consumida; NENHUMA resposta de modelo, feature ou
                  métrica de entrada de âncora CAL-B2. Regra: nenhum dry-run
                  toca as datas CAL-B2; o executor só pode ser ensaiado
                  offline sobre as âncoras CAL-B1 (development), com
                  transporte falso e fora do repositório
NÃO MUDA          configuração H2 v2, prompts, checker, modelo, thinking,
                  custos, retry, fonte de preço, threshold de degeneração
```

Repete as regras do Amendment 7 para o holdout da v2, com os gates
semânticos do Amendment 8. Onde nada é dito aqui, vale o Amendment 7 tal como
executado na CAL-B1 (mesmo código: `src/experiments/cal_b.py`,
`scripts/run_cal_b.py` com `--cal-b2`).

**Papel.** CAL-B2 = `ONE-SHOT OUT-OF-SAMPLE SANITY CHECK`. Não é teste de
performance e não tem autoridade de tuning. A H2 v1 terminou em
`CAL_B_FAIL — HOLDOUT CONSUMED`; as 10 âncoras CAL-B1 são development evidence
e nunca voltam a ser holdout. A v2 corrigiu só `TECHNICAL FEATURE SEMANTICS
UNDER-SPECIFIED` (Technical Prompt v2).

**Configuração final H2 v2 (congelada; `CAL_B2_FROZEN_PARAMS =
stress_v2_params()`, travada por teste).**

```text
tratamento   H2_TREATMENT_VERSION 2 · technical_prompt_version 2
             TECHNICAL_SYSTEM_PROMPT_V2_SHA256
             a3dec11f4c8911397c0f04ec5c0b7eb6265c420b3b6f7e3f494dd79ca43782e1
provedor     gemini · gemini-3.8-flash · API nativa
geração      thinking_level low · temperature 1.0 · max_output_tokens 8192 ·
             sem seed transmitida
SC           analyst_count 5 · consensus_threshold 0.6 · require_all_votes
execução     decision_frequency 1 · strict_inputs · portfolio_inversion_policy fail
posição      long_target_weight 1.0
risco        volatility_window 21 · risk_max_volatility 0.40 ·
             risk_max_drawdown 0.15 · risk_max_concentration 1.0
retry        6 × 2.0 (operacional)
dados        snapshot científico B3 corrigido (H_REAL_SNAPSHOT_IDENTITY_DIGEST),
             OHLCV oficial B3, fator Yahoo só pela política congelada, feature
             schema científico existente; CostSpec científico congelado (sem
             uso: não há execução)
spec hash    CAL_B2_SPEC_SHA256 = SHA256(canonical_json(ParticipantSpec(
             "llm_agent", CAL_B2_FROZEN_PARAMS).to_dict())) =
             89ac12071d8f68774a3f2af8192c04ff4254a62df90bfc7c5c8d6301767c2324
```

**Resolução de `risk_max_drawdown = 0.15` (não reabrir).** A instrução inicial
da v2 tinha tensão entre preservar 0.25 e reexecutar o Sequential
Development. O Amendment 8 resolveu isso ANTES da execução: devolveu a
autoridade de seleção ao Sequential Development v2, cuja regra S2 congelada
escolheu D02 = 0.15 (`EMPIRICAL_S2`). 0.15 é parte da configuração final v2.
Não é afirmação de superioridade robusta: é seleção de development com R = 3
segundo o protocolo.

**Proveniência dos parâmetros (bases distintas, nunca misturadas).**

```text
CAL_A_V2_SELECTION_BASIS          = PROTOCOL_TIE_FALLBACK
                                    volatility_window 21, risk_max_volatility 0.40
SEQUENTIAL_DEV_V2_SELECTION_BASIS = EMPIRICAL_S2
                                    risk_max_drawdown 0.15
```

**Compromisso.** Exatamente as 10 datas de Amendment 8 — 2018-08-16,
2019-04-05, 2019-10-07, 2020-07-01, 2021-01-21, 2021-09-22, 2022-04-07,
2022-11-01, 2023-06-26, 2023-12-18 —, compromisso integral
`518dd9ddc132244726fc40b2939684876c6f69bf6bad67ea1f91a78fc4e9b167`, conferido
antes da execução. Nenhuma data é trocada, nenhuma âncora nova é selecionada.

**One-shot.** `CAL_B2_REPETITIONS = 1`: uma realização live por âncora (5
amostras Technical). Nunca repetir para medir estabilidade nem rerodar por
HOLD, veto, rationale ruim ou distribuição de ações.

**Independência.** Cada âncora: R$100.000, 100% caixa, posição zero, pico =
capital, histórico causal até close(t), participante novo, zero memória entre
âncoras (posição, equity, rationale, trace, contexto, resposta do provedor).

**Execução selada.** As 10 em um único batch automático, na ordem
comprometida, sem abrir respostas entre âncoras (o progresso só mostra data e
"sealed"); retomada exige o mesmo commit. Ordem: executar as 10 → persistir
artefatos → selar (`sealed.json`, `batch.json`, `BATCH_SEAL.sha256`) →
commitar a evidência bruta → só então abrir o pacote de auditoria. Se o batch
produzir conteúdo científico utilizável, o holdout foi consumido.

**Autorização limitada.** Nenhum bypass global (`CAL_B_AUTHORIZED` continua
False). A única porta é `authorize_cal_b2(phase="CAL-B2", commitment, as 10
datas na ordem, repetitions=1, treatment_version=2,
technical_prompt_version=2, spec_sha256=CAL_B2_SPEC_SHA256)`, que só funciona
com `CAL_B2_STATUS = "SEALED"`; qualquer outra combinação falha fechada. O
cliente do provedor recusa qualquer sessão que não seja a âncora em execução.
Após a observação, `CAL_B2_STATUS = CONSUMED`, com PASS ou FAIL.

**Sem resultado financeiro.** Não carregar t+1, não executar ordem, não
calcular retorno, P&L, Sharpe, Sortino, MDD, hit rate nem benchmark. O objeto
é a decisão em close(t). Relatório: `FINANCIAL_OUTCOME = NOT COMPUTED`.

**Consumo.** Falha puramente infra antes de qualquer resposta utilizável
persistida: âncora não consumida (pode ser retomada). Depois de resposta
utilizável: consumida; crash posterior só se recupera por replay exato do
journal; nunca substituir resposta observada por nova inferência. Replay exato
impossível → `CAL_B2_INVALID — PARTIAL HOLDOUT CONSUMED`, e parar.

**Gates automáticos.**

```text
CB2-A     10/10 decisões completas; 0 falha final de provedor/infra
          (retries recuperados são só evidência operacional)
CB2-S     0 violação de schema, resposta inválida, quorum incompleto,
          truncamento, fallback silencioso, inversão de portfólio, input
          científico faltando; 0 mismatch de tratamento/versão (spec do batch
          = CAL_B2_FROZEN_PARAMS, technical_prompt_version 2, system prompt de
          cada chamada técnica = TECHNICAL_SYSTEM_PROMPT_V2)
CB2-C     0 feature posterior a t, 0 ticker/data/preço absoluto no prompt
          técnico, 0 informação futura/t+1, 0 acesso a Validation/Final
          (t <= 2024-02-28); payload técnico idêntico às features recalculadas
          independentemente só com barras até t
CB2-R     COMPRA com recent_volatility > 0.40 ou current_drawdown > 0.15 ->
          veto duro antes do LLM de risco; regra dura nunca sem violação; veto
          nunca sobrescrito; VENDA/MANTER pelo contrato congelado. Drawdown
          estruturalmente 0 na âncora isolada em caixa (registrado)
CB2-SEM   contradições semânticas objetivas = 0 (Bollinger, SMA50, SMA200,
          MACD vs signal, sinais declarados) em cada rationale técnico visível
          contra o payload que o próprio modelo recebeu
CB2-TRANS afirmações de transição não suportadas = 0 (cruzou, rompeu hoje,
          acaba de romper, reverteu, crossover, entrou na banda…)
CB2-D     total_hold_rate < 0.90, mesma definição do Hardening/CAL-B1
          (HOLD_RATE_CAUSES; BUY_AT_TARGET_NOOP fora). 9 ou 10 HOLD = FAIL
```

CB2-SEM e CB2-TRANS usam exatamente o checker validado em development v2
(`audit_rationale`/`contradictions`/`transitions` e o wrapper
`semantic_audit`), congelado por blob git ANTES do batch e conferido antes de
aplicado:

```text
CAL_B2_CHECKER_BLOBS
  src/agents/feature_semantics.py   7a086701afda203a415cf1f9b67912d4788b3e56
  scripts/run_h2_v2_defect.py       2ec09c494732148680b3543ed4ed7ceae58018c2
```

Nenhuma regex ou regra muda depois de aberto o batch. O checker cobre o
Technical (onde as relações quantitativas são enviadas); Risk/Portfolio ficam
na revisão humana.

**Degeneração, literal.** A v2 passou o hardening dirigido com
`total_hold_rate = 0.867`, perto do limite. Isso não autoriza relaxar CB2-D,
usar 0.95, aceitar 9/10, reclassificar VENDA sem posição ou retirar âncora.
Reportados à parte: TECH_EXPLICIT_HOLD, TECH_NO_MAJORITY, RISK_VETO,
PORTFOLIO_HOLD, ACTION_BUY, ACTION_SELL (e BUY_AT_TARGET_NOOP, fora de
qualquer veto).

**Revisão humana** (só depois da evidência bruta selada e commitada). Fichas
`review/AUTHOR_1.json` e `review/AUTHOR_2.json`, preenchidas
independentemente pelos dois autores: `material_hallucination` e
`rationale_action_coherence` = PASS/FAIL por âncora. Material unsupported claim
= fato específico não fornecido ao estágio e usado materialmente para
justificar a decisão; Technical sem ticker, data, preço absoluto, notícia,
fundamentos ou macro; Risk/Portfolio só com seus payloads explícitos.
Coerência: Technical não defende direção contrária ao sinal; Risk coerente com
métricas e regras duras; Portfolio respeita direção e veredito de risco. O
checker automático não substitui esta revisão. Discordância →
`CAL_B2_REVIEW_DISAGREEMENT`, sem rerodar. Fichas incompletas →
`CAL_B2_AWAITING_HUMAN_REVIEW` (intermediário, não final).

**Regra de status.** PASS só se CB2-A, CB2-S, CB2-C, CB2-R, CB2-SEM,
CB2-TRANS e CB2-D passarem, e as duas revisões concordarem em zero alucinação
material e zero contradição rationale/ação.

```text
gate automático falhou        -> CAL_B2_FAIL — HOLDOUT CONSUMED
revisões incompletas          -> CAL_B2_AWAITING_HUMAN_REVIEW
revisões divergentes          -> CAL_B2_REVIEW_DISAGREEMENT
concordam, algum FAIL         -> CAL_B2_FAIL — HOLDOUT CONSUMED
concordam, tudo PASS          -> CAL_B2_PASS — SANITY CHECK ONLY
replay exato impossível       -> CAL_B2_INVALID — PARTIAL HOLDOUT CONSUMED
```

`CAL_B2_PASS` não é evidência de performance OOS. Só com ele:
`SYSTEM_CALIBRATION_COMPLETE = True` e `READY FOR SYSTEM FREEZE DESIGN`;
Validation não é executada automaticamente. Com FAIL: não editar prompt nem
checker, não relaxar gate, não alterar parâmetro, não rerodar, não substituir
âncora. Parar.

**Pacote de auditoria por âncora.** Data, payload de features, as 5 saídas
técnicas, distribuição de votos, consenso, achados do checker semântico e de
transição, entrada/saída de Risk e Portfolio quando chamados, causa final e
reason codes. Nenhuma informação financeira futura.

**Evidência operacional.** Chamadas lógicas, tentativas HTTP, retries, falhas
transitórias, latência p50/p90, tokens de entrada, saída e thinking. Sem custo
monetário (não há fonte de preço versionada).

**Ordem dos commits.** (1) este freeze; (2) autorização/guards de versão; (3)
evidência bruta selada; (4) gates automáticos; (5) revisão humana; (6) status
final. Evidência bruta nunca muda depois de selada.

#### PROTOCOL AMENDMENT 10 — H2 TREATMENT VERSION 3 (contrato do Risk sem regra numérica inventada)

```text
DATA              2026-10-06
TIPO              nova versão do tratamento, dirigida a defeito objetivo;
                  registrada ANTES de qualquer chamada live v3 e antes da
                  seleção da CAL-B3
OBSERVADO ANTES   toda a evidência v1 e v2 de development, CAL-B1 consumida e
                  a CAL-B2 consumida (lote selado, gates automáticos e pacote
                  de auditoria); nenhum retorno t+1 da CAL-B2 foi calculado;
                  Validation e Final Test intocados
STATUS v2         CAL-B2 executada, os sete gates automáticos PASS, fichas
                  humanas em branco: o status histórico continua
                  CAL_B2_AWAITING_HUMAN_REVIEW (não é reescrito como PASS nem
                  FAIL). A segunda revisão humana NÃO é aguardada nem pedida
                  nesta tarefa; nenhuma ficha é preenchida, completada ou
                  substituída
```

Código: `src/experiments/treatment.py` (`H2_TREATMENT_VERSION = 3`,
`SCIENTIFIC_RISK_PROMPT_VERSION = 2`, governança da v2, regra da CAL-B3),
`src/agents/risk_contract.py` (Risk prompt v2, semântica da confidence,
checker), parâmetro `risk_prompt_version` do `LLMParticipant`.

**Governança da v2.** O conteúdo observado da CAL-B2 passa a ser usado para
corrigir o sistema. Por isso a v2 perde elegibilidade para System Freeze
independentemente de qualquer revisão humana futura:

```text
CAL_B2_STATUS (histórico)              CAL_B2_AWAITING_HUMAN_REVIEW (preservado)
H2_V2_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE   True
razão                                  CAL_B2 CONSUMED AND USED AS DEVELOPMENT EVIDENCE
```

As 10 âncoras CAL-B2 são, daqui em diante, DEVELOPMENT EVIDENCE e nunca voltam
a ser holdout.

**Por quê (defeito objetivo, não performance).** Na âncora CAL-B2 2023-06-26 o
Technical forneceu `confidence` agregada 0.462 (3/5 COMPRA) e o Risk vetou com
"O sinal técnico apresenta uma confiança baixa de 0.462 (abaixo do limiar de
50%)". Não existe limiar de confidence no protocolo nem configurado no Risk; o
threshold foi criado pelo LLM e usado materialmente para justificar `VETADO`:
`UNSUPPORTED NUMERIC DECISION RULE`. O padrão não é isolado: o mesmo checker
(abaixo), aplicado às 158 respostas únicas do Risk LLM na evidência de
development v1/v2 (+ CAL-B2), marca 22 dos 38 vetos — 15 com limiar de
confidence inventado, 5 com limite de métrica inventado, 2 decididos só pela
confidence — e 0 das 120 aprovações. A correção v3 não tem como objetivo aumentar performance, número
de trades, fazer a CAL-B passar nem remover HOLDs: só impedir que o Risk
invente thresholds ou regras quantitativas.

**Changeset v2 → v3 (único).** O system prompt científico do Risk é trocado
pelo Risk Prompt v2 (`risk_prompt_version = 2`, entra no `spec_hash`; o hash
do prompt entra na identidade de cada chamada de risco). Ficam idênticos:
Technical Prompt v2 (`technical_prompt_version = 2`, sha256 `a3dec11f…`,
byte-idêntico), FEATURE_SEMANTICS, checker semântico, STATE NOT TRANSITION, as
8 features e fórmulas (`LLM_FEATURE_SCHEMA_VERSION` 2), N = 5, limiar 0.6,
require_all_votes; gemini · gemini-3.8-flash · API nativa · thinking low ·
temperature 1.0 · max_output_tokens 8192 · sem seed transmitida;
decision_frequency 1 · strict_inputs · portfolio_inversion_policy fail;
long_target_weight 1.0; CostSpec, fonte científica B3, política de ajuste
Yahoo, calendário, snapshot, quantity mode; payload, schema e regras duras do
Risk; prompt e comportamento do Portfolio. Configuração de risco de entrada
da v3 = a selecionada na v2: volatility_window 21 · risk_max_volatility 0.40 ·
risk_max_drawdown 0.15 · risk_max_concentration 1.0. CAL-A v3 e Sequential
Development v3 mantêm a autoridade de seleção que já tinham, sem grade nova.

**Risk Prompt v2 (texto exato, `RISK_SYSTEM_PROMPT_V2`).**

```text
Você é o gestor de risco do Hedge-fund-lab.

Avalie somente o sinal técnico e as métricas de risco explicitamente fornecidas no payload. Não use notícias, conhecimento externo, identidade do ativo, datas ou informação futura.

As regras duras numéricas do sistema são aplicadas deterministicamente antes desta etapa. Se esta chamada foi alcançada, essas regras anteriores não vetaram a operação.

Não invente, suponha nem aplique novos thresholds numéricos que não estejam explicitamente fornecidos no seu payload ou no seu contrato.

O campo confidence do sinal técnico é metadado qualitativo. Não existe um limiar numérico de confidence configurado para aprovação ou veto. Nunca diga ou implique que uma confidence está acima ou abaixo de um threshold inexistente, e nunca aprove ou vete uma operação somente porque a confidence é baixa ou alta.

Você pode considerar confidence qualitativamente em conjunto com as métricas efetivamente fornecidas, mas sem criar cortes numéricos ou regras ocultas.

Você ainda pode retornar VETADO quando a combinação do sinal e das métricas fornecidas indicar risco inadequado. Nesse caso, a justificativa deve se apoiar somente nos valores e relações presentes no payload, sem inventar regras quantitativas externas.

Preserve capital, não invente dados e retorne APROVADO ou VETADO com análise objetiva.
```

O Risk Prompt v1 (`risk_manager.SYSTEM_PROMPT`, sha256 `57ee8505…`) continua
reproduzível com `risk_prompt_version = 1` (default).

**`TECHNICAL_CONFIDENCE_SEMANTICS_V1`.** `confidence` ∈ [0, 1]; qualitativa;
NÃO é probabilidade calibrada; NÃO representa probabilidade de retorno
positivo; NÃO tem threshold de decisão; NÃO controla position sizing (o
Portfolio científico é qualitativo e o alvo é `long_target_weight`); NÃO cria
hard rule; NÃO pode ser base exclusiva de veto ou aprovação do Risk. Nada muda
em como o Technical gera ou o consenso agrega `confidence`.

**Checker do Risk** (`audit_risk_rationale`, determinístico, só o rationale
VISÍVEL do Risk contra o payload que o Risk recebeu; nunca o raciocínio
oculto; nunca reescreve decisão).

```text
UNSUPPORTED_CONFIDENCE_THRESHOLD  (V3-R1) confidence/convicção associada a
          limiar, limite, mínimo, threshold, "nível/patamar/margem mínima",
          "convicção mínima", "não atinge o mínimo", ou comparada (abaixo,
          acima, inferior, menor, <, >…) a número que não está no payload.
          Não existe limiar de confidence, nem acima nem abaixo
UNSUPPORTED_NUMERIC_RULE          (V3-R2) métrica ou consenso comparado a um
          número Y fora do payload ("0.37 excede o limite de 0.30"), ou
          afirmado acima de/excedendo um limite ("excede os limites
          prudenciais"): nenhum limite é fornecido ao Risk e as regras duras
          já passaram. Citar o valor do payload ("volatilidade de 36.46%") e
          qualificá-lo ("elevada", "nível crítico") é permitido
CONFIDENCE_ONLY_DECISION          (V3-R3) veredito sem nenhuma métrica de risco
          (volatilidade, drawdown, concentração) fora de oração concessiva
          (apesar, embora, mesmo com…): decidido só pelo sinal técnico
VERDICT_TEXT_CONTRADICTION        (V3-R3) o texto declara o veredito oposto
```

Português e inglês; números do payload conferidos na escala citada até o
arredondamento citado (36.46% ≡ 0.364617); frações de votos (3/5) não são
comparações. Calibração SÓ com development evidence já consumida (CAL-B1 —
que não tem chamada de Risk LLM —, CAL-B2, Hardening/B0, CAL-A, Sequential,
Stress, v1 e v2); a CAL-B3 nunca é usada. As regras exatas ficam congeladas no
código e nos testes do commit do contrato, ANTES da primeira chamada live v3;
os blobs git são registrados no manifest do hardening dirigido e não mudam
até o fim do development v3.

**CAL-B3 — novo holdout, comprometido antes de qualquer chamada live v3.**
Os mesmos 10 estratos de CAL-B (3, 6, …, 30), uma sessão nova por estrato.

```text
seed       CAL_B3_SELECTION_SEED = SHA256("HEDGE-FUND-LAB|CAL-B3|" +
           CAL_B2_COMMITMENT_HASH), hex
candidatos sessões do estrato (domínio do Amendment 2) menos: CAL-B1,
           CAL-B2, H_real (atuais e as do snapshot anterior), âncoras CAL-A,
           sessões da Sequential Development, sessões de decisão do Stress e
           toda sessão de decisão em qualquer evidência de development v1/v2
           (varredura de docs/evidence)
digest     SHA256(seed + "|" + stratum_id + "|" + ISO_DATE(d))
vencedor   menor digest (ordem lexicográfica)
persistido número de candidatos, hash do ranking, vencedor e
           CAL_B3_COMMITMENT_HASH (SHA-256 das 10 datas)
```

Outcome-blind: nenhum retorno, volatilidade, feature, resposta de LLM ou
regime. Depois do commit, CAL-B3 fica SELADA e inacessível ao development v3:
o runner e o banco de chamadas recusam suas datas; não se calculam features
nem retornos para revisá-las; nada é executado. CAL-B3 **não** é executada
nesta tarefa.

**FROZEN_COMPONENT_REPLAY = TECHNICAL_V2.** O Technical da v3 é byte-idêntico
ao da v2. Em vez de gerar ruído estocástico novo, toda resposta Technical v2
já observada é reaproveitada quando a requisição v3 for IDÊNTICA à v2 — mesma
`LLMCallRequest.identity()`: sessão de decisão, analista, system prompt, user
prompt (payload), provedor/modelo, opções de geração e schema — na evidência
v2 da MESMA fase e da MESMA repetição (CAL-B2: a única realização selada,
reaproveitada nas R = 3 repetições). Requisição sem par idêntico vai ao
provedor (contada e reportada). Portfolio: replay só por identidade exata com
a evidência v2 (ex.: VENDA auto-aprovada com as mesmas métricas); qualquer
request novo (ex.: depois de um parecer de Risk v3) é live. Risk v3: sempre
live, salvo o banco intra-repetição já usado na v1/v2 (mesma identidade, mesma
repetição, entre configurações pareadas). Cada trajetória v3 tem carteira
nova, Risk v3, spec v3, artefatos e equity v3; nenhuma performance v2 é
misturada; só respostas do componente congelado (Technical, e Portfolio por
identidade exata) são reaproveitadas. A prova de igualdade é registrada por
chamada (identity digest, `provider_response_id`, hash do raw e da resposta
validada contra o registro v2).

**Hardening dirigido ao defeito (v3).** Depois do compromisso da CAL-B3.
Estados: as 10 âncoras CAL-B2 consumidas, histórico até close(t), carteira
zerada; configuração = final v2 (21 / 0.40 / 0.15 / 1.0) + Risk prompt v2.
`R = 3`; Technical = replay das respostas CAL-B2 seladas (nenhuma chamada
Technical nova); Risk v2 live quando a trajetória chega ao Risk; Portfolio
replay/live pela regra acima. Nenhum retorno, nenhum preço `t+1`. A âncora
2023-06-26 faz parte obrigatoriamente, com o mesmo Technical output e o mesmo
payload lógico do Risk; não se exige que a decisão mude (pode continuar
`VETADO`), só que a justificativa seja válida sob o novo contrato.

```text
V3-R1  UNSUPPORTED_CONFIDENCE_THRESHOLD = 0
V3-R2  UNSUPPORTED_NUMERIC_RULE = 0
V3-R3  contradições materiais rationale/veredito (CONFIDENCE_ONLY_DECISION +
       VERDICT_TEXT_CONTRADICTION) = 0
V3-S   0 falha de schema/resposta inválida, 0 truncamento, 0 falha final de
       provedor, 0 inversão/fallback de Portfolio
V3-D   total_hold_rate < 0.90 (mesmos códigos HOLD; threshold não muda)
```

Interpretação congelada: V3-S falha → `H2_V3_DEFECT_HARDENING TECHNICAL
FAILURE`; V3-R1, V3-R2 ou V3-R3 falha → `H2_V3_RISK_CONTRACT_FIX FAILED`
(parar; nenhuma outra variável muda); R passa e V3-D falha → `H2_V3 RISK
CONTRACT FIXED — DEGENERACY PERSISTS` (parar); tudo passa → `H2_V3 MINIMAL
DEFECT FIX PASSED`. Mudança de decisão não é critério; não se otimiza por
APROVADO.

**Reexecução de development v3 (só se o hardening dirigido passar).** Mesmos
conjuntos, grades, R, escores, desempates, gates e fronteiras da v2, evidência
em diretórios `*_v3` (v1/v2 nunca sobrescritas), Technical por replay v2:

```text
Diagnostic Hardening  H = 8 H_syn + 4 H_real, R = 5, mesma spec ex ante da v2
                      (freeze v1, LOW, prompt técnico v2) + Risk prompt v2;
                      gates G-A/G-T/G-I/G-F; replay da repetição v2 de mesmo índice
B0                    H, R = 1, só se o Hardening v3 passar; replay do B0 v2
CAL-A                 mesmas 20 âncoras, grade {21,63} x {0.40,0.50,0.60}, R = 3,
                      S1, pareamento e desempate; pode reselecionar
Sequential Dev        2024-03-01..2024-08-29 (liquidação 08-30), D01 0.25 /
                      D02 0.15 / D03 0.35, R = 3,
                      H2_SCIENTIFIC_SHARPE_DEFINITION_V1, S2, mesmo desempate e
                      fronteiras; base = seleção da CAL-A v3; pode reselecionar
Stress                as mesmas 4 janelas comprometidas (sem reseleção), R = 3,
                      gates S-A/S-T/S-C/S-R; config = seleções v3
```

Em cada fase o checker do Risk é aplicado às respostas Risk v3 e reportado
(descritivo; achados residuais vão para o resumo de development e para o
desenho da CAL-B3). Ao fim, se tudo passar: `H2_V3 DEVELOPMENT COMPLETE —
READY FOR CAL-B3 PROTOCOL`, e parar. CAL-B3 não é executada automaticamente.

**Governança para a monografia.** A CAL-B2 passou os gates automáticos mas
revelou, no rationale do Risk, uma regra numérica inexistente usada para
vetar; a v2 ficou inelegível para System Freeze por ter seu holdout usado como
development; a correção v3 é dirigida pelo contrato e não por performance;
Validation e Final Test permaneceram intactos; a v3 é uma nova classe de
comparabilidade.

#### PROTOCOL AMENDMENT 11 — CAL_B3_PROTOCOL_FREEZE_V1

```text
DATA              2026-10-06
TIPO              registro pré-execução; decidido pelos autores ANTES de
                  qualquer chamada live sobre uma âncora de CAL-B3
COMMIT            CAL_B3_FREEZE_COMMIT = o commit que introduz este amendment;
                  o anterior traz o checker v2 do Risk e o corpus de regressão
                  (31d8714); o seguinte traz só a autorização limitada, os
                  guards de versão e os gates que o implementam; o batch roda
                  sobre ele
OBSERVADO ANTES   toda a evidência v1/v2/v3 de development, CAL-B1 e CAL-B2
                  consumidas; NENHUMA resposta de modelo, feature ou métrica de
                  entrada de âncora CAL-B3. Regra: nenhum dry-run toca as datas
                  CAL-B3; o executor só é ensaiado offline sobre âncoras já
                  consumidas (development), com transporte falso e fora do
                  repositório
NÃO MUDA          tratamento H2 v3, prompts, modelo, thinking, custos, retry,
                  fonte de preço, threshold de degeneração
```

Repete as regras dos Amendments 7 e 9 para o holdout da v3, com os gates do
Risk do Amendment 10 e duas decisões de governança novas (veto discricionário
sem mínimo; revisão humana de um autor). Onde nada é dito aqui, vale o
Amendment 9 tal como executado na CAL-B2 (mesmo código:
`src/experiments/cal_b.py`, `scripts/run_cal_b.py` com `--cal-b3`).

**Papel.** CAL-B3 = `ONE-SHOT OUT-OF-SAMPLE SANITY CHECK` da H2 v3. Não é teste
de performance e não tem autoridade de tuning. CAL-B1 e CAL-B2 são development
evidence e nunca voltam a ser holdout.

**Configuração final H2 v3 (congelada; `CAL_B3_FROZEN_PARAMS =
stress_v3_params()`, travada por teste).**

```text
tratamento   H2_TREATMENT_VERSION 3 · technical_prompt_version 2 ·
             risk_prompt_version 2
             TECHNICAL_SYSTEM_PROMPT_V2_SHA256
             a3dec11f4c8911397c0f04ec5c0b7eb6265c420b3b6f7e3f494dd79ca43782e1
             RISK_SYSTEM_PROMPT_V2_SHA256
             990424e307e2c593afc40ebafef2c12387029ecf46a285f18a595c447e1e2151
             Portfolio QUALITATIVE_SYSTEM_PROMPT (inalterado)
             497b56e89f1f2fc193f999e6bc23c88cccb7a2c6da96de5c11f09417482ae68a
provedor     gemini · gemini-3.8-flash · API nativa
geração      thinking_level low · temperature 1.0 · max_output_tokens 8192 ·
             sem seed transmitida
SC           analyst_count 5 · consensus_threshold 0.6 · require_all_votes
execução     decision_frequency 1 · strict_inputs · portfolio_inversion_policy fail
posição      long_target_weight 1.0
risco v3     volatility_window 21 · risk_max_volatility 0.50 ·
             risk_max_drawdown 0.25 · risk_max_concentration 1.0
retry        6 × 2.0 (operacional)
dados        snapshot científico B3 corrigido (H_REAL_SNAPSHOT_IDENTITY_DIGEST),
             mesmo information set até close(t) da CAL-B2
spec hash    CAL_B3_SPEC_SHA256 = SHA256(canonical_json(ParticipantSpec(
             "llm_agent", CAL_B3_FROZEN_PARAMS).to_dict())) =
             1d63ad4cc93f9ef49368ba6772a22403354b36f3cc7d9d57d3b0627b85b9becc
             (o mesmo valor integral já gravado como participant_spec_sha256
             PETR4.SA nos manifests do Hardening/B0 v3)
```

**Proveniência dos parâmetros (bases distintas, nunca misturadas; nenhuma
superioridade robusta afirmada).**

```text
CAL_A_V3_SELECTION_BASIS          = EMPIRICAL_S1
                                    volatility_window 21, risk_max_volatility 0.50
                                    configs 2, 3 e 6 empataram no maior S1;
                                    config 2 venceu pelo desempate predeclarado
                                    (menor config_id); uma âncora discrimina, R = 3
SEQUENTIAL_DEV_V3_SELECTION_BASIS = EMPIRICAL_S2
                                    risk_max_drawdown 0.25
                                    D01 e D03 empataram no maior S2; D01 venceu
                                    pelo menor config_id; R = 3
```

**Compromisso.** Exatamente as 10 datas do Amendment 10 — 2018-08-03,
2019-03-19, 2019-10-18, 2020-05-13, 2021-01-06, 2021-08-17, 2022-03-11,
2022-11-29, 2023-05-12, 2024-01-11 —, compromisso integral
`CAL_B3_COMMITMENT_SHA256 =
a5cadecd361de5059370bf4bfa97b1417b82eb8951950cf92b0aebc7edecdbaf`, conferido
antes da autorização. Nenhuma data é trocada.

**One-shot.** `CAL_B3_REPETITIONS = 1`: uma realização live por âncora (N = 5
Technical), sem banco de chamadas entre âncoras, zero memória entre âncoras
(R$100.000, 100% caixa, posição zero, pico = capital, participante novo). Nunca
rerodar por resultado comportamental (HOLD, veto, aprovação, rationale,
distribuição de ações).

**Execução selada.** As 10 em um único batch automático, na ordem
comprometida, sem inspeção humana intermediária (o progresso só mostra data e
"sealed"); retomada exige o mesmo commit. Ordem: executar → persistir → selar
(`sealed.json`, `batch.json`, `BATCH_SEAL.sha256`) → hash → commitar a
evidência bruta → só então abrir rationales e pacote de auditoria.

**Autorização limitada.** Nenhum bypass global (`CAL_B_AUTHORIZED` continua
False). A única porta é `authorize_cal_b3(phase="CAL-B3", commitment integral,
as 10 datas na ordem, repetitions=1, treatment_version=3,
technical_prompt_version=2, risk_prompt_version=2,
spec_sha256=CAL_B3_SPEC_SHA256)`, que só funciona com `CAL_B3_STATUS =
"SEALED"`; qualquer outra combinação falha fechada. O cliente do provedor
recusa qualquer sessão que não seja a âncora em execução. Após o consumo,
`CAL_B3_STATUS = CONSUMED` e a porta não reabre, com PASS ou FAIL.

**Consumo do holdout.** Sem resposta/trace/rationale científico utilizável:
âncora não consumida, pode ser retomada pela política de infraestrutura
(retry/resume). Com conteúdo científico utilizável: âncora CONSUMED. Crash
depois de resposta persistida: só replay exato do journal. Replay impossível →
`CAL_B3_INVALID — PARTIAL HOLDOUT CONSUMED`, sem nova inferência substituta.

**Sem resultado financeiro.** Não carregar t+1, não executar, não calcular
retorno, P&L, Sharpe, Sortino, MDD, accuracy nem comparação com benchmark. A
CAL-B3 termina na decisão em close(t). Relatório: `FINANCIAL_OUTCOME = NOT
COMPUTED`.

**Risk rationale checker v2 (instrumento de auditoria, congelado aqui).** O
checker do Amendment 10 (v1, blob `7636ad26`) tinha um falso positivo
conhecido em `VERDICT_TEXT_CONTRADICTION`: aceitava negação só até 30
caracteres antes da palavra e marcava "Não há fatores adversos nas métricas
fornecidas que justifiquem veto" (APROVADO) como contradição (v3 Hardening
2002-04-19 e v3 Stress 2018-09-10). Corrigido ANTES da CAL-B3, sem nenhuma
data CAL-B3:

```text
RISK_RATIONALE_CHECKER_VERSION = 2
polaridade por construção, dentro da sentença (não por janela de tokens):
  negação direta          "sem veto", "não vetaram", "not vetoed"
  verbo licenciador negado "não justifica veto", "does not justify a veto"
  existencial + relativo  "não há X ... que justifiquem veto"
  substantivo licenciador "sem razão para vetar", "não há motivo para veto",
                          "no reason to veto"
  sujeito quantificado    "Nada no payload recomenda veto", "Nothing warrants a veto"
  -> apoio ao veredito, não contradição
escopo   fecha em predicado afirmado (há/é/foi...), adversativa (mas, porém,
         but...) ou fim de sentença; "o que"/", which" retomam a oração inteira
         e não herdam a negação
continua contradição
  "há fatores que justificam veto" com APROVADO; "operação aprovada" com
  VETADO; e (direção nova) negar o fundamento do próprio veredito:
  "não há condições para aprovação" com APROVADO
não é veredito deste estágio
  menção à camada determinística ("regras duras de veto", "aprovada pelas
  regras duras"); negação do próprio veredito dentro de concessiva
  ("Embora não haja motivo para veto, ... vetada")
inalterados  V3-R1 UNSUPPORTED_CONFIDENCE_THRESHOLD, V3-R2
             UNSUPPORTED_NUMERIC_RULE, CONFIDENCE_ONLY_DECISION
teto         dupla negação e prefixos como "Com drawdown nulo e sem
             concentração há fatores..." não são resolvidos (registrado)
```

Calibração só com evidência de development já consumida (v1, v2, CAL-B1 — sem
chamada de Risk —, CAL-B2, Hardening/B0, CAL-A, Sequential, Stress e
development v3): 210 respostas únicas do Risk LLM + 37 casos sintéticos PT/EN
rotulados (`docs/evidence/h2_v3/risk_checker_v2/`). Aceitação exigida e
obtida antes de qualquer chamada CAL-B3: 0 dos 2 falsos positivos conhecidos;
0 regressão nos 21 casos inválidos congelados; V3-R1, V3-R2 e
CONFIDENCE_ONLY_DECISION marcam exatamente as mesmas respostas; 0 divergência
no corpus. Nas 210 respostas reais a única mudança v1 → v2 são os 2 falsos
positivos. Reaplicação offline ao corpus v3 (nada rerodado live): V3-R3 2/70 →
0/70; R1 e R2 continuam 0. Os rótulos R1/R2/CONFIDENCE_ONLY dos casos reais
são os achados congelados do v1 (trava de regressão, não afirmação de recall);
os sintéticos foram escritos junto com o v2 e não medem generalização.

```text
CHECKER_VERSION           2
risk_contract.py (blob)   1ff4343a8e5d24ec4f8c71349a64771a21aa3636
corpus golden (sha256)    19f59ae99a8437d023409b9bedd4ae6b83bc4c41c328871124a1d4f0d8e672bb
relatório                 docs/evidence/h2_v3/risk_checker_v2/calibration_report.json
```

A mudança é de instrumento: não muda tratamento, Risk prompt, modelo, spec nem
nenhuma resposta do sistema. Depois deste commit o checker fica congelado;
nenhuma edição depois de aberta a CAL-B3.

**Checkers congelados por blob git** (conferidos antes de aplicados; o audit
recusa qualquer diferença de `src/` ou `scripts/` em relação ao commit do
batch):

```text
CAL_B3_CHECKER_BLOBS
  src/agents/feature_semantics.py   7a086701afda203a415cf1f9b67912d4788b3e56  (Technical, v2)
  scripts/run_h2_v2_defect.py       2ec09c494732148680b3543ed4ed7ceae58018c2  (wrapper v2)
  src/agents/risk_contract.py       1ff4343a8e5d24ec4f8c71349a64771a21aa3636  (Risk, checker v2)
```

**Gates automáticos.**

```text
CB3-A      10/10 decisões completas; 0 falha final de provedor/infra
           (retries recuperados são só diagnóstico)
CB3-S      0 violação de schema, resposta inválida, quorum incompleto,
           truncamento, fallback silencioso, inversão de portfólio, input
           científico faltando; 0 mismatch de versão: spec do batch =
           CAL_B3_FROZEN_PARAMS, system prompt de cada chamada Technical =
           TECHNICAL_SYSTEM_PROMPT_V2, de cada Risk = RISK_SYSTEM_PROMPT_V2,
           de cada Portfolio = QUALITATIVE_SYSTEM_PROMPT
CB3-C      0 dado posterior a t; 0 ticker/data/preço absoluto no Technical;
           0 future leakage; 0 acesso a Validation/Final (t <= 2024-02-28);
           payload Technical e métricas do Risk idênticos aos recalculados
           independentemente só com barras até t
CB3-HR     0 violação das regras duras congeladas: COMPRA com
           recent_volatility > 0.50 (ou drawdown > 0.25, concentração > 1.0)
           vetada deterministicamente antes do Risk LLM; regra dura nunca sem
           violação; veto duro nunca sobrescrito nem seguido de LLM;
           VENDA/MANTER pelo contrato congelado. Drawdown e concentração são
           estruturalmente 0 na âncora isolada em caixa (registrado).
           Obrigatório independentemente da taxa de veto do Risk LLM
CB3-TSEM   0 contradição semântica objetiva (checker Technical v2 congelado)
CB3-TTRANS 0 afirmação de transição não suportada (STATE NOT TRANSITION)
CB3-R1     0 UNSUPPORTED_CONFIDENCE_THRESHOLD (checker do Risk v2 congelado)
CB3-R2     0 UNSUPPORTED_NUMERIC_RULE
CB3-R3     0 CONFIDENCE_ONLY_DECISION e 0 VERDICT_TEXT_CONTRADICTION genuína
           (checker negation-aware congelado; nunca alterado depois de
           observado qualquer rationale CAL-B3)
CB3-D      total_hold_rate < 0.90, exatamente a definição do Hardening/CAL-B1/
           CAL-B2 (HOLD_RATE_CAUSES; BUY_AT_TARGET_NOOP fora). 9/10 ou 10/10
           HOLD = FAIL. Sem gate de mínimo de BUY, de SELL ou de veto do Risk
```

**Risk com zero vetos LLM — decisão de governança.**

```text
RISK_LLM_VETO_RATE_HAS_NO_MINIMUM_GATE = True
```

O Risk LLM é uma camada discricionária posterior às regras duras
determinísticas. Não existe requisito científico de que ele vete uma
quantidade mínima de operações; ele pode legitimamente aprovar tudo o que
passou pelas regras duras. Zero vetos do Risk LLM NÃO é degeneração, falha,
ausência de funcionamento nem motivo para alterar prompt. Zero veto
discricionário não relaxa nenhuma regra dura (CB3-HR continua obrigatório).

**Atividade do Risk — só descritiva (sem PASS/FAIL).** Reportados: chamadas do
Risk LLM, APROVADO, VETADO, taxa de aprovação e de veto, e

```text
RISK_LLM_DISCRETIONARY_VETO = OBSERVED       (alguma chamada VETADO)
                            = NOT_OBSERVED   (chamadas > 0, VETADO = 0)
                            = NOT_EXERCISED  (nenhuma chamada do Risk LLM)
```

Mesmo `Risk LLM: 100% APPROVED` não causa FAIL quando o checker passa, o
rationale é suportado e as regras duras foram respeitadas.

**Revisão humana — não depende do segundo autor.** A CAL-B1/B2 exigiam os dois
autores. Para a CAL-B3, congelado antes da abertura do holdout:

```text
PRIMARY_HUMAN_REVIEWERS_REQUIRED = 1
SECOND_INDEPENDENT_REVIEW        = NOT REQUIRED FOR PROGRESSION
SECOND_INDEPENDENT_REVIEW        = RECOMMENDED AS LATER AUDIT
```

Depois da evidência bruta selada e dos gates automáticos calculados, uma ficha
obrigatória `review/PRIMARY_AUTHOR.json`, preenchida pelo autor principal
disponível, lendo só o pacote de auditoria (sem nenhum resultado t+1). Por
âncora: `material_unsupported_claim` = PASS/FAIL,
`rationale_action_coherence` = PASS/FAIL, `optional_note`. Ninguém preenche
ficha em nome do segundo autor nem inventa concordância.
`review/SECOND_AUTHOR_OPTIONAL.json` nasce `NOT_REVIEWED` e sua ausência não
bloqueia. O processo não é apresentado como revisão dupla independente. Se o
segundo autor revisar depois, o registro é `POST_CAL_B3_SECONDARY_AUDIT` (novo
arquivo; a ficha original nunca é editada em silêncio); problema material vira
discrepância formal com avaliação de impacto científico; rationales e
evidência bruta nunca são alterados retroativamente.

**Material unsupported claim** (mesma definição): afirma fato ou regra
específica, que não foi fornecida ao agente, e que influencia materialmente a
justificativa/decisão. Technical não conhece ticker, data, preço absoluto,
notícia, macro nem fundamentos; Risk não pode criar thresholds, hard rules,
probabilidades nem limites inexistentes.

**Coerência rationale/ação.** Technical: rationale compatível com o sinal.
Risk: rationale compatível com o veredito e com o payload. Portfolio:
rationale compatível com a ação e com o veredito do Risk.

**Regra de status.**

```text
algum gate automático falhou     -> CAL_B3_FAIL — HOLDOUT CONSUMED
                                    (revisão humana só arquivada como análise;
                                    não muda o FAIL)
gates PASS, ficha incompleta     -> CAL_B3_AWAITING_PRIMARY_AUTHOR_REVIEW
                                    (intermediário, não final)
ficha completa, algum FAIL       -> CAL_B3_FAIL — HOLDOUT CONSUMED
ficha completa, tudo PASS        -> CAL_B3_PASS — SANITY CHECK ONLY
replay exato impossível          -> CAL_B3_INVALID — PARTIAL HOLDOUT CONSUMED
```

PASS exige CB3-A, CB3-S, CB3-C, CB3-HR, CB3-TSEM, CB3-TTRANS, CB3-R1, CB3-R2,
CB3-R3 e CB3-D PASS e a ficha do autor principal toda PASS. Não existe gate de
quantidade mínima de vetos do Risk. Com FAIL: não corrigir, não rerodar, não
alterar prompt nem checker, não trocar âncora, não relaxar threshold. Parar.
Com `CAL_B3_PASS — SANITY CHECK ONLY` (não é evidência de performance OOS):
`SYSTEM_CALIBRATION_COMPLETE = True`, `H2_FINAL_TREATMENT_VERSION = 3`,
`READY FOR SYSTEM FREEZE DESIGN`; Validation não é executada automaticamente.

**Pacote de auditoria por âncora.** Data, payload de features, as 5 saídas
Technical, votos e consenso, achados dos checkers Technical e do Risk,
entrada/saída de Risk e Portfolio quando chamados, causa final e reason codes.
Nenhuma informação financeira futura.

**Evidência operacional.** Chamadas lógicas, tentativas HTTP, retries, erros
transitórios do provedor, latência p50/p90, tokens de entrada, saída e
thinking. Sem custo monetário (não há fonte de preço versionada).

**Ordem dos commits.** (1) checker v2 + corpus de regressão (31d8714); (2)
este freeze; (3) autorização limitada/guards/gates; (4) evidência bruta
selada; (5) gates automáticos e pacote de auditoria; (6) revisão do autor
principal; (7) status final. Checker e protocolo commitados antes da primeira
chamada live; evidência bruta nunca muda depois de selada.

### Registro de execução (append-only)

Resultados das regras predeclaradas acima. Não são amendments: nenhuma regra
mudou.

```text
2026-10-04  Diagnostic Hardening, thinking_level = low
            commit f1b903932119ee030354c24d12f7b018f50a4ec2 (freeze)
            evidência docs/evidence/h2/hardening_low_20261004T194849Z/
            G-A 0 falhas finais            PASS
            G-T 0 truncamentos             PASS
            G-I total_hold_rate 0.667      PASS (< 0.90)
            G-F same_state_flip_rate 0.0   PASS (<= 0.10)
            1 HTTP 503 recuperado por retry (fora de G-A)
            -> LOW FROZEN para o H2 v1 (H2_FROZEN_THINKING_LEVEL);
               MEDIUM e HIGH não testados
2026-10-04  B0, uma passada completa sobre H (R = 1), thinking_level = low
            commit 4ec2ba9857d569cfaabbbf7e59d7b13c771edd57
            evidência docs/evidence/h2/b0_low_20261004T195254Z/
            0 falhas finais, 0 truncamentos, 65 chamadas lógicas, 0 retries
            -> B0 PASS: baseline = commit 4ec2ba9 + H2_FREEZE_V1_PARAMS
               (thinking_level=low) + prompts registrados no trace
            [as duas entradas acima: SUPERSEDED BY CALENDAR-CORRECTED REBASELINE,
             Amendment 1]
2026-10-04  Diagnostic Hardening REBASELINED (Amendment 1), thinking_level = low
            commit 62a0c5d93f5f8e15d4c030587864b918e170c8e1, snapshot corrigido
            evidência docs/evidence/h2/hardening_low_20261004T201555Z/
            G-A 0 · G-T 0 · G-I 0.633 · G-F 0.0 -> todos PASS
            2 erros transitórios recuperados por retry (fora de G-A)
            -> LOW FROZEN — REBASELINED; MEDIUM e HIGH não testados
2026-10-04  B0 REBASELINED, uma passada completa sobre o H corrigido (R = 1)
            commit 73db75b5127f97327a6bc86d5d3f31feb5fe26d8
            evidência docs/evidence/h2/b0_low_20261004T202013Z/
            0 falhas finais, 0 truncamentos, 67 chamadas lógicas, 0 retries
            -> B0 PASS — REBASELINED: baseline = commit 73db75b +
               H2_FREEZE_V1_PARAMS (thinking_level=low) + snapshot
               20261004T201258177516Z-b4cf39fc + prompts registrados no trace
2026-10-04  Gate de identificabilidade de CAL-A (Amendment 2)
            commit d3641af46bd3a63ddaa09ce8db4dff40aa0fe3a1
            evidência docs/evidence/cal_a/identifiability.json
            sem LLM, sem t+1, sem retorno; só volatilidade até t e veto
            distinguishing_anchors = 7 (>= 3)  -> CAL-A REDUCED
            nenhuma performance de CAL-A executada; CAL-B trancada
2026-10-04  CAL-A (Amendment 3), 20 âncoras x R=3 x 6 configurações, pareada
            execução abortada em 184/360 por bloqueio de rename no Windows
            (Amendment 4); retomada no commit 18fdc52 com os 30 blocos completos
            evidência docs/evidence/cal_a/run_20261004T231101Z/ (+ abortada
            run_20261004T203435Z/)
            360/360 avaliações; auditoria de pareamento: true; CAL-B: 0 sessões
            S1 = -0.00025157 nas seis configurações (exatamente iguais)
            causas finais diferem só em 2023-01-18 (veto duro vs veto do LLM
            de risco, ambos sem trade); retornos diferem em 0 blocos
            -> CAL_A_DISCRIMINATION = NONE; desempate pelo menor config_id
            -> CAL_A_SELECTED_CONFIG = 1 (volatility_window 21,
               risk_max_volatility 0.40), congelado
            -> CAL_A_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK (Amendment 5):
               desempate, não desempenho superior
2026-10-04  Sequential Development (Amendment 5), D01-D03 x R=3, pareado
            SEQUENTIAL_DEV_FREEZE_COMMIT 2461952a4b1ee84a08aa63261f6a677d79cca3bb
            evidência docs/evidence/sequential_dev/run_20261004T235634Z/
            9/9 runs; 127 sessões de decisão 2024-03-01..2024-08-29,
            liquidação 2024-08-30; 0 falhas finais; 9 erros transitórios
            recuperados por retry; pareamento técnico 381/381; CAL-B: 0 sessões
            drawdown canônico máximo 0.080 < 0.15: nenhum limite da grade
            alcançado; trajetórias idênticas nas três configurações em cada
            repetição (Risk/Portfolio 100% reaproveitados por identidade)
            Sharpe v1 por repetição 1.8445 / 2.4484 / 1.4058 (iguais em D01-D03)
            S2 = 1.8995241002787928 nas três (exatamente iguais)
            -> SEQUENTIAL_DEV_DISCRIMINATION = NONE
            -> SEQUENTIAL_DEV_SELECTED_CONFIG = D01 (risk_max_drawdown 0.25),
               basis PROTOCOL_TIE_FALLBACK, congelado
2026-10-04  Stress Probing: compromisso das janelas (Amendment 6), ANTES de
            qualquer chamada ao provedor
            STRESS_FREEZE_COMMIT 6a64c34 (amendment); o primeiro select nele
            falhou ao serializar a proveniência do snapshot (TypeError),
            antes de gravar ou imprimir qualquer métrica; correção só de
            script em 2b4f578 = STRESS_SELECTION_COMMIT, onde select rodou
            evidência docs/evidence/stress/selection.json, risk_probes.json
            só mercado, só barras dentro dos 20 estratos não-CAL-B
            ranking (top 3)  M1 drawdown   11 0.630 · 2 0.442 · 22 0.191
                             M2 vol        11 1.307 · 2 0.798 · 4 0.517
                             M3 pior ret.  11 -0.297 · 2 -0.149 · 29 -0.066
                             M4 gap        11 0.220 · 2 0.138 · 4 0.124
            S1 MAX_DRAWDOWN            estrato 11  2020-02-07..2020-04-23
                                       (decisão até 04-22)  0.6304418642835597
            S2 MAX_REALIZED_VOLATILITY estrato 2   2018-03-29..2018-06-12
                                       (11 já usado)        0.7984230364753621
            S3 WORST_DAILY_RETURN      estrato 29  2023-10-02..2023-12-13
                                       (11, 2 usados)      -0.06605042741788614
            S4 MAX_ABS_OVERNIGHT_GAP   estrato 4   2018-08-24..2018-11-07
                                       (11, 2 usados)       0.12437432848274144
            estrato seguinte é CAL-B em S1, S2 e S3; nenhuma ordem pode entrar
            probes determinísticos de risco: 19/19 PASS
            -> STRESS_SELECTED_WINDOWS congeladas
2026-10-04  Stress Probing (Amendment 6), S1-S4 x R=3, live independente
            commit de execução 9f06b09 (janelas comprometidas)
            evidência docs/evidence/stress/run_20261005T011248Z/
            12/12 trajetórias; 3133 chamadas live, 0 do banco; 2
            ConnectionResetError recuperados por retry; CAL-B: 0 sessões
            S-A 0 falhas finais          PASS
            S-T 0 truncamentos           PASS
            S-C 0 violações causais/fronteira (inclui 0 divergência entre
                métricas recalculadas e o prompt do LLM de risco)  PASS
            S-R 0 violações do contrato duro  PASS
            regra de volatilidade EXERCISED: 94 COMPRA com vol > 0.40
              (S1 58, S2 27, S4 9), todas decididas pela regra dura antes do
              LLM de risco (85 RISK_VETO_VOLATILITY, 9 BUY_AT_TARGET_NOOP)
            regra de drawdown NOT_EXERCISED: drawdown canônico máximo 0.179
              (S1, 2020) < 0.25 -> HISTORICAL_STRESS_DRAWDOWN_RULE_NOT_EXERCISED;
              o contrato do limiar fica coberto só pelos probes determinísticos
            financeiro (DESCRIPTIVE ONLY, sem autoridade):
              S1 Sharpe -2.596 nas 3 (retorno -13.9%, MDD 17.9%; trajetórias
                 idênticas)
              S2 Sharpe 2.414 / 3.366 / 3.131 (retorno +11.1% / +16.9% / +14.0%)
              S3 Sharpe -0.381 / -0.571 / -0.571 (retorno -1.3% / -1.8% / -1.8%)
              S4 Sharpe 3.481 nas 3 (retorno +24.8%; trajetórias idênticas)
            -> STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL
               (integridade/contratos; não é aprovação econômica);
               nenhum parâmetro alterado; CAL-B não executada
2026-10-04  CAL-B one-shot (Amendment 7), 10 âncoras x R=1, outcome-blind
            CAL_B_FREEZE_COMMIT 02ab735 (freeze + autorização limitada)
            evidência docs/evidence/cal_b/run_20261005T021523Z/
            selo bruto commitado antes do pacote (33785f9); selos conferidos
            10/10 seladas na ordem comprometida; 51 chamadas lógicas, 51 HTTP
            200, 0 retry, 0 recuperação; nenhum preço t+1 lido
            CB-A PASS · CB-S PASS · CB-C PASS · CB-R PASS
            CB-D FAIL: 9/10 HOLD (8 TECH_EXPLICIT_HOLD + 1
                 RISK_VETO_VOLATILITY), total_hold_rate 0.90 >= 0.90
            distribuição: técnico MANTER 8 · COMPRA 1 · VENDA 1; causas
            TECH_EXPLICIT_HOLD 8 · RISK_VETO_VOLATILITY 1 · ACTION_SELL 1
            (VENDA com carteira zerada: alvo 0, sem exposição)
            pré-filtro léxico: 0 marcações; revisão humana não altera o status
            -> CAL_B_FAIL — HOLDOUT CONSUMED; CAL_B_STATUS = CONSUMED;
               SYSTEM_CALIBRATION_COMPLETE = False; nenhum rerun, nenhum gate
               relaxado, nenhum parâmetro ou prompt alterado
2026-10-05  H2 v2 (Amendment 8): compromisso da CAL-B2, ANTES de qualquer chamada v2
            seed SHA256("HEDGE-FUND-LAB|CAL-B2|" + 51d73b22...f38c0)
            só calendário; excluídas CAL-B1, H_real (atual e pré-Amendment 1),
            âncoras CAL-A e toda sessão de decisão em docs/evidence
            evidência docs/evidence/cal_b2/selection.json
            estrato 3  2018-07-19 -> 2018-08-16    estrato 18 2021-08-20 -> 2021-09-22
            estrato 6  2019-03-07 -> 2019-04-05    estrato 21 2022-03-31 -> 2022-04-07
            estrato 9  2019-10-15 -> 2019-10-07    estrato 24 2022-11-04 -> 2022-11-01
            estrato 12 2020-06-01 -> 2020-07-01    estrato 27 2023-06-15 -> 2023-06-26
            estrato 15 2021-01-13 -> 2021-01-21    estrato 30 2024-01-22 -> 2023-12-18
            CAL_B2_COMMITMENT_SHA256 518dd9ddc132244726fc40b2939684876c6f69bf6bad67ea1f91a78fc4e9b167
            -> CAL-B2 SELADA (runner e banco recusam as datas; não executada)
2026-10-05  H2 v2 — hardening dirigido ao defeito (Amendment 8), CAL-B1 x R=3, N=5
            commit a96d78c (CAL-B2 já comprometida); primeira chamada live v2
            evidência docs/evidence/h2_v2/defect_hardening_20261006T022111Z/
            V2-S1 contradições semânticas 0/150 votos   PASS (v1 CAL-B1: 32/50)
            V2-S2 transições não suportadas 0/150       PASS (v1 CAL-B1: 33/50)
            V2-A  0 falhas finais (1 HTTP 503 recuperado) PASS
            V2-T  0 truncamentos                         PASS
            V2-D  total_hold_rate 0.867 (26/30) < 0.90   PASS
                  explicit hold 0.733 · vetos de risco 0.133 · flip 0.0
            -> H2_V2 MINIMAL DEFECT FIX PASSED; segue a reexecução de development v2
2026-10-05  Diagnostic Hardening v2 (H = 8 H_syn + 4 H_real, R = 5), thinking low
            commit 312f0e7; evidência docs/evidence/h2_v2/hardening_low_20261006T022444Z/
            G-A 0 · G-T 0 · G-I 0.383 (v1 rebaselined: 0.633) · G-F 0.0 -> PASS
            348 chamadas lógicas, 0 retries
2026-10-05  B0 v2 (H, R = 1); evidência docs/evidence/h2_v2/b0_low_20261006T022838Z/
            G-A 0 · G-T 0 · G-I 0.50 -> B0 PASS (v2)
2026-10-05  CAL-A v2: mesmas 20 âncoras, grade, R = 3, pareamento, S1 e desempate
            commit 7fb50dd; evidência docs/evidence/cal_a_v2/run_20261006T022946Z/
            360/360 avaliações; pareamento técnico true; CAL-B (B1/B2): 0 sessões
            360 chamadas live (300 técnicas), 1617 do banco, 1 HTTP 503 recuperado
            S1 = 0.00071857 nas seis configurações (exatamente iguais)
            -> CAL_A_V2_DISCRIMINATION = NONE -> config 1 (volatility_window 21,
               risk_max_volatility 0.40), basis PROTOCOL_TIE_FALLBACK
2026-10-06  Sequential Development v2: mesma janela, D01-D03, R = 3, S2, fronteira
            commit b0821b4; evidência docs/evidence/sequential_dev_v2/run_20261006T023608Z/
            9/9 runs; base 21/0.40 (CAL-A v2); pareamento técnico 381/381;
            CAL-B (B1/B2): 0 sessões; data_end máx. 2024-08-30; 1 reset recuperado
            drawdown canônico máx. 0.144 / 0.166 / 0.220 por repetição: a regra
            D02 (0.15) disparou em r2 (11 vetos) e r3 (27), todos acima do limite,
            0 ordens de compra acima do limite
            Sharpe v1 por repetição D01 0.9587 / 0.1994 / -1.2595
                                    D02 0.9587 / -0.4917 / -0.4635
                                    D03 = D01
            S2 D01 -0.0338 · D02 +0.0012 · D03 -0.0338
            -> SEQUENTIAL_DEV_V2_DISCRIMINATION = YES -> D02 (risk_max_drawdown
               0.15), basis EMPIRICAL_S2 (regra do Amendment 5; R = 3, development
               evidence, sem afirmação de superioridade robusta)
            nota: a lista "manter" da tarefa v2 citava risk_max_drawdown 0.25 como
            parte da mudança isolada (hardening dirigido); o Amendment 8 manteve a
            autoridade do Sequential Development, cuja regra seleciona 0.15
2026-10-06  Stress v2 — execução ABORTADA (falha operacional, não do tratamento)
            commit 54d3d05; evidência preservada docs/evidence/stress_v2/run_20261006T030202Z/
            S1 r1 completo; antes de S1 r2 o operador criou um arquivo não rastreado
            (scripts/h2_v2_summary.py) e o guard de proveniência do runner recusou
            o run seguinte (DirtyRepositoryError) antes de construir o participante.
            Nenhum código muda. Pela política congelada do Stress (sem checkpoint
            predeclarado), as 12 trajetórias são refeitas do zero; o run abortado
            fica fora de qualquer análise
2026-10-06  Stress v2 (reexecução completa): mesmas 4 janelas, R = 3, mesmos gates
            commit e9fd332; evidência docs/evidence/stress_v2/run_20261006T030655Z/
            config 21 / 0.40 / dd 0.15 (seleções v2) + prompt técnico v2
            12/12 trajetórias; 3124 chamadas live, 0 do banco; 22 HTTP 503
            recuperados por retry; CAL-B (B1/B2): 0 sessões
            S-A 0 falhas finais · S-T 0 · S-C 0 violações · S-R 0 violações -> PASS
            regra de volatilidade EXERCISED; regra de drawdown NOT_EXERCISED pela
            definição congelada (COMPRA com dd > 0.15 só mascarada pela
            volatilidade ou já no alvo); MDD de S2 0.381 > 0.15: o limite veta
            entrada, não é stop-loss (limitação registrada)
            financeiro (DESCRIPTIVE ONLY): Sharpe S1 -2.840 (x3), S2 -1.068/-1.068/
            -0.601, S3 -0.793/-0.331/-0.793, S4 3.794 (x3)
            -> STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL (v2)
2026-10-06  Resumo de development v2 (descritivo; docs/evidence/h2_v2/development_summary.json)
            votos técnicos com contradição semântica, v1 -> v2: Hardening 0.317 -> 0.000,
            CAL-A 0.383 -> 0.003, Sequential Dev 0.351 -> 0.000, Stress 0.335 -> 0.000
            votos com transição não suportada, v1 -> v2: 0.37-0.42 -> 0.000-0.009
            TECH_EXPLICIT_HOLD v1 -> v2: Hardening 0.617 -> 0.383, CAL-A 0.467 -> 0.650,
            Sequential Dev 0.627 -> 0.648, Stress 0.523 -> 0.539
            seleções v2: CAL-A config 1 (21/0.40, PROTOCOL_TIE_FALLBACK);
            Sequential Dev D02 (dd 0.15, EMPIRICAL_S2)
            CAL-B2: 0 sessões de decisão v2, não executada; nenhuma sessão v2 >= 2024-09-02
            -> H2_V2 DEVELOPMENT COMPLETE — READY FOR CAL-B2 PROTOCOL
2026-10-06  CAL-B2 one-shot (Amendment 9), 10 âncoras x R=1, outcome-blind
            CAL_B2_FREEZE_COMMIT f6e8c93; autorização/guards c9cc719 (batch)
            evidência docs/evidence/cal_b2/run_20261006T125636Z/
            selo bruto commitado antes do pacote (59533dc); selos conferidos
            10/10 seladas na ordem comprometida; 56 chamadas lógicas, 56 HTTP
            200, 0 retry, 0 recuperação; spec 89ac1207...; nenhum preço t+1 lido
            CB2-A PASS · CB2-S PASS · CB2-C PASS · CB2-R PASS
            CB2-SEM PASS (0/50 votos com contradição) · CB2-TRANS PASS (0/50)
            CB2-D PASS: 7/10 HOLD (6 TECH_EXPLICIT_HOLD + 1 RISK_VETO_LLM),
                 total_hold_rate 0.70 < 0.90
            distribuição: técnico MANTER 6 · COMPRA 3 · VENDA 1; causas
            TECH_EXPLICIT_HOLD 6 · ACTION_BUY 2 · ACTION_SELL 1 (VENDA com
            carteira zerada, alvo 0) · RISK_VETO_LLM 1; nenhum veto duro
            (vol máx. nas COMPRA 0.371 <= 0.40; drawdown 0 na âncora)
            pré-filtro léxico: 0 marcações
            -> CAL_B2_STATUS = CONSUMED; status CAL_B2_AWAITING_HUMAN_REVIEW
               (gates automáticos PASS; fichas dos dois autores em branco)
2026-10-06  H2 v3 (Amendment 10): governança da v2 e compromisso da CAL-B3, ANTES de qualquer chamada v3
            CAL-B2: status histórico CAL_B2_AWAITING_HUMAN_REVIEW preservado (fichas em
            branco, segunda revisão não aguardada); H2_V2_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE =
            True (CAL_B2 CONSUMED AND USED AS DEVELOPMENT EVIDENCE)
            contrato e checker do Risk congelados em c148dc7 (+ 9101c93, só estilo de teste)
            seed SHA256("HEDGE-FUND-LAB|CAL-B3|" + 518dd9dd...b167) = f1c36f4d...8184
            só calendário; seleção rodada em eb3fd1d; excluídas CAL-B1, CAL-B2, H_real
            (atual e pré-Amendment 1), âncoras CAL-A, Sequential Dev e as 369 sessões de
            decisão em docs/evidence (inclui Stress e todo development v1/v2)
            evidência docs/evidence/cal_b3/selection.json
            estrato 3  -> 2018-08-03 (49 cand.)    estrato 18 -> 2021-08-17 (48)
            estrato 6  -> 2019-03-19 (48)          estrato 21 -> 2022-03-11 (48)
            estrato 9  -> 2019-10-18 (49)          estrato 24 -> 2022-11-29 (48)
            estrato 12 -> 2020-05-13 (48)          estrato 27 -> 2023-05-12 (48)
            estrato 15 -> 2021-01-06 (49)          estrato 30 -> 2024-01-11 (48)
            CAL_B3_COMMITMENT_SHA256 a5cadecd361de5059370bf4bfa97b1417b82eb8951950cf92b0aebc7edecdbaf
            -> CAL-B3 SELADA (runner e banco recusam as datas; não executada)
2026-10-06  H2 v3 — hardening dirigido ao defeito (Amendment 10), CAL-B2 x R=3
            commit 2e33eac (CAL-B3 já comprometida); primeira chamada live v3
            evidência docs/evidence/h2_v3/defect_hardening_20261006T151527Z/
            config final v2 (21 / 0.40 / 0.15 / 1.0) + Risk prompt v2 (990424e3...)
            checker congelado: risk_contract.py 7636ad26 · h2_v3.py e6f5ca5a
            Technical: 150/150 respostas CAL-B2 reaproveitadas por identidade exata,
              0 chamada Technical nova, 0 mismatch; prompt técnico a3dec11f em todas
            Portfolio: 3 replay (VENDA auto-aprovada) + 9 live; Risk: 9 live
            V3-R1 limiar de confidence inventado 0/9             PASS (v1 na CAL-B2: 1/3)
            V3-R2 regra numérica inventada 0/9                   PASS
            V3-R3 contradições rationale/veredito 0/9            PASS
            V3-S  0 falha, 0 truncamento, 0 erro final, 0 inversão/fallback  PASS
            V3-D  total_hold_rate 0.60 (18/30, todos TECH_EXPLICIT_HOLD) < 0.90  PASS
            caso-alvo 2023-06-26: mesmo payload lógico do Risk nas 3 repetições;
              v1 VETADO com "abaixo do limiar de 50%" -> v3 APROVADO x3, sem limiar
              nem regra inventada (mudança de decisão não era critério)
            Risk v3: 9/9 APROVADO (v1 na CAL-B2: 2 APROVADO, 1 VETADO) — registrado
              como observação descritiva, sem autoridade de seleção
            18 HTTP 200, 0 retry
            -> H2_V3 MINIMAL DEFECT FIX PASSED; segue a reexecução de development v3
2026-10-06  Diagnostic Hardening v3 (H = 8 H_syn + 4 H_real, R = 5), thinking low
            commit dff13ee; evidência docs/evidence/h2_v3/hardening_low_20261006T151731Z/
            spec = a ex ante da v2 (freeze v1, LOW, prompt técnico v2) + Risk prompt v2
            Technical 300/300 replay do Hardening v2 (mesma repetição), 0 mismatch;
            Portfolio 26 replay + 11 live; Risk 11 live (11 APROVADO)
            G-A 0 · G-T 0 · G-I 0.383 (v2: 0.383) · G-F 0.0 -> PASS
            checker do Risk (descritivo): V3-R1 0/11 · V3-R2 0/11 · V3-R3 1/11 — o único
            achado é FALSO POSITIVO conhecido ("Não há fatores adversos ... que justifiquem
            veto": negação fora da janela de 30 caracteres); checker congelado, não alterado
            22 HTTP 200, 0 retry
2026-10-06  B0 v3 (H, R = 1); evidência docs/evidence/h2_v3/b0_low_20261006T151857Z/
            Technical 60/60 replay do B0 v2; Risk 2 live (2 APROVADO), 0 achado do checker
            G-A 0 · G-T 0 · G-I 0.50 -> B0 PASS (v3)
2026-10-06  CAL-A v3: mesmas 20 âncoras, grade, R = 3, pareamento, S1 e desempate
            commit e5c66d3; evidência docs/evidence/cal_a_v3/run_20261006T151945Z/
            360/360 avaliações; pareamento técnico true; CAL-B (B1/B2/B3): 0 sessões
            Technical 1800/1800 replay da CAL-A v2 (mesma repetição), 0 mismatch, 0 live;
            40 chamadas live (20 Risk, 20 Portfolio), 0 retry; Portfolio 66 replay
            Risk v3: 20/20 APROVADO; checker V3-R1 0 · V3-R2 0 · V3-R3 0
            S1: configs 2, 3, 6 = 0.00125779; configs 1, 4, 5 = 0.00071857
            única âncora que discrimina: 2023-01-18 (vol 0.445 em 21 / 0.520 em 63):
              0.40 e 63/0.50 vetam por regra dura; 21/0.50, 21/0.60 e 63/0.60 levam ao
              Risk v3, que aprova (na v2 o Risk v1 vetava por confidence baixa)
            -> CAL_A_V3_DISCRIMINATION = YES, empate exato no topo (2, 3, 6) -> menor
               config_id -> config 2 (volatility_window 21, risk_max_volatility 0.50),
               basis EMPIRICAL_S1 (uma âncora, R = 3: development evidence, sem
               afirmação de superioridade robusta)
2026-10-06  Sequential Development v3: mesma janela, D01-D03, R = 3, S2, fronteira
            commit 9e99d1c; evidência docs/evidence/sequential_dev_v3/run_20261006T152426Z/
            9/9 runs; base 21 / 0.50 (CAL-A v3); pareamento técnico 381/381;
            CAL-B (B1/B2/B3): 0 sessões; data_end máx. 2024-08-30
            Technical 5715/5715 replay do Sequential v2 (mesma repetição), 0 mismatch;
            26 chamadas live (Risk 11 únicas, todas APROVADO; Portfolio), 0 retry
            checker do Risk: V3-R1 0 · V3-R2 0 · V3-R3 0
            drawdown canônico máx. por repetição 0.144 / 0.166 / 0.223 (D01/D03); D02 (0.15)
            vetou por regra dura em r2 (11) e r3 (27), todos acima do limite, 0 ordens
            acima do limite; com 0.25/0.35 o Risk v3 aprova as entradas que o Risk v1 vetava
            com "excede os limites prudenciais" (regra inventada, V3-R2 na evidência v2)
            Sharpe v1 por repetição D01 0.9653 / 0.2436 / -0.4247
                                    D02 0.9653 / -0.3947 / -0.3565
                                    D03 = D01
            S2 D01 0.2614 · D02 0.0714 · D03 0.2614
            -> SEQUENTIAL_DEV_V3_DISCRIMINATION = YES, empate exato no topo (D01, D03) ->
               menor config_id -> D01 (risk_max_drawdown 0.25), basis EMPIRICAL_S2
               (R = 3, development evidence, sem afirmação de superioridade robusta)
2026-10-06  Stress v3: mesmas 4 janelas comprometidas (sem reseleção), R = 3, mesmos gates
            commit a19e26d; evidência docs/evidence/stress_v3/run_20261006T152701Z/
            config 21 / 0.50 / dd 0.25 (seleções v3) + Risk prompt v2
            12/12 trajetórias; Technical 2985/2985 replay do Stress v2 (mesma repetição),
            0 mismatch; Portfolio 44 replay + 85 live; 102 chamadas live, 0 retry;
            CAL-B (B1/B2/B3): 0 sessões
            S-A 0 falhas finais · S-T 0 · S-C 0 violações · S-R 0 violações -> PASS
            regra de volatilidade EXERCISED (S2, S4); regra de drawdown NOT_EXERCISED pela
            definição congelada; MDD de S2 0.381 > 0.25: o limite veta entrada, não é
            stop-loss (limitação registrada, igual à v2)
            Risk v3: 17/17 APROVADO; checker V3-R1 0 · V3-R2 0 · V3-R3 1/17 — FALSO
            POSITIVO conhecido ("sem violação de limites ou condições adversas que
            justifiquem veto": negação fora da janela); checker congelado, não alterado
            financeiro (DESCRIPTIVE ONLY): Sharpe S1 -1.899/-1.899/-1.599, S2 -1.068/
            -1.068/-0.601, S3 -0.331/0.800/1.447, S4 4.266/4.266/4.536
            -> STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL (v3)
2026-10-06  Resumo de development v3 (descritivo; docs/evidence/h2_v3/development_summary.json)
            respostas únicas do Risk LLM com limiar de confidence inventado (V3-R1):
              v1 Hardening 0.067 · CAL-A 0.227 · Stress 0.200; v2 CAL-A 0.050 · Stress 0.200 ·
              CAL-B2 0.333 -> v3 0.000 em todas as fases (0/70)
            regra numérica inventada (V3-R2): v2 Sequential Dev 0.278 -> v3 0.000 (0/70)
            V3-R3 v3: 2/70, ambos o falso positivo conhecido de negação distante
            Technical: 11010 respostas v2 reaproveitadas por identidade exata, 0 live,
              0 mismatch; Portfolio 173 replay + 206 live
            OBSERVAÇÃO (sem autoridade): vereditos do Risk LLM v1 48 APROVADO / 19 VETADO,
              v2 55 / 18, v3 70 / 0 — sem regra inventada, o Risk v3 não vetou nenhuma
              entrada que passou pelas regras duras; vai para o desenho da CAL-B3
            seleções v3: CAL-A config 2 (21 / 0.50, EMPIRICAL_S1, empate no topo 2/3/6);
            Sequential Dev D01 (dd 0.25, EMPIRICAL_S2, empate no topo D01/D03)
            configuração final v3: 21 / 0.50 / 0.25 / 1.0 + Technical prompt v2 + Risk prompt v2
            CAL-B3: 0 sessões de decisão v3, selada, não executada; nenhuma sessão v3 >= 2024-09-02
            -> H2_V3 DEVELOPMENT COMPLETE — READY FOR CAL-B3 PROTOCOL
```
