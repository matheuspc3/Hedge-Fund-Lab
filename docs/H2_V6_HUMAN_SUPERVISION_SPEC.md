# H2 v6 supervisionada — especificação técnica (revisão 3)

**Estado:** implementada no Premium V2 por
[`scripts/run_h2_v6_supervised.py`](../scripts/run_h2_v6_supervised.py).
A revisão 1 era só proposta; esta revisão incorpora os ajustes técnicos de
posições divergentes, preços brutos × ajustados, máquina de estados e
recuperação. O runner original `scripts/run_h2_v6_forward.py`, a decisão de
09/10/2026, os ledgers existentes e a identidade H2 v6 não mudam.

## 1. Separação das estratégias

| | H2 v6 original | H2 v6 supervisionada (`h2_v6_supervised`) |
|---|---|---|
| Decisão | agentes (Gemini) | a mesma `decision.json`, verificada por SHA256; nenhuma chamada nova |
| Ledger | `data/forward/h2_v6_paper/state.json` | `data/forward/h2_v6_supervised/state.json` |
| Ordens | toda intenção `DECIDED` vira alvo na abertura T | só propostas aprovadas que passam nos limites |
| Aprovações | nunca consulta | `approvals/<S>.json`, `approvals/<S>.cancel.json` |
| Natureza | tratamento congelado | tratamento + julgamento humano não cego |

A supervisionada só lê arquivos do Forward Test original. Capital R$ 100.000,
custos, execução fracionária, calendário, manifesto e convenção de preços
ajustados são os mesmos (`fwd.new_state`, `fwd.reconcile`, `ExecutionEngine._settle`).

A diferença de patrimônio entre as duas mede o efeito do filtro humano
*daquela pessoa, naquele período*, com amostra pequena e julgamento não cego.
A interface descreve a divergência; não afirma causalidade estatística.

## 2. Inicialização

Mesmo gate dos benchmarks: só é possível criar a carteira supervisionada
enquanto o ledger original tem apenas a sessão de início e a abertura-alvo dela
ainda está no futuro. Início comum: fechamento de 09/10/2026, em caixa.
Depois disso, `sync` recusa `NOT_COMPARABLE` e nenhuma aprovação, timestamp ou
operação é reconstruída. Um início posterior exigiria nova identidade e seria
exibido como não comparável.

## 3. Da decisão original à proposta supervisionada

A direção vem só de campos validados: `status`, `record.final_cause` e a
intenção gravada, conferida contra a causa. O texto dos agentes nunca é
interpretado.

| `final_cause` original | Direção | Proposta para a supervisionada |
|---|---|---|
| `ACTION_BUY` | COMPRA (alvo `long_target_weight`) | aguarda aprovação se o peso supervisionado estiver abaixo do alvo; senão `SEM_ORDEM_NECESSARIA` |
| `ACTION_SELL` | VENDA (alvo 0) | aguarda aprovação se houver unidades; senão `SEM_ORDEM_NECESSARIA` |
| `TECH_EXPLICIT_HOLD`, `TECH_NO_MAJORITY`, `PORTFOLIO_HOLD` | MANTER | `SEM_ORDEM_NECESSARIA`: posição supervisionada preservada |
| `RISK_VETO_*` | veto | `SEM_ORDEM_NECESSARIA`, com a causa registrada |
| `BUY_AT_TARGET_NOOP` | COMPRA técnica sem aprovação de Risk/Portfolio | sem ordem; `SEM_DECISAO` se a supervisionada não estiver no alvo |
| falhas, `INVALID_*`, `PROVIDER_*`, `NOT_ELIGIBLE` | — | `SEM_DECISAO` |
| status `FAILED`, `LATE_NOT_EXECUTABLE`, sessão MISSED | — | `SEM_DECISAO` |

Regras de posição divergente:

- COMPRA nunca reduz exposição e VENDA nunca aumenta. Se a execução na abertura
  exigir o lado contrário (deriva de preço, limite de concentração), não há operação.
- MANTER nunca vira compra ou venda para igualar as carteiras.
- Risk Manager e `BUY_AT_TARGET_NOOP` avaliaram a **carteira original**
  (drawdown, concentração, peso observado). A supervisionada não reinterpreta um
  veto nem promove uma COMPRA não aprovada; esse limite é declarado na interface.

## 4. Preços brutos × ajustados

| Uso | Base | Origem |
|---|---|---|
| Preço máximo de compra, mínimo de venda, gap | **bruto oficial B3** | fechamento bruto de S: `sessions/S/input.json → last_bar_official_raw`; abertura bruta de T: `sessions/T/input.json`, ou o COTAHIST em cache se o SHA256 dele for o registrado no `input.json` mais recente |
| Liquidação, patrimônio, retorno, proventos | **ajustado** | `bars.csv` da última sessão, exatamente como na original |

Antes de executar, a sessão T precisa ser coerente nas duas bases: o fator
`ajustado/bruto` da abertura deve igualar o do fechamento (tolerância 1e-6, a
mesma do extrator B3). Se o bruto estiver ausente ou o fator divergir, a ordem
fica `BLOQUEADA_BASE_PRECOS` e a causa é exibida. Abertura e fechamento nunca
são comparados entre bases diferentes. A execução registra os dois preços e a
origem de cada um.

## 5. Limites

Todos opcionais, verificados no backend; valores não numéricos, não finitos,
fora do intervalo ou incoerentes com a direção são recusados.

| Campo | Direção | Intervalo | Verificação |
|---|---|---|---|
| `max_buy_price` | COMPRA | 0 < x ≤ 1.000.000 (R$, bruto) | reconciliação: abertura bruta > limite → `NAO_EXECUTADA_LIMITE_PRECO` |
| `min_sell_price` | VENDA | 0 < x ≤ 1.000.000 (R$, bruto) | reconciliação: abertura bruta < limite → `NAO_EXECUTADA_LIMITE_PRECO` |
| `max_gap_up` | ambas | 0 < x ≤ 1 | reconciliação: abertura/fechamento brutos − 1 > x → `NAO_EXECUTADA_GAP` |
| `max_gap_down` | ambas | 0 < x ≤ 1 | reconciliação: 1 − abertura/fechamento brutos > x → `NAO_EXECUTADA_GAP` |
| `max_concentration` | COMPRA | 0 < x ≤ 1 | na aprovação: alvo = min(alvo, x) → `AJUSTADA_CONCENTRACAO`; se o peso já atinge x, `SEM_ORDEM_NECESSARIA` |
| `max_volatility` | ambas | 0 < x ≤ 10 | na aprovação: `risk_metrics.recent_volatility` **gravada na sessão original** > x, ou ausente → `BLOQUEADA_VOLATILIDADE` |

A ordem é liquidação na abertura (leilão) condicionada ao preço oficial: executa
ao preço de abertura de T se todos os limites passarem; senão não executa
naquele dia. Não há inferência de preenchimento intradiário pela máxima/mínima.
Um feed intradiário futuro seria fonte separada e só informativa.

Concentração limita o peso **logo após a liquidação, descontados os custos**.
Para uma compra com posição inicial A, patrimônio E na abertura, alvo t e custo
proporcional c, o notional adicional é `(t * E - A) / (1 + t * c)`.
Somente a supervisionada ajusta o peso enviado ao motor congelado; preços,
custos e liquidação continuam os mesmos. Deriva posterior no fechamento pode
ultrapassar o peso de abertura e não provoca rebalanceamento automático.

## 6. Máquina de estados

```text
proposta ─► SEM_DECISAO | SEM_ORDEM_NECESSARIA                         (terminais)
proposta ─► AGUARDANDO_APROVACAO ─┬─ rejeitar ─► REJEITADA
                                  ├─ prazo ────► EXPIRADA
                                  └─ aprovar ──► APROVADA | AJUSTADA_CONCENTRACAO
                                                 | BLOQUEADA_VOLATILIDADE | SEM_ORDEM_NECESSARIA
APROVADA | AJUSTADA_CONCENTRACAO ─┬─ cancelar (antes do prazo) ─► CANCELADA
                                  └─ prazo ─► PENDENTE_ABERTURA ─► (reconciliação de T)
       EXECUTADA | NAO_EXECUTADA_LIMITE_PRECO | NAO_EXECUTADA_GAP
       | BLOQUEADA_BASE_PRECOS | SEM_ORDEM_NECESSARIA
```

- O backend calcula o estado a partir de registros imutáveis e do relógio; a
  interface apenas o exibe.
- Aprovar ou rejeitar só em `AGUARDANDO_APROVACAO`, depois de `generated_at` da
  decisão e antes de `target_open_deadline`. Cancelar só em `APROVADA` ou
  `AJUSTADA_CONCENTRACAO`, antes do prazo.
- `APROVADA` significa aprovada e ainda cancelável. Passado o prazo, vira
  `PENDENTE_ABERTURA`: o preço oficial ainda não foi observado. `EXECUTADA` só
  existe depois da reconciliação com o fechamento de T.
- Nada é editado: uma aprovação por sessão (`O_CREAT|O_EXCL`), no máximo um
  cancelamento, cada um com evento próprio.

## 7. Registro de aprovação

```json
{
  "kind": "H2_V6_SUPERVISED_ACTION", "schema_version": 1,
  "strategy": "h2_v6_supervised", "action": "APPROVE",
  "decision_session": "2026-10-09", "target_session": "2026-10-13",
  "decision_sha256": "…", "input_sha256": "…",
  "limits": {"max_buy_price": 57.3, "max_concentration": 0.8},
  "effect": {"state": "AJUSTADA_CONCENTRACAO", "target_weight": 0.8, "reason": "…"},
  "created_at": "2026-10-10T21:02:11-03:00",
  "expires_at": "2026-10-13T10:00:00-03:00",
  "idempotency_key": "sha256(h2_v6_supervised|2026-10-09|decision_sha256)",
  "previous_audit_sha256": "…"
}
```

Rejeição: `action = REJECT`, sem limites. Cancelamento: arquivo
`<S>.cancel.json`, `action = CANCEL`, com `approval_sha256`. O servidor é local
e não autentica pessoas; não há campo de identidade do operador.

## 8. Auditoria e recuperação

`audit.jsonl` é append-only. Cada linha tem `seq`, `event` (`PROPOSED`,
`APPROVED`, `REJECTED`, `CANCELLED`, `RESOLVED`), `session`, `record_sha256`,
`recorded_at`, `previous_sha256` e o próprio `sha256`.

As fontes de verdade são os arquivos write-once e o `state.json`, que é
trocado de forma atômica. O journal é derivado deles e reparado de forma
determinística no início de cada operação:

| Queda entre | Recuperação |
|---|---|
| aprovação gravada → evento | o evento ausente é anexado a partir do arquivo, com o `created_at` original |
| evento → liquidação | nada liquidado; o próximo `sync` recalcula o mesmo resultado |
| liquidação → `state.json` | a liquidação é só em memória; o `sync` seguinte refaz a mesma conta |
| `state.json` → eventos `RESOLVED` | eventos anexados a partir do estado salvo |
| linha do journal incompleta | a cauda sem `\n` é descartada e o evento é derivado novamente |

Duplicidade é impossível: a liquidação só ocorre para sessões depois da marcação
salva, e repetir `sync` na mesma sessão não escreve nada novo. Nenhum comando
apaga aprovações, decisões ou reservas. `verify` confere offline a cadeia, a
correspondência evento ↔ registro, o SHA da decisão, prazos e execuções sem
aprovação.

Antes de aceitar uma ação humana ou reconciliar a carteira, o backend recupera
eventos ausentes e exige auditoria íntegra, incluindo os hashes da decisão e do
input original. Adulteração bloqueia a operação com
`supervision_integrity_failed`; não basta mostrar o erro na consulta. A
recuperação só completa eventos ausentes, nunca legitima registros alterados.

## 9. Endpoints

| Método | Endpoint | Efeito |
|---|---|---|
| GET | `/api/forward/supervision` | estado, propostas, ações, resultados, linha do tempo, verificação da auditoria |
| POST | `/api/forward/supervision/approve` | `{confirm:true, decision_session, decision_sha256, limits:{…}}` |
| POST | `/api/forward/supervision/reject` | `{confirm:true, decision_session, decision_sha256}` |
| POST | `/api/forward/supervision/cancel` | `{confirm:true, decision_session, decision_sha256}` |
| POST | `/api/forward/supervision/sync` | `{}`; job assíncrono com o lock de operações existente |

Mesmo contrato dos POST existentes: loopback, Host exato, Origin igual, CSRF,
JSON ≤ 4096 bytes sem chaves duplicadas ou não finitos, campos exatos.
Aprovar ordem **não** autoriza chamar o Gemini; nenhum desses endpoints chama
o modelo ou escreve no ledger original.
