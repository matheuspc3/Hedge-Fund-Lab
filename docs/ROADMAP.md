# Roadmap do Hedge-Fund-Lab

Atualizado em **16/10/2026**. Plano de trabalho a partir da V7.6.5.
Este é o planejamento ativo. Especificações científicas, aprovações e autorizações
continuam em seus documentos próprios; um checkbox aqui não as substitui.

Ler primeiro a [direção do projeto e decisões aceitas](DIRECAO_DO_PROJETO.md).
Ela define o destino do produto; este roadmap define a ordem para chegar lá.

[Início](../INICIO.md) · [Estado atual](ESTADO_ATUAL.md) ·
[Documentação e evidências](README.md)

## Objetivo e ponto de partida

Acompanhar carteiras simuladas ao longo dos pregões: decisões rastreáveis,
preços com origem, autorizações válidas, operações paper determinísticas,
caixa, posições, liquidação, patrimônio e reconciliação. O TCC deve explicar
o que foi implementado, o que foi observado e o que ainda não foi demonstrado.

**Experiência combinada:** tela inicial de carteira com seletor de estratégia,
patrimônio, variações em R$/%, posições e evolução diária comparativa.
**D0 de referência: 13/10/2026.** A referência multiativos tem pesos iniciais
aceitos de **20% em cada um dos cinco ativos**. Detalhes de entrada e manutenção
continuam em PAPER-01; nenhuma posição ou execução é criada por esta decisão.

**Base existente:** V7.6.5 `LEDGER_QUALIFIED_OFFLINE`, com motor financeiro V5
reutilizado, SQLite temporário, eventos, replay, contabilidade, D+2 e histórico
sintético. O dashboard lê uma exportação verificada. Não há carteira oficial
multiativos ativa, ingestão diária ou execução oficial habilitada.
PAPER-03 acrescenta raiz durável exclusivamente sintética e recuperação
isolada, preservando esse escritor TEMP e o leitor da exportação.

**Não reconstruir essa base.** Revisar e ampliar apenas os contratos e adaptadores
necessários. [Limites da entrega](evidence/hfl_paper_ledger_v765/LIMITATIONS.md).

## Sequência principal

A sequência técnica abaixo sustenta o [fluxo de uso diário](#uso-diário-pela-interface--dp-17).
Qualificar mais um ensaio não substitui disponibilizar esse fluxo ao usuário.
Cada incremento deve indicar qual ação cotidiana passa a funcionar na interface.

| Ordem | ID | Entrega | Situação | Depende de | Pronto quando |
|---|---|---|---|---|---|
| 0 | DOC-01 | Vault, índices, estado atual e separação do histórico | Concluído nesta organização | — | Início único; links verificados; documentos de evidência preservados |
| 1 | PAPER-01 | Contrato operacional do piloto multiativos | **Bases DP-09–DP-15 aprovadas; regras técnicas pendentes** | V7.6.5 | [DRAFT parcialmente revisado](PILOTO_MULTIATIVOS_SPEC.md); custos, risco, dados, prazos/execução e autoridade técnica ainda pendentes; nenhuma operação ativada |
| 2 | DATA-01 | Calendário e dados prospectivos | **Calendário planejado/importador local qualificados; primeiro ZIP/bundle observado pendente** | PAPER-01 delimita fonte e semântica; incrementos locais/documentais autorizados separadamente | Extensão versionada, 47 checks direcionados; planejamento 13/10–31/12 e D+2 sem extrapolação; validar arquivo real, condições de aquisição/uso e eventos corporativos antes da integração |
| 3 | PAPER-02 | Fluxo prospectivo completo offline | **Ensaio integrado sintético implementado** | Ensaio autorizado separadamente; fixtures DATA-01 e parâmetros de teste explícitos | Duas carteiras, oito sessões, CLOSE t → proposta → validação → autorização/intenção ex-ante → OPEN t+1 → D+2 → reconciliação; projeção JSON e checks direcionados |
| 4 | PAPER-03 | Preparação de operação e ensaio | **Durabilidade/restauração sintéticas qualificadas; revisão independente pendente** | PAPER-02 | Raiz dedicada, continuidade entre processos, sessão atômica, backup SQLite/restauração isolada e runbook; acesso local inspecionado, sem autenticação financeira real; ativação ainda separada |
| 5 | PAPER-04 | Piloto paper prospectivo independente | **Bloqueado para execução** | PAPER-03; protocolo e autorizações específicos | Sessões novas registradas sem antecipação de dados; falhas/interrupções auditadas; nenhuma decisão V1/V2 convertida em ordem |
| 6 | PAPER-05 | Rotina diária e comparação | Planejado | Piloto aceito e política de automação definida | Atualização idempotente, alerta de defasagem e recuperação; comparações somente sob dados, custos e períodos equivalentes |

Registro consultivo separado, DP-01/DP-08/DP-16: [tentativa de previsão de 14/10](daily/2026-10-14.md).
Bloqueio das 03h preservado no histórico; reconsulta das 12:05 mostrou barras
Yahoo válidas nos cinco ativos. Preparo iniciado pelo operador às 13:00 terminou
às **13:02:16**, com **cinco inputs PREPARED**, zero pareceres/claims/chamadas novas.
Vínculo do dashboard alinhado a 13/10; corrigida exibição de bloqueio antigo
durante job novo. Retomada agora depende de preflight válido e autorização
específica do orçamento agregado. É preparação consultiva, não conclusão de
PAPER-05 nem ativação do piloto.

Ordem de dependência, sem prazo inventado: `PAPER-01 → DATA-01 → PAPER-02 → PAPER-03 → PAPER-04 → PAPER-05`.
Evidência real e revisão das políticas bloqueiam a **ativação oficial**, não o
ensaio sintético PAPER-02 autorizado e entregue separadamente.
Não atribuir uma nova versão Premium antes de fechar o escopo da respectiva entrega.

**Pendência específica DATA-01:** após Lucas confirmar o escopo de uso local,
validar o primeiro ZIP diário pós-D0 que ele fornecer pelo mecanismo local da
[seção 14](PILOTO_MULTIATIVOS_SPEC.md#14-data-01--calendário-planejado-e-importação-local-versionados).
A [avaliação de provedores e do fluxo](AVALIACAO_COLETA_DADOS_2026-10-14.md)
recomenda essa prova manual para a marcação RAW e mantém a fonte dos agentes em
aberto; não autoriza aquisição, exibição, gasto ou troca de fonte.
Enquanto o arquivo está pendente, a proposta técnica PAPER-01 foi consolidada
na [tabela da seção 8.1](PILOTO_MULTIATIVOS_SPEC.md#81-proposta-objetiva-para-fechar-regras-técnicas--14102026):
execução/prazos, custos, risco, eventos, caixa e autorização, com justificativas
e decisões restantes de Lucas. DP-01–DP-15 não foram reabertas; proposta ainda
não aprova parâmetros, gasto ou ativação.
Refinamento R7 solicitado antes do aceite: [redução sob veto/excesso e drawdown](PILOTO_MULTIATIVOS_SPEC.md#41-redução-de-posições-sob-veto-ou-excesso-de-risco--proposta-r7)
separa vendas elegíveis de novas compras, preserva controles e perda histórica;
agentes com admissão até 85% versus referência com entrada até 100%. Proposta
documental pendente de decisão/qualificação, sem alterar V5/V2 ou implementar extensão.
Avaliação do `justfile`, extrator B3, Radar e provedores registrada no documento
ligado acima. B3 não deve ser automatizada até resolver as condições aplicáveis;
arquivo local segue o caminho imediato somente se Lucas confirmar o escopo de
uso. Nenhum novo downloader foi criado.
Sem ordens, inferências pagas, ETL antigo ou ativação. Planejamento por regra
documentada/exceções não exige enumeração literal de pregões futuros; ocorrência,
negociação de cada instrumento e liquidação continuam distintas.

## PAPER-01: bases aprovadas; regras técnicas pendentes

O [contrato operacional do piloto](PILOTO_MULTIATIVOS_SPEC.md), em
**DRAFT — BASES APROVADAS; REGRAS TÉCNICAS PENDENTES**, atende DP-01–DP-15: matriz de reuso com evidências
de código/testes, ciclo causal, benchmark 20%, indicadores e plano mínimo
DATA-01/PAPER-02/PAPER-03. Não declara aprovação, freeze ou prontidão operacional.
Foram usadas, fora das evidências seladas, a
[arquitetura do ledger](evidence/hfl_paper_ledger_v765/LEDGER_ARCHITECTURE.md),
[integração Global PM](evidence/hfl_paper_ledger_v765/GLOBAL_PM_INTEGRATION.md) e
[limitações](evidence/hfl_paper_ledger_v765/LIMITATIONS.md).

Lucas aprovou em 14/10 as bases DP-09–DP-15: finalidade operacional/descritiva,
capital R$ 100 mil por carteira, Buy & Hold sem rebalanceamento/reinvestimento,
proventos em caixa, sem aportes/retiradas, rotina manual/autorização explícita,
revisão após 20 pregões e início efetivo elegível. Custos, limites/veto, fonte,
eventos, prazos e execução continuam pendentes. A primeira implementação
local DATA-01 foi autorizada e qualificada separadamente com fixtures, sem
aprovar essas recomendações nem autorizar download ou gasto.
O limite fixo de exposição 85% do V5 e o acoplamento de autorização à mesma
sessão/marca exigem extensão versionada qualificada em PAPER-02; não basta
conectar o snapshot V2 nem retirar a guarda TEMP do escritor existente.

| Decisão a fechar | O que precisa ficar explícito |
|---|---|
| Identidade e escopo | Novo tratamento, carteira, universo, capital virtual e sessões; finalidade de demonstração operacional ou avaliação científica |
| Relógio causal | Dados disponíveis em t, instante da decisão, prazo de autorização, disponibilidade do preço observado em t+1 e horário de reconciliação |
| Preços e fonte | RAW para contabilidade; representação dos indicadores; OPEN/CLOSE; fonte, vintage, hash, cache e condições de uso |
| Quantidades e execução | Lote/frações, limite de exposição, slippage, fill integral/parcial, ausência de preço, cancelamento e expiração |
| Custos e patrimônio | Custos versionados, caixa/reservas/recebíveis/D+2, rendimento de caixa e tratamento de proventos/eventos corporativos |
| Risco | Proposta R7 refinada: redução pura elegível sob veto/excesso; drawdown bloqueia compras até revisão sem impedir saída; exposição agentes 85% versus referência até 100%. Aceite/qualificação pendentes, sem mudar V5/V2 |
| Autorização | Quem autoriza, como autentica, vínculo com carteira/proposta/estado/quantidades/prazo; inferência paga e ordem paper são consentimentos distintos |
| Persistência e recuperação | Raiz oficial futura, backups, restauração, IDs/idempotência, corrupção e falhas sem reparo silencioso |
| Avaliação | Objetivo, duração, controles, métricas, critérios de parada e sucesso operacional; não condicionar sucesso a retorno positivo |
| Orçamento | Dados, infraestrutura e inferências separados; limites e consentimentos próprios antes de qualquer gasto |

Saída documental entregue: recomendações e bloqueios nomeados, matriz e plano
de qualificação offline. Revisão humana ainda pendente para avançar nas escolhas
aplicáveis. Redigir o contrato
não autoriza criar a carteira oficial, operar, gastar ou acessar o holdout H2.

## DATA-01: incrementos locais entregues, bloqueios oficiais explícitos

[Contrato e uso do adaptador](PILOTO_MULTIATIVOS_SPEC.md#9-data-01--mecanismo-implementado-e-qualificado-offline):
manifest local + ZIP COTAHIST → validação/reuso do parser → bundle RAW com hashes,
seleção e disponibilidade conservadora → consulta OPEN/CLOSE. Calendário sintético
separado; o verificado continua limitado a agosto/2026. CLI, reimportação e revisão
explícita exercitadas; 16 checks direcionados passaram, sem rede ou suíte completa.

O [segundo incremento](PILOTO_MULTIATIVOS_SPEC.md#10-data-01--segundo-incremento-evidencias-b3-e-formato-diario)
preserva nove documentos públicos B3 e seus recibos/hashes, consome o artefato
documental de 2026 e qualifica COTAHIST diário pós-D0 com 24 checks. Datas são
conferidas antes do parser; origem documentada exige catálogo independente,
atualmente vazio. Não houve download de preços nem aprovação de uso/distribuição.

Bloqueio: ofício de feriados cobre 2026, mas não se comprovou enumeração positiva
para 13/10–30/11 e suas duas sessões seguintes sem inferência por dias úteis.
`b3-2026` retorna bloqueio de cobertura positiva/D+2; lista histórica e H2 intactos.
Esse é o bloqueio do artefato DATA-01 anterior, preservado. **Incremento atual:**
[extensão local](../scripts/pilot_observed_data.py), sem mudar módulos fixados,
planeja 53 sessões em 13/10–31/12 por semana documentada e exceções B3 do segmento.
Próxima sessão e D+2 usam calendários separados; cobertura 2027 é recusada.
Base semanal do participante/íon e alcance da corroboração UP2DATA são explícitos;
não se alega calendário positivo oficial nem sessão ocorrida. Horários centrais
OC005 revisados para 13–14/10; fora disso, indisponibilidade de vigência.
Registro de aquisição, original/hash, validação do diário e consulta RAW
qualificados com 19 novos checks, 24 anteriores e 4 do parser: **47 aprovados**.
Revisão explícita sem sobrescrita, disponibilidade conservadora da importação,
fixture segregada e leitura PAPER-03 preservada. Lucas confirmou ausência de ZIP;
observações e bundles observados continuam vazios. RAW de marcação separado do
histórico ajustado Yahoo dos analistas. Condições/canal de coleta automática
continuam em avaliação, preservando arquivo local como opção disponível.
Essas etapas DATA-01 não implementaram execução nem aprovaram políticas financeiras.
Os bloqueios reais continuam valendo para ativação oficial; o ensaio PAPER-02
abaixo utiliza somente parâmetros e dados de teste.

## PAPER-02: duas carteiras e projeção sintéticas

Atende **DP-01/03/04/05/07**. [Ponte versionada](../scripts/pilot_paper.py),
[qualificador executável](../scripts/qualify_pilot_paper.py) e
[checks](../tests/test_pilot_paper.py). [Contrato implementado](PILOTO_MULTIATIVOS_SPEC.md#11-paper-02--ensaio-integrado-exclusivamente-sintetico).
Um comando gera apenas em TEMP oito bundles diários, SQLite, exportações
independentes e `projection.json`. Agentes: HOLD inicial, compra de 100 PETR4,
venda posterior de 40; referência: uma entrada de cinco alvos de 20% e manutenção.

Reuso sem editar fontes antigos: bytecode V5 de reserva/fill/contabilidade,
risco com warm-up sintético e transações/envelope/replay/idempotência V7.6.5.
Dependências locais vinculam calendário e políticas de teste; `POLICY` original
permanece em 85%. A referência tem política própria, sem alavancagem. Relógio
econômico e liberação de fixtures são simulados; importação e gravação preservam
seus horários reais. Nenhuma aprovação humana real ou publicação B3 é alegada.

UX-M3/M5 já conecta esta projeção explicitamente sintética ao seletor/cartões/
gráfico da tela inicial, com estados indisponível e histórico insuficiente.
PAPER-03 entrega durabilidade/backup sintéticos e documenta acesso local; PAPER-01 segue DRAFT,
DATA-01 agora tem planejamento versionado, mas segue sem bundle real. Eventos corporativos
não suportados bloqueiam a sessão e a continuidade, sem tratamento fictício.

## PAPER-03: durabilidade e recuperação exclusivamente sintéticas

Atende **DP-01–DP-05/07**, com [adaptador/CLI](../scripts/pilot_trial.py),
[checks](../tests/test_pilot_trial.py) e
[runbook/limites](PILOTO_MULTIATIVOS_SPEC.md#13-paper-03--persistência-e-recuperação-do-ensaio-sintético).
Raiz dedicada `data/platform/paper-synthetic/`; duas carteiras continuam entre
processos sem reinicializar eventos/capital. Uma transação confirma sessão,
checkpoints e recibo; repetição preserva IDs. Exportação atômica usa o leitor
existente via `HFL_PILOT_DEMO`, sem alterar a demonstração ou abrir escrita HTTP.
Backup nativo SQLite e restauração em diretório novo com comparação integral;
cópia antiga é STALE, restaurações ficam isoladas para conferência.

Estado qualificado é durabilidade/recuperação **sintética**, sem carteira oficial.
Revisão independente, adoção de uma cópia como escritor corrente, backup externo
e autoridade financeira autenticada continuam pendentes antes da operação
prospectiva. ACL local foi inspecionada; não testada sob outra conta. PAPER-01
segue DRAFT e DATA-01 real continua bloqueado. Verificação no
[estado atual](ESTADO_ATUAL.md#paper-03--durabilidade-e-restauração-sintéticas-14102026).

## Frentes de apoio e acervo histórico

### Uso diário pela interface — DP-17

**15/10 — DP-21/24, APP-05:** gestor vinculado ao snapshot pessoal e quórum íntegro
em Agentes → Resultados. Quantidades coordenadas, redução parcial/saída total,
custos declarados, prévia antes/depois e aprovação separada para registro atômico
idempotente no SQLite simulado. Preços são CLOSE RAW de referência identificados;
não cotação ao vivo nem OPEN futuro. Buy & Hold/externas permanecem consultivas.
Recuperação de resposta usa envelopes sem nova chamada. Risco global, eventos,
liquidação prospectiva e auditoria de todas as tentativas continuam pendentes.
APP-03 deve qualificar também a cotação recente desejada por Lucas, com horário
e atraso explícitos, antes de usá-la em uma prévia de movimentação.

**DP-23 / UX — frontend aprovado aplicado em 15/10:** navegação permanente
Carteira, Operações, Agentes, Comparação e Dados; criar carteira em `/wallets/new`,
comprar/vender/corrigir em `/operations`, contexto de carteira nos links e seletor
compartilhado. Agentes tem etapas visíveis Configurar → Dados e custo → Resultados;
o comando de verificar prepara e faz preflight, sem iniciar inferência. Orçamento
agregado, consentimento e confirmação de gasto permanecem próprios. Histórico,
recuperação e opções manuais continuam acessíveis. Comparação e proventos exibem
ausência de integração, sem curvas ou pagamentos fictícios. Laboratório e Legacy
usam contextos independentes. APP-03/04 e a execução prospectiva APP-05 seguem pendentes; o registro manual por cesta está no incremento DP-24 acima.
Ver [estado e verificações](ESTADO_ATUAL.md) e [ciclo atualizado](CICLO_USO_PLATAFORMA.md).

**Incremento de 15/10 — DP-22/APP-05 (cadastro de análise):** Início →
“Abrir quórum para esta carteira” e Radar → “Nova análise para uma carteira”.
Carteira/ativos, alvo editável (padrão amanhã/próxima sessão) e sessão de dados
separados; contexto/revisão imutáveis, histórico por carteira e nova identidade
operacional sem reiniciar o servidor a cada execução. Criação não coleta nem
infere. O comitê por ativo ainda não consome posições/dia-alvo nos prompts;
nesta etapa, gestor/aplicação ainda não existiam; a entrega manual DP-24 acima acrescenta esse fluxo. O
[mapa completo do ciclo](CICLO_USO_PLATAFORMA.md) identifica o fluxo existente,
as lacunas e a sequência APP-03 → APP-05 → APP-04/recuperação.

Pedido de Lucas em 14/10/2026: criar carteiras e registrar operações pela
plataforma, usando essas mesmas carteiras no início, com evolução e proventos.
Esta é a entrega de produto a priorizar junto das dependências operacionais;
não é uma nova arena ou reformulação estética.

**APP-01/APP-02 entregues em 14/10/2026:** a home cria/seleciona carteiras pessoais
e registra compras/vendas, com prévia, confirmação, histórico e correções.
`dashboard/manual_portfolio_api.py` mantém identidade e SQLite próprios;
o mesmo replay alimenta catálogo, detalhe e operações. As APIs anteriores e
`scripts/pilot_trial.py` continuam exclusivamente demonstrativas/consultivas.
O preparo Radar no cabeçalho não atualiza por si só a contabilidade pessoal.

**Base inicial em uso — DP-20:** Buy & Hold e Multiagentes cadastradas em 14/10,
cada uma com R$ 100 mil próprios e as mesmas cinco posições próximas de 20%.
Entrada manual autorizada, referência CLOSE de 13/10 e custos zero; caixa residual
R$ 177,44 por carteira. Cadastro real vazio excluído do seletor com evento
preservado. Estratégia/grupo/nota de entrada pertencem ao mesmo SQLite pessoal.
Não ativa o escritor prospectivo PAPER-04 nem reaproveita decisões antigas.

| Ordem / ID | Ação cotidiana a entregar | Critério de aceite / dependência |
|---|---|---|
| 1 / APP-01 | **Entregue: criar carteira e escolhê-la na home** | Nome, natureza, capital/data próprios e persistência entre processos. DP-20: Buy & Hold/Multiagentes com base inicial manual comum registrada; entrada prospectiva continua separada |
| 2 / APP-02 | **Entregue: registrar e consultar operações pela tela** | Compra/venda, custos declarados, data econômica/registro distintos; prévia, confirmação idempotente, replay histórico e correção/anulação preservando original. Caixa econômico, sem modelar liquidação da corretora; não cria ordem |
| 3 / APP-03 | **Parcial: patrimônio B3 e explorador histórico Yahoo entregues** | Home: evolução pelo mesmo ledger/RAW B3; abaixo das posições, histórico Yahoo máximo, ativos/períodos editáveis e variação por arraste (DP-25), barras intradiárias do dia e dos pregões anteriores em acervo local (DP-26), sem alimentar marcas/ordens. Estimativa atual separada do fechamento histórico; lacunas explícitas. Pendentes cobertura contínua de marcas, comparação e integração prospectiva DATA-01; sem preço ao vivo/proventos |
| 4 / APP-04 | Acompanhar dividendos/JCP e eventos | Elegibilidade/quantidade, ex-date, pagamento, origem e estado previsto/reconhecido/recebido; direitos e caixa sem dupla contagem; histórico recalculado de forma rastreável. Depende das regras e do tratamento de eventos de PAPER-01 |
| 5 / APP-05 | Gestor e aplicação manual aos preços de referência entregues; concluir recuperação/auditoria e execução prospectiva | DP-21/24: quantidades sobre a carteira escolhida → prévia → aprovação → cesta atômica/idempotente no ledger simulado; sem redigitação. Consentimentos pagos/financeiros separados. Pendentes preços recentes, risco global, eventos, D+2 e auditoria integral; não ativa o piloto prospectivo |

**APP-03, 15/10 — DP-04/05/17/23:** gráficos pessoais na home e preços por ativo
em reais/variação percentual, com tabelas acessíveis. Referências RAW preservadas
do Radar (09, 13 e 14/10), sem inferência/download/escrita financeira. Série pessoal
começa em 14/10; 15/10 permanece sem fechamento. Correções atuais são aplicadas
pela data econômica. Não promove dados ajustados, sintéticos ou custo médio a
cotação, nem ativa o piloto oficial. Verificação e limites no estado atual.

**Extensão DP-25:** explorador substitui o gráfico curto de ações por histórico
diário máximo Yahoo em cache, desde 2000 nos cinco ativos, com filtros de período,
seleção de uma/várias séries e medição por mouse/toque. Coleta explícita pela tela,
snapshots preservados e ajustes identificados; não altera a série patrimonial B3.

**Extensão DP-26, 16/10:** até 60 pregões o explorador usa barras intradiárias
(1D: 1 min; 5D: 5 min; até 15 pregões: 15 min; 1M: 1 hora). Cada pregão fechado
é guardado uma vez na melhor resolução que o Yahoo ainda tem; o dia aberto
aparece com ~15 min de atraso e atualiza a cada 2 min. Basta abrir a página ao
menos a cada ~3 semanas para não perder o 1 min. Próximo passo possível,
se Lucas pedir: usar a cotação recente na prévia de APP-05 (exige revisar DP-24).

**Definições confirmadas por Lucas:** DP-18 exige mesma base inicial de posições
nas carteiras simuladas comparadas, aproximadamente 20% por ativo, e DP-19 inclui
carteiras pessoais com operações reais externas. Estas têm capital/histórico
próprios, sem imposição da base do piloto. Cadastro histórico não envia ordens
nem retroage decisões dos agentes. A proposta de 85% dos agentes precisa de
revisão explícita para compatibilizar a base comum; não produzir venda automática.

**Próximo fluxo de produto solicitado — DP-21/APP-05:** sugestões sobre esta
carteira Multiagentes e movimentações simuladas registradas ao aprovar, com prévia,
revisão/idempotência e controles financeiros. APP-03 fornece as referências RAW
por data/origem para conferir marcação/evolução e apoiar esse fluxo; APP-04
acrescenta proventos. Regras prospectivas PAPER-01/04 continuam próprias. Não
remover guardas sintéticos nem usar custo médio como cotação; proposta consultiva
antiga não vira ordem para a carteira nova.

**Pronto para uso diário:** pelo navegador, criar uma carteira, registrar uma
operação válida, atualizar sua marcação e conferir posições, caixa, evolução e
proventos; fechar/reabrir sem perder dados; falhar ou repetir sem duplicar
lançamentos. O uso normal não exige CLI, edição de JSON ou cópia manual entre
carteira e home. Demonstração e Legacy permanecem separados. Esse critério
completo ainda depende de APP-03/04/05. APP-01/02 já permitem o cadastro
e acompanhamento contábil manual; [verificação e limites](ESTADO_ATUAL.md#app-0102--carteiras-pessoais-e-operações-pela-home-14102026).

### Legacy H2/PETR4 — consulta histórica (DP-16)

| ID | Trabalho | Situação / aceite |
|---|---|---|
| H2-01 | Preservar consulta histórica e apresentar pendências com precisão | Consulta no Legacy; auditoria V7.6.5 preservada; nova leitura deve registrar data/última marca sem alegar reconciliação ou encerramento |
| H2-02 | Melhorar texto de PENDENTE | Mantido apenas como melhoria de consulta histórica; não constitui fila ativa; GET não escreve nem muda política |
| H2-03 | Deliberações acadêmicas e eventual Final Test | Bloqueado até ratificação, freeze/release e autorização específicos; independente do piloto multiativos |

A observação documentada de 13/10 encontrou original pendente e supervisionada
expirada, ambas sem compra. Não é consulta em tempo real. Uma reconciliação
posterior só pode seguir o contrato original e evidência ex-ante; não inventar
decisão, aprovação ou fill. [Auditoria H2](evidence/hfl_paper_ledger_v765/H2_PENDING_STATE_AUDIT.md).

### UX e auditoria

Manter os IDs existentes do [plano UX](evidence/hfl_methodology_ux_review_v761/UX_MIGRATION_PLAN.md),
usando os estados atuais abaixo; o texto do plano original é histórico da proposta.

| Marco | Estado atual | Próximo trabalho / aceite |
|---|---|---|
| UX-M1 | Concluído como base | Reutilizar arquitetura de informação e nomenclatura |
| UX-M2 | Parcial | Adotar tokens, estados, ajuda e componentes nas páginas restantes |
| UX-M3 | **Início de carteira demonstrativa implementado — DP-02** | Abertura padrão sem carteira oficial; demonstração exige seleção explícita; menu, aliases, auditoria/readiness preservados em seção secundária |
| UX-M4 | Parcial; atualização compartilhada e revisão de orçamento web entregues | Preparo no cabeçalho; Radar permite teto agregado/consentimento pela interface, revalida orçamento e mantém confirmação paga separada; concluir demais controles de Mercado/Radar |
| UX-M5 | **DP-03–DP-05 implementados na demonstração PAPER-02** | Seletor, sessões/períodos calculados, patrimônio/caixa/posições/decisões, ativos e base 100; dados oficiais seguem dependentes dos gates operacionais |
| UX-M6 | Legacy reorganizado, DP-16 | Piloto PETR4/Pesquisa H2/backtests em hub secundário somente consulta; controles e POSTs exclusivos encerrados na web; evidências e GETs preservados |
| UX-M7 | Pendente | Auditoria, custos, logs, configurações e ajuda; sem expor journals privados |
| UX-M8 | Pendente, com checks incrementais | Teclado, foco, leitor de tela, zoom nativo 200%, responsividade e regressão; declarar limitações |

Prioridade: clareza dos estados e acompanhamento temporal durante PAPER-02/03;
migrar UX-M6 e UX-M7 em entregas pequenas; fechar UX-M8 após as migrações,
mantendo acessibilidade em cada mudança. Não abrir uma reformulação estética geral.

### UX-M4 — orçamento autorizado pela interface, 14/10/2026

Pedido de Lucas: parametrizar/revisar orçamento no Radar, sem CLI/chat. Atende
DP-01/13/16 e controles consultivos que apoiam PAPER-05. Painel após preflight
mostra reservas e exposição; usuário digita teto aceitável e confirma revisão.
GET `/api/platform/radar-budget` e POST `/api/platform/radar-budget-authorization`
reutilizam `radar_runs.budget/authorize_budget`, com validação web/CSRF/identidade,
teto e snapshot. Não alteram fontes selados, limite global ou reservas antigas.
Somente depois de registrar o orçamento, o preflight é refeito e a confirmação
paga continua separada no botão 3. A autorização existente cobre o conjunto de
ativos pendentes da execução; a tela identifica esse conjunto e exige sua seleção.
[Verificação/limites](ESTADO_ATUAL.md). Nenhuma autorização real ou inferência
executada pelo agente; próximo passo é Lucas revisar os valores na própria tela.

### UX-M4 — atualização manual no cabeçalho, 14/10/2026

Pedido de Lucas, DP-01/04/05/13/16. Botão “Atualizar dados da bolsa” na shell
compartilhada, disponível em todos os módulos. Reutiliza GETs do registro/view
e o POST `/api/radar/prepare` com CSRF e identidade da execução operacional;
nenhum endpoint/runner/dependência novo. Sessão, universo, progresso, bloqueios
por ativo e atualização da visualização explícitos. Abrir painel só consulta;
coleta começa no comando “Atualizar agora”. Não dispara inferência nem operações,
não muda a data do registro e preserva dados congelados/Legacy. Verificação e
limites no [estado atual](ESTADO_ATUAL.md). Próximo passo operacional é preparar
a sessão 13/10 pelo botão e avaliar seu resultado/preflight, sob os gates existentes;
ensaio demonstrativo e piloto oficial permanecem separados.

### UX-M3/M5/M6 — reorganização Legacy, 14/10/2026

Atende **DP-01/02/03/05/16** e TECH-01 na fronteira H2. `/legacy` é um hub
para `/legacy/paper`, `/legacy/h2` e `/legacy/backtests`. Aliases `/paper`,
`/h2`, `/index.html` (incluindo variantes existentes) continuam servindo as
mesmas páginas sem reescrever query/fragmento; `/#readiness` e `/#wallets`
apontam às consultas históricas correspondentes. Legacy é acesso secundário;
Auditoria multiativos permanece ativa. Home e seu overview HTTP não consultam
carteiras, decisões, supervisão, integridade ou relógio H2. Demonstração sintética,
seletor, posições, decisões, gráfico e “ainda não iniciado” preservados.
Sem alteração de estados, autorizações, reservas, ledgers ou pendências; não se
alega encerramento financeiro. Verificação e limites no [estado atual](ESTADO_ATUAL.md).
Próximo passo continua PAPER-01/DATA-01/PAPER-03; reorganização não ativa piloto.

### UX-M3/M5 — início integrado, 14/10/2026

[Contrato e comandos](PILOTO_MULTIATIVOS_SPEC.md#12-ux-m3m5--tela-inicial-demonstrativa-integrada)
e [verificação](ESTADO_ATUAL.md#ux-m3m5--tela-inicial-de-carteiras-14102026).
Preparação explícita do ensaio gera exportação selada em `data/platform/pilot-demo.json`;
GET verifica schema/classificação/replay e não escreve ou executa qualificador.
Períodos usam âncoras/cobertura do calendário sintético; não há constantes
permanentes de insuficiência. Chart.js local recebe valores calculados no backend,
com lacunas nulas, destaque da selecionada e tabela acessível. Chrome desktop e
390 px verificados com capturas reais. Sem novas dependências ou redesenho geral.

Próximo passo operacional: revisão independente/acesso/recuperação corrente e os bloqueios reais DATA-01/PAPER-01,
mantendo separado o modo demonstrativo. Integrar dados oficiais à mesma leitura
somente após qualificação de fonte, disponibilidade, calendário e autoridade;
não mudar rótulos ou promover a exportação sintética.

### Pesquisa multiativos e monografia

| ID | Trabalho | Dependência / limite |
|---|---|---|
| SCI-01 | Revisão independente V7.5/V7.6 e erratas | Preservar originais; distinguir conformidade de benefício financeiro |
| SCI-02 | Resolver pré-registro e proteção do holdout | Decisões D1–D12, protocolo, custos Radar/PM e freeze; nenhuma campanha paga autorizada |
| SCI-03 | Planejar C1/C3 e demais campanhas | C1=19 (10+9), C3=10 é recomendação V7.6.1; vagas PM compartilhadas e orçamento Radar separado; não é autorização |
| TCC-01 | Alinhar escopo e alegações com coautor/orientador | H2 e multiativos separados; resultados OA-1 exploratórios; limites dos dados sintéticos |
| TCC-02 | Atualizar texto, tabelas e figuras com evidências | Usar manifests e fontes identificáveis; publicar resultados negativos e limitações |
| TCC-03 | Pacote reproduzível para banca | Fontes, versões, instruções offline, dados publicáveis e revisão de privacidade; monografia e código coerentes |

[Decisões do pré-registro](evidence/hfl_methodology_ux_review_v761/PREREGISTRATION_DECISIONS.md) ·
[Erratas formais](evidence/hfl_methodology_ux_review_v761/FORMAL_ERRATA.md) ·
[Monografia](faculdade/monografia/main.tex).

## Pendências técnicas transversais

| ID | Item | Tratamento |
|---|---|---|
| TECH-01 | Fronteira web do experimento PETR4/H2 encerrada para mutações (DP-16) | POSTs `/api/forward/*` e `/api/h2/*` recusados antes de jobs/escritas; runners/CLIs selados intactos. Caminhos V1 do Gestor Global continuam sob proposta própria, fora deste encerramento |
| TECH-02 | 14 falhas na regressão registrada | Triar por causa e autoridade; não atualizar expectativas científicas para esconder falhas; baseline conhecido não é suíte verde |
| TECH-03 | Calendário antigo limitado a agosto; extensão DATA-01 planejada até 31/12/2026 | Preservar calendário antigo/H2; validar ZIP observado, revisar horários além de 14/10 e nova versão para 2027; planejamento não comprova ocorrência |
| TECH-04 | Persistência durável sintética qualificada em PAPER-03 | Raiz dedicada e backup/restauração isolada; prontidão oficial, adoção como escritor e backup externo/revisão independente continuam pendentes |

[Proposta backend V1](evidence/hfl_radar_ux_v763/V1_BACKEND_CLOSURE_PROPOSAL.md) ·
[Regressão V7.6.5](evidence/hfl_paper_ledger_v765/REGRESSION_REPORT.md).

## Como trabalhar a cada entrega

1. Ler DIRECAO_DO_PROJETO, escolher um ID e escrever escopo/aceite vinculado
   às decisões DP aplicáveis; conferir código e callers existentes.
2. Reutilizar o motor e os padrões existentes; evitar dependências e abstrações novas.
3. Implementar o menor incremento autorizado com um check significativo quando houver lógica não trivial.
4. Validar o fluxo afetado e a preservação; ampliar testes apenas se houver motivo.
5. Registrar resultado e limites, atualizar este roadmap e o estado atual.
6. Levar decisões científicas, ativação e gastos para suas aprovações específicas.

Organizar documentos não libera campanhas, Final Test, novas inferências ou
ordens. Manter evidências seladas, ledgers e configurações pessoais intactos.

## Fora do caminho crítico

Fine-tuning/LoRA, memória histórica, notícias/sentimento, MT5, envio de ordens reais a corretora,
tempo real sem atraso, intraday em marcas/operações, novos provedores e mais ativos. Só promover um item quando houver
necessidade demonstrada e capacidade de avaliá-lo sem comprometer o TCC.

## Histórico do planejamento

O [roadmap anterior](archive/ROADMAP_ATE_V765.md) foi preservado como registro
do desenvolvimento da arena, calibração e entregas. Seus rótulos de prioridade
e próximas fases pertencem àquele contexto. Specs e evidências citadas nele
continuam nos caminhos originais; este plano não altera contratos científicos.
