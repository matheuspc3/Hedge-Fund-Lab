# H2 v6 — Evaluation Protocol Amendment Proposal

**H2_V6 EVALUATION AMENDMENT PROPOSED — AWAITING AUTHOR APPROVAL**

Proposta para revisão dos autores e orientador, preparada na branch `#1-Update`,
sobre a pré-auditoria `7e6a0ad`. **NOT APPROVED. NOT FROZEN.** Não autoriza
Validation, Final Test nem chamadas científicas. O bloqueio do System Freeze
continua vigente até aprovação expressa das escolhas abaixo e qualificação da
infraestrutura de avaliação. A CAL-B4 permanece `CAL_B4_PASS — SANITY CHECK ONLY`,
consumida one-shot; `SYSTEM_CALIBRATION_COMPLETE=True`; tratamento final v6.

## 1. Matriz SF-B1 a SF-B6

| ID | Problema e fonte vigente | Decisão candidata | Justificativa e limite |
|---|---|---|---|
| SF-B1 | H0/H2 operacional ainda TBD; [EXPERIMENT_PROTOCOL](EXPERIMENT_PROTOCOL.md) §2 e monografia, “Síntese e Hipóteses da Pesquisa” | H0_2: Δ ≤ 0; HA_2: Δ > 0. Δ = média dos três Sharpes LLM − Sharpe B&H. Um contraste primário no Final | Preserva a pergunta H2, identifica direção e estimando. H1 multiativo permanece separado. Inferência temporal condicionada às três trajetórias, sem alegação de generalização a futuras chamadas Gemini |
| SF-B2 | R de avaliação TBD; protocolo §15 | R=3 em Validation e R=3 no Final, novas chamadas científicas em cada run; benchmark determinístico uma execução por fase | Evita escolher o melhor run. Mesmos dados, identidade, custos e parâmetros; independência de chamadas não transforma runs em mercados independentes |
| SF-B3 | Agregação não escolhida; protocolo §15 | Média aritmética dos três Sharpes, todos os runs publicados | Mantém o estimando pedido; Sharpe da curva média seria outra estatística |
| SF-B4 | Teste, α, IC e resampling TBD; protocolo §18 | Candidato A: stationary bootstrap temporal pareado, basic centrado, α=0.05, B=5000, seed=20261008, bloco médio=10 | Captura dependência temporal e entre séries, sob pressupostos. Fragilidades e única alternativa B studentizada em §5, antes de aprovação |
| SF-B5 | Famílias escolhidas, specs exatas abertas; protocolo §12/§17.3, estratégias e registry | B&H existente; SMA50/200 por regime; Bollinger20/2 por estado com desigualdades inclusivas | O nome da classe não define o contrato. SMA/Bollinger existentes diferem: novos adapters identificados seriam necessários após aprovação |
| SF-B6 | MAR é default técnico; turnover atual é drift; protocolo §17 e `backtesting/metrics.py` | Sortino MAR diário=0/rf anual=0 com flag; turnover = nocional absoluto executado/capital inicial | Mantém convenção técnica, explicita razão econômica indefinida e distingue negociação de variação de pesos |

Fonte da descoberta e separação de aprovação:
[SYSTEM_FREEZE_PRE_AUDIT.md](evidence/h2_v6/SYSTEM_FREEZE_PRE_AUDIT.md).
Esta proposta fecha a especificação **para revisão**, não fecha os bloqueios como
decisões aprovadas e não substitui o protocolo histórico.

## 2. Identidade preservada versus amendment novo

Já aprovados e preservados: tratamento H2=6; Technical Prompt=5; Response
Schema=2; Evidence Vocabulary=1; Evidence Validator=1; Risk Prompt=2; checker=3;
Portfolio existente; N=5; consensus_threshold=0.6; require_all_votes=true;
volatility_window=21; risk_max_volatility=0.50; risk_max_drawdown=0.25;
risk_max_concentration=1.0. Runtime/model/opções/retries continuam exatamente
na ParticipantSpec final e na autorização histórica, sem alterações.

| Identidade existente | Valor canônico preservado |
|---|---|
| ParticipantSpec H2 v6 SHA256 | `7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938` |
| CAL-B4 commitment SHA256 | `35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7` |
| Snapshot | `20261004T201258177516Z-b4cf39fc761f251d2dd18e787008345a` |
| Snapshot identity | `b4cf39fc761f251d2dd18e787008345aaf02bd9e19f913390c510338b84ee7d4` |
| PETR4.SA CSV SHA256 | `7b6a0018191028ecea2ee66785c27f771a721aa4a96c4953ca87ac6d688c3ffa` |
| Revisão humana CAL-B4 SHA256 | `33db64913ace88d2b5c72bcdc2b37b608f939e4ade0e681b4a46dbbbb1474733` |

Sharpe científico v1, rf=0, frequência=252, ddof=1; capital R$100.000;
cash_return=0; long-only; quantity_mode=`fractional_notional`; custos
brokerage_fixed=0, spread_bps=5, tax_rate=0.00032; mesmo snapshot/calendário,
causalidade e close(t) → open(t+1) são preservados. A sensibilidade previamente
declarada `{0,5,10,20}` bps é exclusivamente descritiva, sem seleção de custo.

Novos e pendentes: H0_2/HA_2 operacional, R=3 nas duas fases, agregação, âmbito
condicional da inferência, teste/IC/seed/bloco/degenerações, specs e regras exatas
SMA/Bollinger, desempate de bandas colapsadas, MAR/flags/turnover de ordens,
completude das fases e release por integridade. Defaults e protótipos não são
aprovação. A monografia, código produtivo, prompts, contratos e evidências
históricas não foram editados.

## 3. Estimando, fases e replicações propostas

Para a fase separadamente, sejam r_0,t os retornos líquidos do Buy & Hold e
r_j,t os retornos líquidos do run LLM j=1,2,3, todos nas mesmas sessões.

```text
S_j = sqrt(252) * mean(r_j) / sd(r_j, ddof=1)
Δ_hat = (S_1 + S_2 + S_3)/3 − S_0
H0_2: Δ ≤ 0             HA_2: Δ > 0
```

Δ é o contraste de Sharpes marginais das quatro séries sob o modelo temporal
adotado; Δ_hat é o estimador calculado nas três trajetórias observadas. O escopo
confirmatório proposto é condicionado a essas trajetórias. Não é uma estimativa
com incerteza completa sobre toda a população de futuras realizações do agente.
Se os autores exigirem essa última interpretação, R=3 com bootstrap exclusivamente
temporal é insuficiente e SF-B1/SF-B4 continuam abertos nessa interpretação.

Publicar três Sharpes, três Δ_j=S_j−S_0, média, mínimo, máximo e desvio-padrão
descritivo entre runs com ddof=1; retornos, equity curves, trades e custos de cada
run. O desvio entre runs não é erro-padrão da hipótese confirmatória. Não
selecionar run; não calcular Sharpe da curva média como substituto; não fazer
mediana pós-hoc nem média de decisões.

Validation: três runs completos, integridade e desempenho fora da calibração,
sem tuning, seleção ou teste confirmatório. Pode publicar Δ e comparações
descritivas; não consumir um segundo contraste confirmatório com α=0.05.
Final: três runs completos e o único teste confirmatório. Nunca concatenar
Validation e Final para esse teste. SMA, Bollinger, Sortino, drawdown, CAGR,
turnover, custos e sensibilidade são exploratórios/descritivos, sem p-valores
confirmatórios adicionais. Não há família de três testes por run.

Runs LLM usam instâncias, traces e identidades de execução distintos; nenhum
cache/replay científico entre runs. Retentativas exclusivamente conforme contrato
congelado, dentro da mesma identidade. A seed estatística não é seed do modelo,
não é enviada ao Gemini e não garante independência interna do provedor. Um
run incompleto não pode ser substituído por outro após observar seu desempenho;
exige recuperação exata pelo contrato aprovado ou interrupção por integridade.
Benchmarks determinísticos são executados uma vez por fase/cenário de custos.

## 4. Candidato A: definição exata do teste e intervalo basic

### Amostra e pressupostos

Usar `periodic_returns` da curva líquida canônica de cada run. Primeiro ponto da
curva é o capital inicial em decision_start; último é settlement. O retorno de
entrada com custos e o retorno de settlement permanecem; dias em caixa são
zeros. Nenhum retorno de warmup integra a amostra. Não fabricar retorno para
o primeiro ponto, usar log-retorno, remover zeros, preencher datas, truncar
sessões ou fazer inner join: os quatro índices completos devem ser idênticos,
ordenados, únicos, finitos e iguais ao calendário esperado da fase.

A unidade reamostrada é a linha vetorial
`(r_0,t, r_1,t, r_2,t, r_3,t)` por sessão. Votos, trades e runs inteiros não são
unidades de bootstrap. Não reconstruir decisões nem rerodar o motor nas amostras;
esta é inferência sobre retornos realizados, sem novas chamadas científicas.

Sob um processo vetorial aproximadamente estacionário, dependência fraca e
momentos suficientes, o bootstrap temporal é uma aproximação plausível. Não
garante validade em presença de quebra de regime, dependência longa ou razão
de Sharpe degenerada. Essa avaliação de adequação foi feita antes de escrever
o protótipo e sem acessar qualquer resultado reservado.

### Índices stationary e estatística

Configuração candidata fixa: B=5000; alpha=1/20; gerador NumPy
`Generator(PCG64(20261008))`; probabilidade de reinício p_block=1/10. Cada
reamostragem tem n linhas. Primeiro índice uniforme em `{0,...,n−1}`. Em cada
passo, sortear U uniforme; se U<0.1, reiniciar com índice uniforme; caso
contrário, avançar um índice circularmente módulo n. Os blocos têm comprimento
geométrico médio 10. Circularidade não calcula t+1 real fora da fase: apenas
reutiliza retornos já contidos na amostra.

Aplicar **o mesmo vetor de índices às quatro colunas**. Recalcular o Sharpe
canônico v1 em cada coluna, fazer média dos três Sharpes e subtrair B&H:
`Δ_b*`. Definir `e_b = Δ_b* − Δ_hat`. Isso centra o erro bootstrap na estimativa;
não impõe igualdade de Sharpe aos dados originais e não é um teste nulo exato
em amostra finita. A fronteira Δ=0 aproxima a hipótese nula composta.

### p-valor, quantil e decisão, inclusive empates

Ordenar os B erros: `e_(1) ≤ ... ≤ e_(B)`. Definir:

```text
p_plus = (1 + count[e_b ≥ Δ_hat]) / (B + 1)
k = floor((1 − alpha)*(B + 1)) + 1 = 4751
q = e_(k)                           # índice matemático iniciado em 1
L_95 = Δ_hat − q
IC unilateral basic = [L_95, +infinito)
superioridade = estimável AND Δ_hat > 0 AND p_plus < 0.05 AND L_95 > 0
```

Usar comparação `≥` no p-valor, incluindo todos os empates, e comparação estrita
`>` no limite; sem tolerância de empate econômica, sem quantil interpolado.
Essa escolha de rank inverte exatamente a regra discreta `p_plus<alpha`,
inclusive na presença de empates; usar o quantil interpolado padrão de 95%
com a correção +1 poderia criar discordância na fronteira. Para B=5000, rejeitar
requer no máximo 249 erros ≥ Δ_hat. L=0/p=0.05 não prova superioridade.
O +1 evita p=0; não transforma a aproximação bootstrap em teste exato.

### Degenerações e resultados

O Sharpe canônico continua atribuindo escore técnico 0 quando n<2 ou
sd<1e-15. Isso não é uma razão econômica bem definida. Proposta de guard
inferencial: se qualquer uma das quatro séries originais, ou qualquer amostra
bootstrap, acionar essa convenção, preservar e publicar os escores com flags,
quantidade de amostras degeneradas e `INCONCLUSIVE_DEGENERATE`; p e L são null.
Também não inferir se todos os erros bootstrap forem idênticos. Não descartar
amostras, substituir scores, sortear novamente nem relaxar o limite. NaN/inf,
sessões ausentes ou séries desalinhadas são falha de integridade, sem p-valor.

Quando estimável: Δ_hat≤0 é resultado negativo/nulo; Δ_hat>0 sem rejeição é
positivo inconclusivo; somente a regra completa acima autoriza “superioridade
no contraste primário, sob os pressupostos”. Não rejeição não prova igualdade.
Todos os resultados, inclusive negativos e degenerados, devem ser publicados.

### Pseudocódigo

```text
exigir exatamente B&H + LLM1 + LLM2 + LLM3 completos e pareados
obter Δ_hat e flags com o Sharpe científico v1
rng = PCG64(20261008)
para b = 1..5000:
    I_b = stationary_indices(n, prob_restart=0.1, rng)
    R_b = R[I_b, todas_as_colunas]
    Δ_b = média(Sharpe_v1(R_b, LLM1..3)) − Sharpe_v1(R_b, B&H)
    salvar e_b = Δ_b − Δ_hat e flags; nunca refazer amostra degenerada
se degenerado: publicar scores, flags, p=null, L=null, inconclusivo
senão: calcular p_plus, e_(4751), L_95 e decisão estrita
publicar identidades, versões NumPy/Pandas/Python, n, B, seed, bloco,
índices/erros ou respectivos artifacts íntegros, e o contraste único
```

## 5. Adequação metodológica e única alternativa para aprovação

[Lo (2002)](https://traders.berkeley.edu/papers/The-Statistics-of-Sharpe-Ratios.pdf)
mostra que a dependência dos retornos afeta a incerteza do Sharpe e sua agregação
temporal. Preservamos o escore protocolar diário ×sqrt(252); a interpretação
é esse escore anualizado por convenção, sem afirmar que equivale ao Sharpe
econômico de retornos anuais sob autocorrelação.

[Politis & Romano (1994)](https://users.ssc.wisc.edu/~behansen/718/Politis%20Romano.pdf)
fundamentam a reamostragem stationary com blocos de comprimento aleatório para
observações estacionárias fracamente dependentes. Isso sustenta o algoritmo de
índices; não estabelece que bloco médio 10 é ideal para PETR4 nem garante
cobertura de 95% em uma amostra de aproximadamente um ano.

[Ledoit & Wolf (2008)](https://www.econ.uzh.ch/apps/workingpapers/wp/iewwp320.pdf)
propõem inferência studentizada para diferença de Sharpes e discutem limitações
do bootstrap não studentizado. Seu procedimento temporal usa blocos circulares,
estimação própria de erro-padrão e seleção/calibração de bloco. Nosso candidato
A é basic não studentizado, unilateral, com média de três Sharpes: **não é uma
implementação do método exato dos autores**.

**Parecer:** A é coerente computacionalmente e aceitável como candidato
condicional de primeira ordem, mas não merece aprovação automática como teste
confirmatório robusto. Há cerca de 247/249 retornos, não 3×esse número de
mercados independentes; bloco médio 10 corresponde aproximadamente a 25 blocos
esperados. Caudas, não estacionariedade e volatilidade baixa prejudicam a
aproximação. R=3 dá descrição modesta de variabilidade entre chamadas, que a
reamostragem temporal não integra como nova população de runs. Não há estudo
de tamanho/poder/cobertura neste trabalho; testes de código não o substituem.

**Única alternativa B:** manter o mesmo estimando, pareamento, B=5000, seed,
stationary com bloco médio 10 e escopo condicional, mas studentizar o contraste
com erro-padrão delta/HAC Bartlett de lag máximo 9, fixado antes das fases.
É uma adaptação proposta, inspirada na studentização, não o algoritmo de
Ledoit & Wolf. É mais simples que um bootstrap aninhado; não resolve por si
só o horizonte curto, quebras de regime ou incerteza sobre novos runs.

Para especificá-la sem ambiguidade, para cada coluna j:

```text
a = n/(n−1); μ_j = mean(r_j); m2_j = mean(r_j²)
s_j² = a*(m2_j−μ_j²)
c = (−1, 1/3, 1/3, 1/3)
g_μ,j = c_j*sqrt(252)*(1/s_j + a*μ_j²/s_j³)
g_m2,j = −c_j*sqrt(252)*a*μ_j/(2*s_j³)
X_t = (r_0,t,...,r_3,t,r_0,t²,...,r_3,t²)
h_t = g'*(X_t−mean(X))
γ_l = sum(h_t*h_(t−l), t=l+1..n)/n
Ω = γ_0 + 2*sum((1−l/10)*γ_l, l=1..9)
se = sqrt(Ω/n)
z_hat = Δ_hat/se_original
e_b_student = (Δ_b*−Δ_hat)/se_b*  # recalcular gradiente/HAC em cada amostra
p_plus = (1+count[e_b_student ≥ z_hat])/(B+1)
L_95 = Δ_hat − e_student_(4751)*se_original
```

Requer n≥11, Sharpes não degenerados, Ω/se finitos e estritamente positivos em
todas as amostras; falha dessa condição produz inconclusivo, sem clamp ou
reamostragem. No cálculo definitivo, a variância amostral deverá vir do mesmo
helper canônico para evitar cancelamento numérico em `m2−μ²`.
Regra de decisão e empates idêntica a A. Essa alternativa está especificada
para revisão, **não implementada nem escolhida**. Aprovar A aceitando seus
limites, ou B com qualificação offline adicional, antes da Validation; não
executar ambos e escolher o que rejeitar H0. B não corrige o escopo condicional.

## 6. Inventário e identidade exata dos benchmarks candidatos

Registry atual `src/experiments/participants.py`: `buy_and_hold`, `sma_cross`,
`bollinger`, `indicator_family_control`, `equal_weight`, `min_variance`,
`llm_agent`. `build_participant` verifica parâmetros pela assinatura e cria
instância nova. `BuyAndHoldParticipant` já emite alvo 1 na primeira observação
da execução, mesmo com warmup; depois emite lista vazia. É reutilizável.

`SMACrossParticipant` compra/vende somente em cruzamentos entre t−1 e t, com
desigualdades estritas. Se o mercado já estiver em regime SMA50>SMA200 na
primeira decisão, pode ficar em caixa até outro cruzamento. A regra proposta
compra nessa primeira decisão; igualdade sai para caixa. Portanto, mudar apenas
os parâmetros não resolve a diferença.

`BollingerParticipant` age em rompimentos estritos para fora das bandas entre
t−1 e t. A proposta age no nível atual com ≤/≥, incluindo a primeira decisão
já fora de banda. Há ainda diferença entre a descrição textual no módulo
legado e suas condições executáveis; não a corrigimos dentro deste amendment.
`indicator_family_control` é controle combinado, não substitui as duas specs.
Equal Weight/MinVar pertencem ao estudo multiativo H1, fora do contraste H2.

Specs candidatas serializáveis com o `ParticipantSpec` existente:

```json
{"kind":"buy_and_hold","params":{"ticker":"PETR4.SA"}}
{"kind":"sma_regime_h2_proposed","params":{"ticker":"PETR4.SA","fast_window":50,"slow_window":200}}
{"kind":"bollinger_state_h2_proposed","params":{"ticker":"PETR4.SA","window":20,"k":2.0}}
```

Os dois kinds novos são identidades propostas, **ausentes do registry produtivo**.
O protótipo offline os demonstra reaproveitando `SignalParticipant`, `sma` e
`bollinger_bands`; não cria um caminho alternativo para execução científica.

| Regra | Buy & Hold primário | SMA secundário | Bollinger secundário |
|---|---|---|---|
| Lookback indicador | nenhum | 50/200 fechamentos incluindo t | 20 fechamentos incluindo t |
| Indicador | nenhum | médias aritméticas rolling completas | média rolling20 ± 2×sd rolling20, ddof=1 |
| Inicialização da fase | caixa, posições zero | caixa, alvo zero | caixa, alvo zero |
| Primeira decisão válida | alvo 1 | alvo 1 se SMA50>SMA200; senão 0 | close≤lower entra; close≥upper permanece caixa; dentro mantém caixa |
| Regras posteriores | nenhuma intenção nova | alvo 1 se fast>slow; senão 0 | close≤lower entra se caixa; close≥upper sai se long; dentro mantém |
| Igualdades | sem comparação | fast=slow → caixa | inclusivas; se lower=upper, HOLD, evitando alternância artificial; desempate novo sujeito à aprovação |
| Frequência | primeira decisão apenas | consulta diária | consulta diária |
| Posição mantida | sem rebalanceamento | só emitir intent ao mudar alvo | só emitir intent ao mudar alvo |
| Entrada inválida | guard de dados | histórico insuficiente/NaN/inf falha | histórico insuficiente/NaN/inf falha |

Contrato comum: ticker PETR4.SA; single-asset; alvo em {0,1}; sem short/alavancagem;
mesmo snapshot e calendário; instâncias novas por fase; warmup apenas histórico;
observação causal até close(t); `OrderIntent` só executa no open seguinte pelo
motor existente; preço/custos/limite de caixa conforme `CostModel` congelado e
execução fracionária; posições marcadas no close até settlement. Alvo 100% é
nominal; custos podem deixar pequeno saldo de caixa, sem rebalanceamento diário
para eliminar drift. Nenhuma venda terminal forçada é introduzida: settlement
executa a última intenção e marca patrimônio, não liquida automaticamente toda
posição. Runs de fases diferentes começam novamente em caixa; nenhum estado
ou ordem pendente passa de uma fase a outra.

SHA256 da spec = SHA256 UTF-8 de `canonical_json(ParticipantSpec.to_dict())`,
chaves ordenadas/sem espaços. Esses hashes não cobrem código/regras por si sós;
um futuro manifesto aprovado deve vincular também adapter, helpers, motor,
custos, calendário, snapshot e documentação. Hashes candidatos e fontes
observadas estão no relatório reproduzível do self-check descrito em §10.

## 7. Métricas secundárias candidatas

Sortino: rf anual=0, MAR diário=0, frequência=252, retornos líquidos completos.
`D = sqrt(mean(min(r_t−0,0)^2))`, incluindo observações positivas/zero no
denominador da média. Valor técnico = `sqrt(252)*mean(r)/D` conforme helper
canônico. Para n<2 ou D<1e-15, manter o 0 técnico e publicar
`degenerate=true`, motivo `INSUFFICIENT_OBSERVATIONS` ou `ZERO_DOWNSIDE`, D,
n, e `economic_value=null`. Tabela econômica deve mostrar “indefinido por
degeneração”, não um Sortino econômico zero ou infinito. Sem downside não implica
boa precisão ou superioridade. Dados inválidos falham; não viram degeneração.

Turnover de ordens por fase/run:

```text
notional_executed = sum(abs(trade.quantity * trade.price))
order_turnover = notional_executed / 100000
executed_orders = quantidade de registros Trade realmente executados
total_cost = sum(trade.cost)
```

Compras e vendas contam ambas, sem dividir por dois ou anualizar. Preço é o
preço-base executado do registro Trade; spread/tax/brokerage ficam nos custos,
sem duplicar custo no nocional. Quantidade fracionária é unidade sintética.
Ordens canceladas, intents, sinais e ordens não preenchidas não contam.
Executar validações de tipo/direção, preço e quantidade finitos positivos,
custos não negativos e datas da fase. Listas vazias: turnover=0, ordens=0,
custos=0. B&H conta sua compra inicial e somente eventual venda realmente
executada, sem venda fictícia no fim. Mesmo contrato para todos os runs.

O `turnover(weights)` legado é a média de mudanças absolutas de pesos observados,
incluindo drift de mercado. Se publicado, rotular “diagnóstico de mudança de
pesos”; nunca “turnover de ordens”. MDD/CAGR/exposição/custos são descritivos,
calculados por run com helpers existentes e definições registradas.

## 8. Janelas e viabilidade no fluxo existente

| Fase proposta | Domínio | decision_start | decision_end | settlement | Pontos da curva / retornos esperados pelo calendário |
|---|---|---|---|---|---|
| Validation | 2024-09-02..2025-08-29 | 2024-09-02 | 2025-08-28 | 2025-08-29 | 248 / 247 |
| Final Test | 2025-09-01..2026-08-31 | 2025-09-01 | 2026-08-28 | 2026-08-31 | 250 / 249 |

Contagens reproduzidas na pré-auditoria exclusivamente do calendário B3; não
são resultados de execução. Confirmar índices completos antes da inferência.
Última sessão reservada ao settlement, sem nova decisão; nenhuma ordem cruza
o limite. A frase “504 sessões de warmup” deve manter a semântica já existente:
`minimum_history_sessions=504` significa pelo menos 503 sessões anteriores
mais a barra da primeira decisão. Exigir 504 sessões estritamente anteriores
mudaria o contrato; não fizemos essa alteração silenciosa. Confirmar a redação
na aprovação.

Fluxo rastreado: `ExperimentRunner` verifica snapshot/provenance, resolve
`EvaluationWindow`, aplica `require_cal_b_locked`, resolve `PhaseWindow`, exige
settlement na fase, recorta dados em phase.end, instancia participante novo,
executa `ExecutionEngine`, calcula métricas e persiste artifacts. A observação
usa histórico até t; o motor liquida intents em t+1 e não consulta participante
no settlement. `RunArtifacts.persist` publica atomicamente sem sobrescrever um
run existente. Isso é atomicidade de artifacts, não prova de idempotência live
de chamadas após crash.

Viável reutilizar: `ParticipantSpec`, `EvaluationSpec`, `CostSpec`,
`ExecutionSpec`, `PhaseWindow`, `resolve_evaluation_window`,
`require_execution_within_phase`, `SignalParticipant`, BuyAndHold existente,
indicadores puros, `periodic_returns`, `sharpe_components`, `sortino_ratio`,
`total_transaction_cost`, traces/replay e persistência existentes.

Ainda necessários após aprovação, **não conectados nesta tarefa**:

1. Um contrato/manifesto de avaliação que vincule decisões aprovadas, hashes,
   versões, spec final e limites, mantendo identidade do tratamento.
2. Adapters SMA-regime/Bollinger-estado com kinds próprios e registro explícito;
   não editar os kinds históricos para mudar sua semântica.
3. Módulo de avaliação para pareamento estrito com calendário da fase,
   agregação, teste escolhido, flags Sortino e turnover sobre trades.
4. Orquestração de exatamente três runs com identidades distintas, recuperação
   exata, completude e manifestos; não apenas três chamadas ao runner genérico.
5. Guard de Validation → Final por conclusão e identidade, nunca desempenho;
   o contexto/label do runner sozinho não assegura esse release.
6. Vincular as duas `PhaseWindow` explícitas, pois PHASES global hoje só declara
   Sequential; verificar settlement antes de qualquer construção/chamada live.
7. Sensibilidade de custo descritiva por replay exato, sem novas decisões LLM
   ou tuning, somente se esse replay for qualificado e aprovado. Mudança de
   custos altera estado de risco e pode fazer replay exato falhar: não afirmar
   que o suporte atual resolve automaticamente essa análise contrafactual.

Nada exige alteração de Technical, Risk, Portfolio, prompts, schema, checker,
vocabulary ou validator. Alterações posteriores da camada de avaliação terão
de ser revisadas e receber identidade própria; não atualizar retroativamente
hashes ou selos da CAL-B4 para acomodá-las.

Release candidato: exatamente três runs Validation íntegros/completos,
benchmark primário completo, calendário e settlement corretos, identidade
congelada correspondente, traces/schemas/requests válidos, custos/execução
consistentes, artifacts persistidos/selados, auditoria sem falha de integridade.
Resultado financeiro negativo, p-valor alto e degeneração estatística não
impedem release se os dados forem íntegros. Falha de integridade impede release
mesmo com performance positiva. Após revisão de integridade, uma autorização
específica ainda será necessária para as chamadas das fases futuras; esta
proposta não herda as autorizações live limitadas a development/CAL-B4.

## 9. Impacto na monografia e referências

Não editar agora `docs/faculdade/monografia/main.tex` nem o protocolo DRAFT.
Após aprovação, incorporar H0_2/HA_2 e o contraste primário B&H à H2, preservando
a formulação de pesquisa e H1 multiativo. Distinguir benchmarks secundários,
replicação de chamadas, estimando condicional, hipótese confirmatória única e
Validation descritiva. Método deve apresentar custos, janelas/settlement,
warmup inclusivo, regras SMA/Bollinger, teste escolhido, degenerações e
limitações. Resultados devem apresentar todos os runs, sem narrativa de
superioridade antes de cumprir o critério e sem ocultar negativos/inconclusivos.
Explicar a convenção de anualização, sem modificar o Sharpe aprovado.

Bibliografia a integrar após aprovação (nenhum arquivo bibliográfico alterado):

- Lo, A. W. (2002). *The Statistics of Sharpe Ratios*. Financial Analysts
  Journal, 58(4), 36–52. [DOI 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453).
- Ledoit, O.; Wolf, M. (2008). *Robust Performance Hypothesis Testing with the
  Sharpe Ratio*. Journal of Empirical Finance, 15(5), 850–859.
  [DOI 10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002).
  A verificação consultou também a versão integral dos autores, UZH Working
  Paper 320, janeiro de 2008, com diferenças explicitadas em §5.
- Politis, D. N.; Romano, J. P. (1994). *The Stationary Bootstrap*. Journal of
  the American Statistical Association, 89(428), 1303–1313.
  [DOI 10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870).

Consultas externas desta tarefa foram exclusivamente bibliográficas. Zero
chamadas Gemini/API científica; nenhum segredo, prompt científico ou dado do
snapshot foi enviado nessas consultas.

## 10. Verificação offline e preservação

Self-check isolado:
[check_h2_v6_evaluation_proposal.py](../scripts/check_h2_v6_evaluation_proposal.py).
É referência executável de proposta, não código aprovado. Não recebe argumentos,
não abre prices reais, não grava artifacts, não instancia LLM e bloqueia sockets
durante suas verificações. Os novos adapters não entram no registry.

```powershell
.venv/Scripts/python.exe -B scripts/check_h2_v6_evaluation_proposal.py
```

Verifica com séries sintéticas: agregação distinta do Sharpe de retorno médio;
exatamente três runs/um contraste; rejeição de desalinhamento/NaN/benchmark
adicional; índices compartilhados nas quatro colunas; determinismo PCG64 com
B=5000; p/IC e rank 4751 com empate e fronteira; negativos e degenerações sem
PASS artificial; Sortino sem downside e downside sobre todas as observações;
turnover compra+venda, custos, lista vazia e exclusão de cancelamento; regime
SMA na entrada/igualdade; Bollinger inclusivo, manutenção de estado e bandas
colapsadas; motor fracionário com custos, warmup 503+1, compra B&H em t+1,
settlement e recusa de crossing. Não calcula performance real CAL-B4.

Preservação usa `run_cal_b4.verify_freeze` e `run_cal_b.verify_seal` existentes,
confere hashes dos dez anchor seals/AUDIT_SEAL, os 12 gates já persistidos,
assinatura humana e status; não chama `audit`, `status`, `run`, nem recria
avaliação humana. O guard completo `verified_batch` também foi executado antes
dos novos arquivos, com árvore limpa. Baseline de 6752 arquivos e guardas
preservado; one-shot permanece consumido. Hashes são checagens de identidade,
não nova análise comportamental das respostas ou outcomes da CAL-B4.

Resultado observado: **self-check PASS**; configuração B=5000 por chamada,
determinismo conferido em duas chamadas sintéticas idênticas; nenhuma conexão
de rede do self-check. Reexecução após o guard de nocional finito: PASS.
Preservação: **6752 arquivos baseline conferidos; 10/10 selos; 12/12 gates PASS**;
revisão humana/status/commitment/spec preservados, sem recalcular outcomes.

| Identidade candidata, não congelada | SHA256 |
|---|---|
| B&H ParticipantSpec | `cbdb92508d9766c5668b2500eea837cce3f5384d117f08a61765765829be0ef1` |
| SMA regime ParticipantSpec | `9fec52feb42a4dcea4ff7ca6973db348e03cf3efb92fe64252ac32e373f02bc5` |
| Bollinger estado ParticipantSpec | `1ba8fddb165ec8b4bec5025f7be1ee38a8ff5e5e30d7e88c9b24958e2ec47345` |
| Bytes observados do protótipo offline | `d707c5927203ecd6ad507ad6bd1773a8fe839c80f2c2e4afc5677e7904b330b1` |

Hashes de código/helper já congelados são os mapeamentos integrais
`source_and_scientific_artifact_sha256` de
[protocol_freeze_v1.json](evidence/cal_b4/protocol_freeze_v1.json) e
`sources_sha256` de [guards_freeze.json](evidence/cal_b4/guards_freeze.json),
conferidos pelo guard existente. O hash do protótipo é registro dos bytes
observados, não um novo selo científico aprovado.

Testes adicionais existentes, somente sintéticos/mocks:

```powershell
.venv/Scripts/python.exe -B -m pytest tests/experiments/test_phases.py tests/backtesting/test_arena_evaluation_window.py -q -p no:cacheprovider --basetemp .pytest_temp/h2_v6_amendment_proposal_verified
```

**57 PASS, 0 FAIL, 0 ERROR, 0.83s**. Inclui o runner recortando o mercado na
fronteira sem observar preços posteriores. A primeira tentativa teve 56 PASS
e um erro de criação do diretório temporário por permissão do sandbox;
a repetição com escrita temporária permitida passou integralmente. Isso foi
um problema de ambiente de teste, sem execução ou falha científica reservada.

Qualificação adicional necessária se alternativa B for escolhida: testes da
studentização, HAC, recálculo por amostra e casos de variância nula; B não está
qualificada pelo protótipo A. Nenhum resultado sintético demonstra cobertura
estatística ou desempenho financeiro do sistema.

## 11. Riscos residuais e aprovação formal pendente

Persistem: apenas um mercado/ativo e aproximadamente um ano por fase; três runs
com mercado compartilhado e possível dependência do provedor; caudas/regimes e
bloco 10 pré-fixado; comportamento adaptativo do risco/estado pode contrariar
estacionariedade; reamostragem de retornos não simula novamente a política;
degeneração por inatividade; anualização protocolar não ajustada à
autocorrelação; dados ajustados e unidades sintéticas conforme limitações já
documentadas; leitura de Validation antes do Final pode influenciar narrativa,
portanto nenhuma mudança de tratamento/teste/threshold após abrir Validation.
Seed fixa torna a análise reproduzível em ambiente identificado, sem garantir
resultados bit a bit em versões diferentes; guardar ambiente e artifacts.

Decisões que exigem manifestação dos autores e orientador antes do freeze:

1. Aprovar H0_2/HA_2, B&H único primário, escopo condicional e Final único
   confirmatório, mantendo H1 e Validation descritiva?
2. Aprovar R=3 em cada fase, média de Sharpes, divulgação integral e ausência
   de seleção/reposição orientada por desempenho?
3. Escolher previamente **A basic** com suas limitações ou **B studentizado**
   com qualificação adicional, inclusive B/seed/bloco, rank, empates,
   degenerações e conclusão estatística? Nenhuma escolha foi feita aqui.
4. Aprovar specs SMA50/200 e Bollinger20/2, diferença do legado, ddof=1,
   inicialização em caixa, igualdades e HOLD em bandas colapsadas?
5. Aprovar MAR/rf=0, flags/null do Sortino e turnover executado/capital inicial,
   com ambos os lados e sem fechamento terminal fictício?
6. Confirmar warmup inclusivo 504=503+1, decision_end/settlement das duas fases,
   release apenas por integridade/completude/identidade e tratamento da
   sensibilidade de custos sem novas inferências?

Não foi preenchida assinatura ou resposta em nome dos autores. Próximo passo
permitido: revisão e aprovação formal dessas escolhas; depois, implementar e
qualificar apenas a camada de avaliação escolhida e retomar o desenho do System
Freeze. **System Freeze não executado; Validation e Final Test NOT EXECUTED.**

Estado de saída:
`H2_V6 EVALUATION AMENDMENT PROPOSED — AWAITING AUTHOR APPROVAL`.
