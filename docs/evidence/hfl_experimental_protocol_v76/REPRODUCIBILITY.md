# Reprodutibilidade — auditoria e qualificação offline da V7.6

Todos os comandos são offline: nenhum chama o Gemini, exige chave, cria
registro, claim, journal ou reserva, ou grava em `data/`. Só o `build` grava,
e só três JSON desta pasta. Execute na raiz do repositório.

## 1. Entradas

| Conjunto | Caminho | No Git? |
|---|---|---|
| Pacote V7.6 | `docs/evidence/hfl_experimental_protocol_v76/` | sim |
| Pacote V7.5 | `docs/evidence/hfl_scientific_consolidation_v75/` | sim |
| Código | `scripts/experiment_protocol_v76.py`, `scripts/verify_consolidation_v75.py` e os runners selados que eles importam (somente leitura) | sim |
| Radar recovery-01 | `data/radar/hfl_multiasset_v1_recovery_01/`, `data/radar/registry.json` | **não** |
| Global PM V1 e V2 reais | `data/global_pm/hfl_global_pm_v1/v7-5a78…/`, `data/global_pm/hfl_global_pm_v2/v74-76d0…/` e as reservas | **não** |

Sem os registros locais, os testes da classe `Protocol` são pulados e os
verificadores acusam `missing`. Os testes de regras puras (`PureRules`) rodam
em qualquer cópia.

## 2. Comandos

```powershell
$P = '.venv/Scripts/python.exe'
& $P -B scripts/experiment_protocol_v76.py audit       # auditoria V7.5 (ok: true)
& $P -B scripts/experiment_protocol_v76.py erratum     # errata de tokens do Radar
& $P -B scripts/experiment_protocol_v76.py validate    # {"errors": []}
& $P -B scripts/experiment_protocol_v76.py plan        # plano e orçamento (igual a BUDGET_PLAN.json)
& $P -B scripts/experiment_protocol_v76.py qualify     # 34/34 casos, árvores seladas inalteradas
& $P -B scripts/experiment_protocol_v76.py readiness   # state: QUALIFIED_OFFLINE
& $P -m pytest -q tests/test_experiment_protocol_v76.py tests/test_consolidation_v75.py
python -B scripts/verify_consolidation_v75.py          # pacote V7.5 (só biblioteca padrão)
& $P -B scripts/check_preservation.py --since docs/evidence/hfl_experimental_protocol_v76/preservation_before.json
```

**GRAVA** (só nesta pasta: `BUDGET_PLAN.json`, `READINESS_REPORT.json` e os
campos `state`, `documents`, `protocol_sha256` e `supporting_documents` do
`EXPERIMENT_MANIFEST.json`):

```powershell
& $P -B scripts/experiment_protocol_v76.py build
```

Rodar `build` depois de editar um documento do protocolo muda o
`protocol_sha256`. No estado `QUALIFIED_OFFLINE` isso é permitido; depois de
`FROZEN_FOR_FUTURE_EVALUATION`, o validador recusa (`frozen_protocol_modified`)
e a mudança exige versão nova.

Testes de pipeline sem PostgreSQL: [TEST_FAILURE_TRIAGE.md](TEST_FAILURE_TRIAGE.md), seção 2.

## 3. O que cada verificação garante

| Verificação | Garante | Não garante |
|---|---|---|
| `audit` | hashes, fontes, métricas, separação real × sintético e status selados da V7.5; recomputação de tokens pelos envelopes brutos | revisão humana independente |
| `erratum` | estado do campo de pensamento em cada envelope bruto (com hash conferido); regra de agregação no código | cobrança real |
| `validate` | identidade, estados, contratos V2 e Radar iguais aos selados, cenários e métricas coerentes, ausência de vazamento temporal e de janelas H2, V1 fora das campanhas | qualidade científica das escolhas |
| `qualify` | cada regra de S0–S9 se comporta como declarado no validador V2 selado, sem efeitos | comportamento do modelo real |
| `plan` | contagem de chamadas, reservas, tetos e bloqueios; IDs determinísticos e únicos | custo efetivo |
| `readiness` | portões e bloqueios; estado máximo `QUALIFIED_OFFLINE` | autorização de execução |

## 4. Hashes e fins de linha

Os hashes de documentos (`EXPERIMENT_MANIFEST.json → documents`) são calculados
sobre os bytes com fim de linha LF, como estão no Git. Numa cópia com
`core.autocrlf=true`, o checkout converte para CRLF e o `validate` acusa
`protocol_documents_changed_rebuild_required`. Use
`git -c core.autocrlf=false clone …`, ou confira os blobs do Git. O mesmo
vale para o pacote V7.5.

## 5. Determinismo

Os contextos de qualificação são congelados num instante fixo
(`QUAL_AT = 2026-10-12T21:00:00+00:00`), então `qualification_sha256` se
repete entre execuções. O plano não tem horário e `plan_sha256` também se
repete. A seleção de sessões depende só do calendário e da semente.
