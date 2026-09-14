# Estado atual do Hedge-Fund-Lab

Documento vivo, descrito sobre o estado versionado da branch `#1-Update` no
commit `139a0a9` (13/09/2026). A baseline original foi auditada em **10/09/2026**
e desde então o documento incorpora os fatos introduzidos pelos commits
seguintes — motor experimental comum para o participante LLM, trace/replay
auditável, desacoplamento entre decisão do LLM e sizing científico e a
formalização do protocolo de calibração retrospectiva. Portanto **nem todo o
conteúdo abaixo corresponde à auditoria de 10/09**: o texto descreve o HEAD
atual, e medições antigas continuam identificadas com a data em que foram
observadas.

O objetivo é responder até onde o projeto chega hoje e evitar que planos antigos
sejam confundidos com implementação. Capacidades e limitações descritas como
parte do sistema são evidência do repositório; contagens de banco, execuções e
medições identificadas como locais são evidência observada no ambiente daquela
auditoria e não conteúdo versionado no Git.

## Conclusão executiva

O projeto já é um bom **protótipo técnico de laboratório quantitativo**. Ele
coleta e persiste dados, calcula indicadores, executa cinco benchmarks clássicos,
possui dashboard e contém um fluxo LLM auditável de três estágios cujo primeiro
estágio é um quorum configurável de 30 chamadas.

Ele ainda **não é a arena científica descrita como objetivo**. Um caminho comum
preliminar já recebe `MarketObservation`, chama `Participant`, normaliza a
decisão como `OrderIntent` e executa os cinco benchmarks clássicos — single e
multi-ativo — pelo mesmo `ExecutionEngine`. **O participante LLM entrou nesse
mesmo caminho**, na versão single-asset: `ExperimentSpec(kind="llm_agent")` ->
`ExperimentRunner` -> `LLMParticipant` -> `ExecutionEngine` -> `RunResult` ->
manifest, com os mesmos guards de snapshot e de proveniência Git. O desenho
experimental foi formalizado em `EXPERIMENT_PROTOCOL.md` como calibração
retrospectiva do sistema seguida de avaliação pseudo-live, mas nenhuma data de
calibração, validação ou teste foi selecionada; não existem walk-forward,
análise estatística nem protocolo congelado, e o hardening do cliente LLM
continua pendente. Portanto,
os números exibidos no dashboard e os JSONs de agentes são demonstrações
técnicas, não evidência de que uma abordagem venceu outra.

## O que existe hoje

| Área | Status | O que realmente faz |
|---|---|---|
| Dados | Implementado com lacunas | Baixa OHLCV diário pelo `yfinance`, mantém cache CSV mutável por ticker, valida estrutura, finitude e consistência OHLCV e pode materializar `DatasetSnapshot` imutável com identidade verificável do manifest, hashes por arquivo, proveniência e cobertura pelo calendário local. |
| Persistência | Implementado | Tabelas de ativos, cotações e indicadores, com unicidade por ativo/data e atualização em conflito nos caminhos principais. |
| Indicadores | Implementado | SMA 50/200, Bollinger 20/2, RSI 14 e MACD 12/26/9. |
| Estratégias clássicas | Implementado | Buy & Hold, SMA Cross e Bollinger single-asset; Equal Weight e Mínima Variância multi-ativo. |
| Backtest clássico | Bloqueado para ciência | Single e multi-asset decidem com dados até o fechamento de `t`, executam na abertura observada de `t+1`, calculam custos sobre o notional e preservam caixa não negativo. Retorno, risco, drawdown e custo total agora vêm do módulo canônico. O motor comum existe na **camada experimental** (`ExperimentRunner`/`ExecutionEngine`), mas o **dashboard e os demais caminhos legados** ainda instanciam engines próprios com custo zero e não passam por ele. |
| Sistema de agentes | Parcial | Quorum técnico -> risco -> portfólio em LangGraph, com contratos Pydantic e regras duras. Opera um ticker por execução. |
| Quorum de 30 | Implementado com ressalvas | Faz 30 chamadas concorrentes do mesmo papel e cliente, variando prompt, temperatura e seed registrado. Exige 25/30 por padrão e todos os votos válidos. |
| Cliente LLM real | Parcial | Cliente HTTP OpenAI-compatible, retry, cache e telemetria básica. A integração específica chamada de OmniRouter/Agent Router não está isolada nem comprovada no repositório. |
| Backtest LLM legado | Implementado com lacunas | `AgentBacktestEngine` decide no fechamento de `t`, executa na próxima abertura observada e registra ciclo, votos, trades e curva em JSON. A última previsão fica pendente. Continua disponível como caminho operacional; a parte de execução financeira dele **não** foi reutilizada pela arena. |
| Runner diário | Parcial | `DailyAgentRunner` persiste estado, reconcilia a previsão pendente na abertura esperada e avança uma sessão por execução. Ainda não integra a arena nem um manifest canônico. |
| Calendário B3 | Parcial | `B3Calendar` resolve fins de semana, feriados recorrentes e exceções explícitas sem dependência externa; ainda precisa de validação/versionamento contra calendário oficial. |
| Arena clássicos x LLM | Parcial | Contrato mínimo de participante e intenção, com execução comum long-only single e multi-ativo para os cinco benchmarks clássicos e para o participante LLM single-asset. Todos executam pelo mesmo `ExecutionEngine`, pelo mesmo `ExperimentRunner` e produzem o mesmo `RunResult`. Falta o participante LLM multi-ativo e falta o protocolo científico. |
| Participante LLM na arena | Implementado (single-asset) | `LLMParticipant` recebe apenas `MarketObservation`, monta o `AgentState` a partir de `close(t)`, delega ao grafo existente e termina em peso alvo. Não executa trade, não mexe em caixa, não aplica custo. Falha de provedor derruba o run em vez de virar `MANTER`. Registrado no registry como `llm_agent`. |
| Dashboard | Parcial | Compara as cinco estratégias clássicas e exibe indicadores. Uma tela separada dispara backtest LLM, mas não incorpora o resultado à arena. |
| Orquestração experimental | Implementado com lacunas | `src/experiments/` executa os cinco clássicos **e o `llm_agent`** a partir de um snapshot validado, com `spec_hash` estável, `run_id`, participante novo por run, evidência do snapshot capturada no `run()` e manifest atômico em `data/runs/<run_id>/`. A `ExperimentSpec` declara a janela avaliada (`EvaluationSpec`: `decision_start`, `decision_end`, `minimum_history_sessions`), que entra no `spec_hash`; o warm-up anterior é histórico e não produz decisão, trade nem performance. Não cobre a **escolha** das janelas nem análise estatística. |
| Avaliação científica | Planejado | O protocolo pseudo-live está documentado, mas não existem janelas experimentais selecionadas, walk-forward, testes de hipótese, análise de sensibilidade ou exportação científica. |
| Operação em tempo real/MT5/BRAPI | Planejado | O runner diário é simulação persistente; integrações de mercado e execução automática não existem. O estágio Live/Shadow do protocolo ainda não foi executado. |
| Historical Memory | Planejado | Não existe. Sem corpus, proveniência temporal de documentos, retriever, embeddings ou vector store. Registrada no protocolo como extensão planejada e hipótese experimental separável. |

### Duas camadas distintas, e só uma tem motor comum

A frase "não há motor comum" já não descreve o repositório. Ela precisa ser lida
por camada:

```text
CAMADA EXPERIMENTAL  (src/experiments/, src/backtesting/arena.py)
    motor comum JÁ EXISTE
    ExperimentSpec -> ExperimentRunner -> Participant
        -> ExecutionEngine -> RunResult -> manifest
    usado pelos cinco benchmarks clássicos E pelo llm_agent

DASHBOARD / CAMINHOS LEGADOS  (scripts/generate_dashboard_data.py,
                               AgentBacktestEngine, DailyAgentRunner)
    ainda usam engines e fluxos próprios
    custo zero, sem spec_hash, sem run manifest, fora do RunResult
```

Nenhuma limitação registrada neste documento nega o motor comum da camada
experimental; as que permanecem são sobre protocolo, janelas, cobertura
multi-ativo do LLM e migração dos caminhos legados.

## Fluxos executáveis

### Pipeline e dashboard clássico

`just run` encadeia:

1. `src.pipeline.flows.pipeline_etl`;
2. extração ou leitura do cache;
3. limpeza e indicadores;
4. carga no banco;
5. `scripts/generate_dashboard_data.py`;
6. três backtests single-asset agregados e dois multi-ativo;
7. geração de `dashboard/data.json`;
8. servidor HTTP local em `http://localhost:8081`.

No estado auditado, o PostgreSQL local contém 10 ativos, 26.390 cotações e
26.390 registros de indicadores, sem duplicatas de ativo/data, cobrindo
04/01/2016 a 05/08/2026. Cada ticker tinha uma barra final com algum OHLC igual
a zero. O gate atual rejeita essas barras em novas execuções, mas não repara
automaticamente dados inválidos já persistidos antes desta validação.

### Snapshot de dataset

`src.pipeline.snapshot.create_dataset_snapshot()` reutiliza o `DataExtractor` e
o gate `validate_ohlcv`, analisa cada ticker contra as sessões esperadas do
`B3Calendar` e materializa uma cópia independente em
`data/snapshots/<snapshot_id>/data/`. O cache permanece uma otimização mutável;
alterações posteriores nele não reescrevem snapshots existentes.

Cada diretório possui `manifest.json` serializado com chaves ordenadas e um CSV
por ticker. O manifest registra intervalo solicitado e efetivo, contagens,
lacunas e datas inesperadas, SHA-256 e tamanho dos arquivos, fonte e versão do
`yfinance`, política de ajuste observável, versão do Python/pipeline, commit e
estado dirty do Git, além das regras e exceções do calendário. Um ID existente
nunca é sobrescrito silenciosamente.

#### Identidade verificável do manifest (schema 2)

O `snapshot_id` é `timestamp UTC + digest`, e o digest é o SHA-256 do JSON
canônico do manifest inteiro **menos o próprio `snapshot_id`** — sem
circularidade e sem deixar campo científico de fora. `quality` (inclusive
`scientific_ready`), `coverage`, a lista de `files` com seus SHA-256 declarados,
`tickers`, intervalos, `source`, `calendar`, `pipeline` e `code` fazem todos
parte da identidade.

No carregamento, `load_dataset_snapshot()` valida em ordem fail-closed: JSON,
schema, formato do ID, digest recalculado, coerência entre o prefixo temporal do
ID e `created_at`, e nome do diretório igual ao `snapshot_id`. Qualquer
divergência levanta `SnapshotIdentityError`. Isso fecha o buraco em que
`"scientific_ready": false` podia virar `true` na mão sem tocar em nenhum CSV.

São duas garantias separadas e ambas mantidas: identidade do manifest (o que o
artefato afirma) e integridade dos arquivos (os bytes dos CSVs, conferidos por
`verify_snapshot_integrity`). A primeira não substitui a segunda.

É tamper-evidence dentro do modelo do projeto — detecta adulteração e
incoerência do artefato —, não assinatura criptográfica: quem recomputa o ID
depois de editar o conteúdo não é barrado por este mecanismo.

Snapshots do schema 1 não possuem essa garantia. São reconhecidos, nomeados e
recusados com pedido de regeneração; não existe migração automática que copie um
manifest antigo e o declare confiável.

Cobertura completa exige todas as sessões locais esperadas e nenhuma barra em
data não esperada. Lacunas não recebem `ffill` nem preço inventado: o artefato é
preservado para auditoria como `attention_required`, com
`scientific_ready=false`. Intervalos sem nenhuma sessão são marcados
`no_expected_sessions`. OHLCV inválido ou falha de qualquer ticker obrigatório
interrompe a criação antes da publicação do diretório final.

### Backtest multiagente

`scripts/run_agent_backtest.py` lê um ticker do banco, seleciona os últimos `N`
pregões, constrói um grafo e executa:

1. **Comitê técnico**: 30 pareceres concorrentes por padrão.
2. **Agregação**: compra, venda ou manter exige 25/30; falha obrigatória força
   `MANTER`.
3. **Risco**: vendas/manutenção passam sem aumentar exposição; compras passam por
   volatilidade, drawdown e concentração antes da análise LLM.
4. **Portfólio**: no modo legado — que é o default de `PortfolioConfig` e o que
   este script usa — limita compras por fractional Kelly sobre a `confidence`,
   tamanho máximo e espaço de concentração; depois pede decisão ao LLM sem
   permitir inversão do sinal. Esse caminho é **operacional, não científico**:
   a arena usa o modo qualitativo, descrito abaixo.
5. **Execução**: uma decisão de `t` vira ordem para a abertura de `t+1`.
6. **Auditoria**: salva curva, trades, decisões, votos e telemetria em JSON. Cada
   decisão inclui `as_of`, `target_session`, `status`, `execution_date`,
   `execution_price` e justificativa de status.

No replay histórico, `target_session` é a próxima data realmente observada no
índice, portanto sexta-feira aponta para a barra de segunda-feira quando ela
existe. A última decisão acionável permanece `PREDICTED`, sem trade nem impacto
nas métricas. Uma decisão executada vira `EXECUTED`; `MANTER` vira `NO_ACTION`;
veto ou ordem impossível vira `REJECTED`. Como o replay não deve inventar dados,
a última previsão ainda fica com `target_session=null`.

### Runner diário

`scripts/run_agent_daily.py` usa `DailyAgentRunner` para avançar exatamente uma
sessão por execução. O runner persiste caixa, posição, custos, curva, trades,
decisões e última sessão em JSON; mantém no máximo uma previsão `PREDICTED`;
reconcilia essa previsão na abertura da sessão-alvo; e só então gera a previsão
seguinte. O estado é gravado por substituição atômica e protegido por lock local
contra dois processos no mesmo host.

`B3Calendar` já resolve a próxima sessão por fins de semana, feriados recorrentes
e conjuntos explícitos de fechamentos/aberturas excepcionais. É uma aproximação
local, não um feed oficial: exceções futuras ainda precisam ser conferidas e
versionadas para uso científico. O runner também continua single-asset e separado
da arena clássica.

O chamado “gestor de portfólio” ainda dimensiona uma posição de **um único
ativo**. Ele não recebe o universo de ativos, correlações, pesos correntes da
carteira ou restrições globais. O quorum é um ensemble estocástico de um papel,
não 30 especialistas ou 30 modelos independentes.

### Arena incremental — cinco benchmarks clássicos

`src/backtesting/arena.py` concentra a fatia comum sem substituir os motores
anteriores:

```text
MarketObservation até close(t)
        -> Participant.decide(...)
        -> OrderIntent de peso alvo
        -> ExecutionEngine em open(t+1)
        -> Trade + equity em close(t+1)
```

Cinco adaptadores usam esse caminho:

| Participante | Onde está | Como decide |
|---|---|---|
| `BuyAndHoldParticipant` | `src/strategies/buy_and_hold.py` | Uma intenção na primeira sessão observável. |
| `SMACrossParticipant` | `src/strategies/sma_cross.py` | Médias rápida e lenta recalculadas sobre o histórico truncado em `t`. |
| `BollingerParticipant` | `src/strategies/bollinger_bands.py` | Bandas estimadas só com dados até `t`. |
| `EqualWeightParticipant` | `src/backtesting/portfolio.py` | `1/N` sobre os ativos observados, na cadência de rebalance do motor legado. |
| `MinVarianceParticipant` | `src/backtesting/portfolio.py` | Reutiliza `MinVariancePortfolio`, que já recebe histórico truncado. |

Nenhum participante decide direção de negociação: `OrderIntent` carrega apenas
`ticker`, `target_weight` e `decision_time`. Os dois single-asset alternam entre
100% investido e caixa e só emitem intenção quando o peso alvo muda, portanto
uma posição mantida não gera trade repetido. Os dois multi-ativo emitem o peso
alvo de cada ticker do universo a cada rebalance.

Na abertura de `t+1`, o executor converte cada peso alvo em quantidade alvo
sobre o patrimônio observado e compara com a posição corrente: déficit vira
`BUY`, excesso vira `SELL`, posição já no alvo não gera trade. Como o preço de
abertura pode ter aberto em gap, uma intenção que no fechamento anterior
implicaria aumento pode ser executada como venda — `Trade.type` reflete a
operação realmente executada. O executor usa `CostModel`, quantidade inteira,
caixa não negativo e posição long-only. Um intent na única/última sessão permanece uma decisão sem abertura
observada e não gera trade — o participante decide igual e não é informado de
que aquela era a última sessão. A observação contém cópias dos históricos
truncadas em `t` e nenhum campo sobre a sessão seguinte, portanto o participante
não recebe preços futuros nem o horizonte da amostra por esse contrato.

No caminho multi-ativo, o calendário é a interseção explícita dos índices, sem
forward-fill nem barra fabricada; os tickers são percorridos em ordem
determinística; e a alocação segue uma política puramente técnica: alvos e
deltas calculados sobre o patrimônio na abertura, vendas antes das compras e,
quando o caixa não cobre todos os déficits, escalonamento de todos os alvos pelo
mesmo fator seguido de truncamento. O fator vem de busca binária sobre o custo
reportado pelo `CostModel`, então o resultado não depende da ordem dos tickers e
não assume a fórmula de custo. O resíduo de caixa não é redistribuído.

Esta implementação continua técnica: peso alvo entre zero e um foi escolhido
como semântica extensível, sem congelar lote B3, slippage, liquidez, margem,
política de suspensão ou rateio científico definitivo. `BacktestEngine`,
`PortfolioBacktestEngine` e `AgentBacktestEngine` continuam ativos em paralelo e
o dashboard segue usando os motores legados. Como o executor não consome
`DatasetSnapshot`, o guard de `scientific_ready` permanece responsabilidade da
futura camada de `ExperimentSpec`; não foi criada uma integração artificial
nesta etapa.

#### Divergência intencional com o motor multi-ativo legado

`PortfolioBacktestEngine` dimensiona as compras em laço por ticker ordenado,
comprando o máximo possível de cada um antes de passar ao seguinte. Quando há
custos positivos e os pesos somam 1,0, o caixa liberado pelas vendas não cobre
todos os alvos e o último ticker da ordem alfabética recebe o que sobrou — em
cenário extremo, nada. A arena não replica esse viés: escalona os alvos em
conjunto. Os testes de paridade cobrem cenários sem disputa por caixa (custo
zero, ou pesos com folga suficiente para os custos), onde os dois motores
coincidem trade a trade; a divergência tem teste próprio, junto com a prova de
que permutar a ordem dos tickers não altera curva, trades, custos nem posições
na arena.

### Camada experimental — spec, runner e manifest

`src/experiments/` fecha o caminho entre snapshot e resultado auditável:

```text
DatasetSnapshot -> ExperimentSpec -> ExperimentRunner -> RunResult -> manifest.json
```

O que já está garantido por teste:

- **Snapshot é a única fonte de OHLCV.** O runner lê `data/snapshots/<id>`; não
  chama `yfinance` nem o cache mutável. Um teste monkeypatcha o download para
  falhar e o run passa mesmo assim.
- **Gate científico fail-closed.** `scientific_ready=false` levanta
  `SnapshotNotReadyError` antes de a arena rodar. Não existe "rodar mesmo assim".
- **Identidade do snapshot verificada.** O manifest do snapshot é conferido
  contra o digest embutido no `snapshot_id` e contra o nome do diretório;
  manifest adulterado levanta `SnapshotIdentityError` antes do gate científico.
  Promover um snapshot reprovado editando `quality.scientific_ready` não
  funciona.
- **Integridade verificada.** Tamanho e SHA-256 de cada CSV são conferidos contra
  o manifest do snapshot; arquivo adulterado ou ausente levanta
  `SnapshotIntegrityError` e nenhum run é publicado.
- **Participante novo por run.** O registry constrói uma instância a cada
  execução. Os clássicos guardam estado entre sessões (`_target_weight`,
  `_session_index`), então reutilizar a instância contaminaria a segunda
  execução.
- **`spec_hash` determinístico e estável.** SHA-256 do JSON canônico da spec;
  independe da ordem dos dicionários e não contém horário, `run_id` nem caminho
  local. `ParticipantSpec.params` é copiado na construção e guardado como
  `MappingProxyType`: mutar o dicionário original do chamador ou tentar escrever
  em `participant.params[...]` não altera a spec — a identidade de uma
  `ExperimentSpec` criada é estável por toda a sua vida.
- **Coerência presa ao artefato.** No manifest publicado,
  `spec_hash == SHA-256(canonical_json(manifest["experiment_spec"]))`. Quem lê o
  run não precisa confiar no runner que o escreveu.
- **Proveniência do snapshot capturada no run.** `RunResult` carrega um
  `SnapshotEvidence` congelado no momento em que o snapshot passou pelos guards
  e antes da execução: `snapshot_id`, `schema_version`, `identity_digest` e o
  manifest verificado em JSON canônico. `persist()` não relê o diretório, então
  adulterar (ou apagar) o snapshot entre `run()` e `persist()` não reescreve
  retroativamente a descrição histórica do que foi executado.
- **`run_id` por execução.** Duas execuções da mesma spec produzem resultados
  idênticos, o mesmo `spec_hash` e `run_id` distintos.
- **Proveniência limpa exigida por padrão.** O guard exige commit conhecido e
  `git_dirty=false`: working tree suja, commit indeterminado e proveniência Git
  não verificável levantam `DirtyRepositoryError` antes de carregar dados ou
  construir o participante. `allow_dirty=True` libera explicitamente os dois casos para
  desenvolvimento e o resultado continua identificável como não-limpo. Não é
  parâmetro da spec e não altera o `spec_hash`.
- **Publicação atômica.** Artefatos são escritos num diretório temporário e só
  então renomeados; falha no meio não deixa run parcial aparentando validade.

O universo efetivo é derivado sem seleção dinâmica: single-asset recebe o
`ticker` declarado na spec (ausência no snapshot é falha, não remoção
silenciosa) e carteira recebe todos os tickers do snapshot. Universo entregue e
universo do snapshot ficam ambos registrados.

Os defaults de métrica (`freq=252`, `rf=0`, `mar=0`) e de custo entram pelo spec
e são gravados no manifest como valores efetivamente usados — registro, não
congelamento. `MetricSpec` e `CostSpec` existem justamente para que nenhum
default científico fique implícito.

Artefatos ficam em `data/runs/<run_id>/` com `manifest.json`, `equity.csv` e
`trades.csv`, fora do versionamento Git. O manifest sempre registra
`code.git_commit` e `code.git_dirty`, mais `reproducibility.clean_source` e
`reproducibility.allow_dirty`. `clean_source` só é verdadeiro quando o Git
confirma um commit conhecido sem alterações pendentes — a mesma regra do
guard, em função única, para que os dois não divirjam. Quando o commit não pode
ser determinado, `git_commit` permanece nulo e `clean_source` é falso: nenhum
SHA é inventado.

Nenhum diff ou patch do working tree é persistido. A regra é simples: run
científico reproduzível equivale a commit conhecido mais tree limpa.

Participantes cobertos por esta camada: os cinco benchmarks clássicos e o
`llm_agent`. O participante LLM é experimental e single-asset, roda pela mesma
Arena e pelo mesmo `ExperimentRunner` dos benchmarks, termina em decisão
qualitativa com sizing determinístico e publica trace auditável com replay —
detalhes em "Participante LLM na arena". Historical Memory não está
implementada e o protocolo científico continua **DRAFT — NÃO CONGELADO**.

Limitações desta camada: `ExperimentSpec` não descreve período, janelas
experimentais nem walk-forward — o recorte executado é a cobertura do snapshot —,
não há catálogo/consulta de runs, o dashboard continua
gerando seus números pelos motores legados e o snapshot ainda depende do
`B3Calendar` local não validado contra fonte oficial.

## Evidência de validação

As verificações abaixo foram observadas no ambiente local durante a auditoria;
seus resultados não são, por si só, conteúdo versionado no Git:

| Verificação | Resultado |
|---|---|
| Suíte de pipeline com SQLite em memória (`poetry run pytest tests/pipeline -q`) | **108 passaram** em 10/09/2026 |
| Suíte de backtesting (`poetry run pytest tests/backtesting -q`) | **191 passaram** em 12/09/2026 |
| Suíte experimental (`poetry run pytest tests/experiments -q`) | **64 passaram** em 13/09/2026 |
| Suítes de agentes e experimentos após o trace de LLM (`pytest tests/agents tests/experiments -q`) | **263 passaram** em 13/09/2026 |
| Suíte completa com SQLite em memória (`poetry run pytest -q`) | **509 passaram** em 13/09/2026 |
| Suíte completa após o trace de LLM (`poetry run pytest -q`) | **689 passaram** em 13/09/2026 |
| Cobertura (última medição, anterior a esta mudança) | **95%** |
| Ruff | **14 violações preexistentes fora dos arquivos desta mudança** |
| Ruff nos arquivos desta mudança | **verde** |
| Pyright nos arquivos desta mudança | **verde** |
| Pyright no escopo configurado (última medição) | **181 erros** |
| Pyright em `src/agents`+`src/experiments`+testes, antes/depois desta mudança | **50 -> 50** (nenhum erro novo) |
| Mutação A — remover comparação de prompt no replay | **3 testes falham** |
| Mutação B — contador de retry global entre chamadas concorrentes | **2 testes falham** |
| Mutação C — aceitar registro sobrando no trace | **1 teste falha** |
| Mutação D — retirar o hash do trace do manifest | **3 testes falham** |
| Mutação E — retirar `response_schema_sha256` da identidade da chamada | **1 teste falha** |
| Ensemble concorrente terminando fora de ordem (conclusão `[2, 3, 1]`) | trace publicado em ordem de emissão `[1, 2, 3]`, idêntico em 5 execuções |
| Run mock determinístico antes/depois desta mudança | **impressão digital idêntica** (equity, trades, métricas e pesos alvo) |
| Banco PostgreSQL local | 10 ativos; 26.390 datas únicas de cotação e indicadores |
| Duplicatas ativo/data | 0 |
| Barras com algum OHLC não positivo | 1 por ticker, na última data |

O conflito da última previsão foi resolvido no contrato e nos testes: ela é
preservada como `PREDICTED`, sem `execution_date` ou `execution_price`, e não
entra em trades ou desempenho até ser reconciliada por uma abertura futura.

A cobertura alta comprova que muito código foi exercitado, mas não valida o
desenho experimental. O antigo teste “sem look-ahead”, que esperava compra pelo
fechamento da própria barra do sinal, foi substituído por casos explícitos que
distinguem `close(t)` de `open(t+1)` e rejeitam trade na última decisão.

## Problemas que invalidam a comparação atual

### 1. Unidade experimental ainda não é comum — apesar do motor já ser

O motor comum **não** é mais a limitação. Os cinco benchmarks clássicos e o
`llm_agent` passam pelo mesmo caminho experimental:

```text
ExperimentSpec(kind=...) -> ExperimentRunner -> Participant
    -> ExecutionEngine -> RunResult -> manifest
```

com o mesmo `spec_hash`, os mesmos guards de snapshot e de proveniência Git, e o
mesmo `RunResult` consolidado. Todos compartilham a semântica de observação até
o fechamento de `t` e execução na abertura de `t+1`.

O que ainda impede tratar as execuções como uma competição científica:

- **Protocolo ainda não congelado.** Hipóteses, prompts, modelo/provider,
  parâmetros dos agentes, sizing, custos, métrica primária e plano estatístico
  continuam `DRAFT` em `docs/EXPERIMENT_PROTOCOL.md`.
- **Janelas experimentais existem, mas nenhuma foi escolhida.** O mecanismo
  está implementado — `EvaluationSpec`, gate de warm-up, settlement explícito,
  `phase`/`case_id` no manifest — e nenhuma data de calibração, validação ou
  teste foi selecionada. Ter como representar a janela não é ter escolhido
  qual janela.
- **LLM ainda single-asset.** `LLMParticipant` recusa universo com mais de um
  ativo; a stack de agentes descreve um ticker por execução.
- **Participantes single-asset e multi-ativo ainda não formam necessariamente a
  mesma unidade experimental** — ver "3. Participantes diferentes" abaixo.
- **Dashboard continua usando caminhos legados**, com engines e fluxos próprios
  e custo zero; ele não consome `ExperimentRunner`/`RunResult`.
- **Custos científicos finais ainda `TBD`.**
- **Análise estatística ainda não executada.**

### 2. Custos não comparáveis

O dashboard instancia todos os motores com `CostModel()` padrão, isto é, custo
zero. Os motores agora calculam custos percentuais sobre
`abs(quantity * execution_price)`, reservam esses custos antes da compra e não
deixam o caixa negativo. Os valores científicos de corretagem, spread, slippage,
taxas e lotes continuam `TBD`; logo, os resultados do dashboard ainda não são uma
comparação líquida congelada.

O `allow_short=True` legado do single-asset agora é rejeitado explicitamente, e o
motor multi-asset rejeita pesos negativos. Isso evita ampliar um suporte que era
incompleto; política de margem, fechamento da posição e demais regras de short
continuam pendentes de decisão metodológica.

### 3. Participantes diferentes

As três estratégias single-asset são executadas separadamente nos dez ativos e
depois agregadas. Equal Weight e Mínima Variância são carteiras conjuntas. O LLM
opera apenas um ticker. Essas unidades experimentais não são equivalentes.

### 4. Métricas e agregação

- `src/backtesting/metrics.py` valida que a equity curve seja temporal, ordenada,
  única e finita, e concentra retornos, retorno total, CAGR técnico,
  volatilidade, Sharpe, Sortino, drawdown e duração de drawdown.
- A curva média single-asset usa explicitamente apenas a interseção das datas
  observadas por todos os tickers; sua composição não varia silenciosamente.
- O scatter consome retorno, volatilidade anualizada e Sharpe calculados
  diretamente da mesma equity curve; não reconstrói volatilidade por divisão.
- O período publicado vem do primeiro e último ponto efetivamente observado, e
  o custo total é a soma de `trade.cost` dos trades executados.
- O dashboard ainda não publica turnover, exposição, benchmark de mercado ou
  incerteza estatística. A definição legada de mudança média de pesos inclui
  drift e não foi promovida a turnover científico.
- `252` sessões/ano, taxa livre de risco zero e MAR zero são defaults técnicos
  configuráveis, não parâmetros experimentais congelados.

### 5. Protocolo experimental ainda não congelado

Existe um protocolo documental em `docs/EXPERIMENT_PROTOCOL.md`, marcado como
**DRAFT — NÃO CONGELADO**. `ExperimentSpec`, `RunResult` e run manifest já
existem como mecanismo técnico, mas ainda não existem janelas experimentais,
prompts, parâmetros ou universo congelados; walk-forward; avaliação pseudo-live
executada; nem análise estatística implementada. Ter um manifest reproduzível
não torna o protocolo aprovado.

#### Metodologia registrada, ainda não executada

O desenho experimental deixou de ser TRAIN/VALIDATION/TEST clássico e passou a
ser descrito como calibração retrospectiva do sistema seguida de avaliação em
ambiente causal pseudo-live:

```text
SYSTEM CALIBRATION -> FREEZE -> PSEUDO-LIVE VALIDATION -> FINAL TEST -> LIVE/SHADOW
```

Motivo: o LLM chega pré-treinado e o experimento v1 não faz fine-tuning nem
estima pesos sobre período algum. O que se ajusta retrospectivamente é o
**sistema** — prompts, papéis, quorum, consenso, temperaturas, limites de risco
e `decision_frequency` —, e o risco metodológico a conter passa a ser o
overfitting dos próprios pesquisadores sobre os períodos observados.
`long_target_weight` deixou de pertencer a esse conjunto: passou a ser decisão
declarada de política de exposição, não parâmetro de calibração por desempenho.

A governança dessa calibração também passou a ser documental: o protocolo
descreve subfases com autoridades distintas — Diagnostic Hardening, CAL-A,
Sequential Development, Stress e CAL-B —, a quantidade de âncoras
(`CORE = 30 = CAL-A 20 + CAL-B 10`, mais até 8 âncoras de stress fora do CORE),
quais parâmetros cada subfase pode alterar e a regra one-shot do CAL-B. **Nada
disso foi executado**, nenhuma data foi escolhida e nenhum critério de seleção
foi definido.

Estado factual de cada item:

| Item | Estado |
|---|---|
| Desenho pseudo-live (decisão em `close(t)`, execução em `open(t+1)`, relógio avançando uma sessão por vez) | Documentado; o mecanismo de execução já existe na arena e no `AgentBacktestEngine` |
| Calibração retrospectiva do sistema como etapa declarada | Documentada; nunca executada como fase formal |
| Janela base de mercado `>= 2 anos` | Aprovada conceitualmente; **mecanismo implementado**. `minimum_history_sessions` é campo obrigatório da `EvaluationSpec` e o gate falha antes de construir o participante. O valor recomendado passou a ser 504 sessões disponíveis até e incluindo `decision_start` (503 anteriores + a sessão de decisão); recomendado e documentado, ainda não congelado. A janela continua expansiva (`snapshot[:t]`), por decisão registrada |
| Governança da CALIBRATION (subfases, autoridade por parâmetro, CAL-B one-shot, disjunção de datas) | Documentada em `EXPERIMENT_PROTOCOL.md` §5.12. Nenhuma subfase executada; nenhum baseline `B0` existe |
| Historical Memory | Não implementada. Nenhum corpus, retriever, embedding ou vector store |
| Calibration Cases, Validation, Final Test | Quantidade de âncoras decidida (`CORE = 30`, `CAL-A = 20`, `CAL-B = 10`, stress `<= 8` fora do CORE); **nenhuma data selecionada** |
| Critério agregado de CAL-A, janela e critério do Sequential Development, regra de síntese dos runs de Validation | `TBD`. Espaço de decisão delimitado no protocolo, valor não escolhido |
| Métrica primária, universo final, provider/model, custos | `TBD` |

Nada disso alterou código, schema ou configuração de execução: a formalização é
documental.

## Riscos técnicos relevantes

### Dados

- O cache continua usando apenas o ticker como chave. Um hit exige cobertura dos
  limites inicial e final inclusivos, e o retorno é recortado para o intervalo
  pedido. O `end` enviado ao `yfinance` permanece exclusivo e recebe um dia a
  mais que o limite público inclusivo.
- Quando a cobertura é insuficiente, a extração baixa novamente o intervalo
  completo solicitado, combina-o com o cache validado, mantém a resposta nova no
  overlap, deduplica, ordena e persiste o CSV atualizado.
- O gate fail-fast rejeita índice não temporal, `NaT`, duplicatas, desordem,
  colunas ausentes ou não numéricas, `NaN`, infinitos, OHLC não positivo ou
  inconsistente e volume negativo. Volume zero é aceito; `NaN` em volume é
  rejeitado. O forward-fill ficou restrito a colunas auxiliares após a primeira
  validação OHLCV.
- O snapshot detecta limites e lacunas internas pelo `B3Calendar`, mas esse
  calendário continua sendo aproximação local não validada contra fonte oficial
  versionada. Moeda, timezone e política científica de proventos/splits seguem
  pendentes; o extractor ainda usa o default de ajuste do provedor e o registra
  como tal no manifest.
- O flow continua processando os demais tickers após uma falha, porém agora
  retorna `PipelineResult` com tickers bem-sucedidos, falhos, erros e
  `complete=false`, tornando a carga parcial observável por automação.
- `create_all()` não migra bancos existentes. Não há sistema de migrations.

### Agentes e LLM

- A opção `seed` é registrada no voto e na chave do cache, mas o cliente HTTP
  envia apenas `temperature`, `top_p` e `max_tokens`. A seed não chega ao modelo.
  **Continua verdade**, agora provado e publicado: o trace separa
  `requested_options` (o que o ensemble pediu, incluindo `seed`) de
  `transport_options` (o que entrou no corpo HTTP, de onde `seed` está ausente).
  Não há determinismo por seed neste provedor, e a documentação não afirma que
  haja.
- O schema Pydantic é anexado ao prompt, porém não é enviado como structured
  output nativo (`response_format`/JSON Schema do provedor).
- ~~Retry e telemetria compartilham um contador mutável entre chamadas
  concorrentes~~ — **corrigido**. `LLMClient._retries_context` foi removido; o
  contador de tentativas vive em um rascunho por invocação guardado em
  `ContextVar`, que o `asyncio` copia por task. Há teste de concorrência com
  analistas que falham um número diferente de vezes, fora de lockstep.
- O cache grava todas as chamadas concorrentes no mesmo arquivo temporário, sem
  lock. Isso cria risco de corrida, perda de entradas e votos inválidos.
  **Deixado fora do caminho científico em vez de corrigido**: o
  `LLMParticipant` não monta `CachedLLMClient` e o `ExperimentRunner` não o
  introduz. Cache é otimização; evidência experimental é o trace. A chave do
  cache também não inclui `provider`/`model`, então trocar de modelo
  reaproveitaria a resposta anterior — mais uma razão para mantê-lo fora.
- Falhas de conexão são agregadas com segurança no comitê técnico, mas risco e
  portfólio só capturam respostas inválidas; uma falha de rede após o quorum pode
  abortar o grafo.
- ~~A confiança textual do LLM é usada como probabilidade de vitória na fórmula
  de Kelly~~ — **resolvido no caminho científico**. `confidence` continua sendo
  produzida pelo analista, continua no trace (`llm_calls.jsonl`), continua
  chegando ao gestor de risco e ao de portfólio como contexto qualitativo e
  continua disponível para calibração futura — ela apenas **não entra em
  nenhuma fórmula de dimensionamento**. A arena usa sizing determinístico; o
  Kelly sobre `confidence` sobrevive apenas onde explicitamente configurado
  (`sizing_mode="legacy_confidence_kelly"`), que é o caminho operacional
  legado. A calibração empírica de `confidence` continua não existindo e
  continua fora do experimento v1.
- A telemetria legada `LLMTelemetry` registra tokens, latência, retry e modelo,
  mas custo permanece sempre zero. O vínculo com run, data, agente e hash de
  prompt **passou a existir** no trace por chamada (`llm_calls.jsonl`), que é o
  artefato científico; `LLMTelemetry` continua como telemetria operacional do
  cliente e não é usada como evidência.
- No trace, uso de tokens só aparece quando o provedor devolve `usage`; caso
  contrário é `null`. Zero apresentado como medição seria estimativa disfarçada
  de fato.
- O dry-run subestima rodadas quando existe previsão no último dia e trata
  `analistas + 2` como número fixo. O número não é fixo: por decisão elegível o
  grafo pede entre `N` e `N + 2` chamadas lógicas (`N = analyst_count`), porque o
  veredito de risco resolve caminhos determinísticos antes de chamar o modelo e o
  Portfolio Manager não é executado sob veto nem sob `MANTER`; cache evita
  chamadas externas e retry pode multiplicar as tentativas físicas sobre a mesma
  chamada lógica. Hoje o dry-run não é uma estimativa confiável de gasto — o
  número confiável é o observado no trace (`attempt_count` por chamada).

### Participante LLM na arena — o que ficou dentro e o que ficou fora

Entregue nesta fase:

- `src/agents/participant.py` com `LLMParticipant`, `LLMDecisionError`,
  `LLMDecisionRecord`, `FailureRecordingClient` e `target_portfolio_to_intents`.
- `llm_agent` no registry, construído só por `kind` mais parâmetros escalares.
- Configuração material do LLM na `ParticipantSpec`, portanto dentro do
  `spec_hash` e do manifest: `provider`, `model`, `retry_attempts`,
  `retry_base_delay`, `analyst_count`, `consensus_threshold`,
  `require_all_votes`, `temperature_min`, `temperature_max`, `seed_base`,
  `risk_max_volatility`, `risk_max_drawdown`, `risk_max_concentration`,
  `long_target_weight`, `volatility_window` e `decision_frequency`.

  Saíram da spec do `llm_agent`, por terem deixado de afetar o comportamento:
  `kelly_fraction`, `max_position_size`, `portfolio_max_concentration` e
  `payoff_ratio`. Manter parâmetro morto na spec permitiria registrar como
  "configurações distintas" dois runs que decidem e executam exatamente igual —
  `spec_hash` diferente, comportamento idêntico. Eles são recusados na
  construção do participante e continuam existindo apenas nos caminhos legados,
  com seus próprios parâmetros.
- Credencial fora de tudo isso: continua vindo do ambiente, como antes.
- `provider="agent_router"` exige `model` explícito — sem modelo declarado não
  há proveniência e o run não começa.

**Frequência de decisão migrada, não inventada.** `decision_frequency` existia
no motor legado e não tinha equivalente na primeira versão do participante, o
que transformaria silenciosamente a estratégia em decisão a cada pregão. Agora
existe, é do participante e entra na spec. Os dois defaults do código legado são
diferentes e ficam registrados como são:

```text
AgentBacktestEngine (classe/API) default = 1
scripts/run_agent_backtest.py       default = 5
```

`LLMParticipant` adota `1`, o default da classe. Nenhum dos dois é parâmetro
científico congelado: `5` é escolha operacional do script de demonstração, feita
para reduzir chamadas, e continua não aprovada como metodologia.

Uma divergência com o legado é deliberada: lá a última barra era sempre
elegível (`is_last_day`), o que exige saber que o recorte terminou. O contrato
da arena não entrega essa informação, então a elegibilidade aqui depende apenas
do índice já percorrido.

**`MANTER` continua significando nenhuma ordem.** O participante single-asset
não converte `MANTER` em `target_weight` igual ao peso do fechamento: isso
viraria um rebalance na abertura seguinte depois de um gap, que não é "não
fazer nada". A regra vale para este participante migrado e não altera a decisão
de carteira-alvo completa obrigatória para o futuro LLM multi-ativo.

**Paridade de dimensionamento com o legado, e onde ela termina.** Sem gap
(`open(t+1) == close(t)`) e sem custos, a tradução reproduz exatamente a
quantidade do motor legado na compra. Na venda ela coincide quando
`posição * size` é inteiro; quando não é, divergem em uma ação, porque o legado
trunca a *quantidade vendida* e a arena trunca a *posição alvo* remanescente.
Isso é política de lote e arredondamento da arena, que continua `TBD`, e está
preso por teste em vez de escondido. Com gap ou com custos não existe paridade
esperada, por construção: a direção nasce na abertura e os custos são do
executor.

**Multi-ativo: NÃO implementado nesta fase.** A stack de agentes é single-asset
por construção e não possui etapa de alocação entre ativos. Transformar isso em
um laço por ticker com normalização de pesos criaria uma estratégia nova, sem
raciocínio cross-asset, que nunca foi aprovada. O `LLMParticipant` recusa
explicitamente universo com mais de um ativo. O contrato de carteira-alvo
completa já está implementado e testado, então a evolução multi-ativo só
precisa substituir a origem dos pesos.

**Sizing científico: decisão qualitativa + alvo determinístico.** A estratégia
LLM da arena **mudou de propósito** nesta fase, e essa é a diferença em relação
aos hardenings anteriores: aqui não se busca fingerprint idêntico ao
comportamento antigo. O que permanece igual é dados, Arena, custos, timing,
métricas e benchmarks; o que muda deliberadamente é a regra de dimensionamento
do participante LLM.

```text
Technical Analyst (LLM)   -> COMPRA / VENDA / MANTER
        v
Risk Manager (regras+LLM) -> APROVADO / VETADO
        v
Portfolio Manager (LLM)   -> PortfolioAction  (qualitativa, sem quantidade)
        v
FixedTargetSizing         -> target_weight
        v
ExecutionEngine em open(t+1)
```

Semântica:

```text
COMPRA aprovada -> target_weight = long_target_weight
VENDA  aprovada -> target_weight = 0.0
MANTER          -> nenhuma intenção
veto de risco   -> nenhuma intenção
```

O gestor de portfólio não escolhe 3%, 17%, 42% ou 82% de exposição: o schema
`PortfolioAction` não tem campo de tamanho, então a autoridade de sizing não é
ignorada — ela não é concedida. `calculate_kelly_size` não é chamada neste
caminho, e há teste que faz a função explodir e exige que o run continue.

`long_target_weight` é validado (`0 < w <= 1`, e `w <= risk_max_concentration`),
entra no `spec_hash` e no manifest. O default técnico é `0.25`, herdado do antigo
teto `max_position_size` para manter API e testes convenientes:

```text
technical default       = 0.25
scientific frozen value = TBD  (EXPERIMENT PROTOCOL v1)
```

Nada nisso congela 25% como decisão metodológica.

**`COMPRA` passou a significar exposição alvo, não ordem de compra.** Com a
exposição corrente abaixo do alvo o executor compra; depois de um gap de alta
que empurre a exposição acima do alvo, o mesmo alvo exige vender. Isso está
preso por teste: dois datasets idênticos até `close(t)` e diferentes apenas em
`open(t+1)` produzem a mesma decisão e o mesmo alvo, e trades de direção
oposta. A direção financeira continua sendo responsabilidade da arena.

**O que ficou de fora.** Calibração empírica de `confidence`, long/short,
`volatility_target`, `calibrated_kelly` e o valor definitivo do alvo. A
arquitetura deixa o ponto de troca de política explícito (`FixedTargetSizing`),
sem implementar as alternativas.

**Paridade com o motor legado terminou aqui, de propósito.** Existiam três
provas de que a tradução reproduzia `floor(caixa * size / preço)` do
`AgentBacktestEngine`. Elas foram removidas junto com o comportamento que
prendiam: mantê-las exigiria manter `position_size` vivo no caminho científico
só para satisfazê-las. O motor legado segue com seu dimensionamento e seus
próprios testes.

**Proveniência de prompt.** Os prompts continuam vivendo em
`src/agents/technical_analyst.py`, `risk_manager.py` e `portfolio_manager.py`,
como constantes de módulo, e **continua não existindo registry nem
versionamento explícito de prompt** — nenhum campo `prompt_version` foi
inventado, porque não há mecanismo real de versionamento por trás dele.

O que passou a existir é proveniência do texto concreto: cada chamada grava os
dois prompts **lógicos completos** e seus SHA-256, calculados sobre o texto
exato em UTF-8, sem normalizar espaço em branco. Gravar o texto, e não apenas o
hash, é deliberado: o trace precisa permitir reconstruir a chamada, e nenhum
prompt do projeto carrega segredo. Registry formal de prompt segue como
hardening futuro.

**Prompt lógico não é prompt de transporte.** O `AgentRouterLLMClient`
transforma a chamada antes de enviá-la: ele serializa `model_json_schema()` do
`response_schema` e o acrescenta ao system prompt. Logo, para esse provedor, o
`system_prompt` publicado **não é** literalmente o texto que foi para o corpo
HTTP, e o trace não o descreve como tal.

```text
system_prompt            -> prompt LÓGICO, o que a stack de agentes pediu
response_schema_sha256   -> estrutura do schema, que vai junto na requisição
molde que une os dois    -> código, coberto pelo git_commit
--------------------------------------------------------------------------
determinam o prompt de TRANSPORTE

transport_system_prompt_sha256 -> hash do texto final, quando o cliente o
                                  reporta (null no mock, que não transforma)
```

Essa distinção não é cosmética. Antes desta rodada a identidade da chamada
usava só o **nome** da classe do schema, então afrouxar um limite de `Field`
sem renomear a classe mudava o que era perguntado ao provedor e **o replay
aceitava em silêncio**. Com `response_schema_sha256` na identidade, esse caso
levanta `ReplayMismatchError`.

**Fail-soft remanescente, herdado e não alterado.** O `portfolio_manager`
converte em `MANTER` uma decisão que inverte o sinal técnico, e o
`risk_manager` veta por métrica ausente no aquecimento do recorte. Nenhum dos
dois é falha de infraestrutura e ambos foram preservados como estão, para não
substituir silenciosamente o comportamento científico atual. Ambos aparecem em
`LLMDecisionRecord.errors`.

**Trace de chamadas integrado ao run (fase atual).** O que antes vivia só na
instância do participante agora é artefato publicado do run.

Um run `llm_agent` publica `data/runs/<run_id>/llm_calls.jsonl` ao lado de
`equity.csv` e `trades.csv`, e o manifest (schema 3) ganha
`participant_artifacts` com caminho, `schema_version`, `call_count`,
`error_count`, tamanho e `sha256` dos bytes publicados. O contrato é genérico
(`RunArtifactProvider` em `src/artifacts.py`): o runner não faz
`isinstance(participant, LLMParticipant)` e os clássicos não implementam nada,
publicando `participant_artifacts` vazio.

Cada registro contém `call_id`, `sequence`, `stage`, `analyst_id`,
`decision_session`, `provider`, `requested_model`, prompts lógicos completos e
seus hashes, `response_schema` com `response_schema_sha256`,
`requested_options`, `transport_options`, `transport_system_prompt_sha256`,
`started_at`, `duration_ms`, `attempt_count`/`retry_count`, `status`, tipo e
mensagem do erro quando houver, e a resposta validada em
`model_dump(mode="json")`.

`LLMTelemetry` continua acumulando no cliente como telemetria operacional e
não foi promovida a evidência.

**Reprodutibilidade: o que é e o que não é garantido.** Esta é a distinção
central para o TCC.

```text
mesma ExperimentSpec + mesmo snapshot + LLM externo ao vivo
    -> NÃO garante resposta idêntica
```

Mesmo `model`, mesma `temperature` e mesmo `seed` registrado não bastam: o
provedor não promete determinismo, e neste cliente `seed` sequer é transmitido.
A garantia forte passou a ser outra, em dois tempos:

```text
run ao vivo -> trace
trace       -> replay determinístico, sem rede, mesmas decisões
```

Há prova ponta a ponta: RUN A grava com mock determinístico e publica;
RUN B reexecuta a mesma arena com `ReplayLLMClient` lendo o trace publicado,
com as superfícies de rede patchadas para explodir, e produz as **mesmas**
decisões, trades, curva de equity e métricas. Ao final, o replay exige que o
trace tenha sido consumido inteiro.

O replay se recusa a fingir: prompt, modelo, provedor, opções solicitadas,
schema, papel, analista, sessão ou ordem diferentes levantam
`ReplayMismatchError` em vez de devolver a próxima resposta. Registro faltando
e registro sobrando também. Relógio e duração **não** entram na identidade —
reproduzir não pode falhar porque o tempo passou.

**Erro definitivo também é evidência.** Uma chamada que falhou de vez grava
`status="error"`, `error_type`, `error_message` e `attempt_count`. Só a
mensagem, sem stack trace: o stack é instável entre execuções e não acrescenta
informação sobre a inferência.

**Run que falha continua não sendo publicado.** `run_and_persist()` mantém o
comportamento anterior — uma falha do participante impede a publicação do run,
e nada foi alterado em silêncio. Persistir diretórios de run falho é proposta
registrada, não implementada.

### Dashboard e operação

- O dashboard e a tela `/lab` continuam consumindo os motores legados; eles não
  leem `data/runs/` nem exibem resultados do `llm_agent` na arena.
- `/lab` dispara processos sem fila, identificador, cancelamento ou endpoint de
  status; a conclusão é inferida por texto no log.
- A tela seleciona o provedor real por padrão e o servidor escuta em todas as
  interfaces. Não deve ser exposto fora de ambiente local.
- O endpoint trunca o log compartilhado antes de cada execução; duas execuções
  podem interferir uma na outra.
- Linhas de log, inclusive texto produzido pelo LLM, são inseridas no HTML sem
  escape na tela do laboratório.
- A aplicação ainda pode escrever informações sensíveis de configuração,
  incluindo senha do banco, no log. O diretório `data/logs/` não é mais
  versionado, mas a exposição local continua sendo um risco e o conteúdo logado
  deve ser sanitizado.
- `dashboard/data.json` gerado tem cerca de 16 MB e é carregado integralmente pelo
  navegador.

## Execuções LLM encontradas

Existem auditorias reais locais para PETR4 e WEGE3. Cada uma contém apenas duas
datas de decisão, terminou sem trades e não constitui experimento. Em WEGE3, uma
compra consensual foi vetada porque ainda não havia observações suficientes para
volatilidade. Outras rodadas tiveram quorum incompleto. Isso demonstra integração
com um modelo real e comportamento fail-safe em alguns caminhos, não desempenho.

## Documentação defasada ou contraditória

- `archive/PLAN_HEDGEFUND.md` descreve a intenção original e as fases 5–7, que
  não foram implementadas. A tabela de resultados é exemplo, não resultado
  observado.
- `archive/ROADMAP_IDEIAS.md` marca todo o sistema multiagente como pendente,
  embora uma primeira versão exista; esse roadmap foi substituído.
- `archive/HANDOFF_OUTRO_PC.md` diz que Prefect foi atualizado para 3.x; o
  `pyproject.toml` e o lock atuais usam Prefect 2.20.25.
- A monografia descreve um grafo cíclico capaz de pedir reavaliação; o grafo atual
  é linear e não possui retorno do risco ao analista.
- A monografia alterna escopo de dois ativos e universo de dez ativos, promete
  custo/turnover líquido ainda ausente e contém blocos duplicados de resumo,
  abstract, introdução, planejamento e considerações parciais.
- Marcadores `verify` e `remarks` permanecem no texto acadêmico e indicam trechos
  ainda não aprovados.

## Baseline honesta

O projeto pode ser apresentado hoje como:

> Protótipo de laboratório de dados e backtesting para ativos da B3, com cinco
> benchmarks clássicos, dashboard exploratório e uma primeira estratégia LLM
> single-asset organizada em quorum técnico, filtro de risco e dimensionamento de
> posição, com auditoria por decisão.

Ainda não deve ser apresentado como:

> Hedge fund autônomo, arena comparativa válida, sistema de negociação em tempo
> real, portfólio LLM multi-ativo ou evidência de superioridade de agentes.
