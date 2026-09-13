# Arquitetura do Hedge-Fund-Lab

Este documento registra primeiro a arquitetura que existe e depois a arquitetura
alvo. A separação evita redesenhar diretórios antes de corrigir o contrato
experimental central.

## Arquitetura atual

```text
yfinance ──> cache CSV mutável ──> OHLCV validado ──> limpeza/indicadores ──> PostgreSQL
                                      │                                      │
                                      └──> DatasetSnapshot imutável          │
                                           + manifest + SHA-256               │
                                                                              │
                         ┌─────────────────────────┴──────────────────────┐
                         │                                                │
              gerador do dashboard                           runner de agentes
                         │                                                │
          ┌──────────────┴──────────────┐                     dados de um ticker
          │                             │                                │
  3 estratégias single-asset   2 carteiras multi-ativo        quorum técnico (30)
          │                             │                                │
          └──────────────┬──────────────┘                         gestor de risco
                         │                                                │
                  dashboard/data.json                           gestor de portfólio
                         │                                                │
                 dashboard clássico                          execução em t+1 + JSON
```

São dois produtos paralelos:

1. um comparador clássico que gera um arquivo estático para o dashboard;
2. um backtest LLM single-asset com auditoria própria.

Eles compartilham dados, estruturas de custo/trade e o relógio conceitual
fechamento de `t` -> abertura de `t+1`, mas não compartilham o motor, a unidade
experimental ou o formato de resultado. Em paralelo, a arena já executa os cinco
benchmarks clássicos **e o participante LLM single-asset** pelo contrato comum
descrito abaixo; o dashboard e os dois runners LLM legados
(`AgentBacktestEngine` e `DailyAgentRunner`) continuam nos motores próprios e
permanecem disponíveis como caminhos operacionais.

## Componentes atuais

### Configuração e observabilidade

- `src/config.py`: settings globais carregadas no import a partir de `.env`.
- `src/logger.py`: logger raiz para console e arquivo.
- Limitação: settings e conexão são singletons; testes e múltiplos experimentos
  isolados exigem patching ou novos processos.

### Dados

- `src/pipeline/extract.py`: `yfinance`, retry e cache CSV mutável.
- `src/pipeline/snapshot.py`: cobertura por sessões locais e materialização
  imutável de CSVs com manifest, proveniência, qualidade e SHA-256. Lacunas ou
  datas inesperadas produzem `scientific_ready=false` sem fabricar barras.
  `load_dataset_snapshot`, `verify_snapshot_integrity` e `load_snapshot_frames`
  são a porta de entrada dos consumidores científicos: leem o artefato, conferem
  identidade e hashes e não tocam em rede nem no cache mutável.

O artefato tem **duas garantias distintas e complementares**:

```text
manifest identity          file integrity
(o que o artefato afirma)  (os bytes dos CSVs)
        │                          │
snapshot_id = timestamp    verify_snapshot_integrity
            + digest              tamanho + SHA-256
```

O `snapshot_id` é a âncora verificável da primeira. O digest é o SHA-256 do JSON
canônico do manifest **inteiro menos o próprio `snapshot_id`** — evitando
circularidade e, ao mesmo tempo, deixando de fora nenhum campo científico:
`source`, intervalos solicitado e efetivo, `tickers`, `files` (com `path`,
`size` e `sha256` declarados), `coverage`, `quality`, `calendar`, `pipeline` e
`code` entram todos na identidade. Em particular, `quality.scientific_ready` —
que o runner usa como gate — não pode ser editado sem quebrar o ID.

No carregamento os guards são fail-closed e nesta ordem: JSON válido, schema
suportado, identidade (formato do ID, digest recalculado, coerência entre o
prefixo temporal e `created_at`, e nome do diretório igual ao `snapshot_id`),
reconstrução do objeto; depois, no runner, `scientific_ready`, tamanho/SHA dos
arquivos e só então os frames. Manifest adulterado levanta
`SnapshotIdentityError`; CSV adulterado continua levantando
`SnapshotIntegrityError`. Uma garantia não substitui a outra.

Isso é tamper-evidence dentro do modelo do projeto — detecta adulteração e
incoerência do artefato. Não é assinatura criptográfica e não resiste a quem
recomputa o ID depois de editar o conteúdo.

`MANIFEST_SCHEMA_VERSION = 2` introduz essa garantia. Snapshots do schema 1 não
a possuem e são recusados por nome, pedindo regeneração pelo pipeline atual;
não existe migração que copie um manifest antigo e o declare confiável.
- `src/pipeline/transform.py` e `src/indicators/`: limpeza e features.
- `src/pipeline/load.py`: batch e upsert.
- `src/db/`: conexão e três modelos ORM.
- `src/pipeline/flows.py`: orquestração Prefect por ticker e `PipelineResult`
  explícito para sucesso total ou carga parcial.

O snapshot registra que `B3Calendar` usa regras locais e exceções explícitas;
ele não o apresenta como calendário histórico oficial. A validação contra uma
fonte oficial/versionada permanece requisito da arquitetura científica.

### Estratégias e execução clássica

- `src/strategies/`: interface de sinais e cinco classes. As classes
  `EqualWeight` e `MinVariance` desse diretório são versões single-asset
  conceituais e não alimentam o dashboard multi-ativo.
- `src/backtesting/engine.py`: execução single-asset na abertura seguinte ao sinal.
- `src/backtesting/portfolio.py`: contém outra interface de estratégia, as
  implementações multi-ativo realmente usadas, seu motor legado e os adaptadores
  que expõem essas mesmas estratégias como participantes da arena; pesos
  calculados no fechamento são executados na abertura seguinte.
- `src/backtesting/metrics.py` e `costs.py`: funções compartilhadas.

Há duplicação de conceitos: duas interfaces de estratégia, duas famílias de
Equal Weight/Mínima Variância e dois motores com semânticas diferentes.

### Arena incremental

`src/backtesting/arena.py` contém o contrato técnico mínimo e o executor comum.
Os cinco adaptadores clássicos vivem ao lado das estratégias que reutilizam:
`BuyAndHoldParticipant`, `SMACrossParticipant` e `BollingerParticipant` em
`src/strategies/`; `EqualWeightParticipant` e `MinVarianceParticipant` em
`src/backtesting/portfolio.py`.

```text
histórico copiado e truncado até close(t)
   (um DataFrame por ticker)
                  │
                  v
        MarketObservation
                  │
                  v
          Participant.decide
                  │
                  v
 OrderIntent(ticker, target_weight,
             decision_time)      — uma ou zero por ticker
                  │
                  v
 ExecutionEngine na abertura observada de t+1
   deltas -> vendas -> orçamento -> compras escalonadas
                  │
                  v
       Trade(s) + equity de carteira no fechamento
```

`OrderIntent` representa decisão, não execução. Preço, quantidade inteira,
custo e caixa resultante pertencem ao executor e aparecem apenas no `Trade`.
`MarketObservation` carrega somente informação de `t`: o participante não
conhece o horizonte do dataset e não consegue identificar a última sessão do
recorte. A elegibilidade de execução pertence ao executor, que associa cada
intenção à próxima abertura observada — e a descarta sem trade quando ela não
existe.
O executor reutiliza `CostModel` e o `Trade` já existente, rejeita
short/alavancagem e não lê arquivos de dados ou snapshots. Ele recebe os dados
já preparados, aceita `Mapping[ticker, DataFrame]` e devolve o `BacktestResult`
mínimo — `RunResult` continua sendo trabalho futuro e não foi antecipado. Os
três motores legados permanecem disponíveis e compatíveis como caminhos
operacionais.

No caminho multi-ativo o executor:

- ordena os tickers deterministicamente e usa a interseção dos calendários como
  calendário comum, sem forward-fill nem barra fabricada;
- calcula o patrimônio na abertura, converte pesos alvo em quantidades inteiras
  e deriva os deltas por ticker;
- executa as vendas antes das compras, para que o rebalance financie a si mesmo;
- quando o caixa não cobre todos os déficits, escalona todos os alvos de compra
  pelo mesmo fator e trunca — política técnica, determinística e independente da
  ordem dos tickers, obtida por busca binária sobre o custo reportado pelo
  `CostModel`;
- rejeita peso negativo, não finito ou soma acima de um, e mantém o caixa não
  negativo.

`OrderIntent` não declara direção. O participante expressa apenas a posição
alvo; comprar, vender ou não fazer nada é derivado na abertura de `t+1`, a
partir do delta entre a posição corrente e a quantidade alvo. Um gap overnight
pode inverter a operação sem que a intenção mude, e `Trade.type` registra o que
foi de fato executado.
O guard de `DatasetSnapshot.scientific_ready` pertence ao `ExperimentRunner`,
não ao executor: esta camada recebe DataFrames já preparados.

### Camada experimental

`src/experiments/` transforma a arena numa execução identificável. O runner não
contém regra de estratégia nem regra financeira: ele resolve o snapshot, monta
os objetos a partir da spec e delega tudo ao `ExecutionEngine`.

```text
DatasetSnapshot imutável (data/snapshots/<snapshot_id>)
        │  identidade do manifest + SHA-256 por arquivo
        v
ExperimentSpec  (snapshot_id, ParticipantSpec, capital, CostSpec, MetricSpec)
        │  spec_hash = SHA-256(canonical_json(spec))
        v
ExperimentRunner.run()
        ├── exige proveniência Git limpa ..... senão DirtyRepositoryError
        ├── carrega o manifest do snapshot
        │     └── identidade verificada ...... senão SnapshotIdentityError
        ├── exige scientific_ready ........... senão SnapshotNotReadyError
        ├── confere tamanho e hash dos CSVs .. senão SnapshotIntegrityError
        ├── CAPTURA SnapshotEvidence ......... manifest canônico congelado
        ├── resolve o universo efetivo
        ├── participant factory (registry) ... instância NOVA por run
        ├── CostSpec.build() -> CostModel
        └── ExecutionEngine(...).run()
        │
        v
RunResult (run_id, spec_hash, SnapshotEvidence, BacktestResult, métricas, custo)
        │
        v
ExperimentRunner.persist()  — não relê o snapshot
        │
        v
data/runs/<run_id>/{manifest.json, equity.csv, trades.csv}   publicação atômica
```

- `spec.py`: `ParticipantSpec`, `CostSpec`, `MetricSpec`, `ExperimentSpec`,
  `canonical_json` e `spec_hash`. Nenhum objeto vivo, nenhum caminho local.
  `ParticipantSpec.params` é copiado na construção e guardado como
  `MappingProxyType`: `frozen=True` congela o campo, não o dicionário que ele
  aponta. Nem mutar o dicionário original do chamador nem escrever em
  `participant.params[...]` altera a spec, de modo que uma `ExperimentSpec`
  criada tem identidade estável por toda a sua vida. `to_dict()` continua
  devolvendo um `dict` novo e JSON-serializável.
- `participants.py`: registry explícito dos cinco clássicos, do `llm_agent` e
  `build_participant`. Não existe import path arbitrário vindo de fora. A
  `ParticipantSpec` do `llm_agent` descreve provedor, modelo requisitado,
  retry, quorum, frequência de decisão e limites de risco e de portfólio como
  escalares JSON — tudo entra no `spec_hash` e no manifest. Credencial não entra: chave de API,
  token e header de autorização continuam sendo ambiente de execução e nunca
  são serializados em spec, manifest, log ou artefato de auditoria.
- `runner.py`: `ExperimentRunner` e `RunResult`.

`ExperimentSpec` carrega `snapshot_id`, não caminho: o diretório onde o snapshot
está é ambiente de execução e não pode alterar a identidade da spec. Por isso
`snapshot_dir`, `runs_dir` e `repository_dir` são argumentos do runner.

O universo efetivo é derivado deterministicamente, sem seleção dinâmica:
participantes single-asset declaram `ticker` nos parâmetros e recebem apenas
ele; participantes de carteira recebem todos os tickers do snapshot. Um ticker
pedido que não exista no snapshot é falha, não remoção silenciosa. O universo
entregue e a lista completa do snapshot ficam ambos no manifest.

Runs reproduzíveis exigem proveniência Git verificável e working tree limpa. O
guard é fail-closed estrito: exige commit conhecido **e** `git_dirty=false`.
Working tree suja, commit indeterminado e proveniência não verificável (sem Git
utilizável no diretório) são rejeitados igualmente, porque nenhum dos três
permite reproduzir o run a partir de um commit; a mensagem de erro distingue os
casos. A mesma regra decide `reproducibility.clean_source`, então guard e
manifest não podem divergir.

`allow_dirty=True` é o escape explícito de desenvolvimento e cobre ambos —
libera a execução, grava `reproducibility.clean_source=false` no manifest e não
entra na `ExperimentSpec` nem altera o `spec_hash`, porque é política
operacional e não parâmetro experimental. Commit desconhecido continua `null`:
nada é inventado. A proveniência é conferida no início do `run()`, antes de
carregar dados ou construir participante, e o valor conferido é o que vai para
o manifest.

`spec_hash` responde "estes dois runs usaram a mesma configuração?"; `run_id`
identifica a execução concreta. Dois runs da mesma spec têm o mesmo `spec_hash`
e `run_id` diferentes. O manifest publicado prende essa coerência ao artefato:
`spec_hash == SHA-256(canonical_json(manifest["experiment_spec"]))`, verificável
sem confiar no runner que o escreveu.

A proveniência do snapshot é capturada **durante o `run()`**, no mesmo ponto em
que o artefato passa pelos guards e antes de qualquer execução. `RunResult`
carrega um `SnapshotEvidence` — `snapshot_id`, `schema_version`,
`identity_digest`, caminho e o manifest verificado em JSON canônico — e não uma
referência para estruturas mutáveis do `DatasetSnapshot`. `persist()` não relê o
diretório: alterar (ou apagar) o snapshot entre `run()` e `persist()` não
reescreve retroativamente o que o manifest do run afirma ter sido executado. A
regra é que nunca se registre B como executado quando A foi o snapshot
efetivamente entregue ao `ExecutionEngine`.

### Sistema multiagente

- `src/agents/state.py`: contratos Pydantic e estado LangGraph.
- `src/agents/participant.py`: adaptador do grafo para o contrato da arena.
- `technical_analyst.py`: chamada individual legada e ensemble concorrente.
- `risk_manager.py`: regras determinísticas e parecer LLM.
- `portfolio_manager.py`: decisão do gestor em dois modos explícitos —
  `qualitative` (científico, sem quantidade) e `legacy_confidence_kelly`
  (operacional, `confidence` -> Kelly -> teto de posição).
- `graph.py`: grafo linear.
- `llm_client.py`: mock, retry, cache e cliente HTTP real.
- `llm_trace.py`: identidade de chamada, gravação ao vivo e replay
  determinístico (`RecordingLLMClient`, `ReplayLLMClient`).
- `src/artifacts.py`: contrato genérico de evidência publicável de participante
  (`RunArtifact`, `RunArtifactProvider`), fora de `agents` e de `experiments`
  porque os dois lados precisam dele.
- `src/backtesting/agent_engine.py`: relógio fechamento -> próxima abertura.
- `src/backtesting/daily_agent.py`: estado persistente, reconciliação da previsão
  pendente e avanço de uma sessão por execução.
- `src/backtesting/b3_calendar.py`: calendário local de sessões por regras
  recorrentes e exceções explícitas.

O grafo atual é:

```text
START
  │
  v
30 analistas técnicos concorrentes
  │  25/30 + todos válidos por padrão
  v
gestor de risco
  ├── VETADO ──> END (sem FinalDecision)
  └── APROVADO
          │
          v
   gestor de portfólio
          │
          v
         END
```

No caminho científico o gestor de portfólio devolve `PortfolioAction`
(qualitativa) e o grafo termina sem `FinalDecision`; no caminho legado ele
devolve `FinalDecision` com `position_size`. O modo é declarado em
`PortfolioConfig.sizing_mode` e nunca inferido.

O primeiro estágio é um quorum interno, então a descrição mais precisa é
**três estágios decisórios, sendo o primeiro um ensemble de 30 amostras**. São
30 amostras do mesmo papel, do mesmo prompt e do mesmo modelo, variando
temperatura e seed registrado — não 30 especialistas independentes.

### Participante LLM na arena

`src/agents/participant.py` liga esse grafo à arena. Ele é um adaptador: não
reimplementa schema, cliente, prompt, nó nem grafo, e não reutiliza nada do
lado de execução do `AgentBacktestEngine`.

```text
DatasetSnapshot
        v
ExperimentRunner  (spec kind="llm_agent")
        v
LLMParticipant.decide(MarketObservation)   <- só informação de close(t)
        v
AgentState
        v
quorum técnico (LLM)        -> COMPRA / VENDA / MANTER
        v
gestor de risco (regras + LLM) -> APROVADO / VETADO
        v
gestor de portfólio (LLM)   -> PortfolioAction: decisão QUALITATIVA
        v
política determinística de sizing  -> target_weight
        v
carteira-alvo completa sobre o universo observado
        v
OrderIntent(target_weight)
        v
ExecutionEngine na abertura de t+1  -> Trade
        v
RunResult + manifest
```

**O LLM decide; o LLM não dimensiona.** Essa separação é a regra metodológica
desta camada. O modelo participa de todas as etapas de *qualidade da decisão* —
ler indicadores, formar consenso, aprovar risco, consolidar direção — e não
participa de nenhuma etapa de *tamanho da posição*. A exposição alvo sai de uma
política determinística e configurável, fora do alcance do modelo.

A separação é a regra: **a stack de agentes decide, a arena executa.** O
participante termina em peso alvo; quantidade inteira, direção, preço de
execução, custo, caixa e `Trade` continuam sendo exclusividade do
`ExecutionEngine`.

Três decisões desta camada merecem registro:

1. **Indicadores recalculados sobre histórico truncado.** O snapshot guarda
   OHLCV puro, e o `AgentState` precisa dos oito indicadores que o motor legado
   lia de colunas pré-calculadas. O participante chama a mesma
   `DataTransformer.calculate_indicators` do pipeline sobre `history` até `t`.
   Como `rolling` e `ewm(adjust=False)` são varreduras para frente, o valor em
   `t` é idêntico ao da série inteira — a diferença é que não existe barra
   futura para observar.

2. **Decisão qualitativa e sizing determinístico.** O gestor de portfólio do
   caminho científico responde `PortfolioAction` — `decision` e `reasoning`,
   sem nenhum campo de quantidade. O peso alvo sai de `FixedTargetSizing`:

   ```text
   COMPRA aprovada -> target_weight = long_target_weight
   VENDA  aprovada -> target_weight = 0.0
   MANTER          -> nenhuma intenção
   veto de risco   -> nenhuma intenção
   ```

   Nada nessa tradução olha `confidence`, caixa, posição corrente ou próxima
   abertura. Duas execuções que só diferem na confiança reportada produzem
   exatamente o mesmo peso, e isso está preso por teste.

   **Por que não é mais Kelly.** A cadeia anterior era
   `confidence -> Kelly -> max_position_size -> position_size -> peso`. Ela
   tratava a confiança textual do LLM como probabilidade empírica de vitória,
   o que o projeto não sustenta sem calibração. `calculate_kelly_size` continua
   existindo, e continua sendo usada — no modo `legacy_confidence_kelly`, que
   serve o `AgentBacktestEngine` e o `DailyAgentRunner`, e que é o default de
   `PortfolioConfig` justamente para que esses runners não troquem de política
   em silêncio. O `LLMParticipant` força `sizing_mode="qualitative"` e não
   expõe parâmetro algum de Kelly.

   **`long_target_weight` não está congelado.** O default técnico é `0.25` — o
   antigo teto `max_position_size`, adotado só para manter a API conveniente. O
   valor científico é `TBD` no protocolo experimental v1. Ele é validado
   (`0 < w <= 1`, e `w <= risk_max_concentration`, porque um alvo acima do
   limite duro mandaria construir exatamente a exposição que o gestor de risco
   existe para vetar), entra na `ParticipantSpec`, no `spec_hash` e no manifest.

   **`COMPRA` é estado desejado, não ordem de compra.** Emitir o alvo significa
   querer estar exposto naquele peso. Com exposição corrente abaixo do alvo o
   executor compra; depois de um gap de alta que empurre a exposição acima do
   alvo, o mesmo alvo exige vender. A direção financeira nasce na abertura de
   `t+1` e pertence à arena — o participante não declara `side`. Duas
   diferenças seguem declaradas: o peso alcançado difere do alvo porque a
   execução acontece a outro preço, e o alvo não desconta custos, que pertencem
   ao executor.

   A política é um ponto de troca, não uma fórmula embutida: `FixedTargetSizing`
   é a primeira de uma família prevista (`fixed_target`, `volatility_target`,
   `calibrated_kelly`). As outras **não** existem e não são simuladas.

3. **Frequência de decisão preservada.** `decision_frequency` migra a opção de
   mesmo nome do `AgentBacktestEngine`: só as sessões cujo índice é múltiplo
   dela chamam o grafo; as demais não tocam o provedor e não emitem intenção. A
   regra é do participante, não do runner nem do executor — o motor financeiro
   continua ignorante da frequência. O contador é interno, começa em zero a
   cada instância e é reiniciado quando a observação mostra a primeira sessão
   do recorte; ele nunca deriva do tamanho do dataset, da próxima sessão ou da
   distância até o fim.

   Uma divergência em relação ao motor legado é deliberada e declarada: lá a
   última barra era sempre elegível (`is_last_day`), o que exige saber que o
   recorte acabou. Essa informação não existe no contrato da arena e o
   participante não pode reconstruí-la.

4. **`MANTER` é ausência de ordem, não alvo igual ao peso corrente.** Reemitir
   o peso observado em `close(t)` faria o executor recalcular a quantidade alvo
   sobre o patrimônio da abertura seguinte; depois de um gap, isso exigiria
   comprar ou vender. "Não fazer nada" precisa ser a ausência de ordem, como no
   motor legado. Essa regra é do participante single-asset migrado e **não**
   enfraquece o contrato de carteira-alvo completa do futuro LLM multi-ativo:
   uma decisão de carteira continua obrigada a declarar todos os tickers.

5. **Falha não vira `MANTER`.** Uma casca `FailureRecordingClient` observa o
   limite do provedor por fora do retry. Timeout, erro de provedor, JSON
   inválido, schema inválido e quorum incompletado por falhas levantam
   `LLMDecisionError` e derrubam o run. Quorum sem supermaioria com todos os
   votos válidos continua sendo `MANTER`: ali não houve falha nenhuma, é a
   regra de agregação da metodologia atual.

#### Trace de chamadas e replay determinístico

Um run com provedor externo **não é reprodutível por configuração**. Mesma
spec, mesmo snapshot, mesmo `model` e mesma `temperature` podem devolver textos
diferentes. A reprodutibilidade forte do projeto passa a ser feita em dois
tempos, e é essa distinção que sustenta o capítulo experimental do TCC.

```text
LIVE

MarketObservation(close(t))
        v
LLMParticipant.decide       -> begin_session(t)
        v
RecordingLLMClient          <- fronteira que o grafo enxerga
        v
FailureRecordingClient
        v
RetryingLLMClient
        v
provedor (agent_router / mock)
        v
LLMCallRecord por chamada lógica
        v
decision -> target_weight -> Arena -> RunResult
        v
data/runs/<run_id>/llm_calls.jsonl  (+ hash no manifest)
```

```text
REPLAY

llm_calls.jsonl
        v
ReplayLLMClient    <- sem rede, sem provedor, sem credencial
        v
mesma pilha, mesmo grafo, mesmo participante
        v
mesmas decisões -> mesma Arena -> mesmos trades, equity e métricas
```

A **ordem dos wrappers é material**. `RecordingLLMClient` fica acima do retry,
de modo que cada registro descreve *uma chamada lógica* e sabe quantas
tentativas HTTP ela custou (`attempt_count`), em vez de gerar um registro por
tentativa; e acima do `FailureRecordingClient`, de modo que a falha final entre
no trace antes de subir para o participante. Uma tentativa recuperada pelo
retry continua não sendo falha — aparece apenas como `attempt_count > 1`.

Cada `LLMCallRecord` registra `call_id`, `sequence`, `stage`
(`technical_analyst` / `risk_manager` / `portfolio_manager`), `analyst_id`
quando é ensemble, `decision_session`, `provider`, `requested_model`, os dois
prompts **lógicos completos** mais seus SHA-256, `response_schema` com
`response_schema_sha256`, `requested_options`, `transport_options`,
`started_at`, `duration_ms`, `attempt_count`, `status`, erro quando houver, a
resposta validada (`model_dump(mode="json")`), e — quando o provedor entrega —
`raw_response`, `token_usage`, `provider_endpoint` e
`transport_system_prompt_sha256`.

**Prompt lógico e prompt de transporte são coisas diferentes.** O
`AgentRouterLLMClient` serializa `model_json_schema()` do `response_schema`
dentro do system prompt antes de montar o corpo HTTP:

```text
system_prompt (lógico)  +  model_json_schema(response_schema)
        v
system prompt de TRANSPORTE, que é o que vai no corpo HTTP
```

Por isso o trace não chama `system_prompt` de "texto enviado ao provedor", e
por isso `response_schema_sha256` entra na identidade: o nome da classe não
identifica o contrato, e o contrato viaja junto na requisição. Afrouxar um
limite de `Field` sem renomear a classe muda o que foi perguntado ao modelo, e
o replay precisa recusar isso — antes desta correção ele aceitava em silêncio.

Três escolhas explicam o resto do desenho:

- **`stage` e `decision_session` são declarados, não deduzidos.** O papel vem
  de um `LLMCallMetadata` que o próprio nó passa na chamada, sem contaminar o
  prompt; a sessão vem de `begin_session(observation.session)`, chamado pelo
  participante, que é quem a conhece. Nada é reconstruído depois lendo texto de
  prompt ou ordem de chamadas.
- **Identidade não inclui relógio.** `started_at` e `duration_ms` são medições
  da execução, não da pergunta, e ficam fora da identidade usada pelo replay —
  reproduzir não pode falhar porque o tempo passou. Divergência de prompt,
  modelo, provedor, opções solicitadas, schema, papel, analista ou sessão, sim,
  falha com `ReplayMismatchError`.
- **Contadores por invocação, não por cliente.** O número de tentativas vive em
  um rascunho criado a cada `generate` e guardado em `ContextVar`, que o
  `asyncio` copia por task. Os 30 analistas concorrentes do ensemble não podem
  publicar o `attempt_count` uns dos outros.
- **O trace é canônico por ordem de emissão, não de conclusão.** `sequence` é
  atribuído de forma síncrona no momento em que a chamada é emitida, antes de
  qualquer `await` que suspenda, e `records` publica ordenado por ele. Entre os
  analistas paralelos, portanto, **quem terminou primeiro não influencia o
  arquivo**: só a ordem em que `asyncio.gather` criou as tarefas, que é a ordem
  dos argumentos. A ordem **entre estágios** (`technical` -> `risk` ->
  `portfolio`) é sequencial e continua sendo material.

O trace é `llm_calls.jsonl`: UTF-8, LF, um JSON por chamada lógica, chaves
ordenadas, com `schema_version` próprio — independente de
`RUN_MANIFEST_SCHEMA_VERSION` e de `SPEC_SCHEMA_VERSION`.

#### Evidência de participante no run

O runner **não conhece o `LLMParticipant`**. Existe um contrato genérico e
pequeno em `src/artifacts.py`:

```text
Participant que também é RunArtifactProvider
        v
run_artifacts() -> tuple[RunArtifact, ...]   (bytes já congelados)
        v
RunResult.artifacts
        v
persist() escreve os bytes + manifest registra path/schema_version/sha256
```

Pelo mesmo princípio do `SnapshotEvidence`, a evidência é congelada logo após
o motor terminar; `persist()` escreve o que foi capturado e não volta a
perguntar nada ao participante nem ao provedor. O `sha256` é calculado sobre os
bytes publicados, então "manifest íntegro com artefato adulterado" é um estado
detectável. Participantes clássicos não implementam nada disso e seguem
publicando apenas `equity.csv`, `trades.csv` e `manifest.json`, com
`participant_artifacts` vazio.

#### Contrato de carteira-alvo completa

Para o caminho multi-ativo, a regra já está implementada e testada em
`target_portfolio_to_intents`: **uma decisão de carteira declara um peso para
cada ativo do universo observado.**

```text
ticker omitido   -> DECISÃO INVÁLIDA
ticker extra     -> DECISÃO INVÁLIDA
ticker duplicado -> DECISÃO INVÁLIDA
peso NaN/Inf     -> DECISÃO INVÁLIDA
peso < 0 ou > 1  -> DECISÃO INVÁLIDA
soma > 1 + tol   -> DECISÃO INVÁLIDA
```

Omitir um ativo não significa manter posição, não significa peso zero e não
autoriza o executor a inferir nada. Peso zero é decisão explícita e precisa ser
escrita. Nada é normalizado silenciosamente; o caixa é implícito em
`1 - Σ pesos`.

Ausência de intenção é coisa diferente de decisão parcial: `MANTER`, veto de
risco e ausência de decisão final devolvem lista vazia, ou seja, *nenhuma
decisão nova*, e o executor mantém a posição. É a mesma semântica que os cinco
participantes clássicos já usam e que o motor legado aplicava.

#### Limitação declarada: single-asset

A stack de agentes atual é single-asset por construção — `AgentState` descreve
um ticker, um preço e uma posição escalar, e não existe etapa de construção de
carteira entre ativos. O `LLMParticipant` **recusa explicitamente** um universo
com mais de um ativo em vez de rodar um laço independente por ticker e
normalizar pesos: isso seria outra estratégia, sem raciocínio cross-asset e sem
sustentação no código ou na metodologia atual.

A evolução multi-ativo já tem o contrato pronto e só precisa substituir a
origem dos pesos, porque a decisão single-asset já passa pelo mesmo
`target_portfolio_to_intents` — o universo de um ativo é o caso degenerado da
carteira completa.

### Apresentação

- `scripts/generate_dashboard_data.py`: consulta, backtests, agregação e
  serialização estão concentrados em um script grande.
- `dashboard/index.html` + `app.js`: dashboard clássico Chart.js.
- `dashboard/lab.html`: formulário e terminal do runner LLM.
- `dashboard/server.py`: arquivos estáticos, SSE e disparo de subprocessos.

## Contrato experimental que falta

O objetivo do projeto requer uma única cadeia capaz de receber qualquer
participante e executar todos sob as mesmas condições:

```text
DatasetSnapshot imutável
        │
        v
features disponíveis até t
        │
        v
Participant.decide(state_t)
        │
        v
ordens normalizadas
        │
        v
ExecutionEngine na abertura de t+1
        │
        v
custos, caixa e posições
        │
        v
RunResult + auditoria + métricas canônicas
```

`Participant` pode ser Buy & Hold, SMA, Bollinger, Equal Weight, Mínima
Variância ou o grafo LLM. O adaptador muda; dados, execução, custos e métricas não.

## Ciclo operacional diário desejado

O produto-alvo não toma todas as decisões de uma vez. Ele avança um pregão por
vez, sempre tentando decidir hoje o que deverá ser executado na manhã do próximo
pregão.

```text
fechamento confirmado do pregão t
              │
              v
ingestão e validação da barra final de t
              │
              v
snapshot imutável com informação disponível até t
              │
              v
clássicos e LLM geram decisões para o próximo pregão
              │
              v
risco valida + portfólio converte em ordens pendentes
              │
              v
abertura do próximo pregão t+1: execução/simulação
              │
              v
reconciliação, marcação a mercado e novo ciclo após o fechamento
```

Em termos operacionais, uma execução feita após o fechamento do dia 24 produz
uma previsão com `as_of=24`. Na abertura seguinte, ela é executada ou simulada
com o preço realmente disponível. Após o fechamento desse novo pregão, o sistema
incorpora a barra observada e produz a próxima previsão. “Amanhã” significa
**próxima sessão da bolsa**, não simplesmente data civil + 1.

No replay histórico já implementado, a sessão-alvo é a próxima barra observada,
o que resolve naturalmente sexta-feira para segunda-feira. Na última barra ela
fica nula, pois não há futuro conhecido. No modo diário, `B3Calendar` já preenche
a próxima sessão antes que sua barra exista. Como ele usa regras locais e
exceções explícitas, o uso científico ainda exige validação e versionamento
contra o calendário oficial aplicável ao período.

### Dois modos, a mesma semântica

1. **Backtest/replay histórico**: percorre barras antigas em ordem. A decisão de
   `t` só pode usar dados até `t` e é executada com a abertura histórica de
   `t+1`.
2. **Diário/paper trading**: a última decisão não tem ainda a abertura de `t+1`.
   Ela fica persistida como previsão/ordem pendente e será reconciliada quando o
   próximo pregão começar.

O backtest não apaga a previsão da última barra, porque ela representa o uso
diário real, nem a conta como trade, retorno ou acerto. O `DailyAgentRunner` já
persiste essa previsão entre processos, reconcilia sua sessão-alvo e impede mais
de uma previsão pendente. O ciclo mínimo atualmente implementado é:

```text
PREDICTED -> EXECUTED
          └-> REJECTED
MANTER    -> NO_ACTION
```

Estados mais ricos como `SCHEDULED`, `RECONCILED`, `CANCELLED` e `EXPIRED`
continuam sendo arquitetura-alvo; o runner atual usa os estados mínimos acima e
permanece separado da arena comum.

### Arena incremental

Todos os participantes devem produzir sua decisão no mesmo fechamento e receber
a mesma abertura seguinte. A arena acumula, pregão após pregão:

- previsão e ordens de cada participante;
- preço e custo efetivos de execução;
- caixa, posições e patrimônio após a execução;
- divergência entre os 30 votos do quorum;
- métricas acumuladas, sem recalcular ou reescrever decisões passadas.

O backtest serve para acelerar esse relógio sobre dez anos de histórico. O modo
diário avança exatamente um passo do mesmo motor.

## Arquitetura alvo

```text
                         ExperimentSpec
        (snapshot, universo, split, capital, custos, calendário, seeds)
                                │
                                v
                    Unified Experiment Runner
                                │
          ┌─────────────────────┼─────────────────────┐
          v                     v                     v
  Classic Participant   Allocation Participant   LLM Participant
          └─────────────────────┼─────────────────────┘
                                v
                     Unified Execution Engine
                     decisão t / execução t+1
                                │
                                v
                RunResult + Event/Audit Records
                                │
                 ┌──────────────┴──────────────┐
                 v                             v
          Canonical Metrics              Dashboard/Exports
```

Dentro de `LLM Participant`:

```text
Universe snapshot em t
          │
          v
Quorum técnico de 30
          │
          v
Risk policy determinística -> parecer LLM opcional
          │
          v
Portfolio construction multi-ativo
          │
          v
ordens alvo normalizadas
```

### Responsabilidades da arquitetura alvo

| Componente | Responsabilidade | Não deve fazer |
|---|---|---|
| Data snapshot | Fixar dados, fonte, intervalo, versão e validações | Decidir estratégia |
| Feature pipeline | Calcular somente com informação disponível até `t` | Executar ordem |
| Participant | Produzir intenção/ordens alvo a partir do estado | Alterar caixa diretamente |
| Execution engine | Relógio, lotes, caixa, posições, custos e slippage | Conhecer prompts |
| Experiment runner | Aplicar mesma especificação a todos | Calcular métrica ad hoc por participante |
| Metrics | Calcular resultados canônicos e comparáveis | Ler dados futuros |
| Audit store | Persistir eventos e identidade do run | Ser apenas texto de log |
| Dashboard | Consultar runs e exibir resultados | Ser o orquestrador científico |

## Organização de código recomendada

Não é recomendável mover o repositório inteiro agora. Primeiro deve existir um
motor unificado com testes. Depois, a estrutura pode convergir para:

```text
src/
├── config.py
├── data/              # extração, validação, snapshots, features e storage
├── strategies/
│   ├── base.py        # um único contrato de participante
│   ├── classical/     # buy-hold, SMA, Bollinger, equal weight, min variance
│   └── multiagent/    # adaptador do grafo para o contrato comum
├── execution/         # ordens, broker simulado, custos e motor único
├── agents/            # quorum, risco, portfólio, clientes e contratos LLM
├── experiments/       # specs, splits, arena, manifests e runs
└── reporting/         # métricas, tabelas e payloads do dashboard
```

Migração mínima, na ordem:

1. corrigir o motor existente e explicitar o contrato temporal;
2. criar um resultado canônico e adaptar participantes;
3. criar a arena;
4. só então mover módulos e eliminar implementações duplicadas.

## Invariantes obrigatórios

1. Nenhum participante observa informação posterior ao instante de decisão.
2. Todos competem no mesmo snapshot, calendário, universo, capital e período.
3. Toda ordem usa o mesmo modelo de execução e custo.
4. Caixa não fica negativo e posição respeita lote/short configurado.
5. Toda métrica vem do mesmo módulo e mesma curva líquida.
6. Todo run possui configuração imutável, hashes, seeds e versões.
7. Prompt e modelo são congelados antes do conjunto de teste.
8. LLM pode sugerir; regras determinísticas preservam limites financeiros.
9. Falha de dados, rede ou validação é explícita e fail-closed.
10. Resultado mock nunca é misturado a resultado científico.
