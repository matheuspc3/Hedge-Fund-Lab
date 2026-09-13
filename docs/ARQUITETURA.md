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
benchmarks clássicos pelo contrato comum descrito abaixo; o dashboard e o
participante LLM continuam nos motores legados.

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
  os hashes e não tocam em rede nem no cache mutável.
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
        │  scientific_ready + SHA-256 por arquivo
        v
ExperimentSpec  (snapshot_id, ParticipantSpec, capital, CostSpec, MetricSpec)
        │  spec_hash = SHA-256(canonical_json(spec))
        v
ExperimentRunner
        ├── exige proveniência Git limpa ..... senão DirtyRepositoryError
        ├── carrega o manifest do snapshot
        ├── exige scientific_ready ........... senão SnapshotNotReadyError
        ├── confere tamanho e hash dos CSVs .. senão SnapshotIntegrityError
        ├── resolve o universo efetivo
        ├── participant factory (registry) ... instância NOVA por run
        ├── CostSpec.build() -> CostModel
        └── ExecutionEngine(...).run()
        │
        v
RunResult (run_id, spec_hash, BacktestResult, métricas canônicas, custo total)
        │
        v
data/runs/<run_id>/{manifest.json, equity.csv, trades.csv}   publicação atômica
```

- `spec.py`: `ParticipantSpec`, `CostSpec`, `MetricSpec`, `ExperimentSpec`,
  `canonical_json` e `spec_hash`. Nenhum objeto vivo, nenhum caminho local.
- `participants.py`: registry explícito dos cinco clássicos e `build_participant`.
  Não existe import path arbitrário vindo de fora.
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
e `run_id` diferentes.

### Sistema multiagente

- `src/agents/state.py`: contratos Pydantic e estado LangGraph.
- `technical_analyst.py`: chamada individual legada e ensemble concorrente.
- `risk_manager.py`: regras determinísticas e parecer LLM.
- `portfolio_manager.py`: Kelly/limites e decisão LLM.
- `graph.py`: grafo linear.
- `llm_client.py`: mock, retry, cache e cliente HTTP real.
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

O primeiro estágio é um quorum interno, então a descrição mais precisa é
**três estágios decisórios, sendo o primeiro um ensemble de 30 amostras**.

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
