# Direção do projeto e decisões de produto

Versão 26 — **16/11/2026**. Decisões registradas a partir da conversa com Lucas.
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
| DP-27 | Base de mercado local e permanente dos cinco ativos, com o máximo de histórico, atualizada de forma incremental ao iniciar a aplicação ou pelo botão "Atualizar"; a marcação diária do patrimônio deixa de depender de análises dos agentes | Pedido e autorização explícitos de Lucas em 16/10. Download automático da B3 autorizado para uso local, sem redistribuição: COTAHIST anuais desde 2000 uma vez e diários dos pregões faltantes. Guardar só as linhas dos cinco ativos com URL, hash, tamanho e instante de aquisição; os ZIPs podem ser descartados. Cada linha preserva OHLCV RAW B3 (marcação), fator/ajuste Yahoo identificado (análise) e o instante de aquisição para auditoria; consultas "as-of" enxergam só sessões até a data da decisão, sem antecipação. Pregão não publicado fica como lacuna explícita; sem scheduler (DP-13). Encerra, para esse uso, a pendência de automatizar a B3 do DATA-01; ativação oficial PAPER-04 continua com seus gates. Direção futura registrada, sem implementação agora: recortes temporais/eventos (ex.: eleições 2022), indicadores e padrões recorrentes por ativo consultáveis pelos agentes, sempre com corte pela data da decisão e tamanho de amostra explícito |
| DP-28 | Página Comparação com gráfico de retorno acumulado em % desde o início comum das carteiras do mesmo grupo, mais o Ibovespa como referência externa coletado na mesma atualização de dados | Decisão de Lucas em 16/10: opção A (retorno acumulado em %, não índice base 100) e Ibovespa incluído. Fecha, para essa página, as pendências "Gráfico conjunto" e "Outras referências". Ibovespa via Yahoo (^BVSP), identificado como referência externa, sem marcar patrimônio nem alimentar agentes; ancorado no último fechamento anterior ao início das carteiras. Carteiras pessoais ficam fora do gráfico do grupo (DP-19). Linguagem neutra: diferença observada não demonstra superioridade (DP-09); o Ibovespa inclui proventos reinvestidos e as carteiras ainda não (APP-04), o que deve ser dito na tela. Em 17/10 Lucas incluiu o CDI (Banco Central, SGS 12), coletado na mesma atualização |
| DP-29 | Códigos antigos da B3 são normalizados para o código atual, com a origem preservada em cada linha | Decisão de Lucas em 17/10 ("mesmo que ITAU4 fosse o antigo, hoje é ITUB4, então traduz"). ITAU4→ITUB4 aplicado após verificar renome limpo: sem pregões sobrepostos e continuidade de preço (+1,97% na troca de 19→20/05/2009). WEGE4 não foi traduzido: negociou ao mesmo tempo que WEGE3 (61 pregões em comum, classes distintas até 31/05/2007); misturar exige decisão própria. Em 17/10 Lucas escolheu a opção B: WEGE4 até 31/05/2007 e WEGE3 desde 01/06/2007 (continuidade 16,10 → 16,70, +3,7%), descartando as linhas pouco líquidas da WEGE3 anteriores à troca e preservando a origem |
| DP-30 | Proventos (APP-04): fonte B3 oficial; JCP creditado líquido de 15% de IR; provento vira caixa só no pagamento, ficando "a receber" entre a data-com e o pagamento | Escolhas de Lucas em 17/10 entre opções apresentadas. Elegibilidade pela posição na data-com; recebível fora do caixa disponível e sem dupla contagem no pagamento. Buy & Hold mantém proventos em caixa (DP-11). Em 17/10 Lucas escolheu a opção A: proventos recebidos passam a ser lançados no livro de operações como entradas idempotentes, para que livro, home e gestor usem o mesmo caixa (substitui, para recebidos, o cálculo só na leitura) |
| DP-31 | Backtest no Laboratório só de regras determinísticas (cesta com ou sem rebalanceamento) sobre a base local; agentes de IA são avaliados apenas de forma prospectiva | Decisão de Lucas em 17/10: backtest de agentes no passado é caro e contaminado (o modelo conhece o desfecho), e um modelo substituto mais fraco tornaria a comparação injusta. O backtest de regras usa preços ajustados (proventos reinvestidos), compara com Ibovespa e CDI no mesmo período e é resultado histórico, não previsão; não altera o piloto nem os ledgers. A visão de "munição" para os agentes (DP-27) entra em fase de pesquisa documental antes de qualquer implementação |
| DP-33 | Operação aprovada executa no primeiro leilão oficial da B3 após a aprovação; cotação atrasada só na prévia; tolerância proporcional à volatilidade e ao tempo; proposta válida até os leilões do pregão-alvo; sem cotação no prompt do gestor | Lucas aprovou em 19/10 as cinco recomendações do [relatório](../reports/Relógio%20de%20dados%20e%20preço%20de%20execução.md). (1) Aprovação antes da pré-abertura executa na abertura oficial do dia; durante o pregão até o corte antes do call de fechamento, no fechamento oficial do dia; depois, na abertura do pregão seguinte; estado "aguardando leilão" até o preço oficial chegar pela atualização DP-27, lançamento idempotente com data do leilão; horários de corte configuráveis por regime (horário de verão dos EUA). (2) A cotação atrasada do Yahoo entra só no código da prévia, como retrato selado (valor, fonte, atraso, horários de cotação e coleta, estado do pregão, hash), nunca na marcação, no preço da operação ou nos prompts — exceção restrita à DP-26. (3) Nova prévia quando a cotação se move além de clamp(3·σ₆₀·√(h/415); 0,5%; 2%), sem nova chamada paga, e alerta de "tese velha" a 3σ desde o fechamento anterior ajustado por proventos. (4) Proposta válida até os leilões do pregão-alvo; expirada, registra custo de oportunidade. (5) Cotação no prompt só com teste pareado pré-registrado e orçamento próprio. Atualiza a DP-24 no preço de registro (antes: fechamento de referência do pregão anterior); cada operação guarda preço de decisão, da prévia, da aprovação e do leilão para medir o implementation shortfall |
| DP-34 | Ciclo diário autônomo da carteira Multiagentes: análise, analistas, gestor e aprovação rodam sozinhos todo pregão, com teto diário de reserva Gemini de US$ 4, aprovação automática salvo alerta de tese velha, tentativas às 09:00, 12:00 e 16:00 (America/Sao_Paulo), aviso por e-mail, servidor pessoal no Railway acessível só pela rede Tailscale de Lucas | Lucas pediu em 20/10 o ciclo completo ("nem todo dia eu vou entrar lá", "rodar fielmente todo dia pouco antes da bolsa abrir… caso não tenha ele tenta de novo 12h e depois 16h") e escolheu: teto diário de reserva US$ 4; aprovação automática exceto com alerta de tese velha (aí espera Lucas); download automático da B3 no servidor do Railway para uso pessoal, sem redistribuição (amplia a DP-27 de "uso local"); aviso por e-mail; acesso via Tailscale. Substitui, para essa rotina, a rotina manual e a autorização explícita da DP-13 e os consentimentos por chamada/ordem da DP-16/DP-21/DP-24, que continuam valendo no uso manual pela interface. Toda autorização automática fica registrada como da rotina (não de Lucas), com teto, horário e motivo; a regra de leilão da DP-33 não muda. Três tentativas sem dados consolidados: dia registrado como sem análise, nada inventado |
| DP-35 | Novas aprovações durante o pregão executam na simulação com preço posterior à aprovação, sem esperar o fechamento | Lucas escolheu explicitamente em 22/10 “Executar durante o pregão, com um preço obtido após a aprovação”. Atualiza DP-33/34: antes do corte da abertura continua OPEN oficial B3; entre os cortes de abertura e fechamento passa a INTRADAY, inclusive nas tentativas automáticas de 12h/16h. Preço simulado = Open da primeira barra negociada e coerente de 1 minuto do Yahoo cujo início seja estritamente posterior à aprovação, da mesma sessão e já completa na coleta; atraso aproximado de 15 min, sem alegar fill real ou preço instantâneo. A fonte de todos os ativos da cesta é selada antes do lançamento atômico/idempotente; faltando preço, espera, sem antecipar abertura nem substituir pelo fechamento. Prazo de coleta: até 30 min após o fim do período contínuo; sem captura válida, registra não execução. Depois do corte final, o próximo OPEN só vale se ainda dentro do alvo. Ordens OPEN/CLOSE já aprovadas mantêm a política gravada. Servidor consulta pendências a cada minuto sem depender do navegador. Amplia DP-26 apenas para esta execução simulada; marcação diária continua RAW B3, e cotações não entram nos prompts do gestor |

**DP-36 — SMA e Bollinger na comparação desde 14/10 (23/10/2026).** Lucas pediu
carteiras simuladas de SMA 50/200 e Bollinger 20/2, sem chamadas de agentes,
usando dados reais e a mesma cesta, caixa, capital independente e grupo das
carteiras iniciadas em 14/10. Histórico anterior serve só ao aquecimento dos
indicadores; reconstruir os sinais desde o fechamento de 14/10, com operações
na abertura oficial B3 da sessão seguinte e registro do instante real da
reconstrução. Cada ativo tem uma parcela independente de 20% do capital inicial;
compra com o saldo dessa parcela quando está zerado, venda integral quando há
sinal de saída, sem shorts/alavancagem nem transferência de caixa entre ativos;
proventos recebidos continuam em caixa. Entrada inicial com custos zero (DP-20);
Lucas escolheu o percentual da última configuração do gestor, fixado na criação
das regras (0,03%, confirmado por GET no servidor em 23/10). Sinais de cruzamento
SMA e rompimento das bandas reutilizam as implementações existentes, com
parâmetros fixos; cada decisão, inclusive manter, conserva os inputs e a fonte.
As decisões usam fechamento B3 × fator Yahoo da versão disponível, congelada
no recibo; a reconstrução não afirma disponibilidade histórica dessa versão do
ajuste. Operações e patrimônio usam RAW B3 e o mesmo livro com proventos.
Rotina avança na atualização de mercado, separada da rotina paga Multiagentes;
dados/preço faltantes bloqueiam, sem substituir por fechamento ou inventar fill.
Equal Weight e Mínima Variância ficam fora deste incremento, dado o horizonte
de um mês e pouco até a entrega do TCC. Curvas podem coincidir com Buy & Hold;
Lucas aceita mantê-las para coletar eventual diferença. Ocultar uma curva depois
não apaga evidências nem omite do relato que a regra não produziu diferença.
Amplia DP-18/28/31 e PAPER-05; os backtests/H2 Legacy continuam preservados.

**DP-37 — extensão exploratória limitada, 12/11/2026:** Lucas autorizou por voz
implementar e, sob os guardrails financeiros, executar primeiro duas semanas
históricas da carteira multiativos atual com Gemini 3.8 Flash. Reabre a DP-31
somente para este replay produzido agora, sem substituir o acompanhamento diário,
retomar H2 ou afirmar ausência de contaminação. Período escolhido antes de medir
retorno: 06–17/04/2026, dez pregões após março, com aquecimento anterior apenas
para indicadores. Reusar comitês, risco, gestor da carteira, validação e livro;
identidade/SQLite/artefatos próprios, sem alterar piloto ou evidências seladas.
A DP-34 autoriza US$ 4/dia apenas para a rotina diária: não é um teto agregado
para dez sessões executadas agora. Reserva do replay US$ 34,77504; inferência
foi autorizada por Lucas com teto agregado de US$ 34,78 ("autorizo, pode fazer")
após o preflight. [Contrato, estado e comandos](REPLAY_MULTIATIVOS.md).

**13/11 — segunda janela da DP-37:** depois da investigação de blocos de queda,
Lucas escolheu e autorizou 20/04–05/05/2026: "gostei da 20 de abril a 5 de maios.
podemos fazer, pede la pra ele". Novo ensaio independente com o mesmo Gemini,
fluxo, capital, regras e custos; teto agregado próprio de até US$ 34,78. A seleção
foi feita pela queda observada, portanto é estresse retrospectivo exploratório.
Não autoriza calibrar vendas, reparar prompts/gates, comparar modelos ou alterar
o ensaio anterior. Proventos respeitam direito na data-com e caixa no pagamento.

**13/11 — campanha contínua da DP-37:** Lucas autorizou uma nova trajetória
06/04–12/11/2026 (153 pregões), sem juntar/resetar os dois pilotos. Conjunto final
confirmado: Multiagentes, Buy & Hold, SMA 50/200, Bollinger 20/2, Equal Weight e
Mínima Variância. Primeiro concluir as cinco referências; depois inferência
Gemini 3.8 Flash contínua; frontend de exploração após dados/resultados. Seis
capitais independentes R$ 100 mil e mesma cesta DP-20; custos posteriores 0,03%,
RAW B3, abertura seguinte e proventos no pagamento. Buy & Hold/regras não
reinvestem os proventos; o gestor mantém o fluxo atual, recebendo todo o caixa
disponível do livro e podendo realocá-lo somente sob seus sinais/gates.
Equal/Mínima reutilizam as definições multiativos existentes: 63 pregões entre
rebalanceamentos, 252 retornos na Mínima, long-only, parâmetros/otimizador sem
calibração pelo resultado. DP-36 da aplicação atual (23/10) fornece as regras
SMA/Bollinger, copiadas e verificadas por hash na worktree histórica da campanha.
Autorizado ajuste exclusivamente operacional: até duas tentativas de transporte
por chamada lógica, todas preservadas, uma única resposta aceita, schemas/quórum
inalterados. Teto **único US$ 34,78** para toda esta campanha, incluindo retries,
incerteza e chamadas em voo; reserva durável antes de cada HTTP e nenhum reset
por lote/retomada. Não altera outubro, pilotos/H2, produção ou deploy.
[Inventário, origem e convenções](../reports/inventario_replay_continuo_2026-11-13.md).

**14/11 — consulta do replay no servidor pessoal:** Lucas autorizou continuar
o plano de disponibilização da DP-37. Reutilizar o pacote já concluído, copiá-lo
para pasta própria do volume e oferecer consulta pelo Laboratório, com os mesmos
controles de origem e Tailscale. Não inclui nova inferência, mudança de estratégia
ou integração dos livros retrospectivos às carteiras diárias. Código segue pelo
original e pela fork que alimenta o Railway; dados privados ficam fora do Git.

**15/11 — diagnóstico dos 5 achados do replay v1 e plano Abril–Novembro v2 (`DP-37` / `REPLAY-01` → `REPLAY-02`):** após a auditoria do replay `06/04–12/11/2026`, Lucas pediu documentar os 5 achados empíricos do `v1` (trava de caixa/rebalanceamento em `MANTER`, compra de topo/venda de fundo com RSI médio `63,17` vs `35,07`, veto de volatilidade bloqueando `VENDA` em 25 casos, concentração até `77,49%` / compras residuais de 3 ações e homogeneidade `83,01%` `5x0` do comitê) e estruturar o plano do **Replay Abril–Novembro v2 (`REPLAY-02`)** focado nos 4 gargalos, **mantendo o `v1` preservado lado a lado** para mostrar a evolução arquitetural no TCC. A execução paga do `v2` permanece condicionada à qualificação offline do adaptador v2 e autorização específica do orçamento. [Diagnóstico e plano v2](../reports/auditoria_posicoes_replay_2026-04_2026-11.md).

**16/11 — campanha exploratória v3 (`DP-37` / `REPLAY-03`):** após o diagnóstico do *cash drag* e *timing* residual do `v2`, Lucas autorizou implementar e executar a campanha **Abril–Novembro v3 (`REPLAY-03`, `scripts/continuous_replay_v3.py`)** sob os **4 Pilares** (5 lentes especialistas únicas + guardas de extremo; memória de posição, *Core Floor* 8%, venda escalonada 45% e anti-*whipsaw* 8 pregões; `Trim-on-Strength`; `Dip-Rebalance` sob *cash drag* > 25%), **mantendo `v1` e `v2` integralmente preservados** para comparação controlada de três gerações no TCC (`R$ 82.178,71` → `R$ 85.743,57` → `R$ 100.067,36`). [Relatório v3](../reports/replay_continuo_v3_2026-04_2026-11.md).

**15/11 — reorganização da navegação para o TCC (atualiza DP-23 / DP-37):** Lucas
esclareceu que a campanha contínua de abril a novembro (`DP-37` / `REPLAY-01`,
153 pregões e seis carteiras) é o foco empírico principal do TCC e aprovou:
(1) promover **Replay abril–novembro** (`/laboratory/replay/`) a item próprio na
barra principal (`Carteira`, `Operações`, `Agentes`, `Comparação`,
`Replay abril–novembro`), além de atalhos diretos em `/comparison` e `/laboratory`;
(2) limpar atalhos intermediários obsoletos ou sintéticos da navegação ativa
(`/portfolio` e seus cinco sub-links sintéticos no Laboratório, `/data`, `/market`,
`/legacy/backtests` e o banner demonstrativo `/?demo=1` no Laboratório), mantendo
as rotas HTTP e arquivos existentes preservados para compatibilidade e auditoria;
(3) priorizar `/logs` (`Atividade e registros`) e `/agents` (`Voto por agente`) em
Auditoria e manter em Legacy apenas o acervo histórico (`/legacy`, `/legacy/paper`,
`/legacy/h2`).

### Correspondência dos identificadores históricos

A consolidação de 14/11 preserva as decisões de ambos os ramos e dá uma referência
inequívoca a cada assunto. O número DP-35 foi usado independentemente nos dois
ramos; a correspondência abaixo resolve a documentação ativa, sem mudar a decisão.

| Referência atual | Assunto e autorização | Rótulo histórico preservado |
|---|---|---|
| DP-35 | Execução simulada intradiária, aprovada em 22/10 | DP-35 na aplicação e nas ordens de outubro |
| DP-36 | SMA/Bollinger na comparação diária, aprovadas em 23/10 | DP-36 na aplicação e como fonte das regras do replay |
| DP-37 | Replay retrospectivo exploratório, autorizado em 12/11 e ampliado em 13/11 | DP-35 / REPLAY-01; DP-35/36 quando a campanha também cita a fonte SMA/Bollinger |

**Alias documental: DP35-replay → DP-37.** Scripts, relatórios históricos,
manifests, recibos, ordens, hashes e evidências mantêm os identificadores com que
foram produzidos; não devem ser regravados para acompanhar esta correspondência.
A DP-37 não substitui a política intradiária da DP-35 nem transforma o replay em
acompanhamento prospectivo. O replay mantém sua execução OPEN RAW B3 e suas
limitações declaradas, independentemente da rotina diária.

Em 14/11 Lucas autorizou integrar as melhorias do Matheus já preservadas na fork,
as decisões operacionais validadas e o código/relato do replay. A consolidação
preserva os dois históricos, sem refazer simulações; publicação e transferência
dos dados permanecem etapas próprias. [Estado e verificação](ESTADO_ATUAL.md).

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

**Universo da Multiagentes — esclarecimento DP-07/DP-24/DP-34, 22/10:** Lucas
explicitou que vender toda a posição não exclui a ação das próximas análises:
ela pode voltar a ser candidata a compra. O universo continua PETR4, VALE3,
ITUB4, WEGE3 e BBAS3, independentemente das quantidades atuais, inclusive quando
a carteira estiver inteiramente em caixa. O gestor recebe as posições reais e
considera quantidade zero para ativos ausentes; analisar não obriga comprar nem manter
20% após a entrada inicial. Análises já registradas preservam seu universo.

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
| Outras referências | DP-28 (16–17/10): Ibovespa e CDI entram na Comparação como referências externas; demais ainda a definir. Definir quais entram no grupo multiativos; não transferir automaticamente os benchmarks single-asset do H2 |
| Gráfico conjunto | DP-28 (16/10): retorno acumulado em % escolhido para a Comparação. Preferência técnica por retorno acumulado ou índice base 100; mostrar patrimônio absoluto na carteira selecionada; definir apresentação por grupos comparáveis |
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

As versões 18–20 foram numeradas em ramos diferentes. As entradas abaixo
preservam seus rótulos e datas originais; DP-35 nas entradas de replay de
12–13/11 corresponde à DP-37 pela tabela acima.

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
| 16/10/2026 | Versão 11: DP-27, base de mercado local incremental desde 2000, download automático da B3 para uso local, marcação desacoplada das análises e visão futura de munição histórica para os agentes | Lucas respondeu “sim” às três perguntas: download automático da B3, descarte dos ZIPs com hash preservado e registro da visão sem implementação imediata |
| 16/10/2026 | Versão 12: DP-28, Comparação por retorno acumulado em % com Ibovespa como referência externa | Lucas: “vai de A”, “pode fazer, já extrai o ibovespa também da nossa atualização de dados” |
| 17/10/2026 | Versão 13: CDI na DP-28; DP-29 normaliza ITAU4→ITUB4; DP-30 define fonte, JCP e momento de caixa dos proventos | Lucas: “concordo em mostrar proventos”, “normalizaria o código antigo para o usado atual” e respostas às três perguntas de proventos |
| 17/10/2026 | Versão 14: DP-29 opção B para WEG; DP-31 backtest só de regras e pesquisa da munição dos agentes | Lucas: “vamos de B”, “só o primeiro por enquanto… o modelo já conhece e é caro”, “vamos dar uma investigada… quais tópicos podemos rastrear” |
| 17/10/2026 | Versão 15: DP-30 opção A, proventos recebidos lançados no livro | Lucas: “faremos a A” após a explicação de A (lançar no livro) e B (aviso na prévia) |
| 19/10/2026 | Versão 16: DP-33, execução no próximo leilão oficial, cotação atrasada só na prévia, tolerância por volatilidade, validade por pregão | Lucas: “eu aprovo, acredito que possa ser uma boa sim”, sobre as cinco recomendações do relatório de relógio de dados e preço de execução |
| 20/10/2026 | Versão 17: DP-34, ciclo diário autônomo (teto US$ 4/dia, aprovação automática salvo alerta, 09:00/12:00/16:00, e-mail, Railway + Tailscale) | Lucas: "eu queria o ciclo completo, pq nem todo dia eu vou entrar la"; respostas às perguntas de teto, aprovação, B3 na nuvem e avisos |
| 22/10/2026 | Versão 18: explicita o universo fixo dos cinco ativos mesmo após venda total | Lucas observou que sair de VALE3 não elimina a possibilidade de recomprar em outra sessão |
| 22/10/2026 | Versão 19: DP-35, execução simulada intradiária com barra posterior à aprovação | Escolha explícita de Lucas da modalidade “Executar durante o pregão”, após discutir a exposição adicional de esperar o fechamento |
| 23/10/2026 | Versão 20: DP-36, SMA 50/200 e Bollinger 20/2 desde a mesma cesta de 14/10 | Lucas aceitou curvas iguais ao Buy & Hold: “o importante é estar lá para caso a gente consiga coletar uma informação diferente”; custo igual à última configuração dos agentes, fixado na criação |
| 12/11/2026 | Versão 18: DP-35, replay exploratório multiativos de duas semanas | Autorização por voz de Lucas, encaminhada nesta tarefa; menor adaptação do fluxo atual, execução condicionada ao orçamento agregado |
| 13/11/2026 | Versão 19: segunda janela DP-35, 20/04–05/05, autorizada com teto US$ 34,78 | Lucas escolheu a janela A após a triagem offline e pediu sua execução; mesmos componentes/regras, identidade e capital independentes |
| 23/10/2026 | Versão 20 da aplicação atual: DP-36, carteiras SMA/Bollinger na comparação | Registro existente no checkout principal, preservado e identificado por fonte; não substitui os snapshots dos pilotos |
| 13/11/2026 | Versão 21: campanha contínua DP-35 com seis carteiras, referências antes da inferência, frontend depois | Lucas confirmou Equal Weight e Mínima Variância além de SMA/Bollinger/B&H/Multiagentes e autorizou execução/reparo operacional sob teto agregado US$ 34,78 |
| 14/11/2026 | Versão 22: consolida os ramos e identifica o replay como DP-37, com alias dos rótulos históricos | Lucas autorizou preservar melhorias do Matheus e decisões da fork; correspondência documental sem regravar evidências ou alterar políticas |
| 14/11/2026 | Versão 23: consulta do replay no servidor sob DP-37 | Lucas pediu continuar o plano de transferência verificada e acesso pelo Laboratório, preservando a operação diária e sem novas inferências |
| 15/11/2026 | Versão 24: reorganização da navegação para o TCC (DP-23 / DP-37) | Lucas indicou o replay abril–novembro como ponto central do TCC e aprovou item próprio na barra principal e limpeza de páginas sintéticas/redundantes da navegação ativa |
| 15/11/2026 | Versão 25: campanha exploratória v2 (`REPLAY-02`, DP-37 / regras DP-36) concluída e comparada ao `v1` | Lucas autorizou execução paga sob teto US$ 34,78 após qualificação offline das 4 correções estruturais (`Trim-to-Fund`, cap 30% + mínimo R$ 2.000, R7 assimétrico e comitê 2+2+1); `v1` preservado integralmente |
| 16/11/2026 | Versão 26: campanha exploratória v3 (`REPLAY-03`, DP-37 / regras DP-36) concluída e comparada a `v1` e `v2` | Lucas autorizou execução paga sob teto US$ 34,78 após qualificação offline dos 4 Pilares (5 lentes únicas + guardas de extremo, memória de posição / Core Floor 8% / venda escalonada 45% / anti-whipsaw 8d, Trim-on-Strength e Dip-Rebalance); `v1` e `v2` preservados integralmente |

**Nota histórica das bases DP-09–DP-15:** o parágrafo abaixo preserva os limites
da aprovação inicial. As autorizações posteriores, inclusive DP-20 e DP-33–DP-37,
estão registradas individualmente acima.

Essa aprovação não inclui custo de 0,1%, buffer de 2%, limite de exposição de
85%, política de veto, prazo de processamento, rendimento de caixa, fonte ou
modelo de execução. Esses itens continuam pendentes. Não autoriza gasto Gemini,
criação de carteira oficial, ativação ou primeira ordem prospectiva. DP-20,
registrada depois, autoriza separadamente a entrada simulada manual descrita acima.
