# Roadmap do Hedge-Fund-Lab

> Este documento é a única fonte de verdade para planejamento, prioridades,
> progresso e próximas fases do Hedge-Fund-Lab. Documentos antigos de
> planejamento foram movidos para [`archive/`](archive/) e possuem apenas valor
> histórico.

## 1. Objetivo do roadmap

A prioridade do TCC2 é transformar o laboratório técnico atual em uma arena
experimental reproduzível e cientificamente defensável. Validade dos dados,
equivalência entre participantes, execução sem look-ahead, custos comparáveis e
rastreabilidade vêm antes de otimizações, dashboard ou operação em tempo real.

Este documento define a ordem do trabalho. O estado verificável da implementação
fica em [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md), a estrutura técnica em
[`ARQUITETURA.md`](ARQUITETURA.md) e o contrato científico em
[`EXPERIMENT_PROTOCOL.md`](EXPERIMENT_PROTOCOL.md).

## 2. Decisões metodológicas atuais

As escolhas abaixo são recomendações de trabalho, não aprovações implícitas.

O status desta tabela é **metodológico**, não de implementação: "pendente de
congelamento" significa que a escolha científica ainda não foi aprovada, e não
que o mecanismo técnico esteja ausente. `ExperimentSpec`, `ExperimentRunner`,
`ExecutionEngine` e `RunResult` já existem e são usados pelos seis participantes
— possuir o mecanismo não equivale a ter congelado. O estado de implementação
está em [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md).

| Tema | Direção atual | Status |
|---|---|---|
| Unidade experimental | Carteira multi-ativo comum a todos os participantes | **STATUS: proposta / pendente de congelamento** |
| Universo principal | Os 10 ativos já usados pelo projeto | **STATUS: proposta / pendente de congelamento** |
| Análises secundárias | PETR4 e WEGE3, sem substituir a comparação principal | **STATUS: proposta / pendente de congelamento** |
| Informação e execução | Features disponíveis no fechamento de `t`; execução na abertura de `t+1` | **STATUS: proposta / pendente de congelamento** |
| Desenho experimental | Calibração retrospectiva do sistema -> freeze -> validação pseudo-live -> teste final -> live/shadow, em vez de TRAIN/TEST clássico | **STATUS: decisão metodológica aprovada** (datas e períodos continuam `TBD`) |
| Janela base de mercado | O sistema decide em `t` com pelo menos ~2 anos de histórico causalmente disponível | **STATUS: decisão metodológica aprovada**; gate implementado como `minimum_history_sessions` (valor `TBD`) |
| Modo de histórico | `expanding`: a decisão em `t` enxerga todo o histórico causal até `t` | **STATUS: decisão metodológica aprovada para o v1**; rolling fica como ablation futura |
| Historical Memory | Recuperação seletiva de episódios antigos, sob `available_at <= decision_time` | **STATUS: extensão planejada, não implementada** |
| Custos | Uma especificação versionada e idêntica para todos | **STATUS: proposta / pendente de congelamento** |
| Resultado | `RunResult` e manifest canônicos, identificados por `run_id` | **STATUS: proposta / pendente de congelamento** |
| Risco | Regras determinísticas obrigatórias; LLM apenas complementa | **STATUS: proposta / pendente de congelamento** |
| Kelly | Confiança textual do LLM não é `P(win)`; sizing científico é determinístico | **STATUS: decisão metodológica aprovada** (o valor de `long_target_weight` continua `TBD`) |
| Tempo real | Fora do caminho crítico até a arena histórica ser válida | **STATUS: proposta / pendente de congelamento** |

Quorum, modelos, prompts, thresholds, janelas experimentais, custos e demais
parâmetros finais devem ser aprovados pela dupla/orientador e congelados no
protocolo antes da validação pseudo-live e do teste final. Uma recomendação
deste roadmap não substitui esse congelamento.

## 3. Estado atual resumido

- Pipeline de extração, transformação e carga de OHLCV diário via `yfinance`.
- Indicadores SMA, Bollinger, RSI e MACD.
- Cinco benchmarks clássicos: três single-asset e dois multi-ativo, todos com
  caminho pelo contrato comum da arena.
- Participante LLM single-asset (`llm_agent`) também pelo contrato comum, com
  decisão do grafo existente e execução exclusivamente pela arena.
- Motores de backtesting clássicos legados e o motor LLM legado
  (`AgentBacktestEngine`), preservados como caminhos operacionais fora do
  contrato comum.
- Sistema multiagente linear: ensemble técnico, risco e portfólio.
- `AgentRouterLLMClient` HTTP OpenAI-compatible com configuração por ambiente.
- Retry, cache e telemetria básica de tokens, latência e modelo.
- `DailyAgentRunner` com estado persistido e reconciliação da previsão pendente.
- `B3Calendar` local com regras recorrentes e exceções explícitas.
- Dashboard dos benchmarks e tela separada para execução do participante LLM.

Limitações, evidências e riscos detalhados permanecem em
[`ESTADO_ATUAL.md`](ESTADO_ATUAL.md).

## 4. Fase atual — Núcleo científico comum

**Prioridade máxima atual (P0).** O objetivo é corrigir dados, relógio, execução,
custos e métricas antes de construir a arena.

### Dados

- [x] Corrigir a verificação da cobertura inicial e final do cache.
- [x] Recortar exatamente o intervalo solicitado.
- [x] Criar gate de qualidade OHLC, unicidade, volume e ordenação.
- [~] Integrar calendário local configurável ao gate de cobertura do snapshot;
  validação contra fonte oficial/versionada permanece pendente.
- [x] Rejeitar barras inválidas, inclusive OHLC não positivo ou inconsistente.
- [x] Criar snapshot imutável com versão, fonte, horário, parâmetros, hashes,
  cobertura por sessão e relatório de qualidade.
- [x] Dar identidade verificável ao manifest do snapshot: `snapshot_id`
  ancorado no digest do manifest completo, cobrindo `quality`, `coverage`,
  `files` e demais metadados, conferido contra o nome do diretório no
  carregamento. Schema legado recusado em vez de migrado.
- [x] Tornar carga parcial observável e consumível por automação.
- [ ] Adotar migrations antes que o schema passe a evoluir.

### Execução

- [x] Aplicar decisão em `t` e execução em `t+1` a todos os participantes
  clássicos atuais.
- [~] Definir ordem canônica: o contrato técnico preliminar `OrderIntent` já
  registra ativo, peso alvo e instante da decisão, enquanto direção e
  elegibilidade de execução pertencem ao executor; políticas científicas
  definitivas ainda não foram congeladas.
- [~] Definir alocação multi-ativo: o executor comum já vende antes de comprar e
  escalona as compras pelo mesmo fator quando o caixa não cobre todos os alvos,
  o que remove a dependência da ordem dos tickers; lote, resíduo de caixa e
  política definitiva de rateio continuam pendentes de congelamento.
- [x] Calcular custos sobre o valor financeiro total de cada ordem.
- [x] Reservar custos ao dimensionar quantidade.
- [x] Proibir caixa negativo.
- [ ] Aplicar a mesma política de lote, slippage, spread, corretagem e
  emolumentos.
- [~] Definir política de short: o caminho preliminar da arena rejeita peso
  negativo e alavancagem explicitamente; a política científica continua
  pendente.

### Métricas

- [x] Consolidar retorno periódico, retorno total, CAGR técnico, volatilidade,
  Sharpe, Sortino, Max Drawdown e duração de drawdown em uma implementação
  canônica.
- [x] Calcular o custo total pela soma dos custos dos trades executados.
- [~] Consolidar Turnover e exposição; a mudança de pesos existente inclui
  drift de mercado e os motores ainda não expõem histórico comum de caixa e
  posições.
- [~] Definir unidades e anualização de modo inequívoco; a implementação usa
  frações, `252` sessões/ano, risk-free zero e MAR zero como defaults técnicos
  configuráveis, ainda pendentes de congelamento científico.
- [x] Corrigir a agregação temporal, o período observado e as estimativas ad hoc
  do dashboard.
- [x] Calcular as métricas principais dos benchmarks clássicos atuais a partir
  da mesma curva líquida validada.

**Critério de saída:** benchmarks executam com dados validados, relógio `t ->
t+1`, custos corretos e métricas canônicas, deixando manifest reproduzível.

## 5. Arena de participantes

O contrato conceitual comum poderá ser representado por nomes como estes, sem
obrigar nomes exatos de classes antes da decisão de implementação:

```text
Participant
├── BuyAndHoldParticipant
├── SMACrossParticipant
├── BollingerParticipant
├── EqualWeightParticipant
├── MinVarianceParticipant
└── LLMParticipant          # registry: kind="llm_agent"
```

Os seis já existem. `LLMParticipant` é single-asset: ele recusa universo com
mais de um ativo em vez de inventar alocação entre ativos.

O invariante é:

```text
mesmos dados
+ mesmo relógio
+ mesmo capital
+ mesmos custos
+ mesmo motor
→ resultados comparáveis
```

- [x] Definir o contrato mínimo de `Participant`.
- [x] Criar `MarketObservation` causal e `OrderIntent` técnico preliminar.
- [x] Criar caminho comum de execução long-only para a migração incremental.
- [x] Adaptar Buy & Hold como primeiro participante.
- [x] Adaptar SMA Cross.
- [x] Adaptar Bollinger Bands.
- [x] Estender o caminho comum para carteira multi-ativo.
- [x] Adaptar Equal Weight.
- [x] Adaptar Mínima Variância.
- [x] Adaptar o participante LLM single-asset ao contrato comum.
- [ ] Evoluir o participante LLM para carteira-alvo multi-ativo; o contrato de
  carteira completa já existe e é validado, falta a etapa de alocação entre
  ativos na stack de agentes.
- [~] Criar `ExperimentSpec` como identidade completa da execução.

  Já existe na spec, dentro do `spec_hash`: `snapshot_id`, `ParticipantSpec`
  serializável com os parâmetros materiais do participante, universo derivado
  deterministicamente, capital, custos e parâmetros de métrica.

  A janela avaliada entrou na spec: `EvaluationSpec` com `decision_start`,
  `decision_end` e `minimum_history_sessions`, dentro do `spec_hash`.

  Ainda falta: benchmark de mercado como campo da spec, e os valores
  científicos de janela, frequência, seeds e demais parâmetros continuam
  dependendo do congelamento.
- [x] Decidir como o período/janela experimental será representado — escolhida a
  janela dentro da `ExperimentSpec`, sobre um snapshot amplo, em vez de um
  snapshot por Calibration Case.
- [ ] Escolher as janelas concretas de calibração, validação e teste final.
  `TBD — EXPERIMENT PROTOCOL v1`; o mecanismo não escolhe datas.
- [x] Garantir participante novo por execução, sem estado compartilhado entre runs.
- [x] Exigir `scientific_ready` e verificar identidade do manifest e hashes dos
  arquivos do snapshot antes de executar.
- [x] Tornar `ExperimentSpec` realmente imutável: `ParticipantSpec.params`
  read-only e `spec_hash` estável depois da construção.
- [x] Capturar a proveniência do snapshot no `run()` e impedir que `persist()`
  a redescubra relendo o artefato.
- [x] Exigir proveniência Git verificável e working tree limpa, com escape
  explícito de desenvolvimento registrado no manifest.
- [x] Criar `RunResult` e manifest canônicos.
- [x] Identificar e persistir cada execução por `run_id` e `spec_hash`.
- [x] Adaptar os cinco benchmarks e o participante LLM ao contrato comum: os
  cinco clássicos e o `llm_agent` single-asset executam pelo mesmo
  `ExecutionEngine` e pelo mesmo `ExperimentRunner`.
- [ ] Executar replay histórico e avanço diário com a mesma semântica.
- [x] Implementar `DailyAgentRunner` para avançar um pregão por execução.
- [x] Persistir estado diário e previsão pendente entre processos.
- [x] Implementar `B3Calendar` para resolver a próxima sessão.
- [~] Persistir `as_of`, `target_session`, status e execução no fluxo LLM; ainda
  faltam ordem canônica, validade e integração com o futuro `RunResult`.
- [ ] Validar o calendário local contra uma fonte oficial/versionada e registrar
  exceções no manifest.

**Critério de saída:** uma única execução produz resultados comparáveis e
auditáveis para todos os participantes sob a mesma `ExperimentSpec`.

## 6. Hardening do participante LLM

O cliente real já existe; esta fase é de hardening, não de implementação inicial.

### Implementado

- [x] Cliente HTTP OpenAI-compatible (`AgentRouterLLMClient`).
- [x] Configuração por ambiente.
- [x] Retry.
- [x] Cache.
- [x] Telemetria básica.
- [x] Tokens.
- [x] Latência.
- [x] Modelo.
- [x] Trace por chamada lógica publicado junto do run
      (`data/runs/<run_id>/llm_calls.jsonl`), com `schema_version` próprio.
- [x] Identidade explícita de chamada: `call_id`, `sequence`, `stage`,
      `analyst_id`, `decision_session`, provedor e modelo solicitados.
- [x] Prompts lógicos completos e SHA-256 de cada um, sobre o texto exato em
      UTF-8, com a distinção entre prompt lógico e prompt de transporte
      documentada em vez de apagada.
- [x] `response_schema_sha256` na identidade da chamada: o schema viaja dentro
      do system prompt, então mudar a estrutura sem renomear a classe passa a
      ser detectado pelo replay.
- [x] Separação entre opção solicitada e opção efetivamente transmitida, que é
      o que prova a lacuna de `seed`.
- [x] `attempt_count` por chamada, sem estado mutável compartilhado.
- [x] Replay determinístico do trace, sem rede, com detecção de divergência e
      de trace incompleto ou excedente.
- [x] Contrato genérico de evidência de participante (`RunArtifactProvider`),
      com `path`, `schema_version`, `call_count` e `sha256` no manifest.
- [x] Validação estrita de parâmetros inteiros do `LLMParticipant`, incluindo
      a borda `bool`, que o Pydantic converteria para `1` em silêncio.

Esses itens comprovam o protocolo HTTP implementado no repositório, não
compatibilidade oficial com um provedor específico.

### Pendências

- [ ] Registrar custo real ou estimado. O trace já preserva `token_usage` do
  provedor quando ele o devolve, e grava `null` quando não devolve; custo
  continua sempre zero em `LLMTelemetry`.
- [~] Vincular telemetria a run, agente, data e hash de prompt. **Feito** para o
  trace por chamada: `decision_session`, `stage`, `analyst_id` e os hashes de
  prompt estão no artefato do run. **Falta** versionamento de prompt de fato —
  os prompts seguem como constantes de módulo, sem registry, e nenhum campo
  `prompt_version` foi inventado sem mecanismo por trás.
- [ ] Usar structured output nativo quando o endpoint suportar.
- [ ] Verificar documentalmente o suporte real a `seed`.
- [ ] Enviar `seed` somente quando suportada. A lacuna agora é visível no
  artefato: `seed` aparece em `requested_options` e nunca em
  `transport_options`.
- [ ] Tornar o cache seguro sob concorrência. Mantido fora do caminho
  científico em vez de corrigido: o `LLMParticipant` não monta
  `CachedLLMClient` e o runner não o introduz. A chave do cache também ignora
  `provider`/`model`.
- [x] Remover estado mutável compartilhado de retry/telemetria.
  `LLMClient._retries_context` deixou de existir; o contador vive em rascunho
  por invocação em `ContextVar`, com teste de concorrência fora de lockstep.
- [ ] Preservar `raw_response` em todo provedor. Hoje o `AgentRouterLLMClient`
  grava o conteúdo bruto antes do parse; provedores sem essa captura registram
  apenas `validated_response`.
- [ ] Fingerprint real de modelo devolvido pelo provedor. O trace registra o
  modelo *solicitado* e o endpoint sanitizado, não a versão de pesos servida.
- [ ] Decidir se runs que falham devem publicar diretório próprio. Hoje uma
  falha do participante impede a publicação, comportamento preservado.
- [~] Garantir fail-closed completo após o quorum, inclusive risco e portfólio.
  No caminho da arena, falha não recuperada do provedor — timeout, erro HTTP,
  JSON inválido, schema inválido, quorum incompletado por falha — levanta
  `LLMDecisionError` e derruba o run em vez de virar `MANTER`. Os motores
  legados continuam com o fail-soft anterior, e o fail-soft de "decisão inverteu
  o sinal técnico" no `portfolio_manager` segue intacto.
- [x] Calibrar confiança **ou** retirar Kelly probabilístico do primeiro
  experimento — **concluído pela segunda via**. O Kelly sobre `confidence` saiu
  do caminho científico: o `LLMParticipant` usa `sizing_mode="qualitative"`, o
  gestor de portfólio responde um schema sem campo de tamanho e o peso alvo vem
  de política determinística (`FixedTargetSizing`). `calculate_kelly_size`
  continua existindo e ativa apenas no modo `legacy_confidence_kelly`, que serve
  o `AgentBacktestEngine` e o `DailyAgentRunner`. A calibração empírica de
  `confidence` **não** foi feita e continua fora do experimento v1 — ela é
  ablation futura, não pendência bloqueante.
- [ ] Evoluir o participante LLM para carteira multi-ativo (contrato de
  carteira-alvo completa já implementado e testado).
- [ ] Corrigir o dry-run para separar chamadas lógicas, externas e cache hits.

**Critério de saída:** uma execução pequena pode ser reproduzida pelo manifest,
tem custo conhecido e não perde votos ou atribuição de telemetria por corrida.

Estado: a **atribuição por corrida está resolvida** e a **reprodução exata está
resolvida por replay do trace**, não por reexecução contra o provedor — mesma
spec com LLM ao vivo continua sem garantir resposta idêntica. Custo conhecido
segue pendente.

## 7. Protocolo experimental

**PRÓXIMO MARCO DO PROJETO: `Freeze EXPERIMENT PROTOCOL v1`.** A infraestrutura
experimental e a metodologia de decisão do participante LLM estão resolvidas; o
desenho científico está formalizado em
[`EXPERIMENT_PROTOCOL.md`](EXPERIMENT_PROTOCOL.md). O que resta é decisão
científica da dupla/orientador, não código.

O desenho aprovado é calibração retrospectiva do sistema seguida de avaliação
causal pseudo-live, e não TRAIN/TEST clássico — o LLM chega pré-treinado e o
experimento v1 não faz fine-tuning:

```text
SYSTEM CALIBRATION -> FREEZE -> PSEUDO-LIVE VALIDATION -> FINAL TEST -> LIVE/SHADOW
```

O freeze é o que separa calibração de avaliação e é o controle contra
overfitting dos pesquisadores. Ele se subdivide nas decisões pendentes abaixo.

### 7.1 Seleção das janelas experimentais

- [ ] Selecionar os Calibration Cases, cobrindo mais de um regime de mercado
  (alta, baixa, lateral, volatilidade alta/baixa, choques macro, eventos
  políticos, juros, commodities quando aplicável).
- [ ] Definir a quantidade de Calibration Cases.
- [ ] Definir o período de PSEUDO-LIVE VALIDATION, sem interseção com a
  calibração.
- [ ] Definir o FINAL TEST PERIOD, separado de calibração e validação.
- [ ] Definir Walk-Forward como análise de robustez, não como desenho principal.

### 7.2 Parâmetros a congelar

- [ ] Congelar `long_target_weight` (hoje apenas default técnico `0.25`) e a
  política de sizing do experimento v1.
- [ ] Congelar `decision_frequency`.
- [ ] Congelar prompts, papéis, `analyst_count`, `consensus_threshold` e
  temperaturas.
- [ ] Congelar provider/model e política de seeds/estocasticidade.
- [ ] Congelar universo, snapshot, dados e features.
- [ ] Congelar a parametrização exata da janela base de mercado `>= 2 anos`
  (calendário x pregões, mínimo x máximo, sessões faltantes).
- [ ] Congelar custos, taxa livre de risco e benchmark de mercado.
- [ ] Definir a métrica primária e separar diagnóstico de decisão de performance
  de carteira.
- [ ] Aprovar ablations e análise estatística antes de observar o FINAL TEST.
- [ ] Versionar prompts e snapshots.

### 7.3 Desenho da Historical Memory

Fora do caminho crítico do freeze v1; entra no protocolo apenas se for ativada.

- [ ] Definir a política de recuperação (quando o agente consulta e o que
  recebe).
- [ ] Definir o schema de proveniência temporal com `available_at`, garantindo
  `available_at <= decision_time`.
- [ ] Definir o tratamento de hindsight em documentos retrospectivos.
- [ ] Definir algoritmo de retrieval, embeddings e armazenamento.
- [ ] Desenhar a ablation `base context` vs `base context + historical memory`.

## 8. Ablation Study

Experimento planejado para identificar qual componente realmente acrescenta
valor, sempre sob a mesma especificação:

```text
A — quantitativos clássicos
B — agente técnico único
C — ensemble técnico
D — ensemble + risk manager
E — sistema completo
F — local vs cloud
```

Opcional posteriormente:

```text
G — roteamento híbrido local/cloud
H — sistema completo + Historical Memory
```

A ablation `H` só existe se a Historical Memory for implementada, e deve isolar
exclusivamente a disponibilidade/política de recuperação histórica, mantendo
dados recentes, modelo, prompts-base, quorum, risco, sizing, Arena, custos e
período idênticos.

**STATUS: proposta / pendente de congelamento.** Variantes, número de seeds e
comparações estatísticas devem ser aprovados no protocolo.

## 9. Resultados científicos

- [ ] Executar a PSEUDO-LIVE VALIDATION após o congelamento, sem alterar o
  sistema com base nos seus resultados.
- [ ] Executar o FINAL TEST após o congelamento.
- [ ] Executar Walk-Forward.
- [ ] Reportar Sharpe líquido, Sortino, MaxDD, Turnover, custos e robustez.
- [ ] Fazer análise estatística com premissas declaradas previamente.
- [ ] Analisar por subperíodo e por seed.
- [ ] Executar análise de sensibilidade a custos e parâmetros aprovados.
- [ ] Vincular cada tabela e figura a `run_id` e manifest reproduzível.

Resultado mock continua sendo demonstração técnica e nunca evidência científica.

## 10. Produto e visualização

O dashboard vem depois da validade experimental.

- [ ] Consultar catálogo por `run_id`, sem depender de um JSON monolítico.
- [ ] Impedir comparação de runs com specs diferentes.
- [ ] Exibir badges `MOCK`, `CALIBRATION`, `VALIDATION`, `FINAL TEST` e
  `LIVE/SHADOW`.
- [ ] Exibir custos, modelo e versão do prompt.
- [ ] Isolar jobs, status e logs; permitir cancelamento.
- [ ] Escapar conteúdo não confiável e evitar chamada paga acidental.

## 11. Monografia e defesa

Código, arquitetura, experimento, resultados e monografia devem descrever a
mesma realidade. A monografia não será alterada nesta reorganização.

Pendências conhecidas:

- [ ] Resolver grafo descrito como cíclico versus implementação linear.
- [ ] Resolver escopo principal de 2 ativos versus 10 ativos.
- [ ] Resolver marcadores `verify` e `remarks`.
- [ ] Corrigir descrições futuras de funcionalidades já existentes ou descrições
  como existentes de itens ainda planejados.
- [ ] Gerar tabelas e figuras apenas a partir dos manifests finais.

## 12. Backlog e trabalhos futuros

Fora do caminho crítico do primeiro experimento:

### P2/P3

- LoRA/fine-tuning — experimento opcional, não requisito da hipótese principal;
  o experimento v1 é explicitamente sem fine-tuning.
- Historical Memory: corpus com proveniência temporal, retriever e ablation
  correspondente (seção 7.3).
- Roteamento híbrido local/cloud.
- Modelos quantitativos auxiliares.
- Integração MT5.
- BRAPI para operação diária.
- Notícias e sentimento.
- Execução automática.
- Trading em tempo real.

## 13. Milestones

Sem datas até existir cronograma confirmado.

| Marco | Resultado esperado |
|---|---|
| M1 — Scientific Core | Dados, execução, custos e métricas canônicos e validados |
| M2 — Common Arena | Participantes sob o mesmo contrato, motor e `ExperimentSpec` |
| M3 — LLM Hardened | Concorrência, telemetria, custo e fail-closed confiáveis |
| M4 — Experimental Protocol Frozen | `Freeze EXPERIMENT PROTOCOL v1`: janelas, parâmetros e métricas aprovados antes da validação pseudo-live |
| M5 — Ablations Executed | Variantes executadas e rastreadas por manifest |
| M6 — OOS Scientific Results | Validação pseudo-live, FINAL TEST, Walk-Forward e análises concluídos |
| M7 — TCC Final | Código, evidências, monografia e defesa alinhados |
| M8 — Live / Shadow | Decisão para o próximo pregão real registrada antes da abertura e avaliada depois |

## Definição de pronto do primeiro experimento científico

Um resultado só entra na comparação principal quando usa snapshot validado e
imutável; universo, período, calendário, capital e custos idênticos; decisão em
`t` e execução em `t+1`; métricas canônicas sobre curva líquida; manifest com
versões, seeds, modelos e prompts; parâmetros congelados antes da validação
pseudo-live e do FINAL TEST; falhas
explícitas; e reprodução possível em outra máquina. Até lá, toda saída deve ser
rotulada **DEMONSTRAÇÃO TÉCNICA — NÃO CIENTÍFICA**.
