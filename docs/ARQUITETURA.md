# Arquitetura atual do Hedge-Fund-Lab

Mapa técnico de referência em **14/10/2026 — V7.6.5 e ponte sintética PAPER-02**.
[Direção](DIRECAO_DO_PROJETO.md) · [Estado](ESTADO_ATUAL.md) ·
[Roadmap](ROADMAP.md) · [Documentação](README.md).

## Fronteiras do sistema

**15/10 — explorador Yahoo DP-25 / APP-03:** `stock_history_api.py` e
`stock-explorer.js` separam o histórico longo de ações da marcação patrimonial.
GET `/api/portfolio/stock-history?wallet=...` verifica e lê cópias locais;
POST `/api/portfolio/stock-history/refresh` exige fronteira local, CSRF e JSON
estrito e consulta yfinance `period=max`, `interval=1d`, `auto_adjust=False`,
`repair=False`, com corte na sessão já encerrada. O normalizador/validador existente
marca barras inválidas como lacunas; CSV original é preservado. Publicador atômico
existente grava snapshots imutáveis com hash e troca somente latest. Atualização
concorrente é recusada; até três downloads simultâneos, universo limitado a 20.
Falhas conservam snapshots anteriores. Respostas JSON extensas negociam gzip
pela biblioteca padrão. A UI filtra em memória, permite ativos/períodos/séries e
mede endpoints por pointer events; não promove Yahoo a marca B3 nem escreve no ledger.

**15/10 — marcação e gráficos pessoais DP-04/05/17/23 / APP-03:**
`portfolio_history_api.py` atende GET `/api/portfolio/history?wallet=...`, com a
fronteira local Host/Origin existente. Reutiliza catálogo/replay do ledger pessoal,
calendário limitado DATA-01 e validação dos inputs Radar registrados não sintéticos.
Preço vem de `raw_bar.fechamento`, com hashes/OHLCV/disponibilidade verificados;
referências divergentes ficam indisponíveis. Cache em memória é limitado e indexado
pelos hashes dos arquivos/manifest. Não há download, inferência ou gravação no ledger.
`personal-charts.js` acompanha o evento de seleção existente, confere revisão e
usa Chart.js já instalado: evolução pela data econômica e preços por ativo abaixo
das posições, com tabelas acessíveis. Posições atuais marcadas ao último fechamento
formam estimativa separada da série diária; ausência de fechamento permanece null.
Histórico incorpora correções atuais, sem se apresentar como versão conhecida no
passado. Cobertura restrita às referências preservadas; eventos/proventos, coleta
contínua e comparação financeira entre carteiras ainda exigem integração.

**15/10 — gestor pessoal DP-21/24 / APP-05:** `wallet_manager_api.py` e
`wallet-manager.js` estendem Resultados do Radar, com GET de histórico e POSTs
prepare/preflight/run/replay/preview/apply em `/api/platform/wallet-manager`.
Host/Origin/CSRF/JSON estritos são os mesmos da plataforma. O contexto congela
revisão/posições/caixa, alvo, pareceres, custos e RAW CLOSE; uma nova identidade
reutiliza transporte durável, CallBank e schema validation do Global PM sem
alterar tratamentos selados. O compilador valida quantidades/sinais/caixa e deriva
a tabela antes/depois. `manual_portfolio_api.batch` usa o mesmo escritor TRADE
e replay dentro de uma transação SQLite única, com vínculo à proposta, revisão
e idempotência por cesta. Propostas não gravam posições; somente aprovação
financeira posterior registra simulação manual hoje aos preços de referência.
Sem preços ao vivo, broker, liquidação ou qualificação de risco global; carteira
externa e Buy & Hold recusam aplicação automática. APP-03/04 seguem pendentes.

**15/10 — frontend DP-23:** `product.css` aplica a identidade clara aprovada,
carregada pela shell após os tokens existentes. `product.js` conduz navegação e
contexto, os read models de comparação/prontidão e as etapas visíveis de Agentes.
`PRODUCT_PAGES` serve `/operations`, `/comparison`, `/dividends`, `/wallets/new`
e `/laboratory` com o HTML pessoal existente; `/data` tem página própria de consulta.
GET e HEAD usam o mesmo mapeamento. `manual-portfolio.js` preserva os POSTs e o
replay existentes; seleção e criação preservam a rota e carregam a carteira nos
links. Em Laboratório/Legacy/demonstração, o seletor pessoal fica desabilitado para
não substituir identidades de ledgers anteriores. `radar.js` reutiliza preparar,
poll de job e preflight no comando guiado; inferência conserva os gates anteriores.
Trocar de etapa descarta consentimento ainda não confirmado, sem cancelar worker
ou alterar autorizações gravadas. Nenhum novo escritor financeiro ou dependência.

**15/10 — análises por carteira (DP-22):** `radar_analysis_api.py` estende a
plataforma com cadastro de execução; `radar-analysis.js` fornece escolha de
carteira, alvo, referência e histórico no Radar. Reutiliza o SQLite pessoal em
consulta e `radar_runs.register/select` para identidades. `wallet-analysis.json`
guarda snapshot/revisão, datas, classificação e request selados e imutáveis.
O servidor serializa cadastro, gate/dispatch Radar e autorização de orçamento
com um RLock compartilhado antes de trocar o ROOT do worker existente. Não troca
raiz com worker ativo/lock pendente; header de execução anterior continua recusado.
Repetição do mesmo command_id recupera a criação interrompida/confirmada sem
duplicar registro. Não altera os módulos selados Radar/comitê/registry.
Posições e dia-alvo não entram nos prompts selados dos comitês por ativo. Entram
no novo gestor pessoal descrito acima; o registro é uma simulação manual explícita,
sem ativar execução prospectiva. [Fluxo e limites](CICLO_USO_PLATAFORMA.md).

```text
Dados observados + proveniência → indicadores → agentes → consenso → risco
                                                               │
                    H2/PETR4                                   │ Radar multiativos
                    decisão H2                                 pareceres por ativo
                    contratos próprios                         Global PM + validador
                    ledgers H2                                 proposta consultiva
                         │                                          │
                         └────────── APIs de consulta ──────────────┘
                                         │
                               dashboard Python/HTML/JS

Ledger multiativos V7.6.5: qualificação SINTÉTICA isolada → exportação → GET/UI
Proposta consultiva → execução paper OFICIAL multiativos: integração ainda pendente
```

O desenho resume responsabilidades, não coloca os tratamentos no mesmo pipeline
financeiro. Uma proposta validada não cria posição. A UI apresenta estados;
contratos/runners próprios continuam sendo autoridade para decisões e contabilidade.

DP-16: na web, `/legacy` reúne `/legacy/paper`, `/legacy/h2` e
`/legacy/backtests`. `/paper`, `/h2` e `/index.html` continuam aliases de consulta,
sem alterar query/fragmentos. POSTs de `/api/forward/*` (prepare, preflight, run,
benchmarks, supervision/sync, approve, reject, cancel, scenario) e `/api/h2/*`
são recusados com `403 legacy_read_only`, antes de despacho/escrita. GETs e
controles compartilhados Radar/Gestor Global permanecem disponíveis. A home usa
`active_overview`, sem consultas ao experimento independente; `overview` continua
como projeção histórica para o CLI existente e GETs `readiness`/`legacy-overview`.
Runners, contratos, CLIs, ledgers, reservas, autorizações e pendências não mudam.

## Mapa de componentes

| Camada | Caminhos | Responsabilidade e limite |
|---|---|---|
| Dados/indicadores | [pipeline](../src/pipeline/), [indicadores](../src/indicators/) | ETL/cache, validação, snapshots e features; fonte/representação dependem do tratamento |
| Entrada local DATA-01 | [pilot_market_data](../scripts/pilot_market_data.py), [checks](../tests/test_pilot_market_data.py) | Manifest + ZIP local → bundle RAW verificável; reusa parser/validador; calendário sintético separado do verificado; sem feed/ledger |
| Agentes | [agents](../src/agents/) | Clientes, respostas estruturadas, analistas, risco, portfólio e grafo; configuração genérica não substitui identidade congelada |
| Backtesting | [backtesting](../src/backtesting/), [strategies](../src/strategies/) | Motores/estratégias históricos; não são o ledger prospectivo novo |
| Arena comum | [experiments](../src/experiments/) | Spec, participantes, execução comum e resultados; LLM da arena é single-asset |
| H2 original | [runner forward](../scripts/run_h2_v6_forward.py), [API](../dashboard/forward_api.py) | Decisão, estado e reconciliação segundo contrato H2 original |
| H2 supervisionada | [runner](../scripts/run_h2_v6_supervised.py) | Aprovação vinculada a proposta/prazo, independente da original |
| Benchmarks H2 | [runner](../scripts/run_h2_v6_forward_benchmarks.py) | Carteiras determinísticas independentes |
| Radar | [multiasset_radar](../scripts/multiasset_radar.py), [radar_api](../dashboard/radar_api.py) | Pareceres por ativo, dados e comitês; sem ordem financeira multiativos |
| Global PM | [V1](../scripts/multiasset_global_pm.py), [V2](../scripts/multiasset_global_pm_v2.py), [platform_api](../dashboard/platform_api.py) | Contexto, proposta, validação e evidência; históricos V1/V2 preservados |
| Motor financeiro reutilizado | [multiasset_portfolio](../scripts/multiasset_portfolio.py), [multiasset_manager](../scripts/multiasset_manager.py) | Contabilidade/contratos V5 reutilizados sem reescrever fontes selados |
| Ledger novo | [paper_ledger](../scripts/paper_ledger.py), [qualificador](../scripts/qualify_paper_ledger.py) | Envelope, Store SQLite, eventos/replay e reconciliação; escrita restrita a TEMP sintético |
| Ponte PAPER-02 | [pilot_paper](../scripts/pilot_paper.py), [ensaio](../scripts/qualify_pilot_paper.py), [checks](../tests/test_pilot_paper.py) | Reuso local das funções V5/V765, sem mutar globais; CLOSE t/autorização/intenção → OPEN t+1; políticas sintéticas separadas, D+2 e projeção JSON; mesmos guardas TEMP |
| Início demonstrativo UX-M3/M5 | [leitura](../dashboard/pilot_api.py), [preparação](../scripts/prepare_pilot_demo.py), [página](../dashboard/platform.html), [checks](../tests/test_pilot_home.py) | Exportação selada PAPER-02 preparada explicitamente → GET sem SQLite/escrita → seletor, métricas, posições e gráfico local; classificação sintética e períodos/lacunas calculados no backend |
| Consulta de carteiras | [monitoring_api](../dashboard/monitoring_api.py), [paper_ledger_api](../dashboard/paper_ledger_api.py) | Projeções de H2/snapshot PM e exportação sintética; GET não avança sessões |
| Interface | [server](../dashboard/server.py), [monitoring.js](../dashboard/monitoring.js), [design system](../dashboard/) | Rotas e apresentação; evolução para carteira inicial está no roadmap |

O pipeline genérico yfinance/PostgreSQL continua disponível. O Radar oficial
usa COTAHIST com ajustes documentados; a contabilidade prospectiva nova exige
preços RAW e disponibilidade temporal próprios. Não trocar uma fonte pela outra
nem misturar preços ajustados, marcas, fills e dados sintéticos.

## Persistência e autoridades

APP-01/02, DP-17–DP-19: a home também mantém o fluxo pessoal **criar → prévia →
confirmar operação → consultar**. `dashboard/manual-portfolio.js` usa GET
`/api/portfolio/manual` e POSTs `/api/portfolio/manual/preview|confirm`; o servidor
reutiliza Host/Origin/CSRF/JSON estrito, sem nova autenticação. O detalhe é a
própria carteira selecionada na home. `/portfolio` passa a se chamar **Gestor e
demonstrações**, preservando rotas, consultas e simuladores anteriores.

`dashboard/manual_portfolio_api.py`, identidade `HFL-MANUAL-PORTFOLIO-V1`, grava
somente `data/platform/manual-v1/manual.sqlite3`. GET não cria banco; prévia é
somente leitura. SQLite `BEGIN IMMEDIATE`/`synchronous=FULL`, comando UNIQUE e
eventos imutáveis encadeados por hash garantem transação/repetição. Confirmação
revalida a revisão da prévia. Replay ordena data econômica e sequência original
de lançamento no mesmo dia; correções retêm essa precedência. Cada leitura
recalcula posições/caixa do mesmo histórico, sem saldos paralelos.

DP-20 acrescenta metadados opcionais de criação para as duas simulações:
estratégia `BUY_HOLD`/`MULTIAGENT`, grupo de base inicial manual e nota de origem.
Não alteram o motor nem ativam agentes; preservam o vínculo das carteiras que
serão usadas em APP-05. `ARCHIVE` exclui somente cadastros sem lançamentos do
catálogo ativo, mantendo evento original e motivo; posteriores escritas são
recusadas. Usa a mesma prévia/revisão/confirmação/transação, sem migração física
ou remoção de trigger. Links antigos recuperam a seleção com aviso na home.

Reuso: `multiasset_portfolio` fornece Decimal, centavos, unidades, símbolos,
selos e `fill` (quantidade/base/resultado), vinculado pelo `pilot_paper.bind`
existente a custos declarados e reconciliação pessoal. Fontes V5/V2/V765 intactos.
O adaptador é **contabilidade econômica**, sem calendário de liquidação,
autoridade de execução, política de risco dos agentes ou taxa automática de 0,1%.
Referência de execução temporária no cálculo nunca sai como cotação atual.
DATA-01 e seus leitores continuam separados até APP-03; ausência de preços não
impede o registro pessoal, mas impede patrimônio marcado com posições e retorno.
Veja o [contrato pessoal](PILOTO_MULTIATIVOS_SPEC.md#15-app-0102--registro-pessoal-persistente-pela-interface).

| Área | Origem dos registros | Situação |
|---|---|---|
| Carteiras pessoais APP-01/02 | SQLite próprio `data/platform/manual-v1/manual.sqlite3` | Cadastro/operações/correções pela home; simulação ou real externa, fora do piloto; sem cotação/proventos/ordens |
| H2 prospectivo | Ledgers independentes em `data/forward` | Evoluem exclusivamente pelos runners e regras originais |
| Radar/Global PM | Raízes de runs e registros em `data/radar`, `data/global_pm`, `data/platform` | Pareceres/propostas e evidências; não são posições executadas |
| Ledger novo | SQLite temporário na qualificação; exportação em evidências V7.6.5 | Sem raiz oficial durável nem avanço diário ativo |
| Evidência científica | Protocolos, manifests, hashes, journals e checkpoints | Preservar identidade, bytes e caminho quando vinculados à qualificação |
| Documentação ativa | Direção, roadmap e estado | Resumos/planejamento; não substituem autorização nem protocolo |

## Lacunas para o produto decidido

DATA-01 já qualifica importação local RAW com fixtures, hashes, disponibilidade
na importação e revisão explícita. Não é feed oficial: calendário verificado
continua até agosto/2026; datas do piloto real permanecem bloqueadas. O segundo
incremento verifica [documentos B3 preservados](evidence/pilot_market_data_2026/sources.json)
e aceita formato diário pós-D0, sem expor registros antigos ao parser. Artefato
documental `b3-2026` comprova feriados, mas não fornece lista positiva operacional.
Origem de aquisição exige catálogo independente, ainda vazio; não há bundle real.
[Contrato do adaptador](PILOTO_MULTIATIVOS_SPEC.md#9-data-01--mecanismo-implementado-e-qualificado-offline).

PAPER-02 entrega o ciclo sintético em oito sessões e `projection.json` para duas
carteiras independentes. `Store` reutiliza o bytecode/transações do escritor V765
com redutor/identidade locais; o esquema físico SQLite permanece V1. Redutor novo
e antigo recusam identidades cruzadas. Reserva/fill/custos/centavos V5 usam
dependências locais de política/calendário; risco usa somente warm-up sintético.
Todos os arquivos antigos permanecem intactos. A classificação nunca é promovida.
Detalhes e relógios: [contrato implementado](PILOTO_MULTIATIVOS_SPEC.md#11-paper-02--ensaio-integrado-exclusivamente-sintetico).

Para ativação oficial faltam calendário prospectivo, ingestão RAW oficial, eventos corporativos, primeiro fill causal observado,
autorização humana oficial, persistência/backup, atualização/reconciliação diária
e comparação operacional com referências definidas. A experiência de carteira
como início, seletor, períodos e gráfico conjunto DP-02–DP-05 está implementada
em modo demonstrativo explícito; ativação oficial permanece separada.

`GET /api/portfolio/pilot?demo=1` lê `HFL_PILOT_DEMO` ou o caminho controlado
`data/platform/pilot-demo.json`. Não aceita caminho por URL. Confere selos,
schema/identidade/classificação, replay e igualdade da projeção PAPER-02;
retorna somente campos públicos de apresentação, sem journals/contextos privados.
Bytes são relidos a cada GET; cache limitado é por bytes + fingerprints, não por
nome/mtime. Arquivo ausente/inválido não tem fallback. `prepare_pilot_demo.py`
é o único fluxo de preparação: usa qualificador existente em TEMP, publica
exportação nova com `x` e reutiliza arquivo existente somente após validação.

Backend calcula âncoras/cobertura e ΔR$/% a partir de snapshots completos;
JavaScript apenas apresenta valores. A última marca reconciliada é a referência,
mesmo quando há sessão posterior pendente. Gráfico inclui `null` em lacunas do
calendário, sem conectar pontos ausentes. O laboratório anterior fica expansível,
com anchors/readiness/auditoria e navegação preservados. Não há servidor/framework novo.

O plano está no [roadmap](ROADMAP.md); detalhes técnicos do ledger estão em sua
[arquitetura](evidence/hfl_paper_ledger_v765/LEDGER_ARCHITECTURE.md),
[contabilidade](evidence/hfl_paper_ledger_v765/ACCOUNTING_INVARIANTS.md),
[persistência](evidence/hfl_paper_ledger_v765/PERSISTENCE_AND_RECOVERY.md) e
[limitações](evidence/hfl_paper_ledger_v765/LIMITATIONS.md).

A [arquitetura V7](HFL_PLATFORM_ARCHITECTURE.md) é referência versionada da
plataforma, anterior à migração UX e ao ledger novo. O
[documento geral anterior](archive/ARQUITETURA_NUCLEO_ATE_V765.md) preserva os
detalhes extensos da arena e desenhos históricos; não orienta novas prioridades.
