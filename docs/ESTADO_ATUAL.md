# Estado atual do Hedge-Fund-Lab

Estado em **16/10/2026**, base V7.6.5 e incrementos datados abaixo, incluindo APP-01/02 e cadastro de análises por carteira.
Foram lidos código, relatórios e resultados de qualificação existentes.
Não foram reexecutados experimentos nem auditados os estados financeiros
correntes. Na organização inicial foram executados apenas checks de
documentação, lint e preservação. DATA-01 chegou a 47 checks direcionados
na extensão abaixo (19 novos, 24 anteriores e 4 do parser);
PAPER-02 reexecutou checks direcionados da integração e contratos reutilizados,
conforme registro abaixo. Os resultados da suíte completa são históricos.
Estado financeiro corrente exige leitura datada.

## Acervo intradiário Yahoo — DP-26 / APP-03, 16/10/2026

O mesmo **Histórico das ações** passou a mostrar o preço ao longo do dia. Até 60
pregões no período, o gráfico usa barras intradiárias, sem ajuste: 1 pregão em
1 min, até 5 em 5 min, até 15 em 15 min e até 60 em 1 hora. Acima disso, e na série
ajustada por proventos, continua o diário. Novo botão **1D**; 1D/5D/1M incluem o
pregão aberto, com última barra, horário da consulta e aviso de ~15 min de atraso.

Medido em 16/10: o Yahoo guarda 1 min por ~30 dias (7 por consulta), 5 min por
60 e 1 hora por 730. Por isso, [o leitor/coleta](../dashboard/stock_history_api.py)
grava cada pregão fechado uma única vez em
`data/platform/stock-history-v1/<ativo>/intraday/<dia>/<intervalo>.json`
(selado, imutável, OHLCV como recebido), na melhor resolução ainda disponível.
O dia aberto fica só em memória e é arquivado depois das 18h. Uma resolução
mais grossa só ocupa um dia recente se a mais fina já foi consultada sem barras.
A coleta roda ao abrir a página, no botão **Atualizar histórico Yahoo** e a cada
2 min enquanto o período inclui o pregão aberto e a aba está visível; sem scheduler.
Abrir a página ao menos a cada ~3 semanas evita perder dias em 1 min.

Carga inicial real: 5 ativos × 496 pregões (17/10/2024 a 15/10/2026), sem
pregão faltando: 20 em 1 min, 21 em 5 min e 455 em 1 hora por ativo; 35
consultas, 19 s, 22 MB no total do diretório. Minutos de leilão sem negócio
(10:00–10:04 e 16:55–16:59) vêm vazios, ficam no arquivo e não viram lacuna.
Barras incoerentes viram lacuna, sem reparo. A última barra de 1 min é 16:54,
sem o leilão de fechamento, então difere em centavos do fechamento diário
(ex.: VALE3 13/10: 67,26 contra 67,16). Desdobramento futuro deixa os dias
antigos na escala antiga. Nada disso vira marca B3, preço de operação ou input
dos agentes.

Verificação: **9 testes** do explorador (2 novos: camadas, pregão em memória,
sem repetir consultas, lacuna, falha da camada fina e cópia corrompida);
Chrome desktop/celular com coleta respondida localmente validou 1 min, 5 min,
15 min e 1 hora a partir do acervo real, arraste, tabelas e troca de carteira.
Endpoint real às 14:57 devolveu barras de hoje até 14:42 nos cinco ativos.
O check de navegador também deixou de fixar a curva de patrimônio em três pontos.
Suíte completa: 1.991 passaram e 39 falharam, nenhuma em teste que use o
explorador. As falhas são de testes antigos em desacordo com o estado atual:
menu DP-23 com 8 links (esperavam 5), Legacy somente consulta (403 onde
esperavam 400), hashes de preservação/selos e `pipeline/test_flows`. Sem
linha de base limpa para comparar; ficam para uma revisão própria.

## Explorador de histórico das ações — DP-25 / APP-03, 15/10/2026

**Histórico das ações**, abaixo das posições, agora permite selecionar uma ação
ou várias, 5D/1M/6M/YTD/1A/5A/Máx, datas personalizadas, reais/percentual e série
Close/Adj Close. Arraste com mouse ou toque mede duas datas efetivas e apresenta
preços, diferença em reais e percentual por ativo. Campos de data oferecem o
mesmo cálculo sem depender do arraste. Endpoint ausente não é substituído por
outro dia; lacunas continuam visíveis.

[Leitor/coleta](../dashboard/stock_history_api.py) e
[interface](../dashboard/stock-explorer.js) usam yfinance já instalado e Chart.js.
Coleta real autorizada pelo pedido DP-25: **33.367 registros diários** dos cinco
ativos, desde janeiro de 2000 (ITUB4 desde dezembro de 2000) até 14/10/2026.
**81 barras incompletas/inconsistentes** ficaram como lacunas, sem reparo.
CSV recebido e snapshots com hashes são preservados em
`data/platform/stock-history-v1/<ativo>`; só o ponteiro latest é substituível.
Falha de atualização conserva a cópia anterior. Abrir/trocar filtros só lê o
cache; **Atualizar histórico Yahoo** dispara coleta explícita protegida por
Host/Origin/CSRF/JSON estritos, sem scheduler ou IA.

Close Yahoo é identificado como ajustado por desdobramentos; Adj Close inclui
ajustes por proventos. Nenhuma dessas séries vira marca contábil B3, operação
ou input selado dos agentes. Gráfico diário não oferece intradiário/tempo real;
Máx significa o máximo devolvido pelo provedor, sem garantia de toda a vida do ativo.
Sem preço em um dos extremos, o percentual é indisponível. Histórico recebido
agora pode incorporar revisões posteriores às datas históricas.

Verificação: **44 testes e 9 subchecks** passaram; sete checks do explorador,
incluindo fonte/ajustes/corte, lacunas, preservação, corrupção, falhas, concorrência,
CSRF/origem/JSON e transporte gzip. Chrome desktop/celular validou Máx desde 2000,
filtros, seleção, percentual, arraste por mouse/toque, tabelas e troca de carteira,
com POSTs/rede externa bloqueados. A coleta real foi feita separadamente; ledger
pessoal permaneceu idêntico. Suíte completa não executada.
Ruff, documentação (341 links), whitespace e preservação aprovados
(`violations: []`). Servidor 8085 recarregado; resposta completa dos 33.367
registros conferida em HTTP 200/gzip (cerca de 500 KB), sem mudança no ledger.
Próximo passo: qualificar atualização/mark-to-market e comparação patrimonial,
mantendo este explorador independente das regras de execução.

## Gráficos pessoais e patrimônio de referência — DP-02/04/05/17/23, APP-03, 15/10/2026

Incremento anterior deste dia; o gráfico de ações RAW curto abaixo foi substituído
pelo explorador DP-25 acima. Patrimônio e posições continuam usando esse leitor B3.

Na home, a carteira selecionada mostra patrimônio estimado, posições marcadas,
gráfico de evolução e, abaixo de **Suas posições**, preços das ações dia a dia.
O segundo gráfico alterna reais/variação percentual; legendas permitem selecionar
séries e tabelas apresentam os valores sem depender do canvas.

[Leitor](../dashboard/portfolio_history_api.py) e
[interface](../dashboard/personal-charts.js) reutilizam replay/Decimal e Chart.js,
sem novo escritor financeiro. GET verifica inputs congelados de execuções Radar
registradas não sintéticas; usa somente o CLOSE **RAW**, nunca o fechamento
ajustado ou custo médio. Hashes, disponibilidade e OHLCV são conferidos; conflito
de referências fica como lacuna. A consulta não baixa preços nem chama agentes.

Há referências locais de **09, 13 e 14/10**. As carteiras começaram em 14/10:
o ponto inicial é capital cadastrado, distinto do fechamento desse dia.
Na Multiagentes, o fechamento de 14/10 resulta em **R$ 99.835,33**. As posições
atuais, incluindo operações de 15/10 e custos corrigidos, valem **R$ 99.831,60**
aos mesmos preços de 14/10; essa estimativa não vira fechamento de 15/10.
Falta de cotação interrompe a linha, inclusive no dia ainda não encerrado.

Histórico é reconstruído pela data econômica, com as correções atuais; originais
continuam no ledger. Referências foram conhecidas/preparadas agora, sem alegar
disponibilidade retroativa. Cobertura curta, calendário limitado e ausência de
proventos/eventos registrados impedem tratar isso como série completa de retorno.
Comparação entre carteiras, coleta contínua, preços ao vivo, APP-04 e ativação
prospectiva permanecem pendentes. DATA-01/PAPER não são promovidos por essa consulta.

Verificação: **53 testes e 9 subchecks** passaram, incluindo replay histórico,
correções, lacunas, conflitos, RAW/ajustado, disponibilidade, cache e GET sem escrita.
Chrome desktop/celular conferiu os dois gráficos, valores, troca de carteira,
modo percentual e ausência de overflow, com POSTs e rede externa bloqueados.
Ruff, documentação (339 links), whitespace e preservação passaram, com
`violations: []`. Servidor 8085 atualizado; home, script e API responderam 200,
com bytes do ledger pessoal inalterados após as consultas.
Suíte completa não executada. Próximo passo: ampliar cobertura RAW com origem,
data e disponibilidade, mantendo eventos e preços ao vivo como integrações próprias.

## Gestor da carteira e cesta simulada — DP-21/24, APP-05, 15/10/2026

**Correção autorizada em 15/10:** custos das duas movimentações já registradas
da Multiagentes corrigidos de 5% para 0,03%, por pedido explícito de Lucas.
Total R$ 622,85 → **R$ 3,73**; caixa R$ 7.113,59 → **R$ 7.732,71**. Quantidades
e preços preservados. Duas CORRECTION atômicas/idempotentes, backup verificado e
originais/proposta imutáveis. Tela informa a correção e distingue custos registrados
da taxa original usada pelo gestor. Chrome somente GET, reconciliação e repetição
conferidos. [Registro, escopo e recibo](daily/2026-10-15.md). Não define taxa geral.

Em **Agentes → Resultados**, [gestor](../dashboard/wallet_manager_api.py) e
[interface](../dashboard/wallet-manager.js) recebem o snapshot da carteira,
dia-alvo, pareceres íntegros e CLOSE RAW B3 congelado. O gestor propõe quantidades
de compra/venda/manutenção, inclusive venda parcial ou saída total. O backend
deriva posições/pesos antes/depois, valores, custos declarados e caixa restante;
rejeita venda descoberta, crédito, cesta incompleta, frações e operações contrárias
ao parecer/veto. Não converte confiança em peso nem aplica automaticamente 85%.

Refinamento DP-23/24: ação **Executar plano simulado → Ver prévia** no início do resultado, antes da
justificativa/tabela. Campo de taxa explicita que 5 representa 5% por operação.
Proposta existente e custos preservados, sem executar a cesta de Lucas.
Fluxo revalidado no Chrome desktop/celular com provedor falso e SQLite isolado;
GET da página confirmou os controles antes da justificativa/tabela. Docs/diff passaram.

Lucas escolheu **simulação manual aos preços de referência mostrados**, com
custos informados na tela. Inferência tem preflight/consentimento próprio, uma
chamada sem retries automáticos, reserva conservadora e diário durável reutilizados
do Global PM. O contrato novo não modifica V1/V2 ou resultados antigos. Contexto,
resposta, autorização e evidências ficam em `wallet-manager/<id>` sob a execução
Radar. Contratos anteriores permanecem consultáveis após mudança do código.

Prévia e aprovação financeira separadas registram toda a cesta em uma transação
no SQLite pessoal, reutilizando TRADE/replay/correções/hash chain. Repetição e
concorrência não duplicam; falha reverte a cesta inteira. Cada operação guarda
run/proposta/hashes, referência, custos e data econômica; o histórico de Operações
leva à proposta. Revisão desatualizada exige nova análise. Buy & Hold e carteiras
externas são consultivas para este fluxo, sem rebalanceamento/negócio simulado.

Limites: apenas referência histórica explícita, registro econômico na data de hoje;
sem cotação ao vivo, OPEN futuro, D+2, eventos corporativos ou qualificação de risco
global. O gestor exige todos os pareceres do universo selecionado completos e
todas as posições cobertas. APP-03/04 e ativação prospectiva continuam pendentes.
Histórico de rejeições explícitas, todas as tentativas de prévia/preflight e backup
independente ainda não constituem auditoria integral da aplicação.

Verificação: checks em [test_wallet_manager.py](../tests/test_wallet_manager.py),
incluindo transporte nativo falso/diário/replay offline, venda parcial/total,
caixa/custos/veto, revisão, rollback e concorrência. Chrome desktop/celular percorreu
preparo → consentimento pago → resposta falsa → prévia → aprovação por teclado →
registro → reabertura/histórico, com SQLite isolado. Nenhuma chamada paga ou mudança
nas carteiras de Lucas foi feita durante a implementação. Passaram **66 testes
direcionados e 9 subchecks**, incluindo Chrome e checks adicionais de falhas
preservadas e expiração. Ruff, sintaxe JavaScript, documentação (334 links), whitespace e
preservação passaram, com `violations: []`. GETs do servidor atualizado na porta
8085 conferidos; servidor anterior preservado. Suíte completa não executada.

Próximo passo: usar um quórum vinculado à Multiagentes e revisar a proposta na tela;
depois qualificar cotações recentes/horário e integrar marcação diária em APP-03.

## Frontend aprovado aplicado — DP-23, 15/10/2026

Identidade clara/azul mineral da prévia aplicada à plataforma. Menu permanente
Carteira, Operações, Agentes, Comparação e Dados; Laboratório/Legacy/Auditoria
secundários. Criar carteira fica no grupo de ações do topo, junto de Registrar
operação e Analisar carteira; tem rota própria e encaminha para Operações. Compra,
venda, prévia, confirmação, correção/anulação e histórico usam as mesmas APIs e
SQLite. O seletor compartilha a carteira nos links das áreas ativas; contextos
históricos e sintéticos não recebem a identidade da carteira pessoal.

Agentes dividido em Configurar → Dados e custo → Resultados, sem página única
com todos os controles. O comando guiado prepara dados e, terminado o job,
executa preflight; não chama os modelos. Diagnóstico por ativo, preparação
manual e recuperação continuam disponíveis. Histórico consultável por carteira
e por execução; custo, teto agregado e confirmação paga mantêm seus controles.
Deixar a etapa de custo limpa consentimento pendente. Não altera modelos nem
converte o snapshot em análise da carteira inteira.

Comparação mostra cadastros/capital/caixa/posições com patrimônio indisponível
quando faltam marcas; gráfico, preço e proventos fictícios da prévia não foram
incorporados. A Central de dados lê a prontidão da execução operacional e mostra
fonte, sessão, bloqueio e próxima ação. Cotações do cadastro pessoal continuam
APP-03, proventos APP-04 e proposta/aplicação automática APP-05.

Verificação: cadastro/compra/venda parcial/correção/erro/reabertura no Chrome com
SQLite temporário, desktop/celular/teclado e reinício em processo novo passaram.
Chrome também conferiu cinco áreas com dados reais somente em GET, navegação
primária e ausência de overflow. Orçamento testado no navegador com fixtures de
execução pendente (a histórica real permanece concluída/somente leitura), sem
POST real de autorização ou inferência. Passaram **49 testes direcionados e 9
subtests** (46 de carteiras/análises/rotas/Legacy e 3 de prontidão/troca de execução),
o check JavaScript de fluxo guiado/orçamento, lint, sintaxe e documentação (9 hubs,
331 links locais). Preservação histórica: `violations: []`. Suíte completa não
executada. Sem alteração das
carteiras do usuário, coleta real ou chamadas pagas pelo assistente nesta entrega.

## Nova análise por carteira e dia-alvo — DP-22/APP-05, 15/10/2026

**Ocorrência operacional, 15/10 às 01:48:** preparação da sessão 14/10 na execução
`radar-ui-747084b5790b4f4abf8274b296047e04` bloqueou os cinco ativos com
`URLError/WinError 10061`. O servidor 8084 iniciado pelo assistente herdou o
proxy/restrição de rede do sandbox; ausência de `input.json` no preflight era
consequência desse download recusado. Reiniciado o mesmo servidor fora da
restrição, preservando identidade/seleção, e HEAD ao arquivo B3 respondeu HTTP
200. Isso comprova conectividade, não cobertura das barras de 14/10. Job e
last_prepare originais copiados sem sobrescrita para
`data/radar/analysis-747084b5790b4f4abf8274b296047e04/diagnostics/prepare-bf44cdc23a112e773b33cfd6.json`.
Não foi repetida a coleta nem executada inferência; próximo passo é repetir
Preparar dados na mesma análise e conferir o resultado por ativo.

**Atualização às 01:55–02:00:** Lucas repetiu a preparação. O ZIP B3 2026 foi
baixado (93.509.689 bytes), mas os cinco ativos bloquearam com
`ValueError: no adjustment factor around 2026-10-14`. Falta fator de ajuste
válido na resposta Yahoo usada pelo pipeline; não é mais o erro de conexão.
Nenhum input/parecer de 14/10 foi criado. Preservado o segundo diagnóstico em
`diagnostics/prepare-d2c6913a87c6420ae439efb5.json` na mesma raiz. Correção
DP-22/APP-05 de diagnóstico: prontidão exibe erro registrado e orientação
específica para fator Yahoo, sem sugerir divergência corporativa para qualquer
falha. Preflight lê a prontidão atual, mostra a causa de coleta no lugar de
arquivo ausente e aguarda preparo em andamento; uma preparação nova também
limpa o resultado/consentimento anterior. Reuso dos checks existentes; 20 testes
direcionados passaram, além do check JavaScript de orçamento/diagnóstico,
sintaxe, lint e formatação. Chrome desktop/celular confirmou a causa registrada
na prontidão e no preflight, com POST de preflight simulado e coleta/agentes
bloqueados. Módulos selados e critérios de ajuste intactos;
sem herança de fator na borda, preço inventado ou uso de RAW como ajustado.
O servidor 8084 foi reiniciado para carregar a correção. Próximo passo para a
sessão 14/10 é a fonte fornecer um fator válido; UI mais clara não desbloqueia dados.

Implementado o cadastro de análise na interface: Início → **Abrir quórum para
esta carteira**, ou Radar → **Nova análise para uma carteira**. Escolha de
carteira/ativos, dia-alvo editável com padrão amanhã/próxima sessão planejada,
sessão de dados separada e histórico por carteira. Cada criação preserva
snapshot/revisão e horário real em contexto selado próprio; reanálise histórica
é identificada como produzida agora. Repetição de confirmação não duplica; uma
criação com revisão desatualizada é recusada. Nova execução inicializa seu
universo e assume o runner do processo sem reinício por execução, sob lock
compartilhado com dispatch/autorização. Worker ativo e lock pendente bloqueiam
troca; requisições identificadas com execução antiga continuam recusadas.

Arquivos: `dashboard/radar_analysis_api.py`, `dashboard/radar-analysis.js`,
integração em server/platform API, Radar e link no detalhe da carteira. Reuso
do cadastro SQLite pessoal, registro Radar e pipeline existente; sem novas
dependências nem mudanças nos módulos selados de inferência/registro. Nenhuma
carteira/operação real do usuário foi alterada durante esta implementação.

**Verificação:** 40 testes e 9 subtests direcionados de criação de análises,
carteiras, atualização de mercado e Legacy passaram; 16 testes são do cadastro
novo. Cobrem idempotência, criação interrompida, snapshot/histórico após compra,
calendário/final de semana, datas inválidas, revisão, busy, corrupção e HTTP
Origin/CSRF. Chrome real verificou desktop e celular, carteira vazia/com posição,
troca de carteira/data, histórico, teclado, foco e ausência de overflow; POSTs
interceptados por fixtures, tráfego externo bloqueado. Capturas locais em
`data/cache/radar-analysis-ui/`. Lint, sintaxe JavaScript, documentação (9 hubs,
links locais válidos) e whitespace aprovados. Preservação: `violations: []` nas
baselines históricas. Não executadas suíte completa, coleta real ou inferência paga.

**Limites e próximo passo:** o dia-alvo identifica uso pretendido, e o snapshot
vincula a consulta à carteira; os prompts existentes ainda não consomem posições
ou horizonte da data-alvo. Quórum atual é por ativo. Proposta/aprovação/aplicação
automática no ledger pessoal continuam APP-05; preços/evolução APP-03 e proventos
APP-04 também pendentes. Último job/preparo são resumos substituíveis, não arquivo
integral de todas as tentativas. O [mapa do ciclo completo](CICLO_USO_PLATAFORMA.md)
identifica cada caminho, registro e lacuna. Próximo incremento: APP-03 e contrato
de contexto do agente da carteira em APP-05, sem criar outra base/simulador.

## Base inicial Buy & Hold / Multiagentes — DP-20/21, 14/10/2026

A pedido explícito de Lucas, excluído do seletor o cadastro real externo vazio
“Buy & Hold” e criadas **Buy & Hold** e **Multiagentes**, ambas simuladas, com
R$ 100 mil independentes. Dez compras registradas pelo mesmo fluxo HTTP de
prévia/confirmação da home, cinco em cada carteira. Entrada econômica **14/10**,
referência histórica **CLOSE B3 de 13/10**, custos iniciais **zero**. São o ponto
de partida de uso solicitado; não são fills prospectivos nem decisão dos agentes.

| Ativo | Quantidade em cada carteira | Preço de referência, R$ | Valor inicial, R$ |
|---|---:|---:|---:|
| PETR4 | 351 | 56,85 | 19.954,35 |
| VALE3 | 297 | 67,16 | 19.946,52 |
| ITUB4 | 402 | 49,68 | 19.971,36 |
| WEGE3 | 393 | 50,81 | 19.968,33 |
| BBAS3 | 824 | 24,25 | 19.982,00 |

Cada carteira: **R$ 99.822,56 alocados e R$ 177,44 em caixa**. Alvos de R$ 20 mil
por ativo arredondados para ações inteiras, sem redistribuir sobras; mesmas
quantidades/base de custo nas duas. Estratégia, grupo `manual-initial-20261014`
e nota de referência/custos pertencem ao evento de criação no SQLite pessoal.
Home apresenta essa origem e distingue a base manual do piloto prospectivo pendente.
Patrimônio marcado/retorno continuam indisponíveis sem cotações atuais integradas.

Identidades: Buy & Hold `manual-bf4d687c03594170b0e2a2bcaa39fa46`;
Multiagentes `manual-5be40ea8853a476e94b799b6d45389ed`.
Cadastro anterior `manual-5f60dc15a6384f97bf1197d85fc16096` recebe evento `ARCHIVE`,
sem apagar a criação ou trocar sua natureza. Exclusão limitada a carteiras sem
lançamentos; GET/replay removem do catálogo ativo e recusam novas operações.
Link antigo recupera o seletor com aviso e carteira disponível.

Fonte local já adquirida: COTAHIST B3, ZIP SHA-256
`580d3b0bc768ef86c4b1afdd6d08eb05bae76f21db04f8cbc636d5bec54cdd7e`.
Hash e preços RAW conferidos pelo parser existente; nenhuma coleta/inferência
ou ordem real. Recibos de comandos/eventos, sem saldos paralelos:
`data/cache/initial-allocation-receipt.json`; backup SQLite anterior:
`data/cache/initial-allocation-before.sqlite3`. Ledgers/ensaios selados intactos.
Somente o servidor iniciado pelo agente na 8082 foi atualizado após conferir
jobs inativos e identidade do processo; instância anterior 8081 preservada.

Verificação: sete checks pessoais aprovados, incluindo dois novos de exclusão
rastreável e metadados de estratégia/grupo; Chrome desktop/390 px conferiu as duas
carteiras persistidas, somente GET. Quantidades/custos/caixa iguais; cadastro
antigo ausente, link antigo recuperado, zero exceções JS/tráfego externo/escritas.
Capturas em `data/cache/initial-allocation-ui/`. Lint, documentação/diff e
preservação conferidos; releitura em processo independente também validada.

**Próximo fluxo, DP-21/APP-05:** sugestões sobre **esta** Multiagentes → prévia/
validação → aprovação explícita → registro automático e idempotente das
movimentações simuladas, sem redigitação. Essa integração ainda não está
disponível. APP-03 deve fornecer preços com data/origem; regras futuras de
custos/risco, incluindo 85%, continuam pendentes. Não houve autorização genérica
ou nova chamada paga para inferência.

## APP-01/02 — carteiras pessoais e operações pela home, 14/10/2026

Entregue o fluxo **criar carteira → registrar operação → consultar a mesma
carteira na home**, conforme DP-02/03/16/17/19 e configuração pendente DP-18.
O cadastro aceita simulação manual ou registro de negócio real externo, com
capital/data próprios e início em caixa. Prévia mostra caixa, quantidade e
custo médio antes/depois do histórico inteiro. Confirmação idempotente grava
no SQLite pessoal; seletor, detalhe, posições e histórico usam o mesmo replay.
Não há saldos persistidos no navegador nem cópias JSON.

Operações anteriores a D0 são admitidas desde o início pessoal. Data econômica
e cadastro UTC real permanecem distintos. Inclusão antiga e correção/anulação
recalculam a sequência e rejeitam saldo/venda posterior inválidos. O botão
**Corrigir** exige motivo, permite substituir/anular e preserva o original
na tabela de rastreabilidade. Replay usa data e precedência original no mesmo
dia. Custos declarados, sem taxa automática; caixa econômico, sem afirmar
liquidação na corretora. [Contrato e checks](PILOTO_MULTIATIVOS_SPEC.md#15-app-0102--registro-pessoal-persistente-pela-interface).

`dashboard/manual_portfolio_api.py` reutiliza primitivas e cálculo de base/
quantidade/resultado V5 por vinculação local já usada em PAPER-02, sem editar
fontes selados. Identidade `HFL-MANUAL-PORTFOLIO-V1` e raiz própria
`data/platform/manual-v1/manual.sqlite3`. Transações FULL/IMMEDIATE, eventos
imutáveis/encadeados, comando único, replay e revisão da prévia protegem contra
gravação parcial, concorrência e duplicação. Host/Origin/CSRF existentes mantidos.
Não cria decisões, autorizações ou ordens; nenhum envio à corretora, inferência,
coleta, agendamento, ativação do piloto ou alteração de ledger antigo.

A home passa a ser de carteiras pessoais; a demonstração continua explicitamente
em `/?demo=1`. A antiga página `/portfolio` foi renomeada **Gestor e demonstrações**,
com link às carteiras da home; rotas/cenários/consultas preservados. Legacy segue
somente consulta. Base comum dos agentes/Buy & Hold aparece pendente, com
R$ 100 mil independentes e cinco alvos de 20%; preços, fills, custos e revisão
dos 85% ainda exigem PAPER-01. Não houve venda forçada nem política nova aplicada.

**Limites:** ações com quantidades inteiras, capital inicial único, datas civis
declaradas sem certificação de pregão, sem liquidação/aportes/retiradas/impostos
ou eventos corporativos. Sem referência RAW integrada, patrimônio com posições,
retorno e gráfico diário ficam indisponíveis; custo médio não vira cotação.
Proventos permanecem APP-04; atualização/marcação é APP-03, próximo incremento.
Backup externo e recuperação operacional pela interface continuam pendentes.
Chrome/teclado não substituem ensaio com leitor de tela ou hardware móvel real.

**Verificação:** 50 testes direcionados aprovados (49 de contabilidade/HTTP/home/
navegação e o check geral Chrome), mais 38 subtests. Os cinco checks novos cobrem
compra, venda parcial, histórico, correção/anulação, saldo/quantidade/custos,
prévia obsoleta, idempotência concorrente, rollback, origem local/CSRF e releitura
em processo novo. Jornada Chrome pessoal real desktop/390 px aprovada, com
teclado, foco no erro, recarga e reinício isolado do servidor, sem tráfego externo
ou POSTs de outros módulos. Capturas em `data/cache/manual-portfolio-ui/`
inspecionadas. Leitor de tela e hardware móvel não ensaiados. Suíte completa
não executada; as falhas históricas TECH-02 não foram requalificadas.

O roteiro geral foi atualizado para abrir o laboratório expansível e esperar
o menu atual. Ele revelou o alias `/#wallets` sem redirecionamento numa troca
apenas de hash: `platform.js` agora trata também `hashchange` no mesmo roteador
de Legacy. Check geral aprovado após a correção, sem relaxar guardas financeiros.
Lint/formatação Python, sintaxe JS, 322 links locais e `git diff --check`
aprovados. Preservação antes/depois: `changes: []`, `violations: []`; baselines
históricas mantêm somente as duas diferenças OPERATIONAL Radar já conhecidas.

**Uso imediato:** versão atual servida em `http://127.0.0.1:8082/`, cadastro
vazio pronto para preenchimento, sem exemplos gravados no banco pessoal.
Servidor anterior da porta 8081 preservado; nenhum processo do usuário encerrado.
Servidores/bancos das jornadas foram isolados e encerrados após os checks.
Para iniciar de novo, usar o servidor existente `dashboard/server.py 8082`;
nenhum agendamento foi criado. Próximo incremento: APP-03, referências RAW com
data/origem e marcação sobre esse mesmo histórico; APP-04 para proventos.

## UX-M4 — parametrização/revisão de orçamento na interface, 14/10/2026

Lucas esclareceu que orçamento deve ser parametrizado/autorizado na interface,
sem CLI/chat. Atende DP-01/13/16 e controles consultivos de apoio a PAPER-05.
Após o preflight técnico, painel Radar apresenta execução/sessão/ativos,
reservas anteriores/próprias, novo lote e exposição total. Usuário digita o teto
agregado aceitável para esta autorização, marca consentimento e registra. Teto
insuficiente, ausência de consentimento ou escopo diferente mantêm bloqueio.

Novos GET `radar-budget` e POST `radar-budget-authorization` em `/api/platform/`
reutilizam o mecanismo imutável `radar_runs.budget/authorize_budget`. Wrapper web
valida esquema exato, confirmação booleana, teto positivo/finito, token, owner e
header da execução operacional, modo, permissão de escrita, ausência de job/lock
e cobertura da exposição. Servidor exige origin/CSRF e JSON estrito. O mecanismo
existente revalida token/snapshot e orçamento próprio antes de gravar. Não altera
limite global de US$ 5 ou libera reservas anteriores; autoriza a exposição exata
revisada, sem permissão futura genérica. O valor digitado é um teto de revisão,
não parâmetro persistente de política. O contrato existente cobre todos os ativos
pendentes do run: a UI mostra esse conjunto e exige a seleção correspondente.

Registro de orçamento não chama Gemini. Sucesso refaz consultas/preflight e
limpa o consentimento pago anterior; botão 3 só habilita após novo consentimento
do lote, com o diálogo de custo existente e gates de execução intactos.
Mudanças de seleção/valores/snapshot invalidam revisão; duplo clique não duplica
registro. CLI/runner/contratos selados, ledgers e reservas intactos. Nenhuma
autorização real, chamada paga ou operação criada pelo agente.

Verificação: **71 testes aprovados e 36 subtests** (duas expectativas antigas de
dados locais do lote 09/10, documentadas na entrega anterior, fora desta seleção).
Checks novos cobrem teto insuficiente/NaN/bool/consentimento, token obsoleto,
owner/header incorretos, concorrência, escrita isolada sem provider, revisão UI,
duplo clique, preflight renovado e confirmação paga separada. [Harness UI](../tests/radar_budget_ui_check.js)
e [Chrome](../tests/radar_budget_browser_check.mjs) passaram desktop/390 px;
POSTs de preflight/autorização interceptados com fixtures, zero escrita real,
tráfego externo ou exceção JS. Capturas inspecionadas em
`data/cache/radar-budget-ui/`. Lint/sintaxe JS, links/diff e preservação conferidos.
Dashboard reiniciado após jobs inativos. Próximo passo: Lucas usar F5, refazer
preflight e revisar/autorizar o orçamento na própria tela; inferência é a etapa 3.

## Radar — preparo concluído e alerta antigo corrigido, 14/10/2026

Operador iniciou prepare às 13:00:30; job terminou **13:02:16 -03:00** com
**5/5 PREPARED**, zero pareceres, claims ou chamadas reservadas na execução
`radar-2026-10-14-asof-13`. A mensagem de erro reportada durante a tentativa vinha
do last_prepare das 03:02:51, não do job atual. [Registro diário](daily/2026-10-14.md).
Atende DP-01/DP-16 e UX-M4/preparação consultiva PAPER-05.

Corrigidos `radar.js` e o read model `platform_api.radar_readiness`: sem alerta
histórico como resultado atual durante prepare; erros datados sem diagnóstico
genérico de bonificação; PREPARING para inputs ainda não gerados no job ativo,
com inputs confirmados preservados. Nenhum runner, normalizador, contrato selado
ou gate financeiro alterado. Seis testes e sete subtests direcionados aprovados,
lint/sintaxe JS/links/diff conferidos; reinício somente após jobs inativos.
Não houve nova coleta ou inferência iniciada pelo agente: a preparação concluída
foi a do operador. Próximo passo é preflight/autorização de orçamento, sem
transformar inputs em pareceres/ordens ou ativar PAPER-04.

## UX-M4 — atualizar dados pelo cabeçalho, 14/10/2026

Lucas pediu atualização dos dados da bolsa acessível de qualquer módulo.
Entregue em `dashboard/shell.html/js/css`, sem novo endpoint/dependência e sem
alterar os runners selados. Atende DP-01/04/05/13/16, apoio à preparação consultiva
PAPER-05/DATA-01; não conclui ingestão prospectiva nem ativa PAPER-04.

Botão “Atualizar dados da bolsa” abre diálogo com a sessão/universo da execução
operacional do servidor. “Atualizar agora” reutiliza `/api/radar/prepare`, headers
CSRF/run e gates existentes. Nenhuma consulta/coleta automática ao carregar a
página; abrir o painel faz só GET. Duplo clique não duplica job; polling acompanha
o ID iniciado, retoma preparo em andamento ao abrir em outro módulo e informa
job trocado, falha, bloqueios por ativo ou cobertura completa. Há link ao Radar
e comando para atualizar a visualização atual. Teclado/Escape/foco e layout móvel
verificados. Mesmo no Legacy, o alvo do botão é explicitamente multiativos ativo,
sem acionar `/api/forward/*` ou alterar estados históricos.

Limites: sessão e universo são os do registro operacional, sem avançar data ou
criar novo run; sessão mais recente encerrada produz aviso para escolher seu
registro no Radar. Inputs já congelados permanecem preservados pelo preparador.
Atualizar preços/histórico não recalcula pareceres, patrimônio demonstrativo ou
ledger oficial; Gemini/preflight/autorização/execução seguem ações distintas.
Nenhuma coleta real, preparação, chamada paga, ordem ou autorização foi efetuada
na implementação/verificação; POST do navegador foi interceptado com fixture.

Verificação: **60 testes aprovados, 23 subtests, 1 jornada histórica omitida**
na seleção shell/gates Radar/Legacy/novo botão. **Duas falhas preexistentes de
expectativa sobre dados locais:** os testes
`test_real_recovery_has_five_official_inputs_equivalent_to_original` e
`test_real_itub4_bonus_normalized_and_bbas3_restricted` ainda pressupõem lote
09/10 sem claims/reservas e 30 chamadas planejadas; o lote já estava COMPLETED,
com cinco claims e zero chamadas novas planejadas antes desta entrega. Não
alteradas expectativas ou registros para ocultar essas falhas. Suíte completa
não executada. [Check do novo fluxo](../tests/test_market_update.py) e
[jornada Chrome](../tests/market_update_browser_check.mjs) passaram: todos os
módulos, desktop/390 px, diálogo/teclado/foco, prepare com fixture, zero POST real,
tráfego externo ou exceção JS. Capturas locais em `data/cache/market-update-ui/`.
Lint/sintaxe JS, links e diff conferidos; preservação `violations: []`, mesmas
duas diferenças Radar OPERATIONAL anteriores. Próximo passo é o operador usar
“Atualizar agora” e conferir os bloqueios/resultado antes do preflight pago.

## Radar — vínculo operacional corrigido, 14/10/2026

Atende DP-01/DP-16 e UX-M4/preparação consultiva PAPER-05. Dashboard 8081 ainda
escrevia na execução 09/10 ao consultar 13/10, desabilitando Preparar/Preflight
pelo gate correto. Após confirmar ausência de jobs ativos, selecionada a execução
`radar-2026-10-14-asof-13` pelo CLI existente e reiniciado o dashboard. API/Chrome
confirmaram vínculo correto, isolamento qualificado, cinco ativos selecionados e
botões habilitados. Data/fonte continuam imutáveis por identidade. Zero POSTs na
verificação, nenhuma preparação/inferência/ordem; sem mudança de código.
Snapshot antes/depois: somente registry OPERATIONAL, nenhuma violação; incidente
antigo preservado somente consulta. [Registro diário](daily/2026-10-14.md).
Próximo passo: operador preparar dados e conferir preflight, com orçamento pago
sujeito aos gates/autorização próprios; piloto oficial continua não iniciado.

## Dados de 13/10 — reconsulta de disponibilidade, 14/10 às 12:05

A pedido de Lucas, nova consulta segregada Yahoo encontrou **OHLCV válido nos
cinco ativos**, incluindo ITUB4 antes ausente. Fator `Adj Close / Close` disponível
e positivo; barras de 13/10 conferidas com o COTAHIST previamente adquirido,
com diferença float abaixo de R$ 0,00001 e volumes iguais. [Registro diário e
limites](daily/2026-10-14.md). Atende DP-01/DP-16 e diagnóstico DATA-01/PAPER-05.
Não houve novo download B3, prepare/preflight, agentes, chamada paga, reserva,
ordem, reconciliação ou ativação. Status selado da tentativa das 03h intacto;
consulta resolve a ausência da barra final, sem qualificar histórico completo
ou promover D0 a bundle oficial. Próximo passo é preparação/preflight Radar,
seguindo os gates e autorização próprios de orçamento antes de qualquer Gemini.

## UX-M3/M5/M6 — Legacy somente consulta, 14/10/2026

Decisão explícita de Lucas **DP-16**, atualização de prioridade/navegação da DP-08;
atende UX-M3/M5/M6 e TECH-01 na fronteira web H2. Plataforma ativa permanece
multiativos: carteiras, patrimônio, posições, decisões, operações e comparação
diária, com Mercado/Radar/Gestor Global e auditoria próprios. PETR4 permanece
entre os cinco ativos; apenas o experimento independente PETR4/H2 virou legado.

`/legacy` agora reúne Piloto PETR4 (`/legacy/paper`), Pesquisa H2
(`/legacy/h2`) e Backtests históricos (`/legacy/backtests`). Acesso secundário
na shell, com contexto de etapa anterior e documentação do TCC. `/paper`, `/h2`,
`/index.html` e suas variantes existentes continuam aliases sem reescrever
query/fragmentos. `/#readiness` e `/#wallets` encaminham para consultas históricas,
preservando os demais parâmetros. Carteiras independentes/decisões/operações
históricas permanecem na página paper; o hub liga também o relatório de
integridade/supervisão/processos antes apresentado na home.

Home HTML/JS e `/api/platform/overview` não carregam estados H2: retirados
atalhos destacados, cinco cartões single-asset, alertas e próximas ações daquela
frente. Mantidos seletor, patrimônio/caixa, posições, decisões/operações, comparação
e gráficos sintéticos, opt-in demonstrativo e estado oficial “ainda não iniciado”.
Auditoria ativa consulta processos Radar/Global e integridade demonstrativa
multiativos; ausência de dados não vira prontidão. O overview histórico permanece
no CLI existente e nos GETs `readiness`/`legacy-overview`, sem alteração de CLI.

Removidos os controles/diálogos e POSTs do JS paper. Na fronteira HTTP,
`POST /api/forward/*` é recusado com **403 `legacy_read_only`** antes de CSRF,
jobs ou escritas: prepare, preflight (também grava job), run, benchmarks,
supervision/sync, supervision/approve, supervision/reject, supervision/cancel,
scenario (exclusivo da UI antiga), inclusive nomes futuros naquele namespace.
`POST /api/h2/*` igualmente bloqueado. GETs históricos e status/CSRF compartilhado
continuam disponíveis; POSTs de Radar e Gestor Global mantêm seu despacho e gates.
O acompanhamento reconhece `/legacy/paper` como fonte H2, sem cruzar o catálogo PM.
Simulação local de quórum continua puramente demonstrativa e sem escrita.

**Preservação:** nenhuma execução/cancelamento/reconciliação de intenções antigas,
mudança de autorização, reserva, ledger, pendência, runner, contrato ou CLI selado.
Nenhuma chamada paga, aquisição de preços ou carteira oficial ativada. Legacy não
significa “sem pendências” nem “financeiramente encerrado”. A reorganização não
qualifica operação prospectiva nem faz nova auditoria financeira corrente.

**Verificação:** 119 testes direcionados aprovados (85 dos contratos web/H2/Global,
mais os 13 checks integrados da home reexecutados com TEMP externo; 21 adicionais
de shell/HTTP/acompanhamento), com 65 subtests aprovados. Os 8 checks de métricas
da home aparecem nas duas execuções e foram contados uma vez. Três jornadas
Chrome históricas foram omitidas nessa execução de pytest; a jornada Chrome
específica [legacy_ui_check.mjs](../tests/legacy_ui_check.mjs) passou em 1440 px e
390 px, com queries/fragments, aliases, cinco carteiras H2, home/auditoria sem H2,
menu por teclado e zero POST/tráfego externo/exceções JS. Capturas locais
inspecionadas em `data/cache/legacy-web-check/browser/` (artefatos não selados).
[Checks HTTP](../tests/test_legacy_web.py) envenenam os leitores H2 na home e os
escritores no POST; contratos existentes verificam GET sem escrita/inferência.
Lint, sintaxe JS, links locais e diff sem whitespace inválido aprovados.
Preservação: `violations: []`, mesmas duas diferenças OPERATIONAL Radar já
registradas antes da reorganização. Suíte completa não executada.

Checks de home usam TEMP externo por contrato selado; tentativas iniciais foram
interrompidas por ACL/sandbox e pela recusa correta de SQLite sintético dentro do
repositório. Reexecutados sem mudar o contrato, usando fixtures externas isoladas.
Próximo passo permanece fechar regras PAPER-01, validar o primeiro bundle
observado DATA-01 e concluir revisão PAPER-03, antes de ativar PAPER-04.

## PAPER-01 — risco refinado antes do aceite, 14/10/2026

Por solicitação de Lucas, a [proposta R7 na seção 4.1 existente](PILOTO_MULTIATIVOS_SPEC.md#41-redução-de-posições-sob-veto-ou-excesso-de-risco--proposta-r7)
substitui a recomendação anterior de bloquear inclusive venda sob veto.
Atende PAPER-01 e DP-01/04/05/08/13; nenhuma decisão DP foi reaberta.
Propõe cesta só de vendas de posições detidas/disponíveis, redução de exposição
e projeção de risco antes/depois nas mesmas marcas, sem criar/agravar excessos
de concentração/volatilidade. Redução parcial pode manter excesso remanescente.
Dados, contabilidade, custódia, custos/giro, eventos, prazos e autorização
permanecem obrigatórios; dado/risco ausente não vira permissão de saída.

Drawdown conserva pico, patrimônio e perda mesmo após liquidar; custo pode
piorá-lo. O limite proposto bloqueia novas compras até revisão explícita,
sem exigir drawdown abaixo do teto para vender. Sem reiniciar série/pico ou
comprar com recebíveis. Referência mantém política própria, sem gatilho automático
dos agentes; diferença entre admissão de exposição 85% nos agentes e entrada
até 100% na referência deve acompanhar a comparação descritiva.

Caminho de redução, testes de não agravamento e revisão pós-drawdown aguardam
aceite e qualificação futuros. Todos os demais parâmetros permanecem propostas.
Somente especificação, roadmap e estado ativos revistos; nenhum código,
V5/V2 selado, banco, demonstração ou backup alterado, sem chamadas pagas,
extensão implementada ou ativação. Verificação: **9 índices/304 links locais** e
`git diff --check` aprovados; preservação com `violations: []` e as mesmas duas
diferenças OPERATIONAL preexistentes/hashes. Exemplo de drawdown conferido com
Decimal (22% → 22,06% após custo de R$ 60); nenhuma suíte financeira reexecutada.

## PAPER-01 — proposta técnica consolidada, 14/10/2026

Após revisão da entrega DATA-01, Lucas pediu proposta objetiva enquanto o ZIP
real está pendente. A [tabela na especificação existente, seção 8.1](PILOTO_MULTIATIVOS_SPEC.md#81-proposta-objetiva-para-fechar-regras-técnicas--14102026)
consolida R2–R9 em execução, prazos, custos, risco, eventos corporativos, caixa/
liquidação e autorização, com justificativa e decisão restante de Lucas.
Atende PAPER-01 e DP-01/04/05/08/13/15; DP-01–DP-15 continuam aceitas.
Não há especificação paralela, regra técnica nova aprovada ou ativação.

Valores preservados como propostas: custo paper 0,1% por perna, buffer 2%,
OPEN RAW/slippage zero, prazo até 12h do dia civil seguinte, limites V5 dos
agentes, política independente da referência, caixa sem rendimento e comando
manual D+2. Naquela consolidação, destacados veto que também impedia venda
(recomendação substituída pela revisão R7 acima), convenção fracionária com
RAW de lote padrão e identidade/ACL ainda não qualificadas para autorização real.
Primeiro ZIP/bundle observado segue pendente; quando fornecido, validar pelo
fluxo DATA-01 existente. Canal de aquisição automática continua em avaliação.

Entrega somente documental: estado, roadmap e especificação ativos. Sem mudança
de código, módulos selados, demonstração, bancos ou backups; sem chamadas pagas,
coleta de preços ou ativação. Verificação: **9 índices/299 links locais** e
`git diff --check` aprovados; preservação com `violations: []` e as mesmas duas
diferenças OPERATIONAL preexistentes, com hashes inalterados. Nenhuma suíte
financeira reexecutada nesta consolidação.

## DATA-01 — planejamento e importação local, 14/10/2026

**Mecanismo qualificado; validação com primeiro ZIP real pendente.** Atende
DP-01/04/05/06/08/13/15, preparando PAPER-04 para leitura diária RAW sem operação.
[Extensão versionada](../scripts/pilot_observed_data.py),
[19 checks novos](../tests/test_pilot_observed_data.py) e
[contratos, avaliação de reuso e runbook](PILOTO_MULTIATIVOS_SPEC.md#14-data-01--calendário-planejado-e-importação-local-versionados).
Lucas confirmou que não baixou nenhum diário para este piloto. Não há aquisição
nem bundle observado; testes sintéticos não suprem essa evidência.

Calendário planejado de 13/10–31/12/2026, **53 sessões derivadas** de semana
documentada e exceções B3 para ações à vista. Base semanal do participante Itaú/íon
e alcance limitado da corroboração B3 UP2DATA explicitados; não se alega lista
positiva oficial nem ocorrência. Negociação e Câmara B3 têm listas próprias;
próxima sessão e D+2 qualificados dentro da cobertura, com recusa de extrapolação
para 2027. Horários OC005, vigentes desde 09/03, têm revisão conservadora para
13–14/10; fora dela, `UNAVAILABLE_VIGENCY`. Janelas não são instantes observados.
Documentos novos têm URL, versão, obtenção e hash no
[catálogo próprio](evidence/pilot_market_data_2026/observed_v1/sources.json).
O calendário histórico, o adaptador e o catálogo anteriores permanecem intactos.

Arquivo externo → aquisição com ZIP original/hash, URL declarada, operador,
sessão conferida, instante real e comprovante opcional → validação de todos os
registros antes dos preços → bundle RAW com cinco ativos → OPEN/CLOSE.
Reutiliza parser e funções compatíveis DATA-01, vinculando dependências privadas
com helper já existente. Sem novo motor, dependência ou mudança de fingerprints.
Natureza `ORIGIN_DOCUMENTED_NOT_AUTHENTICATED` distingue integridade/proveniência
de autenticação B3. Disponibilidade só desde importação real; nenhum
`published_at` livre. Retificação exige vínculo explícito e saída nova.
Armazenamento exclusivo `data/platform/observed-market-v1/`; nenhum bundle
novo é conectado ao motor sintético por troca de classificação.

`justfile`, `src/pipeline/b3_official.py` e `scripts/multiasset_radar.py` avaliados
somente por leitura: parser RAW reutilizável; comandos ETL e `prepare` acoplam
coleta anual/histórico ajustado ao Yahoo. RAW para marcação fica separado do
ajustado exigido pelos analistas. **Nenhum downloader criado; canal automático e
condições de uso em aberto.** Arquivo local permanece opção, sem converter
download manual em requisito definitivo. Página oficial/passos de obtenção e
entrada humana exata estão no runbook. Uso local e redistribuição separados,
sem licença presumida ou publicação de preços.

A [avaliação independente do fluxo e dos provedores](AVALIACAO_COLETA_DADOS_2026-10-14.md)
recomenda, como incremento imediato e condicionado à confirmação de uso por
Lucas, validar COTAHIST-D pós-D0 importado pelo operador. Para os agentes,
nenhuma alternativa foi qualificada nos cinco papéis. Sem ZIP/bundle real ou
decisão de uso, DATA-01 permanece pendente; PAPER-04 segue bloqueado.

Verificação: **47 checks aprovados** — 19 novos, 24 DATA-01 anteriores, 4 do
parser/extrator com mocks. CLI em processos novos com rede bloqueada; validações
de calendário/horários, datas pré-D0/múltiplas, metadados, duplicatas, ausência,
OHLC/volume, aquisição/hash/fixture, revisões e disponibilidade. Demonstração
e raiz PAPER-03 existente lidas com sucesso, sem alterar bytes/ledger.
Ruff check/format e `git diff --check` aprovados; documentação: 9 índices,
297 links locais válidos nesta entrega.
Suíte completa, ETL antigo, Gemini/chamadas pagas e ativação não executados.

Preservação antes/depois: **11.402 arquivos** comparados em
scripts/tests/src/dashboard/evidências e demonstração/raiz/backups PAPER-03;
**zero alterados ou removidos**. Adições: CLI, check e pacote documental
`observed_v1`. Resumo local em
`data/platform/data01-observed-checks/preservation-files.json`.
Check de baselines: `violations: []`; mesmas duas diferenças OPERATIONAL
preexistentes, sem mudança de hashes. Alterações anteriores do operador preservadas;
somente estado, roadmap e especificação ativos atualizados por esta etapa.

Próximo passo: Lucas fornecer caminho/sessão do diário pós-13/10 quando obtido;
validar aquisição e primeiro bundle real, mantendo canal/uso automático em
avaliação. PAPER-04 exige ainda contrato prospectivo de preços/fases, eventos,
autorização autenticada, regras técnicas PAPER-01, novas decisões com histórico
ajustado válido e orçamento próprio, ponte financeira qualificada e revisão
operacional. Bases DP-09–DP-15 continuam aceitas; **DATA-01 integral e piloto
oficial não estão concluídos ou ativados**.

## Tentativa de previsão consultiva — 14/10/2026

Pedido de Lucas antes da abertura, dados pretendidos até CLOSE 13/10; DP-01/DP-08
e preparação de histórico para PAPER-05. [Registro diário](daily/2026-10-14.md).
Nova execução `radar-2026-10-14-asof-13`, persistida no registry/raiz próprios.
B3 contém OHLCV de 13/10, mas Yahoo tem barras incompletas/ausentes; os cinco
ativos bloquearam por falta de fator de ajuste na borda final. Agente independente
confirmou a guarda. **Nenhuma previsão, inferência paga, reserva nova ou operação.**
Diagnóstico/preflight/cache preservados; repetir preparação quando a fonte completar
os dados. Antes do lote pago, resolver autorização separada de orçamento agregado
(reservas anteriores US$ 6,63552 > teto US$ 5). Não qualifica ativação do piloto.

## Decisões do piloto — 14/10/2026

Lucas aprovou DP-09–DP-15: piloto operacional com resultados descritivos; agentes
e Buy & Hold com R$ 100 mil independentes; referência sem rebalanceamento ou
reinvestimento, proventos em caixa; sem aportes/retiradas; rotina manual diária
com autorização explícita; revisão após 20 pregões; primeira sessão elegível após
preparação, preservando D0=13/10 como marco. [Registro de direção](DIRECAO_DO_PROJETO.md).
Custos, limites de risco, buffers, fonte, prazos e execução não foram aprovados.
Essa revisão não criou carteira, ordem, gasto ou ativação oficial.

## PAPER-03 — durabilidade e restauração sintéticas, 14/10/2026

**Durabilidade/recuperação do ensaio qualificadas — DP-01–DP-05/07; sem ativação
oficial.** [CLI](../scripts/pilot_trial.py), [checks](../tests/test_pilot_trial.py) e
[runbook/contratos/limites](PILOTO_MULTIATIVOS_SPEC.md#13-paper-03--persistência-e-recuperação-do-ensaio-sintético).
Raiz exclusiva abaixo de `data/platform/paper-synthetic/`, com contenção absoluta/
resolvida e recusa de links/junctions. Criação exige diretório novo. Mantém TEMP
e fontes/contratos do escritor antigo; não converte a demonstração em carteira.

Reutiliza Store/eventos/replay/idempotência/checkpoint/transações V7.6.5, ponte
PAPER-02, motor V5, reconciliação, projeção e leitor da interface. Único fonte
anterior alterado: `qualify_pilot_paper.py`, extraindo o roteiro de **uma** sessão
para uso pelo qualificador TEMP e pelo ensaio durável. Novos: CLI e check acima.
Não há dependência, motor financeiro, política ou interface novos. SQLite guarda
identidade UUID, fingerprints, schema, calendário/bundles normalizados completos,
eventos, checkpoints e recibos. Uma transação confirma as duas carteiras e o
comando; retomada valida tudo antes de escrever, sem reconstruir histórico.

Ensaio mantido em `data/platform/paper-synthetic/paper03-20261014`, identidade
`ee3314b4-7264-4497-ba38-9873d792f752`. Inicialização em processo próprio; avanços
04/11 e 05/11 em processos novos, encerramento, consulta/replay e continuação
06/11–12/11 em outros processos. Transcript local com PIDs em
`data/platform/paper03-checks/acceptance.jsonl`; resumo em `acceptance-result.json`
na mesma pasta. Os oito snapshots por carteira preservam IDs anteriores,
capital e autorizações. Resultado da fixture original: agentes **R$ 100.039,36**,
caixa R$ 97.594,36/custos R$ 5,64; referência **R$ 101.744,07**, caixa
R$ 1.878,57/custos R$ 98,03. Sem reservas/recebíveis/custódia pendentes ao fim.

Backup `backups/completo` via SQLite nativo foi restaurado em
`paper03-20261014-restored`, com igualdade integral do snapshot: metadata,
bundles, comandos, IDs, eventos, checkpoints, saldos, posições, história e
projeção. Cabeças finais: **46 eventos** nos agentes e **47** na referência;
snapshot integral `7f26f09f1e53e58df24011466a634d17fa61519bd42811696c5eb3d97ef22b1d`.
Backup após três sessões restaurado em `paper03-20261014-old-restored`
é **STALE**, explicitamente faltando cinco sessões. Raiz corrente intacta;
retry confirmado da última sessão devolve recibo original e não duplica efeito.
Restaurações são cópias de conferência, sem avanço/publicação; não há adoção
automática como escritor nem perda silenciosa dos eventos posteriores.

`export` publica `projection.json` com temporário/flush/fsync, validação pelo
leitor existente e substituição atômica, serializada com escritores. Leitura
pela API existente qualificada via `HFL_PILOT_DEMO`, ainda `SYNTHETIC_TEST` e
`official_activation=false`. GET segue somente leitura, sem SQLite, comando,
qualificador ou caminho HTTP. Demonstração anterior preservada. O arquivo só
muda por `export` explícito; sua sessão pode ficar atrás do ledger.

Verificação executada: **124 checks direcionados aprovados**:

- `python -B -m unittest discover -s tests -p test_pilot_trial.py -v`: **16** —
  processos independentes, cenário original, retry/conflito/ordem, rollback de
  ambas carteiras, ACK perdido, processo morto antes/depois do commit, processos
  concorrentes, backup concorrente, corrupção/schema/fingerprints/classificação,
  backup incompleto/incompatível, destino existente, STALE e publicação atômica.
- Mesmo comando para `test_pilot_paper.py`: **29**; `test_pilot_market_data.py`:
  **24**; `test_paper_ledger_v765.py`: **34**; `test_pilot_home.py`: **21**, incluindo
  HTTP local e JavaScript real. São 108 checks anteriores reexecutados.
- Ruff check/format dos três Python afetados e `git diff --check` aprovados.
  `check_docs.py`, incluindo a especificação em memória: **9 páginas/280 links**.

Preservação antes/depois: `violations: []`, mesmas duas diferenças OPERATIONAL
preexistentes e mesmos hashes. Comparação adicional de **11.384 arquivos** em
scripts/tests/src/dashboard/evidências: somente `qualify_pilot_paper.py` mudou;
nenhum removido, apenas CLI e check novos. Fontes selados, DATA-01, ponte
PAPER-02, preparador/leitor/tela e alterações preexistentes do operador
preservados. Somente roadmap, estado e especificação ativos foram atualizados.

Os ensaios Python precisaram da execução local fora do sandbox por WinError 5
no TEMP/token isolado, com revisão automática aprovada. Não foram alteradas
permissões de outras pastas. Na raiz final, proprietário `LUCAS\LUCAS` e ACL
explícita criada por `mkdir(mode=0o700)` neste ambiente: proprietário, SYSTEM e
Administradores com controle; entradas não herdadas. **Inspeção de ACL**, sem
teste de outra conta nem autenticação humana/financeira qualificada. Identidade
de ambiente não comprova autorização real.

Hashes são locais, sem assinatura/cabeça externa; backups no mesmo volume não
protegem perda de disco/pasta. Sem teste de energia/hardware, navegador novo,
acessibilidade integral ou suíte completa. Não houve rede externa, Gemini,
preço real, scheduler, mudança financeira ou acesso/reconciliação H2/holdout.
PAPER-01 segue DRAFT, DATA-01 real segue bloqueado. Antes de PAPER-04 faltam
revisão R1–R9, dados/calendário/fases/disponibilidade reais, eventos corporativos,
decisões/autoridade autenticadas, adoção explícita de cópia como escritor,
backup independente e revisão independente. Os registros anteriores abaixo
descrevem os marcos anteriores; esta seção atualiza o estado de PAPER-03.

## UX-M3/M5 — tela inicial de carteiras, 14/10/2026

**Experiência demonstrativa implementada — DP-02–DP-05; ativação oficial pendente.**
[Contrato/comandos](PILOTO_MULTIATIVOS_SPEC.md#12-ux-m3m5--tela-inicial-demonstrativa-integrada).
`/` abre sem carteira oficial; `/?demo=1` exige opt-in sintético e oferece duas
carteiras, sessões, períodos, patrimônio/caixa/investido/posições, gráfico base
100, resumo dos cinco ativos, posições, decisões e operações. Tema, shell,
ajuda e Chart.js local reutilizados; laboratório anterior fica expansível,
com anchors de auditoria/readiness/carteiras e destinos preservados.

Novos: [API de leitura](../dashboard/pilot_api.py),
[preparador](../scripts/prepare_pilot_demo.py), [checks Python](../tests/test_pilot_home.py)
e [check do JavaScript real](../tests/pilot_home_ui_check.js).
Alterados somente servidor/HTML/JS/CSS da página inicial e cinco documentos ativos.
`pilot_paper.py`, qualificador PAPER-02, políticas V5, fontes selados e contratos
anteriores permanecem intactos. Não há outro motor, framework ou dependência.

Preparação explícita `.venv/Scripts/python.exe -B scripts/prepare_pilot_demo.py`
gerou `data/platform/pilot-demo.json`, schema/identidade sintéticos, envelopes e
projeção conferidos por replay. GET `/api/portfolio/pilot?demo=1` não escreve,
abre SQLite, executa qualificador ou inferência. Caminho controlado/configuração
`HFL_PILOT_DEMO`, nunca caminho na URL. Ausência/corrupção não têm fallback.
Arquivo existente válido é reutilizado sem sobrescrita. Consulta limita campos
públicos e mantém H2/consultivo V2 fora do grupo.

Períodos calculados dinamicamente por âncora/cobertura/cadeia diária: virada de
mês/ano e 12 meses civis, inclusive 29/02. No cenário curto, mês/ano/12 meses
continuam insuficientes, com parcial desde início separado. Fonte temporal é
o snapshot reconciliado, não relógio da consulta nem sessão pendente. Gráfico
preserva lacunas nulas, sem interpolação, com tabela acessível e destaque textual.
Preços/variações dos ativos vêm dos bundles; mudanças de posição incluem trades
e não são chamadas de retorno. Pesos da referência diferem de seus alvos iniciais.

Verificação executada nesta entrega: **59 testes aprovados**:

- `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_pilot_home.py -v`: **21** — métricas, âncoras, lacunas, exportação, GET sem escrita/rede, schema/integridade, seleção/sessão/período, vazio/pendência e JavaScript real com respostas fora de ordem.
- Mesmo comando com `test_pilot_paper.py`: **29** preservados. Não se afirma reexecução dos 87 anteriores combinados.
- `.venv/Scripts/python.exe -B -m pytest tests/test_ui_v762.py -k 'not browser_checks' tests/test_platform_ui.py -q`: **9 passed**, 23 subtests; check headless antigo não executado, substituído aqui por jornada manual real via computer-use/Chrome.
- `node --check` dos dois JS; Ruff check/format dos Python afetados; links/documentação e `git diff --check` aprovados. Sem suíte completa.

Servidor keyless existente em `http://127.0.0.1:8097/`; demonstração explícita em
`http://127.0.0.1:8097/?demo=1`. Chrome real verificou entrada/saída, carteiras,
períodos, datas/selo, sessão indisponível, exportação ausente/inválida e recuperação.
Celular **390×844**: sem overflow horizontal da página; tabelas rolam em regiões
focáveis e abriram por teclado, com outline visível. Capturas reais em
`TEMP/hfl-home-ui-xaD84O`: `desktop-agents.jpg`, `desktop-reference-month.jpg`,
`desktop-not-started.jpg`, `mobile-reference.jpg`, `mobile-accessible-tables.jpg`,
`mobile-not-started.jpg`, `desktop-missing-export.jpg`, `desktop-integrity-invalid.jpg`
e `desktop-session-unavailable.jpg`. Testes de ausência/corrupção usaram cópia
descartável e instância keyless separada; exportação controlada intacta.
Capturas adicionais: `desktop-first-session-cash.jpg` (baseline sem curva),
`desktop-chart-tooltip.jpg` e `mobile-portfolio-viewport.jpg`. Foco da ajuda
Patrimônio no celular ficou em y≈120, abaixo do selo persistente (fim y=99),
com outline visível; margem de rolagem impede o selo de encobrir controles.

Preservação antes/depois: `violations: []`, mesmas duas diferenças OPERATIONAL
preexistentes. Comparação adicional de hashes registra somente os arquivos
autorizados acima, sem remoções. Alterações preexistentes do operador preservadas.
Dos 11.435 arquivos existentes na captura inicial, só os nove autorizados foram
alterados; quatro arquivos novos adicionados. Todos os fontes/artefatos antigos
PAPER-02, DATA-01 e evidências seladas mantiveram seus hashes. Documentação:
9 páginas/270 links locais aprovados, incluindo a especificação em memória.
Sem rede externa, Gemini, dados reais, ordens, scheduler, alteração/reconciliação
H2 ou acesso ao holdout. Não qualifica integralmente leitor de tela/zoom 200%.
PAPER-01 segue DRAFT; DATA-01 real e PAPER-03 continuam pendentes. Próximo passo
operacional: resolver fonte/calendário/fases/disponibilidade/autoridade e
durabilidade/backup, preservando o modo demonstrativo separado.

## PAPER-02 — ensaio integrado entregue, 14/10/2026

Atende DP-01/03/04/05/07. [Contrato e comando](PILOTO_MULTIATIVOS_SPEC.md#11-paper-02--ensaio-integrado-exclusivamente-sintetico),
[ponte](../scripts/pilot_paper.py), [qualificador](../scripts/qualify_pilot_paper.py)
e [checks](../tests/test_pilot_paper.py). Oito sessões sintéticas (03–12/11),
cobertura extra explícita e warm-up de risco sintético, duas carteiras em TEMP:
CLOSE t → roteiro TRADE/HOLD → validação → autorização/reserva antes do OPEN
t+1 → fill com disponibilidade/prazo separados → D+2 → CLOSE/reconciliação.
Referência conserva alvos iniciais de 20%, entra uma vez e mantém; agentes
iniciam em caixa, compram 100 PETR4 e vendem 40 posteriormente. Nenhum parecer
real é fabricado, nenhum OPEN redimensiona a quantidade autorizada.

Exemplo final gerado pelo CLI em `TEMP/hfl-paper-paper02-2fr468ax`: bundles,
`ledger.sqlite3`, duas exportações e `projection.json` selado. Resultado final:
agentes **R$ 100.039,36**, caixa R$ 97.594,36, custos R$ 5,64; referência
**R$ 101.744,07**, caixa R$ 1.878,57, custos R$ 98,03. Todos os snapshots verificam
`E=S+B+ΣQ×RAW=C+realizado+renda+não realizado`; ao fim não há reservas,
recebíveis nem custódia pendente. São resultados da fixture, sem evidência
de retorno real. Catálogo, posições, pesos/alvos, trades, história, variações
R$/%, base 100 e estados de ausência/histórico insuficiente estão no JSON.

Verificação direcionada: **87 testes aprovados**:

- `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_pilot_paper.py -v`: **29**, incluindo falhas de autorização/tempo/estado, OPEN/CLOSE, saldo/custódia, D+2, divergência, idempotência, rollback/ack perdido, referência, risco, bloqueio corporativo, separação e ausência de rede.
- Mesmo comando com `test_pilot_market_data.py`: **24** preservados.
- Mesmo comando com `test_paper_ledger_v765.py`: **34** preservados, incluindo morte de processo, concorrência, contratos/autorização/V5 e projeção antiga.
- `.venv/Scripts/python.exe -B scripts/qualify_pilot_paper.py`: ensaio completo aprovado, saída somente TEMP; sem rede, Gemini, preços reais ou suíte completa.
- Ruff check/format dos três arquivos novos aprovados; `git diff --check` aprovado. Links e catálogo documental aprovados, incluindo especificação em memória.
- `check_preservation.py` antes/depois: `violations: []`, mesmas duas diferenças OPERATIONAL preexistentes e mesmos hashes. Comparação adicional de **11.377 arquivos existentes** em scripts/src/dashboard/tests/evidências: nenhum modificado/removido, apenas os três arquivos novos. Fontes antigos, calendário histórico, contratos H2 e alterações preexistentes preservados.

A ponte usa o mesmo bytecode de reserva/fill/custos V5 e do Store/replay V765,
com dependências locais explícitas. `POLICY` original permanece 85%; referência
tem política de teste própria. Agentes conservam gates financeiros e risco;
giro/custo são conferidos na prévia e no OPEN observado. Relógios econômicos,
autorização e liberação de fixture são simulados; recibos de importação e
`recorded_at` conservam relógios reais. Nenhum horário B3 ou ato humano real
é alegado. Identidade nova impede leitura cruzada com o contrato anterior.

PAPER-01 permanece **DRAFT** e R1–R9 pendentes; DATA-01 permanece sem cobertura
positiva prospectiva/fonte/bundle real. Isso bloqueia ativação oficial, não o
ensaio sintético concluído. Eventos corporativos não suportados interrompem a
sessão e a continuidade; integração de agentes/pareceres reais, autoridade
autenticada e persistência/backup ainda faltam. A conexão do JSON à tela inicial
foi entregue em UX-M3/M5; ativação operacional continua separada.

[Início](../INICIO.md) · [Roadmap](ROADMAP.md) · [Documentação e evidências](README.md)

## Resumo

| Área | Estado observado/documentado | Limite |
|---|---|---|
| Radar oficial 09/10 | Recuperação separada; cinco pareceres/25 votos; veto BBAS3 | Consultivo; não representa operações |
| Global PM V1 | `REJECTED_BY_VALIDATOR`, tratamento encerrado | Evidência histórica; pendência de encerramento dos caminhos pagos no backend |
| Global PM V2 | `VALID_PROPOSAL`, R$ 100 mil hipotéticos, 100% caixa, zero operações | Snapshot consultivo; não prova rentabilidade |
| Ledger multiativos V7.6.5 | `LEDGER_QUALIFIED_OFFLINE` | SQLite gravável temporário/sintético; nenhuma carteira oficial ativa |
| API do ledger | GET com filtros, sessões e paginação | Lê exportação sintética verificada; GET não avança pregão |
| Fluxo paper oficial multiativos | `OFFICIAL_PAPER_DISABLED` | Sem autorização humana oficial, ingestão diária ou fill causal de abertura integrados |
| PAPER-01 — contrato do piloto | [Bases DP-09–DP-15 aprovadas; regras técnicas pendentes](PILOTO_MULTIATIVOS_SPEC.md) | DRAFT; demais recomendações não aprovadas; sem carteira oficial criada ou prontidão operacional |
| DATA-01 — entrada local | Planejamento 13/10–31/12 e importador RAW versionados; 47 checks aprovados | Primeiro ZIP/bundle observado pendente; horários revisados até 14/10, canal/uso automático em avaliação; nenhuma integração financeira |
| PAPER-02 — integração offline | Duas carteiras sintéticas, oito sessões, autorização/intenção ex-ante, OPEN t+1, D+2 e JSON comparativo | Demonstração TEMP preservada; UI e durabilidade sintéticas ampliadas em UX/PAPER-03, políticas R1–R9 seguem pendentes |
| PAPER-03 — durabilidade/recuperação | SQLite em raiz dedicada, continuidade por CLI, exportação atômica, backup nativo e restauração integral isolada | Exclusivamente sintético; sem adoção automática como escritor, backup externo, autenticação financeira ou revisão independente |
| H2 original em observação V7.6.5 | PENDENTE, sem compra; aguardava processamento/reconciliação de 13/10 | Não aplicar TTL de aprovação da supervisionada; não é consulta atual |
| H2 supervisionada em observação V7.6.5 | EXPIRADA sem aprovação, sem compra | Não autorizar retroativamente |
| H2 OA-1 | Validation provisória exploratória, não ratificada academicamente | Resultados negativos preservados; não libera Final Test |
| H2 Final Test | Bloqueado nos documentos consultados | Ratificação, freeze/release e autorização específicos |
| UX | Início de carteira demonstrativa integrado PAPER-02, seletor/períodos/posições/gráfico; menu e H2 separado preservados | Ativação oficial, Auditoria própria e acessibilidade integral pendentes |

H2/PETR4 e Radar/Global PM são linhas independentes: não compartilhar capital,
autorizações, carteiras, preços ou alegações científicas entre tratamentos.

## Evidência técnica recente

- [Entrega V7.6.5](evidence/hfl_paper_ledger_v765/README.md): eventos, replay,
  idempotência, caixa/custódia/recebíveis, D+2 e reconciliação exercitados offline.
- [Limitações](evidence/hfl_paper_ledger_v765/LIMITATIONS.md): calendário novo
  cobre até agosto/2026; sem feed ativo, corporate actions integrado, scheduler,
  backup/restauração de disco ou raiz oficial de escrita.
- [API e dashboard](evidence/hfl_paper_ledger_v765/API_READ_MODELS.md): modo
  sintético explícito, histórico de cinco sessões, caixa puro compacto e H2 separado.
- [Auditoria da pendência H2](evidence/hfl_paper_ledger_v765/H2_PENDING_STATE_AUDIT.md):
  contratos diferentes explicam PENDENTE versus EXPIRADA; nenhuma reconciliação criada.

## Qualificação registrada, sem nova execução nesta organização

V7.6.5 registra **49 testes direcionados e 68 subchecks**, **Chrome 30/30**,
**1801 passed, 14 failed preexistentes e 129 subchecks** na regressão.
Comparação por nome: nenhuma falha nova registrada. A suíte completa permanece
vermelha. [Relatório](evidence/hfl_paper_ledger_v765/REGRESSION_REPORT.md) e
[resultado estruturado](evidence/hfl_paper_ledger_v765/QUALIFICATION_RESULT.json).

## Contexto científico que não pode ser apagado

- [Síntese OA-1](H2_V6_OA1_VALIDATION_SCIENTIFIC_SUMMARY.md): avaliação
  descritiva e exploratória; não é teste confirmatório.
- [Integração H2 de avaliação](H2_V6_EVALUATION_PRODUCTION_INTEGRATION.md):
  caminho qualificado offline; manifesto candidato e aprovação/freeze pendentes
  naquela entrega. A OA-1 posterior tem autorização provisória própria.
- [Consolidação V7.5](evidence/hfl_scientific_consolidation_v75/README.md) e
  [protocolo V7.6](evidence/hfl_experimental_protocol_v76/README.md): conformidade,
  robustez, proveniência e ameaças à validade; campanhas não autorizadas por este resumo.
- [Erratas](evidence/hfl_methodology_ux_review_v761/FORMAL_ERRATA.md): correções
  não destrutivas; não substituem resultados selados nem confirmam a fatura real.

## Entrega documental PAPER-01 — 13/10/2026

[Especificação produzida](PILOTO_MULTIATIVOS_SPEC.md), em **DRAFT — AGUARDANDO
REVISÃO**, ligada a DP-01–DP-08. Apenas contrato ativo, índice, roadmap e este
estado foram alterados pela tarefa; alterações preexistentes preservadas.

- `.venv/Scripts/python.exe -B scripts/check_docs.py`: aprovado; 8 índices,
  214 links locais e catálogo completo. O mesmo check incluindo a especificação
  em memória aprovou 9 páginas e 220 links locais; script mantido intacto.
- `.venv/Scripts/python.exe -B scripts/check_preservation.py`: aprovado antes
  e depois; `violations: []`. As duas diferenças OPERATIONAL históricas em
  `job.json`/`last_prepare.json` já existiam e mantiveram os mesmos hashes.
- Comparação adicional antes/depois: 342 arquivos em `scripts`, `src`,
  `dashboard`, `tests` e pacote V7.6.5 mantiveram seus hashes (excluídos caches
  Python); nenhuma adição/remoção nessas áreas. `git diff --check` aprovado.

Esses checks não qualificam o contrato prospectivo nem reexecutam os testes
citados. Sem suíte da aplicação, download, operação, banco novo ou aprovação.

## DATA-01 — primeira implementação, 13/10/2026

[Adaptador local](../scripts/pilot_market_data.py) e
[checks](../tests/test_pilot_market_data.py), ligados a DP-01/04/05.
[Contrato de entrada/saída e comandos](PILOTO_MULTIATIVOS_SPEC.md#9-data-01--mecanismo-implementado-e-qualificado-offline).
Reusados parser COTAHIST, validador OHLCV, JSON canônico e consulta da lista de
sessões fixada; fontes selados intactos. Exemplo em TEMP com 15 barras sintéticas,
reimportação com mesma identidade e retificação v2 em processos novos.

Checks direcionados: **16 aprovados**; lint/formatação dos dois arquivos novos
aprovados. A primeira execução no sandbox encontrou WinError 5 no TEMP/Python
3.13; a execução isolada fora dele passou com rede bloqueada. Sem suíte completa,
download, Gemini, indicador novo, UI, ordens ou acesso a preços protegidos H2.
Resultado oficial explícito: **13/10/2026 bloqueado por cobertura de calendário**,
antes de ler arquivo de preços. O calendário histórico não foi alterado.

Verificação final DATA-01: `check_docs.py` aprovado (8 índices/221 links);
incluindo a especificação em memória, 9 páginas/229 links. `check_preservation.py`
aprovado antes/depois com `violations: []` e as mesmas duas diferenças
OPERATIONAL preexistentes. Comparação adicional: os 342 arquivos existentes de
`scripts`, `src`, `dashboard`, `tests` e pacote V7.6.5 mantiveram seus hashes;
somente adaptador e check novos foram acrescentados nessas áreas. `git diff
--check` e whitespace dos arquivos novos aprovados. Alterações preexistentes
do operador preservadas. Foram atualizados apenas os cinco documentos ativos
(contrato, índice, roadmap, estado e arquitetura), além dos dois arquivos novos.

## DATA-01 — segundo incremento, 13/10/2026

[Contrato atualizado](PILOTO_MULTIATIVOS_SPEC.md#10-data-01--segundo-incremento-evidencias-b3-e-formato-diario)
e [catálogo de evidências](evidence/pilot_market_data_2026/sources.json): nove
documentos públicos B3 com URL, versão, obtenção UTC, escopo, bytes e hashes.
Adaptador/checks existentes ampliados; parser, calendário histórico e H2 intactos.

- Calendário: feriados/suspensões documentados de 01/01–31/12/2026 (OC041/2026).
  Intervalo técnico 13/10–30/11 e duas sessões seguintes **não comprovados como
  lista positiva**, sem inferência por dias úteis. `b3-2026` verifica evidências
  e retorna bloqueio positivo/D+2, mantendo sessões observadas vazias.
- Fonte/formato: ZIP/TXT COTAHIST diário confirmado no seletor oficial. Formato
  diário, datas de todos os instrumentos antes do parser, FATCOT unitário e ISIN
  qualificados com fixtures. OPEN/PREABE e CLOSE/PREULT não trazem instante exato.
- Bundle real: **indisponível**; nenhum arquivo explicitamente disponibilizado
  para esta tarefa. Registro de aquisições vazio; aparência, URL/manifest e hash
  isolados não promovem dados a fonte oficial. Disponibilidade na importação.
- Uso/publicação: página de cotações restringe coleta automatizada; termos
  restringem redistribuição/difusão. Uso no piloto/TCC ainda precisa de
  esclarecimento. SLA de publicação e cronograma de retificação não encontrados.
- Verificação: **24 checks aprovados, incluindo os 16 anteriores**; Ruff e
  formatação aprovados. CLI diária em processos novos com rede bloqueada; exemplo
  V1 anterior legível sem reescrita. Sem suíte completa ou download de preços.

Verificação final do segundo incremento: `check_docs.py` aprovado (8 índices,
226 links; incluindo a especificação em memória, 9 páginas/236 links).
`check_preservation.py` antes/depois: `violations: []`, mesmas duas diferenças
OPERATIONAL preexistentes. Comparação de 346 arquivos existentes: apenas
`scripts/pilot_market_data.py` e `tests/test_pilot_market_data.py` alterados;
344 mantiveram seus hashes, incluindo fontes selados e calendário histórico.
Nova evidência: nove documentos públicos e um catálogo JSON nesta entrega,
sem relatório adicional. `git diff --check` aprovado. As cinco páginas ativas
foram atualizadas; alterações preexistentes do operador preservadas.

## Próxima ação

**Validar o primeiro diário pós-D0 quando Lucas fornecer o caminho; manter a
definição do canal automático e condições de uso em aberto, avaliando reuso antes
de outro downloader.** O [contrato em DRAFT](PILOTO_MULTIATIVOS_SPEC.md) registra
bases DP-09–DP-15 já aceitas, planejamento e importação qualificados. Antes de
PAPER-04 faltam regras técnicas de execução/custos/risco, fonte/disponibilidade,
eventos, novas decisões/autorização autenticada, revisão independente e recuperação
como escritor corrente. Ampliar revisão dos horários para as sessões utilizadas;
não exigir enumeração literal futura nem tomar planejamento por ocorrência.
RAW de marcação e histórico ajustado dos analistas têm requisitos distintos.
Nenhuma execução, ingestão financeira oficial, inferência paga ou leitura de preços
do holdout/H2 foi feita nesta tarefa. A ordem e os critérios de saída estão no
[roadmap](ROADMAP.md).
O [estado anterior](archive/ESTADO_ANTERIOR_2026-10-13.md) foi preservado: acumulava
fotografias históricas, inclusive status depois superados, e não orienta a operação atual.
