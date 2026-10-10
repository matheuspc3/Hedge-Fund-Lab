# H2 v6 — Runbook: dashboard e Validation provisória OA-1

Estado: **HEDGE-FUND-LAB DASHBOARD READY — VALIDATION AWAITING AUTHOR AUTHORIZATION**.
Governança: [amendment OA-1](H2_V6_OPERATIONAL_AMENDMENT_OA1.md). Final Test fica fora deste runbook.

## Dashboard (somente leitura)

```powershell
.venv\Scripts\python.exe dashboard/server.py        # ou: just dashboard
# http://localhost:8081/h2   (atalhos: #demo/compare, #provisional/experiments)
```

O servidor escuta só em `127.0.0.1`. Não há endpoint de escrita, de credenciais ou que dispare
inferência. Fontes: **Provisória OA-1**, **Oficial** (bloqueada) e **Demonstração** (dados
sintéticos, faixa `DEMONSTRAÇÃO — DADOS SINTÉTICOS`, nunca misturados com os reais).

| Endpoint (GET) | Conteúdo |
|---|---|
| `/api/h2/status` | identidade do manifesto, governança, estado das fases |
| `/api/h2/validation?source=` | métricas, curvas, ΔSharpe, progresso, custos, selos |
| `/api/h2/run?source=&run=` | decisions e timeline de trades de um run |
| `/api/h2/trace?source=&run=&session=` | chamadas Technical/Risk/Portfolio de uma sessão |
| `/api/h2/artifact?source=&run=&name=` | download de artifact selado (lista branca: `manifest.json`, `equity.csv`, `trades.csv`, `decisions.jsonl` e os três arquivos de fase) |
| `/api/h2/analysis?source=` | preço × decisões, ciclos, exposição, comportamento multiagente |
| `/api/h2/decision?source=&run=&session=` | Technical → Risk → Portfolio → execução de uma sessão |

Durante a execução, abra **Experimentos**: atualização a cada 10 s. Ela mostra sessões, chamadas,
tentativas HTTP, retries, erros de transporte e chamadas em voo por run. O journal é lido com
`immutable=1`, sem locks, e nunca bloqueia os commits FULL do run.

## Análise pós-Validation

Abra `http://localhost:8081/h2#provisional/decisions` com a fonte **Provisória OA-1**. A faixa
`VALIDATION OA-1 — NÃO RATIFICADA ACADEMICAMENTE` fica visível em todas as abas.

- **Decisões.** O gráfico mostra o fechamento de PETR4, as SMA50/200 reconstruídas, a decisão
  em *t* (marcador vazado) e a execução em *t+1* (marcador cheio). Os botões filtram L01, L02,
  L03 e os trades do Bollinger. Clicar num marcador ou numa data abre a sessão com os cinco
  votos, o Risk (regras, veto efetivo ou sem efeito), o PM e a execução; ←/→ e o campo de data
  navegam. Clicar num ciclo da timeline o destaca no gráfico.
- **Comparações.** Mostra o patrimônio dos seis participantes (o tooltip traz o retorno
  acumulado), as métricas, a exposição ao mercado com os dois denominadores e a grade de
  custos, que exibe `N/A — EXACT_REPLAY_INVALID` onde o replay é inválido.
- **Multiagente.** Para cada camada mostra se foi chamada, se produziu decisão e se alterou a
  trajetória. Traz ainda votos por analista, frequência de consenso, divergência entre runs e o
  fluxo sinal → decisão → ordem.

Tudo é calculado no backend a partir dos artifacts `COMPLETE` da fonte. Nenhum preço externo é
usado e o snapshot não é aberto. A demonstração não tem traces e mostra um estado vazio.
`llm_calls.jsonl` (prompts completos), `provider_journal.jsonl` (envelopes HTTP) e os SQLite
não são servidos por HTTP; os traces mostram só entradas estruturadas e respostas validadas, e
a auditoria completa continua offline sobre os arquivos em disco. O Chart.js 4.4.1 é servido
localmente (`dashboard/vendor/`), então os gráficos funcionam sem CDN; sem internet, só as
fontes Google caem para as fontes do sistema.
Verificação: `.venv\Scripts\python.exe -B -m pytest tests/test_h2_dashboard_analysis.py`.
Síntese: [H2_V6_OA1_VALIDATION_SCIENTIFIC_SUMMARY.md](H2_V6_OA1_VALIDATION_SCIENTIFIC_SUMMARY.md).

## Validation provisória: passos exatos

1. **Preflight** (offline, sem egress), em árvore limpa:
   `.venv\Scripts\python.exe -B scripts/run_h2_v6_provisional.py preflight`
2. **Autorização do autor** (ato humano; agentes não executam). Use a frase impressa pelo preflight:
   `.venv\Scripts\python.exe -B scripts/run_h2_v6_provisional.py authorize --signatory "<nome completo>" --confirm "AUTORIZO OA-1 VALIDATION <prefixo>"`
3. **Congelar o pacote operacional:** `git add docs/evidence/h2_v6_provisional && git commit -m "Record OA-1 author authorization"`.
   O registro vincula manifesto, amendment, runner, tratamento, R, runs, janela, snapshot, host, saída e commit.
4. **Preflight de novo:** deve imprimir `PREFLIGHT: READY` e o comando exato com `--confirm <12 hex>`.
5. **Executar** (egress e cobrança reais):
   `.venv\Scripts\python.exe -B scripts/run_h2_v6_provisional.py run --confirm <12 hex do registro>`.
   O comando executa L01..L03 e os benchmarks, grava `summary.json`, fecha as 24 disposições de
   custo, emite `validation_release.json` e chama `audit`.
6. **Selar:** `git add docs/evidence/h2_v6_provisional && git commit -m "Seal OA-1 provisional Validation checkpoint"`.
   Para reauditar: `... run_h2_v6_provisional.py audit` (idempotente).
   Faça backup de `data/runs/h2_v6_provisional/` (ignorado pelo Git).

## Estimativa (Gemini 3.8 Flash, tier pago, preço introdutório até 2026-12-31)

| Item | Valor |
|---|---|
| Sessões de decisão × runs | 247 × 3 |
| Chamadas lógicas | ~3.850 esperadas (5 técnicos/sessão + Risk/Portfolio ocasionais); máx. 5.187 |
| Tentativas HTTP | máx. 31.122 (6 por chamada) |
| Tokens | ~4,24 M entrada; ~0,73 M saída, incluindo thoughts |
| Custo | **~US$ 6 esperado**; orçamento prudente US$ 15; teto teórico ~US$ 980 (todas as tentativas com 8.192 tokens de saída) |
| Duração | ~45 min para os três runs, mais replay local de custos |

Preços: US$ 0,75 / 3,75 por 1 M tokens; a partir de 2027-01-01, US$ 1,50 / 7,50. Confirme no
painel de billing. ~5 chamadas simultâneas por sessão exigem tier pago (≈100 RPM). Cotas do
free tier causam 429 e esgotam os retries.

## Falhas irrecuperáveis (fail closed, sem chamada substituta)

- Interromper no meio de um slot (Ctrl+C, suspensão, queda de energia ou rede): a recuperação é
  replay-only; o slot não continua com nova inferência.
- Recusa do provedor (chave inválida, 400/401/403) ou retries esgotados (429/5xx persistentes):
  o erro fica registrado e o slot falha deterministicamente.
- `execution.lock` restante após queda: investigar manualmente; nunca remover às cegas.
- Banco/journal corrompido ou apagado: não é reconstruído.

Uma Validation provisória incompleta exige novo amendment. Antes de executar: energia na
tomada, suspensão desativada, rede estável e terminal dedicado.
