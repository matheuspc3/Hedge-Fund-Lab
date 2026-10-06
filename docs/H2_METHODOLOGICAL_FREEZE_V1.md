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
```
