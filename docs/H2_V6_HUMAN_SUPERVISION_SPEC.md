# H2 v6 supervisionada — especificação técnica (não implementada)

**Estado:** proposta para uma fase futura. Nada aqui altera o runner
`scripts/run_h2_v6_forward.py`, a decisão de 09/10/2026, os ledgers existentes
ou a identidade H2 v6. Nenhum endpoint ou botão de aprovação foi criado.

## 1. Objetivo e princípio de separação

Permitir que uma pessoa aprove ou rejeite a recomendação dos agentes e defina
limites antes de uma operação virtual, **sem contaminar a H2 v6 original**.

A H2 v6 original continua executando mecanicamente toda decisão `DECIDED`.
A supervisão vive em uma estratégia separada, `h2_v6_supervised`, com ledger
próprio em `data/forward/h2_v6_supervised/`, que:

- lê a decisão original de S (`sessions/<S>/decision.json`) por hash, sem
  reescrevê-la e sem nova chamada ao modelo;
- aplica o filtro humano registrado para S;
- liquida com o mesmo motor (`ExecutionEngine._settle`), custos, capital,
  calendário e preços observados da carteira IA.

| | H2 v6 original | H2 v6 supervisionada |
|---|---|---|
| Decisão | agentes | a mesma decisão dos agentes (mesmo `decision_sha256`) |
| Execução | toda intenção vira ordem na abertura T | só intenções aprovadas e dentro dos limites |
| Ledger | `h2_v6_paper/state.json` | `h2_v6_supervised/state.json` |
| Natureza | tratamento congelado | tratamento + julgamento humano não cego |
| Comparação | referência | pareada contra a original, mesmo início |

Leitura metodológica: a diferença entre as duas curvas mede o efeito do filtro
humano *daquela pessoa, naquele período*. O julgamento não é cego (a pessoa vê
o raciocínio dos agentes e o mercado) nem replicável; é avaliação exploratória,
fora da ciência H2 v6. Iniciar a estratégia supervisionada exige o mesmo gate
dos benchmarks: inicialização só antes de uma abertura futura, sem backfill.

## 2. Registro de aprovação

Um arquivo write-once por sessão, `approvals/<S>.json`, gravado e sincronizado
antes de qualquer efeito:

```json
{
  "kind": "H2_V6_SUPERVISED_APPROVAL", "schema_version": 1,
  "strategy": "h2_v6_supervised",
  "decision_session": "2026-10-13", "target_session": "2026-10-14",
  "decision_sha256": "…", "input_sha256": "…",
  "action": "APPROVE | REJECT",
  "limits": {
    "max_buy_price": 57.30,
    "max_open_gap": 0.03,
    "max_concentration": 0.80,
    "max_recent_volatility": 0.45
  },
  "created_at": "2026-10-13T19:02:11-03:00",
  "expires_at": "2026-10-14T10:00:00-03:00",
  "operator": "local", "note": "texto livre opcional",
  "idempotency_key": "sha256(strategy|S|decision_sha256)",
  "previous_audit_sha256": "…"
}
```

- `decision_sha256` amarra a aprovação ao conteúdo exato da decisão; qualquer
  divergência invalida o registro.
- Limites são opcionais; ausência significa "sem limite adicional".
- `operator` é declarativo: o servidor é local e não autentica pessoas. Se houver
  vários operadores, isso exige autenticação própria antes da implementação.

### Validade

- Criável somente depois de `decision.generated_at` e antes de
  `target_open_deadline` (10:00 BRT de T); o servidor usa o próprio relógio.
- `expires_at` = prazo de abertura de T. Não há aprovação "permanente" nem
  aprovação para sessões futuras ainda não decididas.
- Sem registro no prazo → `EXPIRADA`: nenhuma ordem, posição mantida. Isso é
  diferente de `REJEITADA` e é contado separadamente.
- Cancelamento: um segundo arquivo write-once `approvals/<S>.cancel.json`,
  também antes do prazo. Não há edição; a trilha preserva as duas intenções.

## 3. Limites e quando cada um pode ser verificado

| Limite | Momento | Fonte | Efeito |
|---|---|---|---|
| Concentração máxima | antes da abertura | decisão + carteira supervisionada | alvo = min(alvo, limite); estado `AJUSTADA_CONCENTRACAO` |
| Bloqueio por volatilidade | antes da abertura | `risk_metrics.recent_volatility` gravado em S | se acima do limite, `BLOQUEADA_VOLATILIDADE` |
| Gap máximo na abertura | reconciliação | abertura oficial de T vs. fechamento de S | se \|abertura/fechamento − 1\| > limite, `NAO_EXECUTADA_GAP` |
| Preço máximo de compra | reconciliação | abertura oficial de T | se abertura > limite, `NAO_EXECUTADA_LIMITE_PRECO` |

Venda usa o simétrico `min_sell_price`, se definido. A volatilidade é a já
calculada causalmente para S; nada novo é estimado.

### Sem falsa execução intradiária

O sistema tem apenas o COTAHIST diário oficial. Portanto, a ordem modelada é
**a participação no leilão de abertura com limite**: executa ao preço de
abertura de T se ele respeitar os limites; caso contrário, não executa naquele
dia. Não se infere preenchimento posterior pela mínima/máxima do dia, pois o
horário e o preço reais são desconhecidos. A interface nunca exibe "executada
às 10:00": até a reconciliação do fechamento de T, o estado é
`PENDENTE_ABERTURA`.

Um feed intradiário futuro seria fonte separada, com horário e procedência
gravados, usado apenas para alertas de interface. A liquidação do ledger
continuaria pela abertura oficial reconciliada, preservando comparabilidade
com a H2 v6 original.

## 4. Estados da ordem supervisionada

```text
PROPOSTA ──► AGUARDANDO_APROVACAO ──► APROVADA ──► PENDENTE_ABERTURA ──► EXECUTADA
                 │                       │  │              ├──► NAO_EXECUTADA_LIMITE_PRECO
                 │                       │  │              └──► NAO_EXECUTADA_GAP
                 │                       │  ├──► AJUSTADA_CONCENTRACAO ──► PENDENTE_ABERTURA
                 │                       │  └──► BLOQUEADA_VOLATILIDADE
                 │                       └──► CANCELADA
                 ├──► REJEITADA
                 └──► EXPIRADA
SEM_ORDEM_NECESSARIA (alvo = posição)   ·   SEM_DECISAO (MISSED/FAILED/LATE na original)
```

Estados terminais sem ordem mantêm a posição. Uma ordem não executada não é
reapresentada no dia seguinte: a próxima decisão dos agentes gera nova proposta.

## 5. Idempotência

- Chave `sha256(strategy | decision_session | decision_sha256)`; um único
  registro de aprovação e no máximo um cancelamento por chave.
- Gravação por `O_CREAT|O_EXCL` + `fsync`, como os claims `run-<S>.json`.
  Cliques duplicados, recargas e dois servidores resultam em `409`.
- A sincronização do ledger supervisionado é idempotente por sessão, como
  `run_h2_v6_forward_benchmarks.py`: repetir não cria ordens novas.
- Lock exclusivo próprio; nunca o lock do ledger original.

## 6. Trilha de auditoria

- `approvals/audit.jsonl` append-only; cada linha contém o hash da anterior
  (`previous_audit_sha256`), o hash do arquivo write-once e o evento
  (`CREATED`, `CANCELLED`, `EXPIRED`, `APPLIED`, `SETTLED`).
- O `state.json` supervisionado registra, por sessão, `decision_sha256`,
  hash da aprovação e resultado da reconciliação.
- Um verificador offline recompõe a cadeia e confirma que nenhuma aprovação
  foi criada após o prazo ou alterada.

## 7. Interface e endpoints futuros

- `GET /api/forward/supervision?session=S`: proposta, aprovação, estado.
- `POST /api/forward/supervision/approve` e `/reject`: mesmo contrato dos POST
  existentes (Host exato, Origin, CSRF, JSON ≤ 4096 bytes, sem campos extras,
  sem chaves duplicadas ou valores não finitos), mais `decision_sha256` e
  confirmação explícita por checkbox.
- Nenhum desses endpoints chama o Gemini, altera `decision.json` ou toca o
  ledger original.
- A Visão Geral mostraria a quinta carteira, rotulada "supervisionada".

## 8. Testes exigidos antes de ativar

Aprovação antes/depois do prazo; hash de decisão divergente; dupla aprovação;
cancelamento; expiração; cada limite (abertura acima/abaixo, gap positivo e
negativo, concentração parcial, volatilidade); sessão MISSED/FAILED/LATE;
idempotência da sincronização; isolamento completo do ledger original
(hashes protegidos inalterados); cadeia de auditoria adulterada detectada.
