# Ciclo de uso da plataforma

Mapa conferido no código em **15/10/2026**. Referências de autoridade:
[direção e decisões](DIRECAO_DO_PROJETO.md), [roadmap](ROADMAP.md) e
[estado atual](ESTADO_ATUAL.md). Vinculado a DP-17–DP-24 e APP-01–APP-05.

**Frontend DP-23 aplicado:** menu permanente Carteira/Operações/Agentes/Comparação/Dados,
com seletor de carteira compartilhado. As etapas dos agentes ficam visíveis na
navegação da própria área. Laboratório e Legacy preservam identidades separadas.

## Destino do produto

Criar ou selecionar uma carteira → registrar sua base → acompanhar preços,
patrimônio e proventos → pedir um quórum para aquela carteira e um dia-alvo →
revisar a proposta → aprovar ou rejeitar → registrar automaticamente a cesta
simulada aprovada → acompanhar o resultado. Todas as versões e decisões devem
permanecer consultáveis. Operações reais externas são apenas registros de
negócios que Lucas já fez; a plataforma não envia ordens à corretora.

## O que pode ser feito hoje

| Etapa | Caminho na interface | Situação e limite |
|---|---|---|
| Criar carteira do zero | Início → Criar carteira | Implementado: nome, natureza simulada/real externa, capital e data inicial. Começa em caixa |
| Escolher carteira | Seletor do topo | Implementado nas áreas ativas; operações/análise usam a carteira escolhida. Laboratório/Legacy têm contextos independentes |
| Fazer a alocação inicial | Registrar operação → Compra → Ver prévia → Confirmar registro | Implementado por ativo; distribuidor automático de capital/cesta inicial ainda não existe na tela |
| Comprar mais ou vender | Mesmo formulário, com quantidade, preço, custos e data econômica | Implementado; prévia confere efeito em caixa e posições, sem venda descoberta nem crédito. Não busca preço de execução automaticamente |
| Registrar operação antiga | Informar a data econômica correta | Implementado; replay valida também os eventos posteriores. Data de cadastro permanece atual |
| Corrigir ou anular lançamento | Operações → Corrigir → prévia/confirmação | Implementado; original e motivo permanecem na rastreabilidade |
| Abrir análise para uma carteira | Carteira → Analisar carteira; ou Agentes → Configurar | Implementado: carteira, ativos, dia-alvo e sessão dos dados; estado da carteira preservado em execução própria |
| Preparar dados | Agentes → Dados e custo → Verificar dados e custo | Comando guiado prepara e faz preflight; sujeito à disponibilidade/integridade. Preparação manual continua nas opções técnicas. Não atualiza a marcação financeira pessoal |
| Rodar o quórum por ativo | Preflight → revisar orçamento/consentimento → executar lote | Fluxo existente: cinco analistas técnicos por ativo, consenso e Risk. Até cinco ativos. Inferência paga depende de autorização própria |
| Consultar pareceres anteriores | Seletor de execuções do Radar; histórico da carteira no cadastro de análise | Implementado; abrir consulta não repete inferência. Reanálise usa outra identidade, preservando a anterior |
| Obter proposta considerando a carteira inteira | Agentes → Resultados → Plano de alocação | Implementado em APP-05: informar custos, preparar/preflight, autorizar uma chamada do gestor; quantidades parciais/totais, posição/peso/caixa antes/depois. Exige quórum completo e revisão atual da carteira |
| Aprovar e aplicar cesta automaticamente | Plano → Ver prévia → aprovação financeira | Implementado para simulação manual aos preços CLOSE RAW identificados, registro hoje em uma transação idempotente. Buy & Hold/externas consultivas; não é OPEN futuro nem execução prospectiva |
| Ver patrimônio estimado e evolução diária | Início → carteira selecionada | APP-03 parcial: posições atuais ao último CLOSE RAW local identificado; série diária reconstitui posições/caixa de cada data, com correções atuais. Lacunas e fechamento pendente não são preenchidos; sem preços ao vivo/proventos |
| Explorar histórico das ações | Início → abaixo de Suas posições → Histórico das ações | DP-25: escolher uma/várias ações, atalhos 5D a Máx ou datas; reais/% e Close/Adj Close Yahoo. Arrastar mede preços/diferença/% entre duas datas. Histórico máximo em cache desde 2000; Atualizar histórico Yahoo faz coleta explícita. Separado das marcas B3 do patrimônio |
| Dividendos/JCP, splits e bonificações | Carteira → proventos/eventos | Pendente em APP-04, incluindo direito, recebimento e ajustes rastreáveis |
| Aportes, retiradas e liquidação | Carteira → movimentações de caixa | Pendente para carteiras pessoais; atualmente capital inicial e caixa econômico das compras/vendas. Sem liquidação de corretora |
| Backup/restauração pela interface | Administração/recuperação | Pendente para o aplicativo pessoal. PAPER-03 qualifica recuperação sintética própria, sem cobrir automaticamente o SQLite pessoal e os novos quóruns |
| Consultar fases antigas | Legacy | Implementado, somente consulta; PETR4/H2 e backtests antigos preservados |

## Roteiro cotidiano

As áreas atuais têm estes papéis:

| Área | Uso no ciclo |
|---|---|
| Carteira (`/`) | Patrimônio estimado, evolução diária, posições, preços diários e caixa econômico; entrada para operações, proventos e quórum |
| Operações (`/operations`) | Cadastro de compras/vendas, prévia, confirmação, correções e histórico da carteira selecionada |
| Criar carteira (`/wallets/new`) | Nome, natureza, capital/data inicial; ao confirmar, encaminha para Operações |
| Comparação (`/comparison`) | Carteiras independentes; valores registrados, sem retorno/gráfico quando faltam marcas |
| Dados (`/data`) | Prontidão, fonte/sessão, bloqueios e próximos passos da execução operacional |
| Mercado (`/market`) | Explorar os dados/pareceres da execução selecionada; não é homebroker nem livro de ordens |
| Agentes (`/radar`) | Configurar, Dados e custo e Resultados; comitês e histórico preservados |
| Laboratório (`/laboratory`, `/portfolio`) | Demonstrações e gestor consultivo anterior; não operam a carteira pessoal |
| Auditoria (`/#audit`) e Logs (`/logs`) | Integridade e processos existentes; não substituem o histórico de operações da carteira |
| Legacy (`/legacy`) | Acervo PETR4/H2/backtests, com navegação secundária e mutações web bloqueadas |
| Cabeçalho → Atualizar dados da bolsa | Preparar a sessão da execução operacional corrente; não cria outra execução nem atualiza automaticamente o patrimônio pessoal |

1. Abrir o Início e escolher a carteira. Buy & Hold e Multiagentes existentes
   continuam com a base manual DP-20; não recriar nem realocar ao atualizar a página.
2. Para uma carteira nova, cadastrar natureza, capital e data. Registrar cada
   compra inicial com preço e custos conhecidos. Conferir a prévia e confirmar.
   Carteira pessoal pode ter outro capital/composição; a base comum de cerca de
   20% por ativo se aplica ao grupo comparativo definido por Lucas.
3. Registrar compras/vendas adicionais da mesma forma. Em carteira real externa,
   informar somente negócios realmente realizados fora da plataforma. Em simulação,
   registrar a convenção de preço/custos utilizada, sem confundi-la com execução real.
4. Para consultar os agentes, usar **Analisar carteira**. Em Agentes → Configurar,
   conferir carteira, ativos e datas; trocar a carteira ali também é possível.
5. Clicar **Criar análise e continuar**. Isso registra o contexto, seleciona
   a execução operacional e navega para ela. Não prepara dados nem chama o provedor.
6. Na etapa **Dados e custo**, clicar **Verificar dados e custo**. O fluxo prepara
   os dados e verifica requisitos ao terminar. Dados ausentes/incompletos bloqueiam; não preencher
   silenciosamente com barras antigas ou sintéticas.
7. Se desejar inferência paga, revisar o lote, reservas, teto e consentimentos
   mostrados pelo backend. Aprovar gasto de IA e aprovar movimentação financeira
   são decisões distintas. A criação da análise não autoriza nenhum dos dois.
8. Consultar votos, consenso, Risk e parecer final por ativo. Em **Plano de
   alocação**, informar o custo percentual desta simulação, preparar o contexto,
   revisar reserva/teto e autorizar a chamada separada do gestor. Todos os
   pareceres devem estar completos; a carteira precisa manter a revisão original.
9. Revisar quantidades de compra/venda/manutenção, reduções parciais ou saídas,
   preço CLOSE RAW/data/origem, custos e caixa. **Ver prévia → aprovar e registrar**
   grava a cesta inteira no mesmo SQLite, como simulação manual na data de hoje.
   Não usa preço de agora nem OPEN futuro. Buy & Hold permanece sem rebalanceamento;
   carteira externa recebe consulta, sem registrar negócios simulados. Voltar à
   carteira/Operações para conferir o histórico e o vínculo com a proposta.
10. Consultar execuções anteriores no histórico. Para outra análise, criar nova
    execução. Não sobrescrever pareceres, trocar a sessão de uma execução antiga
    nem apagar incidentes para conseguir repetir um lote.

## As quatro datas que não devem se confundir

| Data | Significado |
|---|---|
| Dia-alvo | Quando se pretende usar a análise; padrão amanhã, ou próxima sessão planejada se amanhã não houver pregão |
| Sessão dos dados | Último fechamento escolhido, obrigatoriamente anterior ao alvo e já encerrado; publicação é conferida na preparação |
| Criação/preparação/execução | Horários reais em que contexto, dados e pareceres foram produzidos; não retroagem com o seletor de data |
| Data econômica da operação | Quando a compra/venda registrada aconteceu no modelo ou fora do sistema; independente da data do cadastro |

Exemplo: em **15/10**, o alvo padrão é **16/10**. Antes do corte conservador das
18h, os dados sugeridos vão até **14/10**, caso disponíveis. Lucas pode selecionar
**15/10** como alvo para uma análise de hoje. Depois do corte, a sessão sugerida
pode ser 15/10, mas a disponibilidade do arquivo continua sendo outra verificação.

A extensão usa o calendário planejado DATA-01 até dezembro de 2026; não infere
sessões além da cobertura. Reanálise histórica é produzida agora com o estado
atual preservado da carteira e a versão dos dados preparada agora. Não equivale
a uma previsão feita no passado ou a um backtest sem informação futura.

**Limite do modelo atual:** dia-alvo e posições são guardados no contexto, mas
os prompts selados do comitê técnico não recebem esses campos. Produzem sinais
e justificativas com indicadores por ativo, sem preço-alvo numérico nem horizonte
condicionado à data escolhida. O novo gestor APP-05 recebe esses campos para
coordenar quantidades, com contrato próprio e preços de referência explícitos.
Não relabela sinais antigos como previsões condicionadas a outro horizonte.

## Histórico e rastreabilidade

| Registro | Onde vive | Política atual |
|---|---|---|
| Carteiras, operações, correções e arquivamento | `data/platform/manual-v1/manual.sqlite3` | Eventos encadeados, append-only e comandos idempotentes; correção preserva original |
| Identidade e seleção das execuções | `data/radar/registry.json` | Reuso do registro existente; seleção é ponteiro operacional, identidades anteriores continuam registradas |
| Carteira/revisão, alvo, referência e horário de criação | `data/radar/analysis-<command_id>/wallet-analysis.json` | Contexto selado e imutável, vinculado à identidade da execução |
| Dados preparados, votos, pareceres, reservas e chamadas | Raiz de cada execução Radar | Reuso dos inputs congelados, eventos e diário de chamadas existentes; sem reexecutar ao consultar |
| Planos do gestor, contexto, inferência e falhas/recuperações | `wallet-manager/<id>` sob a execução Radar | Contexto/resultados/autorizações imutáveis, diário/envelopes duráveis e falhas por tentativa preservadas; mudança de contrato mantém consulta e bloqueia novas ações sobre contexto antigo |
| Cesta aprovada | Eventos TRADE no SQLite pessoal | Uma transação; fonte identifica run/proposta/hashes, referências, custos e data. Repetição/concorrência não duplicam, correções preservam os originais |
| Último job e último preparo | `job.json` / `last_prepare.json` da execução | Resumos operacionais substituíveis; não são um arquivo integral de todas as tentativas de preparação/preflight |
| Evidências científicas e fases anteriores | `docs/evidence`, raízes históricas e Legacy | Preservadas; não migradas ou apagadas nesta entrega |

Repetir uma confirmação recebida parcialmente não duplica a criação: o mesmo
comando recupera o contexto original. Se a carteira mudar antes de criar uma nova
análise, a revisão desatualizada é recusada. Depois de criada, o snapshot permanece
e a diferença é informada na consulta.

APP-05 já preserva propostas, justificativas, autorização de inferência, envelopes,
falhas/recuperações e o vínculo da cesta aprovada com suas operações. Para cumprir
**todo e qualquer histórico**, ainda faltam rejeições explícitas do usuário,
expirações e cada tentativa de preparação/preflight/prévia em eventos duráveis.
Os resumos de job atuais não atendem sozinhos a essa exigência.
APP-03/04 devem preservar versões de marcações, retificações e eventos corporativos.
Hashes locais detectam diferenças; não autenticam origem nem substituem backup.

## Ordem de conclusão do ciclo

1. **APP-03:** consulta local RAW, patrimônio estimado e gráficos da home entregues.
   Ampliar cobertura contínua, qualificar preços recentes e integrar comparação,
   mantendo origem/data e ausência explícitas. O histórico atual usa correções
   conhecidas agora, sem se apresentar como marcação preservada no passado.
2. **APP-05, contexto dos agentes:** entregue para o gestor final, com posições,
   caixa, custos, revisão e dia-alvo; comitês por ativo permanecem separados.
3. **APP-05, decisão e aplicação:** entregue para registro manual aos preços de
   referência, com prévia, aprovação e transação idempotente. Completar auditoria
   integral, risco global, eventos e qualificação prospectiva antes de ativar OPEN/D+2.
4. **APP-04:** proventos/eventos e reconciliação, evitando duplicar direito e caixa.
5. **Operação diária:** backup independente, restauração qualificada do aplicativo,
   auditoria de tentativas e consulta completa pela tela. Não confundir a recuperação
   da demonstração com prontidão do aplicativo pessoal.

O foco permanece nas carteiras já cadastradas. Não criar outro simulador, outra
base inicial ou outra arena para contornar as integrações que faltam.
