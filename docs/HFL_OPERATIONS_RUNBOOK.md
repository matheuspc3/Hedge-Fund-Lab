# HFL V7.3 — runbook operacional

Executar no diretório do projeto, em PowerShell. Cada comando abaixo traz uma
classe:

| Classe | Significado |
|---|---|
| **CONSULTA** | Somente leitura, gratuita. Não baixa, não grava, não chama Gemini. |
| **GRAVA** | Gratuita, mas baixa dados e/ou escreve inputs, ledgers ou registros. Só por ação explícita. |
| **PAGA** | Chama Gemini. Exige preflight, token e autorização própria. |

Nenhum comando PAGA foi executado. Na V7.3, os únicos GRAVA executados foram o
registro das execuções Radar (`data/radar/registry.json`), o preparo dos cinco
inputs da nova raiz de recuperação e snapshots de preservação; a raiz do
incidente não foi alterada (seção V7.3 abaixo).

## V7.4 — Global PM V2

A inferência real V1 `v7-5a78ea5d15214e37bcae18f167ffcee3` é evidência somente
leitura: `REJECTED_BY_VALIDATOR`, custo `UNKNOWN` (pensamento não informado),
reserva US$ 0,159744 mantida. Não preparar nem executar nada sobre ela.

| Ação | Comando | Classe |
|---|---|---|
| Reproduzir a rejeição e o contrafactual | `.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py incident` | CONSULTA |
| Testes offline V2 | `.venv/Scripts/python.exe -m pytest -q tests/test_global_pm_v2.py` | CONSULTA |
| Qualificação sintética A–F (US$ 0) | `.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py qualify` | GRAVA |
| Preparar contexto V2 de uma execução Radar | `… run_global_pm_v2.py prepare --radar-run ID --confirm-hypothetical --ack-fixture-policy` | GRAVA |
| Preflight (origem, orçamento V1+V2, validade) | `… run_global_pm_v2.py preflight --id v74-…` | CONSULTA |
| Inferência V2 (uma chamada, sem retry) | `… run_global_pm_v2.py run --id v74-… --confirm <token> --authorize-paid` | **PAGA** |
| Resultado / replay do journal | `… run_global_pm_v2.py status --id v74-…` / `replay --id v74-…` | CONSULTA |

A UI de `/portfolio` mostra registros V2 somente para consulta; preparar e
executar V2 é pelo CLI, com autorização humana separada. Antes e depois de
qualquer GRAVA/PAGA: `scripts/check_preservation.py --snapshot`/`--since`.
Detalhes: [evidence/hfl_global_pm_v2/README.md](evidence/hfl_global_pm_v2/README.md).

## V7.3 — execuções Radar, incidente e recuperação

Cada **execução Radar** é uma raiz própria em `data/radar/` (sessão, universo,
inputs, claims, journals, reservas e orçamento próprios), catalogada em
`data/radar/registry.json`. O registry é **índice e allowlist**, não autoridade:
estados, contagens e orçamento são sempre recalculados dos registros de cada raiz
por `scripts/radar_runs.py`. O navegador só envia IDs, nunca caminhos.

| ID | Raiz | Estado em 12/10/2026 |
|---|---|---|
| `radar-2026-10-09-original` | `data/radar/hfl_multiasset_v1` | `INCIDENT_PRESERVED` — `INCIDENT_2026_10_12_NETWORK_GUARD`: **Falha local confirmada — lote preservado — não reutilizável para novas chamadas.** 5 inputs, 5 claims, 5 falhas, 25 chamadas reservadas, 0 respostas; reserva local US$ 3,31776 (não é custo faturado; cobrança no provedor não confirmada). |
| `radar-2026-10-09-recovery-01` | `data/radar/hfl_multiasset_v1_recovery_01` | `INPUTS_READY` — 5 inputs oficiais preparados em 12/10 12:59, 0 claims; nova instância operacional do **mesmo tratamento** (manifesto `77d75777…`); orçamento próprio US$ 3,32; **selecionada** e execução operacional do servidor. Pago bloqueado até a autorização de orçamento agregado (E). |
| `radar-demo-v4` | `data/radar/demo-v4` | `COMPLETED` — demonstração sintética, somente leitura. |

Estados conceituais (`radar_runs.status`):

| Estado | Significado |
|---|---|
| `INCIDENT_PRESERVED` | incidente catalogado; nunca alvo de chamadas |
| `INPUTS_READY` | inputs completos; a exposição agregada exige autorização de orçamento separada |
| `AWAITING_AUTHORIZATION` | falta só o preflight e a autorização paga do lote |
| `RUNNING` | `operation.lock` presente (pode ser lock órfão: consultar) |
| `COMPLETED` | todos os pareceres do universo íntegros |
| `PARTIAL` | parte concluída, parte com claim sem resultado |
| `RECOVERY_REQUIRED` | claims sem resultado: só replay offline |
| `BLOCKED` | inputs ausentes, execução somente leitura, análises fora da sessão/universo da execução ou divergência material com a execução de referência |
| `INTEGRITY_ERROR` | input, journal, reserva ou autorização divergente |

Nos jobs e na landing, os estados comuns da V7 (`COMMON` em `platform_api.py`)
continuam valendo.

**Orçamento.** Valores distintos na UI e no diagnóstico: estimado
(planejamento), reserva conservadora, custo observado pelos tokens do provedor
(estimativa, não fatura), faturado confirmado (sempre "desconhecido": não há
fonte de fatura local), reserva de resultado incerto, orçamento da execução e
exposição agregada das execuções oficiais. Não existe política aprovada de teto
agregado: o limite local original de **US$ 5** vale para a soma. Incidente
(US$ 3,31776) + lote de recuperação (US$ 3,31776) = **US$ 6,63552**: o lote pago
fica bloqueado até uma **autorização de orçamento separada**, gravada pelo
operador e vinculada à exposição atual (qualquer nova reserva em qualquer
execução a invalida). Reservas antigas nunca são liberadas nem copiadas.

**Limite conhecido.** Os CLIs selados (`run_multiasset_radar.py --root`,
`radar_corporate_events.py prepare --root`, `run_global_pm.py`) não consultam o
registry nem o orçamento agregado. Use os comandos abaixo; o servidor só aceita
`prepare`/`run` na execução operacional registrada.

### A. Reiniciar a plataforma

| # | Passo | Comando | Classe |
|---|---|---|---|
| 1 | Descobrir quem escuta (12/10 12:22: PID 51508 em 8081, anterior à V7.3; nada em 8090). | `Get-NetTCPConnection -State Listen -LocalPort 8081,8090 -ErrorAction SilentlyContinue \| Select-Object LocalPort,OwningProcess` | CONSULTA |
| 2 | Confirmar que o PID é o servidor HFL (`…\.venv\Scripts\python.exe dashboard/server.py`). **Não encerrar processo desconhecido.** | `Get-CimInstance Win32_Process -Filter "ProcessId=<PID>" \| Select-Object ProcessId,CreationDate,CommandLine` | CONSULTA |
| 3 | Conferir que não há job Radar/Global em `RUNNING` (encerrar no meio de um lote exige replay offline). | `.venv/Scripts/python.exe -B scripts/check_platform.py` (seção Jobs) | CONSULTA |
| 4 | Encerrar o servidor antigo: Ctrl+C no terminal dele; sem terminal, `Stop-Process -Id <PID>` **somente** para o PID confirmado no passo 2. Não reutilizar processo antigo: pode manter o guard selado vazado. | Ctrl+C / `Stop-Process -Id <PID>` | GRAVA (estado do processo; nenhum registro) |
| 5 | Iniciar a versão corrigida. Log esperado: `Radar runner: radar-2026-10-09-recovery-01`. Sem registry válido: `Radar runner: nenhum` e preparo/execução recusados (sem fallback). | `.venv/Scripts/python.exe -B dashboard/server.py 8081` | CONSULTA (serve a UI) |
| 6 | Em `/radar`: execução selecionada no seletor, "Execução operacional do servidor", sem aviso de isolamento. Com aviso: reiniciar de novo — o botão pago fica desabilitado e o backend recusa `run` (`network_isolation_not_qualified_restart_server`). | `http://localhost:8081/radar` | CONSULTA |

### B. Consultar o incidente (somente leitura)

| Comando | Classe |
|---|---|
| `.venv/Scripts/python.exe -B scripts/radar_runs.py status --run radar-2026-10-09-original` | CONSULTA |
| `http://localhost:8081/radar?run=radar-2026-10-09-original` (botões desabilitados) | CONSULTA |
| `.venv/Scripts/python.exe -B scripts/check_platform.py` (seção "Execuções Radar") | CONSULTA |
| Forense: [incidente](evidence/hfl_incident_2026_10_12/README.md); hashes dos 45 arquivos: [incident_root_sha256.json](evidence/hfl_radar_v73/incident_root_sha256.json) | CONSULTA |

Replay do incidente não reconstrói nada (não há envelopes) e a plataforma não
aceita comandos nessa execução. Nunca apagar claims, journals, `failure.json` ou
a reserva.

### C. Preparar a nova execução (executado em 12/10/2026; referência)

```powershell
$P = '.venv/Scripts/python.exe'; $T = 'PETR4','VALE3','ITUB4','WEGE3','BBAS3'
& $P -B scripts/check_preservation.py --snapshot data/platform/antes-v73-recovery-prepare.json   # GRAVA (só o snapshot)
& $P -B scripts/radar_runs.py register --run radar-2026-10-09-original --path data/radar/hfl_multiasset_v1 --session 2026-10-09 --tickers $T --existing --incident INCIDENT_2026_10_12_NETWORK_GUARD   # GRAVA (registry)
& $P -B scripts/radar_runs.py register --run radar-demo-v4 --path data/radar/demo-v4 --session 2026-10-09 --tickers PETR4 VALE3 ITUB4 BBAS3 WEGE3 --mode SYNTHETIC_DEMO --existing --read-only   # GRAVA (registry)
& $P -B scripts/radar_runs.py register --run radar-2026-10-09-recovery-01 --path data/radar/hfl_multiasset_v1_recovery_01 --session 2026-10-09 --tickers $T --budget-usd 3.32 --instance-of radar-2026-10-09-original --select   # GRAVA (registry)
& $P -B scripts/radar_runs.py prepare --run radar-2026-10-09-recovery-01   # GRAVA (inputs da nova raiz; B3 + yfinance; sem Gemini)
& $P -B scripts/check_preservation.py --since data/platform/antes-v73-recovery-prepare.json   # CONSULTA
& $P -B scripts/radar_runs.py compare --run radar-2026-10-09-recovery-01 --with radar-2026-10-09-original   # CONSULTA; exit 1 se divergência material
```

`register` recusa raiz já registrada (aliasing), raiz nova não vazia (nada é
copiado), caminho fora de `data/radar/<nome>`, symlink/junção e instância com
manifesto diferente. `prepare` usa o mesmo caminho normalizado do botão de
`/radar` (`radar_corporate_events.install()` + `radar.prepare`) com a sessão e o
universo da execução. Resultado: 5 `PREPARED`; comparação sem divergência
material ([evidências V7.3](evidence/hfl_radar_v73/README.md)).

### D. Conferir preservação

| Comando | Esperado | Classe |
|---|---|---|
| `& $P -B scripts/check_preservation.py` | `violations: []`; só `job.json` e `last_prepare.json` da raiz do incidente como OPERATIONAL (mudaram em 12/10 02:41 e 02:59, antes da V7.3) | CONSULTA |
| `& $P -B scripts/check_preservation.py --since <snapshot>` | nenhuma VIOLATION | CONSULTA |
| `& $P -B -m pytest -q tests/test_radar_runs.py -k real` | incidente idêntico aos 45 hashes; recuperação com 5 inputs válidos | CONSULTA |
| `& $P -B scripts/radar_runs.py compare --run radar-2026-10-09-recovery-01 --with radar-2026-10-09-original` | `material: false` | CONSULTA |

### E. Preflight e orçamento

| # | Passo | Comando | Classe |
|---|---|---|---|
| 1 | Reservas por execução (com situação forense), orçamento da execução, chamadas máximas/planejadas (30/29: BBAS3 tem veto determinístico, sem Risk), exposição agregada e `budget_token`. | `& $P -B scripts/radar_runs.py budget --run radar-2026-10-09-recovery-01` | CONSULTA |
| 2 | **Decisão humana separada** sobre a exposição agregada acima do limite local (US$ 6,63552 > US$ 5): grava `budget_authorizations/<token>.json` na raiz da recuperação. Não chama provedor e não libera a reserva antiga. Sem este passo o lote pago continua bloqueado. | `& $P -B scripts/radar_runs.py authorize-budget --run radar-2026-10-09-recovery-01 --confirm <budget_token>` | GRAVA |
| 3 | Preflight completo: preflight selado do lote + orçamento agregado + bloqueios + frase de consentimento + `confirmation_token`. Exige `$env:GEMINI_API_KEY` no mesmo terminal (sem ela: `gemini_api_key_missing`). Exit 0 só sem bloqueios. | `& $P -B scripts/radar_runs.py preflight --run radar-2026-10-09-recovery-01` | CONSULTA |

### F. Autorizar o Gemini (procedimento futuro — **não executado** nesta entrega)

```powershell
$env:GEMINI_API_KEY = '<chave somente neste terminal; nunca em arquivo, log ou relatório>'
& $P -B scripts/radar_runs.py preflight --run radar-2026-10-09-recovery-01   # CONSULTA: copiar confirmation_token
& $P -B scripts/radar_runs.py run --run radar-2026-10-09-recovery-01 --confirm <confirmation_token> --authorize-paid   # PAGA: até 30 chamadas, reserva US$ 3,31776
```

Preferir o CLI (processo próprio, `network_scope` instalado explicitamente).
Pela UI: servidor reiniciado (A); a chave vem do ambiente ou do `.env` (ver "Chave"),
`/radar?run=radar-2026-10-09-recovery-01` → "2. Verificar preflight" → marcar o
consentimento → "3. Confirmar e executar". O backend repete todas as checagens.
Token, preflight ou autorização de outra execução nunca valem aqui.

### G. Consultar resultados

`/radar?run=radar-2026-10-09-recovery-01` (tabela, Sala de Decisão por ativo e
comparação), `& $P -B scripts/radar_runs.py status --run radar-2026-10-09-recovery-01`
e `scripts/check_platform.py` — todos CONSULTA. Falha parcial (`PARTIAL`,
`RECOVERY_REQUIRED`): só replay offline, nunca repetir chamadas do claim.

### H. Enviar ao Gestor Global (R$ 100.000 hipotéticos)

| # | Passo | Local | Classe |
|---|---|---|---|
| 1 | Com 5/5 pareceres completos, "Levar seleção ao Gestor Global" em `/radar?run=…` abre `/portfolio?run=radar-2026-10-09-recovery-01&…#global-workflow`. | UI | CONSULTA |
| 2 | "Verificar pareceres": o backend relê os cinco pareceres **na raiz da execução** (mesma sessão, oficial, íntegros) e devolve seus hashes. | UI | CONSULTA |
| 3 | Capital `100000`, os dois reconhecimentos, "Preparar contexto": grava o registro de origem selado (`data/platform/v7/radar_origins/<id>.json`: execução, tratamento, sessão, universo, fonte, hashes dos pareceres, referências dos inputs) e o contexto imutável. Hashes do navegador divergentes bloqueiam. | UI | GRAVA |
| 4 | Preflight global (estimativa, teto US$ 0,159744, validade 24 h, token). | UI | CONSULTA |
| 5 | Autorizar **apenas** a inferência global (exige origem `VERIFIED`; a autorização Radar não vale aqui). | UI | **PAGA** |

Trocar depois a execução selecionada não altera um contexto congelado nem sua
origem. Contextos do CLI V6 (`run_global_pm.py prepare --radar-root …`) não têm
registro de origem V7.3; a plataforma recusa sua inferência paga.

## Iniciar e consultar

```powershell
.venv/Scripts/python.exe -B dashboard/server.py 8081          # serve a UI (loopback)
.venv/Scripts/python.exe -B scripts/check_platform.py         # CONSULTA, resumo por seção
.venv/Scripts/python.exe -B scripts/check_platform.py --json  # CONSULTA, visão completa
.venv/Scripts/python.exe -B scripts/run_h2_v6_supervised.py verify  # CONSULTA
git status --short                                            # CONSULTA
```

Abrir `http://localhost:8081/`. Se a porta estiver ocupada, usar outra e acessar
**todos os módulos na mesma base**. Não usar servidor estático genérico.

`check_platform.py` informa, por seção: H2 original (decisão e sessão-alvo),
supervisão (estado e prazo), carteiras e benchmarks (prontidão e posições),
Radar (estado por ticker e próxima ação), Global PM (pareceres e validade dos
contextos), mercado (última sessão observada), jobs incompletos/incertos/
bloqueados, integridade e ações manuais pendentes. Roda sob bloqueio de rede.
Código de saída 2 se a integridade H2 não puder ser verificada; conferir as
seções mesmo com código 0. A página `/` mostra as mesmas derivações no bloco
**Atenção necessária**.

## Fotografia em 12/10/2026 (feriado B3; próximo pregão 13/10)

- Última sessão observada **09/10**. Cinco carteiras de R$ 100.000 cada, em
  caixa, sem operações reconciliadas. Capitais independentes; não somar.
- Decisão original de 09/10: COMPRA PETR4, 5/5 votos, Risk aprovado, alvo 100%
  na abertura de **13/10 às 10h BRT**. Gerada em 10/10 15:17:04 BRT. SHA-256
  `27e51c949aebac155b1d890c6fff74d1a242852d7f5c8d3a30cdc602a6a09ddc`.
- Supervisionada: **AGUARDANDO_APROVACAO**, prazo **13/10 às 10h BRT**, auditoria
  íntegra (1 evento), nenhuma aprovação registrada.
- Ordens para 13/10: H2, Buy & Hold e SMA. Bollinger sem ordem. SMA/Bollinger
  comparáveis.
- Radar oficial 09/10: cinco inputs congelados (ITUB4 preparado pelo operador
  em 12/10 02:41). O lote pago de 02:59 falhou por completo (incidente abaixo):
  claims imutáveis, 0/5 pareceres, US$ 3,31776 reservados, US$ 1,68224 livres
  nessa raiz. Global PM oficial indisponível.

## Checklist A — 13/10, antes da abertura (até 10h BRT)

| # | Passo | Comando / local | Classe |
|---|---|---|---|
| 1 | Árvore e diagnóstico. Esperado: integridade íntegra, próxima ação = supervisão. | `git status --short` · `scripts/check_platform.py` | CONSULTA |
| 2 | Auditoria da supervisão. | `scripts/run_h2_v6_supervised.py verify` | CONSULTA |
| 3 | Conferir a decisão **já registrada** de 09/10 (SHA acima), quórum, Risk, PM e intenção. **Não clicar em executar agentes; não rodar `run_h2_v6_forward.py run`**: 09/10 já está decidida. | `/paper#sala` | CONSULTA |
| 4 | Conferir limites da supervisão e simular cenário (em memória). | `/paper#supervisao`, `/paper#mercado` | CONSULTA |
| 5 | Decisão humana, se o operador quiser: aprovar ou rejeitar antes de 10h. Write-once, sem Gemini. Sem ação tempestiva, expira; não inventar aprovação nem mudar prazo. | UI `/paper#supervisao` ou `scripts/run_h2_v6_supervised.py approve 2026-10-09 27e51c949aebac155b1d890c6fff74d1a242852d7f5c8d3a30cdc602a6a09ddc [--limit NOME=VALOR]` (ou `reject` com os mesmos argumentos) | GRAVA |
| 6 | Calendário: 13/10 é sessão regular (12/10 feriado). Previsão não confirma leilão; não há intradiário. | `/paper#mercado` | CONSULTA |
| 7 | **Não** preparar contexto Global PM agora: vale 24 h e não há pareceres oficiais. | — | — |

## Checklist B — depois da publicação do COTAHIST de 13/10

Os runners consideram a sessão encerrada a partir de **18h BRT**. Executar
quando a B3 tiver publicado os dados de 13/10; se o preparo não encontrar a
sessão, parar e tentar mais tarde. Nunca inventar preço.

| # | Passo | Comando | Classe |
|---|---|---|---|
| 1 | Diagnóstico: esperado "Preparar o fechamento oficial de 13/10/2026". | `scripts/check_platform.py` | CONSULTA |
| 2 | Congelar o input oficial de 13/10 (COTAHIST + fator yfinance). | `scripts/run_h2_v6_forward.py prepare` | GRAVA |
| 3 | Conferir offline: sessão 13/10, abertura bruta oficial, fator, custos, prévia de reconciliação (unidades, caixa, custos), hashes e identidade. | `scripts/run_h2_v6_forward.py preflight` | CONSULTA |
| 4 | Supervisionada: reconcilia a ordem de 13/10 **somente** se aprovada e válida; caso contrário registra o desfecho (rejeitada/expirada). | `scripts/run_h2_v6_supervised.py sync` e depois `verify` | GRAVA / CONSULTA |
| 5 | Benchmarks determinísticos: reconcilia a ordem SMA de 13/10 e marca Bollinger; podem criar ordens para 14/10. | `scripts/run_h2_v6_forward_benchmarks.py sma_regime_h2_proposed` · `… bollinger_state_h2_proposed` | GRAVA |
| 6 | H2 original + Buy & Hold: a reconciliação da intenção de 13/10 acontece **dentro** do `run`, que também decide 13/10 com Gemini. Só com autorização explícita, usando o token do passo 3. Sem autorização, essas duas carteiras permanecem marcadas em 09/10 com a intenção pendente (limitação deliberada: não há reconciliação H2 isolada). | `scripts/run_h2_v6_forward.py run --confirm <token>` | **PAGA** |
| 7 | Se o passo 6 ocorreu antes de 14/10 10h, sincronizar a supervisionada de novo para registrar a proposta de 13/10 (sem decisão gravada, `sync` não fecha a proposta antes do prazo). | `scripts/run_h2_v6_supervised.py sync` | GRAVA |
| 8 | Conferência final: carteiras, custos, posições, jobs e integridade. | `scripts/check_platform.py` · `/paper#carteiras` · `git status --short` | CONSULTA |

Benchmarks e supervisionada têm ledgers próprios; não copiar posições entre
carteiras. Não reconciliar manualmente nem editar ledgers.

## Radar → Gestor Global (laboratório, opcional)

Desde a V7.2 existe **um único caminho de preparo**: o botão "1. Preparar dados"
de `/radar` e o CLI abaixo executam a mesma chamada `radar.prepare` com o
normalizador de bonificações instalado (`radar_corporate_events.install()`, feito
pelo `server.py` na inicialização). Nenhum ticker tem caminho próprio.
**Preparar dados e executar análises são ações independentes**: preparar é
gratuito, grava inputs e nunca chama Gemini; analisar exige preflight e
autorização paga do lote. Fluxo para uma sessão encerrada `S`:

| # | Passo | Comando | Classe |
|---|---|---|---|
| 0 | Registrar hashes antes (arquivo novo, nunca sobrescrito). | `scripts/check_preservation.py --snapshot data/platform/antes-S.json` | GRAVA (só o snapshot) |
| 1 | Preparar os cinco na execução registrada: reutiliza inputs existentes sem regravar; congela os ausentes. | `/radar?run=ID` → "1. Preparar dados", ou `scripts/radar_runs.py prepare --run ID` | GRAVA |
| 2 | Antes/depois: só `last_prepare.json`, `job.json`, cache COTAHIST (OPERATIONAL) e arquivos novos (NEW); `violations` vazio. | `scripts/check_preservation.py --since data/platform/antes-S.json` | CONSULTA |
| 3 | Conferir inputs, normalização, risco individual e preflight por ticker. | `/radar` (Conferência dos inputs) ou `scripts/check_platform.py` | CONSULTA |
| 4 | Opcional: eventos, histórico e equivalência com o extrator original. | `scripts/radar_corporate_events.py diagnose --session S` | CONSULTA (lê rede) |
| 5 | Preflight do lote Radar: estimativa, reserva, orçamento próprio e agregado, token. | `/radar?run=ID` ("2. Verificar preflight") ou `scripts/radar_runs.py preflight --run ID` | CONSULTA |
| 6 | Autorizar o **lote Radar** (até 6 chamadas por ativo, sem retry) na execução registrada; ver V7.3 E–F. | `scripts/radar_runs.py run --run ID --confirm <token> --authorize-paid` ou `/radar?run=ID` | **PAGA** |
| 7 | Elegibilidade conjunta (mesma fonte/sessão, todos os pareceres). | `/portfolio#global-workflow` ou `scripts/check_platform.py` | CONSULTA |
| 8 | Preparar contexto com snapshot hipotético **perto do uso** (validade 24 h). | `/portfolio#global-workflow` | GRAVA |
| 9 | Preflight global (Risk conjunto, estimativa, teto US$ 0,159744). | idem | CONSULTA |
| 10 | Autorizar a **inferência Global PM**; a autorização Radar não vale aqui. | idem | **PAGA** |

`scripts/run_multiasset_radar.py prepare` (CLI V4 selado) continua com o extrator
original estrito; para preparar use o botão ou `radar_corporate_events.py prepare`.
Um bloqueio em `last_prepare.json` descreve só a última chamada; a autoridade são
os inputs congelados (`analyses/<ticker>/<sessão>/input.json`).

**Preparo do ITUB4 na raiz oficial (executado pelo operador em 12/10 02:41; referência):**

```powershell
.venv/Scripts/python.exe -B scripts/check_preservation.py --snapshot data/platform/antes-itub4-2026-10-09.json
.venv/Scripts/python.exe -B scripts/radar_corporate_events.py prepare --session 2026-10-09 --tickers PETR4 VALE3 ITUB4 WEGE3 BBAS3
.venv/Scripts/python.exe -B scripts/check_preservation.py --since data/platform/antes-itub4-2026-10-09.json
```

Os quatro inputs existentes são reutilizados byte a byte; ITUB4 é congelado com o
evento de 26/12/2025 em `source.corporate_events`. Resultado esperado: "5 inputs
prontos; 0/5 pareceres oficiais" (qualificado em raiz isolada pelo endpoint real).
Equivale a clicar "1. Preparar dados" com os cinco selecionados e a sessão 09/10.

Chave: o runner H2 e, desde a V7.4, o **servidor** (`dashboard/server.py`) leem
`GEMINI_API_KEY` do `.env` local (fora do Git) quando o ambiente não a tem; o
ambiente do terminal sempre prevalece. Só essa variável é carregada, só no
processo do servidor, e o log mostra apenas a origem (`ambiente`, `.env` ou
`ausente`), nunca o valor. Ter a chave não autoriza nada: as etapas PAGAS
continuam exigindo preflight, token e consentimento explícito. Os CLIs pagos
(`radar_runs.py run`, `run_global_pm_v2.py run`) ainda leem **somente o ambiente
do processo**: para eles, definir `$env:GEMINI_API_KEY` no terminal (sem ela:
`gemini_api_key_missing`). Nunca colar a chave em comandos registrados ou na UI.
Nenhuma operação financeira multiativos existe.

## ITUB4 — causa-raiz e correção

Bloqueio original: `split-like mismatch between yfinance and B3 closes:
{2025: 0.97087, 2026: 1.0}`. Evidência (`docs/evidence/hfl_platform_v71`):

- yfinance registra **Stock Split 1.03 em 26/12/2025** para ITUB4.SA e, mesmo com
  `auto_adjust=False`, devolve `Close` retroajustado por splits. COTAHIST é
  nominal. Antes de 26/12, `Close(yf)/fechamento B3 = 1/1,03 = 0,970874`
  exatamente; depois, 1,000000. `Adj Close/Close` (fator de proventos) é contínuo
  no evento (0,978753 dos dois lados).
- A B3 corrobora: em 26/12/2025 o COTAHIST marca ITUB4 `PN EB N1`
  (**ex-bonificação**) e o número de distribuição DISMES muda 362→363; fechamento
  40,26 → 39,10. Mesmo padrão em 18/03/2025 (bonificação de 10%).
- Não é exclusivo de ITUB4: 40 ativos à vista têm marca de ex-bonificação na
  janela de 450 dias. Amostra verificada: ITUB3 1,03; MGLU3 1,05; RADL3 1,02;
  KLBN4 1,01; EGIE3 1,40. Todos bloqueados pelo extrator original e corrigidos.
  PETR4, VALE3, WEGE3 e BBAS3 não têm evento na janela.

Correção (`scripts/radar_corporate_events.py`, V7.2 `RADAR_CORPORATE_EVENTS_V2`;
`src/` e os arquivos selados do Radar inalterados): restaura o `Close` nominal do
yfinance **apenas** para eventos que a B3 confirma como bonificação na mesma
sessão (marca ESPECI com "B" — EB, EDB, EJB — e mudança de DISMES) e confere as
sessões vizinhas; depois aplica a mesma guarda anual e a mesma tolerância (1e-3)
do original. Desdobramento, grupamento, dividendo (EJ/ED) ou evento sem
confirmação continuam bloqueando. Vários eventos na janela são tratados do mais
recente ao mais antigo. `Adj Close`, o OHLC bruto e o volume oficial não mudam;
o fator passa a incluir o evento (retorno total contínuo). Sem evento, o
resultado é idêntico bit a bit ao extrator original. O input registra tipo,
data-ex, razão, fator de preço aplicado, ESPECI, DISMES, fechamentos e hash do
módulo em `source.corporate_events`; o manifesto Radar não muda, logo os
pareceres seguem compatíveis com o Global PM.

## Incidente de 12/10/2026 02:59 — guard offline no lote pago

Causa: o guard offline selado (`no_network()`) troca o socket do processo
inteiro; um GET de prontidão (V7.2) o ativava em paralelo ao worker pago. As 25
chamadas falharam localmente antes de qualquer conexão; zero envelopes. Correção:
`scripts/network_scope.py` (guard por contexto), instalado por `server.main()`.
O lote é um **incidente imutável**: não apagar claims, journals, falhas ou a
reserva; replay não reconstrói e não chama o provedor. Nova tentativa somente em
raiz operacional separada, com orçamento e autorização novos.
Detalhes e procedimento: [incidente](evidence/hfl_incident_2026_10_12/README.md).

## Ciclo de vida dos arquivos

Política em `scripts/check_preservation.py`; baselines históricos nunca são
editados. Evidência imutável: manifests, inputs congelados e barras, eventos,
decisões, journals, claims, reservas/autorizações, registros científicos e
demonstrações seladas. Estado operacional mutável autorizado: `last_prepare.json`
(relatório da última chamada), `job.json`, `universe.json`, caches COTAHIST do
ano corrente e jobs da UI. Ledgers (`state.json` de H2, supervisionada e
benchmarks) evoluem só pelos runners originais e são conferidos por eles. Um
cache nunca é relido para validar um input congelado: o input guarda o SHA do
COTAHIST que usou e é verificado pelas próprias barras.

## Jobs interrompidos ou erro

Consultar `/#audit`, `/api/platform/jobs`, `check_platform.py` e o detalhe da
análise. Custo N/D não significa zero. Com claim/journal e sem resultado,
**Recuperar somente offline** uma única vez. Nunca apagar claim, journal ou lock
para forçar nova chamada; não ressuscitar contexto expirado nem substituir
hashes. Logs brutos ficam locais.

## Qualificação

Ver [evidências V7.3](evidence/hfl_radar_v73/README.md), [evidências V7.2](evidence/hfl_platform_v72/README.md),
[evidências V7.1](evidence/hfl_platform_v71/README.md),
[evidências V7](evidence/hfl_platform_v7/README.md) e
[arquitetura](HFL_PLATFORM_ARCHITECTURE.md). Nenhum passo desta entrega executou
Gemini, Validation, Final Test, aprovação humana, reconciliação ou operação
financeira.
