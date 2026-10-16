# HFL Premium V7.3 — execuções Radar, recuperação segura e endurecimento operacional

Qualificação de 12/10/2026. **Nenhuma chamada paga, nenhum claim novo, nenhuma
reserva liberada.** A chave Gemini esteve ausente em todo o trabalho. Arquitetura:
[HFL_PLATFORM_ARCHITECTURE.md](../../HFL_PLATFORM_ARCHITECTURE.md#v73--execuções-radar-multi-run).
Procedimentos: [runbook V7.3](../../HFL_OPERATIONS_RUNBOOK.md#v73--execuções-radar-incidente-e-recuperação).

| Arquivo | Conteúdo |
|---|---|
| [registry.json](registry.json) | Cópia do registry operacional (revisão 3) |
| [incident_root_sha256.json](incident_root_sha256.json) | SHA-256 dos 45 arquivos da raiz do incidente, tirados **antes** de qualquer alteração da V7.3 |
| [prepare_recovery.json](prepare_recovery.json) | Saída do preparo dos cinco inputs da recuperação |
| [compare_recovery_vs_original.json](compare_recovery_vs_original.json) | Comparação econômica recuperação × original |
| [preservation_since_prepare.json](preservation_since_prepare.json) | Antes/depois do registro + preparo |
| [preservation_baselines.json](preservation_baselines.json) | Baselines históricos no fim da entrega |
| [budget_recovery.json](budget_recovery.json), [preflight_recovery.json](preflight_recovery.json) | Orçamento e preflight (CONSULTA) |
| [check_platform.txt](check_platform.txt) | Diagnóstico final somente leitura |
| [regression_before_v73.txt](regression_before_v73.txt), [regression.txt](regression.txt), [ruff.txt](ruff.txt) | Regressão antes/depois e lint |
| [ui_check.json](ui_check.json) + `*.jpg` | Validação da UI via Chrome DevTools em 1440/640/420 px |

## 1. Registry de execuções: arquitetura e justificativa

`data/radar/registry.json` (local, fora do Git como todo `data/radar/`) é uma
allowlist versionada (`schema_version`, `revision`, histórico, selo SHA-256) e um
**índice**, não autoridade. `scripts/radar_runs.py` recalcula tudo dos registros
de cada raiz: inputs (`checked_input`), resultados (`detail`), claims, journals
(SQLite somente leitura), reservas e autorizações.

Por que um módulo externo, e não parâmetros no código existente: os arquivos
selados (`multiasset_radar.py`, `run_multiasset_radar.py`, `radar_api.py`)
entram no manifesto do tratamento (`sources_sha256`). Editá-los mudaria o
manifesto, invalidaria todo input congelado e transformaria a recuperação em
outro tratamento. O mesmo vale para o Global PM e o V5 (`contracts()`) e para
`radar_corporate_events.py` (hash na proveniência). Todos já aceitam a raiz
como parâmetro; faltava só uma autoridade que escolhesse raízes com segurança.
`dashboard/global_pm_api.py` e `portfolio_api.py` são fixados pelo baseline V7
e também não foram editados (uma edição intermediária foi detectada pelo próprio
`check_preservation.py` e revertida byte a byte).

Segurança do caminho: só IDs `radar-…` chegam do navegador; caminho registrado
precisa ser exatamente `data/radar/<nome>` (sem separadores, `..`, unidade ou
UNC); a raiz resolvida tem de ser idêntica ao caminho e filha direta de
`data/radar` (symlink ou junção é recusado), fora das áreas protegidas, e
nenhuma raiz pode ser registrada duas vezes (aliasing, com `normcase`).
Registry ausente, corrompido ou com selo divergente: tudo falha com
`registry_unavailable`/`registry_corrupted`, o servidor fica sem execução
operacional e nada é selecionado automaticamente.

Identidade: uma instância (`--instance-of`) só é aceita com o mesmo manifesto
(modelo, prompts, parâmetros e contratos) — `radar-2026-10-09-recovery-01` é
registrada como nova instância operacional do mesmo tratamento (`77d75777…`).
Raiz nova precisa estar vazia (nada copiado). Incidentes vêm de um catálogo
fixo (`INCIDENTS`) e são sempre somente leitura, inclusive contra edição manual
do registry.

## 2. Revisão da correção do guard (`scripts/network_scope.py`)

A correção do commit `8143808` foi confirmada (dispatcher único por `ContextVar`;
GET continua offline; worker não é afetado; sem patch/restore por chamada, logo
sem vazamento). A revisão encontrou e corrigiu dois pontos:

1. **Falso positivo de isolamento.** `getattr(socket.create_connection,
   "_hfl_scoped", False)` devolve um `MagicMock` verdadeiro quando o guard
   selado está ativo ou vazado. O indicador `network_isolation` (V7.2) e o
   `install()` podiam afirmar "isolado" exatamente no estado do incidente. Agora
   `qualified()` exige `is True` nos três atributos e nenhum módulo carregado com
   o guard selado.
2. **Instalação sobre patch ativo.** `install()` recusa
   (`network_patch_active_at_install`) se os atributos não são os originais do
   interpretador: capturar o guard selado como "original" tornaria o bloqueio
   permanente.

`qualified()` alimenta a UI (botão pago desabilitado) e o backend (`run` recusado
com `network_isolation_not_qualified_restart_server`). `radar_runs.py` instala o
guard explicitamente no CLI. Reinício no mesmo processo é idempotente (sem
dupla camada); o dispatcher não precisa de desinstalação no encerramento.
Limite registrado: em interpretadores cujas threads herdam o contexto (3.14
free-threaded), uma thread criada *dentro* de um escopo offline herdaria o
escopo; nenhum worker é criado assim hoje.

Servidor existente: nada escutava em 8090. Em 8081 há o servidor do operador
(PID 51508, iniciado 12/10 12:22, depois da correção do guard, mas anterior à
V7.3 — UI e execução operacional antigas). Não foi encerrado; o runbook (A)
descreve a reinicialização.

## 3–5. Execuções registradas e nova raiz

| ID | Estado | Inputs | Pareceres | Claims | Falhas | Reservadas / respostas | Reservado US$ |
|---|---|---|---|---|---|---|---|
| `radar-2026-10-09-original` (incidente) | `INCIDENT_PRESERVED` | 5 | 0 | 5 | 5 | 25 / 0 | 3,31776 (incerto; bloqueio local antes da conexão) |
| `radar-2026-10-09-recovery-01` | `INPUTS_READY` | 5 | 0 | 0 | 0 | 0 / 0 | 0 |
| `radar-demo-v4` (sintética) | `COMPLETED` | 5 | 5 | 5 | 0 | 30 / 30 | — |

Preparo (`radar_runs.py prepare`, mesmo caminho normalizado do botão): cinco
`PREPARED` em 4 min 12 s; COTAHIST 2026 baixado para o cache da nova raiz,
2025 lido de `data/raw` (somente leitura), fator do yfinance. Sem Gemini.

## 6. Comparação econômica com os inputs originais

Mesmos SHA dos COTAHIST 2025/2026 nos dois preparos, logo dados oficiais B3
idênticos. Por ativo: sessões (311, desde 2025-07-16), volume, barra bruta de
09/10, último fechamento ajustado, volatilidade 21d, eventos corporativos e
manifesto **idênticos**. A série ajustada difere por ruído do fator do yfinance:

| Ativo | Status | Máx. diferença relativa | Sessões diferentes | Features |
|---|---|---|---|---|
| PETR4 | EQUIVALENT_WITHIN_TOLERANCE | 1,42e-7 | 68 | idênticas |
| VALE3 | EQUIVALENT_WITHIN_TOLERANCE | 1,18e-7 | 36 | idênticas |
| ITUB4 | EQUIVALENT_WITHIN_TOLERANCE | 6,62e-7 | 161 | `rsi` 76,557382 → 76,557381 |
| WEGE3 | EQUIVALENT_WITHIN_TOLERANCE | 2,21e-7 | 91 | idênticas |
| BBAS3 | EQUIVALENT_WITHIN_TOLERANCE | 2,87e-7 | 101 | idênticas |

Tolerâncias declaradas (não aplicadas aos dados): preço ajustado relativo ≤
`FACTOR_NEIGHBOR_TOLERANCE` (1e-6, a mesma que o pipeline usa para considerar
fatores iguais); features/métricas ≤ 2e-6 absoluto (canônicas em 6 casas). Os
quatro ativos sem evento foram preparados no original (11/10) com o extrator V4;
na recuperação, com `RADAR_CORPORATE_EVENTS_V2` (sem evento, resultado igual):
diferença de proveniência, não econômica. ITUB4 tem a mesma bonificação de
26/12/2025 (×1,03, `PN EB N1`, DISMES 362→363) e o mesmo hash do normalizador.
BBAS3 continua com restrição individual (vol 0,5448 > 0,5): veto determinístico,
sem chamada de Risk. **Sem divergência material**; uma divergência material
deixaria a execução `BLOCKED` e o lote pago recusado.

## 7. UI com seleção de execução

`/radar` ganhou o seletor "Execução Radar consultada" (ID, sessão, estado,
pareceres, marcador de incidente) e o cartão da execução (sessão, origem,
estado e motivos, pareceres, classificação e identidade de tratamento, data de
preparação, inputs/claims/falhas, chamadas/respostas, orçamento próprio, reserva
das outras execuções com situação forense, próximo lote, exposição agregada,
autorização de orçamento e comparação). A URL leva `?run=`. Trocar a execução
aborta todas as requisições pendentes (`AbortController`) e invalida preflight e
consentimento; nenhum registro de duas raízes é misturado. Sessão e fonte vêm da
execução (não editáveis). Só a execução operacional do servidor aceita gravações;
POST leva o cabeçalho `X-HFL-Radar-Run`. A landing mostra a execução selecionada.

Validação real (Chrome headless via DevTools, servidor V7.3 próprio na porta
8093, somente GETs; [ui_check.json](ui_check.json)): 37/37 checagens — cartão
coerente com a seleção nas três execuções em 1440/640/420 px, universo de cinco
ativos, incidente somente leitura com banner, sem rolagem horizontal (Radar e
landing), Tab alcança o seletor, seta para baixo troca a execução e o cartão/URL
acompanham, três trocas rápidas terminam na última sem mistura, Gestor Global
com a execução transportada, modo travado e motivos da mesma execução. Zero erros
de console. A validação encontrou e corrigiu dois defeitos: universo vazio na
recuperação (a página lia `universe.json` operacional em vez do universo
registrado) e motivos do Gestor Global vindos da raiz legada (mistura de raízes).

Capturas: `radar-2026-10-09-recovery-01-{1440,640,420}.jpg`,
`radar-2026-10-09-original-1440.jpg`, `radar-demo-v4-1440.jpg`,
`global-pm-run-1440.jpg`, `landing-1440.jpg`.

## 8. Integração de origem com o Global PM

Fluxo: `/radar?run=ID` → "Levar seleção ao Gestor Global" →
`/portfolio?run=ID…` → `radar-selection` relê os pareceres **na raiz da
execução** → `global-prepare` com `radar_run` e `opinion_hashes` → o backend relê
tudo de novo (`pm.load_opinions`, selado), exige hashes iguais, mesma sessão da
execução, mesmo modo, ativos do universo e cinco pareceres íntegros → grava
`data/platform/v7/radar_origins/<id>.json` (selado, imutável) → congela o
contexto. `global?id=` mostra a origem (`VERIFIED`/`MISMATCH`/`MISSING`);
`global-run` pago exige `VERIFIED`. Modo oficial sem execução é recusado
(`radar_run_required`). Trocar depois a execução selecionada não muda o contexto
nem a origem (teste). Hoje a recuperação tem 0/5 pareceres: o Global PM oficial
permanece bloqueado. Execução financeira multiativos continua inexistente.

## 9–10. Orçamento entre execuções e estados

Distinções expostas em UI, CLI e diagnóstico: estimado (US$ 0,14625 para o lote),
reserva conservadora (US$ 3,31776), custo observado pelos tokens (estimativa,
não fatura), faturado confirmado (sempre desconhecido), reserva incerta, orçamento
da execução (US$ 3,32) e exposição agregada (US$ 6,63552 > limite local US$ 5).
Sem política aprovada de teto agregado, o bloqueio permanece: o lote pago exige
`radar_runs.py authorize-budget` (decisão humana, **não executada**), vinculado às
reservas de todas as execuções no momento; qualquer reserva nova o invalida. A
reserva do incidente não foi liberada nem copiada. Mapeamento dos estados no
[runbook](../../HFL_OPERATIONS_RUNBOOK.md#v73--execuções-radar-incidente-e-recuperação).

Limite conhecido: os CLIs selados (`run_multiasset_radar.py --root`,
`radar_corporate_events.py prepare --root`) não consultam registry nem orçamento
agregado; o runbook usa `radar_runs.py`. Caminho de correção: parâmetro de gate
quando esses arquivos forem reselados.

## 11. Testes

`tests/test_radar_runs.py` (37 testes, raízes e registry temporários, Gemini falso
em loopback, transporte real bloqueado) cobre os 30 cenários pedidos: registry
com várias execuções; seleção válida; ID desconhecido; path traversal (8
variações); symlink/junção externa; registry ausente/corrompido/selo divergente/
aliasing; incidente somente leitura; ledgers, claims e orçamentos independentes;
orçamento agregado não contornável (autorização com token, invalidação por nova
reserva, orçamento da execução); cinco inputs oficiais reais válidos; ITUB4
normalizado e BBAS3 restrito (reais); troca de execução durante consulta (Node,
abort); Radar → Global PM na mesma raiz e origem congelada; mistura de sessão e
de fonte; menos de cinco pareceres; GET sem efeitos; replay sem conexão; GET
offline concorrente com worker pago; dois guards sobrepostos; recusa de instalar
sobre patch e detecção de regressão; falha de comitê e cobrança desconhecida;
preflight sem chamadas nem gravação; pago bloqueado sem cabeçalho, isolamento,
orçamento, fora da identidade ou com fonte trocada; incidente nunca alvo;
preservação dos 45 arquivos do incidente; estado vazio da UI com registry
corrompido. Mutações (remover o gate agregado; remover o cabeçalho de execução)
derrubam os testes correspondentes.

Regressão (V4–V7.3, H2 dashboard/supervisão/forward; [regression.txt](regression.txt)):
**253 aprovados, 2 falhas** (as duas legadas da seção 12). Antes da V7.3, o mesmo
conjunto sem os testes novos dava 215 aprovados e 3 falhas
([regression_before_v73.txt](regression_before_v73.txt)): as duas legadas e um
`PermissionError [WinError 5]` transitório do Windows em `os.replace` dentro de
uma pasta temporária de teste V5 (antivírus/indexador), que não se repetiu.
Durante a V7.3, uma rodada intermediária expôs duas quebras de contrato
introduzidas por esta entrega (título "[Radar oficial" do diagnóstico e
`attention()` com relatório sem a chave nova), corrigidas antes da rodada
final. Ruff (check e format) e `node --check` limpos ([ruff.txt](ruff.txt)).

## 12. As duas falhas legadas de preservação

`test_global_pm.py::test_31_original_ledgers_preserved` e
`test_multiasset_portfolio.py::test_original_scientific_radar_and_ledger_preservation`
comparam o hash exato de **todos** os arquivos fixados pelos baselines históricos
V6 (11.027) e V5 (10.922). Divergem apenas
`data/radar/hfl_multiasset_v1/job.json` e `last_prepare.json`, alterados pelas
ações do operador em 12/10 (preparo do ITUB4 às 02:41 e lote das 02:59), antes
da V7.3 e inalterados por ela.

- **Estado histórico selado:** inputs, barras, eventos, claims, journals,
  reservas, manifestos, decisões, evidências — todos idênticos (`violations: []`
  nos quatro baselines; 45/45 arquivos do incidente idênticos).
- **Estado operacional legítimo:** `job.json` (estado do job da API),
  `last_prepare.json` (relatório da última chamada), `universe.json`, caches
  COTAHIST — classificados OPERATIONAL desde a V7.2.

Fixtures isoladas não reproduzem a verificação original: os testes existem para
conferir o repositório real contra os pinos históricos, e o conteúdo antigo
daqueles dois arquivos não é recuperável (só o hash) nem pode ser reescrito para
imitar o passado. Proposta metodológica (**não aplicada**, depende de aprovação):
nos dois testes, manter o hash exato para tudo que `check_preservation.classify`
classifica como VIOLATION e apenas relatar os OPERATIONAL — equivalente a exigir
`check_preservation.baselines()["violations"] == []`, que passa hoje. Baselines e
valores esperados não foram alterados. **A suíte não está toda verde:** essas
duas falhas permanecem, pelo motivo acima.

## 13. Comandos do próximo preflight

```powershell
$P = '.venv/Scripts/python.exe'
& $P -B scripts/radar_runs.py budget --run radar-2026-10-09-recovery-01                          # CONSULTA → budget_token
& $P -B scripts/radar_runs.py authorize-budget --run radar-2026-10-09-recovery-01 --confirm <budget_token>   # GRAVA, decisão humana
$env:GEMINI_API_KEY = '<somente neste terminal>'
& $P -B scripts/radar_runs.py preflight --run radar-2026-10-09-recovery-01                       # CONSULTA → confirmation_token
& $P -B scripts/radar_runs.py run --run radar-2026-10-09-recovery-01 --confirm <confirmation_token> --authorize-paid   # PAGA (não executado)
```

Estado atual do preflight: `BLOCKED` por `aggregate_budget_authorization_required`
e `gemini_api_key_missing`; 30 chamadas máximas, 29 planejadas.

## 14. Preservação

- `check_preservation.py` no fim: `violations: []` nos quatro baselines; só
  `job.json` e `last_prepare.json` do incidente diferem (OPERATIONAL, anteriores
  à V7.3) — [preservation_baselines.json](preservation_baselines.json).
- Snapshot antes de qualquer alteração (`data/platform/antes-v73-2026-10-12.json`)
  × fim: nenhum arquivo da raiz do incidente nem de `data/forward` mudou; novos
  apenas o registry (OPERATIONAL) e a raiz da recuperação; `demo-v4` entrou na
  cobertura depois (UNCOVERED_BEFORE) e é conferida pelo baseline V7, que fixa
  seus 65 arquivos sem diferença.
- Registro + preparo: [preservation_since_prepare.json](preservation_since_prepare.json),
  sem VIOLATION. A raiz da recuperação não existia antes (verificado).
- Regressão final: snapshot antes × depois sem nenhuma mudança.
- `test_real_incident_records_all_preserved`: 45/45 arquivos do incidente
  (5 claims, 5 `failure.json`, journals, eventos, inputs, reserva) idênticos a
  [incident_root_sha256.json](incident_root_sha256.json).
- H2: integridade íntegra (manifesto `dc118ce9…`), decisão de 09/10 e ledgers
  intactos (`check_platform.txt`).

## Restrições respeitadas

Sem Gemini real, claims pagos, liberação de reservas, reescrita de journals,
decisões H2, Validation, Final Test, alterações em `src/`, prompts ou parâmetros
congelados, carteiras prospectivas, aprovação supervisionada, reconciliação,
operação financeira multiativos, migração de stack ou push.
