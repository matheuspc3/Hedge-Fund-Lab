# Reprodutibilidade e auditoria

Todos os comandos abaixo são **somente leitura**: não chamam o Gemini, não
exigem chave, não criam inferências, claims, journals ou reservas e não gravam
em `data/`. A única exceção está marcada como GRAVA e escreve apenas nesta
pasta. Execute na raiz do repositório (PowerShell ou Git Bash).

## 1. Entradas necessárias

| Conjunto | Caminho | No Git? | Necessário para |
|---|---|---|---|
| Pacote V7.5 | `docs/evidence/hfl_scientific_consolidation_v75/` | sim | leitura; conferência dos `.md` |
| Evidências V7.3/V7.4/incidente | `docs/evidence/hfl_radar_v73/`, `hfl_global_pm_v2/`, `hfl_incident_2026_10_12/` | sim | diagnóstico, contratos, forense |
| Código dos tratamentos | `scripts/multiasset_global_pm.py`, `run_global_pm.py`, `multiasset_global_pm_v2.py`, `run_global_pm_v2.py` | sim | hashes selados nos contextos; verificadores |
| Radar recovery-01 | `data/radar/hfl_multiasset_v1_recovery_01/` e `data/radar/registry.json` | **não** | pareceres, journals, tokens |
| Global PM V1 | `data/global_pm/hfl_global_pm_v1/v7-5a78ea5d15214e37bcae18f167ffcee3/` + reserva `bdb948af….json` + `data/platform/v7/radar_origins/v7-5a78….json` | **não** | resultado V1 |
| Global PM V2 | `data/global_pm/hfl_global_pm_v2/v74-76d07c0d32444cecaf07e875deacb519/` + reserva `13ad05f3….json` | **não** | resultado V2 |

A lista completa, com SHA-256 e tamanho de cada arquivo, está em
[EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json) (`sources`). Um avaliador sem
os registros locais consegue ler e conferir a coerência das evidências
versionadas, mas não recalcular as métricas; nesse caso o verificador lista os
arquivos ausentes em `missing`.

**Não copiar para o Git nem para documentação pública:** `private/` (journals
privados e bancos SQLite das chamadas, com prompts e respostas brutas do
provedor), arquivos `.env`, chaves e qualquer `data/` operacional. O
manifesto registra só hashes e tamanhos desses arquivos.

## 2. Verificação da consolidação (só biblioteca padrão)

```powershell
python -B scripts/verify_consolidation_v75.py
```

Recalcula a partir das fontes primárias: hashes do manifesto; todas as métricas
de [METRICS.json](METRICS.json); os números transcritos em
[COMPARISON_V1_V2.md](COMPARISON_V1_V2.md) e
[COST_ACCOUNTING.md](COST_ACCOUNTING.md). Saída esperada:

```json
{"missing": [], "violations": [], "operational_changes": [], "metric_divergences": [], "doc_divergences": [], "ok": true}
```

Interpretação: `violations` = arquivo imutável com hash diferente;
`operational_changes` = arquivo OPERATIONAL (hoje só `data/radar/registry.json`)
mudou, o que não é violação; `metric_divergences` = métrica recalculada
diferente da publicada; `doc_divergences` = número publicado nos `.md` que
não confere. Código de saída 1 em qualquer divergência.

Regerar o pacote derivado (**GRAVA** apenas `METRICS.json` e
`EVIDENCE_MANIFEST.json` nesta pasta; usar somente se a fonte mudar de forma
autorizada):

```powershell
python -B scripts/verify_consolidation_v75.py build
```

## 3. Verificadores existentes (reutilizados, não duplicados)

Exigem o ambiente do projeto (`.venv`), sem chave Gemini:

```powershell
$P = '.venv/Scripts/python.exe'
# V1: confere os 6 arquivos do registro, revalida no instante gravado, refaz o contrafactual em memória
& $P -B scripts/run_global_pm_v2.py incident
# V2: confere selos, journal, SQLite (mode=ro), custo e revalida a resposta com o validador V2
& $P -B scripts/run_global_pm_v2.py status --id v74-76d07c0d32444cecaf07e875deacb519
# Radar: estado, claims, journals, reservas e comparação com o lote original
& $P -B scripts/radar_runs.py status --run radar-2026-10-09-recovery-01
# Preservação: baselines históricos e comparação com o snapshot da V7.5
& $P -B scripts/check_preservation.py
& $P -B scripts/check_preservation.py --since docs/evidence/hfl_scientific_consolidation_v75/preservation_before.json
# Testes
& $P -m pytest -q tests/test_consolidation_v75.py tests/test_global_pm_v2.py
```

Resultados esperados: `incident` idêntico a
[../hfl_global_pm_v2/incident_reproduction.json](../hfl_global_pm_v2/incident_reproduction.json);
`status` com `"status": "VALID_PROPOSAL"` e sem exceção de integridade;
`radar_runs` com `state: COMPLETED`, 5 pareceres, 29 respostas, integridade `OK`;
preservação com `violations: []`.

O `status` V2 sempre informa `expired`. A partir de 13/10/2026 17:29 BRT ele
passa a `true`, e o status selado continua `VALID_PROPOSAL`. Isso é esperado.

## 4. Critérios de preservação

1. Os arquivos IMMUTABLE do manifesto mantêm o SHA-256 registrado.
2. `check_preservation.py --since preservation_before.json`: `changes: []`,
   `violations: []`.
3. `check_preservation.py` (baselines): `violations: []`; as duas mudanças
   OPERATIONAL legadas (`data/radar/hfl_multiasset_v1/job.json` e
   `last_prepare.json`) são conhecidas desde a V7.3.
4. O código selado V1 e V2 tem o mesmo hash registrado em
   `contracts.sources_sha256` dos contextos (`gpm_*.integrity.treatment_sources_unchanged`).

## 5. Procedimento de auditoria sugerido

1. Rodar a seção 2 e a seção 3; guardar as saídas.
2. Escolher uma linha qualquer de [COMPARISON_V1_V2.md](COMPARISON_V1_V2.md),
   localizar a métrica em [METRICS.json](METRICS.json) e a fonte em
   `EVIDENCE_MANIFEST.json → provenance`; abrir a fonte e conferir o campo.
3. Conferir que nenhuma conclusão de
   [SCIENTIFIC_REPORT.md](SCIENTIFIC_REPORT.md), seção 14, cita resultado
   financeiro, taxa ou superioridade.
4. Conferir que nenhum registro com `planner = FAKE_GLOBAL_PM_NOT_GEMINI` ou
   modo `SYNTHETIC_DEMO` aparece como resultado (`gpm.records_by_planner`).
