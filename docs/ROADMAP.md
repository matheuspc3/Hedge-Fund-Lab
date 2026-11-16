# Roadmap do Hedge-Fund-Lab

Atualizado em **16/11/2026**. Plano de trabalho a partir da V7.6.5.
Este é o planejamento ativo. Especificações científicas, aprovações e autorizações
continuam em seus documentos próprios; um checkbox aqui não as substitui.

Ler primeiro a [direção do projeto e decisões aceitas](DIRECAO_DO_PROJETO.md).
Ela define o destino do produto; este roadmap define a ordem para chegar lá.

[Início](../INICIO.md) · [Estado atual](ESTADO_ATUAL.md) ·
[Documentação e evidências](README.md)

## Objetivo e ponto de partida

**16/11 — dados v2 no Railway, DP-37 / REPLAY-02:** deploy `b29aecf`
confirmado em SUCCESS. Pacote v2 instalado atomicamente no volume em
`data/replays/april-november-2026-flash-v2/`, com 12 arquivos conferidos pelo
manifesto e idempotência PASS; todos os 14 arquivos da v1 preservados.
O código implantado ainda atende somente a v1. Ajuste local do importador
(`--version v2`) e das rotas/atalhos v1/v2 qualificado pelos checks existentes.
Próximo passo: publicar esse ajuste de código e conferir a consulta v2 no deploy;
a transferência dos dados já está concluída, sem novas inferências.

**REPLAY-02 / DP-37 (regras DP-36) — campanha contínua v2 concluída (15/11):** execução real autorizada por Lucas em `scripts/continuous_replay_v2.py` (`HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2`), 06/04–12/11/2026, 153 pregões com 5 referências pré-calculadas (paridade exata com o `v1`, `sha256` `f3225f02...`) e inferência contínua das 18:33 às 23:39 (São Paulo). **918/918 estados diários reconciliados** (`152` pregões `COMPLETED` + `1` lacuna *fail-closed* em `2026-06-26` por `WinError 10054` na chamada de risco de `BBAS3` após `4/5` votos técnicos `VENDA`, preservando a posição). **Multiagentes v2** encerrou em **R$ 85.743,57 (-14,2564%)**, avanço de **+R$ 3.564,86 (+3,5649 p.p.)** sobre o `v1` (R$ 82.178,71), com corte de 55,8% no giro (`38` vs `86` operações) e custos (`R$ 119,87` vs `R$ 184,40`), ainda abaixo do `Buy & Hold` (`-R$ 3.047,54`) e da `Bollinger 20/2` (`R$ 104.887,05`, `+4,8870%`). Os 4 gargalos operaram conforme projetado: `2` `Trim-to-Fund` em `PETR4` (`+R$ 1.812,50` PnL vs `-R$ 1.783,77` no `v1`), `0` compras `< R$ 2.000`, `29,98%` teto máximo em proposta `BUY` (`32,23%` por deriva), `2` saídas sob veto `R7` (`ITUB4` `26.491,50` e `BBAS3` `5.712,30`), e queda da unanimidade `5-0` de `83,01%` para `15,13%`; permanece o *cash drag* estrutural (`24,69%` média, `45,86%` no fim) sob teto de 30% em universo de 5 ativos. Orçamento PASS: `4.702` chamadas lógicas (`4.701` com trace + `1` erro de transporte em `2026-06-26`), `4.711` tentativas físicas (`9` retries), exposição **US$ 10,03082025** (`US$ 8,92490025` conhecido + `US$ 1,105920` reservado) abaixo do teto `US$ 34,78`. `v1` preservado (`explorer.json` `88c3a0e1...`, `calls.json` `b5ef9585...`). [Relatório v2](../reports/replay_continuo_v2_2026-04_2026-11.md) · [Pacote selado v2](../output/replay-continuo-v2-20261115/manifest.json) · [Comparativo JSON](../output/auditoria-replay-v2/comparacao_v1_v2.json). Próximo passo: incorporar o comparativo `v1` vs `v2` à monografia (`TCC-02/03`).

**15/11 — exploração dos resultados e plano Abril–Novembro v2, DP-37 / REPLAY-01 → REPLAY-02:** auditoria de posições, cobertura e atribuição concluída com os **5 achados empíricos do replay v1** documentados e verificados por script: (1) trava de caixa/rebalanceamento em `MANTER` (`VALE3` 94 pregões zerada com 14 `COMPRA` ignoradas; `ITUB4` 27 `COMPRA` seguidas ignoradas); (2) compra no topo e venda no fundo em 4/5 ativos (`RSI` médio `63,17` em `COMPRA` vs `35,07` em `VENDA`); (3) veto de volatilidade `HARD_ASSET_VOLATILITY_RULE` bloqueando `VENDA` em 25 pares ativo/pregão; (4) concentração extrema (101/153 pregões com apenas 2 ativos $\ge 2\%$, pico de `77,49%` em `VALE3`) e compras de "poeira" (`3` ações em `BBAS3`); (5) homogeneidade do comitê (`83,01%` de unanimidade `5x0`). Estruturado o **Plano de Melhoria para o Replay Abril–Novembro v2 (`REPLAY-02`)** focado nos 4 gargalos (`Trim-to-Fund`, teto de concentração `30%` + lote mínimo `R$ 2.000`, assimetria de risco `R7` liberando `SELL` sob veto e diversidade Tendência vs Reversão no comitê), mantendo o `v1` 100% preservado para comparação direta no TCC. [Relatório dos 5 achados e plano v2](../reports/auditoria_posicoes_replay_2026-04_2026-11.md). Próximo passo: implementar e qualificar offline o adaptador `v2` antes de preflight/execução paga.

**15/11 — reorganização da navegação para o TCC, DP-23 / DP-37:** **Replay abril–novembro**
(`/laboratory/replay/`) promovido a item próprio na barra principal de navegação
(`Carteira`, `Operações`, `Agentes`, `Comparação`, `Replay abril–novembro`), com
atalhos diretos também em `/comparison` e `/laboratory`. Removidos da navegação
ativa os sub-links sintéticos de `/portfolio`, o bloco demonstrativo `/?demo=1`
ao abrir `/laboratory`, e os atalhos redundantes `/data`, `/market` e
`/legacy/backtests`, mantendo as rotas HTTP e arquivos intactos para
compatibilidade e testes de preservação. Auditoria passa a destacar `/logs` e
`/agents`; Legacy concentra `/legacy`, `/legacy/paper` e `/legacy/h2`. Checkout
local alinhado à `main` (`b673e55`). Verificação: `check_replay_server.py` PASS,
`node --check` PASS e **141 testes aprovados** (1 skip).

**14/11 — disponibilização da consulta, DP-37 / REPLAY-01:** acesso
`/laboratory/replay/` pelo Laboratório e importador do pacote selado implementados.
Dados transferidos pelo Tailscale, com conferência de hashes no volume e sem
alterar o livro diário. Checks de importação/rotas e regressão de 133 testes
aprovados (um skip opcional); navegador local e download CSV verificados.
O aceite da publicação é abrir a mesma consulta no deploy, após sincronizar o
código, e confirmar persistência dos arquivos e isolamento das carteiras.
[Procedimento](REPLAY_MULTIATIVOS.md#consulta-no-servidor-pessoal).
Depois: explorar resultados e registrar análises descritivas no TCC, sem novas
inferências ou alterações estratégicas nesta entrega.

**14/11 — integração autorizada, DP-35/36/37 / REPLAY-01:** Lucas aprovou
preservar as melhorias do Matheus já incorporadas à fork, o universo fixo dos
cinco ativos, SMA/Bollinger com seus controles e a execução intradiária simulada.
O código e os relatos do replay são integrados em worktree separada, sem refazer
as simulações nem alterar a revisão histórica paga. A correspondência documental
mantém DP-35 para intradiário, DP-36 para regras e DP-37 para replay;
[aliases históricos](DIRECAO_DO_PROJETO.md#correspondência-dos-identificadores-históricos).
Verificação final integrada: **133 testes aprovados e um ignorado**, em 32 s.
Os 69 arquivos existentes de lógica do dashboard são idênticos à versão da fork;
o HTML do replay é adicional. A reconstrução do explorador reproduziu exatamente
os bytes do HTML, chamadas e inicializador originais, sem nova inferência.
Nenhum deploy ou envio de dados. Próximo passo: versionar a integração e preparar
a publicação/transferência separada, preservando os resultados já concluídos.


**Registro anterior de 14/11 — commit do replay e revisão Railway/original:** Lucas
pediu guardar o trabalho no repositório do Matheus e examinar as alterações que
existem na fork implantada antes de incorporá-las. Naquele momento, a
transferência/deploy ficou suspensa; depois Lucas autorizou a integração acima. [Comparação das fontes e avaliação por conjunto](../reports/revisao_railway_vs_matheus_2026-11-14.md),
incluindo a colisão documental do ID DP-35 agora resolvida pela correspondência
com DP-37; a comparação original permanece como evidência da revisão.


**REPLAY-01 / DP-37 (regras DP-36) — campanha contínua concluída (13/11):** seis carteiras,
06/04–12/11/2026, 153 pregões sem reset. Referências concluídas antes da inferência;
Multiagentes terminou às 22:28 (São Paulo), inclusive durante a interrupção do
Codex, sem nova instância. Os 918 estados diários passaram pela reconciliação.
Multiagentes: R$ 82.178,71 (-17,8213%); Buy & Hold: R$ 88.791,11 (-11,2089%).
Bollinger teve o maior patrimônio nesta trajetória: R$ 104.887,05 (+4,8870%).
Resultado descritivo e retrospectivo, sem evidência de superioridade.

4703 chamadas lógicas, 4709 tentativas físicas, seis retries recuperados e nenhuma
lacuna diária. Uso conhecido estimado US$ 7,44444225 mais reserva incerta
US$ 0,663552: exposição US$ 8,10799425, sob o teto único US$ 34,78.
Preservação PASS: 1069 arquivos anteriores, 157 diagnósticos e 76 fontes seladas.
Reparos pré-pagos de componentes JCP e escala numérica SLSQP documentados;
os livros e marcas diagnósticos permanecem imutáveis, sem retuning por retorno.
Produção Railway consultada apenas em leitura; outubro, H2 e pilotos separados.

Explorador local entregue com comparação das seis curvas, posições, decisões,
operações, proventos, chamadas e CSV/JSON. Verificado em 1280 e 390 px, sem erros
de execução; sem deploy. [Resultado e limites](../reports/replay_continuo_2026-04_2026-11.md)
· [Como abrir e verificar](REPLAY_MULTIATIVOS.md#explorador-local-e-entrega-final)
· [Inventário](../reports/inventario_replay_continuo_2026-11-13.md).
Próximo passo: explorar a trajetória e incorporar resultados negativos e limites
no TCC; uma nova campanha requer escopo próprio.

**REPLAY-01 / DP-37 — seleção de janela de queda (13/11):** investigação offline
concluída, 130 blocos móveis examinados e três candidatos sem pregões-alvo
sobrepostos: 20/04–05/05, 26/05–09/06 e 04–17/08/2026. Recomendada a primeira
para Lucas avaliar; posteriormente ele escolheu e autorizou o bloco 20/04–05/05.
Retornos da cesta com direitos líquidos: −7,20%, −4,73%, −6,08%; 150 snapshots
técnicos anteriores às decisões verificados, cobertura completa e nenhum split.
A segunda execução terminou: dez marcações, oito análises completas, duas lacunas
de conexão (23 e 30/04), nove operações. Multiagentes R$ 92.668,80 (−7,3312%)
versus Buy & Hold R$ 92.800,14 (−7,19986%): diferença −R$ 131,34. Houve VENDA
e realocação sem alterar regras, mas sem benefício neste bloco. Reconciliação
real/proventos PASS; recebíveis R$ 252,54 / R$ 252,49 fora do caixa. Uso conhecido
estimado US$ 0,4645395; até US$ 0,5751315 com respostas incertas, dentro do teto
próprio US$ 34,78 em todas as retomadas. Primeiro replay preservado (528 hashes).
Raiz `data/cache/historical-replay/april-may-2026-flash/`; adaptador só de datas,
sem editar o runner congelado. Próximo passo: avaliar a evidência no TCC, sem
ampliação automática. [Resultado](../reports/replay_multiasset_2026-04-20_2026-05-05.md) ·
[Triagem das janelas](../reports/janelas_queda_multiativos_2026-11-13.md).

**Extensão pontual REPLAY-01 / DP-37 (12/11):** runner isolado da carteira
multiativos atual, 06–17/04/2026, dez sessões, implementado e validado offline.
Entrega esperada: decisões/operações/patrimônio versus Buy & Hold com a mesma
base, custos e proveniência, mantendo o acompanhamento diário como objetivo.
Execução Gemini real concluída: dez pregões marcados, sete análises completas,
três sem parecer final por conexão interrompida e uma compra. Teto autorizado
US$ 34,78; uso conhecido estimado US$ 0,4650735, até US$ 0,6309615 incluindo
as respostas incertas. Multiagentes R$ 102.503,49 versus Buy & Hold R$ 102.498,88;
diferença R$ 4,61 sem alegação de superioridade. Check real PASS.
[Resultado e evidências](../reports/replay_multiasset_2026-04.md) ·
[Contrato e verificação](REPLAY_MULTIATIVOS.md).
Não reabre H2, não altera ledgers nem promove este ensaio a evidência prospectiva.

Acompanhar carteiras simuladas ao longo dos pregões: decisões rastreáveis,
preços com origem, autorizações válidas, operações paper determinísticas,
caixa, posições, liquidação, patrimônio e reconciliação. O TCC deve explicar
o que foi implementado, o que foi observado e o que ainda não foi demonstrado.

**Experiência combinada:** tela inicial de carteira com seletor de estratégia,
patrimônio, variações em R$/%, posições e evolução diária comparativa.
**D0 de referência: 13/10/2026.** A referência multiativos tem pesos iniciais
aceitos de **20% em cada um dos cinco ativos**. Detalhes de entrada e manutenção
continuam em PAPER-01; nenhuma posição ou execução é criada por esta decisão.

**Base histórica de 16/10:** V7.6.5 `LEDGER_QUALIFIED_OFFLINE`, com motor financeiro V5
reutilizado, SQLite temporário, eventos, replay, contabilidade, D+2 e histórico
sintético. Naquela qualificação, o dashboard lia uma exportação verificada e não
havia carteira oficial multiativos ativa, ingestão diária ou execução habilitada.
As entregas posteriores da aplicação e do Railway são registradas por data abaixo.
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
DP-27 (16/10) autorizou download automático da B3 para a base local de uso próprio; a ativação oficial continua com seus gates.
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

**SMA/Bollinger no comparativo, 23/10 — DP-36, PAPER-05:** implementado e publicado
em `dashboard/rule_portfolios.py`: duas carteiras independentes com a cesta de
14/10, regra determinística, sinais congelados no fechamento e execução OPEN
B3 seguinte, sem IA. Parcelas de capital por ativo, custos fixados na criação,
operações/sinais/manter persistidos no mesmo SQLite com recuperação idempotente;
rotina de atualização de mercado, home, operações, seletor e comparação integrados.
Carteiras de regra excluídas da seleção/execução dos agentes. 130 testes passaram
(um optativo ignorado); prévia isolada com dados reais até 20/10 e comparação
desktop/celular verificadas. A base local não tem os dados necessários desde
21/10 e mostra atraso explicitamente. **Servidor atualizado e carteiras criadas:**
Lucas confirmou o deploy específico após o bloqueio inicial da revisão automática.
Deploy `38c9ee72-2541-4ade-b28a-613f0b8dee46` SUCCESS, fonte fixada em `2baa6c3`,
no ambiente `tcc` do projeto Centauro ERP. Backup íntegro, taxa de 0,03%, duas
carteiras com 7 decisões/7 sessões conferidas desde 14/10; nenhuma operação além
da cesta inicial até 22/10, por isso coincidem com Buy & Hold. GETs e Chrome
confirmaram as quatro carteiras, curva, tabela e seletor; repetir inicialização/
processamento não alterou revisões. Carteiras e hashes das três ordens anteriores
preservados. Dados necessários de 23/10 ainda ausentes: bloqueio explícito, sem
inventar execução. Próximo passo: acompanhar a chegada da base B3 de 23/10 e
as próximas sessões. Não copiar o SQLite antigo do PC sobre o volume da nuvem.

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
| 3 / APP-03 | **Parcial: patrimônio B3 e explorador histórico Yahoo entregues** | Home: evolução pelo mesmo ledger/RAW B3; abaixo das posições, histórico Yahoo máximo, ativos/períodos editáveis e variação por arraste (DP-25), barras intradiárias do dia e dos pregões anteriores em acervo local (DP-26), sem alimentar marcas/ordens. Estimativa atual separada do fechamento histórico; lacunas explícitas. Pendentes cobertura contínua de marcas, comparação e integração prospectiva DATA-01; sem preço ao vivo/proventos; home com variações por período, alocação e marcadores de operações (16/10); base local B3 desde 2000 com atualização incremental e marcação desacoplada das análises (DP-27, 16/10) |
| 4 / APP-04 | Acompanhar dividendos/JCP e eventos | **Entregue em 17/10 (DP-30):** fonte B3, JCP líquido, caixa no pagamento; ver parágrafo "Proventos, 17/10". Elegibilidade/quantidade, ex-date, pagamento, origem e estado previsto/reconhecido/recebido; direitos e caixa sem dupla contagem; histórico recalculado de forma rastreável. Depende das regras e do tratamento de eventos de PAPER-01 |
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

**Home, 16/10 — DP-01/03/04/05/13/21, APP-03/05:** a home mostra patrimônio estimado
com seletor de período (Dia, 5 dias, Mês, Ano, 12 meses, Desde o início), caixa
econômico e investido em ações, em % do patrimônio. Períodos usam só fechamentos
disponíveis; âncora anterior ao início ou sem fechamento vira histórico insuficiente,
nunca zero. "Rotina do dia" traz último fechamento, pregões pendentes, policy
Buy & Hold (sem rebalanceamento, proventos em caixa — DP-11), última proposta do
gestor com link "Revisar proposta" e operações da sessão marcadas como gestor ou
manual. Gráfico marca dias com operações; "Suas posições" tem alocação e a marca de
20% só no grupo-piloto (DP-07/18). Comparação neutra com carteiras do mesmo grupo
só com mesma âncora e fechamentos finais; nunca soma carteiras. Somente leitura.
Verificação e limites no estado atual.

**Base de mercado, 16/10 — DP-27, APP-03/DATA-01:** `dashboard/market_base_api.py` mantém a base local permanente dos cinco ativos em `data/platform/market-base-v1/b3/`, com um JSON selado e imutável por arquivo COTAHIST da B3 (URL, SHA-256, bytes, instante de aquisição), guardando só as linhas dos cinco ativos. Por sessão ficam OHLC, preço médio, quantidade, negócios e volume financeiro RAW; o ajuste Yahoo entra só na série de análise. Consultas "as-of" enxergam apenas sessões até a data da decisão. A atualização é incremental (anuais de 2000 ao último ano; diários quando faltam poucas sessões), roda ao iniciar a aplicação (`HFL_MARKET_BASE_AUTOUPDATE=0` desativa) e pelo botão "Atualizar dados da bolsa"; 404 significa "B3 ainda não publicou". O cabeçalho deixou de preparar a execução do Radar e mostra cobertura por ativo, último pregão fechado e progresso; "Rotina do dia" ganha "Atualizar dados" com pregões pendentes. Marcas da home usam a base desde a data de início da carteira; divergência com referências do Radar vira lacuna, nunca "último vence". Achado: a B3 responde 403 ao user-agent padrão do Python, então a base envia "HedgeFundLab/1.0 (uso local; TCC)". O módulo selado `src/pipeline/b3_official.py`, usado pela preparação de análise do Radar, mantém o agente padrão; novas sessões do Radar tendem a falhar com 403. Não alterado; a decidir com Lucas. (Resolvido em 17/10 sem editar o módulo selado: opener de user-agent só para a B3 no servidor.)

**Comparação, 16/10 — DP-28, APP-03/UX-M5:** a página Comparação (`/comparison`) deixa de mostrar "aguardando preços" e "Patrimônio marcado: Indisponível"; passa a usar o histórico de cada carteira (`GET /api/portfolio/history`). O gráfico traz retorno acumulado em % das carteiras do mesmo grupo desde o início comum (ponto "Início" = 0%), com lacunas sem valor (nunca zero), e o Ibovespa como linha tracejada de referência externa. A tabela (também acessível por sessão) mostra patrimônio marcado e data, retorno desde o início, dia, diferença vs Buy & Hold em p.p. (mesmo grupo e mesmas datas), caixa, operações e custos, mais a linha "Ibovespa (referência)". Carteiras pessoais ficam fora do grupo (DP-19); carteira do grupo com início diferente fica fora do gráfico, com aviso. O Ibovespa (`^BVSP`, Yahoo) é coletado pela mesma atualização da base de mercado (DP-27), guardado como snapshot "IBOV" fora do intradiário e do explorador; `GET /api/platform/market-base/benchmark?since=YYYY-MM-DD` (somente leitura; 400 em data inválida ou parâmetro extra) devolve o fechamento-âncora e os pregões seguintes. Carga real: 8.292 pregões desde 27/04/1993; 178 dias sem fechamento válido viram lacuna. Nota da tela: o Ibovespa inclui proventos reinvestidos e as carteiras ainda não (APP-04); a diferença é descritiva, não indica superioridade (DP-09); CDI ainda não incluído. Valores de 16/10: Buy & Hold −1,55% e Multiagentes −1,52% (14/10 → 16/10; +0,03 p.p.); Ibovespa −0,70% (13/10 → 16/10). Verificação e limites no estado atual.

**Referências e histórico, 17/10 — DP-28/29, APP-03/DATA-01:** o CDI (Banco Central, SGS série 12) entra por `dashboard/reference_rates_api.py`: janelas de 9 anos desde 03/01/2000 e incremento depois, um JSON selado e imutável por janela em `market-base-v1/rates/`; datas sobrepostas divergentes viram conflito. O acúmulo rende a taxa da data d de d até o próximo dia útil, com índice 1,0 na âncora. Carga real: 6.728 dias de 03/01/2000 a 15/10/2026 (16/10 ainda não publicado pelo BC). A mesma atualização da base (DP-27) atualiza o CDI; `benchmark` inclui `cdi`; a Comparação mostra o CDI em linha pontilhada e a linha "CDI (referência)" na tabela (13/10 → 15/10: +0,10%). Códigos antigos (DP-29): `ALIASES = {"ITAU4": "ITUB4"}` em `dashboard/market_base_api.py` traduz as linhas de ITAU4 para ITUB4 com `source_symbol: "ITAU4"`, com registros suplementares imutáveis `b3/COTAHIST_A<ano>.ZIP+ITAU4.json` para 2000–2009. Renome verificado: ITAU4 de 03/01/2000 a 19/05/2009, ITUB4 desde 20/05/2009, zero pregões sobrepostos, +1,97% na troca (29,45 → 30,03); ITUB4 agora desde 03/01/2000 (6.642 linhas, 1 lacuna, 0 conflitos). WEGE4 não traduzido: negociou junto com WEGE3 (61 pregões em comum, classes distintas até 31/05/2007); misturar exige decisão de Lucas. Radar (403): a B3 recusa o user-agent padrão do Python; `market_base_api.install_b3_user_agent` instala no servidor, ao iniciar, um opener com "HedgeFundLab/1.0 (uso local; TCC)" somente para `*.bmfbovespa.com.br`, sem editar o módulo selado `src/pipeline/b3_official.py`; urlopen simples da B3 retornou 200 ao vivo. Limite: CLIs fora do servidor não instalam o opener. Verificação e limites no estado atual.

**APP-04 (proventos), 17/10:** passa a seguir DP-30 (fonte B3 oficial; JCP líquido de 15% de IR; provento vira caixa só no pagamento, ficando "a receber" entre a data-com e o pagamento). Em andamento, não entregue.

**Ciclo diário autônomo, 20/10 — DP-34:** rotina no próprio servidor (`dashboard/daily_cycle.py`, ligada por `HFL_DAILY_CYCLE=1`) roda o ciclo completo da Multiagentes às 09:00, com novas tentativas às 12:00 e 16:00, teto diário de reserva US$ 4, aprovação automática salvo alerta de tese velha, registro selado por tentativa e e-mail via Resend; empacotamento Railway + Tailscale pronto ([guia](DEPLOY_RAILWAY.md)). Volume `hfl-data` de 20 GB criado a pedido de Lucas no ambiente `tcc`, montado em `/app/data`; novo deploy SUCCESS, com Tailscale Running, Serve ativo e servidor iniciado nos logs. Migração concluída: 23.112 arquivos com hashes conferidos, SQLite íntegro e carteiras iguais pela API HTTPS; home 200. Em 21/10, cotações/histórico e agentes restaurados com os selos originais, download B3 e e-mail testados; gestor com teto diário, sem alterar o Legacy. Ordem pendente adia novas análises pagas até o preço oficial. Deploy final e ativação concluídos em 21/10: rotina e coleta em `1`, agendador confirmado nos logs, API HTTPS e cotações/gráficos verificados no Chrome após ajuste de MTU 1280. Primeira tentativa automática às 09:00 de 21/10 ainda futura; conferir registro/e-mail e preço oficial da ordem pendente. Ambiente fixado no commit da correção, com PR em rascunho para revisão. Cópia local preservada com dashboard parado; Railway é a cópia de trabalho.

**Execução intradiária, 22/10 — DP-35/APP-05:** modalidade publicada no `tcc`:
novas aprovações entre os cortes usam o Open da primeira barra negociada de 1 min
posterior à aprovação (Yahoo, atraso ~15 min), sem esperar o fechamento. Consulta
automática a cada minuto; fonte completa selada antes da cesta atômica, retomada
idempotente e não execução explícita sem captura até 30 min após o contínuo.
Prévia vincula modalidade/sessão à aprovação; painel, home e ciclo distinguem a
modalidade. Ordens antigas preservadas. Verificação integrada: 118 aprovados,
um optativo ignorado; Node/Ruff e prévia Chrome aprovados. Conexão Railway
restabelecida; envio autorizado ao fork concluído, fonte fixada em `4fefe40`.
Deploy `5b2b7739-d8db-44ce-a990-514db37b54ae` aceito no `tcc` às 11:44 de
Brasília, inicialmente `QUEUED` durante incidente do Railway; ativação `SUCCESS`
confirmada às 13:41 com servidor/rotina nos logs, API e JS publicados via HTTPS
200, universo completo e hash da ordem antiga preservado. Não houve teste de
fill financeiro no servidor; recuperação e execução verificadas offline.
[PR #2](https://github.com/LuquinhasPS/Hedge-Fund-Lab/pull/2) em rascunho;
fonte do deploy no fork de Lucas, fixada no código aprovado; sincronizar sua
main não altera esse pin. Próximo passo: acompanhar nova aprovação intradiária.

**Textos do gestor, 22/10 — DP-17/UX-M4:** acentos restaurados no arquivo JS,
com check UTF-8, sintaxe e prévia Chrome; 57 testes do gestor aprovados, um
browser check optativo ignorado. Ordem de venda de WEGE3 aprovada às 10:35
confirmada para CLOSE de 22/10 (DP-33), ainda aguardando preço oficial. Pendente
publicar os textos com as correções abaixo; registros financeiros preservados.

**Ciclo em execução, 22/10 — DP-17/UX-M4:** correção local do resumo que
regredia Dados/Orçamento durante os Analistas e só se ajustava no Gestor. Usa
inputs verificados e reservas persistidas, com check Node e prévia Chrome do
estado real capturado. Não altera consentimentos nem inicia chamadas. Pendente
publicar após a execução manual, junto da correção de universo abaixo.

**Universo após venda total, 22/10 — DP-07/DP-24/DP-34, APP-05:** corrigido
localmente o padrão da análise manual e da rotina: a Multiagentes acompanha os
cinco ativos mesmo com posições zeradas, permitindo ao gestor considerar novas
compras. Novas análises incompletas recusadas no backend; histórico e análise
manual em curso preservados. 86 testes aprovados, um browser check optativo
ignorado. Pendente publicar no Railway após a execução manual de Lucas;
[verificação e limites](ESTADO_ATUAL.md).

**Diagnóstico de coleta, 22/10 — DP-27/DP-34:** disparo automático das 09h
confirmado; 3/4 inputs prontos, PETR4 bloqueado por download anual B3 interrompido
(24 de 86,7 MB), zero chamadas de agentes e US$ 0 reservado. Preparo manual e
automático compartilham a mesma função; transferência sem retry e download
repetido por ativo identificados. Sem alteração operacional para preservar o
teste manual pedido por Lucas. Evidências, limite de atribuição ao incidente do
Railway e pendência de troca de segredos no [estado atual](ESTADO_ATUAL.md).

**Acesso, 21/10 — DP-34:** MTU 1280 não impediu recorrência do timeout Chrome.
Deploy seguinte concluído e aplicação saudável; acesso voltou usando relay
Tailscale (`TS_DEBUG_ALWAYS_USE_DERP=true`, salvo só no serviço `tcc` e aplicado
ao daemon). Dez novas conexões Chrome com HTTP 200, relay confirmado e carteira
carregada no navegador. A causa exata do problema UDP direto segue indeterminada;
o relay pode aumentar latência. Próximo passo: acompanhar a rodada automática.

**Tela dos agentes, 20/10 — DP-17:** passos gratuitos andam sozinhos (verificação após criar, preparação e prévia do gestor, Resultados ao completar o quórum), foco no próximo consentimento, progresso do lote, taxa lembrada e barra de etapas fixa; os quatro consentimentos seguem separados. Consentimento pago único analistas + gestor fica para decisão de Lucas. Verificação e limites no estado atual.

**Execução no leilão, 19/10 — DP-33, APP-05:** a aprovação do gestor vira ordem "aguardando leilão" e executa no primeiro leilão oficial da B3 após a aprovação (abertura antes de 09:45, fechamento até 16:50, abertura seguinte depois; horários configuráveis por regime), lançada pela atualização de dados ao preço oficial com data do leilão; proposta válida até os leilões do pregão-alvo. A prévia mostra a cotação atrasada do Yahoo como retrato selado (nunca preço de execução, marca ou prompt), pede nova prévia se o preço sair da faixa `clamp(3·σ60·√(h/415); 0,5%; 2%)` e exige ciência no alerta de tese velha. Cada operação guarda preço de decisão, cotações da prévia e da aprovação e preço do leilão. Verificação e limites no estado atual.

**Proventos no livro, backtest e pesquisa, 18/10 — DP-30 A, DP-31:** proventos recebidos passam a ser lançamentos idempotentes no livro (livro, home e gestor com o mesmo caixa); backtest de regras no Laboratório com Ibovespa e CDI; [pesquisa da munição para os agentes](PESQUISA_MUNICAO_AGENTES.md) com recomendação em fases e decisões pendentes (DP-32). Verificação e limites no estado atual.

**Proventos, 17/10 — DP-30, APP-04:** `dashboard/dividends_api.py` lê a consulta pública da B3 (`GetListedSupplementCompany`, uma por emissor, cerca de 12 meses de histórico), filtra a classe pelo ISIN (ON/PN) e guarda snapshots selados imutáveis em `market-base-v1/dividends/<ativo>/`, sem duplicar quando nada muda; a atualização da base (DP-27) a executa. Direito pela posição ao fim da data-com; JCP líquido de 15%; estados Anunciado (data-com futura, quantidade estimada), A receber e Recebido. O histórico de patrimônio soma recebidos e a receber ao patrimônio, `cash_available` = caixa do livro + recebidos; a receber nunca é caixa. Página Proventos com totais e eventos, caixa da home e Rotina do dia com a receber, coluna de proventos na tabela de patrimônio e nota da Comparação ajustada. Hoje nenhuma data-com desde 13/10: as duas carteiras mostram R$ 0,00 real. Verificação e limites no estado atual.

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
