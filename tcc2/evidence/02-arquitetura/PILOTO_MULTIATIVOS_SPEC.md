# PAPER-01 — contrato operacional do piloto multiativos

**DRAFT — BASES APROVADAS; REGRAS TÉCNICAS PENDENTES** · revisão em 14/10/2026.
Bases DP-09–DP-15 e composição inicial comum DP-18 aprovadas por Lucas em 14/10;
demais recomendações continuam pendentes. DP-17/19 ampliam os fluxos da interface
e o registro pessoal, sem promover lançamentos históricos ao piloto. Não autoriza
inferência paga, criação de carteira oficial, ingestão oficial ou operação paper.

[Direção](DIRECAO_DO_PROJETO.md) · [Roadmap](ROADMAP.md) ·
[Estado](ESTADO_ATUAL.md) · [Índice](README.md).

## 1. Produto, autoridade e base observada

Atende **DP-01–DP-08 / PAPER-01**: tornar implementável o acompanhamento diário
da carteira selecionada, com patrimônio, caixa, posições, períodos, comparação
e rastreabilidade decisão → autorização → operação → patrimônio reconciliado.
O primeiro incremento é demonstração operacional prospectiva; avaliar benefício
financeiro exige protocolo científico próprio. Sucesso operacional independe de lucro.

**Aceito:** carteira como início; seletor de carteiras independentes; indicadores
em R$/%; trajetória diária; D0=13/10/2026; referência com alvos iniciais de 20%
em PETR4, VALE3, ITUB4, WEGE3 e BBAS3; H2 e Radar/PM separados.
**Atualização aceita em 14/10:** piloto operacional/descritivo; agentes e Buy & Hold
com R$ 100 mil independentes; referência sem rebalanceamento/reinvestimento,
proventos em caixa; sem aportes/retiradas; rotina manual com autorização explícita;
revisão após 20 pregões; início efetivo na primeira sessão elegível após preparação.
Registro canônico: DP-09–DP-15 no documento de direção.
**Atualização posterior aceita — DP-18:** as carteiras simuladas comparadas
devem partir das mesmas posições, aproximadamente 20% em cada ativo. Isso
substitui a recomendação de primeira alocação independente dos agentes. A
proposta de exposição máxima de 85% precisa de revisão; execução inicial,
custos, quantidades e sessão continuam pendentes. Ver seção 8.2.
**Recomendado, ainda não aprovado:** demais números/limites, custos, buffers,
fonte, eventos, rendimento de caixa, prazos e execução. O texto R1–R9 abaixo
preserva a formulação anterior; a seção 8 explicita o estado atualizado de revisão.

Não há carteira oficial multiativos ativa. V2 é proposta consultiva de **100%
caixa e zero operações**; COMPRA PETR4 pertence ao H2. Nenhuma V1/V2, aprovação
ou decisão H2 pode originar ordens deste piloto.

### Matriz de reutilização

Evidências com linhas referem-se ao checkout inspecionado nesta tarefa. **C** =
observado no código; **T** = cenário conferido no teste existente e resultado
histórico registrado, sem reexecução aqui; **D** = documentação versionada.
Ter um teste não demonstra funcionamento prospectivo oficial.

| Componente existente / evidência | Capacidade observada | Limitação | Próxima integração |
|---|---|---|---|
| C: `scripts/paper_ledger.py:186–260,493–519` | Envelope, carteira própria, eventos, hashes, replay/checkpoint | Só autoridade/classificação sintética; fingerprints fixos | Contrato prospectivo versionado, sem promover fixture |
| C: `scripts/paper_ledger.py:523–577,619–699`; T: `tests/test_paper_ledger_v765.py:399–427,464–519` | SQLite stdlib, evento+checkpoint atômicos, chave/pedido, rollback, confirmação perdida, concorrência | Escrita somente TEMP externo; replay O(n); sem backup de disco | PAPER-03: raiz durável restrita, restauração e ancoragem |
| C: `scripts/multiasset_portfolio.py:160–232,294–410,413–591`; T: `tests/test_paper_ledger_v765.py:90–132,604–655` | Decimal, centavos HALF_EVEN, base, reservas, compras/vendas, recebível, D+2 e identidade patrimonial | Pré-financiado, inteiro/BRL, cesta integral; política DEMO fixa | Reusar contabilidade; qualificar ponte de preços/tempo/política |
| C: `scripts/multiasset_manager.py:132–258,295–517`; T: `tests/test_paper_ledger_v765.py:154–180,211–250` | Risco, validação, veto, proposta sem ordem, vínculo de autorização | Mesma sessão/marca; 60 retornos ajustados; limites didáticos | Validação prospectiva em duas etapas e política por estratégia |
| C: `scripts/multiasset_global_pm_v2.py:244–300,358–421,480–526`; `scripts/run_global_pm_v2.py:448–501,553–557`; T: `tests/test_global_pm_v2.py:125–141,267–309,790–847` | Contexto congelado, validador independente, aprovação paga separada | Consultivo; ponte matemática sintética, não recebe carteira ativa | Nova decisão/identidade e snapshot do ledger; não usar run histórico |
| C: `scripts/multiasset_radar.py:225–248,269–335`; `src/pipeline/b3_official.py:48–68,90–150` | Leitura COTAHIST RAW, histórico ajustado, features e hashes | Prepare pode baixar dados; fatores ajustados usam yfinance; sem vintage prospectivo de disponibilidade | DATA-01: entrada local congelada e corte temporal; canal automático/reuso em avaliação na seção 14, sem chamar prepare nesta tarefa |
| C: `scripts/paper_ledger.py:63–145,375–425`; T: `tests/test_paper_ledger_v765.py:252–258,281–341` | Calendário coberto, D+2, RAW, OPEN/CLOSE de fixture, ausência de marca | Lista termina 31/08/2026; execução só SYNTHETIC_REFERENCE, não OPEN oficial | Calendário ampliado validado, fonte real e fill causal t+1 |
| C: `scripts/multiasset_portfolio.py:548–563,594–664`; T: `tests/test_multiasset_portfolio.py:323–383` | Provento/JCP, pagamento, split e bloqueio de evento não reconciliado no V5 | `paper_ledger.EVENTS` não expõe CORPORATE/CORPORATE_PAID; sem entitlement ex-date prospectivo | Ponte de eventos, elegibilidade e pagamento antes de operar em tais datas |
| C: `scripts/paper_ledger.py:154–183,280–303,458–477`; T: `tests/test_paper_ledger_v765.py:331–397` | Invariantes, indisponibilidade, reconciliação e histórico só em sucesso | Sessão publicada imutável; não reabre passado; reconciliação interna não é custódia externa | Fechamento diário e recuperação cronológica; fonte de confirmação paper explícita |
| C: `dashboard/paper_ledger_api.py:43–51,64–144,191–264,268–296`; `dashboard/server.py:480–482`; T: `tests/test_paper_ledger_v765.py:755–811` | GET, sessão, páginas, posições/curva calculadas no backend; GET sem escrita | Lê exportação sintética; `summary.cash` é disponível, curva usa liquidado; `decision_session` do trade é a sessão do fill sintético | Projeção prospectiva, períodos, origem/corte e vínculo real à decisão |

D: [qualificação V7.6.5](evidence/hfl_paper_ledger_v765/QUALIFICATION_RESULT.json)
registra 49 testes/68 subchecks direcionados e 30 checks de navegador; regressão
1801 passed/14 falhas preexistentes. [V5](evidence/hfl_multiasset_portfolio/README.md)
registra 29 checks offline, incluindo o cenário corporativo acima. São resultados
anteriores, de fixtures. Nesta tarefa só se executam checks documentais/preservação.

**Dois impedimentos concretos ao reuso direto:**

- `multiasset_portfolio.POLICY` (`:18–36`) fixa exposição 85%; `safety` (`:298–308`)
  é chamada por `fill` (`:410`), inclusive na prévia de reserva. A referência
  quase integral de cinco alvos de 20% falha. Não reduzir os alvos para 17%,
  falsificar pareceres favoráveis ou mudar constantes globais para contornar.
- `manager.validate` (`:327–343`) exige mesma sessão/estado/marca; V5 proíbe
  marcar com reserva pendente (`:447–450`); `checked_observation` compara
  `observed_at` com `effective_at` (`paper_ledger.py:137–141`). Portanto reservar
  em t, marcar OPEN em t+1 e executar após publicação diária não é hoje suportado.
  A ponte prospectiva deve distinguir estado aprovado, preço de execução e
  processamento tardio, sem produzir uma aprovação sintética depois da abertura.

## 2. Carteiras, entrada e relógio

**R1 — recomendação:** duas carteiras BRL long-only, sem crédito, com IDs novos
estáveis e mesmo capital virtual **C=R$ 100.000,00**: agentes e referência
`BUY_HOLD_EQUAL_WEIGHT_INITIAL`. Mesmo universo dos cinco ativos. Separar
`portfolio_id`, estratégia/versão, protocolo (ou finalidade operacional), data de
inicialização, capital, políticas e fontes. Justificativa: comparação legível e
reuso da escala existente; impacto: capital e orçamento do novo tratamento
continuam pendentes, sem aproveitar saldos H2. Outras estratégias ficam fora.

**R2 — recomendação:** Buy & Hold compra uma cesta inicial; sem rebalanceamento
periódico, reinvestimento de proventos ou venda voluntária posterior. Caixa residual
e proventos permanecem em caixa, sem rendimento no piloto. Eventos obrigatórios
são contabilizados; deslistagem, conversão não suportada ou saída excepcional
interrompem o acompanhamento válido até decisão explícita, sem venda fictícia.
Justificativa: referência determinística simples; impacto: pesos derivam e o
resíduo pode crescer; não é um índice de retorno total com reinvestimento.

**D0, inicialização e primeiro fill são três fatos diferentes.** D0 continua
13/10/2026 como marco do produto. `s0` é a sessão de criação efetivamente
autorizada, com C em caixa e snapshot inicial reconciliado antes de operar.
Se criada depois de D0, não gerar pontos de caixa, retorno zero ou compras
entre D0 e s0. A tela informa “marco D0; carteira ainda não iniciada” e depois
“histórico desde s0”. O ponto inicial pode ser reconciliado em s0 sem operações;
qualquer ordem será para sessão posterior. Nenhum fill é imposto em 13/10.

Para a primeira decisão, t é a primeira sessão encerrada, t≥s0, cujos dados,
indicadores, estado e eventual inferência estão disponíveis e congelados **antes**
da abertura-alvo de u=próxima sessão B3 após t. `target_open_at` vem do horário
validado em DATA-01, em America/Sao_Paulo, sem fixar 10h por suposição.
Se dados, decisão ou autorização chegarem tarde, essa abertura é inelegível;
obter contexto/decisão/autorização novos para outra abertura. Não usar contexto
antigo com TTL renovado automaticamente. Agentes podem decidir manter caixa;
referência faz sua decisão determinística própria.

**R3 — recomendação de execução:** uma cesta pendente por carteira, quantidades
inteiras (unidades, inclusive fracionário; sem fração de ação), fill integral
atômico ou nenhum fill. Custos didáticos comuns `fee=money(0,001×q×P)` por perna,
HALF_EVEN em centavos, sem IR sobre ganho nem remuneração de caixa; retenção de
proventos somente se comprovada. Preço de fill = OPEN RAW observado de u, com
slippage adicional zero, explicitamente hipótese paper sem garantia de liquidez.
Justificativa: aproxima a base qualificada; impacto: não demonstra custo ou
executabilidade real. Taxa, fracionário e modelo precisam de revisão.

Para o benchmark, reservar **C/5 por ativo, incluindo custos**, sem redistribuir
sobras. Recomendação inicial de limite: `L_i=money(CLOSE_RAW_i(t)×1,02)`;
`q_i=max{q inteiro≥0: money(q×L_i)+fee(q,L_i)≤C/5}`. Registrar o alvo 20%, q,
limite e teto de custo antes da abertura. Se q=0 em qualquer ativo, bloquear
a entrada para revisão, não criar cesta de quatro ativos. Para venda dos agentes,
limite inicial sugerido `money(CLOSE_RAW_i(t)×0,98)`; as quantidades vêm da proposta,
não de ajuste automático no fill. O buffer de 2% limita gap e reserva caixa;
é parâmetro proposto, sem calibração comprovada. Se OPEN violar limite, custo,
saldo, elegibilidade ou cobertura de uma perna, cancelar a cesta inteira.
Pesos realizados `q_i×OPEN_i/E` diferem de 20% por preços, custos, inteiros e
reserva conservadora; mostrar alvo e realizado separadamente. Nunca recalcular
q com OPEN já conhecido e tratá-lo como quantidade autorizada ex-ante.

### Sequência e falhas de tempo

1. Encerrar t: importar dados congelados disponíveis, tratar eventos/D+2 devidos,
   marcar CLOSE RAW e reconciliar; só então produzir contexto do gestor.
2. Antes de `target_open_at(u)`: congelar proposta, validar, registrar autorização
   humana e intenção executável com q/limites/prazo. A prévia não é uma posição.
3. Na fase OPEN de u: a intenção é elegível; quando o dado se tornar disponível,
   validar o preço/condições e processar o fill paper. Não consultar OPEN para
   decidir, aprovar, aumentar quantidade ou trocar ativo.
4. No fechamento de u: incorporar liquidações/eventos devidos, CLOSE RAW completo,
   marcar e reconciliar. Publicar um snapshot diário apenas em sucesso. Repetir
   para sessões seguintes; decisão sem operações também termina em marca/reconciliação.

**R4 — recomendação de prazo:** autorização criada antes da abertura, válida
para a fase OPEN de uma única sessão, com expiração econômica explícita no fim
dessa fase segundo calendário validado. Atraso de publicação não estende a
janela econômica; permitir processamento da intenção já selada até **12h do dia
civil seguinte a u**. Justificativa: admitir arquivo diário e trabalho manual;
impacto: não é execução em tempo real e pode expirar em dias sem pregão.
O prazo de processamento é separado da validade econômica da autorização.
Expiração econômica é avaliada para a abertura-alvo: se a autorização já estava
vencida naquele momento, não há fill. Se estava válida e a intenção foi selada
antes da abertura, o processamento posterior só contabiliza esse fato dentro
do prazo separado; não cria nem renova autorização. Após o prazo de
processamento, não contabilizar novo fill, mesmo com autorização ex-ante.

Persistir `data_session`, `decision_at`, `authorized_at`, `target_open_at`,
`economic_session/phase`, `economic_at` quando comprovado, `available_at`,
`processed_at/recorded_at`, `expires_at` econômico e `processing_deadline`.
Um arquivo diário OPEN não comprova o segundo exato do primeiro negócio:
identificar precisão OPEN/SESSÃO e deixar instante real indisponível. Não usar
o horário de processamento como se fosse o horário econômico. O envelope atual
exige `effective_at` preciso/monotônico; essa distinção exige contrato versionado
na ponte futura, preservando replay antigo. Para decisão, `available_at≤decision_at`;
para contabilizar fill tardio, `available_at≤processed_at`, com intenção/autorização
ex-ante verificadas, e não `available_at≤horário econômico da abertura`.

Sem OPEN: PENDENTE_DADO até o prazo; depois EXPIRADA_SEM_FILL, liberar reservas,
preservar diagnóstico. Ausência de autorização em prazo: EXPIRADA_SEM_AUTORIZAÇÃO.
Cancelamento humano anterior ao fill deixa evento e libera reservas; uma cesta
cancelada/expirada não renasce com os mesmos IDs. Dado ausente de CLOSE mantém
última marca **com sua data**, bloqueia nova decisão dependente e não publica
ponto. Dado tardio completo permite retomar a sessão ainda aberta em ordem
econômica; nunca inserir fill em sessão já finalizada ou retroceder a cadeia.
Se isso for necessário, interromper e revisar correção versionada; sem reparo
silencioso, sobrescrita ou aprovação retroativa. Reinício recupera a intenção
selada e os mesmos comandos, sem inferir novamente.

## 3. Dados, caixa e eventos

**R5 — recomendação:** COTAHIST B3 como candidato para OPEN/CLOSE RAW, importado
manualmente, com arquivo local imutável. Não presumir horário de publicação,
licença, atraso ou disponibilidade de outubro: DATA-01 deve verificar condições
de uso, cobertura e corte antes de escolher essa fonte para o piloto. Se não
atender ao prazo de R4, revisar prazo/fonte antes de operar, sem simular entrega.
Cada bundle registra fornecedor/fonte, ticker/instrumento (incluindo convenção
do fracionário), sessão/calendário, BRL, RAW ou ADJUSTED, OPEN/CLOSE, instante de
coleta e disponibilidade comprovada (coleta como limite conservador quando não
houver prova anterior), vintage, versão do parser, hash bruto e hash normalizado.
Retificações geram nova versão e diagnóstico; não reescrevem sessão reconciliada.

Indicadores usam representação própria ajustada, separada da contabilidade:
recomenda-se reusar cálculo Radar, seus 200 pregões mínimos e os 60 retornos
alinhados do risco, congelando também fatores/fonte/vintage disponíveis em t.
Ajuste obtido posteriormente não é conhecimento ex-ante. RAW para quantidade,
base, OPEN de fill e CLOSE de patrimônio; nenhum preço ajustado cria saldo.
Se não houver histórico/fatores temporalmente justificáveis, bloquear inferência
dos agentes, sem converter cache de pesquisa em fonte prospectiva. Impacto de R5:
reuso do parser/features, mas ingestão e disponibilidade ainda são trabalho novo.

O calendário novo valida sessões, horários de abertura/fase, fechamentos,
feriados e duas sessões futuras para D+2, inclusive virada de ano. Hoje a
interseção do adaptador termina em agosto/2026 e o motor limita ano a 2026;
outubro e eventual 2027 são bloqueios, não extensões presumidas. Não emprestar
calendário/estado H2. D+2 é recomendação de modelo paper reutilizado, sujeito à
verificação da regra aplicável ao instrumento/período em DATA-01.

| Grandeza | Autoridade contábil proposta (reuso V5) |
|---|---|
| Caixa liquidado S | `financial.settled_cash`; compra debita bruto+custo no fill |
| Reserva R / disponível A | soma `pending.cash_reserved`; `A=S−R`; reserva não reduz patrimônio novamente |
| Recebíveis B | soma `receivables.amount`: venda líquida até D+2 e provento reconhecido até pagamento; não financiam compra |
| Quantidade Q / disponível | total inclui compra em liquidação; vendável = total−reservada−unsettled |
| Investido V / patrimônio E | `V=Σ Q_i×CLOSE_RAW_i`; `E=S+B+V`; posição vendida sai no fill |
| Base/PnL | compra agrega bruto+custo à base; venda parcial retira base proporcional HALF_EVEN; `E=C+realized_pnl+income_net+unrealized_pnl` |
| D+2 | compra libera custódia; venda transfere recebível ao liquidado mediante confirmação paper identificada; sem novo custo/PnL |

**R6 — recomendação:** confirmar D+2 por comando manual com fonte
`PAPER_CALENDAR_CONFIRMATION`, calendário/hash, operador e ID único; não dizer
que houve confirmação de corretora. Proventos: fonte oficial do emissor/B3,
data-com, ex-date, pagamento, posição elegível, bruto, retenção comprovada e
líquido. Reconhecer direito líquido como recebível/renda na ex-date, pagar na
data comprovada; não reinvestir no benchmark. Entitlement usa posição econômica
e negociações elegíveis, sem presumir que custódia liquidada atual resolve
data-com. V5 não integra esse registro histórico de direitos: precisa de ponte
qualificada. Split/bonificação/grupamento altera q/base unitária conservando
base total; frações/compensações exigem fonte e regra explícita. Não inventar
dinheiro para fechar identidade. Justificativa: RAW sem eventos distorce retorno;
impacto: evento não suportado suspende marca/ordens e a série comparável. Mesmo
em carteira sem ordens, eventos e liquidações continuam obrigatórios.

## 4. Gestor, risco e autorização

Nova decisão: snapshot reconciliado da carteira + dados/features disponíveis de
t + novos pareceres identificados → contexto congelado do novo tratamento →
gestor → proposta estruturada → validador determinístico. Reusar cálculos e
schema onde compatíveis; a ponte V2 atual continua consultiva, não é runner do
piloto. Registrar versão de modelo/prompt, configuração, contexto, pareceres e
resposta/hash. Em PAPER-02 o produtor é fixture sem rede; produtor pago futuro
só após autorização própria. Não converter recomendação textual em execução.

**Proposta válida** respeita estado, fontes e política, mas não autoriza ordem.
**Autorização** é ato humano autenticado e registrado. **Ordem executável** tem
autorização vigente, intenção registrada antes da abertura, quantidades/limites
fixos, reservas possíveis e gates de dado/calendário/risco. No processamento,
validar OPEN e transição do estado aprovado sem redecidir. Apenas marca de
abertura pode mudar conforme a regra selada; qualquer operação, liquidação ou
evento corporativo que altere o estado aprovado invalida a intenção. Regularizar
D+2/eventos conhecidos antes do corte; não autorizar em cima de estado incompleto.

Vínculo mínimo: operador autenticado, carteira/tratamento, proposta e validação
por ID/hash, snapshot/estado e marca de t, política/calendário/fontes, operações
por ID/ativo/lado/q, preço-limite/teto de custo/exposição, sessão/fase-alvo,
emissão/expiração/prazo de processamento. Rejeição, revogação e expiração também
são registros. Autorização de inferência paga fixa campanha/modelo/chamadas/
orçamento; não autoriza ordem. Aprovação paper não autoriza gasto de inferência.

**R7 — proposta refinada em 14/10/2026, ainda não aprovada:** manter os valores
didáticos propostos (40% concentração, 85% exposição, 35% volatilidade anual,
20% drawdown por pico de eventos, 100% giro/dia, custo/dia até 1% e 10 operações),
60 retornos/252; distinguir admissão de exposição de redução de posições
existentes conforme seção 4.1. Veto impede compra/aumento do ativo; excesso de
limite bloqueia compras da carteira, mas não rejeita automaticamente uma cesta
de redução elegível. Ausência de parecer continua permitindo apenas manutenção.
Não há venda forçada/autônoma. A proposta anterior mantinha
`NO_OPERATION_ON_VETO` inclusive venda; esta revisão substitui essa recomendação
para o futuro tratamento. Política e comportamento V5/V2 selados permanecem
intactos; nenhuma redução sob veto está implementada por esta revisão.

Benchmark usa regra determinística, sem parecer/veto/volatilidade/drawdown dos
agentes; conserva controles comuns de saldo, fonte, inteiro, custos, autorização
e integridade. Recomenda-se exposição de entrada até 100% sem alavancagem,
alvos 20%; concentração posterior pode derivar sem rebalanceamento. Essa
diferença deve aparecer na comparação. O V5 fixo **não implementa** tal política:
PAPER-02 precisa qualificar extensão versionada restrita aos pontos de política
e execução incompatíveis, preservando bytes, identidade e replay selados.
Não basta envolver `b.fill` com um validador permissivo: ele chama o limite 85%.
Reusar `view`, Decimal, base/recebíveis e algoritmo financeiro; não duplicar todo
o ledger, mutar `POLICY` em runtime nem importar demo como carteira. A escolha
da extensão é requisito de implementação e revisão, não capacidade entregue.

Proposta válida sem operações registra decisão `HOLD/NO_OPERATIONS` com motivo
e hashes; pode ter ciência humana sem autorização de ordem. Não chamar reserva/
fill, criar ordem de quantidade zero nem atribuir ausência de resposta a HOLD.
Ausência de decisão é `DECISION_MISSING`; a carteira existente ainda é marcada,
liquidada e reconciliada quando os dados permitem.

### 4.1. Redução de posições sob veto ou excesso de risco — proposta R7

Refinamento solicitado por Lucas **antes do aceite**, vinculado a PAPER-01 e
DP-01/04/05/08/13. Propõe um caminho de redução distinto da admissão de compras,
com validação determinística própria na futura extensão versionada. Não mudar
`POLICY`, remover guardas globais, mutar V5/V2 ou reutilizar seus ensaios como
aprovação desta política. Demais parâmetros R2–R9 continuam propostas.

| Situação | Regra recomendada |
|---|---|
| Veto de um ativo com posição existente | Proibir compra/aumento desse ativo; admitir sua venda parcial ou total pelo caminho de redução. O veto e seu parecer permanecem registrados, não são convertidos em aprovação de compra |
| Exposição, concentração ou volatilidade acima do limite | Bloquear novas compras da carteira; admitir cesta apenas de redução que diminua exposição e não agrave os demais excessos corrigíveis. Pode permanecer acima do limite após redução parcial; não exigir saneamento integral numa única cesta |
| Drawdown acima do limite proposto de 20% | Bloquear novas compras e registrar estado de revisão; permitir redução elegível sem exigir drawdown pós-venda abaixo de 20% ou menor que o anterior. Manter perda, pico e série; retomada de compras depende de revisão humana explícita |
| Integridade, dado/risco indisponível, custódia, evento não reconciliado ou autorização inválida | Bloquear a operação também na redução. Falta de dados não é excesso de risco mensurado; não atribuir zero a volatilidade indisponível nem fabricar parecer |

**Critério de redução:** a cesta contém somente SELL de instrumentos já detidos,
sem BUY, troca de ativo ou compensação por exposição líquida. Para cada ativo,
`0 ≤ Q_depois ≤ Q_antes`, com redução estrita em ao menos um. A quantidade vendida
inteira e positiva não excede `Q_total − Q_reservada − Q_em_liquidação`, conferida
na reserva e no fill. Uma reserva própria já criada é reconhecida uma única vez
na conferência do fill; não somar disponibilidade duas vezes. Nunca vender a
descoberto, financiar compra com recebível ou contar venda não liquidada como
caixa disponível. Custos, base, PnL realizado e recebíveis D+2 seguem registrados.

**Comparação antes/depois:** projetar ambos os estados com o mesmo vetor de preços
RAW e o mesmo contexto de risco congelado antes da abertura-alvo, incluindo custos
no estado projetado. Não usar histórico posterior para aprovar a intenção.
Exigir patrimônio positivo, valor bruto investido estritamente menor
e razão investido/patrimônio não crescente. Isso mede efeito da cesta, sem
atribuir à venda uma variação de preço ocorrida entre duas sessões. Recalcular
concentração e volatilidade projetadas: não criar nova violação desses limites
nem agravar um excesso já presente. Uma venda pode aumentar concentração de
outros ativos ou volatilidade por alterar diversificação; o rótulo redução não
dispensa essa conferência. Excesso residual é registrado, não apagado.
Drawdown tem tratamento próprio abaixo, sem teste de cura pela venda.

Na proposta usar dados disponíveis antes da abertura-alvo; no processamento
revalidar a cesta inteira com OPEN RAW e condições autorizadas. Se perder
elegibilidade, recusar/expirar conforme R3/R4, sem recalcular quantidades nem
aproveitar só as vendas de uma cesta mista anteriormente aprovada. Uma nova
cesta de redução exige nova proposta e autorização ex-ante para sessão elegível.
Variações posteriores do mercado continuam aparecendo nas marcas, não constituem
por si aumento de posição autorizado.

**Controles preservados:** origem/vintage/RAW, dados e histórico de risco válidos,
parecer exigido pela política, calendário/fase/disponibilidade, preço-limite,
teto de custo, giro/dia e quantidade de operações, custódia/reservas, eventos,
estado reconciliado, autorização autenticada vinculada a q/limites/prazo,
idempotência e transação integral. Veto ou excesso de limite precisa ser
classificado separadamente de falha nesses controles, não ignorado junto com
qualquer erro de um relatório `BLOCKED`. Se custo/giro/custódia impedir a venda,
registrar o bloqueio e planejar outro ciclo elegível; a redução não concede
exceção automática. Nenhuma venda surge só porque um limite foi ultrapassado.

**Drawdown persiste após liquidar:** conservar
`DD = max(0, 1 − E/H)`, com patrimônio reconciliado `E = S + B + V` e pico
histórico `H` preservado. Vender troca posição por recebível/caixa e realiza PnL;
não recompõe patrimônio perdido. Custos podem aprofundar o drawdown, portanto
não impor `DD_depois ≤ DD_antes` como requisito de saída. Exemplo meramente
aritmético, não dado observado: pico R$ 100.000, patrimônio R$ 78.000,
investido R$ 60.000 e caixa R$ 18.000 dão DD 22%. Venda integral nas mesmas marcas,
com custo proposto de R$ 60, deixa patrimônio R$ 77.940 (caixa R$ 18.000 +
recebível R$ 59.940 até D+2), exposição zero e **DD 22,06%**. A saída é permitida
se cumprir os controles; não é recuperação da perda.

Após o gatilho de drawdown, permanecer sem novas compras mesmo se uma marca
posterior recuperar o indicador, até revisão humana registrada. Revisão deve
vincular causa, estado, limites/política e eventual retomada autorizada; não
reiniciar pico, capital, IDs ou série para contornar o limite. Retomada fora dos
limites vigentes exigiria decisão separada e nova versão explícita da política,
preservando histórico. A aprovação de uma venda de redução não libera compras.

**Exposição e comparação entre estratégias:**

| Agentes — proposta | Referência — proposta técnica, com DP-07/11 preservadas |
|---|---|
| Limite de admissão 85% do patrimônio em ações, ao menos 15% fora delas quando dentro do limite; essa parcela pode conter recebíveis, não necessariamente caixa disponível. Excesso por valorização não força venda automática | Entrada com teto até 100% sem crédito, alvos iniciais 20% e custos/sobras respeitados; exposição realizada pode ser menor. Sem rebalanceamento, reinvestimento ou veto dos agentes; pesos posteriores derivam |
| Redução sob veto/excesso conforme este caminho, com autorização | Sem importar automaticamente o gatilho de saída dos agentes. Eventos obrigatórios seguem tratamento próprio; saída excepcional exige decisão explícita |

Mostrar exposição realizada, caixa e recebíveis junto dos retornos; mesmas
fontes/custos/capital não tornam o risco equivalente. Uma diferença de retorno
pode resultar da exposição 85% versus até 100%, permanência em caixa ou política
de veto; não atribuir automaticamente a habilidade dos agentes.

**Decisão ainda pendente de Lucas:** aceitar esse caminho de redução, os testes
de não agravamento, bloqueio de compras após drawdown com revisão explícita e
políticas de exposição separadas. Valores numéricos, custos, buffers, prazos,
eventos, caixa e mecanismo de autoridade permanecem sem aprovação presumida.
Antes de implementar, qualificar redução parcial ainda acima do limite, veto,
custódia insuficiente, cesta mista, métricas agravadas, drawdown com custo,
autorização vencida e dados ausentes. São requisitos futuros, não testes ou
capacidade já entregues. Esta revisão não altera código, não ativa o piloto
e não faz chamadas pagas.

## 5. Indicadores e comparação da tela inicial

**R8 — recomendação:** calcular métricas no backend a partir de snapshots diários
reconciliados completos, nunca sobre a página de 50 pontos da API. Capitalização
inicial C é único fluxo externo; **aportes/retiradas ficam excluídos do piloto**.
Proventos e custos são resultados internos. Se houver fluxo externo, bloquear
essas métricas até contrato de retorno com fluxos; não subtrair aporte como lucro.
Justificativa: fórmulas verificáveis sem TWR novo; impacto: sem simular aportes.

Para sessão s e âncora a: `ΔR$(a,s)=E_s−E_a`;
`Δ%(a,s)=100×(E_s/E_a−1)`; desde início, `E_a=C` do snapshot autorizado em s0.
Diário usa fechamento da sessão B3 imediatamente anterior; primeiro fechamento
após inicialização pode usar C, rotulado “desde inicialização”, sem fingir
fechamento anterior. Em s0, baseline não é retorno diário. “Dias anteriores”
seleciona a sessão e aplica a mesma regra.

| Período selecionado, encerrado em s | Âncora a requerida |
|---|---|
| Diário | Sessão B3 imediatamente anterior a s |
| Mês corrente (MTD) | Última sessão anterior ao primeiro dia do mês de s |
| Mês passado escolhido | Última sessão anterior ao mês; fim na última sessão do mês escolhido |
| Ano corrente (YTD) | Última sessão do ano civil anterior ao de s |
| Ano passado escolhido | Última sessão anterior ao ano; fim na última sessão desse ano |
| Últimos 12 meses | Última sessão ≤ data de s menos 12 meses civis; ajustar 29/02 para 28/02 se necessário |

Últimos 12 meses não significa YTD nem 252 pontos. Períodos correntes são “até s”,
sem extrapolação/anualização. Se a âncora anteceder s0, mostrar **histórico
insuficiente para o período completo** e, separadamente, “desde s0 (parcial)”
com C. Sem snapshot da âncora por lacuna, não substituir por uma sessão mais
antiga silenciosamente. Exigir cadeia diária completa entre a e s para publicar
o indicador deste piloto; dado faltante gera indisponibilidade, não zero.

| Campo da interface | Fonte e fórmula propostas |
|---|---|
| Patrimônio / investido / exposição | snapshot `view.equity`; soma `positions.market_value`; `V/E` |
| Caixa principal e detalhe | mostrar liquidado `cash.settled`, disponível `cash.available`, reservado `cash.reserved` e a receber `cash.receivable` separados; disponível não substitui E |
| Variação R$/% e evolução | snapshots `history[].view.equity`, C, calendário e âncora acima; guardar sessões usadas e status de cobertura |
| Ativo: quantidade/base/custo médio/valor/peso | `positions.quantity/basis/average_cost/market_value/weight`; `Q×CLOSE_RAW`, `valor/E`; custódia disponível separada |
| Ativo: variação de preço diária | `CLOSE_RAW_s/CLOSE_RAW_anterior−1` e diferença em R$/ação; em ex-date/split, mostrar evento e suspender comparação simples até regra comparável, sem chamá-la de retorno total |
| Posição: resultado e mudança diária | não realizado `market_value−basis`; mudança `V_s−V_anterior` rotulada mudança de valor (inclui trades/eventos), nunca rentabilidade; posição nova sem base diária mostra “nova posição” |
| Custos/resultado/renda | `view.costs/realized_pnl/unrealized_pnl/income_net`; custos já incluídos, não descontar novamente |
| Última decisão/operação/pendência | IDs de proposta/validação/autorização e eventos ligados ao trade; datas de decisão e fill distintas; falta de decisão não é zero trades deliberado |
| Atualidade/integridade | sessão do snapshot, quote/hash/tipo/fonte, data de disponibilidade, reconciliação ID/hash, última sessão esperada e lacunas; horário do GET é consulta |

Recomendação de gráfico: **índice base 100**, `I_s=100×E_s/E_a`, por carteira,
com patrimônio absoluto disponível na selecionada. Usar s0 comum efetivo para o
grupo planejado; se inícios diferirem, mostrar os inícios individuais e oferecer
base comum apenas na primeira sessão reconciliada compartilhada, rotulada
“desde a”. Não apresentar trecho desde D0 sem observações. Pontos faltantes
interrompem linha; nenhuma interpolação/preço carregado como nova observação.
Mostrar alternativa em tabela acessível, legenda/foco e status em texto.

Comparação científica exige mesmo universo, capital inicial e início acordados,
sessões/cortes/vintages/fontes RAW, custos, modelo OPEN/slippage, liquidação,
eventos e janela de métricas; versões e diferenças estratégicas explícitas
(agentes podem ficar em caixa e têm veto/limite, benchmark não). Sem equivalência,
gráfico é descritivo, com aviso de incomparabilidade; não demonstra superioridade.
H2/consultivo/sintético ficam identificados fora desse grupo. Uma observação
mostra baseline/estado, sem alegar série de desempenho.

## 6. Operação, bloqueio e recuperação

**R9 — recomendação:** fluxo manual local, um escritor SQLite, sem novo serviço
ou biblioteca. Operador Lucas autenticado pelo acesso local restrito; comando
explícito registra identidade e hash do objeto aprovado, sem confiar apenas em
campo `operator` enviado pelo cliente. Reusar práticas locais; PAPER-03 deve
qualificar ACL/identidade e revisão independente. Escrita via runner explícito
antes de endpoint web; GET só consulta snapshot/exportação verificada por ID,
sem aceitar caminho arbitrário, baixar dados, inferir, liquidar ou reconciliar
persistindo. Futuro POST exigirá autenticação/controle de origem próprios;
não faz parte do primeiro caminho. Scheduler somente após piloto manual aceito.
Justificativa: menor superfície operacional; impacto: atraso/falha manual visíveis.

Raiz durável futura dedicada fora de TEMP e de H2/Radar/PM, autorizada em
PAPER-03/04; nunca retirar a guarda TEMP de V7.6.5 para ativá-la implicitamente.
Reusar transação, unicidade e replay. Chave identifica pedido completo, carteira,
sessão e autoridade; retry idêntico retorna original, conteúdo diferente dá
conflito; IDs cancelados/fills/liquidações não se reutilizam.

Backup consistente via SQLite stdlib, antes de escrita manual e ao fim da sessão,
incluindo dados/contextos/autorizações e manifest de hashes; cabeça da cadeia em
local independente com acesso controlado. Recomenda-se manter todos os backups
diários durante o piloto e cópia em outro disco. Restaurar em raiz isolada,
comparar integridade/replay/head/último comando, só então trocar raiz explicitamente.
Perda de confirmação: consultar/repetir mesma chave, não criar outro comando.
Crash pré-commit: rollback. Corrupção, cauda divergente, relógio regressivo ou
backup inconsistente: interromper; hashes locais não provam autenticidade contra
administrador. Objetivo proposto: nenhuma duplicação e perda máxima desde último
backup confirmado; não prometer tolerância a perda de disco antes do ensaio.

Bloquear nova ordem em dado/calendário incompleto, autorização ausente/vencida/
estranha, estado modificado, veto/limite conforme distinção da seção 4.1,
custo/saldo/custódia insuficiente,
evento não suportado ou divergência contábil. Interromper piloto (e grupo comparável)
em corrupção, reconciliação falha, evento corporativo sem tratamento, indisponibilidade
além do prazo ou quebra de proveniência/corte. Continuar consultas com último estado
validado e aviso; nenhuma venda automática de encerramento. Retomada exige causa,
evidência, restauração/reconciliação e decisão humana explícitas. Resultado negativo
isolado não é falha operacional; limite de risco segue política registrada.

## 7. Incrementos mínimos futuros

Os arquivos são candidatos, não autorização para mudar fontes selados. Preservar
V5/V2, fingerprints e replay histórico; qualquer extensão ganha identidade/versão
própria só nos pontos incompatíveis. Nenhuma nova arquitetura de ledger.

| Incremento | Comportamento e componentes/arquivos candidatos | Dependências | Menor verificação significativa / critério de saída |
|---|---|---|---|
| DATA-01 | Importação manual de bundles RAW OPEN/CLOSE, disponibilidade/vintage, calendário cobrindo piloto+D+2 e eventos. Reusar parser `src/pipeline/b3_official.py`, features `scripts/multiasset_radar.py:225`, calendário `src/backtesting/b3_calendar.py`; ponte futura junto a `scripts/paper_ledger.py` | Revisão de R4/R5/R6; confirmar fonte/uso/corte. Fixtures podem ser preparadas sem contratar fonte | Check offline: sessão inválida/fim de cobertura bloqueiam; OPEN/CLOSE/RAW/ADJUSTED e datas de disponibilidade distintos; lacuna/evento detectados. Saída: fonte/calendário/hashes e exemplo prospectivo justificáveis, sem ativar escrita oficial |
| PAPER-02 A | Nova decisão fixture → contexto → validação → autorização de teste → intenção ex-ante → OPEN t+1; benchmark 20% com política própria. Reusar `paper_ledger.py`, cálculos V5/manager, contratos PM V2 como referência, `qualify_paper_ledger.py`, `tests/test_paper_ledger_v765.py` | PAPER-01 revisado nos parâmetros de R1–R7; DATA-01; extensão versionada do acoplamento de sessão/85%/preço. Continua TEMP/sintético | Cesta de cinco ativos, q/limite selados antes de OPEN, autorização vencida/dado ausente/gap bloqueiam; zero operações gera decisão sem ordem. Saída: nenhum fill sem intenção ex-ante nem alteração de V5/V2 |
| PAPER-02 B | D+2/eventos → CLOSE → reconciliação → série/indicadores/comparação. Reusar `view/corporate`, envelope/histórico e `dashboard/paper_ledger_api.py`; consumidores futuros `dashboard/monitoring.js`, `dashboard/portfolio.html`, roteamento `dashboard/server.py` | Incremento A, R6/R8; sessões e eventos conhecidos; adaptar leitura prospectiva separada da fixture | Check de livro conhecido compra/venda/provento/split; E exato, duplicado/reinício sem novo efeito, divergência não publica ponto. Check de períodos em virada de mês/ano, 29/02, lacuna e histórico curto. Saída: backend produz campos/âncoras rastreáveis, GET puro, carteiras não se somam; UI de carteira/DP-02–05 só ao consumir esse contrato |
| PAPER-03 | Raiz durável de ensaio, identidade local, backup/restauração, head independente e runbook manual no documento ativo; escritor do envelope e comandos da qualificação como base, sem promover banco TEMP | PAPER-02 qualificado, R9 e fonte/modelo/limites revisados; revisão independente. Orçamentos externos continuam separados | Matar processo antes/depois do commit, restaurar backup em outro diretório, repetir comando perdido, comparar cabeça/IDs/E e bloquear adulteração/usuário sem acesso. Saída: recuperação ensaiada e gates documentados; ativação continua PAPER-04, com autorização específica |

Cobertura mínima que deve ficar nos checks desses incrementos (não executados aqui):

| Cenário | Resultado verificável |
|---|---|
| Autorização vencida na abertura/emitida depois dela ou processamento fora do prazo | Nenhum fill elegível; diagnóstico e liberação; novo ciclo exige nova decisão. Autorização válida na abertura com dado tardio dentro do prazo usa apenas a intenção já selada |
| OPEN ausente ou fora de limite / CLOSE ausente | Cesta sem fill; após prazo expira; marca incompleta não gera ponto, mantém data anterior |
| Comando duplicado/conflitante | Mesmo pedido/chave retorna mesmo evento/saldos; payload diferente falha |
| Reinício/ACK perdido | Replay recupera intenção/commit; sem duplicar inferência, fill, provento ou liquidação |
| Divergência contábil | E/checkpoint/totais/IDs divergentes bloqueiam escrita e publicação; nenhum acerto automático |
| Evento corporativo | Entitlement data-com/ex-date, recebível líquido/pagamento e split conservam identidade; fração não suportada interrompe; benchmark sem reinvestimento |
| Proposta sem operações / sem decisão | HOLD explícito sem ordem/custo; ausência de decisão identificada; ambas permitem marca/D+2 de estado existente |
| Política benchmark versus agentes | 20% inicial não passa pelo veto/85% dos agentes; mesmos custos/fontes; versão selada mantém resultados anteriores |

## 8. Decisões humanas pendentes e estado da entrega

Na entrega original PAPER-01 nenhum grupo abaixo estava aprovado. Em 14/10/2026,
Lucas aprovou as bases DP-09–DP-15 após a entrega PAPER-03. Estado atualizado:

- R1: finalidade operacional/descritiva, duas carteiras de R$ 100 mil e revisão
  após 20 pregões aceitos; início efetivo na primeira sessão elegível após preparação.
- R2: ausência de rebalanceamento/reinvestimento e proventos em caixa aceitos;
  regras de eventos obrigatórios e saídas excepcionais ainda pendentes.
- R8: ausência de aportes/retiradas aceita; isso não aprova integralmente R8
  nem transforma métricas implementadas em protocolo científico ratificado.
- R9: rotina manual diária e autorização explícita de operações aceitas;
  autenticação, autoridade técnica, recuperação/adoção e gastos continuam pendentes.
- R3–R7 e demais partes de R8/R9: não aprovadas por essa concordância.

A lista original abaixo permanece para rastreabilidade; não reabrir as bases
já aceitas nem interpretar aprovação parcial como aceite integral de um grupo.

1. **Finalidade, capital e horizonte (R1):** aprovar piloto operacional com duas
   carteiras de R$ 100 mil e proposta de **20 sessões elegíveis** como ensaio inicial,
   sem prova de superioridade; duração justificada como amostra operacional curta.
   Ampliação/uso científico exige protocolo independente. Confirmar baseline s0
   efetivo, sem preencher D0 retroativamente.
2. **Política e entrada (R2/R3/R7):** Buy & Hold sem rebalanceamento/reinvestimento,
   inteiros/fracionário, orçamento 20% com custo, buffer 2%, OPEN/slippage zero,
   custo 0,1% pré-IR e caixa sem rendimento; limites/veto dos agentes e política
   independente de benchmark. A extensão de política é bloqueio técnico real.
3. **Dados, tempo e eventos (R4–R6):** aprovar fonte somente após DATA-01 comprovar
   cobertura/uso/disponibilidade, prazo de processamento, confirmação paper D+2
   e tratamento de proventos/eventos. Sem isso não há primeiro fill elegível.
4. **Métricas e comparação (R8):** excluir aportes/retiradas, usar índice base 100,
   períodos incompletos explícitos e grupo comparável separado de H2/sintéticos.
5. **Autoridade, operação e gasto (R9):** Lucas como operador/revisor da autorização
   paper local, raiz/backups/retomada revisados em PAPER-03, revisão independente
   antes de PAPER-04. Dados, infraestrutura e inferências têm tetos/consentimentos
   separados ainda não definidos; não estimar fatura nem acionar caminho pago.

**Estado PAPER-01: bases aprovadas; regras técnicas pendentes.** Não houve
congelamento metodológico, aprovação acadêmica ou ativação. PAPER-02/03 sintéticos
já foram qualificados, conforme seções posteriores. Calendário planejado e
importador local entregues na seção 14; primeiro ZIP/bundle observado pendente.
A proposta consolidada abaixo permite decidir as regras técnicas enquanto o
arquivo não chega. PAPER-04 continua bloqueado até as dependências aplicáveis.

Verificações do PAPER-01: check documental e verificador de preservação existentes;
resultado final registrado no estado ativo. Código/testes e evidências inspecionados,
sem reexecutar suítes, consultar estado H2, abrir Final Test/holdout, inferir,
baixar mercado, operar ou criar banco financeiro persistente.

### 8.1. Proposta objetiva para fechar regras técnicas — 14/10/2026

Consolidação solicitada por Lucas após revisar DATA-01. Vinculada a PAPER-01 e
DP-01/04/05/08/13/15; **DP-01–DP-15 permanecem aceitas, sem nova votação**.
As regras abaixo reutilizam R2–R9; são propostas, não parâmetros aprovados ou
implementação prospectiva qualificada. A coluna final delimita o aceite técnico
que ainda cabe a Lucas. A lista original acima permanece como histórico.

| Tema / referência | Regra recomendada | Justificativa | Decisão pendente de Lucas |
|---|---|---|---|
| Execução — R3 | Uma cesta pendente por carteira; unidades inteiras, inclusive fracionário paper; fill integral ou nenhum, no OPEN RAW da próxima sessão elegível, slippage adicional zero. Quantidades e limites fixos antes da abertura; compra limitada a CLOSE × 1,02, venda a CLOSE × 0,98. Referência reserva C/5 por ativo incluindo custo, sem redistribuir sobras | Reutiliza intenção/reserva/fill qualificados; limita gaps e impede escolher quantidades após conhecer OPEN | Aceitar modelo OPEN paper, convenção de fracionário e buffer de 2%; não equivale a execução/liquidez real |
| Prazos — R4 | Decisão, autorização e intenção seladas antes da abertura-alvo; validade econômica restrita à fase OPEN daquela sessão. Processar a intenção até **12h do dia civil seguinte**, America/Sao_Paulo. Sem dado até o prazo: expirar sem fill e liberar reservas; novo ciclo exige nova decisão/autorização | Admite arquivo diário e rotina manual sem aprovação retroativa; sessão finalizada não é reaberta | Aceitar prazo civil, inclusive fins de semana/feriados; horário/fase precisam de cobertura DATA-01 vigente |
| Custos — R3 | **0,1% do financeiro por perna**, tanto compra quanto venda, nas duas carteiras; centavos HALF_EVEN. Sem IR sobre ganho no modelo inicial; retenções de proventos somente com evidência | Mesma hipótese didática e contabilidade reutilizável; não representa tabela de corretora nem resultado líquido fiscal | Aceitar taxa, slippage zero e exclusão do IR sobre ganho; custo não está aprovado por DP-09–DP-15 |
| Risco — R7, refinada | Valores V5 mantidos como propostas; veto bloqueia aumento do ativo e excesso de limite bloqueia compras da carteira. Permitir apenas vendas de redução elegíveis, preservando controles, conforme seção 4.1. Drawdown bloqueia compras até revisão, sem exigir que a saída apague a perda. Agentes: admissão até 85%; referência: entrada até 100% sem crédito | Reduz exposição existente sem compra disfarçada nem venda descoberta; não prende a carteira por uma perda histórica. Estratégias têm exposições diferentes | Aceitar caminho de redução e não agravamento, revisão pós-drawdown e políticas separadas, além dos valores ainda propostos. Extensão futura versionada; V5/V2 selados intactos |
| Eventos corporativos — R2/R6 | Fonte emissor/B3; registrar data-com, ex-date, pagamento e posição economicamente elegível. Reconhecer direito líquido na ex-date e pagar com evidência; split/bonificação/grupamento preservam base total. Frações, conversões ou evento não suportado bloqueiam ordens/publicação válida até reconciliação | RAW exige eventos para patrimônio correto; evita inventar caixa ou operação compensatória | Aceitar reconhecimento/eligibilidade e bloqueio conservador; saídas excepcionais precisam de decisão explícita. Fonte e tratamento devem ser qualificados |
| Caixa e liquidação — R6/R8 | Caixa sem rendimento; recebíveis não financiam compras, reservas reduzem disponível. D+2 no calendário da Câmara B3, confirmado manualmente por comando identificado `PAPER_CALENDAR_CONFIRMATION`; não é confirmação de corretora. Proventos da referência permanecem em caixa conforme DP-11 | Reutiliza identidade patrimonial e custódia/recebíveis V5; torna saldo utilizável e liquidação rastreáveis | Aceitar rendimento zero, restrições de uso do caixa e confirmação paper D+2. Sem reabrir ausência de aportes/retiradas ou reinvestimento |
| Autorização — R9 | Lucas como operador único via acesso local restrito, com identidade/ACL qualificadas. Comando explícito vincula carteira, proposta/validação/estado por hash, q, limites, custo, política, sessão/fase, emissão e prazos. Alteração do estado aprovado invalida intenção; revogação deixa registro. Aprovação paper e orçamento de inferência são atos separados | Reutiliza CLI/recibos e reduz superfície; nome digitado em `operator` não autentica pessoa | Aceitar operador e modelo local; mecanismo de identidade, revogação e acesso exige qualificação antes de uso. Aprovar esta proposta não autoriza gasto nem ativação |

**Limites técnicos concretos:** o DATA-01 atual aceita RAW de lote padrão
010/02; preço desse instrumento como referência para quantidade fracionária é
uma hipótese paper proposta em R3, não cotação fracionária já validada. A aceitação
dessa convenção precisa constar da política; usar preço do mercado fracionário
exigiria cobertura/importação própria antes de operar. O diário informa OPEN na
precisão de sessão, sem provar segundo exato do negócio; a ponte deve conservar
essa precisão, separar horário planejado de instante observado e nunca antecipar
`available_at`. O prazo R4 precisa ser confrontado com disponibilidade real,
sem simular entrega nem prolongá-lo retroativamente.

Aceite de uma linha fecha somente a escolha técnica nela descrita. Implementação
prospectiva, eventos, autoridade, recuperação e revisão independente continuam
exigindo qualificação; regras não são ativadas pela atualização deste documento.
Canal automático/condições de aquisição continuam em avaliação com reuso antes
de outro downloader; entrada local permanece disponível. Quando Lucas fornecer
o ZIP diário pós-D0, validar aquisição e primeiro bundle observado pelo fluxo
da seção 14. Nenhuma chamada paga, coleta de preços ou ativação nesta consolidação.

### 8.2. Uso diário e base inicial comum — DP-17–DP-19, 14/10/2026

Lucas confirmou a experiência completa pela interface, com cadastro de carteira,
registro de operações atuais/antigas, home integrada, evolução e proventos.
Também confirmou duas escolhas no [documento de direção](DIRECAO_DO_PROJETO.md):

- **DP-18:** agentes e referência começam com as mesmas posições, aproximadamente
  20% por ativo, mantendo R$ 100 mil independentes por carteira. A referência
  continua sem rebalanceamento/reinvestimento; a partir da base comum os agentes
  podem alterar sua carteira. Não usar decisões antigas como ordens iniciais.
- **DP-19:** cadastro pessoal aceita operações reais executadas externamente e
  simulações, sempre identificadas. Data econômica e instante de registro são
  distintos; registro histórico não equivale a autorização prospectiva nem
  envio de ordem real. Carteiras pessoais têm capital/histórico próprios e
  ficam fora do grupo comparativo do piloto por padrão.

**Compatibilização ainda pendente:** R1/R3 descreviam inicialização em caixa e
primeiras alocações distintas, enquanto R7 propõe admissão de exposição até 85%
para agentes. A base comparada agora exige posições comuns próximas de 100%.
Definir a formação da cesta comum, preços/quantidades/custos, sessão e snapshot
de início comparável, preservando o funding e todos os eventos contábeis; não
criar fill retroativo, omitir custos ou converter ensaio sintético em carteira.
Revisar a política de exposição explicitamente antes da ponte operacional,
sem alterar V5/V2 selados, impor vendas automáticas ou reduzir a cesta inicial
dos agentes para caber nos 85%. A resposta de Lucas não aprova os demais limites.

O registro histórico pessoal exige um contrato de escrita/revisão próprio;
não adaptar o contrato prospectivo para aceitar decisões tardias dos agentes.
Reutilizar contabilidade e persistência compatíveis. [APP-01–APP-05](ROADMAP.md#uso-diário-pela-interface--dp-17)
organizam incrementos de uso diário, com estados/proventos e recuperação
verificáveis. A base comparativa e o ciclo dos agentes ainda não foram ativados.
O cadastro/registro pessoal APP-01/02 foi implementado separadamente na seção 15.

## 9. DATA-01 — mecanismo implementado e qualificado offline

**13/10/2026 · DP-01, DP-04 e DP-05.** A implementação local abaixo foi autorizada
como DATA-01; não aprova R1–R9 nem transforma este DRAFT em contrato operacional
aprovado. Estado: **mecanismo qualificado offline; cobertura/fonte oficial pendente**.

[Adaptador](../scripts/pilot_market_data.py) e
[checks executáveis](../tests/test_pilot_market_data.py). Reusam as funções puras
`read_cotahist`, `validate_ohlcv` e `canonical_json`; `paper_ledger.sessions`
fornece somente a lista 2026 e sua guarda de hash, sem chamar escritor/redutor.
Nenhum desses fontes foi editado. Não usar `download`, `prepare`, ajuste yfinance
ou os dados históricos H2 para alimentar este mecanismo.

### Entrada, saída e consumo

Entrada é um manifest JSON local explícito, com **exatamente** estes campos:

```json
{
  "schema_version": 1,
  "file": "SYNTHETIC_NOT_MARKET_DATA.zip",
  "file_sha256": "SHA256_DE_64_HEXADECIMAIS_DO_ZIP",
  "source": "SYNTHETIC_COTAHIST_FIXTURE",
  "nature": "SYNTHETIC_TEST",
  "basis": "RAW",
  "currency": "BRL",
  "instrument": "B3_SPOT_STANDARD_LOT_010_02"
}
```

`file` é relativo ao manifest (ou absoluto), e o hash é comparado aos bytes
antes do parser. ZIP deve conter um único TXT COTAHIST. Só lote padrão/mercado
à vista (`CODBDI=02`, `TPMERC=010`, moeda `R$`) é suportado neste incremento;
fracionário/derivativos/outros tickers não são inferidos nem convertidos.
O padrão seleciona os cinco ativos; `--ticker` restringe explicitamente a seleção.
Exige todas as combinações ticker/sessão solicitadas, com OHLC válido e negócio;
duplicatas (inclusive idênticas) são recusadas. Ausência não recebe preço substituto.
Campos JSON duplicados ou desconhecidos, ADJUSTED e fontes desconhecidas falham.

Para fixtures, `--calendar` aponta a JSON local como este (a lista é completa
**somente para o intervalo sintético indicado por seus extremos**):

```json
{
  "nature": "SYNTHETIC_TEST",
  "source": "SYNTHETIC_CALENDAR_NOT_OFFICIAL",
  "sessions": ["2026-04-17", "2026-04-20", "2026-04-22", "2026-04-23", "2026-04-24"]
}
```

Omitir `--calendar` usa exclusivamente a lista histórica verificada/hash fixado
de 2026, até **31/08/2026**. JSON externo nunca pode declarar calendário oficial.
`calendar_session`, `next_session` e `settlement_session` (D+2) só consultam
elementos presentes, sem regra de dia útil nem horário de abertura. Importar preço
da última sessão coberta não prova cobertura de D+2; essa consulta falha quando
faltam duas sessões futuras. Calendário e dado sintéticos permanecem sintéticos.

```powershell
.venv/Scripts/python.exe -B scripts/pilot_market_data.py --input input.json --calendar synthetic_calendar.json --session 2026-04-17 --session 2026-04-20 --session 2026-04-22 --output bundle.json
```

Saída é JSON novo, nunca sobrescrito. `content` contém fonte/natureza, RAW/BRL,
instrumento, seleção, barras OPEN/HIGH/LOW/CLOSE em strings de centavos, volume
inteiro, hashes original/normalizado, versão e hashes dos parsers, calendário e
revisão. `normalized_sha256` sela as barras selecionadas; `content_sha256` sela
todo o conteúdo econômico/proveniência; `sha256` sela também o recibo de importação.
O ZIP é lido uma vez e o parser recebe uma cópia temporária desses mesmos bytes,
evitando divergência entre hash e arquivo alterado durante o parsing. Volume
inteiro é preservado diretamente porque o parser existente o representa em float.

`import` contém caminhos, hash do manifest, `imported_at` UTC e `available_at`.
Este incremento só suporta **IMPORT_TIME_CONSERVATIVE_BOUND**: ambos os instantes
são a conclusão real da importação. Não aceita publicação anterior declarada
sem verificador de evidência, não usa mtime e não inventa horário econômico OPEN.
Assim um arquivo diário pode ter OPEN histórico, mas não pode ser usado em decisão
anterior à importação. Disponibilidade anterior comprovada é integração futura.

Consumo futuro: `verify_bundle(bundle)` verifica integridade e contratos;
`prices(bundle, sessão, "OPEN" ou "CLOSE", at=instante_com_timezone)` verifica
também disponibilidade e retorna os preços requeridos. O consumidor conserva
fonte/natureza, hashes e recibo do bundle ao referenciar esses preços. Consulta
não escreve nem muda identidade/instantes. Não ligar preços diretamente a ordem
sem os gates prospectivos de PAPER-02.

Reimportar os mesmos bytes/parâmetros preserva `content_sha256`, mesmo com outro
horário/caminho de consulta; o recibo/`sha256` da importação são distintos. Para
retificação explícita, passar `--previous bundle-anterior.json` e novo `--output`:
bytes novos na mesma seleção/fonte/calendário/parser geram `revision=n+1` e
`revision_of=content_sha256` anterior. Repetição dos bytes anteriores mantém n.
Mudança de escopo é recusada como retificação. Não há catálogo global nesta fase:
o operador deve fornecer `--previous` para uma correção; sem ele há uma primeira
importação independente, nunca substituição de arquivo. Conservar os originais.

### Qualificação e bloqueios oficiais

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_pilot_market_data.py -v
.venv/Scripts/ruff.exe check --no-cache scripts/pilot_market_data.py tests/test_pilot_market_data.py
.venv/Scripts/ruff.exe format --check scripts/pilot_market_data.py tests/test_pilot_market_data.py
```

**16 checks aprovados**, com fixtures mínimas geradas em TEMP: cinco ativos/15
barras/3 sessões; ausência, conflito, OHLC/preço inválido, instrumento/moeda,
RAW/ADJUSTED, disponibilidade, fim de semana/feriado sintéticos, D+2 insuficiente,
reimportação/correção, selos/classificação, não sobrescrita, precisão e caminhos
protegidos. Sockets, urllib e yfinance bloqueados durante os checks; CLI também
exercitada em processos novos com rede bloqueada. Primeira tentativa no sandbox
falhou por WinError 5 ao criar arquivos TEMP no Python 3.13; execução isolada fora
do sandbox passou, sem alterar permissões do produto. Não se rodou suíte completa.

Exemplo efetivamente gerado em TEMP: `hfl-data01-example-cnrwyblu`, com
`bundle.json`, `repeat.json` e `revision-2.json`, inputs sintéticos separados e
originais preservados. v1/repetição têm conteúdo
`2e4ebc42a205c39748c5290140fa040852a7b87570f9246d1f734927cabd4ce6`;
v2 tem `547a4449694cc8ab89daade639c06d3e4ae6bcc88ff9b14da6a91dead245585d`.
Artefatos temporários não são evidência científica selada nem persistência oficial.

Fonte real reconhecida pelo contrato: `B3_COTAHIST_LOCAL`/`REAL_UNVERIFIED`, RAW,
com calendário verificado. É declaração local, não autenticação B3/licença.
**Hoje nenhuma sessão real do piloto pode ser importada:** datas anteriores a
D0 são bloqueadas para não importar janelas históricas protegidas; outubro/2027
não têm cobertura comprovada no adaptador. O check de 13/10 retorna
`calendar_session_unavailable:2026-10-13` antes de abrir arquivo de preços.
Os caminhos `data/` e `docs/evidence/` são recusados para entrada/saída externa,
inclusive após resolver links; somente a lista de calendário fixada é lida por
sua função própria. Warm-up usa exclusivamente fixtures sintéticas.

Faltam evidência local autorizada de calendário prospectivo, proveniência/uso da
fonte real e verificação de disponibilidade anterior; não há horários, feed,
eventos corporativos completos, indicadores, UI ou integração financeira novos.
`official_ingestion_ready=false` em toda saída. Próximo incremento: qualificar
calendário/fonte prospectivos no DATA-01; PAPER-02 poderá consumir o contrato em
ensaio sintético, após revisão das escolhas operacionais aplicáveis. Nenhum custo,
buffer, prazo, limite 85% ou autorização entre sessões foi aprovado/resolvido aqui.

## 10. DATA-01 — segundo incremento: evidências B3 e formato diário

**13/10/2026 · DP-01, DP-04, DP-05.** Amplia o mesmo adaptador e seus checks;
não reconstrói o importador. As seções anteriores registram o primeiro incremento
e propostas DRAFT. Estado atual: **documentação de calendário/fonte preservada;
formato diário qualificado offline; cobertura positiva prospectiva e bundle real
ainda bloqueados**. Nenhuma política financeira foi aprovada.

### Artefatos e calendário: o que foi e não foi comprovado

[Catálogo verificável de fontes](evidence/pilot_market_data_2026/sources.json):
nove documentos públicos, URL solicitada/final, documento/versão, instante UTC de
obtenção, escopo, tamanho e SHA-256 dos bytes preservados. Coleta em 13/10/2026
às 23h14–23h24 de São Paulo (14/10, 02h14–02h24 UTC). O catálogo também é fixado
por hash no adaptador, e `source_evidence()` confere todos os artefatos offline.
Isso registra a aquisição por HTTPS nesta tarefa; não equivale a assinatura B3.
Não houve download de arquivo de preços ou busca nas raízes científicas.

| Evidência oficial | Confirmação e limite |
|---|---|
| [OC 041/2026-VNC, 30/06/2026](https://www.b3.com.br/data/files/20/57/01/AA/06A1F910ADC36BE9AC094EA8/OC%20041-2026-VNC%20ERRATA%20-%20CALENDARIO%20DE%20FERIADOS%20EM%202026_PT.pdf), Anexo 1, Quadros A/B, páginas 3–5 | Calendário de feriados/suspensões de 01/01–31/12/2026, incluindo 12/10, 02/11 e 20/11. A retificação de julho diz que os demais quadros permanecem inalterados. Pode ser alterado por comunicação posterior |
| [Regulamento de negociação, 30/06/2025](https://b3.com.br/data/files/0B/D0/80/95/753D0A105BF9020AAC094EA8/Regulamento%20de%20Negociacao%20da%20B3.pdf), art. 30 | A B3 divulga sessões/horários em calendários anuais; prevê interrupção/cancelamento. Não fornece aqui uma lista diária positiva para o recorte do piloto |
| [Grade de ações capturada](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/horario-de-negociacao/acoes/) | Há fases distintas: pré-abertura, negociação, call e after-market. Snapshot de referência, sem vigência congelada por sessão; nenhum horário é usado para autorizar fill/publicação |
| [Anúncio B3 sobre D+1, 05/09/2025](https://b3.com.br/pt_br/noticias/liquidacao-d-1.htm) | Descreve D+2 corrente para ações e migração prevista para fevereiro/2028. Sustenta a referência de ciclo; não prova liquidação individual nem autoriza calcular datas sem calendário coberto |

**Bloqueio preciso:** não foi localizada nesta consulta uma enumeração positiva
de sessões que permita comprovar o intervalo técnico requisitado
**13/10–30/11/2026** e suas duas sessões posteriores, sem inferência por dias úteis.
Esse intervalo é uma solicitação de cobertura, não duração aprovada do piloto.
O ofício obtido comprova exclusões, não uma lista positiva completa. Não se
gerou lista com `weekday`, calendário bancário, observações de um ativo ou
regulamento antigo de outro segmento. Sessões previstas ainda não enumeradas
e sessões efetivamente observadas não são preenchidas a partir dessa lacuna.

`load_calendar("b3-2026")` verifica e consome esse novo artefato documental,
separado da lista histórica e das fixtures. `calendar_session` reconhece
`documented_non_session` para exclusões comprovadas, mas sessão/next/D+2 em
13/10 retornam `prospective_positive_session_coverage_unproven`. Seus mapas de
sessões positivas e observadas ficam vazios. JSON autodeclarado oficial, artefato
ausente/adulterado ou lista re-selada com datas inventadas são recusados.
Calendário histórico continua intacto e limitado a agosto/2026; 2027 não é coberto.

### Fonte, semântica e entrada restrita a uma sessão

A [página de cotações históricas](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)
confirma preços sem ajustes de inflação/proventos, em TXT compactado por ZIP.
O [seletor oficial](https://bvmf.bmfbovespa.com.br/pt-br/cotacoes-historicas/FormSeriesHistoricasArq.asp),
capturado sem acionar downloads, oferece séries anuais, mensais e **diárias do
ano corrente**, com nomes `COTAHIST_DDDMMAAAA.ZIP`. Preferir o diário pós-D0.
Não passar um anual inteiro ao parser; este incremento não implementa recorte
de preços históricos de arquivos anuais/mensais.

O [layout preservado](evidence/pilot_market_data_2026/cotahist_layout_20201005.pdf)
tem histórico de revisão 02 em 05/10/2020, embora a capa conserve rev01/2017.
Registros 00/01/99, 245 bytes. Compatibilidade reutilizada: data 3–10, ticker
13–24, CODBDI 11–12, mercado 25–27, moeda 53–56, PREABE 57–69, PREULT 109–121,
FATCOT 211–217 e ISIN 231–242 (posições inclusivas, iniciando em 1).
`OPEN` significa PREABE; `CLOSE` mantém o mapeamento do parser para PREULT,
**último negócio**. Não comprova instante exato/call de fechamento. `volume`
é quantidade QUATOT, conforme o parser, e não montante financeiro VOLTOT.

No manifest, acrescentar ao contrato anterior:

```json
{"format": "COTAHIST_DAILY_245", "file_session": "2026-10-13"}
```

Esses campos identificam compatibilidade, nunca autenticam a origem. O adaptador
V2 exige uma só sessão selecionada e verifica a data de **todo registro 01**,
inclusive de instrumentos não selecionados, antes de chamar `read_cotahist` ou
interpretar preços. Qualquer pré-D0 bloqueia; outra sessão no arquivo diário
também bloqueia, mesmo se renomeado. Mantém hash integral de origem e seleção
explícita; não produz recorte financeiro oculto. Exige moeda BRL/R$, CODBDI 02,
mercado 010, FATCOT unitário `0000001`; preserva ISIN nas barras. A verificação
de ISIN é sintática, não autenticação nem conferência contra cadastro observado.
Fatores/lotes incompatíveis são recusados sem ajustar preços silenciosamente.
Fixtures legadas continuam disponíveis; o contrato diário foi qualificado com
novas fixtures explicitamente sintéticas, sem warm-up real.

### Proveniência, disponibilidade e uso

| Classificação | Critério no adaptador |
|---|---|
| `SYNTHETIC_TEST` | Fixture identificada; continua sintética mesmo com formato e campos B3 corretos; não aceita ID de aquisição como promoção |
| `REAL_UNVERIFIED` | Aparência/formato compatível declarado por `B3_COTAHIST_LOCAL`; não atesta aquisição B3 nem cria sessão observada global |
| `ORIGIN_DOCUMENTED_NOT_AUTHENTICATED` | Reservado a `B3_COTAHIST_DOCUMENTED` com ID de aquisição em catálogo independente fixado/revisado, vinculado ao hash do arquivo. Não basta escrever fonte/URL/ID no manifest; não significa assinatura digital ou licença |

O catálogo de aquisições de preços está **vazio**: nenhum arquivo real pós-D0
foi explicitamente disponibilizado nesta solicitação. Logo nenhum bundle real
foi validado e nenhuma aquisição documentada pode ser aceita agora. Registrar
uma aquisição futura exige preservar URL/origem, evidência de obtenção, instante,
bytes/hash e revisão independente do manifest de preços, por extensão explícita
do catálogo; não por atualização silenciosa de campo. Não há coletor de preços.

Não foi encontrada garantia específica de horário de publicação nem cronograma
de retificações do COTAHIST nos documentos consultados. Data de geração do header
não é prova de publicação/disponibilidade. `available_at=imported_at` real em UTC
continua sendo o único limite conservador aceito; `published_at` livre é recusado.
Repetição conserva identidade dentro da mesma versão do adaptador, e correções
continuam exigindo `--previous`/novo arquivo. V1 permanece legível; reimportação
sob V2 tem versão de parser distinta e não é uma correção silenciosa da V1.

A página de cotações capturada veda coleta automatizada, incluindo IA; os
[termos oficiais](https://www.b3.com.br/pt_br/termos-de-uso-e-protecao-de-dados/termos-de-uso/)
limitam usos pessoais/comerciais e difusão/redistribuição, sem garantir pontualidade
ou exatidão. **Não se presume autorização de uso/distribuição para o piloto/TCC**
a partir de download gratuito. Nenhum serviço foi contratado e nenhum contato
externo foi enviado; aplicabilidade ao uso pretendido precisa ser esclarecida
antes de obter/divulgar dados reais. Consulta de documentação não ativou coleta.

### Verificação e dependências

Mesmos comandos da seção 9: **24 checks aprovados (16 anteriores + 8 novos)**,
rede bloqueada; lint/formatação aprovados. Cobrem documentos ausentes/adulterados,
autodeclaração de calendário, D+2 coberto e limite preservados, bloqueio prospectivo,
diário pós-D0, preços históricos malformados barrados antes do parser, fator/ISIN,
proveniência sem promoção e disponibilidade sem comprovação. Não se rodou suíte
completa. CLI V2 em processos novos gerou cinco barras sintéticas em TEMP
`hfl-data01-daily-frzzj1yg`; reimportação conservou
`b586729f500780064bd82cf324d3e0ffb810fa5d8debc409dfaf8405d45f4ba7`.
O exemplo V1 anterior foi verificado sem reescrever seus bytes.

Para PAPER-02: comprovar sessões previstas/liquidação e horários aplicáveis;
receber arquivo diário real pós-D0 explicitamente autorizado, documentar aquisição
e esclarecer uso; validar primeiro bundle observado com disponibilidade causal.
Eventos corporativos e escolhas operacionais do DRAFT continuam pendentes.
O fluxo sintético pode exercitar a ponte futura; não resolve as dependências
oficiais. `official_ingestion_ready=false` permanece em toda saída.

## 11. PAPER-02 — ensaio integrado exclusivamente sintético

**Implementado em 14/10/2026; não aprova as recomendações R1–R9.** Atende
DP-01/03/04/05/07 com duas carteiras independentes e projeção calculada pelo
backend. Evidência real pendente em DATA-01 bloqueia ativação oficial, não este
ensaio autorizado. Não há conexão com preços, saldos, pareceres ou decisões H2,
Radar/PM nem acesso ao holdout.

### Execução, contratos e reuso

```powershell
.venv/Scripts/python.exe -B scripts/qualify_pilot_paper.py
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_pilot_paper.py -v
```

[Ponte](../scripts/pilot_paper.py), [qualificador](../scripts/qualify_pilot_paper.py)
e [checks](../tests/test_pilot_paper.py). O comando cria uma pasta nova
`TEMP/hfl-paper-paper02-*`, imprime seu caminho e deixa `ledger.sqlite3`,
`projection.json`, exportações separadas e oito diretórios de arquivo/manifest/
bundle sintéticos. Não sobrescreve saídas anteriores nem grava em `data/`.
A pasta contém somente dados descartáveis de teste; persistência durável,
backup/restauração de disco e acesso autenticado continuam em PAPER-03.

Contrato novo: `HFL-PILOT-PAPER-SYNTHETIC-V1`; esquema físico SQLite V1 mantido.
São reutilizados, sem editar fontes antigos:

- DATA-01: importação local, parser COTAHIST, OHLCV, bundle RAW, hashes,
  seleção, classificação e disponibilidade conservadora real da importação.
- V5: Decimal/HALF_EVEN, operações, reservas, custos, fill, custódia, base,
  recebíveis, liquidação, marcas, patrimônio e identidade contábil.
- V5 manager: risco/covariância, 60 retornos/252, com 61 preços ajustados de
  warm-up inteiramente sintéticos e calendário explícito de teste. Não há
  indicadores novos ou pareceres favoráveis inventados. O produtor identificado
  `SCRIPTED_TEST_NO_AGENT_OPINIONS` é roteiro, sem inferência nem validação de
  comitê real; integrar agentes/pareceres/vetos reais exige outro incremento.
- V7.6.5: envelope selado, cadeia/IDs, replay/checkpoint, transações SQLite,
  idempotência, rollback, confirmação perdida e guarda TEMP original. Projeção
  segue os conceitos de carteira, história reconciliada e consulta sem escrita.

`bind` reutiliza o mesmo objeto de bytecode das funções com namespace privado
de dependências explícitas. Não usa `exec`, não altera fonte, não monkeypatcha
globais e não muda `multiasset_portfolio.POLICY`. `Store` herda criação/conexão/
schema/load, vinculando localmente redutor/replay/identidade; os contratos antigo
e novo recusam eventos cruzados. Fingerprints dos componentes ficam no evento
de criação e são conferidos no replay. Mudar implementação exige versão/revisão
explícita; não migrar silenciosamente o banco temporário anterior.

### Parâmetros de teste e relógios

O evento inicial preserva `test_parameters()` completo: R$ 100.000,00 por
carteira, fee 0,001 por perna, HALF_EVEN, quantidades inteiras, buffer de compra/
venda 2%, slippage adicional zero, D+2 no calendário sintético. Agentes conservam
85% exposição, 40% concentração, 35% volatilidade, 20% drawdown, 100% giro,
1% teto de custo e dez operações. Referência usa exposição até 100%, sem crédito,
uma entrada de cinco alvos de 20%, orçamento C/5 incluindo custos por ativo,
sem redistribuir sobras e sem operações voluntárias posteriores. Concentração
posterior da referência pode derivar; não se aplicam seus próprios pareceres
ou os limites estatísticos dos agentes. Saldo, custódia, inteiros, limites de
preço/custo, autorização, calendário e integridade continuam obrigatórios.

As sessões **03/11–12/11/2026 (oito)** e cobertura extra **13/11** são fixtures,
não afirmação de sessões B3. Dias de semana usados para construir o warm-up são
rotulados sintéticos. Não ampliam a lista histórica oficial nem o calendário H2.
Horários de cenário: OPEN 10h, expiração econômica 10h05, CLOSE 18h, liberação
da fixture 18h05, processamento 18h10, decisão 18h20, autorização 18h30, intenção
18h35, limite de processamento 23h na sessão-alvo; todos `-03:00`. **Não são
horários/fases B3 verificados, aprovações humanas reais ou prazos aprovados.**

Três relógios permanecem separados: `available_at=imported_at` real do DATA-01;
`recorded_at` real do SQLite; e instantes econômicos/decisão/autorização/liberação/
processamento do relógio simulado. `fixture_released_at` é gate adicional de
simulação, não `published_at` nem evidência de publicação. Fixture futura pode
ser importada agora porque é criada para teste; o roteiro só consome CLOSE t
na decisão e OPEN t+1 no fill. Não se alega conhecimento de mercado futuro.
Fill conserva `economic_at=null`, precisão `SESSION_OPEN`, sessão-alvo, horário
de OPEN explicitamente de teste, recibo/bundle, autorização e processamento.

### Sequência qualificada e projeção

Importar bundle → CLOSE/reconciliar t → roteiro explícito TRADE/HOLD → validar
contra último estado reconciliado e dados disponíveis → autorizar e reservar
antes do OPEN seguinte. Quantidades/limites/tetos ficam selados em t; prévia
usa limites autorizados, nunca o OPEN conhecido. O fill exige a mesma intenção/
estado reservado, autorização ex-ante vigente na fase econômica, sessão-alvo,
disponibilidade até processamento, prazo separado e todos os preços dentro dos
limites. A cesta é atômica. Marcar OPEN é a única transição autorizada do estado
reservado; outra mudança invalida o vínculo. Reconciliar CLOSE publica um ponto
imutável; confirmações D+2 são identificadas como simulação, nunca corretora.

`paper02-scripted-agents`: HOLD inicial em caixa; compra 100 PETR4 em 05/11;
venda 40 em 10/11 após liberação da custódia; mantém 60. Referência
`paper02-equal-weight-reference`: compra cinco ativos em 04/11 e mantém.
Compras e venda liquidam dentro da cobertura, inclusive venda em 12/11.
Ausência de proposta é `NO_DECISION`, diferente de HOLD validado sem ordens.

`projection.json` selado contém catálogo, estratégia/classificação, fonte/bundle/
sessão, patrimônio, caixa liquidado/disponível/reservado/recebível, quantidades,
base, marcas RAW e pesos, alvos da referência, custos, trades com vínculos e
relógios, liquidações, decisões, snapshots, variação em R$/%, diária/acumulada
e séries comparativas base 100 na primeira sessão reconciliada comum. Não soma
carteiras. Sem período completo, mês/ano/12 meses ficam `INSUFFICIENT_HISTORY`;
sem CLOSE, resumo/período corrente fica `UNAVAILABLE`, com último ponto válido
datado separado. Nenhum dado ausente vira zero, fill ou patrimônio fictício.

Evento corporativo não suportado registra motivo e bloqueia a sessão e a
continuidade; cancelar reserva permanece permitido. Não há ajuste, provento,
entitlement, pagamento ou retomada fictícia. O teste de bloqueio não demonstra
cobertura corporativa. Não há UI, servidor, scheduler ou execução oficial.

### Resultado financeiro do cenário

| Carteira sintética | Patrimônio final | Caixa liquidado | Posições a CLOSE | Custos acumulados | PnL realizado + não realizado | Base 100 |
|---|---:|---:|---:|---:|---:|---:|
| Agentes roteirizados | R$ 100.039,36 | R$ 97.594,36 | R$ 2.445,00 | R$ 5,64 | R$ 8,77 + R$ 30,59 | 100,03936 |
| Referência 20% inicial | R$ 101.744,07 | R$ 1.878,57 | R$ 99.865,50 | R$ 98,03 | R$ 0,00 + R$ 1.744,07 | 101,74407 |

Sem reservas/recebíveis/custódia pendentes ao fim. Para cada carteira/snapshot:
`E=S+B+ΣQ×RAW = C+realizado+renda+não realizado`. Os resultados são propriedades
da fixture, sem evidência de vantagem financeira ou executabilidade real.

Checks direcionados e preservação estão registrados no [estado atual](ESTADO_ATUAL.md).
Próximo incremento: conectar este JSON sintético ao seletor, cartões, posições
e gráfico da tela inicial; manter modo/fonte/sessão e indisponibilidade visíveis.
Ativação oficial continua dependente de revisão R1–R9, calendário/fases/horários
e fonte/acesso real DATA-01, agentes/autoridade reais, eventos corporativos e
PAPER-03. Nenhuma dessas pendências é resolvida por passar fixtures.

## 12. UX-M3/M5 — tela inicial demonstrativa integrada

**Implementada em 14/10/2026, ligada a DP-02–DP-05.** A abertura `/` informa
“Carteira multiativos ainda não iniciada”, sem saldos sintéticos apresentados
como oficiais. O usuário escolhe “Explorar demonstração com dados sintéticos”
ou usa `/?demo=1`. Selo sintético permanece na página durante a rolagem e há
saída para `/`. São mostrados intervalo/sessão de cenário, nunca “hoje”.
H2/consultivo V2 permanecem em suas jornadas e não entram nesta comparação.

### Preparação explícita e consulta

```powershell
.venv/Scripts/python.exe -B scripts/prepare_pilot_demo.py
.venv/Scripts/python.exe -B scripts/serve_dashboard_keyless.py 8097
```

Abrir `http://127.0.0.1:8097/` ou, explicitamente,
`http://127.0.0.1:8097/?demo=1`. Preparação reutiliza o qualificador PAPER-02
em TEMP, sem outro simulador; deixa somente a exportação demonstrativa selada
`data/platform/pilot-demo.json` (área gerada já ignorada pelo Git). SQLite continua
em TEMP e é descartado ao preparar. GET não abre SQLite, grava eventos, executa
qualificador, inferência ou avanço de sessão. Arquivo existente é reutilizado
após verificação e nunca sobrescrito silenciosamente. Nova exportação deve usar
novo caminho via `--output` e configuração explícita `HFL_PILOT_DEMO` do servidor.
Nenhum caminho é aceito pela URL; sem arquivo válido, não há fallback financeiro.

[Preparador](../scripts/prepare_pilot_demo.py), [API](../dashboard/pilot_api.py),
[página](../dashboard/platform.html), [JavaScript](../dashboard/platform.js),
[CSS](../dashboard/platform.css) e [checks](../tests/test_pilot_home.py).
`GET /api/portfolio/pilot` retorna carteira oficial ainda não iniciada.
`GET /api/portfolio/pilot?demo=1` aceita apenas `wallet`, `session`, `period`;
carteiras/sessões/valores inválidos e campos duplicados são recusados.
Períodos: `day`, `since_start`, `month`, `year`, `last_12_months`.

Exportação `HFL-PILOT-DEMO-EXPORT-V1`, schema 1, contém os dois envelopes selados
e a projeção PAPER-02. A leitura verifica schema, identidade, classificação
`SYNTHETIC_TEST`, ativação oficial falsa, fingerprints, replay/checkpoints e
igualdade exata da projeção recalculada. Cache limitado por bytes/fingerprints;
bytes relidos em todo GET para detectar adulteração, inclusive após consulta
válida. API publica apenas campos necessários: sem journals, contexto de risco,
autorizações privadas ou caminhos de arquivos. Hash não autentica origem real;
o contrato aceita somente esta demonstração sintética.

### Métricas, datas e gráfico

O leitor da interface calcula dinamicamente os períodos da seção 5, preservando
o contrato legado `pilot_paper.projection` e suas evidências. MTD exige última
sessão anterior ao mês; YTD, última sessão do ano anterior; 12 meses usa data
civil com 29/02 → 28/02. Diário exige fechamento imediatamente anterior; s0 é
baseline, sem retorno diário fictício. Desde início usa C autorizado. É exigida
cobertura do calendário e cadeia completa de snapshots entre âncora e sessão.
Âncora ausente não é substituída por ponto mais antigo. Lacuna gera indisponível;
período anterior a s0/sem cobertura gera histórico insuficiente. Resultado parcial
“desde o início” só aparece separado quando sua própria cadeia está completa.

Referência financeira padrão é a **última sessão reconciliada válida**, mesmo
com sessão posterior pendente. Selecionar sessão sem snapshot oculta os saldos;
não usa marca anterior, horário do GET ou zero como substituto. Estados vazio,
carregando, erro, integridade inválida e história insuficiente são explícitos.
Revisão de requisição/AbortController impede resposta antiga de sobrescrever
nova seleção; erro limpa conteúdo financeiro anterior.

Chart.js local recebe duas séries base 100 calculadas pelo backend, na primeira
sessão comum efetivamente reconciliada. Calendário entre essa base e a sessão
selecionada permanece no eixo, com `null` onde faltar snapshot e `spanGaps=false`.
Uma observação não mostra curva. Carteira selecionada tem texto, espessura e
traço próprios; tooltip inclui sessão/índice/patrimônio e há tabela acessível.
Não soma patrimônios, anualiza retorno ou afirma superioridade.

Os cinco ativos vêm dos bundles RAW ligados aos snapshots. Sem posição continua
distinto de posição existente; preço por ação/variação da sessão ficam separados
do valor e da mudança de valor da posição (que pode incluir operações). Quantidade,
peso atual, custo médio e não realizado aparecem em tabela. Referência mostra
20% como **alvo inicial**, ao lado dos pesos atuais calculados, sem alocação fixa.

### Verificação e limites

21 checks da interface/leitura (incluem JS real com respostas fora de ordem),
29 PAPER-02 preservados e nove de regressão direcionada do shell/HTTP/tema/
ajuda/gatilhos consultivos passaram. Verificação Chrome real cobriu abertura
padrão, entrada/saída e link explícito, ambas carteiras, período parcial,
sessão sem snapshot, ausência/corrupção/recuperação da exportação, desktop e
celular 390 px, foco/teclado e tabelas roláveis. Capturas e comandos estão no
[estado atual](ESTADO_ATUAL.md#ux-m3m5--tela-inicial-de-carteiras-14102026).

Não é qualificação completa de leitor de tela/zoom 200% nem ativação oficial.
PAPER-01 continua DRAFT; fonte/calendário/fases reais, decisões/autorização reais,
eventos corporativos e persistência/backup PAPER-03 continuam pendentes. Não
promover arquivo sintético por troca de rótulo. Próximo incremento operacional:
qualificar essas dependências e conectar uma fonte autorizada ao contrato de
consulta, mantendo modo demonstrativo separado.

## 13. PAPER-03 — persistência e recuperação do ensaio sintético

**14/10/2026 · DP-01–DP-05/07.** [CLI local](../scripts/pilot_trial.py) e
[checks reproduzíveis](../tests/test_pilot_trial.py). Esta entrega qualifica
durabilidade e recuperação de **SYNTHETIC_TEST**, com `official_activation=false`.
PAPER-01 permanece DRAFT; ativação e revisão independente continuam separadas.

### Armazenamento e continuidade

A única área admitida pelo adaptador é `data/platform/paper-synthetic/`, dentro
do projeto; `--root` escolhe uma subpasta exclusiva. Caminhos absolutos e
resolvidos precisam permanecer nessa área; links/junctions são recusados.
H2, Radar, PM, evidências e `.git` ficam fora da área autorizada. Criação recusa
qualquer diretório existente, inclusive inicialização interrompida; não apagar
nem reutilizar automaticamente um destino incerto. A guarda TEMP dos escritores
antigos permanece intacta. Nenhum parâmetro HTTP escolhe armazenamento.

O SQLite contém identidade UUID do ensaio, classificação, schema físico V1 com
duas tabelas adicionais, fingerprints versionados, calendário e todos os bundles
normalizados sintéticos, eventos/checkpoints originais e recibos de comandos.
Os ZIPs de fixture são gerados/importados em TEMP pelas guardas DATA-01 e depois
descartados; os bundles completos e hashes necessários ao replay ficam no banco.
Retomar não reimporta fixtures nem reconstrói eventos a partir do roteiro.
Mudança de código pinado recusa retomada; não há migração automática.

Reutiliza Store/replay/envelope/idempotência/transações V7.6.5, redutor e motor
V5 via ponte PAPER-02, reconciliação e projeção existentes. O qualificador
PAPER-02 apenas extraiu seu corpo de sessão em `advance_session`; o demonstrador
TEMP continua usando a mesma sequência. Um adaptador de conexão deixa o Store
executar dentro de uma única transação `BEGIN IMMEDIATE`, `synchronous=FULL`.
Eventos das **duas** carteiras, checkpoints e recibo de sessão confirmam juntos.
Antes de escrever, confere schema/triggers, integridade SQLite, identidade,
fingerprints, selos, cadeia, replay/checkpoint, inputs, recibos e reconciliação.

`init` inclui CLOSE/reconciliação e decisões da primeira sessão (03/11).
`advance` recebe próxima sessão e ID explícitos; processa somente essa sessão.
Identificador confirmado repetido retorna o recibo original sem efeitos; mesmo
ID com outra sessão falha. Outra chave não permite repetir sessão concluída.
IDs de eventos, ordens, propostas e autorizações são preservados. Pré-condição
incompleta ou erro interrompe a transação, sem marcar sessão como concluída ou
reparar saldos. Concorrência é serializada pelo SQLite, com espera limitada.

### Runbook curto

Executar na raiz do projeto; cada linha inicia e encerra um processo Python.
Escolher nomes novos para `$ensaio` e `$restaurado` ao repetir o ensaio.
As datas abaixo pertencem exclusivamente à fixture, não a pregões reais B3.

```powershell
$ensaio = 'data/platform/paper-synthetic/meu-ensaio'
$restaurado = 'data/platform/paper-synthetic/minha-restauracao'
.venv/Scripts/python.exe -B scripts/pilot_trial.py init --root $ensaio
.venv/Scripts/python.exe -B scripts/pilot_trial.py advance --root $ensaio --session 2026-11-04 --command-id sessao-04
.venv/Scripts/python.exe -B scripts/pilot_trial.py advance --root $ensaio --session 2026-11-05 --command-id sessao-05
# Todos os processos anteriores encerraram. Conferir e continuar em processos novos.
.venv/Scripts/python.exe -B scripts/pilot_trial.py verify --root $ensaio
foreach ($sessao in @('2026-11-06','2026-11-09','2026-11-10','2026-11-11','2026-11-12')) {
    .venv/Scripts/python.exe -B scripts/pilot_trial.py advance --root $ensaio --session $sessao --command-id "sessao-$sessao"
    if ($LASTEXITCODE -ne 0) { throw 'Avanco recusado; consultar verify e preservar os arquivos.' }
}
.venv/Scripts/python.exe -B scripts/pilot_trial.py export --root $ensaio
.venv/Scripts/python.exe -B scripts/pilot_trial.py backup --root $ensaio --name completo
.venv/Scripts/python.exe -B scripts/pilot_trial.py restore --root $restaurado --from-backup "$ensaio/backups/completo" --compare-root $ensaio
.venv/Scripts/python.exe -B scripts/pilot_trial.py verify --root $restaurado
# Mesmo pedido confirmado: o recibo original volta, sem duplicar eventos.
.venv/Scripts/python.exe -B scripts/pilot_trial.py advance --root $ensaio --session 2026-11-12 --command-id sessao-2026-11-12
```

Consultar `verify` após qualquer confirmação perdida; repetir **mesma sessão e
mesmo ID**. Não gerar ID novo para contornar conflito. Em corrupção, preservar
diretório, interromper escrita e comparar um backup em destino novo. Inicialização
interrompida exige outro nome, sem limpeza automática do destino anterior.

### Publicação e leitura

`export` verifica o banco na mesma transação usada para capturar ambas carteiras,
serializada com escritores. Grava arquivo temporário no próprio diretório,
flush/fsync, verifica pelo leitor existente e faz `os.replace` controlado de
`projection.json`. Falha antes da substituição preserva exportação anterior;
nenhum saldo de uma sessão parcialmente confirmada é publicado. Avançar não
atualiza a exportação implicitamente: sua sessão continua explícita até novo
`export`; não confundir arquivo íntegro com atualização automática.

Formato `HFL-PILOT-DEMO-EXPORT-V1` e leitor `dashboard/pilot_api.py` reutilizados.
Para consultar esse ensaio, em processo de servidor separado configurar:

```powershell
$env:HFL_PILOT_DEMO = (Resolve-Path "$ensaio/projection.json").Path
.venv/Scripts/python.exe -B scripts/serve_dashboard_keyless.py 8098
```

Abrir `http://127.0.0.1:8098/?demo=1` ou consultar
`GET /api/portfolio/pilot?demo=1`. GET continua somente leitura, sem abrir SQLite,
iniciar avanço, gerar exportação ou aceitar caminho na URL. Sem a configuração,
a demonstração anterior `data/platform/pilot-demo.json` permanece selecionada.
Nenhum rótulo vira oficial; o servidor é responsável por apontar explicitamente
para a exportação do ensaio desejado. Não houve reformulação da interface.

### Backup, restauração e limites

`backup --name` usa **SQLite Connection.backup**, partindo de uma transação de
leitura consistente; não copia arquivo de banco ativo. Destino novo recebe
SQLite e `manifest.json` publicado ao final: classificação/identidade/schema,
fingerprints, inputs normalizados, sequência/cabeça de cada carteira, hash do
banco e hash do snapshot integral (eventos, IDs, checkpoints, comandos, saldos,
posições, história e projeção). Backup sem manifest válido não é restaurável.

`restore` exige backup e raiz corrente de comparação explícitos; não sobrescreve
diretório existente. Verifica hashes, integridade, schema, replay, reconciliação,
prefixos de eventos/recibos e compara integralmente a cópia restaurada com o
snapshot do backup. `restoration.json` informa **CURRENT na comparação** ou
**STALE**, cabeças comparadas e sessões posteriores ausentes. A raiz corrente
fica intacta. Restaurações são cópias de conferência: avanço e publicação nelas
são recusados. Não há troca automática da raiz corrente nem promoção de backup
antigo. Recuperar para consulta está qualificado; adotar uma cópia como escritor
corrente requer procedimento explícito futuro, preservando eventos posteriores.

Backups desta etapa ficam no mesmo volume: não demonstram recuperação de perda
de disco. Perda máxima recuperável é o intervalo após o último backup íntegro;
sem backup externo não há proteção contra perda de toda a pasta. Hashes locais
detectam divergências, mas não são assinatura externa, cabeça independente ou
resistência a quem possa alterar todos os arquivos/código. Não houve teste de
queda de energia, hardware defeituoso, ACL sob outro usuário ou autenticação
humana. Publicação atômica foi qualificada para processos/arquivos locais,
sem prometer durabilidade de rename em todos os sistemas de arquivos.

Acesso de escrita é CLI local e contenção de caminhos. Na inspeção Windows,
a raiz de ensaio pertence a `LUCAS\LUCAS`; `mkdir(mode=0o700)` neste Python/Windows
produziu ACL explícita (entradas não herdadas), com controle ao proprietário,
SYSTEM e Administradores. Nenhuma permissão de outra pasta foi
alterada, nenhuma conta criada. Administradores continuam tendo acesso; usuário
de ambiente não autentica pessoa. Autorizações dos eventos permanecem
`SYNTHETIC_TEST_OPERATOR`, sem qualificação de autorização financeira real.

Checks e evidência executada estão no [estado atual](ESTADO_ATUAL.md).
As bases DP-09–DP-15 foram aceitas após esta entrega. O próximo piloto continua
dependente das demais decisões PAPER-01/R1–R9,
fonte/uso/calendário planejado e evidência observada/fases/disponibilidade/D+2 DATA-01, eventos
corporativos, produtor de decisões e autoridade autenticada, procedimento de
adoção/backup independente e revisão independente antes de PAPER-04. Esta
persistência sintética não aprova políticas financeiras, inferências ou operação.

## 14. DATA-01 — calendário planejado e importação local versionados

Entrega de **14/10/2026**, vinculada a **DP-01/04/05/06/08/13/15 e DATA-01**,
como preparação de PAPER-04. Resultado: arquivo diário disponibilizado → registro
de aquisição → validação → bundle RAW → consulta OPEN/CLOSE, sem carteira,
ordem ou alteração dos contratos sintéticos. **Mecanismo qualificado offline;
primeiro arquivo/bundle observado ainda pendente.** Lucas confirmou que não
baixou nenhum ZIP diário para este piloto. Não há aquisição real presumida.

[Extensão e CLI](../scripts/pilot_observed_data.py) e
[checks](../tests/test_pilot_observed_data.py). Reutilizam o parser RAW e o bytecode
das funções compatíveis de importação/validação/consulta de `pilot_market_data.py`,
com dependências vinculadas em namespace privado pelo helper `pilot_paper.bind`.
Não alteram esses módulos, seus fingerprints nem as evidências anteriores.
O leitor antigo recusa o novo bundle; integração financeira exige contrato próprio.

### Calendário: planejamento, ocorrência e liquidação

O [catálogo documental versionado](evidence/pilot_market_data_2026/observed_v1/sources.json)
registra URLs finais, versões, obtenção UTC, bytes e hashes. Sua versão fixada é
`79ea81a13a7854baa8db4d6908fb9a2c2c4d5297d7254db9bd8d99b5db77f632`.
Novos documentos ficam em `observed_v1`; documentos anteriores são referenciados
por hash, sem regravação. Divergência documental ou calendário refeito pelo
operador bloqueia a consulta; nova regra exige nova versão explícita.

| Aspecto | Cobertura e limite |
|---|---|
| Regra regular | Segunda a sexta documentada na página de ações do participante Itaú/íon; página B3 UP2DATA corrobora a semana do serviço, mas não estabelece prazo de COTAHIST. Esta base e sua limitação estão explícitas no catálogo; não se alega enumeração positiva oficial de pregões |
| Exceções do segmento | OC 041/2026-VNC ERRATA, 30/06/2026: exclusões de negociação e Câmara B3 para ações à vista, abertura em 09/07, escopo distinto de câmbio/derivativos agrícolas/CSD2. Revisão de comunicados até 14/10 não identificou outra exclusão aplicável; não garante ausência de aviso não localizado ou futuro |
| Sessões planejadas | 13/10–31/12/2026: **53** datas derivadas, última em 30/12. Calendário `DOCUMENTED_PLAN_NOT_OBSERVATION`; nenhuma data transforma-se em observação por passagem do tempo |
| Negociação versus liquidação | Listas e regras separadas, embora coincidam nesta cobertura; D+2 conta exclusivamente dias da Câmara B3. Não comprova liquidação realizada; não extrapola para 2027 |
| Próxima sessão / D+2 | 14/10 → próxima 15/10, D+2 16/10; 19/11 → D+2 24/11; 30/11 → D+2 02/12. Consulta de próxima/D+2 em 30/12 bloqueia por cobertura insuficiente |
| Horários | OC 005/2026-PRE, 24/02, vigente desde 09/03; fases centrais revisadas apenas para 13–14/10: pré-abertura 09:45–10:00, contínuo 10:00–16:55, call 16:55–17:00, America/Sao_Paulo. Corte de revisão não é expiração oficial. Fora dele: `UNAVAILABLE_VIGENCY`. Leilão pode estender; after-market e fases excepcionais não modelados |
| Ocorrência e instrumentos | `observations` está vazio. Um diário futuro registrará evidência reportada de sua sessão e presença de instrumentos; ausência de ticker não prova bolsa fechada. Presença não prova todo o calendário nem negociação válida: volume/OHLC são conferidos na importação |

Fontes primárias preservadas: [manual vigente de negociação](https://www.b3.com.br/data/files/CF/D0/64/95/753D0A105BF9020AAC094EA8/MPO%20de%20Negociacao%20da%20B3.pdf),
[calendário B3/2026](https://www.b3.com.br/data/files/20/57/01/AA/06A1F910ADC36BE9AC094EA8/OC%20041-2026-VNC%20ERRATA%20-%20CALENDARIO%20DE%20FERIADOS%20EM%202026_PT.pdf),
[horários OC 005](https://www.b3.com.br/data/files/E3/B2/C2/12/BC09C910F37907C9AC094EA8/OC%20005-2026%20PRE%20NOVOS%20HORARIOS%20DE%20NEGOCIACAO_PT.pdf),
[ações íon](https://www.ion.itau/investimentos/produtos/acoes/),
[semana do serviço UP2DATA](https://www.b3.com.br/en_us/market-data-and-indices/data-services/up2data/helpdesk/information-delivery.htm).
Horários são janelas planejadas, sem substituir abertura/fechamento observados
ou disponibilidade dos preços. A lista histórica e o `b3-2026` anteriores
mantêm suas limitações; esta extensão não os modifica nem reutiliza o calendário H2.

### Aquisição existente e separação RAW / ajustado

Avaliação por leitura do código e callers, **sem executar os fluxos**:

| Componente | Reaproveitamento mínimo | Condição/limite |
|---|---|---|
| [justfile](../justfile) `run-pipeline`, `update-all`, `run` | Comandos de referência, sem uso nesta entrega | Executam ETL com download, indicadores e carga; não são entrada isolada de RAW diário |
| [b3_official.py](../src/pipeline/b3_official.py) `read_cotahist` | **Reutilizado pelo DATA-01 e por esta extensão** | Parser puro RAW; sem Yahoo ou rede na leitura local |
| Mesmo módulo, `B3OfficialAdjustedExtractor._cotahist` / `download` | Coleta anual/cache já existe; avaliar reutilização futura antes de outro downloader | `_cotahist` pode baixar anual; `download` combina RAW B3 com fatores Yahoo. Diário isolado precisaria canal permitido, armazenamento próprio e recibo/disponibilidade; não chamar para marcar carteira |
| [multiasset_radar.py](../scripts/multiasset_radar.py) `RadarExtractor._cotahist` / `prepare` | Padrões existentes de armazenamento, congelamento e proveniência | Coleta anual e possibilidade de leitura de cache científico; `prepare` exige histórico ajustado antes de produzir `raw_bar`. Não resolve ingestão RAW diária independente; nenhuma leitura de preços científicos ou chamada de preparação foi feita nesta avaliação |

**Marcação das carteiras:** RAW B3, OPEN/CLOSE separados, unidade BRL e fator de
cotação validado; falha/ausência de Yahoo não deve impedir a futura marcação RAW
se esta tiver evidência válida. **Analistas:** histórico ajustado, fatores Yahoo,
warm-up e indicadores continuam no fluxo separado com suas guardas; um diário
RAW não sana a ausência desse histórico. Não usar preço ajustado como marca
contábil nem emitir nova decisão dos agentes nesta entrega.

Entrada de arquivo local permanece disponível. **Download manual não é requisito
definitivo do produto**; o canal automático, o reaproveitamento dessas coletas e
suas condições de uso continuam em avaliação. Nenhum downloader foi criado.
A [página de cotações históricas](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)
descreve preços sem ajustes e restrições de coleta automatizada. Os
[termos B3](https://www.b3.com.br/pt_br/termos-de-uso-e-protecao-de-dados/termos-de-uso/)
preservados delimitam uso informativo/pessoal e restringem difusão/redistribuição.
Preparação local é distinta de publicação; esta entrega não resolve a
aplicabilidade completa ao piloto nem concede licença ou autorização de coleta.

### Arquivo pendente e obtenção manual disponível

1. Abrir [Séries históricas B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/)
   e seu [seletor oficial](https://bvmf.bmfbovespa.com.br/pt-br/cotacoes-historicas/FormSeriesHistoricasArq.asp).
2. Em **Séries Diárias (do ano corrente)**, escolher mês e sessão **posterior a
   13/10/2026**, quando estiver listada. O snapshot consultado só chegava a 13/10;
   não se afirma disponibilidade de 14/10. Não selecionar arquivo anual/mensal.
3. Salvar o ZIP `COTAHIST_DDDMMAAAA.ZIP` intacto, por exemplo em Downloads,
   fora de `data/`, evidências, H2 e Radar. Guardar URL efetivamente utilizada e
   eventual comprovante disponível; registrar horário de download só se conhecido.
4. Informar o **caminho absoluto do ZIP e sua sessão**, com declaração verdadeira
   de obtenção. Comprovante e horário são opcionais; não inventar nenhum deles.

Nenhum ZIP de preços foi baixado nesta tarefa. Essa entrada humana é o passo
exato pendente para validar o primeiro bundle observado, sem pedir novamente
aprovação das bases DP-09–DP-15.

### Registro, validação, revisões e comandos

Raiz dedicada: `data/platform/observed-market-v1/<nome>/`, com contenção absoluta
e resolvida, recusando links/junctions. Cada aquisição exige ID novo e recebe
`original.zip`, eventual comprovante e `acquisition.json` selado como marcador
de conclusão. Registra hash, URL declarada, sessão conferida em **todos** os
registros, operador, declaração, instante UTC real e limitações. Hash/declaração
não autenticam a B3. Sem assinatura externa presumida; marcador de fixture
conhecida impede classificação observada, mas inspeção não demonstra que um
arquivo arbitrário nunca foi fabricado. Naturezas são explícitas e distintas.

Antes dos preços: ZIP com um TXT limitado a 128 MiB, envelope diário 00/01/99,
245 colunas, sessão única pós-D0, ano/data/contagem do envelope quando observado,
mercado 010/BDI 02, R$, fator 1 e sintaxe ISIN brasileira. O parser/validador
reutilizado recusa duplicatas, OHLC incoerente, preço/volume inválido e ausência
de qualquer um dos cinco ativos. Não há preenchimento silencioso.

Bundle incorpora aquisição, hash do original, parser/código, seleção, calendário,
RAW, OPEN/CLOSE, revisão e importação. Identidade do adaptador é
`PILOT_OBSERVED_COTAHIST_RAW_V1`; natureza observada:
`ORIGIN_DOCUMENTED_NOT_AUTHENTICATED`. No novo contrato, o campo legado
`acquisition_registry_sha256` fixa o **registro individual** incorporado,
sem substituir o catálogo antigo. `available_at = imported_at` real; declaração
de obtenção não antecipa disponibilidade e `published_at` livre é recusado.
Nenhum horário do calendário é convertido em timestamp econômico observado.

Comandos PowerShell, a partir da raiz do projeto. Os caminhos, sessão e declaração
do exemplo abaixo só devem ser usados **depois da obtenção real correspondente**:

```powershell
.venv/Scripts/python.exe -B scripts/pilot_observed_data.py calendar --session 2026-10-14
.venv/Scripts/python.exe -B scripts/pilot_observed_data.py observations
$raiz = 'data/platform/observed-market-v1/pilot'
$arquivo = 'C:\Users\LUCAS\Downloads\COTAHIST_D14102026.ZIP'
# Exemplo condicional: preencher URL/declaração com a obtenção efetiva.
.venv/Scripts/python.exe -B scripts/pilot_observed_data.py register --root $raiz --id b3-20261014-v1 --file $arquivo --session 2026-10-14 --nature ORIGIN_DOCUMENTED_NOT_AUTHENTICATED --operator Lucas --url 'https://bvmf.bmfbovespa.com.br/pt-br/cotacoes-historicas/FormSeriesHistoricasArq.asp' --statement 'Obtido manualmente no seletor B3 para este piloto; sem comprovante adicional.'
.venv/Scripts/python.exe -B scripts/pilot_observed_data.py import --root $raiz --id b3-20261014-v1 --name raw-20261014-v1
$disponivel = (Get-Content "$raiz/bundles/raw-20261014-v1.json" -Raw | ConvertFrom-Json).import.available_at
.venv/Scripts/python.exe -B scripts/pilot_observed_data.py query --root $raiz --name raw-20261014-v1 --session 2026-10-14 --phase CLOSE --at $disponivel
```

`--obtained-at` aceita instante declarado com fuso, nunca futuro, apenas se
conhecido; `--receipt` preserva comprovante opcional como bytes/hash. Não atribuir
ao comprovante autenticação não demonstrada. Saída CLI é envelope com `result`,
`official_activation=false` e `financial_integration_ready=false`.

Retificação: registrar outro ID, importar em nome novo com
`--previous raw-20261014-v1`; deve apontar a revisão mais recente. Arquivo
alterado sem `--previous` bloqueia; revisão incrementa e liga `revision_of`.
Mesmo original/mesma aquisição mantém identidade de conteúdo ao reimportar em
outro nome. Nenhum arquivo anterior é sobrescrito. Diretório interrompido fica
preservado; utilizar novo ID após inspecionar o erro. Não há reparo automático.

### Qualificação e dependências para PAPER-04

Executados **47 checks direcionados**: 19 da extensão, 24 DATA-01 anteriores e
4 do parser/extrator (downloads simulados por mocks, sem coleta). O fluxo CLI
registro/importação/consulta foi exercitado em processos novos, com rede bloqueada
e entradas explicitamente **SYNTHETIC_TEST**; isso não valida um arquivo real.
Leitura da demonstração e da raiz PAPER-03 existente também passou sem alteração.

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_pilot_observed_data.py -v
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_pilot_market_data.py -v
.venv/Scripts/python.exe -B -m pytest tests/pipeline/test_b3_official.py -q
.venv/Scripts/python.exe -m ruff check scripts/pilot_observed_data.py tests/test_pilot_observed_data.py
.venv/Scripts/python.exe -m ruff format --check scripts/pilot_observed_data.py tests/test_pilot_observed_data.py
.venv/Scripts/python.exe -B scripts/check_docs.py
.venv/Scripts/python.exe -B scripts/check_preservation.py
git diff --check
```

Preservação e resultados estão no [estado atual](ESTADO_ATUAL.md). Antes de
conectar o ledger: validar ZIP real e condições de uso/canal; ampliar revisão
de horários quando necessário; definir contrato prospectivo de preços/fases e
disponibilidade, eventos corporativos e autorização autenticada; fechar regras
PAPER-01 de execução, custos, risco e caixa; produzir novas decisões com histórico
ajustado válido e orçamento próprio; qualificar ponte financeira versionada e
revisão/recuperação operacional. Não trocar classificação do motor sintético,
reaproveitar decisão antiga ou antecipar autorização de operação.
**DATA-01 integral e PAPER-04 continuam pendentes.**

## 15. APP-01/02 — registro pessoal persistente pela interface

Implementado em 14/10/2026, **DP-02/03/16/17/19**, com configuração pendente
DP-18. Este contrato pessoal não modifica o contrato prospectivo DRAFT acima.

**DP-20/21, atualização posterior de 14/10:** Lucas autorizou o ponto de partida
manual comum efetivamente registrado: 351 PETR4, 297 VALE3, 402 ITUB4, 393 WEGE3,
824 BBAS3 em cada carteira; R$ 100 mil próprios, referência CLOSE de 13/10,
entrada econômica em 14/10, custos zero e resíduo R$ 177,44. Não é uma execução
prospectiva dos agentes. Estratégia (`BUY_HOLD`/`MULTIAGENT`), `comparison_group`
manual e `initialization_note` são opcionais, fornecidos juntos no CREATE e
permitidos somente para simulação. Não ativam executor ou inferência. A home
exibe a referência histórica e o vínculo da base comum. Propostas sobre essa
Multiagentes e registro paper ao aprovar são o próximo fluxo APP-05.

O cadastro real vazio equivocado foi excluído por `ARCHIVE` com motivo,
preservando o evento CREATE. A ação admite somente carteiras sem lançamentos,
reutiliza prévia/confirmação idempotentes, retira do catálogo ativo e bloqueia
novas operações. Não existe DELETE de evento nem migração do banco. Detalhes da
entrada e identidades estão no [estado atual](ESTADO_ATUAL.md).

- Home `/`: criar carteira (nome, natureza, capital em BRL, data de início),
  selecionar, registrar compra/venda, ver prévia e confirmar. Simulações sugerem
  R$ 100 mil; escolher natureza real externa limpa o capital para preenchimento.
  Todas começam em caixa, sem posições presumidas, com capital independente.
- Natureza imutável: `SIMULATION` ou `EXTERNAL`, origem gravada no evento e
  apresentada na carteira/formulário. Real externa é declaração de negócio
  já feito fora da plataforma; não há envio, roteamento ou executor de ordens.
- Quantidades inteiras positivas de ações B3 (`AAAA3`–`AAAA8`), preços positivos,
  capital/custos não negativos em centavos, valores de entrada até R$ 10 bilhões
  (ou 10 bilhões de ações). Sem taxa didática automática. Datas civis ISO válidas,
  não futuras e desde o início pessoal; não certificam sessão histórica B3.
  D0 do piloto não limita o histórico pessoal. Aportes/retiradas, outros tipos de
  instrumento, impostos e eventos corporativos não são modelados neste incremento.
- Data econômica declarada separada de `recorded_at` UTC real do servidor
  (exibida em São Paulo). Replay ordena data econômica e ordem original no mesmo
  dia. Correção conserva essa precedência; para representar outra ordem intradiária,
  anular e registrar novamente, se a sequência continuar válida. Não se inventa
  hora de execução. Toda operação histórica recalcula também as posteriores.
- Compra debita bruto + custos e capitaliza ambos na base; venda parcial baixa
  base proporcional em centavos HALF_EVEN; venda total zera a base. Custos da
  venda reduzem receita/resultado. Quantidade/caixa insuficientes em qualquer
  ponto rejeitam o comando completo, inclusive quando a inconsistência é posterior.
- Reuso do `fill` V5 com dependências locais pelo `pilot_paper.bind`: custos
  declarados e reconciliação econômica substituem dependências prospectivas.
  Caixa é **econômico**, sem D+2/custódia/liquidação da corretora. Não se apresenta
  como caixa liquidado/liberado para negociar. Não se criam ordens, autorizações,
  decisões ou resultados nos ledgers científicos. Política de 85% não é aplicada.
- **Corrigir** abre os campos do lançamento e exige motivo: substituição atômica
  ou anulação via prévia/confirmar. Eventos anteriores permanecem íntegros na
  consulta de rastreabilidade. Não existe UPDATE/DELETE de lançamento; a correção
  também precisa manter válida toda a sequência. Permite corrigir uma correção.
- Identidade `HFL-MANUAL-PORTFOLIO-V1`, SQLite separado em
  `data/platform/manual-v1/manual.sqlite3`; eventos encadeados/selados, índices
  únicos, triggers imutáveis, `BEGIN IMMEDIATE`, `synchronous=FULL`. Prévia GET-like
  (POST sem escrita) vincula payload normalizado e revisão; confirmação revalida
  ambos sob transação. Mesmo comando/payload retorna o mesmo evento; payload
  diferente no mesmo comando e revisão obsoleta são recusados. Queda antes do
  commit desfaz a transação; resposta perdida após commit pode ser repetida.
- GET não inicializa nem escreve. Catálogo, detalhe e operações vêm do mesmo
  replay, sem saldos em JSON/localStorage. `HFL_MANUAL_ROOT` é configuração do
  processo para isolamento, nunca parâmetro HTTP; recusa raízes científicas do
  projeto. Escrita web reutiliza proteção local Host/Origin/CSRF e JSON estrito.
  Não há nova autenticação/dependência. Backup externo/recuperação operacional
  pela interface continuam fora deste incremento; transação não substitui backup.
- Sem referências de preços qualificadas: posições exibem quantidade/base/custo
  médio, patrimônio marcado fica indisponível enquanto houver posições. Carteira
  somente em caixa tem patrimônio conhecido igual ao caixa. Retornos, curva diária
  e proventos permanecem indisponíveis, nunca preenchidos por custo médio ou fills.
  APP-03 deve integrar referências RAW identificadas por data/origem à mesma fonte
  contábil; APP-04 integra eventos sem dupla contagem.
- Piloto comparativo aparece como configuração pendente: R$ 100 mil por carteira,
  cinco alvos iniciais de 20%, posições comuns. Entrada/custos/arredondamento e
  revisão explícita do limite proposto de 85% continuam PAPER-01; nenhum fill ou
  venda automática. Cadastro manual não depende de PAPER-04. Demonstração em
  `/?demo=1`, consultas em **Gestor e demonstrações** e Legacy continuam separados.

Checks reproduzíveis, sempre com banco de teste isolado:

```powershell
.venv/Scripts/python.exe -B tests/test_manual_portfolio.py
.venv/Scripts/python.exe -B tests/test_manual_portfolio.py --browser
.venv/Scripts/ruff.exe check dashboard/manual_portfolio_api.py dashboard/server.py tests/test_manual_portfolio.py
node --check dashboard/manual-portfolio.js
.venv/Scripts/python.exe -B scripts/check_docs.py
git diff --check
.venv/Scripts/python.exe -B scripts/check_preservation.py
```

O check de navegador inicia/encerra somente seus próprios processos e usa Chrome
headless desktop/390 px. Exercita HTTP real, SQLite real, teclado, erros de campo,
histórico/correção, seleção, recarga e reinício do servidor; bloqueia qualquer
tráfego externo ou POST fora do namespace pessoal. Capturas locais não seladas
em `data/cache/manual-portfolio-ui/`. Resultados e limites no
[estado atual](ESTADO_ATUAL.md#app-0102--carteiras-pessoais-e-operações-pela-home-14102026).
