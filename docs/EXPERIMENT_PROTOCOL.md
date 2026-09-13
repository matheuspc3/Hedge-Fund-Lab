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

Detalhamento na seção 5. Onde este documento diz apenas `TEST`, leia
**FINAL TEST**.

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
risco devem ser aprovadas antes do FINAL TEST. Nenhuma redação está congelada.

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
- `long_target_weight`;
- `decision_frequency`;
- regras de recuperação de contexto histórico;
- demais configurações declaradas do sistema.

Nenhum peso de modelo é alterado nesse processo. O artefato ajustado é a
configuração, capturada pela `ExperimentSpec`, pelo `spec_hash` e pelo commit
(seção 20).

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

São **critérios candidatos**, não uma seleção congelada. Quantidade de casos,
datas e ativo do piloto: `TBD`.

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

### 5.7 Freeze

Ao encerrar a calibração deve existir uma configuração **identificável e
reproduzível**. O freeze abrange, no mínimo, os parâmetros científicos materiais
então existentes:

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

O que **não** foi congelado e permanece `TBD — EXPERIMENT PROTOCOL v1`:

```text
exatamente 2 anos calendários?        TBD
exatamente 504 pregões?               TBD
2 anos como máximo ou só mínimo?      TBD
política exata para sessões faltantes TBD
```

A decisão congelada agora é apenas esta: o sistema deve trabalhar com uma janela
recente de mercado de pelo menos dois anos para formar o contexto base da
decisão.

**Estado técnico verificado, que não congela nada acima.** Hoje a arena entrega
ao participante o recorte `history` do início do snapshot até `session`, isto é,
uma janela **expansiva**, e a `ExperimentSpec` não possui campo de período: o
intervalo experimental é a cobertura efetiva do snapshot. Consequência prática a
resolver no congelamento: garantir a janela base de dois anos em `t` é hoje
responsabilidade de **escolher a cobertura do snapshot** de modo que as datas de
decisão comecem pelo menos dois anos após o início da série. Não existe, no
código atual, parâmetro de janela mínima nem gate que recuse decidir antes disso
— é lacuna conhecida, não capacidade existente.

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

Parâmetros e frequência de cada benchmark: `TBD`. Todos serão congelados antes
do TEST e executados pelo contrato comum.

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

Nenhum dos dois foi aprovado como parâmetro científico. A frequência definitiva
do experimento deve ser decidida junto com as janelas experimentais e o
orçamento de chamadas, antes do FINAL TEST.

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

**Nada aqui congela modelo, prompt, quorum ou seed.** O mecanismo de evidência
existe; as escolhas científicas continuam `TBD`.

## 16. Prompt versioning

Cada prompt científico terá identificador de versão, conteúdo ou hash, papel do
agente, schema esperado e parâmetros de geração. O procedimento de revisão e a
versão final são `TBD`.

Prompts serão congelados antes do TEST. Alterações posteriores criam nova versão
e não sobrescrevem resultados existentes.

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

Diagnóstico do comportamento decisório, por decisão:

- direção prevista;
- direção observada;
- taxa de acerto direcional;
- comportamento de COMPRA/VENDA/MANTER;
- `confidence` reportada;
- consenso e divergência do quorum.

Servem para explicar *como* o sistema decide. Acurácia direcional **não** é,
por conta disto, objetivo principal do TCC, e não pode ser promovida a métrica
primária sem decisão explícita registrada aqui.

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
não a redescobre. Janelas experimentais, seeds, prompts, modelos e benchmark
ainda não fazem parte da spec porque dependem de decisões `TBD`. Em particular, a
spec não declara período: o recorte executado é a cobertura efetiva do snapshot,
e é por ela que uma janela experimental é hoje materializada.

Runs reproduzíveis exigem proveniência Git verificável e working tree limpa. O
`ExperimentRunner` já impõe isso por padrão, de forma fail-closed estrita:
alterações não commitadas, commit indeterminado e proveniência não verificável
abortam a execução antes de qualquer trabalho. Existe um escape explícito de desenvolvimento
(`allow_dirty=True`) que cobre os dois casos, libera a execução e marca
`reproducibility.clean_source=false` no manifest; ele não altera o `spec_hash`.
Nenhum diff do working tree é persistido — a reprodução depende do commit, não
de um patch anexado.

Para o `llm_agent`, o bloco `participant` do manifest carrega a configuração
material do LLM: provedor, modelo requisitado, política de retry, quorum,
limites de risco e de portfólio, janela de volatilidade e payoff. Credencial
não entra em spec, manifest, log nem artefato de auditoria.

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
VALIDATION. Antes dele, dupla e orientador deverão aprovar e registrar:

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
10. versão do código e do manifest.

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
   -> seções 5.6 a 5.9 e regras da seção 22
```

Os três primeiros são controles sobre o que o **sistema** vê. O quarto é controle
sobre o que os **pesquisadores** fazem, e nenhum mecanismo técnico do repositório
o impede sozinho: ele depende do procedimento das seções 5.7 e 22.
