# HFL Premium V7.5 — Consolidação científica: Radar, Global PM V1 × V2

Consolidação documental de 12/10/2026 sobre evidências já existentes.
**Nenhuma chamada ao Gemini, nenhuma inferência nova, nenhum claim, journal ou
reserva criado ou alterado, nenhuma operação financeira, nenhum registro
científico modificado.** O H2 v6 fica fora do escopo e intocado.

Estado das inferências, confirmado de novo nesta etapa pelos verificadores
somente leitura:

| Registro | Tratamento | Status selado |
|---|---|---|
| `radar-2026-10-09-recovery-01` | `HFL-MULTIASSET-RADAR-V1` | `COMPLETED`, 5/5 pareceres, integridade `OK` |
| `v7-5a78ea5d15214e37bcae18f167ffcee3` | `HFL-MULTIASSET-GLOBAL-PM-V1` | **`REJECTED_BY_VALIDATOR`** (`explanation_selection_inconsistent`) |
| `v74-76d07c0d32444cecaf07e875deacb519` | `HFL-MULTIASSET-GLOBAL-PM-V2` | **`VALID_PROPOSAL`** (`GLOBAL_PM_VALIDATION_V2`) |

## Arquivos

| Arquivo | Conteúdo | Público |
|---|---|---|
| [SCIENTIFIC_REPORT.md](SCIENTIFIC_REPORT.md) | Relatório completo (15 seções): arquitetura, procedimento, Radar, estudo de caso V1, V2, discussão, conclusões | banca / orientação |
| [COMPARISON_V1_V2.md](COMPARISON_V1_V2.md) | Tabela V1 × V2, intenção × conformidade × validação × resultado, decisão por ativo | banca |
| [COST_ACCOUNTING.md](COST_ACCOUNTING.md) | Tokens, pisos, estimativas, reservas, cobrança; conciliação do Radar | banca / operador |
| [THREATS_TO_VALIDITY.md](THREATS_TO_VALIDITY.md) | 15 ameaças com efeito e mitigação futura | banca |
| [RESEARCH_GAPS.md](RESEARCH_GAPS.md) | Perguntas abertas priorizadas por valor e viabilidade | orientação |
| [TCC_RESULTS_DRAFT.md](TCC_RESULTS_DRAFT.md) | Texto preliminar para o capítulo de resultados | monografia |
| [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Entradas, comandos offline, critérios de preservação, auditoria | avaliador |
| [EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json) | 64 fontes com SHA-256, classe, natureza, imutabilidade e relação; matriz de proveniência | máquina |
| [METRICS.json](METRICS.json) | 32 métricas com definição, numerador, denominador, unidade, fonte e ressalva | máquina |
| [preservation_before.json](preservation_before.json) | Snapshot de preservação tirado antes de qualquer artefato da V7.5 | verificação |
| `preservation_since.json`, `verification.json`, `regression.txt` | Saídas finais (seção "Verificação final") | verificação |

Código: `scripts/verify_consolidation_v75.py` (só biblioteca padrão; `check`
somente leitura, `build` grava apenas os dois JSON desta pasta) e
`tests/test_consolidation_v75.py` (o pacote confere com os registros; uma
métrica adulterada e um hash adulterado são detectados).

**Consolidação.** Os dez entregáveis pedidos foram mantidos, sem conteúdo
repetido: cada tabela detalhada tem uma única fonte (comparação, custos,
ameaças, lacunas), e o relatório resume e aponta para ela. O rascunho do TCC
tem outro público e outro registro (prosa para a monografia, sem caminhos nem
hashes). As visualizações são diagramas Mermaid de fluxo no relatório (§3 e
§7.4). Não há gráficos de rentabilidade, risco futuro ou alocação, porque não
existem dados observados para eles.

## Escopo e fontes

Sessão de mercado 09/10/2026; inferências em 12/10/2026 sobre dados
congelados. Fontes primárias locais (não versionadas): os cinco comitês do
Radar recovery-01 e os registros V1 e V2 (contexto, autorização, claim, journal
privado, SQLite, resultado, reserva). Fontes versionadas: código dos
tratamentos (hash selado nos contextos), evidências V7.3, V7.4 e do incidente.

| Grupo | Classe | Arquivos | Onde | Git |
|---|---|---|---|---|
| Radar recovery-01: barras, inputs, claims, journals, SQLite, pareceres | PRIMARY | 30 | `data/radar/hfl_multiasset_v1_recovery_01/analyses/` | não |
| Radar: reserva, autorização de orçamento | PRIMARY | 2 | idem | não |
| Registry de execuções | PRIMARY · OPERATIONAL | 1 | `data/radar/registry.json` | não |
| Global PM V1 (registro real) + reserva + origem Radar | PRIMARY | 8 | `data/global_pm/hfl_global_pm_v1/…`, `data/platform/v7/radar_origins/…` | não |
| Global PM V2 (registro real) + reserva | PRIMARY | 7 | `data/global_pm/hfl_global_pm_v2/…` | não |
| Código dos tratamentos V1/V2 | PRIMARY | 4 | `scripts/` | sim |
| Contratos e visões da plataforma | DERIVED | 2 | `docs/evidence/hfl_global_pm_v2/` | sim |
| Reprodução V1, forense do incidente, equivalência, hashes do incidente, snapshot V7.5 | DIAGNOSTIC | 5 | `docs/evidence/…` | sim |
| Qualificação V2 A–F, registro V1 de demonstração | SYNTHETIC | 2 | `docs/evidence/hfl_global_pm_v2/`, `data/global_pm/…` | parcial |
| Auditoria manual V7.4 (§9), delimitação H2 | INTERPRETATIVE | 2 | `docs/` | sim |
| Métricas V7.5 | DERIVED | 1 | esta pasta | sim |

Ausências registradas: nenhuma fonte esperada está ausente. Não existe fatura
do provedor nas evidências locais (cobrança desconhecida). A execução Radar
original não tem pareceres por causa do incidente, e não por ausência de
arquivo.

## Notas de auditoria (sem alteração das fontes)

1. **Pensamento no agregado do Radar.** Os `result.json` de PETR4, ITUB4, WEGE3
   e BBAS3 gravam `thoughts_tokens: 0`, mas as chamadas correspondentes nos
   journals têm `thoughts_tokens: null` (não informado); o `cost_usd` gravado
   ("estimated billing") é, na prática, o piso pelos tokens informados
   ([COST_ACCOUNTING.md](COST_ACCOUNTING.md), §3). O código do Radar é selado e
   não foi editado. A errata formal fica para decisão da orientação.
2. **Risk de BBAS3.** O enunciado de referência descreve "cinco analistas
   Gemini além da avaliação de risco individual" para cada comitê. Em BBAS3, o
   Risk não foi um LLM: a regra determinística de volatilidade vetou o ativo, e
   o Risk LLM não foi chamado (29 chamadas, não 30).
3. **Origem Radar do V1.** O contexto V1 não sela a origem (`radar_origin`
   inexistente no V1); ela está no arquivo lateral
   `data/platform/v7/radar_origins/v7-5a78….json`, e os hashes dos pareceres
   conferem com os `result.json` do Radar. No V2, a origem é selada no contexto.
4. **Texto livre V2.** "Teto regulamentar" (o limite é uma política didática
   interna) e linguagem preditiva ("risco de correção imediata") permanecem na
   resposta válida. Não são erros de dado: são afirmações sem suporte que o
   validador V2, por desenho, não verifica (relatório, §8.3).
5. Os valores da tabela de referência do operador (consensos, Risk,
   recomendações, tokens, pisos e reservas V1/V2) conferem com as fontes
   primárias.

## Limitações

Uma sessão, cinco comitês e duas inferências globais de tratamentos diferentes;
sem repetição; carteira hipotética e políticas didáticas; nenhuma ordem
executada e nenhum resultado financeiro; custo só como piso; texto livre
auditado manualmente; reprodução completa dependente de registros locais. Ver
[THREATS_TO_VALIDITY.md](THREATS_TO_VALIDITY.md).

## Verificação final

Executada depois dos commits `adecfb6` e `12c94ed`, com a árvore limpa.

**Verificadores (somente leitura, sem chave Gemini):**

| Verificação | Resultado |
|---|---|
| `verify_consolidation_v75.py` ([verification.json](verification.json)) | `ok: true`; nada ausente, nenhuma violação, nenhuma divergência de métrica ou de tabela |
| `run_global_pm_v2.py incident` (V1) | `REJECTED_BY_VALIDATOR`; revalidação idêntica à selada; saída idêntica a `../hfl_global_pm_v2/incident_reproduction.json` |
| `run_global_pm_v2.py status --id v74-76d0…` (V2) | `VALID_PROPOSAL`, sem erro de integridade (selos, journal, SQLite `mode=ro`, custo, revalidação) |
| `radar_runs.py status --run radar-2026-10-09-recovery-01` | `COMPLETED`, 5 pareceres, 29/29 respostas, integridade `OK` |

**Preservação:**

- `check_preservation.py --since preservation_before.json`
  ([preservation_since.json](preservation_since.json)): `changes: []`,
  `violations: []`. O mesmo resultado foi obtido antes da V7.5 contra o
  snapshot do operador (`data/platform/antes-gpm-v2.json`).
- Baselines históricos: `violations: []`; só as duas mudanças OPERATIONAL
  legadas (`data/radar/hfl_multiasset_v1/job.json`, `last_prepare.json`).
- Os 52 arquivos PRIMARY do manifesto (registros V1/V2, Radar, código selado)
  mantêm o SHA-256, e o código V1/V2 continua igual ao hash selado nos contextos.

**Regressão** (suíte completa, `pytest -q`; [regression.txt](regression.txt)):
**1706 aprovados, 15 falhas**. A suíte **não** está toda verde. Na V7.4 eram
1703 aprovados; a diferença é +1 teste do commit `946813d` (carregamento da
chave a partir do `.env`) e +2 testes da V7.5. As 15 falhas são exatamente as
mesmas da V7.4 (comparação nome a nome), e nenhuma envolve código da V7.5:

| Falhas | Causa | Relação com a V7.5 |
|---|---|---|
| `test_global_pm.py::test_31_original_ledgers_preserved`, `test_multiasset_portfolio.py::test_original_scientific_radar_and_ledger_preservation` | Legadas de preservação operacional: hash exato de `job.json`/`last_prepare.json` do Radar original, alterados pelo operador em 12/10 (OPERATIONAL, `violations: []`) | nenhuma |
| `test_radar_runs.py::test_real_recovery_has_five_official_inputs_equivalent_to_original`, `::test_real_itub4_bonus_normalized_and_bbas3_restricted` | Testes da V7.3 que afirmam o estado da recuperação **antes** do lote pago (0 claims); desatualizados em relação aos dados locais | nenhuma |
| `tests/pipeline/test_flows.py` (7) | PostgreSQL em `127.0.0.1:5435` indisponível | ambiente |
| `test_cal_b4_safety`, `test_spec`, `test_v6_phase_routing` | Divergências antigas de código/teste H2 | nenhuma |
| `tests/pipeline/test_snapshot.py::test_manifest_adulterado_e_rejeitado[code]` | Par complementar com `test_h2_v6_provisional` (estado de limpeza do Git): com a árvore limpa, falha este | nenhuma |

Nenhum teste antigo foi alterado. Testes novos: `tests/test_consolidation_v75.py`
(2 aprovados). Lint (`ruff check` e `ruff format --check`) limpo nos dois
arquivos de código novos.

## Restrições respeitadas

Sem chamadas ao Gemini ou a qualquer provedor; sem inferência, Radar pago ou
Final Test H2; sem alteração de respostas, status, claims, journals, reservas,
políticas, baselines, Radar, recuperação ou H2 v6; nenhuma escrita em `data/`;
nenhuma ordem ou carteira prospectiva; sem métricas financeiras; sintéticos
separados dos oficiais; sem push.
