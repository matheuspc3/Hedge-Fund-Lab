# Premium V5 — carteira compartilhada offline

Identidade `HFL-MULTIASSET-PORTFOLIO-V1`. Implementação exclusivamente sintética,
sem Gemini, corretora ou executor prospectivo. Referência metodológica:
[projeto aprovado na V4](HFL_MULTIASSET_PORTFOLIO_DESIGN.md).

## Inspeção anterior à implementação

Reutilizar JSON canônico, SHA256, publicação atômica com fsync e lock local já
existentes; adaptar leitura íntegra de pareceres completos do Radar, sem gravar
na sua raiz. Servidor HTTP stdlib, allowlist e proteção de origem permanecem.
Não reutilizar o estado escalar de `LLMParticipant`, o executor
`fractional_notional`, a reescala de unidades por retorno total do Forward,
aprovações supervisionadas nem o sizing Kelly. O MinVariance existente descarta
histórico insuficiente e tem fallback equal weight: inadequado ao novo gate.
Risk original mede concentração de um ativo; Risk global precisa de covariância.

Contratos existentes examinados: state/input/decision/reconciliation do Forward,
aprovações write-once e cadeia de auditoria supervisionada, inputs, claims,
envelopes e selos do Radar. O novo journal usa eventos com sequência, timestamp,
hash anterior e hash próprio. Apenas ele autoriza reconstrução do estado;
snapshot e arquivos por contrato são projeções recuperáveis.

Risco científico: o manifesto enumera todos os arquivos Python em `src/`.
Nenhum arquivo será adicionado ou alterado ali; manifesto, artefatos congelados,
ledgers e Radar existentes terão hashes conferidos. Código fica em scripts e
dashboard, dados em `data/portfolio/hfl_multiasset_v1/demo-*/`.

## Política DEMO_ACCOUNTING_V1

Esta política é fixture para qualificação, **não aprovação metodológica para
execução prospectiva**. BRL, unidades inteiras no fracionário, preços brutos em
centavos. Decimal para preço, dinheiro, unidades, custo e peso. Dinheiro
arredondado HALF_EVEN ao centavo; pesos exibidos com 12 casas, resíduo no caixa;
custo médio exibido com 8 casas. O custo remanescente em centavos é a autoridade,
evitando acumular erro da média exibida. Venda baixa custo proporcional arredondado;
venda total baixa todo o saldo. Taxa ilustrativa de 0,1% por operação, sem
imposto sobre renda ou slippage; resultados são pré-IR. Custos de compra integram
custo de aquisição; custos de venda reduzem receita. Não confundir essa taxa com
tarifa oficial nem com os custos congelados H2.

Compra é pré-financiada: debita caixa no trade e reconhece posição econômica,
mas unidades ficam indisponíveis até confirmação de liquidação. Venda reduz
posição e cria recebível líquido. Sem netting, crédito ou venda descoberta.
Reservas continuam no patrimônio. Dividendos/JCP são fluxos explícitos brutos,
retenção e líquidos fornecidos pela fonte, não estimativas fiscais. Desdobramento,
grupamento e bonificação preservam custo; evento com fração ou reconciliação
incompleta bloqueia ativo, sem inventar venda de fração ou provento. Séries
ajustadas são usadas somente nos retornos de risco.

## Liquidação verificada em 11/10/2026

Ações à vista: [D+2, B3](https://borainvestir.b3.com.br/glossario/data-de-liquidacao/).
Calendário: [OC 041/2026-VNC, 30/06/2026](https://www.b3.com.br/data/files/20/57/01/AA/06A1F910ADC36BE9AC094EA8/OC%20041-2026-VNC%20ERRATA%20-%20CALENDARIO%20DE%20FERIADOS%20EM%202026_PT.pdf),
Quadro A e item 1.1 (inclusive 24/12 e 31/12 sem liquidação na Câmara B3).
O OC 054/2025 foi revogado pelo 003/2026, retificado pelo 041/2026; não usar o
documento revogado como regra vigente. O [projeto D+1](https://b3.com.br/pt_br/noticias/liquidacao-d-1.htm)
não equivale à mudança já implantada. Calendário local B3 v2 coincide com esses
dias de ações em 2026; uso restringe-se a esse ano e exige confirmação explícita,
nunca liberação pelo simples avanço do relógio. Trade em 09/10 liquida em
14/10, após fim de semana e feriado. Fora de 2026, bloquear até novo calendário.

## Decisões pendentes para um piloto real

Autorizar separadamente: janela/anualização e limites globais; tarifas, slippage,
tributação, frações e direitos de proventos; feed bruto oficial com timestamp,
eventos corporativos reconciliados e confirmação de custódia/caixa; calendário e
ciclo vigentes; relógio prospectivo e prazo de aprovação; identidade do operador.
Sem essas decisões, somente a parte prospectiva fica bloqueada. Não há botão,
flag ou comando para habilitá-la nesta versão.

## Arquitetura entregue

| Arquivo | Responsabilidade |
|---|---|
| `scripts/multiasset_portfolio.py` | Decimal, posição/custo remanescente, reservas, fills, recebíveis, confirmações, eventos corporativos, reducer puro e Store durável |
| `scripts/multiasset_manager.py` | Adapter somente leitura V4, risco por covariância, PortfolioProposal, FakePortfolioManager, validação independente e aprovação sintética |
| `scripts/run_multiasset_portfolio.py` | Comandos demo/status/verify/recover e seis cenários em memória |
| `dashboard/portfolio_api.py` | GET allowlisted, verifica cadeia e selo do demo antes de projetar resultados |
| `dashboard/portfolio.html`, `.css`, `.js` | Minha carteira, risco, pareceres, comparação de alocação, operações, cenários A–E e auditoria |
| `dashboard/server.py`, `paper.html` | Rotas/assets da nova área e link na navegação operacional |
| `tests/test_multiasset_portfolio.py` | Checks financeiros, contratos, recovery, HTTP e preservação |
| `.gitignore`, `README.md` | Dados de carteira isolados fora do Git; entrada para documentação e evidências |

Não há nova dependência. Numpy/pandas existentes calculam estatísticas; Chart.js
local existente desenha alocações. Nenhum download de biblioteca/CDN na interface.
O layout reutiliza a folha de estilos do Radar, sem alterar seus bytes.

Fluxo: pareceres e marcas → Risk global → proposta DEMO_RULE_BASED → validador
independente → aprovação fixture → reserva → execução virtual sintética →
confirmação de liquidação. A interface disponibiliza somente a parte de leitura
e simulação em memória. O CLI demo exercita a persistência das demais etapas.

## Contratos financeiros e integridade

JSON canônico UTF-8 v1; valores financeiros são strings Decimal. Estado:
`settled_cash`, `positions{quantity,reserved,unsettled,basis}`, `pending`,
`executions`, `receivables`, `settlements`, `costs`, `realized_pnl`, `income_net`,
`peak_equity`, `marks`, `as_of_session`, `blocked`. A view deriva quantidade
disponível, preço médio, valor de mercado, PnL não realizado, pesos e patrimônio.

`equity = settled_cash + receivables + Σ(quantity × raw_mark)`.
`cash_available = settled_cash - cash_reserved`. Reservas não reduzem patrimônio.
Também se verifica a identidade contábil:
`equity = initial_capital + realized_pnl_net + income_net + unrealized_pnl`.
Compra capitaliza custos na base; venda reconhece custos no resultado realizado.
Não subtrair custos duas vezes. Não há crédito ou conta a pagar financiável.

Uma proposta vincula identidade, portfolio_id, sessão, instante, validade,
state hash, hashes de **todos** os pareceres fornecidos, marcas, Risk e política;
pesos atuais/alvos/caixa, operações, prioridades, dependências e justificativa.
Cada operação possui ID estável, ticker, lado, quantidade inteira, preço-limite,
custo máximo e financiamento. Pesos são intenções: quantidades inteiras e custos
produzem pesos efetivos explicitamente recalculados, sem correção silenciosa.
Plano sem operação exige alvos iguais à carteira atual. Declarações de pesos
não autorizam gastar caixa nem contornar limites de exposição pós-custo.

A aprovação vincula proposta exata, Risk, política, marcas, hash financeiro,
operações e máximos, ação e prazo. O hash financeiro exclui somente os registros
administrativos imutáveis de propostas/aprovações/contextos: registrar a própria
aprovação não muda caixa, preços, ordens ou posições. Qualquer mudança financeira
invalida a aprovação. IDs e hashes dos eventos administrativos permanecem na
cadeia. A reserva de uma proposta registrada reexecuta o validador global;
o fill exige o hash exato do estado reservado. O motor aceita uma aprovação
`proposal_sha256="fixture"` apenas como entrada de testes contábeis sintéticos;
nenhuma rota HTTP ou comando aceita esse payload do usuário/modelo.

Um basket local é reservado atomicamente com financiamento independente de
vendas no mesmo trade. Fills são simulados sequencialmente por prioridade/ID e
checados a cada passo; somente o evento completo publica o efeito. A V1 não
simula preenchimento parcial de uma ordem na corretora: uma falha antes da
publicação não publica nenhum fill do basket. Quantidades parciais de **venda de
posição** são suportadas. Planos dependentes mantêm a compra adiada: o cálculo
condicional não vira caixa; recebimento exige nova proposta e aprovação.

Persistência por carteira:

```text
events/00000001.json …   # autoridade: payload, seq, ID, UTC, hash anterior/próprio
snapshot.json           # checkpoint com hash e referência à cabeça da cadeia
proposals/*.json        # projeções imutáveis dos contratos nos eventos
validations/*.json      # validações seladas, incluindo erros e projeções
approvals/*.json        # aprovações/rejeições de demonstração, sem reuse H2
demo.json               # exemplos A–E, contexto e cabeça final selados
operation.lock          # exclusão entre processos; PID; sem expiração automática
```

INITIALIZED congela política e hashes dos três módulos do motor/gestor/CLI.
Mudança desses bytes bloqueia o ledger anterior: não atualizar seu selo para
fingir o mesmo tratamento. Crie uma nova identidade de carteira sintética.
O manifesto científico original não é atualizado. Eventos são publicados por
fsync + rename no mesmo diretório, sob lock. Snapshot é gravado depois. Crash
antes do evento: nenhum efeito; depois: replay do evento e reconstrução das
projeções. Comando já persistido com mesmo ID/payload é idempotente; payload
diferente é conflito. Snapshot adulterado, cadeia quebrada ou projeção alterada
bloqueiam recuperação. Snapshot ausente/atrasado é reconstruível. `load`, `view`,
`verify` e GET nunca reparam ou gravam. `recover` é comando explícito offline;
completa um basket reservado usando somente autorização e instante originais.

Limite conhecido: leitura reproduz todos os eventos (custo cresce com o ledger),
lock local e arquivo atômico único. Um processo morto pode deixar lock: diagnosticar
PID antes de remover **somente** o lock; nunca apagar eventos/reservas/aprovações
para repetir ordem. Uma reescrita maliciosa de todos os hashes locais não é
autenticada por assinatura externa; os hashes detectam alteração e divergência
em relação aos selos/evidências preservados, não substituem custódia de auditoria.

## Risk global e política de demonstração

| Parâmetro | Fixture V1 | Justificativa / limite |
|---|---:|---|
| Concentração por empresa | 40% | Exercitar seleção de poucas empresas com teto independente |
| Exposição total | 85% | Manter margem de caixa no exemplo |
| Volatilidade anualizada | 35% | Exercitar veto da covariância, sem calibrar desempenho |
| Drawdown consolidado | 20% | Gate ilustrativo sobre pico contábil |
| Turnover por sessão | 100% do equity | Gate cumulativo de movimentos, não reiniciado por proposta |
| Custos por sessão | 1% do equity | Gate cumulativo de custos previstos e executados |
| Operações por sessão | 10 | Limitar o workflow sintético, independente do limite de ativos |
| Janela / anualização | 60 retornos / 252 | 61 fechamentos ajustados coincidentes; escolha didática |

Esses valores não foram selecionados por backtest e **não são limites H2 v6**.
São fixtures versionadas para verificar infraestrutura. Exigir aprovação própria
para um estudo/piloto. Universo inicial de cinco ações não limita a estrutura
interna do estado, que usa mapas de ticker. O catálogo inicial da demonstração
é PETR4, VALE3, ITUB4, WEGE3, BBAS3.

Retornos sem fill (`pct_change(fill_method=None)`), covariância amostral ddof=1,
`σ = sqrt(252 × wᵀΣw)`. A grade precisa conter as últimas 61 sessões completas
em todos os ativos expostos. Falta, duplicidade, NaN, histórico curto ou futuro
bloqueia. Correlação indefinida em retorno constante é null, nunca zero inventado.
Uma carteira comprovadamente 100% em caixa tem exposição de mercado zero;
isso não é imputação de dados. Redução para caixa pode ser validada sem depender
de uma previsão de volatilidade; decisão que mantém exposição precisa de
histórico suficiente na projeção. Mesmo sem métricas, manutenção sem operação
é permitida e exibe Risk bloqueado. Setores só são agregados com metadados
selados, fonte declarada e flag confiável; não há teto setorial aprovado.

Pareceres precisam de cinco votos, selo completo, mesma sessão, fonte, modo e
versão compatível. Falsificação/alteração de hashes falha. COMPRA exige parecer
COMPRA aprovado. Reduzir posição diante de outro sinal aprovado exige justificativa
explícita. VETO individual bloqueia qualquer operação no ativo nesta fixture;
parecer ausente permite apenas manter. Confiança não entra em peso/retorno.
Risco atual e projetado são distintos; o validador mede os efeitos dos custos.

## Demonstração e execução local

```powershell
.venv/Scripts/python.exe scripts/run_multiasset_portfolio.py demo
.venv/Scripts/python.exe scripts/run_multiasset_portfolio.py verify
.venv/Scripts/python.exe scripts/run_multiasset_portfolio.py status
.venv/Scripts/python.exe dashboard/server.py 8088
# http://localhost:8088/portfolio
```

Raiz padrão `data/portfolio/hfl_multiasset_v1/demo-qualified-v5/`. Demo existente
não é sobrescrito; use status/verify. Outro exemplo exige `--root` com outro
`demo-*` diretamente sob a raiz. GET não cria demo. `HFL_PORTFOLIO_ROOT` seleciona
uma carteira **sintética** pré-gerada, não um ledger prospectivo.

| Cenário persistido | Efeito sintético |
|---|---|
| A · 09/10 | Compra 499 PETR4, 333 VALE3, 499 ITUB4; mantém WEGE3/BBAS3 sem posição e R$ 45.035,09 em caixa |
| B · 14/10 | Após custódia das compras, vende 100 PETR4; recebível R$ 3.996,00; caixa disponível continua R$ 45.035,09 |
| C · 16/10 | Recebimento confirmado; novas marcas, pareceres, validação e aprovação; compra 70 WEGE3 por R$ 3.503,50 |
| D · 16/10 | `operations: []`; nenhum efeito financeiro |
| E · 16/10 | Pesos 30% + 30% + 30% + 30% = 120%; bloqueado, sem aprovação/execução |

Estado final: patrimônio R$ 99.937,59; caixa disponível R$ 45.527,59;
custos acumulados R$ 62,41; resultado realizado −R$ 8,00 e não realizado
−R$ 54,41. Preços constantes tornam os custos visíveis; **não** são resultados
de previsão da IA. WEGE3 permanece economicamente na carteira, mas suas 70
unidades estão em liquidação, sem disponibilidade para venda imediata.

Relógio/execução dos exemplos são replay sintético à mesma marca da sessão,
depois da geração dos pareceres fictícios. Não modelam preenchimento em pregão
real, não constituem backfill em carteira prospectiva nem autorizam execução
ao fechamento conhecido. Sessões e timestamps de exemplos históricos são
distinguidos do painel atual. Para execução futura real ainda falta definir
abertura/limite, fonte observável no instante e prazo prospectivo antes do trade.

O adapter `radar_opinions` + `adjusted_histories` lê V4 já selada e verifica
result/input/bars/provider-journal; não chama agentes, cria claim ou grava.
A demonstração usa fixtures próprias em vez de atribuir timestamp histórico
fictício aos pareceres V4 realmente gerados em 11/10. As análises V4 locais
permanecem integralmente preservadas.

API: somente GET `/api/portfolio/status`, `/api/portfolio/scenario?name=…`
(buy, sell_cash, partial, rebalance, hold, rotation) e `/api/portfolio/case?case=A…E`.
Host/Origin e allowlist herdados; query duplicada/extra e diretório fornecido
pelo cliente são recusados. Não existe POST de aprovação/execução nesta área.

## Qualificação

```powershell
.venv/Scripts/python.exe tests/test_multiasset_portfolio.py -v
.venv/Scripts/python.exe -m ruff check scripts/multiasset_portfolio.py scripts/multiasset_manager.py scripts/run_multiasset_portfolio.py dashboard/portfolio_api.py dashboard/server.py tests/test_multiasset_portfolio.py
node --check dashboard/portfolio.js
```

Evidências, logs de teste, inventário de preservação, arquivo ZIP completo e
capturas Chrome em [evidence/hfl_multiasset_portfolio](evidence/hfl_multiasset_portfolio).
O inventário cobre 10.922 arquivos científicos, ledgers locais e Radar V4.
Logs HTTP e locks voláteis são excluídos; não são estados financeiros.
Os testes verificam leitura sem alterações, bloqueio de rede externa, chamadas
Gemini proibidas, origem HTTP e ausência de rota executável.
