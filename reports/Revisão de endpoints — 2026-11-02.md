# Revisão de endpoints — dashboard HTTP

Revisão datada de **02/11/2026**, feita por leitura do código (não da
documentação), sob pedido de Matheus para auditoria endpoint a endpoint.
Ambiente local recriado nesta data; servidor keyless subido em
<http://127.0.0.1:8116/> (Python 3.13.14, `.venv` Poetry, `.env` criado a
partir de `.env.example` com defaults seguros).

Convenções: leitura = projeção sem escrita financeira; ⚠ = escrita real.
Uma linha por endpoint; veredictos e detalhe por módulo nas seções.

## Inventário fiel (resumo)

| # | Rota | Método | Natureza | Guarda própria | Persistência |
|---|---|---|---|---|---|
| 1 | `/`, `/operations`, `/comparison`, `/dividends`, `/wallets/new`, `/laboratory` | GET/HEAD | página | `_local_request` | — |
| 2 | `/legacy`, `/legacy/paper`, `/legacy/h2`, `/legacy/backtests` (aliases `/paper`, `/h2`, `/index.html`) | GET/HEAD | página consulta | `_local_request` | — |
| 3 | `/radar`, `/market`, `/portfolio`, `/logs` + estáticos | GET/HEAD | página consulta | `_local_request` + whitelist | — |
| 4 | `/api/logs` | GET | SSE do log | `_local_request` | leitura do arquivo |
| 5 | `/api/forward/{status,history,decision,supervision,portfolios,agents,market}` | GET | leitura | POST do namespace recusado antes do CSRF | artefatos selados H2 |
| 6 | `/api/h2/{status,validation,run,analysis,trace,decision,artifact}` | GET | leitura | idem; `artifact` baixa selado | docs/evidence + runs |
| 7 | `/api/radar/{status,search,detail}` | GET | leitura | query estrita | radar root |
| 8 | ⚠ `/api/radar/universe` | POST | escrita | CSRF+gate | universo selado |
| 9 | `/api/radar/preflight` | POST | leitura | CSRF+gate | nenhuma (roda sob `no_network`) |
| 10 | ⚠ `/api/radar/prepare` | POST | escrita | CSRF+gate+lock da raiz | dados preparados selados |
| 11 | ⚠ `/api/radar/run` | POST | escrita paga | CSRF+gate+orçamento+consentimentos | pareceres por ativo selados |
| 12 | `/api/portfolio/manual` | GET | leitura | query estrita | SQLite event-sourced |
| 13 | ⚠ `/api/portfolio/manual/{preview,confirm}` | POST | escrita | CSRF+preview token+`command_id` | eventos do ledger |
| 14 | `/api/portfolio/{monitoring,ledger,pilot,history,stock-history,stock-history/intraday}` | GET | leitura | query estrita; ledger/pilot exigem `demo=1` | ledgers/fixture selados |
| 15 | ⚠ `/api/portfolio/stock-history/refresh` | POST | escrita | CSRF, JSON ≤4096 | snapshot Yahoo selado + CSV raw |
| 16 | ⚠ `/api/portfolio/stock-history/intraday/refresh` | POST | escrita | idem | tiers intradiários selados |
| 17 | `/api/global-pm/*` (5) | GET | leitura | verificação `result_sha256` | demo selado |
| 18 | `/api/platform/*` (leitura, ~15) | GET | leitura | query estrita | projeções |
| 19 | ⚠ `/api/platform/market-base/update` | POST | escrita | CSRF+body vazio | B3/Yahoo/CDI/proventos/ordens |
| 20 | ⚠ `/api/platform/radar-analysis` | POST | escrita | CSRF+lock+`command_id` | contexto selado |
| 21 | ⚠ `/api/platform/radar-budget-authorization` | POST | escrita | CSRF+lock+token 64h | autorização orçamento selada |
| 22 | ⚠ `/api/platform/{global-prepare,global-run,global-replay}` | POST | escrita (run pago) | CSRF+token+`authorize_paid` | contexto/propostas selados |
| 23 | ⚠ `/api/platform/wallet-manager/{prepare,preflight,run,replay,preview,apply}` | POST | escrita (run pago) | CSRF+campos exatos+consentimento | contexto/ordens selados |
| 24 | `/api/platform/wallet-manager/{,latest}` | GET | leitura | query estrita | projeção |
| 25 | `/api/lab/backtest` | GET | leitura | validação de números | nenhuma (in-memory) |

Sem endpoint HTTP (internos): `daily_cycle` (DP-34), `dividends_api`,
`reference_rates_api`, `auction_orders`, `network_scope`.

## Camadas de defesa no roteador (`dashboard/server.py`)

1. `_local_request` (server.py:249): Host exato; POST exige Origin == Host;
   `Sec-Fetch-Site` — `cross-site`/`same-site` só por navegação GET de página.
2. POST de `/api/forward/*` e `/api/h2/*` → `legacy_read_only` 403 **antes do
   CSRF** (server.py:433): o legado é recusado mesmo com um CSRF válido.
3. CSRF único por processo (`JOBS.csrf`, `hmac.compare_digest`) — server.py:436.
4. `strict_json` (chave duplicada/NaN recusados), corpo ≤ 65536 no roteador e
   ≤ 4096 nos handlers, sem query string em POST, campos exatos (`fields`).
5. `network_scope` instalado em `setup()`; chamada paga exige `qualified()`.

---

# Achados de ambiente (pré-requisitos da revisão)

## A — Claim de Python do README é falso

`README.md` diz "Python **3.11 a 3.13**". `pyproject.toml` aceita `>=3.11,<3.14`.
Porém `src/agents/llm_trace.py:244` usa `MappingProxyType({})` como default de
dataclass (`transport_options`): o check de default mutável do **Python 3.11
trata unhashable como mutável** e a importação falha
(`ValueError: mutable default <class 'mappingproxy'>`). Testado em 3.11.9 e
3.11.15 (ambos falham); em 3.14 funciona; 3.13.14 funciona (usado neste
ambiente). **Consequência:** o suporte real começa em 3.12/3.13 — docs do TCC e
README devem registrar o piso real. Nenhuma adaptação de código proposta
(`llm_trace.py` é fonte do manifesto de identidade H2; mexer nele é invalidar
selos).

## B — Manifesto candidate com 21/73 hashes divergentes

`docs/evidence/h2_v6_evaluation/system_freeze_candidate.json` (estado
"CANDIDATE / NOT APPROVED / NOT FROZEN") tem SHA-256 de 73 fontes; **21
divergem** da árvore atual (`frozen_sources()` em
`scripts/multiasset_radar.py:135`). Não há commits tocando esses arquivos depois
do congelamento — ou seja, o candidato foi calculado sobre um estado de trabalho
que não virou commit. Sintoma observável: 41 erros de fixture em
`tests/test_wallet_manager.py` (falha em `frozen_sources`, não no módulo em
si); `tests/test_manual_portfolio.py` passa (23/23 subtestes).
**Estado pré-existente do projeto** (as docs da V7.6.5 registram falhas
preexistentes na suíte); tratado aqui como achado para a discussão de
auditabilidade do TCC, não como defeito desta revisão. Nada foi alterado.

---

# Módulo 1 — `wallet-manager` (APP-05, DP-24/DP-33/DP-34)

Arquivo: `dashboard/wallet_manager_api.py` (823 linhas). Identidade
`HFL-WALLET-MANAGER-V1`. Risco financeiro maior da plataforma: único caminho
que transforma parecer de agentes em ordem de leilão da carteira Multiagentes.

## Veredito por endpoint

| Comando | Natureza | Veredito |
|---|---|---|
| GET `/api/platform/wallet-manager?run=` | leitura | OK — histórico + contexto; devolve `csrf_token` |
| GET `.../latest?wallet=` | leitura | OK — varredura linear documentada (`ponytail:` comentário no próprio código) |
| ⚠ `prepare` | escrita selada | OK — idempotente; conflito de custo recusado; contexto expira em 24h |
| `preflight` | leitura (+cache) | OK — orçamento diário global, validade recalculadas toda vez |
| ⚠ `run` | escrita paga | OK — autorização selada **antes** do transporte (claim boundary); janela de crash vira estado de recuperação apenas lido (ver C2) |
| ⚠ `replay` | escrita (sem custo) | OK — exige `calls.sqlite` existente e roda sem rede |
| ⚠ `preview` | leitura* | OK — grava `quotes-preview.json` substituível (o mais novo vence por desenho, comentário DP-33) |
| ⚠ `apply` | escrita financeira | OK — consentimento explícito, bands DP-33 e ack de tese velha antes de registrar ordem |

## Linha a linha — observações

1. **Contratos selados no contexto (`contracts()`, linha 125):** prompt, schema,
   config, o próprio arquivo e `manual_portfolio_api.py` entram em
   `b.sha_file(__file__)`. Qualquer mudança de código invalida o contexto
   (recusa com `manager_contract_changed`) — reproducibilidade forte, mas
   **invalida contextos em aberto a cada deploy** (ver C1: janela de deploy
   invalida contexto em aberto).
2. **Orçamento diário global (`used_budget`, linha 240):** soma
   `usd_reserved` de *todas as autorizações de hoje* em *todos os runs* — é a
   leitura da DP-34 (teto US$ 4/dia para a rotina). O teto do gestor isolado
   é `CONFIG["root_budget_usd"]="4.00"`, substituindo o `5.00` selado do
   Global PM (`scripts/multiasset_global_pm.py:45`) — consistente com a
   decisão de não consumir o teto selado do legacy.
3. **`price_valid_until` = 2027-12-31** (`multiasset_global_pm.py:52`) —
   contrato de preços válido; o check em `preflight` (linha 274) está vivo,
   não é vestígio.
4. **`compile_proposal` (linha 292)** é a contabilidade: ordena
   SELL→HOLD→BUY para o caixa líquido fazer sentido; recusa cesta incompleta
   ou duplicada no universo (`manager_complete_unique_universe_required`),
   HOLD com quantity ≠ "0" (`manager_hold_quantity_must_be_zero`),
   opinião contrária ao sinal (`manager_operation_incompatible_with_opinion`,
   cobrindo VETADO e recomendação incompatível),
   venda acima da posição (`manager_insufficient_units`) e caixa negativo
   (`manager_insufficient_cash`).
5. **`status()` recomputa e confere o cálculo** (linhas 481–503): um
   `result.json` selado cuja contabilidade não reproduz contra as referências
   do `context.json` atual é recusado com `manager_result_changed` — bom
   design (a conta nunca é conferida só no momento da venda).
6. **Estado antes e depois (linha 532–559):** cadeia
   PREPARED→CLAIMED→RUNNING→…→PENDING_AUCTION→EXPIRED/APPLIED e o legado
   "booked at the reference price on approval" citado como regra antiga no
   comentário — migração de estado bem faseada, DP-33 custoso e recusável.
7. **`application(...)`** (linha 629) — prévia e confirmação: a confirmação
   revalida a prévia por digest duplo (token do epch + sha da cotação
   prévia), confere bandas (`manager_quote_moved`) e exige
   `acknowledge_stale` explícito que não pode ser default (linha 710–716).
   A prévia nunca grava no ledger — `manual.batch(…)„ sem `confirm`.
8. **Janela de crash, run→thread:** `run` grava `authorization.json`
   (imutável) e lança daemon; `claim.json` só é escrito dentro de
   `generate()` (linha 391–398). Se o servidor morrer entre a autorização e
   a thread, o estado fica `CLAIMED_RECOVERY_ONLY` e o replay recusa
   (`manager_no_envelope_to_replay`), pois `calls.sqlite` ainda não existe.
   O caminho de saída é abrir nova análise/proposal (sem duplicação
   financeira: `used_budget` conta a reserva). Ver C2.

## Fragilidades e fragilidade/sofisticação — o que vigiar

| ID | Observação | Severidade | Sugestão (só da revisão) |
|---|---|---|---|
| C1 | Contratos selados amarram o código vivo: todo deploy invalida contextos/preparados em aberto (`manager_contract_changed`) | média (operacional) | Esperado pelo desenho; documentar o ciclo "contexto tem validade de 24h e não atravessa mudança de código" sem alterar selos |
| C2 | Crash entre a gravação de `authorization.json` e `claim.json` (que só ocorre dentro de `generate()`) deixa estado sem saída por replay (`manager_no_envelope_to_replay`); recuperação exige nova análise/proposal | média | Mover a gravação de `claim.json` para dentro do lock de `run`, antes de subir a thread, sem tocar no CallBank |
| C3 | `run` e `replay` devolvem o mesmo corpo `{status: CLAIMED_RECOVERY_ONLY}` — o cliente não diferencia autorização recém-emitida de re-execução | baixa | Incluir `replayed: bool` na resposta |
| C4 | `journal.splitlines()[0]` assume exatamente uma chamada lógica; se o gestor um dia fizer múltiplas chamadas, o consumo de tokens no `result.json` viraria truncado | baixa (hoje) | Registrar a limitação em comentário (não há `ponytail:` no ponto) |
| C5 | `quotes-preview.json` é substituível sem selo por novo preview | baixa | Por desenho (o mais novo vence); o digest entra no token de confirmação, então a prévia aprovada é detectável |
| C6 | Os orçamentos de Radar (agregado por run) e do gestor (diário DP-34) são somas independentes, cada uma sob lock próprio; a coordenação entre os dois tetos existe apenas dentro do `daily_cycle` (`within_cap`) | média | Vale o diagrama "mapa de custos" na revisão: radar agregado × gestor diário × rotina DP-34 |

## Conclusão do módulo

Sem defeito de integridade encontrado na leitura: consentimentos são exigidos
antes de qualquer escrita, o replay nunca abre custo novo (roda sem rede), a
contabilidade é revalidada a cada `status()` e cada decisão de gasto existe
como registro selado antes do transporte. É o módulo mais bem blindado da
plataforma — coerente com ser o único a registrar ordens. Recomendo algumas
linhas do capítulo de método do TCC sobre o padrão geral
"autorização selada antes do transporte + revalidação na leitura" como
mecanismo transversal do produto.

---

# Módulo 2 — Radar (universe/prepare/run, orçamento agregado, gates)

Arquivos: `dashboard/radar_api.py` (174), `scripts/radar_runs.py` (1078),
`scripts/multiasset_radar.py` (867), gate do servidor em
`dashboard/platform_api.py:571`. Identidade `HFL-MULTIASSET-RADAR-V1`
(IDENTITY em `multiasset_radar.py`). Papel: análise consultiva por ativo
(comitê de 5 analistas + risco) que alimenta o gestor; nunca executa ordem.

## Veredito por endpoint

| Endpoint | Natureza | Veredito |
|---|---|---|
| GET `status` / `search` / `detail` | leitura | OK — search limitado a 100, catálogo do último COTAHIST anual com cache por mtime |
| ⚠ POST `universe` | escrita | OK — arquivo operacional substituível (`universe.json`, não selado por desenho), sob lock de estado |
| POST `preflight` | leitura | OK — **leitura pura**: todo o corpo roda sob `no_network`; nada é gravado (correção do inventário n° 9) |
| ⚠ POST `prepare` | escrita | OK — sessão fechada exigida (`session_not_closed`) + guard de sessão publicada no gate do servidor; por ativo, gravação independente (`bars.csv`/`input.json` imutáveis + eventos) |
| ⚠ POST `run` | escrita paga | OK — re-preflight dentro do lock e token casando com o novo relatório (anti-TOCTOU); reserva selada antes de qualquer claim; CallBank por ativo, journal imutável, replay sem rede |
| ⚠ POST `/api/platform/radar-budget-authorization` | escrita | OK — grava autorização selada e "never starts calls"; exige `confirm` + `budget_token` 64-hex + exposição ≤ limite |

## Orçamentos e gates (lógica verificada)

- `GLOBAL_BUDGET_USD = 5.0` por preflight do radar (`multiasset_radar.py:46`)
  e `AGGREGATE_CAP_USD = 5.0` somando a reserva de todos os runs
  consultivos (`radar_runs.py:53`) — política documentada em
  `budget()` como `NO_APPROVED_AGGREGATE_CAP_ORIGINAL_LOCAL_LIMIT_APPLIES`.
- `runs.gate()` (radar_runs.py:851): recusa run sem `accepts_new_calls`,
  seleção fora da identidade do run, run bloqueado/integridade, orçamento do
  run excedido e autorização agregada ausente/inválida — só depois disso o
  comando avança.
- `radar_post_gate` (platform_api.py:571): o navegador não escolhe raiz
  (`runner_not_a_registered_run`), header `X-HFL-Radar-Run` deve casar com o
  run do dono (`radar_run_header_mismatch_reload_page`), mix
  live/synthetic recusado (`synthetic_official_mix`) e sessão não publicada
  pela B3 recusada *antes* de baixar o ZIP anual
  (`reference_session_not_yet_published_by_b3`, comentário explica o incômodo
  que a guarda evita). Chamada paga exige `network_scope.qualified()`.

## Linha a linha — observações

1. **Isolamento de gravação (`storage_root`, multiasset_radar.py:356):**
   recusa a raiz do repositório e os diretórios protegidos
   (`src`, `data/forward`, `data/runs`, `data/snapshots`, `data/raw`) —
   dados de ensaio nunca misturam com a base de mercado autoritária. Bom.
2. **`prepare` por ativo (linha 269):** cada ticker grava
   independentemente ("a sibling failure never deletes data" no comentário);
   `input.json`/`bars.csv` imutáveis com identidade e manifest; re-prepare
   sobre input existente exige mesmo manifest (`prepared_identity_differs`).
   `last_prepare.json` é relatório vivo, não selado — fronteira
   operacional/selado clara e consistente em todo o módulo.
3. **`RadarExtractor._cotahist` (linha 203):** anos fechados reutilizam
   `data/raw/cotahist/COTAHIST_A*.ZIP` locais; o ano corrente baixa da B3
   para o cache do radar (não para `data/raw`) — DP-27 respeitada, sem
   redistribuição.
4. **Anti-TOCTOU no `run` (linha 631):** preflight re-executado dentro do
   lock; token deve casar com o **novo** relatório; reserva selada
   (`reservations/<token>.json` imutável) antes do primeiro claim; `gate()`
   do cliente reconfere o input congelado antes de cada transporte
   (`input_changed_before_transport`). O mesmo padrão do wallet-manager,
   aqui por ativo.
5. **`committee` (linha 568):** 5 analistas, consenso 0,6,
   `require_all_votes=True`; regra determinística de risco
   (volatilidade 21d anualizada > 50% → VETADO sem chamada ao LLM,
   `HARD_ASSET_VOLATILITY_RULE`); `portfolio_manager: NOT_INVOKED` —
   coerente com DP-22 (comitê por ativo não consome posições do gestor).
6. **Custo estimado (linha 729):** tarifas por ano codificadas
   (`2026: (0.75, 3.75)`, depois `(1.5, 7.5)`) e rotuladas
   `estimated billing, not invoice`; tokens reais selados no journal
   (`cost_basis` explícito). Aceitável como política didática; ver V-2.
7. **Falha por ativo (linha 770):** `failure.json` vivo + evento
   `FAILED_REPLAY_ONLY`, sem retry automático; recovery é replay offline
   com journal existente (`replay_claim_or_journal_missing` senão). Coerente
   com DP-13/DP-34 (sem autonomia de escrita financeira).
8. **Lock vencido:** `job()` marca `INTERRUPTED_REVIEW_LOCK_AND_REPLAY` e o
   POST recusa com `radar_busy_or_stale_lock`; não há detecção/deleção
   automática de lock vencido — intervenção manual revisando o lock e
   partindo para replay. Friction deliberado, documentado no estado; ver V-1.
9. **`bind` (radar_runs.py:953):** um único runner por processo (raiz selada
   de `radar_api.ROOT`); comentário `ponytail:` já nomeia o upgrade (raiz por
   parâmetro ao resealar). Honesto.
10. **`search` (radar_api.py:35):** catálogo em `lru_cache(2)` com stamp de
    mtime; símbolos validados por `[A-Z]{4}[3-8]`; sem rastro de download
    pago (é leitura local do ZIP).

## Fragilidades observadas (não violações)

| ID | Observação | Severidade | Sugestão (só da revisão) |
|---|---|---|---|
| V-1 | Lock vencido exige intervenção manual (revisar + remover + replay) | baixa (oper.) | Documentar o passo no runbook; automação aqui conflitaria com a política conservadora |
| V-2 | Tarifa de custo estimada codificada por ano no código; mudança de preço do provedor requere novo deploy/código | baixa | Já existe `cost_basis` explícito; para o TCC registrar que reserva ≥ custo observado (política conservadora) |
| V-3 | `universe.json` sem selo (operacional) — qualquer POST autenticado substitui o universo do run selecionado; a invariância do run vem do registry, não do universe.json | baixa | Pode confundir diagnóstico; sugerir nota na UI de que o universo vigente é o do run do registry |
| V-4 | `search` depende do último ZIP anual presente; sem ZIP, catálogo cai para os 5 exemplos (`technical_examples_only`) — comportamento correto mas silencioso para quem não lê `source` | baixa | Já exposto no campo `source`/`note`; ok |

## Conclusão do módulo

Caminho de escrita sólido: dois gates independentes (servidor + registry),
re-preflight anti-TOCTOU com token, reserva selada antes de claim, journal
imutável por ativo e replay sem rede. Não inverte sinal, não escala posição,
não contamina dados RAW. Menor achado operacional: fricção de lock vencido
(deliberada). Recomendo para o TCC usar o Radar como o exemplo didático de
"orçamento por reserva vs. custo observado" — a diferença entre
`usd_reserved` e `usd_observed_provider_tokens` já vem catalogada por run.

---

# Próximos módulos do plano de revisão (a completar em próximas sessões)

3. ⚠ `market-base/update` (megacomando DP-27 — atomicidade das seis etapas)
4. ⚠ `manual_portfolio_api` preview/confirm (referência de idempotência)
5. ⚠ `global-prepare/run/replay` (Global PM)
6. ⚠ refreshers Yahoo (universe ≤20, locks, snapshots)
7. leituras H2/forward (`legacy_read_only`, allow-lists) e `/api/logs` SSE
8. ciclo diário DP-34 (internos: slots, teto, e-mail, sealing)
