# Direção do projeto e decisões de produto

Versão 10 — **16/10/2026**. Decisões registradas a partir da conversa com Lucas.
Este documento fixa o destino do produto; o [roadmap](ROADMAP.md) organiza o
caminho e o [estado atual](ESTADO_ATUAL.md) registra o que já existe.

[Início](../INICIO.md) · [Documentação](README.md).

## Onde queremos chegar

**Uma plataforma com experiência de carteira de investimentos, que acompanha
diariamente carteiras simuladas de agentes de IA e estratégias de referência,
além de carteiras pessoais com operações reais registradas pelo usuário,
permitindo entender suas decisões, operações e evolução patrimonial.**

O diferencial é trocar a carteira observada, comparar as trajetórias e rastrear
como cada decisão afetou posições, caixa e patrimônio. O sistema multiagente,
os controles determinísticos e a auditoria sustentam essa experiência.

O backtesting é uma ferramenta do laboratório. O TCC descreve e avalia a
arquitetura, seus resultados e limitações. Benefício financeiro é uma hipótese
a investigar; não é uma conclusão nem condição para publicar os resultados.

## Decisões aceitas

São decisões de **direção e produto**, não aprovação acadêmica de protocolo,
autorização financeira ou afirmação de que a funcionalidade já foi entregue.

| ID | Decisão | Consequência prática |
|---|---|---|
| DP-01 | O foco é acompanhar carteiras simuladas ao longo dos pregões, com rastreabilidade | Priorizar o ciclo decisão → operação → patrimônio e sua leitura pelo usuário |
| DP-02 | A tela inicial deve ser a visão de carteira | Patrimônio e evolução aparecem primeiro; o índice técnico/auditoria fica acessível a partir dessa visão |
| DP-03 | Um seletor alterna a carteira dos agentes, Buy & Hold e outras referências definidas | Caixa, posições, decisões e resultados pertencem à carteira selecionada; não somar carteiras independentes |
| DP-04 | Exibir patrimônio, caixa, valor investido e variação em R$ e % | Oferecer dia, dias anteriores, mês, ano e últimos 12 meses, sempre com sessão de referência |
| DP-05 | Exibir resumo dos ativos/posições e evolução diária das carteiras | Mostrar valor, quantidade, participação e variação diária; gráfico conjunto permite comparar trajetórias |
| DP-06 | O marco de início do acompanhamento é **13/10/2026 — D0** | Data de referência do produto; não implica compra, aprovação ou fill nessa data |
| DP-07 | A referência multiativos terá **pesos iniciais iguais: 20% por ativo** | PETR4, VALE3, ITUB4, WEGE3 e BBAS3; percentuais de capital, não quantidades iguais nem pesos proporcionais ao preço |
| DP-08 | Preservar a separação H2/PETR4 e Radar/Global PM | Podem ser acessíveis no produto, mantendo tratamentos, capital, ledgers e contexto comparativo identificados |
| DP-09 | Primeiro piloto operacional, com resultados financeiros inicialmente descritivos | Não é teste confirmatório nem comprovação de superioridade |
| DP-10 | Duas carteiras: agentes e Buy & Hold, com R$ 100 mil independentes cada | Mesmo capital inicial; não aproveitar saldos ou posições dos ensaios/H2 |
| DP-11 | Buy & Hold sem rebalanceamento e sem reinvestimento de proventos | Entrada com alvos 20%; proventos ficam em caixa e pesos posteriores podem derivar |
| DP-12 | Sem aportes ou retiradas durante o piloto | Capital inicial é o único fluxo externo; eventos/custos internos continuam contabilizados |
| DP-13 | Rotina inicial manual diária e autorização explícita das operações paper | Sem scheduler/execução autônoma; mecanismo de autorização ainda precisa de qualificação |
| DP-14 | Revisar o funcionamento após 20 pregões | Acompanhamento pode continuar depois da revisão; não equivale a amostra científica suficiente |
| DP-15 | Início efetivo na primeira sessão elegível após preparação | Preservar 13/10 como marco do produto; não fabricar posições, aprovações ou série anterior à inicialização |
| DP-16 | A plataforma ativa é multiativos; o experimento independente PETR4/H2, a antiga Pesquisa H2 e os backtests anteriores ficam em Legacy, somente consulta | Atualiza DP-08 na navegação/prioridade: remove atalhos, carteiras e ações H2 da home; bloqueia mutações exclusivas na fronteira web; preserva registros e pendências. PETR4 continua no universo de cinco ativos; Radar, Mercado, Gestor Global, pesquisa e auditoria multiativos seguem ativos |
| DP-17 | O uso diário deve acontecer pela interface: criar e selecionar carteiras, registrar operações atuais ou antigas, acompanhar patrimônio, evolução e proventos, e conduzir a rotina dos agentes | Priorizar o fluxo completo de uso, além de ensaios e demonstrações. Cadastro, operações e posições devem alimentar a mesma carteira da home; decisões financeiras e natureza dos registros históricos continuam explícitas |
| DP-18 | As carteiras simuladas da comparação começam com as mesmas posições nos cinco ativos, aproximadamente 20% por ativo | Complementa DP-07/10/15: mesmo capital de R$ 100 mil por carteira, base inicial e posições comuns, sem copiar patrimônio entre ledgers. Depois, cada estratégia segue sua política; execução inicial, custos e arredondamento precisam de regras qualificadas |
| DP-19 | Permitir carteiras simuladas e carteiras pessoais de operações reais já executadas fora do sistema | Cadastro identifica a natureza; registro manual não envia ordem à corretora. Carteiras pessoais têm capital/histórico próprios e não entram automaticamente no grupo comparativo do piloto; lançamentos antigos não fabricam decisões prospectivas dos agentes |
| DP-20 | Iniciar Buy & Hold e Multiagentes na aplicação com a mesma cesta simulada apresentada e R$ 100 mil independentes | Lucas autorizou em 14/10 excluir o cadastro real externo vazio e criar duas simulações. Entrada manual em 14/10, referência CLOSE B3 de 13/10, custos iniciais zero, ações inteiras e sobra em caixa; não é fill prospectivo de agentes nem alteração dos ledgers selados |
| DP-21 | Agentes devem sugerir movimentações sobre a carteira Multiagentes cadastrada; a aprovação do usuário deve registrar automaticamente as movimentações simuladas | Próximo fluxo APP-05: proposta vinculada à revisão dessa carteira → prévia/validação → aprovação explícita → registro paper idempotente. Não pede redigitar cada operação; não implica scheduler, envio à corretora ou autorização de inferência paga |
| DP-22 | Abrir quórum pela interface para a carteira escolhida, com dia-alvo editável e padrão amanhã/próxima sessão; preservar todo o histórico | Pedido de Lucas em 15/10: mapear o ciclo completo de criar/alocar/comprar/vender/analisar. Cada análise tem identidade e contexto próprios; datas históricas são reanálises produzidas agora. O cadastro de contexto está implementado; o comitê por ativo ainda não consome posições/dia-alvo, e o gestor quantitativo foi acrescentado depois em DP-24/APP-05. [Mapa completo](CICLO_USO_PLATAFORMA.md) |
| DP-23 | Aplicar a nova identidade visual e a navegação aprovadas na prévia | Lucas: “aí sim. gostei! pode fazer”. Fundo claro, azul mineral, menu visível Carteira/Operações/Agentes/Comparação/Dados, contexto de carteira compartilhado e análises por etapas. Laboratório, Legacy e Auditoria secundários; registros independentes preservados. Usar dados e APIs existentes, sem promover valores fictícios da prévia, declarar preços/proventos entregues ou autorizar inferências durante a implementação |
| DP-24 | O gestor final propõe quantidades coordenadas para a carteira; compra/venda pode ser parcial ou total | Lucas esclareceu que VENDA não significa vender tudo. O gestor recebe posições, caixa, custos declarados e dia-alvo; a prévia mostra quantidades e efeito econômico. Lucas escolheu registrar a simulação aos preços de referência exibidos, enquanto cotação do momento não está integrada. Custos são informados e aprovados por proposta; não presumir taxa zero ou 0,1%, nem apresentar fechamento anterior como preço ao vivo. DP-11 mantém Buy & Hold sem rebalanceamento; carteira externa recebe consulta, sem negócios simulados automáticos |
| DP-25 | Explorar o máximo de histórico diário disponível das ações via yfinance, selecionar uma ou várias e medir a variação em períodos editáveis ou por arraste | Pedido explícito de Lucas em 15/10. Coleta local Yahoo para esse gráfico, com fonte, ajustes e cobertura identificados; cópias e versões preservadas. Não substitui marcas RAW B3 do patrimônio, dados congelados dos agentes nem preços de execução. Sem contratação, inferência paga, scheduler ou cotação intradiária presumida |
| DP-26 | Gráfico de preço ao longo do dia, dos dias anteriores e assim por diante, com barras intradiárias yfinance | Pedido explícito de Lucas em 16/10, que aceitou a mudança de foco e a coleta automatizada local no Yahoo. O Yahoo apaga 1 min após ~30 dias (5 min: 60; 1 h: 730), então cada pregão fechado vira arquivo imutável com a melhor resolução ainda disponível; o pregão aberto fica em memória com atraso de ~15 min. Coleta ao abrir a página, pelo botão e a cada 2 min com o pregão no período; sem scheduler. Amplia DP-25 só no gráfico: não vira marca, preço de operação ou input dos agentes; DP-24 continua com preços de referência |

DP-01–DP-06 e DP-08 registram a direção apresentada por Lucas e discutida na
conversa. DP-07 registra sua concordância explícita com os 20% por ativo.
DP-09–DP-15 foram aprovadas explicitamente por Lucas em 14/10/2026, após a
entrega PAPER-03 e a apresentação da tabela de bases do piloto.
DP-16 foi decidida e autorizada explicitamente por Lucas em 14/10/2026.
Ela substitui a apresentação de H2 como frente principal/paralela ativa da DP-08,
preservando a separação de identidades, capital, ledgers e evidências daquela decisão.
O legado é o experimento independente dedicado exclusivamente a PETR4, não o ativo
PETR4 nem toda pesquisa ou auditoria. Mover para Legacy não executa, cancela ou
reconcilia intenções; não afirma ausência de pendências ou encerramento financeiro.
O bloqueio é da aplicação web; runners, CLIs e contratos selados permanecem intactos.
A implementação e o protocolo prospectivo ainda precisam fechar os detalhes abaixo.

## Uso diário pela interface — DP-17

Em 14/10/2026, Lucas pediu que a plataforma deixe de depender de telas de teste
e comandos técnicos para o uso cotidiano. A direção solicitada compreende:

- Home com seletor das carteiras cadastradas, patrimônio, caixa, posições,
  gráficos, evolução e proventos da carteira selecionada.
- Cadastro de carteira com nome, estratégia, capital, início e estado inicial
  visíveis; sua criação deve disponibilizá-la no mesmo catálogo usado pela home.
- Registro de compras/vendas, consulta de ordens pendentes e histórico de
  operações. Ordem proposta ou autorizada é distinta de operação executada.
- Registro histórico com data econômica e instante de cadastro separados,
  origem identificada e revisão rastreável. Um lançamento antigo não fabrica
  decisão, autorização ou execução prospectiva dos agentes.
- Rotina pela interface para atualizar dados, verificar pendências, consultar
  decisões, autorizar operações e conferir resultados, respeitando os atos e
  orçamentos separados. Diagnósticos técnicos ficam acessíveis em contexto.
- Proventos previstos, direitos reconhecidos e pagamentos recebidos distintos;
  recebível não aparece como caixa disponível nem é contado novamente no pagamento.

**Base inicial comum — DP-18:** Lucas confirmou as mesmas posições iniciais,
aproximadamente 20% em PETR4, VALE3, ITUB4, WEGE3 e BBAS3, para as carteiras
simuladas comparadas. DP-10 mantém R$ 100 mil independentes por carteira e DP-15
mantém início efetivo elegível, sem preencher D0 retroativamente. A cesta/base
inicial será comum; depois, agentes podem alterar posições e a referência segue
DP-11. Quantidades, preços, custos, caixa residual, autorizações e sessão efetiva
da entrada ainda exigem definição/qualificação. Não replicar fills históricos
ou converter uma proposta consultiva antiga em ordem de inicialização.

Essa escolha substitui, para a base inicial comparada, a recomendação anterior
de cada estratégia escolher sua primeira alocação de forma independente. A
proposta de exposição máxima de 85% para os agentes é incompatível com a base
comum próxima de 100%; deve ser revisada explicitamente em PAPER-01, preservando
o V5 selado. Não presumir aprovação dos 85%, vender 15% automaticamente ou
alterar a cesta comum para contornar esse conflito.

**Operações externas — DP-19:** Lucas confirmou que quer registrar simulações
e compras/vendas reais realizadas fora da plataforma. Não foi solicitada
integração com corretora nem envio de ordens reais. Carteiras pessoais preservam
seu capital, datas e posições efetivos; a base de R$ 100 mil/20% do piloto não
é imposta a elas. Resultados e gráficos identificam a natureza e o grupo de
comparação. Documentos do piloto prospectivo não autorizam retroagir operações
dos agentes; cadastro histórico pessoal segue contrato próprio rastreável.

DP-17 define o resultado de produto, não declara carteira oficial ativa,
tratamento de eventos qualificado ou autorização de gasto/operação. Reutilizar
ledger, contabilidade, persistência e leitores; a prioridade de implementação
está no [roadmap](ROADMAP.md#uso-diário-pela-interface--dp-17).

## Comportamento esperado da tela inicial

**15/10 — DP-24 / APP-05:** o gestor da carteira é etapa distinta dos pareceres
individuais. A chamada paga e o registro da cesta exigem consentimentos próprios
na interface. A escolha de preços de referência autoriza um modelo de simulação
manual registrado hoje, não fill prospectivo na abertura nem decisão feita no
passado. O desejo de cotação recente do momento fica como complemento de APP-03:
qualificar fonte, atraso, sessão e horário antes de substituir a referência.
Não altera regras prospectivas pendentes em PAPER-01 ou limites do V5 selado.

**Atualização de 14/10 — DP-20/21:** Lucas esclareceu que as duas carteiras novas
são o ponto de partida de uso da aplicação. Autorizou a cesta apresentada: 351
PETR4 a R$ 56,85; 297 VALE3 a R$ 67,16; 402 ITUB4 a R$ 49,68; 393 WEGE3 a
R$ 50,81; 824 BBAS3 a R$ 24,25, em cada carteira, com R$ 177,44 em caixa.
São registros simulados manuais de 14/10 com referência histórica de 13/10,
não negócios reais externos ou decisão retrospectiva dos agentes. A autorização
de custos zero vale para essa entrada; não aprova custos futuros, 85% ou regras
prospectivas pendentes. Buy & Hold mantém DP-11. O próximo uso desejado é pedir
sugestões para a Multiagentes e registrar a movimentação paper ao aprová-la;
essa integração ainda precisa ser implementada/qualificada em APP-05.

1. Selecionar a carteira e identificar estratégia, origem dos dados e última sessão.
2. Ler patrimônio, caixa, exposição e variação do período selecionado.
3. Explorar evolução diária e comparação com outras carteiras.
4. Ver ativos/posições e suas variações.
5. Entender a última decisão, operações e eventuais pendências; abrir evidências
   quando necessário, sem transformar a página inicial em um relatório técnico.

Por pedido de Lucas em 14/10/2026, a atualização manual dos dados da bolsa fica
acessível no cabeçalho compartilhado, a partir de qualquer módulo. O comando
mostra sessão e ativos da execução operacional, prepara os dados de referência
e informa progresso/bloqueios. Inferência dos agentes e atualização financeira
continuam ações próprias, com seus gates/autorização. Não avança sessão, altera
evidência congelada ou promete cotações em tempo real. Refinamento de UX sob
DP-01/04/05/13/16; não altera as bases do piloto.

Lucas esclareceu em 14/10/2026 que parametrização e autorização de orçamento
devem acontecer pela interface, sem depender de linha de comando ou autorização
pelo chat. O Radar oferece revisão das reservas, teto agregado aceitável para a
execução apresentada e consentimento explícito antes de liberar a confirmação
paga. O teto digitado limita a revisão da exposição exata; não é aumento permanente
do limite global e mudanças de reservas exigem nova revisão. Orçamento, inferência
e operação financeira mantêm autorizações distintas (DP-13/16).

Não mostrar zero quando o dado está ausente. Períodos ainda não completados
aparecem como histórico insuficiente; não extrapolar um ano a partir de poucos dias.
Valores históricos indicam a sessão, sem aparência de cotação em tempo real.
Alvo de alocação, proposta e operação executada têm estados distintos.

## Propostas técnicas e decisões ainda abertas

| Tema | Direção proposta / pendência |
|---|---|
| Capital por carteira | DP-10: R$ 100 mil independentes; entrada manual DP-20 registrada, entrada prospectiva continua pendente |
| Buy & Hold 20% | DP-07/11 fecham alvos, ausência de rebalanceamento e proventos em caixa; eventos obrigatórios e saídas excepcionais ainda precisam de regra |
| Outras referências | Definir quais entram no grupo multiativos; não transferir automaticamente os benchmarks single-asset do H2 |
| Gráfico conjunto | Preferência técnica por retorno acumulado ou índice base 100; mostrar patrimônio absoluto na carteira selecionada; definir apresentação por grupos comparáveis |
| Primeiro fill | Definir sessão, preço observado, disponibilidade dos dados e autorização; D0 não autoriza preencher uma abertura passada |
| Execução e custos | Lotes/frações, resíduo de caixa, custos, slippage, liquidação e eventos corporativos precisam de regras comuns e versionadas |
| Rotina diária | DP-13 fecha operação manual e autorização explícita; definir dados, prazos, identidade do operador e recuperação |
| Avaliação científica | Universo, período, métricas e controles devem ser aprovados no protocolo; gráfico comparativo não demonstra superioridade por si só |

A V2 multiativos existente decidiu 100% caixa e zero operações. A decisão de
COMPRA PETR4 pertence ao H2 e segue contrato próprio. Essas evidências históricas
não são ordens de entrada da nova carteira. [Fontes do estado atual](ESTADO_ATUAL.md).

## Como evitar mudança involuntária de foco

Antes de iniciar uma tarefa, o agente deve ler este documento e o roadmap,
identificar a decisão DP e o item de trabalho que a entrega atende, e explicar
o resultado concreto esperado. Infraestrutura necessária deve ter vínculo
explícito com o acompanhamento da carteira, a confiabilidade ou o TCC.

Ao concluir, registrar o que foi entregue, a verificação feita e a pendência
seguinte. Atualizar estado/roadmap quando houver mudança real. Não apresentar
um recurso lateral como se fosse avanço do objetivo central.

Mudar o destino do produto, acrescentar uma frente principal ou contrariar
uma decisão aceita exige discutir o desvio com Lucas antes de executá-lo.
Escolhas rotineiras compatíveis com a direção podem prosseguir normalmente.
Novas ideias ficam no backlog até serem priorizadas; não ganham prioridade
porque o agente as considera interessantes.

Ao mudar uma decisão, acrescentar registro com data, motivo, autor e ID
substituído. Preservar a decisão anterior no histórico; nunca apagar
evidência científica para adequá-la ao novo planejamento.

## Fora do foco imediato

Envio de ordens reais a corretora, robô autônomo de execução, tempo real sem atraso,
intraday em marcas/operações (DP-26 cobre só o gráfico), fine-tuning,
novos provedores, notícias/sentimento, novos ativos e reformulação estética
sem necessidade do fluxo principal. Nenhum desses itens é requisito atual.

## Histórico de decisões

| Data | Registro | Origem |
|---|---|---|
| 13/10/2026 | Versão 1: objetivo, tela inicial, seletor, indicadores, evolução diária, D0 e separação dos experimentos | Direção descrita por Lucas nesta conversa |
| 13/10/2026 | Pesos iniciais de 20% por ativo para a referência multiativos | Concordância explícita de Lucas; detalhes operacionais ainda abertos |
| 13/10/2026 | Documento persistente e leitura obrigatória pelos agentes | Pedido de Lucas para evitar trabalho em direção diferente sem revisão |
| 14/10/2026 | Versão 2: DP-09–DP-15, bases operacionais do piloto aceitas | Lucas respondeu “concordo, pode fazer o prompt” à tabela apresentada após PAPER-03 |
| 14/10/2026 | Versão 3: DP-16 atualiza DP-08 na navegação e prioridade; Legacy somente consulta para PETR4/H2 e backtests anteriores, sem alteração dos estados financeiros | Decisão e autorização explícitas de Lucas para reorganizar a plataforma |
| 14/10/2026 | Versão 4: DP-17 explicita criação de carteiras, registro de operações, proventos e rotina completa pela interface | Direção de uso diário descrita por Lucas; não declara implementação ou ativação |
| 14/10/2026 | DP-18 confirma posições iniciais iguais, próximas de 20% por ativo; DP-19 inclui registro de operações reais externas e simuladas | Respostas explícitas de Lucas às duas perguntas de escopo; proposta de 85% exige revisão, e carteiras pessoais ficam separadas do piloto |
| 14/10/2026 | Versão 5: DP-20 autoriza substituir o cadastro real vazio por Buy & Hold/Multiagentes simuladas com a cesta apresentada; DP-21 explicita sugestões sobre a carteira e registro paper automático após aprovação | Lucas: “só exclui aquela buy hold lá e cria uma nova ... vão ser nosso pontapé inicial ... a gente aceitando a alocação ocorre automático” |
| 15/10/2026 | Versão 6: DP-22, escolha da carteira/dia-alvo na interface e preservação integral do ciclo | Lucas solicitou implementar o seletor operacional e mapear todo o ciclo de uso; não autoriza chamadas pagas durante a implementação |
| 15/10/2026 | Versão 7: DP-23, aprovação do novo frontend após navegar pela prévia | Lucas aprovou o conceito claro e pediu sua aplicação; não altera decisões financeiras, protocolo ou limites de dados |
| 15/10/2026 | Versão 8: DP-24, gestor com quantidades e movimentações parciais; simulação aos preços de referência apresentados | Lucas pediu alocação coordenada e escolheu a opção de preços de referência, ressaltando o desejo futuro de cotação do momento |
| 16/10/2026 | Versão 10: DP-26, acervo intradiário Yahoo para o gráfico de ações; intraday deixa de estar fora do foco apenas nesse uso | Lucas pediu as barras do dia e dos dias anteriores, aprovou a nova DP e a coleta automatizada local sob os termos do Yahoo (“aceito, pode fazer”) |

Essa aprovação não inclui custo de 0,1%, buffer de 2%, limite de exposição de
85%, política de veto, prazo de processamento, rendimento de caixa, fonte ou
modelo de execução. Esses itens continuam pendentes. Não autoriza gasto Gemini,
criação de carteira oficial, ativação ou primeira ordem prospectiva. DP-20,
registrada depois, autoriza separadamente a entrada simulada manual descrita acima.
