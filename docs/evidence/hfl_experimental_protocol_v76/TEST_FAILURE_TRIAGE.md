# Triagem das 15 falhas da suíte

Reprodução em 12/10/2026, sem alterar testes, baselines, dados científicos nem
serviços. Regressão completa da V7.6: seção "Regressão" do [README.md](README.md).

## 1. Matriz

| # | Teste | Arquivo | Dependência | Reproduzida | Causa | Comprovação | Impacto V7.6 | Impacto científico | Resolução segura | Aprovação metodológica? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `test_31_original_ledgers_preserved` | `tests/test_global_pm.py` | hashes exatos do baseline V6 | sim | `data/radar/hfl_multiasset_v1/job.json` e `last_prepare.json` mudaram por ações do operador em 12/10 (antes da V7.3) | **comprovada:** `check_preservation.py` classifica as duas mudanças como OPERATIONAL, `violations: []` | nenhum | nenhum: arquivos operacionais, não evidência | proposta V7.3: exigir hash exato só do que `classify` marca como VIOLATION | **sim** (muda critério de teste histórico) |
| 2 | `test_original_scientific_radar_and_ledger_preservation` | `tests/test_multiasset_portfolio.py` | baseline V5 | sim | idem (hash `7304…` ≠ `5167…` de `job.json`) | comprovada | nenhum | nenhum | idem | **sim** |
| 3 | `test_real_recovery_has_five_official_inputs_equivalent_to_original` | `tests/test_radar_runs.py` | estado local de `radar-2026-10-09-recovery-01` | sim | afirma `claims == 0`; o lote pago rodou em 12/10 14:58 (5 claims) | **comprovada:** `assert (5 == 5 and not [] and 5 == 0)` | nenhum | nenhum: o teste descreve o estado antes do lote | substituir por teste versionado que confira o estado pré-lote pela evidência V7.3 (`prepare_recovery.json`) e o pós-lote pelos claims | **sim** (teste de outra entrega) |
| 4 | `test_real_itub4_bonus_normalized_and_bbas3_restricted` | `tests/test_radar_runs.py` | plano de orçamento atual | sim | afirma plano 30/29 chamadas; com o lote já executado o plano restante é 0/0 | **comprovada:** `assert (0, 0) == (30, 29)` | nenhum | nenhum | idem | **sim** |
| 5–11 | `TestPipelineFlow::test_full_flow_success`, `test_partial_flow_returns_explicit_failure_summary`, `test_extract_retry_on_failure`, `test_custom_tickers`, `test_single_ticker`, `test_empty_tickers`, `test_default_tickers_from_settings` | `tests/pipeline/test_flows.py` | `DATABASE_URL` do `.env` (PostgreSQL `127.0.0.1:5435`, Docker parado) | sim | `pipeline_etl()` chama `init_db()` no banco configurado, mesmo com extract/transform/load simulados | **comprovada:** com `DATABASE_URL=sqlite:///<arquivo temporário>`, os 10 testes do arquivo passam (seção 2) | nenhum | nenhum | procedimento da seção 2; opcionalmente, um `conftest` que fixe SQLite temporário para esses testes | sim, se o `conftest` antigo for alterado; não para o procedimento |
| 12 | `test_v5_development_s3_failure_blocks_further_phases` | `tests/experiments/test_cal_b4_safety.py` | gates do H2 v5 | sim | a função levanta outra mensagem: esperado `development S3 failure`, obtido `CAL-B4 must stay sealed during v5 development` | **hipótese:** a ordem dos gates do H2 v5 mudou depois do teste; não investigado a fundo para não tocar no H2 | nenhum | nenhum sobre Radar/Global PM; possível desatualização de teste H2 | revisão do H2 por quem mantém o protocolo H2 | **sim** (H2) |
| 13 | `test_registry_cobre_os_cinco_classicos_e_o_participante_llm` | `tests/experiments/test_spec.py` | registro de participantes | sim | o registro tem duas estratégias extras: `sma_regime_h2_proposed`, `bollinger_state_h2_proposed` | **comprovada:** diff do conjunto | nenhum | nenhum (estratégias propostas, não usadas aqui) | decisão H2 sobre o registro ou atualização do teste | **sim** (H2) |
| 14 | `test_structural_failure_prevents_phase_selection_and_progression` | `tests/experiments/test_v6_phase_routing.py` | estado das evidências H2 v6 | sim | `committed_phase("defect")` não levanta exceção | **hipótese:** já existe um PASS de defeito commitado nas evidências H2 v6, e o teste supõe o contrário | nenhum | nenhum fora do H2 | revisão H2 | **sim** (H2) |
| 15 | `test_manifest_adulterado_e_rejeitado[code]` × `test_h2_v6_provisional::test_oa1_validation_seal_and_dashboard` | `tests/pipeline/test_snapshot.py`, `tests/test_h2_v6_provisional.py` | estado limpo/sujo do Git | sim | par complementar: um exige árvore limpa, o outro só detecta a mutação com árvore suja; um dos dois sempre falha | **comprovada:** nesta sessão, com a árvore suja (snapshot V7.6 não commitado), `test_snapshot[code]` passou, como previsto | nenhum | nenhum | marcar a dependência explicitamente (pular com motivo quando o estado do Git não for o exigido) | **sim** (muda teste antigo; um deles é H2) |

Contagem por categoria: preservação operacional 2, V7.3 desatualizados 2,
PostgreSQL 7, H2 3, Git 1. Total: **15**.

## 2. Procedimento reprodutível para os testes de pipeline (sem PostgreSQL)

Não inicia serviço, não lê nem grava o banco persistente (`pgdata`), não altera
o `.env`:

```bash
# Git Bash
T="$(cygpath -m "$TEMP")/flows_$$.db"
DATABASE_URL="sqlite:///$T" .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/pipeline/test_flows.py
rm -f "$T"
```

```powershell
# PowerShell
$env:DATABASE_URL = "sqlite:///$($env:TEMP -replace '\\','/')/flows.db"
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/pipeline/test_flows.py
Remove-Item Env:DATABASE_URL; Remove-Item "$env:TEMP/flows.db"
```

Resultado em 12/10/2026: **10 passed**. A variável de ambiente tem precedência
sobre o `.env` (`pydantic-settings`).

**Integração real com PostgreSQL (não executada):** o `docker-compose.yml`
monta o volume persistente `pgdata` em `5435`. Para testar contra PostgreSQL
sem tocar nesses dados, usar um contêiner descartável com outro nome, outra
porta e sem volume, por exemplo `docker run --rm -d --name hfl-test-db -e
POSTGRES_PASSWORD=test -p 55432:5432 postgres:16`, e
`DATABASE_URL=postgresql://postgres:test@127.0.0.1:55432/postgres`. Isso inicia
um serviço; exige autorização do operador e não foi feito.

## 3. O que não foi feito, e por quê

- Nenhum teste antigo foi editado, nenhum baseline alterado, nenhum dado
  científico tocado: a suíte continua com 15 falhas, por decisão.
- Nenhum serviço foi iniciado; o Docker está parado nesta máquina.
- As três falhas do H2 não foram investigadas além da mensagem: aprofundar
  exigiria executar caminhos do H2 que o escopo da V7.6 manda não tocar.
