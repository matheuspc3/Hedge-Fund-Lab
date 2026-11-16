# Análise dos Dados de Produção — Camada de Carteiras Pessoais

## Natureza dos dados

Os arquivos exportados do painel de produção (`dados-producao/*.json`) correspondem às
carteiras pessoais do produto, **não** à avaliação científica do experimento H2. As
evidências da natureza dos dados estão nos próprios arquivos:

- `nature: "SIMULATION"`;
- `classification: "LOCAL_FROZEN_RADAR_RAW_REFERENCE_NOT_LIVE"`;
- `read_only: true`;
- `history_basis: "ECONOMIC_DATE_REPLAY_WITH_CURRENT_CORRECTIONS"`.

Trata-se da camada operacional determinística (DP-31), executada sobre o motor de
replay econômico com correções atuais, e não de inferência por modelos de linguagem.
Os lançamentos da carteira "Multiagentes" apresentam `origin: "MANAGER"`, isto é,
regras determinísticas do gestor, e não decisões de agentes baseados em LLM. Nenhuma
inferência real e auditável de LLM foi executada neste período, de modo que estes
dados não constituem evidência de desempenho dos agentes.

## Configuração

- Início: D0 = 13/10/2026, capital inicial de R$ 100.000,00 por carteira (DP-10).
- Último fechamento: 10/11/2026.
- Universo: BBAS3, ITUB4, PETR4, VALE3, WEGE3.

## Comparação entre as carteiras

| Carteira | Patrimônio final | Retorno (inception) | Trades pós-entrada | Posições finais |
|---|---|---|---|---|
| Buy & Hold | R$ 85.882,85 | −14,12% | nenhum | 5 |
| Bollinger 20/2 | R$ 85.882,85 | −14,12% | nenhum (`trades: []`) | 5 (idênticas) |
| SMA 50/200 | R$ 85.882,85 | −14,12% | nenhum (`trades: []`) | 5 (idênticas) |
| Multiagentes | R$ 78.270,16 | −21,73% | 11 lançamentos `MANAGER` | 4 (VALE3 liquidada) |

## Achados

1. **Equivalência Buy & Hold ≡ Bollinger ≡ SMA.** As três carteiras fecham com o mesmo
   patrimônio (R$ 85.882,85) e o mesmo retorno acumulado (−14,12%). As estratégias
   Bollinger 20/2 e SMA 50/200 **não produziram nenhum sinal de negociação** nas ~20
   sessões observadas; `positions_through` permanece em "2026-10-14", congelado na
   entrada inicial. No regime observado, ambas degeneraram em buy-and-hold passivo.
   Não há evidência, neste recorte, de que os gatilhos dessas estratégias estejam ativos.

2. **A carteira gerenciada por regras determinísticas teve retorno inferior ao
   benchmark passivo.** A carteira Multiagentes realizou 11 lançamentos de origem
   `MANAGER` e encerrou 7,6 pontos percentuais abaixo (−21,73% contra −14,12%).
   A explicação está nos próprios lançamentos: venda integral de VALE3 (que
   posteriormente se recuperou para R$ 64,80, próximo ao preço de entrada de
   R$ 67,16) e sobreponderação de ITUB4 e PETR4 (que apresentaram as maiores quedas
   do período: ITUB4 ≈ R$ 48,98 → R$ 41,20; PETR4 ≈ R$ 58,11 → R$ 44,95).

3. **Queda generalizada em 26/10/2026.** As quatro carteiras foram afetadas por um
   recuo em bloco em 26/10/2026, com quedas diárias expressivas em BBAS3
   (24,19 → 17,47), ITUB4 (48,98 → 41,70), PETR4 (58,11 → 53,88) e WEGE3
   (50,44 → 44,53). A VALE3 foi o ativo de menor queda no período
   (67,16 → 64,80), justamente o ativo integralmente descartado pela carteira
   Multiagentes.

4. **Proventos irrelevantes no recorte.** Apenas o JCP de ITUB4 ("JRS CAP PROPRIO",
   data-com 30/10/2026, R$ 6,21 a receber em 01/12/2026), sem efeito material sobre
   as conclusões.

## Implicações para a monografia

Estes dados evidenciam o funcionamento da **camada operacional do produto** (ledger
selado, replay econômico com correções e carteiras pessoais determinísticas), e não o
experimento científico H2. Para os capítulos 6–7, o registro factual passível de
documentação é o seguinte: no período observado, as estratégias determinísticas
Bollinger 20/2 e SMA 50/200 não produziram sinais, equivalendo a buy-and-hold, e a
carteira gerenciada por regras determinísticas apresentou retorno inferior ao
benchmark passivo (−21,73% contra −14,12%).

A comparação científica H1/H2 contra benchmarks permanece **bloqueada**: a inferência
real e auditável de LLM não foi executada, e os resultados do `MockLLMClient` não
devem ser interpretados como desempenho real dos agentes (ver `WRITING_RULES.md`).

## Carteiras registradas

A lista completa de carteiras (`GET /api/portfolio/manual`, reproduzida em
`dados-producao/carteiras.json`) contém exatamente quatro carteiras, todas de
natureza `SIMULATION` e capital inicial de R$ 100.000,00:

| ID | Nome | Estratégia | Cash |
|---|---|---|---|
| `manual-bf4d687c03594170b0e2a2bcaa39fa46` | Buy & Hold | `BUY_HOLD` | 177,44 |
| `manual-5be40ea8853a476e94b799b6d45389ed` | Multiagentes | `MULTIAGENT` | 3.578,33 |
| `manual-2c502a1d13774277b647f6e0bc92ec2f` | SMA 50/200 | `SMA_50_200` | 177,44 |
| `manual-e671a60b08d54c52991b93ed7cbff122` | Bollinger 20/2 | `BOLLINGER_20_2` | 177,44 |

Os IDs correspondem, um a um, aos arquivos de estratégia analisados. A carteira de
estratégia `MULTIAGENT` opera com regras determinísticas de gestor (`origin:
"MANAGER"`), não com inferência de LLM.

## Evidências

- `dados-producao/buy-hold.json`
- `dados-producao/bollinger-20-2.json`
- `dados-producao/sma-50-200.json`
- `dados-producao/multiagentes.json`
- `dados-producao/carteiras.json` (lista de carteiras — saída de `GET /api/portfolio/manual`)
