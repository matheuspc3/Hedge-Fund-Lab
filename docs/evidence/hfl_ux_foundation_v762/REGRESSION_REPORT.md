# Regressão e preservação

Consolida os entregáveis `REGRESSION_REPORT` e `PRESERVATION_REPORT`.

## 1. Suíte completa

Comando: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`, árvore
limpa no commit `2e1676b`, 13/10/2026. Saída bruta: [regression.txt](regression.txt).

| | V7.6.1 | V7.6.2 (bruto) | V7.6.2 (efetivo) |
|---|---|---|---|
| Aprovados | 1741 | 1749 | **1750** |
| Falhas | 15 | 16 | **15** |
| Duração | 15 min 34 s | 14 min 39 s | — |

Os 9 testes a mais são os de `tests/test_ui_v762.py`.

**A 16ª falha foi causada por mim durante a execução, não pelo código.**
`tests/experiments/test_h2_v6_provisional.py::test_oa1_validation_seal_and_dashboard`
falhou com `ValueError: evaluation requires a clean repository` porque, enquanto a
suíte rodava, editei `docs/ROADMAP.md` por alguns segundos (a edição foi desfeita
assim que percebi e reaplicada só depois da suíte). Reexecutado isoladamente com a
árvore limpa: **1 passed** (7 min 12 s). É o par sensível ao Git já descrito na V7.6.1: com a árvore limpa, só o `test_snapshot[code]` falha. A saída bruta foi mantida sem edição.

As 15 falhas restantes são **exatamente as mesmas** da V7.6.1 (comparação por
nome de teste) e independem do frontend:

| Grupo | Testes | Causa conhecida |
|---|---|---|
| PostgreSQL | 7 em `tests/pipeline/test_flows.py` | banco local na porta 5435 desligado |
| Preservação legada | `test_global_pm::test_31_original_ledgers_preserved`, `test_multiasset_portfolio::…preservation` | listas de preservação anteriores a recovery-01 |
| V7.3 desatualizados | 2 em `tests/test_radar_runs.py` | expectativas anteriores à recuperação |
| H2 | `test_cal_b4_safety`, `test_spec`, `test_v6_phase_routing` | mensagens e registro de agentes divergentes, já triados na V7.6 |
| Sensível ao estado do Git | `tests/pipeline/test_snapshot.py::test_manifest_adulterado_e_rejeitado[code]` | par complementar de `test_h2_v6_provisional` (um exige árvore suja, o outro limpa); triado na V7.6.1 |

## 2. Testes antigos atualizados (e por quê)

Nenhum teste foi alterado para esconder falha. Dois mudaram porque o pedido da
V7.6.2 alterou o comportamento que eles descreviam:

| Teste | Antes | Agora | Motivo |
|---|---|---|---|
| `tests/test_platform_v7.py` | exigia o texto do grupo antigo "Pesquisa e Auditoria" | exige o rótulo da navegação principal e as áreas "Pesquisa" e "Auditoria" | navegação reorganizada por objetivo (pedido) |
| `tests/test_platform_ui.py` | exigia que preflight, solicitar e autorizar do V1 enviassem as requisições pagas | exige que **não** enviem nada; corrida de seleção e recuperação (`global-replay`) mantidas | V1 encerrado na interface (pedido). Além disso, o script Node ganhou guarda de saída: antes, uma promessa que nunca resolvia fazia o teste passar em silêncio; a mutação `V1_CLOSED=false` agora derruba o teste |

`scripts/review_v761.py` passou a ler `AREAS` (ou `SHELL_LINKS`, se existir) para
continuar inventariando a navegação.

## 3. Testes novos

`tests/test_ui_v762.py` (9): rotas com um só menu e sem versões no título; deep
links; estáticos novos servidos e arquivos privados recusados; área padrão por
página; glossário único e completo; contraste dos tokens; gatilhos V1 fechados e
conjunto fechado de botões pagos; identificadores científicos intactos;
verificações de navegador (113, `ui_checks.json`).

## 4. Preservação

| Verificação | Resultado |
|---|---|
| `check_preservation.py --since preservation_before.json` ([preservation_since.json](preservation_since.json)) | `changes: []`, `violations: []` |
| Pacote V7.5 (`verify_consolidation_v75.py`) | `ok: true` |
| Protocolo V7.6 (`experiment_protocol_v76.py validate`) | `errors: []` |
| Registro V1 `v7-5a78ea5d15214e37bcae18f167ffcee3` | `REJECTED_BY_VALIDATOR` (inalterado) |
| Registro V2 `v74-76d07c0d32444cecaf07e875deacb519` | `VALID_PROPOSAL` (inalterado) |
| Radar `radar-2026-10-09-recovery-01` | inalterado |
| Arquivos alterados desde `9a45564` | só `dashboard/` (apresentação e roteamento de páginas), `scripts/` de UI, `tests/` e esta pasta. Nenhum arquivo em `src/`, `data/`, configurações, claims ou journals; `radar_api.py`, `portfolio_api.py`, `global_pm_api.py` e `platform_api.py` intocados; em `server.py` nenhum handler de API mudou |

Não executado nesta entrega: H2 Final Test, inferências Gemini, paper trading,
campanhas V7.6, push.
