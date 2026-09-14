# Protocolo experimental do Hedge-Fund-Lab

> **STATUS: DRAFT — NÃO CONGELADO**
>
> Este documento é o contrato científico do experimento, não um roadmap. Valores
> e políticas marcados como `TBD` ou `PENDENTE DE CONGELAMENTO` não foram
> aprovados pela dupla/orientador e não podem ser tratados como decisão final.

## 0. Desenho em uma página

O laboratório reproduz um problema operacional, não um problema de aprendizado
supervisionado:

```text
informação conhecida até hoje
        v
sistema multiagente
        v
decisão para o próximo pregão
        v
amanhã acontece
        v
o novo dado passa a fazer parte do histórico
        v
próxima decisão
```

O experimento histórico simula exatamente essa condição, em quatro estágios
sequenciais mais um estágio operacional posterior:

```text
SYSTEM CALIBRATION      (ajuste retrospectivo do sistema, resultado observável)
        v
FREEZE                  (configuração identificável e reproduzível)
        v
PSEUDO-LIVE VALIDATION  (datas fora da calibração, sistema congelado)
        v
FINAL TEST              (avaliação final, separada de calibração e validação)
        v
LIVE / SHADOW           (decisão para o próximo pregão real)
```

A SYSTEM CALIBRATION, por sua vez, tem subfases com autoridades distintas:

```text
DIAGNOSTIC HARDENING -> CAL-A -> SEQUENTIAL DEVELOPMENT -> STRESS REPORT -> CAL-B
```

Detalhamento na seção 5; a governança das subfases, suas autoridades e suas
regras de invalidação estão na seção 5.12. Onde este documento diz apenas
`TEST`, leia **FINAL TEST**.

## 1. Research question

**STATUS: DRAFT — PENDENTE DE CONGELAMENTO.**

Sob a mesma informação historicamente disponível em cada data de decisão, o
mesmo relógio, o mesmo capital, os mesmos custos e o mesmo modelo de execução,
qual é o efeito da utilização de um sistema multiagente baseado em LLM sobre o
desempenho líquido ajustado ao risco em comparação com abordagens quantitativas
clássicas?

A comparação é feita em **ambiente causal pseudo-live**: em cada data simulada
`t` o participante decide com o conjunto de informação que estaria disponível em
`close(t)`, e o resultado de `t+1` só passa a existir para o sistema quando a
simulação avança para `t+1` (seção 5). Não há, no experimento principal v1,
estimação de pesos do LLM sobre período algum.

A redação final e a definição operacional de desempenho líquido ajustado ao
risco devem ser aprovadas **no FREEZE, antes da PSEUDO-LIVE VALIDATION** — e não
apenas antes do FINAL TEST. Nenhuma redação está congelada.

## 2. Hypotheses

- Hipótese principal: `TBD`.
- Hipóteses nulas e alternativas formais: `TBD`.
- Critérios de aceitação/rejeição: `TBD`.
- Hierarquia entre hipótese principal e análises exploratórias: `TBD`.

Nenhuma hipótese será reformulada após observar o conjunto TEST sem ser marcada
como análise pós-hoc.

## 3. Universe

- Universo principal candidato: os 10 ativos já usados pelo projeto.
- Análises secundárias candidatas: PETR4 e WEGE3.
- Critérios de inclusão, exclusão, liquidez e sobrevivência: `TBD`.
- Tratamento de entradas, saídas e mudanças de ticker: `TBD`.

**STATUS: proposta / pendente de congelamento.** O universo principal deve ser
comum a todos os participantes.

## 4. Dataset/snapshot

Cada execução científica deve referenciar um snapshot imutável contendo, no
mínimo:

- fonte e parâmetros de download;
- cobertura solicitada e efetivamente observada por ativo;
- política de ajuste por proventos e splits;
- timezone, moeda e calendário;
- regras e relatório do gate de qualidade OHLCV;
- horário de obtenção, versão e hash dos arquivos;
- versão do pipeline de features.

Fonte definitiva, formato, localização, política de ajustes e schema do manifest:
`TBD`.

Implementação técnica atual, ainda sem congelar essas decisões: o
`DatasetSnapshot` materializa CSVs em diretório próprio, calcula SHA-256 por
arquivo e registra proveniência e cobertura por sessões do `B3Calendar` local.
O `ExperimentRunner` consome apenas esse artefato — nunca `yfinance` nem o cache
mutável —, recusa snapshot com `scientific_ready=false` e reconfere tamanho e
hash de cada arquivo antes de executar.

Capacidade técnica adicional, também sem congelar decisão científica alguma: o
manifest do snapshot possui identidade verificável. O `snapshot_id` é
`timestamp + digest` do JSON canônico do manifest menos o próprio ID, cobrindo
`quality`, `coverage`, `files`, `tickers`, intervalos, fonte, calendário e
pipeline; o carregamento reconfere o digest e o nome do diretório. Adulterar o
manifest — inclusive `scientific_ready` — é detectado, sem que isso substitua a
conferência dos SHA-256 dos CSVs. É tamper-evidence do artefato, não assinatura
criptográfica.
Lacunas, datas inesperadas ou intervalo sem sessões resultam em
`scientific_ready=false`; não há preenchimento de barras. O calendário é
explicitamente identificado como aproximação local com exceções configuráveis e
ainda requer validação contra fonte oficial/versionada.

## 5. Desenho experimental — calibração retrospectiva e avaliação pseudo-live

**STATUS: PENDENTE DE CONGELAMENTO.** O desenho abaixo é a metodologia aprovada;
datas, períodos e valores continuam `TBD`.

### 5.1 Por que não é um TRAIN/TEST clássico

O protocolo clássico

```text
treinar modelo em TRAIN
-> aplicar pesos treinados em TEST
```

pressupõe um modelo cujos parâmetros são estimados sobre os dados do período de
treino. Não é o caso do experimento principal v1. O LLM chega **pré-treinado** e,
neste experimento:

- não haverá fine-tuning;
- não haverá treinamento supervisionado dos pesos do modelo;
- não haverá treinamento sobre retornos futuros;
- não haverá uso de informação posterior à data simulada.

Isso **não** dispensa a separação entre desenvolvimento e avaliação, que continua
obrigatória — por uma razão diferente: quem se ajusta ao período observado não é
o modelo, são os pesquisadores (seção 5.6). O que muda é a natureza do objeto
ajustado: ajusta-se o **sistema**, não o modelo.

### 5.2 System Calibration não é treinamento

Distinção terminológica obrigatória neste projeto.

```text
retrospective system calibration   (calibração retrospectiva do sistema)
        != treinamento do LLM
        != calibração estatística de confidence -> probabilidade
```

**System Calibration** é o ajuste retrospectivo do sistema declarado, sobre datas
históricas conhecidas. Abrange, quando existirem:

- prompts;
- papéis dos agentes;
- quorum;
- parâmetros de consenso;
- temperaturas;
- limites de risco;
- `long_target_weight` — declarado e congelado, **não** calibrado por desempenho
  (seções 5.12 e 11);
- `decision_frequency`;
- regras de recuperação de contexto histórico;
- demais configurações declaradas do sistema.

Nenhum peso de modelo é alterado nesse processo. O artefato ajustado é a
configuração, capturada pela `ExperimentSpec`, pelo `spec_hash` e pelo commit
(seção 20).

**Nem todo item desta lista pode ser ajustado em qualquer momento da
calibração, nem com base em qualquer evidência.** A lista acima descreve o
*escopo* do que é ajustável; qual subfase tem autoridade sobre cada parâmetro,
e sob que tipo de justificativa, está na seção 5.12. Em particular,
`long_target_weight` deixou de ser parâmetro de calibração por desempenho
(seções 5.12 e 11).

A calibração estatística de `LLM confidence -> probability` é questão
**separada** e permanece fora do protocolo principal v1, como já registrado na
seção 11.

### 5.3 Unidade básica da calibração

Uma unidade de calibração é uma **data histórica `t`** (âncora), não um período
inteiro.

```text
informação permitida:
  tudo que estaria disponível até close(t)

informação proibida:
  qualquer dado cuja disponibilidade seja posterior a t
```

Fluxo de uma âncora:

```text
historical anchor t
        v
reconstruir o information set disponível em t
        v
sistema multiagente
        v
target_weight decidido em close(t)
        v
execução pela Arena em open(t+1)
        v
revelar o resultado observado
        v
avaliar a decisão
```

Durante a fase de CALIBRATION — e somente nela — os pesquisadores podem observar
esse resultado e ajustar o sistema antes de executar novos casos.

### 5.4 Sequência temporal

O experimento imita a passagem real do tempo:

```text
t0
-> prever t0+1
-> revelar t0+1

t0+1
-> prever t0+2
-> revelar t0+2

t0+2
-> prever t0+3
...
```

O dado observado em `t+1` só pode entrar na informação do sistema quando a
simulação avançar para `t+1`. **Nunca retroativamente.**

### 5.5 Calibration Cases

```text
CALIBRATION CASES = TBD
```

Nenhuma data está escolhida. Fica registrada apenas a restrição metodológica: a
calibração **não** deve ocorrer sobre um único episódio ou um único regime de
mercado. A seleção final deverá representar mais de uma condição de mercado,
entre critérios candidatos como:

- tendência de alta;
- tendência de baixa;
- mercado lateral;
- alta volatilidade;
- baixa volatilidade;
- choques macroeconômicos;
- eventos políticos;
- períodos eleitorais;
- mudanças relevantes em juros;
- regimes específicos de commodities, quando aplicável.

São **critérios candidatos**, não uma seleção congelada. Datas concretas,
episódios e ativo do piloto: `TBD`.

**Quantidade de âncoras — decisão metodológica aprovada.** A quantidade deixou
de ser `TBD`; as datas não.

```text
CORE   = 30 âncoras
       = CAL-A (20)  ∪  CAL-B (10)
       CAL-A ∩ CAL-B = ∅

STRESS <= 8 âncoras ADICIONAIS, declaradas FORA do CORE
```

Consequência explícita, porque a alternativa oposta chegou a ser considerada:

```text
Stress NÃO reduz CAL-A.

alternativa REJEITADA: retirar as âncoras de stress de dentro do CORE,
o que forçaria CAL-A a cair de 20 para 12 e enfraqueceria a única
subfase de seleção quantitativa do protocolo.
```

Papel de cada conjunto, detalhado na seção 5.12: CAL-A seleciona parâmetros de
decisão instantânea; CAL-B é sanity check one-shot em datas nunca vistas; as
âncoras de stress são diagnóstico qualitativo, sem autoridade de seleção.

### 5.6 Researcher overfitting

Vazamento não ocorre apenas quando o modelo vê o futuro. Os próprios
pesquisadores produzem overfitting ao repetir:

```text
roda período
-> observa resultado
-> altera o sistema
-> roda o mesmo período
-> altera novamente
```

até maximizar aquele conjunto. O produto disso é um sistema sintonizado nas datas
observadas, não uma hipótese testada.

Por isso a separação de estágios é obrigatória:

```text
SYSTEM CALIBRATION
        v
FREEZE
        v
PSEUDO-LIVE VALIDATION
        v
FINAL TEST
```

A separação de estágios é condição necessária e **não suficiente**: ela impede
que a avaliação seja ajustada, mas não limita o ajuste dentro da própria
calibração. O que limita esse ajuste — espaço de busca finito, teto de
configurações e rodadas, critério declarado antes, change log e autoridade por
subfase — está na seção 5.12.

### 5.7 Freeze

O freeze só ocorre **depois de CAL-B aprovado** (seção 5.12). Ao encerrar a
calibração deve existir uma configuração **identificável e reproduzível**. O freeze acontece **antes da PSEUDO-LIVE VALIDATION**, não antes
do FINAL TEST: se um elemento material ainda puder mudar quando a validação
começar, a validação não é out-of-sample. Todo item listado abaixo está
congelado a partir daquele ponto.

O freeze abrange, no mínimo, os parâmetros científicos materiais então
existentes:

- prompts;
- papéis dos agentes;
- provider/model;
- configuração do ensemble;
- consensus threshold;
- temperatures;
- risk limits;
- `long_target_weight`;
- `decision_frequency`;
- política de Historical Memory, caso esteja ativa;
- custos;
- métricas;
- universo;
- demais parâmetros materiais da `ExperimentSpec`.

O mecanismo técnico de proveniência já existe e não é objeto de mudança nesta
formalização:

```text
git commit
spec_hash
snapshot_id
manifest
LLM trace
```

Freeze é um ato metodológico registrado sobre esse mecanismo. Possuir o
mecanismo não equivale a ter congelado (seção 21).

**Declaração explícita obrigatória.** Todo parâmetro científico material deve
ser declarado na `ParticipantSpec` no momento do freeze, **mesmo quando o valor
escolhido coincide com o default técnico do código**. A razão é de proveniência,
não de estilo: `build_participant` liga apenas o que a spec declara, e um
parâmetro omitido é resolvido pelo default do construtor — isto é, pelo código,
coberto só pelo `git_commit`. Parâmetro omitido não entra em `spec.params` e,
portanto, não é distinguido pelo `spec_hash`: duas calibrações com escolhas
diferentes poderiam colidir no mesmo hash. Decisão científica não pode depender
silenciosamente de um default.

A regra de reversão continua valendo em toda a fase seguinte: **alteração
decidida depois de observar a VALIDATION devolve aquela janela para
development/calibration** (seção 5.8), e uma janela nova precisa ser reservada.

### 5.8 Pseudo-live Validation

Depois do freeze, a validação usa datas que **não** participaram da calibração.

```text
parâmetros congelados
prompts congelados
regras congeladas
```

A execução continua sessão a sessão:

```text
information set <= t
-> decisão
-> execução em t+1
-> resultado
-> avançar o relógio
```

Nenhuma alteração metodológica pode ser feita com base nos resultados dessa
própria janela. Se for feita, aquela janela deixa de ser validation e volta a ser
development/calibration, e uma nova janela precisa ser reservada.

Datas de validation: `TBD`.

### 5.9 Final Test

```text
FINAL TEST PERIOD = TBD
```

O FINAL TEST deve ser temporal e intencionalmente separado das datas usadas na
calibração e na validação. Depois de congelado o protocolo, ele é tratado como
avaliação final: qualquer mudança posterior motivada pelo que se observou nele é
explicitamente classificada como

```text
post-hoc
```

e não como confirmação da hipótese original (seção 22).

### 5.10 Live / Shadow

Estágio posterior ao experimento histórico, detalhado na seção 24. Ele não
substitui o teste histórico; aproxima o laboratório do objetivo operacional.

### 5.11 Janela avaliada, warm-up e modo de histórico

Cobertura de dados e período avaliado deixaram de ser a mesma coisa. A
`ExperimentSpec` declara a janela; o snapshot continua descrevendo apenas o que
existe:

```text
data_start ...... decision_start ...... decision_end .. settlement_session
|___ warm-up ___|___ decisões avaliadas ____________|__ executa a última __|
```

Sessões anteriores a `decision_start` são **informação, nunca resultado**: não
chamam o participante, não consomem chamada ao provedor, não geram intent nem
trade, não deslocam a grade de `decision_frequency` e não entram na curva
publicada. A carteira em `decision_start` é sempre capital inicial em caixa e
posição zero.

`settlement_session` é a consequência direta de `close(t) -> open(t+1)`: a
decisão tomada em `decision_end` só vira trade na abertura seguinte. Por isso a
sessão posterior a `decision_end` precisa existir, é processada para liquidar e
marcar o resultado, e **não** recebe decisão nova. Uma janela sem settlement é
recusada antes de o participante ser construído — fail-closed antes de qualquer
chamada paga.

#### Modo de histórico: `expanding` no v1

A decisão em `t` enxerga todo o histórico causal disponível até `t`, nunca
informação posterior. Rolling — usar apenas os últimos `N` períodos — **não**
está implementado e fica como ablation futura. Motivos:

1. corresponde ao comportamento causal já existente na arena (`snapshot[:t]`);
2. satisfaz "pelo menos aproximadamente 2 anos" por construção, porque nunca
   descarta histórico;
3. evita introduzir um novo hiperparâmetro de janela (`N`) que precisaria ser
   congelado e justificado, aumentando os graus de liberdade do pesquisador —
   exatamente o risco que o protocolo existe para conter;
4. preserva todo o histórico causal disponível **e o estado de indicadores
   recursivos**. Este ponto é material e não decorativo: o MACD é calculado com
   `ewm(..., adjust=False)`, cuja saída em `t` depende recursivamente de toda a
   série anterior. Truncar o início da janela mudaria o valor do indicador em
   `t`, e não apenas a quantidade de contexto disponível;
5. rolling continua possível depois, como ablation declarada, sem alterar o
   desenho principal.

> Correção de um registro anterior: chegou a ser afirmado que uma janela rolling
> com `N >= 200` produziria os mesmos indicadores da expansiva, por `sma_200`
> ser a maior janela. A afirmação é forte demais e está retirada — ela vale para
> indicadores de janela finita (SMA, Bollinger, RSI), mas **não** para os
> recursivos por EMA, como o MACD.

#### Histórico mínimo antes da primeira decisão

`minimum_history_sessions` é campo **obrigatório e sem default** da
`EvaluationSpec`. Um default técnico viraria decisão científica silenciosa: quem
executa precisa declarar quanto histórico exige.

Definição canônica única, contada sobre o **calendário comum** do run — a
interseção das sessões de todos os tickers, que é o calendário em que a arena
decide e executa:

```text
warmup_sessions            = sessões comuns estritamente ANTERIORES a decision_start
available_history_sessions = sessões comuns até e INCLUINDO decision_start
                           = warmup_sessions + 1

gate: available_history_sessions >= minimum_history_sessions
      available == minimum      -> passa
      available == minimum - 1  -> falha
```

O `+ 1` é a própria barra de `decision_start`, já observável no fechamento em
que a primeira decisão é tomada. Por isso o piso da spec é `1`: a primeira
decisão avaliada sempre observa pelo menos a própria sessão.

`available_history_sessions` **não** é `len(observation.history[ticker])`. O
histórico entregue ao participante é o quadro daquele ticker recortado em `t`, e
um ticker que negocie em data fora do calendário comum chega com mais barras. A
contagem comum é deliberada: é o único número igual para todos os tickers do
run e é limite inferior do histórico que qualquer um deles recebe. Em run
single-asset — todo o caminho `llm_agent` hoje — os dois números coincidem.

**Valor recomendado — decisão metodológica aprovada, pendente de
congelamento formal:**

```text
minimum_history_sessions = 504

504 sessões disponíveis até e incluindo decision_start
  = 503 sessões estritamente anteriores + a própria sessão t
```

Justificativa aprovada, e só ela: são aproximadamente dois anos de pregões da
B3; satisfaz por construção a janela base aprovada na seção 7.2; é `> 2,5 × 200`,
de modo que a maior janela finita em uso (`sma_200`) está bem além da
inicialização e o MACD — recursivo por EMA, `adjust=False` — tem burn-in amplo;
é **gate de maturidade informacional, não truncamento**, porque o histórico
continua expansivo e nada é descartado. Argumentos estatísticos adicionais
(independência de observações mensais, contagem de regimes, erro de estimador)
foram considerados e **retirados** por não serem demonstráveis neste desenho;
se forem desejados, entram apenas com referência de literatura.

O manifest publica as duas medidas realizadas — `warmup_sessions` e
`warmup_calendar_days` — para que a conformidade seja auditável depois, sem
reler o snapshot. A equivalência em dias corridos é evidência publicada, não
requisito.

#### Duas formas de usar a mesma janela

```text
Calibration Anchor      decision_start == decision_end == t
                        uma decisão em close(t), execução em open(t+1)
                        diagnóstico do sistema

Sequential Evaluation   decision_start < decision_end
                        carteira contínua ao longo da janela
                        Validation e Final Test
```

#### Fronteira da curva publicada

```text
primeiro ponto = decision_start      (capital inicial em caixa, posição zero)
último ponto   = settlement_session  (a última decisão já liquidada)
len(curva)     = evaluated_sessions + 1
```

Warm-up não entra. O `+ 1` é a `settlement_session`, e é por isso que o tamanho
da curva **não** é o número de sessões avaliadas nem o número de decisões. O
manifest publica os dois separadamente: `equity_points` conta a curva,
`evaluation_evidence.evaluated_sessions` conta as sessões da janela.

`evaluated_sessions` são as sessões em que o participante foi **consultado** —
não os intents emitidos. Consultado e sem emitir intent é resultado legítimo:
`MANTER`, veto de risco ou sessão fora da grade de `decision_frequency`. Pela
mesma razão, `first_decision_session` e `last_decision_session` na evidência são
os limites da janela — a arena não conhece a grade do participante e não
publicaria um número que não observa. Quais sessões produziram decisão efetiva
se lê na evidência do participante (o trace de LLM) e nos trades publicados.

#### `decision_frequency` no fim da janela

`decision_frequency` continua governando a elegibilidade, contada a partir de
`decision_start` (índice zero, sempre elegível). `decision_end` é **limite da
janela, não obrigação de decidir**: quando ele não cai na grade, o participante
é consultado, não emite intent, e a `settlement_session` liquida o pendente da
última decisão *efetivamente emitida* — ou nada, se não houver pendente. O run
continua válido.

Forçar uma decisão extraordinária em `decision_end` exigiria que o participante
soubesse que aquela é a última sessão avaliada — exatamente o `is_last_day` do
motor legado, que a causalidade da arena retirou de propósito (seção 12).
Ausência legítima de trade não é falha de settlement.

Distinção que o gate preserva:

```text
há próxima sessão comum, mas nenhum intent pendente  -> run válido, sem trade
não existe sessão comum após decision_end            -> recusado antes de
                                                        construir o participante
```

Sharpe, Sortino, CAGR e MaxDD só fazem sentido sobre a forma sequencial. **Uma
âncora única não produz evidência de desempenho de carteira** e não deve ser
lida como tal; agregação entre múltiplos Calibration Cases não existe e não foi
decidida.

Um snapshot amplo serve várias janelas: Calibration Cases, Validation e Final
Test compartilham o mesmo `snapshot_id` e o mesmo `identity_digest`, e diferem
no `spec_hash` porque a janela difere. Não se cria snapshot por caso.

#### Fase e `case_id`

`phase` (`CALIBRATION`, `VALIDATION`, `FINAL_TEST`, `LIVE_SHADOW`) é
**obrigatória** para todo run que declara janela, e é declarada na construção do
runner — antes de executar, antes de qualquer chamada ao provedor. Não existe
caminho que anexe a fase durante a publicação do run.

Como `phase` distingue apenas os quatro estágios, **a subfase da calibração
(seção 5.12) é registrada no `case_id`**, que é rótulo humano curto e existe
justamente para isso. Nenhum campo novo é criado para representar subfase:

```text
phase   = CALIBRATION
case_id = "hardening-v3" · "cal-a-cfg2-anchor07" · "seqdev-w1-cfg3"
          "stress-report-03" · "cal-b-final"
```

`phase` e `case_id` **não entram no `spec_hash`**, porque não alteram nada do
que é computado: dois runs que só diferem na fase produzem exatamente os mesmos
números, e separá-los no hash quebraria o significado de "mesma configuração,
mesmo resultado". O controle contra reclassificação é a declaração prévia, não o
hash. Diretório nunca é identidade metodológica.


### 5.12 Governança da CALIBRATION

**STATUS: metodologia aprovada. Datas, valores e critérios continuam `TBD`.**

A CALIBRATION não é uma fase única. Ela tem cinco subfases, com autoridades
distintas e **não cumulativas**: um parâmetro ajustado numa subfase não volta a
ser ajustado em outra.

#### Subfases e ordem

```text
CALIBRATION WINDOW
│
├── DIAGNOSTIC HARDENING
│      defeitos de contrato, epistêmicos e de coerência
│      outcome-blind · versionado · sem métrica financeira
│      -> produz o baseline estável B0
│
├── CAL-A                         20 âncoras
│      Performance Calibration de decisão instantânea
│      espaço finito pré-registrado
│
├── SEQUENTIAL DEVELOPMENT        janela curta, datas TBD
│      parâmetros dependentes de trajetória
│      development contaminado, rotulado
│
├── STRESS REPORT                 <= 8 âncoras adicionais, fora do CORE
│      diagnóstico qualitativo de robustez, autoridade zero
│
└── CAL-B                         10 âncoras nunca vistas
       sanity check one-shot, outcome-blind
            v
         FREEZE
```

A ordem é fixa. As mesmas âncoras de stress podem ser executadas **duas vezes**,
em funções distintas:

```text
STRESS PROBING    durante o DIAGNOSTIC HARDENING
                  instrumento de descoberta de defeito, o mais cedo possível

STRESS REPORT     depois do SEQUENTIAL DEVELOPMENT, antes do CAL-B
                  regressão qualitativa / relatório de robustez da
                  configuração candidata final
```

Reutilizar as mesmas datas nas duas funções é legítimo **porque elas pertencem
integralmente a development**. Nenhuma das duas passagens é holdout, nenhuma é
out-of-sample e nenhuma produz evidência de generalização.

#### Duas classes de mudança

```text
DIAGNOSTIC    a justificativa permanece válida com o resultado financeiro
              de t+1 apagado
              -> corrige defeito

PERFORMANCE   a justificativa depende do comportamento observado nos
              resultados das âncoras
              -> seleciona configuração
```

A classe não é determinada pelo parâmetro tocado, e sim pelo que aparece na
justificativa. A mesma mudança em `consensus_threshold` pode ser Diagnostic
("o quorum aprovava com poucos votos válidos por causa de falhas silenciosas")
ou Performance ("o limiar mais alto rendeu mais"). O change log precisa dizer
qual, por versão.

#### Diagnostic Hardening

Objetivo: corrigir defeitos de processo e integridade. **Não otimiza desempenho
financeiro** e não usa métrica financeira.

Taxonomia mínima, obrigatória no change log:

```text
CLASSE A — contrato / operação
   schema inválido, run abortado, quorum incompletado por falha,
   violação de contrato da arena, erro de execução

CLASSE B — epistêmico / leakage
   hallucination, dado inventado, uso de informação fora do information
   set, referência a evento posterior a t

CLASSE C — coerência interna
   reasoning contradiz a ação emitida
   risk verdict contraria a própria regra declarada
   confidence incoerente com a dispersão observada do quorum
```

**Por que esta subfase não é ilimitada.** Outcome-blindness fecha um canal de
contaminação — o resultado financeiro — e deixa outro aberto: os próprios
contextos conhecidos. Iterar prompts, papéis e regras contra as mesmas âncoras
ajusta o sistema àquelas situações mesmo sem ninguém olhar um retorno, porque o
pesquisador já sabe de memória o que aconteceu naquelas datas e porque o texto
do prompt pode absorver o contexto sem citar o resultado.

**Regra de generalidade**, que é o controle verificável desta subfase:

```text
toda alteração de prompt ou de regra deve ser expressa em termos GERAIS

PROIBIDO no texto:
   uma data                   uma faixa de preço
   um ativo específico        um evento nomeado
   um contexto que simplesmente descreva as âncoras observadas
```

Ela é auditável lendo o diff do prompt, o que nenhum teto numérico consegue ser.

**Condição de saída**, declarada antes de começar:

```text
uma passada completa sobre as âncoras de development, com:
   zero defeitos CLASSE A
   zero defeitos CLASSE B
   defeitos CLASSE C apenas do tipo residual declarado previamente
+
duas versões consecutivas sem nova CLASSE de defeito
        v
baseline estável B0
```

**Limite procedimental**, e o que ele *não* é:

```text
H = 10 versões de hardening  ->  LIMIAR DE ESCALONAMENTO
```

Não é proibição de corrigir bug real. Recusar-se a corrigir um defeito para
respeitar um contador seria falha metodológica pior do que a que o contador
tenta evitar. Ultrapassar `H` significa que o sistema não está pronto para ser
congelado, e a decisão de continuar sobe para dupla e orientador com o change
log. O número de versões de hardening é reportado.

O hardening roda sobre as âncoras de CAL-A e sobre o Stress Probing. **Nunca
sobre CAL-B.**

#### Baseline B0 e classe de comparabilidade

O Diagnostic Hardening produz um baseline identificável:

```text
B0 = git_commit
   + ExperimentSpec / spec_hash aplicável
   + prompts (texto e hashes registrados no trace)
   + configuração material declarada
```

Performance Calibration só pode comparar configurações pertencentes à **mesma
classe de comparabilidade**, isto é, ao mesmo baseline. Se durante a Performance
Calibration surgir correção comportamental de classe A ou B:

```text
corrigir o defeito (obrigatório; nunca adiar correção para preservar contagem)
        v
as comparações feitas sobre o baseline anterior ficam INVALIDADAS
        v
nova calibration_version, com novo baseline
        v
a seleção afetada é executada novamente, de forma declarada
        v
as comparações invalidadas permanecem REGISTRADAS, nunca apagadas
```

Teste operacional, quando aplicável, usando o mecanismo que já existe
(seção 15):

```text
replay dos traces existentes contra a versão corrigida
   replay idêntico     -> alteração não-comportamental
                          a classe de comparabilidade sobrevive
   ReplayMismatchError -> comportamento ou contrato mudou
                          nova classe de comparabilidade
```

Limite explícito deste teste: **replay não substitui nova execução contra o
modelo quando o próprio prompt foi alterado.** Prompt alterado é, por
construção, `ReplayMismatchError` — o replay diagnostica a quebra, não fornece
os resultados da nova configuração.

#### CAL-A

```text
CAL-A = 20 âncoras
```

Papel: **Performance Calibration da lógica instantânea de decisão**. Somente
parâmetros cujo efeito seja identificável numa decisão isolada podem ser
selecionados aqui.

Candidatos anchor-calibratable — a lista do protocolo v1 conforme a arquitetura
atual, não uma lista eterna:

```text
prompt variant (dentro do conjunto declarado)
analyst_count
consensus_threshold
temperature_min / temperature_max
risk_max_volatility
volatility_window
```

Procedimento:

```text
espaço finito PRÉ-REGISTRADO, enumerado como lista de specs
N <= 8 configurações no total
R <= 3 rodadas
as 20 âncoras sempre avaliadas integralmente
um único critério agregado
critério declarado ANTES de observar qualquer resultado
desempate declarado antes
nenhuma mudança justificada por âncora individual
nenhum uso de CAL-B, VALIDATION ou FINAL TEST
N e R realizados são reportados
```

O escore agregado de CAL-A é **evidência de desenvolvimento** e nunca é
reportado como resultado científico.

**Critério agregado: `TBD`.** O espaço está restrito, o valor não está escolhido.
Ele precisa satisfazer:

```text
válido sobre 20 âncoras de um dia
alinhado ao trading target (seção 17)
NÃO Sharpe · NÃO Sortino · NÃO CAGR · NÃO MaxDD
NÃO acurácia direcional close-to-close
uma única quantidade agregada
declarado antes dos resultados
```

Candidatos registrados como **discussão, não decisão**:

```text
C1  P&L líquido agregado ou médio das 20 âncoras, com exposição fixa
C2  retorno intradiário capturado por decisão acionável, com abstenções
    reportadas à parte
C3  proporção de âncoras com contribuição líquida positiva
C4  média aparada (trimmed mean) do P&L por âncora, com corte declarado antes
```

`C1` e `C4` só são comparáveis entre configurações porque `long_target_weight`
está fixo (seção 11); se a exposição variasse, nenhum deles seria válido.

#### Parâmetros não identificáveis numa âncora

Uma Calibration Anchor é `decision_start == decision_end == t`, e o run começa
sempre com o capital inicial em caixa, posição zero e contadores zerados
(seção 5.11). Isso produz **impossibilidade estrutural**, não preferência
metodológica:

```text
risk_max_drawdown
   o pico de patrimônio nasce na própria sessão da decisão
   -> current_drawdown = 0 -> o limite nunca é alcançado

risk_max_concentration
   não há posição no instante da decisão
   -> current_concentration = 0 -> o limite nunca liga

decision_frequency
   session_index = 0 na primeira decisão
   -> toda frequência é elegível -> todas produzem a mesma decisão
```

Logo, os três **não podem ser selecionados em CAL-A**. Selecioná-los ali não
seria overfitting: seria escolher com base em evidência de variação nula, com o
desempate virando arbítrio disfarçado de resultado. Eles pertencem ao Sequential
Development.

#### Sequential Development

Subfase formal da CALIBRATION. Natureza:

```text
development contaminado
janela sequencial curta, dentro da área de calendário da CALIBRATION
NÃO é Validation · NÃO é holdout · NÃO é evidência out-of-sample
```

Toda data dentro dessa janela fica queimada para fins out-of-sample,
permanentemente.

Seleciona os parâmetros dependentes de trajetória:

```text
decision_frequency
risk_max_drawdown
risk_max_concentration
```

E verifica, sem selecionar:

```text
turnover
custos acumulados
persistência de posição entre sessões
trajetória de caixa e de patrimônio
efeito de gaps sobre posição já existente
comportamento de VENDA sobre posição existente
```

Esse último item é material: o participante é long-only e `VENDA` significa
peso alvo zero. Sobre carteira zerada isso não gera trade nenhum; a decisão de
venda só é acionável quando há posição, estado que **não existe** numa âncora.

**É a primeira subfase em que Sharpe, Sortino, CAGR, MaxDD, turnover e custos
sequer são definidos**, porque é a primeira com curva de patrimônio. E é
exatamente onde a tentação aparece:

```text
esses números são DEVELOPMENT EVIDENCE
nunca são resultado científico
nunca são agregados aos resultados de VALIDATION ou FINAL TEST
```

Contenção — proposta, ainda sujeita a aprovação final:

```text
uma única janela curta      datas TBD · duração TBD
N_seq <= 4 configurações
R_seq <= 2 rodadas
critério de seleção TBD, declarado ANTES de executar a subfase
```

O Sequential Development **não reabre parâmetro já selecionado em CAL-A**. Se
revelar incompatibilidade real com uma escolha de CAL-A:

```text
amendment declarado de protocolo/calibração
        v
nova calibration_version
        v
repetir a seleção afetada
```

Nunca retuning silencioso.

#### Stress Cases

```text
STRESS <= 8 âncoras ADICIONAIS, fora do CORE
CAL-A permanece 20 · CAL-B permanece 10 · CORE permanece 30
```

Autoridade:

```text
PODE   revelar defeito durante o Diagnostic Hardening (Stress Probing)
PODE   descrever qualitativamente a robustez da configuração final
       (Stress Report)

NÃO PODE   entrar em critério agregado
NÃO PODE   melhorar score de configuração alguma
NÃO PODE   selecionar configuração
NÃO PODE   servir como evidência out-of-sample
```

Datas, episódios e condições concretas: `TBD`. Candidatos de condição extrema —
gap severo, circuit breaker, choque macro, suspensão de negociação, anomalia de
dado, virada abrupta de regime — são critérios candidatos, não seleção.

#### CAL-B — one-shot

```text
CAL-B = 10 âncoras
```

Nunca utilizadas em Diagnostic Hardening, CAL-A, Sequential Development ou
Stress — **nem como âncora, nem contidas dentro da janela sequencial**.

Papel:

```text
one-shot out-of-sample SANITY CHECK
NÃO é performance test
```

Critérios de aprovação, integralmente outcome-blind:

```text
run completa, sem falha de infraestrutura
information set respeitado (nada posterior a t no reasoning)
sem hallucination material
reasoning e ação coerentes
regras duras respeitadas
quorum e contratos de schema íntegros
sem comportamento degenerado
```

Não usar como barra de aprovação:

```text
retorno mínimo · accuracy mínima · P&L mínimo
```

A razão é dimensional antes de ser metodológica: 10 âncoras de um dia não
sustentam afirmação de desempenho, nem para aprovar nem para reprovar. E a
consequência precisa estar escrita, não subentendida:

```text
CAL-B aprovado significa: a configuração congelada se comporta de forma
   íntegra e não degenerada em datas que ninguém usou para ajustá-la.

CAL-B aprovado NÃO significa: desempenho out-of-sample.

desempenho out-of-sample começa na PSEUDO-LIVE VALIDATION.
```

**Consumo do holdout.** A fronteira é anterior à natureza do que foi observado:

```text
run abortou ANTES de produzir decisão, trace e reasoning utilizáveis
   (provedor indisponível, LLMDecisionError por infraestrutura,
    snapshot indisponível)
        -> pode repetir, segundo política declarada ANTES
        -> o holdout ainda não foi observado cientificamente

run produziu decisão, trace e reasoning utilizáveis
        -> CAL-B CONSUMIDO, definitivamente, para esta versão
```

A natureza do que se observou **não importa**. Se dentro do CAL-B aparecer
hallucination, reasoning incoerente ou risk verdict errado, a janela foi aberta
do mesmo jeito. Corrigir o sistema com base nisso é legítimo — o que não é
legítimo é continuar chamando as mesmas 10 âncoras de holdout:

```text
observou comportamento no CAL-B
        v
corrigiu o sistema por causa disso
        v
aquela versão da calibração NÃO PASSOU
aquelas 10 âncoras são development a partir de agora
        v
nova tentativa exige nova versão metodológica e novo pré-registro
```

Nunca: corrigir e seguir tratando as mesmas âncoras como holdout.

#### Matriz de autoridade sobre parâmetros

```text
ALTERAR   a subfase tem autoridade para selecionar ou mudar o valor
AVALIAR   pode medir e reportar evidência, mas não pode mudar
OBSERVA   o valor é registrado; avaliá-lo naquela subfase não é significativo
N/A       o parâmetro não tem efeito observável naquela subfase
```

| Parâmetro / decisão | Diagnostic Hardening | CAL-A | Sequential Dev | Stress | CAL-B |
|---|:--:|:--:|:--:|:--:|:--:|
| prompt variants | ALTERAR (só por defeito) | ALTERAR (seleção declarada) | AVALIAR | OBSERVA | OBSERVA |
| `analyst_count` | AVALIAR | ALTERAR | AVALIAR | OBSERVA | OBSERVA |
| `consensus_threshold` | AVALIAR | ALTERAR | AVALIAR | OBSERVA | OBSERVA |
| `temperature_min` / `temperature_max` | AVALIAR | ALTERAR | AVALIAR | OBSERVA | OBSERVA |
| `volatility_window` | AVALIAR | ALTERAR | AVALIAR | OBSERVA | OBSERVA |
| `risk_max_volatility` | AVALIAR | ALTERAR | AVALIAR | OBSERVA | OBSERVA |
| `risk_max_drawdown` | AVALIAR | **N/A** | ALTERAR | OBSERVA | OBSERVA |
| `risk_max_concentration` | AVALIAR | **N/A** | ALTERAR | OBSERVA | OBSERVA |
| `decision_frequency` | AVALIAR | **N/A** | ALTERAR | OBSERVA | OBSERVA |
| `long_target_weight` | AVALIAR | AVALIAR | AVALIAR | OBSERVA | OBSERVA |
| `require_all_votes` | ALTERAR (regra dura) | AVALIAR | AVALIAR | OBSERVA | OBSERVA |
| `retry_attempts` / `retry_base_delay` | ALTERAR (operacional) | OBSERVA | OBSERVA | OBSERVA | OBSERVA |
| `seed_base` | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** |
| `provider` / `model` | AVALIAR | OBSERVA | OBSERVA | OBSERVA | OBSERVA |
| capital, custos, universo, janela | OBSERVA | OBSERVA | OBSERVA | OBSERVA | OBSERVA |

Invariante:

```text
cada parâmetro tem NO MÁXIMO UMA subfase com autoridade de ALTERAR
```

Uma exceção, deliberada e nomeada: **prompt variants** aparece com `ALTERAR` em
duas subfases. A fronteira não é o parâmetro, é a natureza do ato — no
Diagnostic Hardening a alteração é dirigida por defeito, outcome-blind e em
termos gerais; em CAL-A é **seleção entre variantes já declaradas**, sem edição
nova. Editar prompt durante CAL-A é hardening fora de hora e dispara a regra da
classe de comparabilidade.

`seed_base` é `N/A` em todas as subfases porque a `seed` é solicitada e
registrada no trace, mas **não é transmitida ao provedor** (seção 15): alterá-la
muda o `spec_hash` sem poder mudar resposta alguma do modelo. Mantê-la na matriz
é o que impede que alguém "calibre a seed" no futuro acreditando estar fazendo
algo.

#### Orçamento de chamadas

Duas contagens distintas, que não devem ser confundidas:

```text
CHAMADAS LÓGICAS         o que o grafo pede
   por decisão elegível:  N ... N+2        (N = analyst_count)
   nominal, derivado do grafo, NUNCA garantia

TENTATIVAS AO PROVEDOR   o que a rede vê
   <= retry_attempts x chamadas lógicas
   retry apenas em falha transitória de transporte
```

A faixa `N ... N+2` decorre do grafo: o veredito de risco resolve
deterministicamente vários caminhos antes de qualquer chamada, e o Portfolio
Manager não é executado quando o veredito não é `APROVADO` nem quando o sinal é
`MANTER`. **`N+2` é o teto de um ramo específico, não a média**, e um run que
aborta consome chamadas sem produzir resultado científico utilizável.

Por isso o custo é **medido, não previsto**: o trace publica `attempt_count` por
chamada lógica, de modo que `chamadas lógicas` é o número de registros e
`tentativas` é a soma dos `attempt_count`. O relato de custo do TCC usa o
realizado.

Orçamento monetário: `TBD`. Não é congelado aqui. Registrado apenas o que
domina a conta: o custo é linear em `analyst_count` e em `decision_frequency`, e
as janelas sequenciais — Sequential Development e VALIDATION — custam por sessão
elegível, não por âncora, e por isso dominam o total.

#### Disjunção obrigatória

Invariantes verificáveis, que substituem qualquer embargo temporal (seção 25):

```text
CORE = CAL-A ∪ CAL-B
CAL-A ∩ CAL-B = ∅

STRESS ∩ CAL-B = ∅
CAL-B ∩ SequentialDevelopmentWindow = ∅

DevelopmentWindow ∩ VALIDATION = ∅
DevelopmentWindow ∩ FINAL TEST  = ∅
VALIDATION ∩ FINAL TEST = ∅

toda a CALIBRATION ocorre temporalmente antes da VALIDATION
a VALIDATION ocorre antes do FINAL TEST
```

`DevelopmentWindow` inclui Diagnostic Hardening, CAL-A, Sequential Development e
Stress. **Stress pertence a development.**

A armadilha concreta a verificar ao escolher as datas: a janela de Sequential
Development é um *intervalo*, não um conjunto de datas isoladas. Se ela contiver
uma âncora de CAL-B, o holdout deixou de existir sem que ninguém tenha tomado
essa decisão.

## 6. Walk-Forward

- Tipo de janela: `TBD`.
- Tamanho da janela de estimação, para participantes que estimam parâmetros:
  `TBD`.
- Tamanho da janela de avaliação: `TBD`.
- Passo entre janelas: `TBD`.
- Política de reestimação: `TBD`.

O Walk-Forward é **análise de robustez**, não o desenho principal, e não
introduz treinamento do LLM. Para os participantes clássicos que estimam
parâmetros a partir de histórico — Mínima Variância é o caso concreto hoje —
ele descreve a janela de estimação usada em cada ponto. Para o participante LLM
ele descreve apenas subperíodos de avaliação sob o mesmo protocolo causal da
seção 5. Em nenhum dos dois casos uma janela pode usar dado posterior à data da
decisão.

## 7. Information available at t

Direção proposta: cada participante recebe somente dados confirmados e features
calculáveis até o fechamento da sessão `t`. A lista definitiva de campos, regras
de warm-up, defasagens de publicação e tratamento de ausências é `TBD`.

Nenhuma feature poderá incorporar a abertura ou qualquer dado de `t+1`.

### 7.1 Information set

O critério é **disponibilidade**, não existência do dado no arquivo histórico:

```text
permitido   -> tudo que estaria disponível até close(t)
proibido    -> qualquer informação cuja disponibilidade seja posterior a t
```

Isso vale para preços, features derivadas e — quando existir — qualquer documento
recuperado pela Historical Memory (seções 23 e 25).

### 7.2 Base Market Window >= 2 anos

**Decisão metodológica aprovada nesta versão do documento:**

```text
Base Market Window >= 2 anos
```

Para cada decisão em `t`, o sistema deve ter acesso a pelo menos
aproximadamente dois anos de histórico de mercado causalmente disponível até
`t`. É o contexto base mínimo da decisão.

Parametrização, agora resolvida (seção 5.11), ainda pendente do ato formal de
congelamento:

```text
gate contado em SESSÕES do calendário comum        DECIDIDO
minimum_history_sessions = 504                     DECIDIDO
504 = 503 sessões anteriores + a sessão de decisão DECIDIDO
mínimo, nunca máximo (history mode = expanding)    DECIDIDO
sessões faltantes                                  resolvido pela definição
                                                   canônica do calendário
                                                   comum (seção 5.11)
equivalência em dias corridos                      não é requisito; publicada
                                                   como evidência
```

A decisão conceitual permanece a mesma — o sistema deve trabalhar com uma janela
recente de pelo menos dois anos para formar o contexto base da decisão — e 504
sessões é a sua parametrização aprovada.

**Estado técnico verificado, que não congela nada acima.** A arena entrega ao
participante o recorte `history` do início do snapshot até `session`, isto é,
uma janela **expansiva**.

> Correção de um registro anterior desta seção. Chegou a ser afirmado aqui que
> "não existe, no código atual, parâmetro de janela mínima nem gate que recuse
> decidir antes disso". A afirmação está **obsoleta e retirada**:
> `minimum_history_sessions` é campo obrigatório e sem default da
> `EvaluationSpec`, e o gate recusa a janela antes de construir o participante
> e antes de qualquer chamada paga. A definição canônica da contagem está na
> seção 5.11; o que continua sendo decisão da dupla é o **valor**, hoje
> recomendado em 504 e ainda não congelado.

### 7.3 Informação disponível não é prompt bruto

Dizer

```text
o sistema tem acesso a >= 2 anos
```

não significa

```text
colocar dois anos de candles integralmente no prompt do LLM
```

A infraestrutura pode transformar esses dados em indicadores, estatísticas,
resumos, features ou estruturas consultáveis. A política exata de context
engineering — o que entra no prompt, em que forma, com que agregação e com que
orçamento de tokens — é `TBD`.

Este documento não descreve implementação de context engineering porque ela não
existe: o `LLMParticipant` monta hoje o `AgentState` com o preço de `close(t)` e
os oito indicadores recalculados sobre o histórico truncado, e é isso que chega
ao prompt.

## 8. Execution at t+1

Direção proposta: ordens decididas após o fechamento de `t` tornam-se elegíveis
na abertura da próxima sessão válida `t+1`.

- Tipo de ordem canônica: `TBD`.
- Formação do preço de execução: `TBD`.
- Lotes, arredondamento e liquidez: `TBD`.
- Slippage e spread: `TBD`.
- Falta de barra, suspensão e execução parcial: `TBD`.
- Política de short: `TBD`.

As mesmas regras serão aplicadas a todos os participantes.

Consequência direta deste contrato sobre o **alvo** da decisão, formalizada na
seção 17.1: uma entrada nova decidida em `close(t)` e executada em `open(t+1)`
não recebe o movimento overnight. O trecho que ela efetivamente captura é
`open(t+1) -> close(t+1)`. Por isso `close(t) -> close(t+1)` não é o alvo do
experimento, ainda que seja o alvo natural de uma tarefa de previsão de preço —
que o v1 não possui.

Consequência da semântica de peso alvo, registrada explicitamente: no agente,
`COMPRA` passa a significar **desejar exposição long no peso alvo configurado**,
e não que o trade físico em `open(t+1)` será `BUY`.

```text
target = 25%

close(t): exposição = 20%   -> provavelmente BUY
gap overnight leva a 30%    -> ExecutionEngine pode SELL para voltar a 25%
```

Isso é correto e é a consequência pretendida: a direção financeira concreta
continua sendo responsabilidade da arena, e o participante não declara `side`.

Implementação técnica preliminar, sem congelar as escolhas acima:
`OrderIntent` registra ticker, peso alvo long-only e instante da decisão —
direção não é declarada pelo participante. Nem a direção nem a elegibilidade de
execução pertencem a ele: o `ExecutionEngine` é quem determina se existe próxima
abertura observada, deriva compra ou venda do delta entre posição e quantidade
alvo naquela abertura, e executa com quantidade inteira e o `CostModel`
existente. Os cinco
benchmarks clássicos já usam esse caminho, single e multi-ativo.

Para carteiras, a implementação atual usa a interseção dos calendários como
calendário comum, executa vendas antes de compras e, quando o caixa não cobre
todos os alvos, escalona as compras pelo mesmo fator antes de truncar para
quantidade inteira. Isso é um mecanismo técnico determinístico, escolhido para
remover dependência da ordem dos tickers — não uma política científica de
rateio. Lote B3, slippage, spread científico, liquidez, execução parcial,
margem, política de suspensão/falta de barra, destino do caixa residual e
política definitiva de short continuam `TBD`.

## 9. Capital

- Capital inicial: `TBD`.
- Moeda-base: `TBD`.
- Aportes e retiradas: `TBD`.
- Remuneração de caixa: `TBD`.
- Alavancagem e limites de exposição: `TBD`.

Caixa negativo será proibido, salvo decisão explícita e congelada em sentido
contrário.

## 10. Transaction costs

- Corretagem: `TBD`.
- Emolumentos e taxas: `TBD`.
- Spread: `TBD`.
- Slippage: `TBD`.
- Tributos: `TBD`.
- Fonte e data de vigência dos valores: `TBD`.

**STATUS: PENDENTE DE CONGELAMENTO.** Custos serão calculados sobre o valor
financeiro total e aplicados igualmente a todos os participantes.

## 11. Position sizing

- Universo entregue ao participante: derivado tecnicamente da spec —
  single-asset recebe o `ticker` declarado, carteira recebe todos os tickers do
  snapshot, e o universo efetivo é registrado no manifest. Critério científico
  de composição do universo permanece `TBD` (seção 3).
- Limite por ativo: `TBD`.
- Limite de exposição total: `TBD`.
- Rebalanceamento e frequência: `TBD`.
- Política de caixa residual e lote: `TBD`.
- Política definitiva de Kelly: `TBD`.
- Thresholds determinísticos de risco: `TBD`.
- Valor definitivo de `long_target_weight`: `TBD`.

### Decisão metodológica APROVADA

Duas decisões desta seção deixaram de ser proposta e passaram a ser decisão
aprovada da estratégia LLM. Elas não congelam nenhum valor numérico.

```text
1. confiança textual do LLM NÃO é probabilidade financeira
   -> não será usada como P(win) em fórmula de sizing sem calibração empírica

2. o sizing principal do experimento v1 será DETERMINÍSTICO
   -> o LLM decide direção; a exposição é definida por política externa a ele
```

Consequência operacional adotada para o `llm_agent` da arena:

```text
Technical Analyst   -> COMPRA / VENDA / MANTER
Risk Manager        -> APROVADO / VETADO
Portfolio Manager   -> decisão QUALITATIVA (schema sem campo de tamanho)
Sizing determinístico:
    COMPRA aprovada -> target_weight = long_target_weight
    VENDA  aprovada -> target_weight = 0.0
    MANTER / VETO   -> nenhuma intenção
```

O gestor de portfólio não tem autoridade para escolher a quantidade financeira:
o schema `PortfolioAction` não possui campo de tamanho, de modo que não existe
número a ignorar depois. `confidence` continua sendo produzida, registrada no
trace e enviada aos agentes seguintes como contexto qualitativo — se ela deve
ou não influenciar *qualitativamente* a decisão é uma ablation futura, não
objeto desta decisão.

### `long_target_weight` não é parâmetro de calibração por desempenho

Decisão metodológica aprovada, complementar às duas acima:

```text
long_target_weight = DECISÃO DECLARADA de política de exposição
                     NÃO é parâmetro de Performance Calibration
                     NÃO é otimizado por CAL-A
```

Motivo estrutural, e não apenas de preferência. Sob sizing determinístico e
âncoras que começam com a carteira zerada, a exposição entra como multiplicador
escalar do resultado de cada âncora:

```text
P&L da âncora  ≈  w × retorno capturado  −  custos
```

Otimizar `w` por P&L agregado é, portanto, monótono em `w`: o procedimento
devolve o maior valor permitido quando o agregado é positivo e tende a zero
quando é negativo. Não é seleção, é solução de canto determinada pelo sinal do
agregado. Além disso, misturaria duas coisas distintas — **qualidade da
decisão** e **quantidade de exposição assumida** —, de modo que a configuração
mais agressiva venceria a mais acertada. Há ainda o acoplamento duro já
validado no código, `long_target_weight <= risk_max_concentration`, que faria a
calibração de `w` empurrar contra um limite de risco pertencente a outra
subfase (seção 5.12).

Análise de sensibilidade em `w` continua permitida como análise de
development, ou como análise secundária **pré-declarada**, nunca como seleção
disfarçada.

### O que continua NÃO congelado

```text
long_target_weight  = TBD
```

O default técnico em código é `0.25`, herdado do antigo teto
`max_position_size` apenas para manter API e testes convenientes. **Isso não é
aprovação metodológica.** O valor científico será escolhido junto com os demais
itens do congelamento (seção 21).

Também continuam `TBD`: calibração empírica de `confidence`, adoção de
long/short (o participante atual é long-only por construção) e qualquer
política alternativa de sizing (`volatility_target`, `calibrated_kelly`).

### Kelly não foi removido do projeto

`calculate_kelly_size` continua implementada e continua ativa no modo
`legacy_confidence_kelly`, que serve os caminhos operacionais legados
(`AgentBacktestEngine`, `DailyAgentRunner`) e permanece o default de
`PortfolioConfig` para que esses runners não troquem de política em silêncio.
Ela segue disponível para ablation, comparação metodológica e uma versão
calibrada futura.

```text
legacy / experimental alternative   != main scientific sizing v1
```

O `LLMParticipant` força `sizing_mode="qualitative"` e não expõe parâmetro
algum de Kelly. Os parâmetros que deixaram de ser materiais no caminho
científico — `kelly_fraction`, `max_position_size`,
`portfolio_max_concentration`, `payoff_ratio` — foram retirados da
`ParticipantSpec` do `llm_agent`, para que duas configurações de comportamento
idêntico não produzam `spec_hash` diferente por causa de um parâmetro morto.

### Registro, não congelamento

`long_target_weight` é configuração material: é validado
(`0 < w <= 1` e `w <= risk_max_concentration`, porque um alvo acima do limite
duro mandaria construir exatamente a exposição que o gestor de risco existe
para vetar), entra no `spec_hash` e aparece no manifest. Registrar não é
congelar.

## 12. Benchmarks

Candidatos atuais:

- Buy and Hold;
- SMA Cross;
- Bollinger Bands;
- Equal Weight;
- Mínima Variância;
- benchmark de mercado: `TBD`.

Parâmetros e frequência de cada benchmark: `TBD`. Todos serão congelados no
FREEZE, **antes da PSEUDO-LIVE VALIDATION**, e executados pelo contrato comum.

## 13. Multi-agent variants

Pendência arquitetural anterior, agora resolvida no nível do contrato: um
participante LLM multi-ativo precisa de semântica explícita para tickers
omitidos numa decisão. A regra adotada é **target portfolio completo**.

```text
uma decisão de carteira declara um peso para CADA ativo do universo observado

ticker omitido   -> DECISÃO INVÁLIDA
ticker extra     -> DECISÃO INVÁLIDA
ticker duplicado -> DECISÃO INVÁLIDA
peso NaN/Inf     -> DECISÃO INVÁLIDA
peso < 0 ou > 1  -> DECISÃO INVÁLIDA
soma > 1 + tol   -> DECISÃO INVÁLIDA

cash_weight = 1 - Σ target_weights
```

Ticker omitido não significa manter posição, não significa peso zero e não
autoriza o executor a inferir nada. Isso vale para uma *decisão de carteira*;
não confundir com a ausência de decisão do participante single-asset migrado,
cujo `MANTER` devolve nenhuma intenção — que é como o motor legado não emitia
ordem — e não uma carteira parcial. Peso zero é decisão explícita e precisa ser
escrita. Nada é normalizado silenciosamente. A regra está implementada e
testada em `target_portfolio_to_intents`
(`src/agents/participant.py`).

Isso não altera os cinco clássicos: o `ExecutionEngine` continua tratando
ticker sem intenção como "manter posição", que é a semântica correta para eles.
A ausência de qualquer intenção também continua significando "nenhuma decisão
nova" — coisa distinta de uma decisão de carteira parcial, que é inválida.

**Capacidade técnica atual (não é congelamento).** O participante LLM já
executa pelo mesmo `ExperimentSpec` -> `ExperimentRunner` -> `ExecutionEngine`
-> `RunResult` -> manifest dos clássicos, sob o `kind` `llm_agent`, na versão
**single-asset**. A stack de agentes é single-asset por construção e não possui
etapa de alocação entre ativos; o participante recusa universo com mais de um
ativo em vez de fabricar um laço por ticker. A variante multi-ativo continua
`TBD`.

Variantes candidatas:

- agente técnico único;
- ensemble técnico;
- ensemble + risk manager;
- sistema completo;
- comparação local vs cloud;
- opcionalmente, roteamento híbrido local/cloud.

Número de analistas, quorum, regra para votos inválidos, papéis e thresholds:
`TBD`. A configuração atual de 30 analistas e 25/30 é baseline técnica, não
parâmetro científico automaticamente congelado. Ela é configurável na
`ParticipantSpec` (`analyst_count`, `consensus_threshold`,
`require_all_votes`, `temperature_min`, `temperature_max`, `seed_base`) e entra
no `spec_hash` e no manifest — registrar não é congelar.

Frequência de decisão: `TBD`. `decision_frequency` é configuração material do
participante e entra no `spec_hash` e no manifest, mas registrar não é
congelar. Os dois defaults herdados do código legado são diferentes e ficam
declarados:

```text
AgentBacktestEngine (classe/API) default = 1   <- adotado pelo LLMParticipant
scripts/run_agent_backtest.py       default = 5   <- escolha operacional de demo
```

Nenhum dos dois foi aprovado como parâmetro científico. `decision_frequency` é
item do freeze (seção 5.7): a frequência definitiva deve ser decidida junto com
as janelas experimentais e o orçamento de chamadas e congelada **antes da
PSEUDO-LIVE VALIDATION**, não apenas antes do FINAL TEST.

Descrição correta do primeiro estágio: **ensemble/quorum de múltiplas amostras
do mesmo papel, do mesmo prompt e do mesmo modelo**, variando temperatura e
seed registrado. Não são 30 especialistas independentes; papéis e modelos
distintos não estão implementados.

Distinção adotada entre falha e decisão, no caminho da arena:

```text
timeout / erro de provedor / JSON inválido /
schema inválido / quorum incompletado por falha
        -> LLMDecisionError -> run falha

quorum sem supermaioria, com todos os votos válidos
        -> MANTER (regra de agregação da metodologia atual)
```

Falha de infraestrutura não vira decisão de investimento. O retry legitimamente
configurado hoje (`RetryingLLMClient`) continua valendo: só falha **não
recuperada** derruba o run.

**Precisão sobre a camada em que cada coisa acontece**, para que o protocolo não
descreva o fallback interno como se fosse comportamento científico:

```text
tentativa recuperada pelo retry
        -> NÃO é falha; aparece apenas como attempt_count > 1

falha após o retry
        -> registrada no limite do provedor, antes de o nó engoli-la
        -> o nó do grafo degrada para MANTER / VETADO
           ISTO É FALLBACK INTERNO DO GRAFO

o participante observa a falha registrada
        -> levanta LLMDecisionError -> O RUN FALHA
           ESTE É O COMPORTAMENTO CIENTÍFICO
```

Portanto o `MANTER` defensivo do grafo **nunca chega a existir como decisão de
investimento** no caminho da arena; o sizing sequer é consultado quando há
falha. O `MANTER` legítimo é outro: todos os votos válidos, sem supermaioria.

## 14. Models/providers

- Modelo local: `TBD`.
- Modelo cloud: `TBD`.
- Provedor(es): `TBD`.
- Versão/data de acesso e endpoint: `TBD`.
- Parâmetros de geração suportados: `TBD`.
- Structured output: `TBD`.

Compatibilidade será declarada apenas após validação documental e técnica. Cache
hits e respostas mock serão identificados e não serão confundidos com chamadas
reais.

**Proveniência registrável hoje, sem congelar escolha.** A `ParticipantSpec` do
`llm_agent` grava `provider` e `model` no `spec_hash` e no manifest, e o
provedor real exige `model` explícito — sem modelo declarado o run não começa.
`provider="mock"` também é registrado, de modo que um run mock nunca se confunde
com um run científico.

O que isso identifica é **o que foi tecnicamente solicitado**:

```text
requested_model = "<id enviado ao provedor>"      -> registrado
exact_model_weights / versão interna do modelo    -> NÃO identificável
```

O provedor não expõe versionamento de pesos, então o manifest não afirma
identificá-lo. `base_url`, timeout e credencial continuam sendo ambiente de
execução: a credencial nunca é serializada; o endpoint ainda não entra na spec,
e isso é uma lacuna conhecida de proveniência.

## 15. Seeds and stochasticity

- Seeds por variante e execução: `TBD`.
- Número de repetições: `TBD`.
- Política quando o provedor não aceitar seed: `TBD`.
- Tratamento de não determinismo residual: `TBD`.

Seed só será enviada a um provedor após confirmação de suporte. Toda seed
configurada, enviada ou apenas auditada deverá ser distinguida no manifest.

**Estado técnico verificado.** O `AgentRouterLLMClient` transmite apenas
`temperature`, `top_p` e `max_tokens`. `seed` é gerada pelo ensemble, entra no
`TechnicalVote` e aparece no trace como opção **solicitada**, mas **nunca é
enviada ao endpoint**. Essa distinção passou a ser publicada por chamada:

```text
requested_options  -> {"temperature": ..., "seed": ..., "analyst_id": ...}
transport_options  -> {"temperature": ...}       # seed ausente
```

Portanto: não existe, hoje, determinismo por seed neste provedor, e nada no
projeto deve ser descrito como tal. A decisão sobre enviar `seed` quando houver
suporte documentado continua `TBD`.

### Inferência ao vivo versus inferência por replay

Esta distinção é parte do protocolo, não detalhe de implementação.

```text
inferência ao vivo
  mesma ExperimentSpec + mesmo snapshot + provedor externo
  -> NÃO garante resposta idêntica
  -> fonte primária de evidência: o trace gravado daquela execução

inferência por replay
  trace gravado -> ReplayLLMClient -> sem rede
  -> mesmas respostas, mesmas decisões, mesmos trades, mesmas métricas
  -> é o mecanismo de reprodução exata do experimento
```

Um resultado científico publicado por este projeto é, portanto, um par:
o **run ao vivo** (com seu trace e seu commit) e a **capacidade de replay**
daquele trace. Reexecutar a mesma spec contra o provedor produz *outra*
execução, legítima como nova amostra, jamais como reprodução da primeira.

O replay recusa divergência em vez de acomodá-la: prompt, modelo, provedor,
opções solicitadas, schema, papel, analista, sessão ou ordem diferentes
levantam `ReplayMismatchError`, e sobra ou falta de registro também. Relógio e
duração não entram nessa identidade.

### Repetições da VALIDATION

Proposta registrada, **não congelada**:

```text
2–3 independent live LLM runs
```

Enquanto a `seed` não for transmitida ao provedor, o protocolo **não** descreve
essas repetições como "seeds distintas": elas não são replicações controladas
por seed. Cada repetição mantém idênticos a `ExperimentSpec`, o snapshot, o
provider/model solicitado e os parâmetros de geração, e difere apenas em
`run_id` e trace.

O que elas medem é a **variabilidade operacional residual do provedor e do
modelo** — amostragem com temperatura maior que zero, não determinismo do lado
do provedor, retries e eventual atualização silenciosa do modelo por trás do
identificador solicitado (seção 14).

Invariantes já aprovados:

```text
todos os runs publicados
nenhum run desfavorável escondido
nunca escolher o melhor run post-hoc
mesma spec, mesmo snapshot, mesma configuração
run_ids e traces independentes
```

Ainda `TBD`, e dependente da definição da métrica primária (seção 17.3):

```text
regra de síntese entre os runs
   primeiro run · mediana · média · outra
```

Restrição que vale mesmo com o valor em aberto: a regra de síntese precisa ser
declarada **antes** de executar os runs da VALIDATION. Declará-la depois de ver
os resultados é escolher o melhor run por outro nome.

**Nada aqui congela modelo, prompt, quorum ou seed.** O mecanismo de evidência
existe; as escolhas científicas continuam `TBD`.

## 16. Prompt versioning

Cada prompt científico terá identificador de versão, conteúdo ou hash, papel do
agente, schema esperado e parâmetros de geração. O procedimento de revisão e a
versão final são `TBD`.

Prompts serão congelados no FREEZE, **antes da PSEUDO-LIVE VALIDATION** — não
apenas antes do FINAL TEST. Alterações posteriores criam nova versão e não
sobrescrevem resultados existentes; alterar prompt depois de observar a
VALIDATION devolve aquela janela para development/calibration (seção 5.8).

**Onde os prompts vivem hoje, e o que isso garante.** Eles continuam sendo
constantes de módulo em `src/agents/technical_analyst.py`,
`src/agents/risk_manager.py` e `src/agents/portfolio_manager.py`. **Não existe
prompt registry nem campo de versão de prompt**, e nenhum `prompt_version` é
inventado enquanto não existir mecanismo que o sustente.

O que passou a existir é proveniência do texto concreto de cada chamada:

```text
git_commit                     -> proveniência do CÓDIGO que gerou o prompt
system_prompt / user_prompt    -> o prompt LÓGICO completo, na íntegra
system_prompt_sha256
user_prompt_sha256             -> proveniência desse texto lógico
response_schema_sha256         -> estrutura do schema pedido
transport_system_prompt_sha256 -> hash do texto final enviado, quando o
                                  cliente concreto o reporta
```

Os hashes são SHA-256 do texto exato em UTF-8, **sem normalizar espaço em
branco**: dois prompts que diferem em espaço em branco são prompts diferentes.
O texto completo é gravado, e não só o hash, porque auditoria e replay precisam
reconstruir a chamada — e nenhum prompt do projeto carrega segredo. Credencial
e cabeçalho HTTP continuam fora do artefato por construção.

**Prompt lógico ≠ prompt de transporte.** O `AgentRouterLLMClient` acrescenta o
`model_json_schema()` serializado ao system prompt antes de montar o corpo
HTTP. Portanto o `system_prompt` publicado no trace **não é**, para esse
provedor, o texto literal enviado — e o protocolo não pode descrevê-lo assim.

O que torna a requisição enviada inequívoca é a combinação: prompt lógico na
íntegra + `response_schema_sha256` + o molde, que é código coberto pelo
`git_commit`. Por isso o digest do schema entra na **identidade** usada pelo
replay: dois schemas de mesmo nome e estrutura diferente perguntam coisas
diferentes ao provedor e não podem ser tratados como a mesma chamada.

O vínculo com o código permanece: o `ExperimentRunner` recusa working tree suja
e o manifest grava o commit. Registry e versionamento formal de prompt seguem
`TBD` e hardening futuro.

## 17. Metrics

Duas famílias de métricas poderão ser analisadas **separadamente**, sem que uma
seja convertida na outra.

### 17.1 Decision diagnostics

#### Quatro resultados possíveis, e o papel de cada um

O contrato de execução (`close(t) -> decisão -> open(t+1)`) torna estes quatro
resultados distintos, e misturá-los é o erro que esta subseção existe para
impedir:

```text
A  overnight            close(t)   -> open(t+1)
B  intradiário seguinte open(t+1)  -> close(t+1)
C  close-to-close       close(t)   -> close(t+1)
D  P&L realizado        o que a Arena efetivamente obteve
```

| | o que mede | capturável por uma entrada nova | papel |
|---|---|---|---|
| **A** | o trecho que o contrato de execução doa ao mercado | **não** | diagnóstico do efeito overnight |
| **B** | o movimento negociável depois da execução | **sim** | diagnóstico da decisão |
| **C** | "o mercado subiu amanhã?" — alvo natural de uma tarefa de previsão | não | descritivo |
| **D** | o resultado, com custos, lote inteiro e estado de carteira | é o resultado | resultado científico |

Para uma Calibration Anchor, que começa com a carteira zerada,
`D ≈ w × B − custos`: o termo `A` **não aparece**. Numa janela sequencial a
composição muda com o estado — posição mantida através da noite recebe `C`,
posição liquidada na abertura recebe `A`, entrada nova recebe `B`. Ou seja,
`A` e `C` não são inacionáveis em geral: são inacionáveis para **entradas
novas**, que é o caso de toda âncora.

Exemplo mínimo do porquê isto importa:

```text
close(t) = 100 · COMPRA · open(t+1) = 110 · close(t+1) = 105

C = +5,00%   "acertou a direção"
B = −4,55%   o que a operação realmente viveu
```

A decisão contaria como acerto sob `C` e perde dinheiro sob `D`. Usar `C` como
objetivo otimizaria uma quantidade que a estratégia não pode receber.

#### O v1 não tem tarefa de previsão de preço

O sistema emite `COMPRA / VENDA / MANTER` e um peso alvo. Ele **não** emite
probabilidade, magnitude ou intervalo. Por isso:

```text
MANTER não tem conteúdo direcional: é a decisão de não alterar exposição,
       não a previsão de que o preço ficará estável
VENDA sobre carteira zerada é no-op num participante long-only
COMPRA é estado desejado de exposição, não o sinal do próximo retorno
não existe probabilidade -> Brier, log-score e curva de calibração
       são impossíveis, e confidence está proibida de virar probabilidade
       (seção 11)
```

Separação formal adotada, para não converter uma coisa na outra:

```text
INVESTMENT DECISION QUALITY     primário
   unidade: decisão -> contribuição de P&L líquido realizado (D)

ACTION–OUTCOME CONCORDANCE      descritivo (substitui "acurácia direcional")
   definida APENAS para Calibration Anchors e novas entradas em janela
   sequencial, avaliada contra B
   NÃO se aplica a posição mantida, a saída de posição existente
   nem a MANTER com exposição zero, que é abstenção e é reportada
   separadamente como cobertura

PRICE FORECAST ACCURACY         não existe no v1
   exigiria emissão explícita de previsão probabilística sobre evento
   declarado; é extensão de protocolo, não releitura da saída atual
```

Em VALIDATION e FINAL TEST **não se cria pseudo-acurácia de ação**: a evidência
correta é P&L de carteira, curva de patrimônio e a família canônica da seção
17.2. Medir uma decisão de manter contra `B` seria avaliar o desempenho de uma
operação que não foi feita.

#### Decomposição descritiva em janela sequencial

Permitida como análise descritiva, nunca como objetivo de tuning:

```text
resultado da carteira na sessão, decomposto em
   componente overnight   (sobre posição já carregada)
 + componente intradiário (sobre posição após execução)
 + custos
```

Responde a uma pergunta legítima — quanto do resultado veio de gap sobre posição
já existente — sem transformar isso em alvo.

#### Tabela de diagnósticos e seus papéis

| diagnóstico | descritivo | pode orientar Performance Calibration | resultado científico |
|---|:--:|:--:|:--:|
| `overnight_return` (A) | sim | não | não |
| `intraday_return` (B) | sim | sim, só em CAL-A e agregado | não |
| `close_to_close_return` (C) | sim | não | não |
| `realized_portfolio_pnl` (D) | sim | sim, agregado | sim |
| `action_outcome_concordance` (âncoras e novas entradas) | sim | não | não |
| decomposição overnight/intradiário | sim | não | não |
| cobertura / taxa de abstenção | sim | não | não |
| `confidence`, consenso e divergência do quorum | sim | não | não |
| defeitos, vetos e falhas de schema | sim | sim, via Diagnostic Hardening | não |
| família da seção 17.2 | — | só como development, no Sequential Development | sim, em VALIDATION e FINAL TEST |

Manter vários diagnósticos simultâneos é deliberado; transformá-los todos em
objetivo, não. Exatamente **uma** quantidade agregada é o critério de seleção em
CAL-A (seção 5.12), e todas as demais linhas são descritivas. Sem essa regra, a
coexistência de quatro retornos equivaleria a testes múltiplos implícitos:
sempre haveria uma métrica que melhorou.

### 17.2 Portfolio performance

Família canônica, sobre a curva líquida:

- retorno líquido, total e anualizado;
- CAGR;
- volatilidade anualizada;
- Sharpe líquido;
- Sortino;
- Max Drawdown;
- custos totais;
- número de trades e turnover;
- exposição e caixa;
- medidas adicionais: `TBD`.

### 17.3 Métrica primária

```text
MÉTRICA PRIMÁRIA DO TCC = TBD
```

O que já está decidido é o **objeto** que ela mede:

```text
resultado científico = P&L realizado pela Arena (D)
                     + curva líquida
                     + métricas canônicas da seção 17.2
```

Falta escolher qual função desse objeto é a métrica primária. Duas quantidades
distintas, que não devem ser confundidas e que continuam ambas `TBD`:

```text
MÉTRICA PRIMÁRIA          resultado do TCC, sobre VALIDATION e FINAL TEST
CRITÉRIO AGREGADO CAL-A   seleção entre configurações, evidência de
                          desenvolvimento, restrições na seção 5.12
```

Taxa livre de risco, convenções de anualização, tratamento de dias sem posição e
fórmulas definitivas: `TBD`.

## 18. Statistical analysis

- Teste(s) estatístico(s): `TBD`.
- Nível de significância e intervalos de confiança: `TBD`.
- Correção para comparações múltiplas: `TBD`.
- Tratamento de dependência temporal: `TBD`.
- Unidade de reamostragem/bootstrap: `TBD`.
- Análises por subperíodo e seed: `TBD`.

Os testes e suas premissas serão escolhidos antes de observar o ranking em TEST.

## 19. Ablations e estrutura de comparação

### 19.1 Estrutura conceitual das comparações

```text
classical benchmarks
    Buy & Hold
    SMA
    Bollinger
    [benchmarks multiativo, quando aplicável]

LLM / agentic variants
    sistema multiagente base

future ablations
    multiagent + Historical Memory
    outras, apenas se metodologicamente justificadas
```

Futuras ablations deverão isolar a contribuição de cada componente. Nenhum
participante "LLM simples" está definido neste projeto, e este documento não o
declara existente.

### 19.2 Plano candidato

```text
A — quantitativos clássicos
B — agente técnico único
C — ensemble técnico
D — ensemble + risk manager
E — sistema completo
F — local vs cloud
G — roteamento híbrido local/cloud (opcional posterior)
H — sistema completo + Historical Memory (seção 23)
```

O objetivo é estimar qual componente acrescenta valor. Contrastes, seeds,
orçamento e critérios estatísticos: `TBD`.

## 20. Reproducibility manifest

Cada `run_id` deverá registrar, no mínimo:

- versão do código e ambiente;
- `ExperimentSpec` completa;
- snapshot e hashes;
- universo, calendário e janela experimental (calibration, validation ou
  final test);
- participante e parâmetros;
- capital, custos e regras de execução;
- modelo, provedor e parâmetros efetivamente enviados;
- prompts e schemas versionados;
- seeds configuradas e efetivamente suportadas;
- eventos de telemetria, cache, retry e falha;
- artefatos e versão do cálculo de métricas.

Formato e schema versionado do manifest: `TBD`.

Implementação técnica atual, que não congela nenhum item acima: cada execução
por `ExperimentRunner` publica `data/runs/<run_id>/manifest.json` com
`schema_version`, `run_id`, `spec_hash`, `created_at`, a `ExperimentSpec`
canônica, o participante, identidade/metadados/hashes do snapshot consumido, universo
efetivo, configuração de custo, configuração de métrica, capital, patrimônio
final, métricas, contagem de trades, custo total executado, commit Git e estado
dirty. `spec_hash` é o SHA-256 do JSON canônico da spec e identifica a
configuração; `run_id` identifica a execução. A coerência
`spec_hash == SHA-256(canonical_json(experiment_spec))` é verificável no próprio
artefato. O bloco `snapshot` registra `schema_version` e `identity_digest` do
snapshot, o que permite responder "qual snapshot verificável foi usado neste
run?" sem reler o diretório — a proveniência é capturada no `run()` e `persist()`
não a redescobre.

O que hoje **já** entra na spec, e o que **ainda não** entra, precisa ser lido
com precisão — a lista abaixo foi conferida contra `ParticipantSpec` e a
assinatura de `LLMParticipant.__init__`:

| Elemento | Na spec/`spec_hash`? | Onde vive |
|---|---|---|
| Snapshot consumido | Sim | `snapshot_id` |
| Capital inicial, custos, configuração de métrica | Sim | `ExperimentSpec` |
| Ativo do participante single-asset | Sim | `ParticipantSpec.params.ticker` |
| Provedor e modelo requisitado | Sim | `provider`, `model` |
| Política de retry | Sim | `retry_attempts`, `retry_base_delay` |
| Quorum técnico e consenso | Sim | `analyst_count`, `consensus_threshold`, `require_all_votes` |
| Faixa de temperatura do ensemble | Sim | `temperature_min`, `temperature_max` |
| Base de seeds **configurada** | Sim | `seed_base` |
| Limites duros de risco | Sim | `risk_max_volatility`, `risk_max_drawdown`, `risk_max_concentration` |
| Alvo determinístico de exposição long | Sim | `long_target_weight` |
| Janela de volatilidade | Sim | `volatility_window` |
| Frequência de decisão | Sim | `decision_frequency` |
| Credencial do provedor | **Não, por desenho** | ambiente; nunca em spec, manifest, log ou artefato |
| Texto dos prompts | Não | código-fonte, identificado no trace por SHA-256 |
| Janela experimental (período avaliado) | **Sim** | `evaluation.decision_start` / `decision_end` |
| Histórico mínimo exigido antes da primeira decisão | **Sim** | `evaluation.minimum_history_sessions` (valor científico `TBD`) |
| Fase do protocolo e `case_id` | **Não, por desenho** | manifest (`run_context`), declarados antes do run |
| Benchmark de mercado de referência | Não | `TBD` |

Distinção que o protocolo exige manter, porque as duas coisas costumam ser
confundidas:

```text
CONFIGURAÇÃO PEDIDA / SPEC        EVIDÊNCIA OBSERVADA DURANTE O RUN
-------------------------        ---------------------------------
seed_base configurado            -> sim, spec
seed efetivamente enviada        -> NÃO existe hoje: `seed` é opção
                                    solicitada e não está em
                                    `AgentRouterLLMClient.TRANSMITTED_OPTION_KEYS`
requested options                -> trace (`llm_calls.jsonl`)
transport options                -> trace (`llm_calls.jsonl`)
modelo requisitado               -> spec
prompts efetivamente enviados    -> trace, por digest
```

Ou seja: `seed` aparece no ensemble e no trace como intenção, mas o cliente
real transmite somente `temperature`, `top_p` e `max_tokens`. Declarar
determinismo por `seed` seria falso.

A **janela experimental deixou de estar fora da spec**. `ExperimentSpec.evaluation`
é uma `EvaluationSpec` com `decision_start`, `decision_end` e
`minimum_history_sessions`, os três dentro do `spec_hash`. O benchmark de
mercado continua fora, e as **datas** continuam `TBD`: existe como declarar a
janela, não qual janela declarar.

Runs reproduzíveis exigem proveniência Git verificável e working tree limpa. O
`ExperimentRunner` já impõe isso por padrão, de forma fail-closed estrita:
alterações não commitadas, commit indeterminado e proveniência não verificável
abortam a execução antes de qualquer trabalho. Existe um escape explícito de desenvolvimento
(`allow_dirty=True`) que cobre os dois casos, libera a execução e marca
`reproducibility.clean_source=false` no manifest; ele não altera o `spec_hash`.
Nenhum diff do working tree é persistido — a reprodução depende do commit, não
de um patch anexado.

Para o `llm_agent`, o bloco `participant` do manifest carrega a configuração
material do LLM: provedor, modelo requisitado, política de retry, quorum e
consenso, faixa de temperatura, `seed_base`, limites duros de risco,
`long_target_weight`, janela de volatilidade e frequência de decisão. Não há
`payoff_ratio`, `kelly_fraction` nem `max_position_size` nessa spec: eles
pertencem ao caminho de sizing legado, que o participante científico nunca
executa. Credencial não entra em spec, manifest, log nem artefato de auditoria.

A partir do schema 3, o manifest também publica `participant_artifacts`, e um
run `llm_agent` acompanha o arquivo `llm_calls.jsonl`:

```json
"participant_artifacts": {
  "llm_calls": {
    "path": "llm_calls.jsonl",
    "schema_version": 2,
    "call_count": 123,
    "error_count": 0,
    "bytes": 456789,
    "sha256": "..."
  }
}
```

O `sha256` é dos bytes efetivamente publicados, o que torna detectável o estado
"manifest íntegro, trace adulterado". O contrato é genérico
(`RunArtifactProvider`), e participantes clássicos publicam
`participant_artifacts` vazio. A `ExperimentSpec` **não** ganhou nada disso:
`call_id`, timestamps, latência, tokens observados, resposta bruta e caminho do
trace são o que *aconteceu*, não configuração pedida antes do run.

Com isso, "eventos de telemetria, cache, retry e falha" da lista acima passa a
ter cobertura por chamada — `attempt_count`, `retry_count`, `status`,
`error_type`, `duration_ms` e `token_usage` quando o provedor o devolve. Seguem
**não** registrados: custo monetário (sempre zero), versionamento de prompt
(inexistente por decisão) e fingerprint de modelo devolvido pelo provedor (não
é entregue no contrato atual — o manifest registra o modelo *solicitado* e o
endpoint sanitizado).

## 21. Freeze procedure

O freeze encerra a SYSTEM CALIBRATION (seção 5.7) e abre a PSEUDO-LIVE
VALIDATION. Ele só ocorre **depois de CAL-B aprovado** (seção 5.12). Antes dele,
dupla e orientador deverão aprovar e registrar:

1. pergunta e hipóteses;
2. universo e snapshot;
3. Calibration Cases, período de Validation, período de Final Test e
   Walk-Forward;
4. participantes, parâmetros e benchmarks;
5. modelos, prompts, papéis, quorum, temperaturas e seeds;
6. capital, custos, execução e risco, incluindo `long_target_weight` e
   `decision_frequency`;
7. janela base de mercado (parametrização exata da seção 7.2);
8. política de Historical Memory, se houver alguma ativa;
9. métricas, métrica primária, análise estatística e ablations;
10. versão do código e do manifest;
11. o change log completo da calibração — versões de Diagnostic Hardening,
    configurações avaliadas em CAL-A (`N` e `R` realizados), seleções do
    Sequential Development, comparações invalidadas por mudança de classe de
    comparabilidade e o resultado do CAL-B;
12. a declaração explícita de todo parâmetro material na `ParticipantSpec`,
    inclusive quando o valor coincidir com o default técnico (seção 5.7).

Forma de aprovação, responsáveis e registro imutável: `TBD`. Até essa aprovação,
o status deste documento permanece **DRAFT — NÃO CONGELADO**.

## 22. Rules after opening TEST

- Não ajustar participante, prompt, modelo, parâmetro ou custo após observar TEST.
- Não substituir snapshot ou universo silenciosamente.
- Não descartar falhas ou seeds desfavoráveis sem critério pré-registrado.
- Não promover análise pós-hoc a hipótese confirmatória.
- Toda correção indispensável deverá gerar nova versão do protocolo, novo
  `run_id` e justificativa explícita; a execução anterior será preservada.
- Resultados mock, CALIBRATION, VALIDATION, FINAL TEST e LIVE/SHADOW terão
  rótulos distintos e não serão agregados como se fossem a mesma evidência.
- Alterar o sistema depois de observar a VALIDATION devolve aquela janela à
  condição de development/calibration (seção 5.8); ela deixa de servir como
  evidência out-of-sample.
- CAL-B é aberto uma única vez por versão da calibração. Um run que produziu
  decisão, trace e reasoning utilizáveis consome o holdout, qualquer que tenha
  sido o comportamento observado; corrigir o sistema com base nele exige nova
  versão metodológica e novo pré-registro (seção 5.12).
- Correção comportamental de classe A ou B durante a Performance Calibration
  invalida as comparações do baseline anterior, que permanecem registradas em
  vez de apagadas (seção 5.12).
- Exceções a estas regras: `TBD` e dependem de aprovação antes do congelamento.

## 23. Historical Memory — extensão planejada

**STATUS: hipótese experimental separável. NÃO IMPLEMENTADA.** Nada nesta seção
existe em código, e nada aqui está congelado.

### 23.1 Ideia

Além do contexto base recente obrigatório

```text
Base Market Context >= 2 anos
```

o sistema poderá futuramente consultar uma **Historical Memory** contendo
períodos mais antigos, para que consiga identificar o regime/contexto atual e
solicitar episódios históricos potencialmente análogos.

Exemplo apenas explicativo, não especificação:

```text
contexto atual percebido:
- ano eleitoral
- juros elevados
- alta exposição a commodity

        v
agente solicita contextos historicamente semelhantes

        v
retriever recupera episódios anteriores relevantes
```

### 23.2 Não é history dump

Historical Memory **não** significa fornecer todo o histórico possível ao LLM em
todas as decisões. A proposta é:

```text
contexto recente obrigatório
+
recuperação seletiva de episódios mais antigos
```

A recuperação deve ser acionada segundo política definida pelo sistema. Essa
política é `TBD`, assim como algoritmo de retrieval, embeddings e armazenamento.

### 23.3 Regra científica obrigatória — disponibilidade temporal

Para uma decisão simulada em `t`:

```text
qualquer informação recuperada
deve ter estado disponível em ou antes de t
```

Portanto o futuro corpus precisará de proveniência temporal suficiente para
*provar* essa disponibilidade. Conceitualmente, documentos/eventos poderão
precisar de campos como:

```text
event_date
available_at
source
content
tags / metadata
```

O requisito científico central é:

```text
available_at <= decision_time
```

Nenhum schema definitivo é congelado aqui.

### 23.4 Hindsight em documentos históricos

Forma mais sutil de vazamento: não basta o **evento** ter ocorrido antes de `t`.
Uma descrição posterior do evento pode conter conhecimento que ainda não existia
em `t`.

```text
evento em 2018
documento retrospectivo escrito em 2025
```

Esse documento **não** pode ser tratado como informação disponível numa simulação
de 2019 apenas porque descreve um evento de 2018. O critério é a disponibilidade
da informação, não a data do evento.

### 23.5 Ablation recomendada

Desenho experimental futuro recomendado:

```text
Multiagent — Base Context
vs
Multiagent — Base Context + Historical Memory
```

Mantendo idênticos dados recentes, modelo, prompts-base, quorum, risco, sizing,
Arena, custos e período. A única variável experimental deve ser a
disponibilidade/política de Historical Memory, de modo a responder:

> recuperação adaptativa de contextos históricos acrescenta valor incremental?

Parâmetros dessa ablation não estão congelados e ela não foi executada.

## 24. Live / Shadow forecasting

Estágio posterior ao experimento histórico. Objetivo: usar a informação
disponível no dia corrente real para produzir a decisão do próximo pregão real.

```text
hoje
        v
information set real disponível
        v
decisão
        v
registrar ANTES do próximo pregão
        v
amanhã acontece
        v
avaliar a previsão
```

O registro anterior ao pregão é o que torna a previsão avaliável; uma decisão
registrada depois da abertura não é evidência live. Esta camada **não** substitui
o teste histórico — ela aproxima o laboratório do objetivo operacional final.

Base técnica já existente e reaproveitável, sem que isso a torne aprovada: o
`DailyAgentRunner` persiste a previsão pendente entre processos, reconcilia a
sessão-alvo e avança uma sessão por execução, mas continua fora da arena comum e
sem manifest canônico (`docs/ESTADO_ATUAL.md`). Frequência, ativo, duração e
critério de avaliação do estágio live: `TBD`.

## 25. Controles de leakage — consolidado

Quatro vazamentos distintos, com controles distintos.

```text
1. market future leakage
   decisão em close(t) nunca vê open(t+1) nem barra posterior
   -> features calculadas sobre histórico truncado em t (seção 7)
   -> execução exclusiva pelo ExecutionEngine na abertura seguinte (seção 8)
   -> MarketObservation não revela se existe barra futura no recorte

2. document / retrieval leakage   (quando houver Historical Memory)
   available_at <= decision_time, obrigatório por documento
   -> seção 23.3

3. hindsight annotation
   descrição posterior de evento anterior não é informação disponível
   -> seção 23.4

4. researcher overfitting
   ajustar o sistema repetidamente sobre o mesmo período observado
   -> separação obrigatória calibration / freeze / validation / final test
   -> governança de subfases, espaço de busca finito, critério declarado
      antes, change log e autoridade por parâmetro
   -> seções 5.6 a 5.9, seção 5.12 e regras da seção 22
```

Os três primeiros são controles sobre o que o **sistema** vê. O quarto é controle
sobre o que os **pesquisadores** fazem, e nenhum mecanismo técnico do repositório
o impede sozinho: ele depende do procedimento das seções 5.7, 5.12 e 22.

### Embargo temporal — decisão aprovada

```text
NENHUM embargo temporal obrigatório no v1
```

Um intervalo fixo entre fases — 21 sessões ou qualquer outro número — foi
considerado e **não** foi adotado. O instrumento existe, na literatura de
validação cruzada financeira, porque rótulos abrangem várias barras e amostras
de treino se sobrepõem às de teste. Aqui não há rótulo nem treino: o LLM chega
pré-treinado, e a decisão em `t` usa histórico expansivo que legitimamente
inclui o período de calibração, o que é causal e correto. Contra o vazamento de
mercado, os controles 1 a 3 já respondem; contra o overfitting do pesquisador,
um intervalo não ajuda — conhecimento do pesquisador não é local no tempo e não
decai em algumas sessões.

O controle real de separação é verificável:

```text
ordem cronológica entre as fases
janelas e conjuntos de âncoras disjuntos (invariantes da seção 5.12)
CAL-B isolado de todo development
freeze antes da VALIDATION
pré-registro do espaço de busca e do critério
```

Um gap natural de calendário pode existir por conveniência de seleção de datas,
mas **não é apresentado como controle de leakage** e não tem número científico
associado.
