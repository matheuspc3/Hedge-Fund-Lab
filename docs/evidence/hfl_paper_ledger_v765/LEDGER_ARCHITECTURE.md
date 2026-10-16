# Arquitetura e catálogo de eventos

Identidade operacional: `HFL-MULTIASSET-PAPER-LEDGER-V1`, schema 1. `scripts/paper_ledger.py` envolve o redutor puro V5 e `multiasset_manager.validate/risk`, sem alterar seus bytes. `qualify_paper_ledger.py` é um produtor de fixtures offline, não um runner oficial. PostgreSQL, H2, Radar, Gemini e corretoras não participam da escrita.

```text
fixture estruturada → proposta V5 → validação determinística V5
→ autorização sintética vinculada → reserva → execução sintética
→ confirmação D+2 → observação RAW → valorização → reconciliação
→ eventos + checkpoint transacionais → exportação de qualificação
→ GET verificado → dashboard (opt-in de demonstração)
```

O envelope mantém metadados, referências consultivas, proveniência de preços, validações, autorizações, identidades de fills/liquidações, indisponibilidades, reconciliações e snapshots por sessão. O subestado `financial` continua integralmente sob autoridade do motor V5. Não há contabilidade JavaScript nem outro motor financeiro.

Cada carteira tem ID estável, versão, nome, identidade científica (null nos testes), classificação, BRL, capital inicial, data econômica de criação, status OPEN/CLOSED, política financeira V5, fontes permitidas, IDs de autorização e proveniência. Datas de registro reais ficam nos eventos, separadas das datas econômicas históricas das fixtures.

| Classificação | Semântica |
|---|---|
| SYNTHETIC_TEST | qualificação isolada; única classificação admitida pelo escritor desta versão |
| CONSULTATIVE_SNAPSHOT | referência informativa; nunca posição ou ordem |
| PAPER_ACTIVE | contrato reservado para ativação futura; criação rejeitada nesta versão |
| PAPER_CLOSED | carteira oficial encerrada no contrato futuro; criação rejeitada nesta versão |

Fechar uma fixture muda seu status, preservando a classificação SYNTHETIC_TEST. É proibido promover snapshots ou reutilizar identidade científica H2. Um banco pode armazenar carteiras separadas; cada cadeia/checkpoint é identificado por portfolio_id.

## EVENT_SCHEMA

Todos os eventos possuem `event_id` UUID, `portfolio_id`, `ledger_version`, `kind`, `schema_version`, sequência, `recorded_at` UTC real, `session`, `economic_date`, `effective_at` com timezone, `source`, `payload`, `sha256`, `previous_sha256`, `idempotency_key`, `authority`, `authorization_ref` (null quando não aplicável). Serialização canônica ordenada, SHA-256 e valores financeiros em strings decimais. Sessão/data econômica têm de coincidir com effective_at; registro e tempo econômico nunca retrocedem dentro da cadeia.

| Evento implementado | Efeito / adaptação V5 |
|---|---|
| PORTFOLIO_CREATED | INITIALIZED; capital e metadados em uma transação |
| PROPOSAL_REFERENCED | referência consultiva oficial por ID e hashes; sem efeito financeiro |
| PROPOSAL_LINKED | PROPOSED sintético estruturado + contexto; não é execução |
| VALIDATION_RECORDED | recomputa validate; aceita resultado aprovado ou rejeitado como evidência |
| AUTHORIZATION_RECORDED | exige validação válida, identidade, escopo, hashes e validade; APPROVED V5 |
| PAPER_ORDER_CREATED | RESERVED; cesta explícita aprovada, fonte sintética, limites e saldo |
| PAPER_ORDER_CANCELLED | CANCELLED; libera reservas, não libera reutilização de order_id |
| PAPER_ORDER_EXECUTED | FILLED; alterações financeiras determinadas uma vez pelo V5 |
| SETTLEMENT_RECORDED | SETTLED; identidade própria, fonte de confirmação, cobertura D+2 |
| MARKET_PRICE_OBSERVED | valida e registra proveniência, sem mudar custódia/caixa |
| PORTFOLIO_VALUED | MARKED; se faltar preço, registra indisponibilidade sem inventar marca |
| PORTFOLIO_RECONCILED | registra diagnóstico; somente sucesso publica ponto histórico |
| PORTFOLIO_CLOSED | bloqueia novos eventos; exige zero posições/obrigações e estado consistente |

Não há eventos financeiros derivados POSITION_UPDATED ou CASH_INITIALIZED: seriam duplicação dos efeitos já determinados por criação/fill. VALUATION e EXECUTION continuam distintos. Liquidação não recalcula custo nem lucro. Repetir chave com o mesmo pedido retorna o evento existente; repetir com pedido distinto falha.

`order_id` é `operation_id` do V5, consumido também em cancelamento. `execution_id` identifica um fill de cesta; várias pernas da mesma cesta apontam para ele, mas outra cesta não pode reutilizá-lo. `settlement_id` é único por confirmação; cada order_id liquida uma única vez. `idempotency_key` identifica o comando completo, incluindo tempo econômico, autoridade e autorização. ID do evento é independente dessas identidades.

O tratamento de custos/limites continua didático V5. Identidade operacional nova não constitui modelo LLM novo nem tratamento científico aprovado.
