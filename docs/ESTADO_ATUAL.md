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
| Indicadores | Implementado | SMA 50/200, Bollinger 20/2, RSI 14 (Wilder canônico desde `LLM_FEATURE_SCHEMA_VERSION = 2`) e MACD 12/26/9. |
| Estratégias clássicas | Implementado | Buy & Hold, SMA Cross e Bollinger single-asset; Equal Weight e Mínima Variância multi-ativo. |
| Backtest clássico | Bloqueado para ciência | Single e multi-asset decidem com dados até o fechamento de `t`, executam na abertura observada de `t+1`, calculam custos sobre o notional e preservam caixa não negativo. Retorno, risco, drawdown e custo total agora vêm do módulo canônico. O motor comum existe na **camada experimental** (`ExperimentRunner`/`ExecutionEngine`), mas o **dashboard e os demais caminhos legados** ainda instanciam engines próprios com custo zero e não passam por ele. |
| Sistema de agentes | Parcial | Quorum técnico -> risco -> portfólio em LangGraph, com contratos Pydantic e regras duras. Opera um ticker por execução. |
| Quorum de 30 | Implementado com ressalvas | Faz 30 chamadas concorrentes do mesmo papel e cliente, variando temperatura (faixa 0.2–0.8, se `temperature` não for declarada) e seed registrado. No caminho causal o prompt é idêntico entre analistas; o rótulo "analista n de N" só sobrevive no caminho legado de níveis brutos. Exige 25/30 por padrão e todos os votos válidos. |
| Cliente LLM real | Parcial | Cliente HTTP OpenAI-compatible e cliente nativo da Gemini API (`provider="gemini"`), ambos com retry e telemetria. Erro HTTP é tipado: 400/401/402/403/404 e chave ausente são recusa não repetida (`PROVIDER_REQUEST_REJECTED`); 408/409/429/5xx, rede, timeout, corpo truncado ou não-JSON são transitórios, repetidos (respeitando `Retry-After`/`RetryInfo`) e, esgotados, `PROVIDER_FAILURE`. `gemini-3.8-flash` (API nativa v1beta) está TECHNICALLY QUALIFIED pelo DEV_SMOKE de 2026-10-04 para `temperature`, `max_output_tokens` e `thinking_level=low` (evidência em `docs/evidence/provider_runtime/`); `medium`/`high` e outros modelos seguem não qualificados. Escolha de provedor, modelo e nível continua `PENDING_ADVISOR_RATIFICATION`. |
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
`yfinance`, a política de ajuste **resolvida** (`auto_adjust=true`), a
representação de preço (`adjusted_total_return`), moeda, timezone da bolsa,
versão do Python/pipeline, commit e estado dirty do Git, além das regras e
exceções do calendário. Quando a captura de eventos corporativos está ligada,
`actions/<ticker>.csv` guarda dividendos e splits com SHA-256 na identidade do
manifest — evidência, não insumo do motor v1. Um ID existente
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
operação realmente executada. O executor usa `CostModel`, caixa não negativo e
posição long-only. A **quantidade depende do modo declarado**: `integer_shares`
(default, caminhos legados) trunca para ação inteira; `fractional_notional` (o
caminho científico, exigido em fase científica pelo runner) executa em unidades
fracionárias sintéticas da série de retorno total, sem `floor()` e sem resíduo
de arredondamento. Um intent na única/última sessão permanece uma decisão sem abertura
observada e não gera trade — o participante decide igual e não é informado de
que aquela era a última sessão. A observação contém cópias dos históricos
truncadas em `t` e nenhum campo sobre a sessão seguinte, portanto o participante
não recebe preços futuros nem o horizonte da amostra por esse contrato.

No caminho multi-ativo, o calendário é a interseção explícita dos índices, sem
forward-fill nem barra fabricada; os tickers são percorridos em ordem
determinística; e a alocação segue uma política puramente técnica: alvos e
deltas calculados sobre o patrimônio na abertura, vendas antes das compras e,
quando o caixa não cobre todos os déficits, escalonamento de todos os alvos pelo
mesmo fator, seguido de truncamento apenas em `integer_shares`. O fator vem de
busca binária sobre o custo reportado pelo `CostModel`, então o resultado não
depende da ordem dos tickers e não assume a fórmula de custo. Em
`fractional_notional` essa etapa deixa de compensar truncamento e passa a ser o
que torna a execução exequível: com peso alvo 1 e custo proporcional `r`, o alvo
custaria `equity·(1+r)` e o fator converge para `1/(1+r)`, zerando o caixa e
atingindo peso exato. Em `integer_shares` o resíduo de caixa continua existindo e
não é redistribuído.

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
  parâmetros calibráveis dos agentes, universo e plano estatístico continuam
  abertos, e `docs/EXPERIMENT_PROTOCOL.md` continua `DRAFT`. Já estão fechados:
  CostSpec, métrica primária, benchmarks primário/secundários, critério de
  CAL-A, capital, `long_target_weight` e warm-up (tabela da seção 5).
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
- **CostSpec científico congelado** (protocolo §10: `brokerage_fixed = 0.0`,
  `tax_rate = 0.000320`, `spread_bps = 5.0`), mas só entra nos runs que declaram
  esses valores na `ExperimentSpec`; o dashboard continua com custo zero.
- **Análise estatística ainda não executada.**

### 2. Custos não comparáveis

O dashboard instancia todos os motores com `CostModel()` padrão, isto é, custo
zero. Os motores agora calculam custos percentuais sobre
`abs(quantity * execution_price)`, reservam esses custos antes da compra e não
deixam o caixa negativo. Os valores científicos de corretagem, spread, slippage e
taxas estão congelados na seção 10 do protocolo, mas o dashboard não os usa, e
lote continua `TBD`; logo, os resultados do dashboard ainda não são uma
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
- `risk_free_rate = 0` está fechado no protocolo (§17.3, junto com
  `cash_return = 0`); `252` sessões/ano e MAR zero continuam defaults técnicos
  configuráveis.

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
quais parâmetros cada subfase pode alterar, a regra one-shot do CAL-B e o
critério de seleção do CAL-A (`S1`). **Nada disso foi executado** e nenhuma data
foi escolhida.

Estado factual de cada item:

| Item | Estado |
|---|---|
| Desenho pseudo-live (decisão em `close(t)`, execução em `open(t+1)`, relógio avançando uma sessão por vez) | Documentado; o mecanismo de execução já existe na arena e no `AgentBacktestEngine` |
| Calibração retrospectiva do sistema como etapa declarada | Documentada; nunca executada como fase formal |
| Janela base de mercado `>= 2 anos` | Aprovada conceitualmente; **mecanismo implementado**. `minimum_history_sessions` é campo obrigatório da `EvaluationSpec` e o gate falha antes de construir o participante. Valor **fechado**: `minimum_history_sessions = 504` sessões disponíveis até e incluindo `decision_start` (503 sessões comuns anteriores + a sessão de decisão). A janela continua expansiva (`snapshot[:t]`), por decisão registrada |
| Governança da CALIBRATION (subfases, autoridade por parâmetro, CAL-B one-shot, disjunção de datas) | Documentada em `EXPERIMENT_PROTOCOL.md` §5.12. Nenhuma subfase executada; nenhum baseline `B0` existe |
| Historical Memory | Não implementada. Nenhum corpus, retriever, embedding ou vector store |
| Calibration Cases, Validation, Final Test | Quantidade de âncoras decidida (`CORE = 30`, `CAL-A = 20`, `CAL-B = 10`, stress `<= 8` fora do CORE); **nenhuma data selecionada** |
| Decisões fechadas | `CAL_A_SELECTION_SCORE = S1` (média do retorno líquido realizado nas 20 âncoras); `long_target_weight = 1.0`; `minimum_history_sessions = 504`; `cash_return = 0` e `risk_free_rate = 0`; métrica primária = Sharpe anualizado líquido; benchmark primário = Buy & Hold; secundários = SMA e Bollinger; capital inicial = R$ 100.000; `risk_max_concentration = 1.0` no single-asset v1 (sujeito só ao amendment de autoridade já registrado) |
| Janela, duração e critério do Sequential Development, regra de síntese dos runs de Validation | `TBD`. Espaço de decisão delimitado no protocolo, valor não escolhido |
| Universo final, provider/model | `TBD` |
| Benchmark de mercado (índice) e escopo do amendment de benchmarks | `TBD_ORIENTADOR` — não reabre Buy & Hold nem SMA/Bollinger |
| Custos | **CostSpec congelado** (protocolo §10): `brokerage_fixed = 0.0`, `tax_rate = 0.000320` (B3 v5.0, OC 037/2026-PRE), `spread_bps = 5.0` (premissa conservadora ex ante); ADV check nominal, pior caso WEGE3 0,21%, evidência versionada em `docs/evidence/costspec_liquidity_check.json` |

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
  versionada. Moeda e timezone passaram a ser declarados no manifest, e o
  extractor passa `auto_adjust=True` explicitamente em vez de depender do
  default da versão instalada do provedor. O snapshot recusa recorte que alcance
  a sessão ainda em formação.
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
technical default = 0.25
scientific value  = 1.0   (EXPERIMENT_PROTOCOL.md §11, fechado)
```

O default técnico não é o valor científico: toda spec científica declara
`long_target_weight = 1.0` explicitamente.

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
registrada, não implementada; o harness de Diagnostic Hardening preserva o
trace da tentativa que falhou — inclusive quando o provedor cai no risco ou
no portfólio — e continua o lote; exceção fora do contrato (bug) interrompe
o lote como `HardeningAbortedError`, levando os outcomes já obtidos.

### H2 Methodological Freeze v1

Congelado pelos autores em 2026-10-04, antes de qualquer chamada de
Hardening: `docs/H2_METHODOLOGICAL_FREEZE_V1.md`. Spec do H2 em
`H2_FREEZE_V1_PARAMS` (gemini-3.8-flash nativo, SC 5 × 0.6, temperatura
1.0, 8192 tokens, `portfolio_inversion_policy="fail"`), escada de thinking
LOW → MEDIUM → HIGH, gates G-A/G-T/G-I/G-F e H_real reservado
(2019-04-08, 2020-06-29, 2021-09-17, 2022-12-07, PETR4.SA) a partir do
snapshot `20261004T193839031891Z-6f5e2439…`, que segue
`attention_required` por divergência do `B3Calendar` local (ver o freeze,
seção 7). CAL-A: `CAL_A_CANDIDATE_GRID_UNRESOLVED`.

Executado em 2026-10-04: Diagnostic Hardening com `thinking_level=low`
passou G-A, G-T, G-I (0.667) e G-F (0.0) → **LOW congelado**; passada **B0
PASS** (commit `4ec2ba9`). Evidência em `docs/evidence/h2/`. Nenhuma métrica
financeira foi calculada; CAL-A não foi aberto.

**Rebaseline (Amendment 1, 2026-10-04).** Calendário B3 v2 equivalente às
2649 sessões oficiais do COTAHIST; preço bruto oficial da B3 × fator do
yfinance; snapshot `20261004T201258177516Z-b4cf39fc…` READY. H_real
reaplicado pela mesma regra (2019-04-09, 2020-06-30, 2021-09-17,
2022-12-07). Hardening LOW passou de novo (G-I 0.633, G-F 0.0) → LOW
FROZEN — REBASELINED; B0 PASS — REBASELINED. As execuções anteriores estão
SUPERSEDED. Amendment 2: 30 estratos, CAL-A (20) e CAL-B (10, trancada no
runner) comprometidas por hash; grade de CAL-A {21, 63} × {0.40, 0.50,
0.60}; gate de identificabilidade: 7 âncoras distinguíveis → CAL-A
REDUCED.

**CAL-A executada (Amendment 3/4).** 360 avaliações pareadas (20 âncoras × 3
repetições × 6 configurações), CostSpec congelado. S1 idêntico nas seis
configurações → `CAL_A_DISCRIMINATION = NONE` → configuração 1 pelo
desempate (`volatility_window = 21`, `risk_max_volatility = 0.40`),
congelada (`CAL_A_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK`: desempate, não
desempenho superior). CAL-B, Stress, Validation e Final Test não foram
executados.

**Sequential Development (Amendment 5).** Congelados antes de qualquer
chamada: `H2_SCIENTIFIC_SHARPE_DEFINITION_V1`, janela 2024-03-01..2024-08-29
(liquidação 2024-08-30), invariante
`no_order_execution_may_cross_phase_boundary` no runner, grade D01/D02/D03 =
`risk_max_drawdown` 0.25/0.15/0.35, R = 3, escore S2.
Executado no commit `2461952`: 9/9 runs pareados, 0 falhas finais, CAL-B
intocada. O drawdown máximo (0.080) não alcançou nenhum limite da grade e os
três S2 foram exatamente iguais → `SEQUENTIAL_DEV_DISCRIMINATION = NONE` → D01
(`risk_max_drawdown = 0.25`) pelo `PROTOCOL_TIE_FALLBACK`, congelada. Stress,
Validation e Final Test não foram executados.

**Stress Probing (Amendment 6, `STRESS_PROBING_FREEZE_V1`).** Congelado antes
de qualquer seleção ou chamada: autoridade zero, H2 inteiro congelado, 4
janelas de um estrato completo cada, escolhidas por métricas só de mercado
(M1 drawdown, M2 volatilidade, M3 pior retorno, M4 gap overnight) entre os 20
estratos não-CAL-B, R = 3, fronteira de janela no runner (`boundaries`),
gates só de integridade (S-A, S-T, S-C, S-R) e probes determinísticos do
contrato de risco. Nada financeiro tem autoridade de seleção.
Janelas comprometidas (`9f06b09`): S1 estrato 11 (2020), S2 estrato 2 (2018),
S3 estrato 29 (2023), S4 estrato 4 (2018). Executado: 12/12 trajetórias, 0
falhas finais, 0 truncamentos, 0 violações causais/de fronteira, 0 violações
do contrato duro de risco → `STRESS PROBING COMPLETE — READY FOR CAL-B
PROTOCOL`. Regra de volatilidade exercitada (94 COMPRA vetadas antes do LLM);
regra de drawdown `NOT_EXERCISED` (drawdown máximo 0.179), limitação de
cobertura empírica. Nenhum parâmetro mudou; CAL-B, Validation e Final Test
não foram executados.

**CAL-B (Amendment 7, `CAL_B_PROTOCOL_FREEZE_V1`).** Congelada antes de
qualquer chamada: sanity check one-shot, sem performance e sem tuning; as 10
âncoras comprometidas × R = 1, decisão só com dados até close(t) e sem
execução em t+1; autorização limitada (fase, hash, datas, uma repetição) com
`CAL_B_AUTHORIZED` global ainda False; gates CB-A/S/C/R/D, revisão humana
independente dos dois autores e regra de status congelada.
Executada (`33785f9`): 10/10 âncoras seladas, CB-A/S/C/R PASS, **CB-D FAIL**
(9/10 HOLD, `total_hold_rate` 0.90) → `CAL_B_FAIL — HOLDOUT CONSUMED`,
`CAL_B_STATUS = CONSUMED`, `SYSTEM_CALIBRATION_COMPLETE = False`. Nenhuma
métrica financeira calculada; nada rerodado ou ajustado; uma nova versão
metodológica, se houver, é decisão fora desta fase.
Post-mortem (`docs/evidence/cal_b_v1/postmortem/`, CAL-B1 CONSUMED — NOW
DEVELOPMENT EVIDENCE, sem chamada nova): os HOLDs são do Technical (5/8
unânimes, nenhum via Risk/Portfolio); diagnóstico primário E — MIXED, com
mecanismo dominante na semântica de feature não especificada no prompt
(`bb_upper_gap < 0` lido como rompimento da banda superior em 27/40 votos das
âncoras HOLD, padrão presente desde o Hardening), além de conflito real
tendência/momentum em 5/8 estados e linguagem de cautela em 9/36 votos MANTER.

**H2 v2 (Amendment 8).** Única mudança: o system prompt técnico ganhou o
glossário semântico das 8 features e a regra estado-não-transição
(`technical_prompt_version = 2`); features, schema, N, quorum, geração, risco e
prompts de Risk/Portfolio idênticos. CAL-B2 comprometida antes de qualquer
chamada v2 (seleção determinística só por calendário; selada, não executada).
Hardening dirigido nas âncoras CAL-B1 consumidas: 0/150 contradições e 0/150
transições (v1: 32/50 e 33/50), hold 0.867 → `H2_V2 MINIMAL DEFECT FIX
PASSED`. Development v2 refeito com as regras da v1: Hardening e B0 PASS; CAL-A
v2 sem discriminação (21/0.40 por desempate); Sequential Dev v2 discriminou
(D02, `risk_max_drawdown = 0.15`, EMPIRICAL_S2); Stress v2 com todos os gates
de integridade PASS. Status: `H2_V2 DEVELOPMENT COMPLETE — READY FOR CAL-B2
PROTOCOL`. Validation e Final Test intocados.

**CAL-B2 (Amendment 9, `CAL_B2_PROTOCOL_FREEZE_V1`).** Congelada antes de
qualquer chamada sobre as datas CAL-B2: configuração final v2 (21 / 0.40 por
PROTOCOL_TIE_FALLBACK, drawdown 0.15 por EMPIRICAL_S2), compromisso
`518dd9dd…`, R = 1, batch selado, autorização limitada à fase, hash, datas,
versão do tratamento/prompt e spec hash; gates CB2-A/S/C/R/SEM/TRANS/D com o
checker v2 congelado por blob; revisão humana dos dois autores; nenhuma
métrica financeira.
Executada (`59533dc`): 10/10 âncoras seladas, 0 retry; os sete gates
automáticos PASS (0 contradição semântica, 0 transição, 7/10 HOLD,
`total_hold_rate` 0.70). `CAL_B2_STATUS = CONSUMED`. Estado:
`CAL_B2_AWAITING_HUMAN_REVIEW` até as fichas dos dois autores.

**H2 v3 (Amendment 10).** A CAL-B2 revelou um segundo defeito objetivo,
independente do Technical: em 2023-06-26 o Risk vetou dizendo que a confidence
0.462 estava "abaixo do limiar de 50%" — limiar que não existe no protocolo
nem no Risk. O conteúdo da CAL-B2 passa a ser development evidence; o status
histórico `CAL_B2_AWAITING_HUMAN_REVIEW` é preservado (fichas não preenchidas,
segunda revisão não aguardada) e `H2_V2_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE = True`
(razão: `CAL_B2 CONSUMED AND USED AS DEVELOPMENT EVIDENCE`). A v3 muda só o
system prompt do Risk (`risk_prompt_version = 2`); Technical v2 byte-idêntico,
reaproveitado por replay exato (`FROZEN_COMPONENT_REPLAY = TECHNICAL_V2`).
CAL-B3 comprometida antes de qualquer chamada v3 (`a5cadecd…`; selada, não
executada). Hardening dirigido nas âncoras CAL-B2 (R = 3): 0 limiar de
confidence, 0 regra numérica e 0 contradição em 9 respostas do Risk v3 →
`H2_V3 MINIMAL DEFECT FIX PASSED`. Development v3 refeito com as regras da v2:
Hardening e B0 PASS; CAL-A v3 selecionou 21 / 0.50 (EMPIRICAL_S1, uma âncora);
Sequential Dev v3 selecionou drawdown 0.25 (EMPIRICAL_S2); Stress v3 com todos
os gates PASS. 11010 respostas Technical v2 reaproveitadas, 0 divergência.
Observação: o Risk v3 aprovou 70/70 no development (v1 vetava 19/67, v2
18/73). Status: `H2_V3 DEVELOPMENT COMPLETE — READY FOR CAL-B3 PROTOCOL`.
Validation e Final Test intocados.

**CAL-B3 (Amendment 11, `CAL_B3_PROTOCOL_FREEZE_V1`).** Antes de qualquer
chamada sobre as datas CAL-B3, o checker do Risk passou à versão 2
(negação por construção na sentença; os 2 falsos positivos conhecidos de
`VERDICT_TEXT_CONTRADICTION` corrigidos, R1/R2/CONFIDENCE_ONLY idênticos no
corpus de development) e foi congelado. Configuração final v3 (21 / 0.50 por
EMPIRICAL_S1, drawdown 0.25 por EMPIRICAL_S2; spec `1d63ad4c…`),
compromisso `a5cadecd…`, R = 1, batch selado, autorização limitada à fase,
hash, datas, versões e spec; gates CB3-A/S/C/HR/TSEM/TTRANS/R1/R2/R3/D; sem
gate de mínimo de vetos do Risk LLM (`RISK_LLM_VETO_RATE_HAS_NO_MINIMUM_GATE`);
revisão humana de um autor (`PRIMARY_HUMAN_REVIEWERS_REQUIRED = 1`; segunda
revisão recomendada como auditoria posterior, não bloqueante); nenhuma
métrica financeira.
Executada uma vez (10 âncoras × R = 1, 57 chamadas, 0 retry): os dez gates
automáticos PASS (6/10 HOLD, total_hold_rate 0.60; 0 contradição semântica ou
transição nos 50 votos; 0 achado do checker do Risk; 0 violação de regra
dura). Risk LLM 3/3 APROVADO (`NOT_OBSERVED`, descritivo). CAL-B3 consumida;
status `CAL_B3_AWAITING_PRIMARY_AUTHOR_REVIEW`. Nenhum resultado financeiro;
Validation e Final Test intocados.

### Hardening pré-B0 — suporte implementado

Implementado como engenharia, sem rodar CAL-A, CAL-B, Stress científico,
Validation ou Final Test, e sem usar resultado financeiro:

- **Self-Consistency suportado.** No caminho causal o prompt lógico é idêntico
  entre os analistas; `analyst_id` fica só em metadado e na identidade do trace.
  `temperature`, `thinking_level` e `max_output_tokens` declarados chegam
  explicitamente a técnico, risco e portfólio. A configuração provisória
  (`analyst_count=5`, `consensus_threshold=0.6`, `temperature=1.0`,
  `decision_frequency=1`, `strict_inputs=True`,
  `portfolio_inversion_policy="fail"`) está em
  `src/experiments/hardening.py` como `H2_SC_PROVISIONAL_PARAMS` —
  `PENDING_ADVISOR_RATIFICATION`.
- **`decisions.jsonl`**, causas finais estruturadas e `BUY_AT_TARGET_NOOP`
  (protocolo, seção 13). O no-op só é usado quando nenhuma intenção é
  emitida e compara o peso na mesma representação canônica da regra de
  concentração.
- **Fail-closed** com `strict_inputs=True`, exigido pelo runner em fase
  científica. Falha do provedor em qualquer papel — técnico, risco ou
  portfólio — vira `LLMDecisionError` com causa estruturada e registro em
  `decisions`, nunca exceção de transporte crua nem `MANTER`.
- **Preflight científico** antes de construir o participante (protocolo,
  seção 14): todo parâmetro material escrito na spec, sem default
  invisível, e qualificação empírica do modelo — hoje só
  `gemini / gemini-3.8-flash` com `thinking_level=low`, por DEV_SMOKE
  técnico; isso não autoriza fase científica antes do freeze metodológico.
- **RSI canônico de Wilder** e `LLM_FEATURE_SCHEMA_VERSION = 2`, verificado
  contra a planilha primária `cs-rsi.xls` da StockCharts em 2026-10-04.
  NaN no preço é recusado. `0/0 → 50` é convenção local.
- **`indicator_family_control`**: indicator-family-matched classical control
  (SMA 50/200 + Bollinger 20/2 + RSI 14 + MACD 12/26/9, soma com pesos iguais).
  A direção da regra de RSI é `PENDING_ADVISOR_RATIFICATION`.
- **Conjunto H dedicado** (`src/experiments/hardening.py`): oito geradores
  sintéticos determinísticos versionados (`H_SYN_VERSION = 1`), infraestrutura
  para estados reais reservados (`H_REAL_SESSIONS` vazio; `real_state` exige
  os conjuntos reservados e recusa sobreposição), harness que decide sem
  liquidar, diagnósticos de inatividade e de instabilidade no mesmo estado
  e gates propostos 0,90 / 0,10 marcados `PENDING_ADVISOR_RATIFICATION`.
  H_syn v1 está congelado por digest do payload canônico de cada estado
  (`H_SYN_PAYLOAD_DIGESTS`). Limitação declarada: todo estado de H parte de
  carteira zerada, então concentração, drawdown e `BUY_AT_TARGET_NOOP` não
  são exercitados por H_syn — só por fixtures unitárias separadas.

Nenhum probe científico foi executado, nenhum `thinking_level` ou modelo foi
escolhido e nenhum B0 foi gerado.

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
