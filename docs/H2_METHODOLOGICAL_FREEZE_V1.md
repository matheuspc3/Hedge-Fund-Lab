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
```
