# Qualificação offline e interação

Comandos reproduzíveis (Python/Chrome instalados, permissão de TEMP externo):

```powershell
.venv/Scripts/python.exe -B -m pytest tests/test_paper_ledger_v765.py tests/test_ui_v765.py tests/test_ui_v764.py tests/test_portfolio_monitoring.py -q --basetemp "$env:TEMP/hfl-pytest-v765-check"
.venv/Scripts/python.exe -B scripts/qualify_paper_ledger.py
```

`qualify_paper_ledger.py` sempre cria banco externo temporário e bloqueia rede; sem `--export` não escreve evidência. O teste usa unittest stdlib no framework pytest já instalado, sem dependências novas. A exportação final contém 27 eventos, cinco sessões, duas compras, uma venda e três confirmações D+2. Outro processo abre o SQLite e verifica; a API é comparada antes/depois do reinício HTTP.

| Requisitos do pedido | Verificação executável |
|---|---|
| 1–3 criação, persistência, saldo | identity_initial_cash_restart_and_second_process, storage_boundaries |
| 4–5 compra/venda | whole_lifecycle_accounting_and_history |
| 6–9 caixa/custódia/quantidade/preço inválidos | invalid_cash_custody_quantity_price_and_concentration |
| 10–12 custos/reservas/recebíveis | buy_reservation_cancel, buy_cost, sale_receivable_cannot_fund_purchase |
| 13–15 D+2/feriado/cobertura desconhecida | d_plus_two_weekend_holiday_and_unknown_calendar, early_unknown_and_duplicate_settlement |
| 16–19 marca oficial de fixture/sintética/fonte/ausência | official_format_fixture_valuation, invalid_price_provenance, missing_marks_unavailable |
| 20–24 realizado/não realizado/patrimônio/exposição/drawdown | whole_lifecycle (valores exatos e sinais), curva completa exportada |
| 25–26 reconciliação/divergência | reconciliation_divergence, corrupted_checkpoint |
| 27–28 duplicidade/replay | idempotency_conflict, duplicate_execution, duplicate_import, replay_and_deleted_tail |
| 29 interrupção | atomic_transaction_interruptions_and_actual_process_death; crash durante reconciliação |
| 30–32 corrupção/hash/tempo | corrupted_database, hash_chain_mutation, resealed_invalid_events |
| 33–34 chave conflitante/concorrência | concurrent_retry, concurrent_conflicting_payload |
| 35 veto | veto_blocks_buy_and_sale; não habilita política B |
| 36–37 rejeitada/sem operações | official_references_remain_advisory, no_operation_proposal |
| 38–39 H2/multiativos/sintético/oficial | storage/classifications, explicit_demo_opt_in, Chrome identity e deep_link |
| 40–42 GET/paginação/sessões | ReadChecks + HTTP read-only/restart, query filters |
| 43–46 UI vazia/com posições/operações/sessões | scripts/ui_check_v765.mjs, capturas reais |
| 47 reinício servidor | test_ledger_http_get_no_write_routes_and_server_restart |
| 48–50 sem Gemini/reais/preservação | no_network, processo sem chave, interceptação local GET, snapshots/hash e testes de preservação existentes |

Cinco mutantes de guardas são compilados em memória. Cada check é executado primeiro no módulo original e depois no mutante, exigindo que a ausência de guarda produza AssertionError. Nenhum arquivo do motor/calendário científico é modificado. Remoções: RAW, checkpoint, escopo de autorização, vínculo de autorização no fill, cobertura do calendário.

Primeira rodada de 28 testes: três falhas de harness (expectativa do código de expiração do V5 e conexões SQLite de teste não fechadas no Windows). Corrigidas sem mudar o motor V5; rodada seguinte 28 passed/58 subtests. Rodada ampliada: 32 passed/68 subtests (`offline_qualified.txt`). A rodada direcionada final, incluindo concorrência conflitante e IDs entre ordens: **49 passed, 68 subtests passed** (`targeted_final.txt`), dos quais 34 novos de ledger e dois HTTP/Chrome; os demais são regressão de integração existente. Não se omitem as rodadas anteriores. Regressão completa: 1801 passed, mesmas 14 falhas conhecidas e 129 subtests.

Chrome: cliente CDP/headless já existente, processo keyless, interceptação permite somente GET local. Checks cobrem caixa puro, ausência de curva para ponto único, opt-in por teclado, identidade/origem, resumo, posições, cinco sessões, três operações, D+2, paginação, seleção histórica/reload, recebíveis, ajuda/Escape/foco, V1/V2, migração de deep link H2, quatro tamanhos de tela, reflow equivalente a 200%, erro de leitura/retry e catálogo vazio. Report `ui_final.json`: 30 checks, zero bloqueios/tentativas externas/escritas, zero exceções.

Na primeira execução Chrome houve duas falhas nos roteiros: clique em ajuda de aba oculta e link local antigo da jornada H2. Corrigidas para abrir aba visível e consultar H2 em `/paper`; assertions financeiras/identidade permanecem. `browser_tests.txt`: quatro testes HTTP/Chrome V7.6.4/V7.6.5 aprovados. Não se declara acessibilidade integral: leitor de tela, zoom nativo do navegador e auditoria WCAG completa continuam pendentes. Reflow 720×450 equivale à área CSS de 1440×900 a 200%, mas não é teste de zoom nativo.
