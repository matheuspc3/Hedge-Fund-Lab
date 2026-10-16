# HFL V7.1 — official data & operational readiness

Qualificação de 11–12/10/2026, branch `#1-Update`, sem push. Nenhuma chamada
Gemini, aprovação, reconciliação, operação financeira, Validation ou Final Test.
Runbook: [HFL_OPERATIONS_RUNBOOK.md](../../HFL_OPERATIONS_RUNBOOK.md).

| Evidência | Conteúdo |
|---|---|
| [itub4_diagnosis.json](itub4_diagnosis.json) | Diagnóstico reproduzível dos cinco tickers oficiais, sessão 09/10 |
| [other_bonus_sample.json](other_bonus_sample.json) | Mesmo diagnóstico em ITUB3, MGLU3, RADL3, KLBN4, EGIE3 |
| [radar_isolated_prepare.json](radar_isolated_prepare.json) | `radar.prepare` real dos cinco em raiz isolada + preflight Radar + recusa Global PM |
| [preflight_radar_official.json](preflight_radar_official.json) | Preflight Radar da raiz oficial (somente leitura) |
| [preflight_global.json](preflight_global.json) | Prontidão por ticker, seleção oficial e preflight do contexto sintético V7 |
| [integrity.json](integrity.json) | Quatro baselines de preservação, identidade científica e hash da decisão |
| [regression.txt](regression.txt) | Suíte de regressão V7 + testes novos |
| `landing-*.jpg`, `radar-640.jpg`, `global-workflow-420.jpg` | Capturas via DevTools em largura CSS exata |

## 1. ITUB4: causa-raiz

Bloqueio: `split-like mismatch between yfinance and B3 closes: {2025: 0.9708737739656967, 2026: 0.9999999928491858}`.

| Fato | Valor | Fonte |
|---|---|---|
| Evento no yfinance | `Stock Splits = 1.03` em **2025-12-26** (também 1.10 em 2025-03-18) | `yf.download(actions=True)`, `Ticker.splits` |
| `Close(yf) / fechamento B3` | 0,970874 = 1/1,03 até 23/12/2025; 1,000000 a partir de 26/12 | COTAHIST × yfinance |
| `Adj Close / Close` | 0,978753 em 22/12, 23/12 e 26/12 (contínuo) | yfinance |
| Marca oficial B3 em 26/12/2025 | ESPECI `PN EB N1` (ex-bonificação); DISMES 362→363 | COTAHIST_A2025 |
| Fechamento oficial | 40,26 (23/12) → 39,10 (26/12); 40,26/1,03 = 39,087 | COTAHIST_A2025 |

Conclusão: diferença de convenção, não dado ruim. O yfinance trata a
bonificação de 3% como split e retroajusta `Close` mesmo com
`auto_adjust=False`; o COTAHIST é nominal; o extrator original assume `Close`
nominal e, corretamente, recusa a mistura. Não é exclusivo de ITUB4: 40 ativos
à vista têm marca de ex-bonificação na janela de 450 dias. Na amostra, todos
foram bloqueados pelo original e explicados por evento corroborado.

## 2. Correção

`scripts/radar_corporate_events.py` (camada exploratória do Radar), injetado
pelo parâmetro já existente `radar.prepare(extractor=...)`. Nenhum byte de
`src/`, `multiasset_radar.py`, `radar_api.py` ou `run_multiasset_radar.py` mudou.

- Restaura o `Close` nominal do yfinance só para split **corroborado pela B3**
  (DISMES muda na mesma sessão) e confere as duas sessões vizinhas ao evento.
- Depois aplica a mesma guarda anual e a mesma tolerância 1e-3 do original.
  Evento não corroborado, data divergente ou desvio sem evento: continua bloqueado.
- Sem evento, saída idêntica bit a bit ao extrator original
  (`original_extractor_identical_bars: true` para PETR4, VALE3, WEGE3, BBAS3).
- O input registra `source.corporate_events` (evento, ESPECI, DISMES, fechamentos,
  hash do módulo). O manifesto Radar não muda (`77d75777…`), portanto a família
  de pareceres continua compatível com o Global PM.

Testes offline em `tests/test_radar_corporate_events.py` (COTAHIST sintético com
ESPECI/DISMES): bonificação corroborada, original ainda bloqueia, split sem
DISMES recusado, evento com data divergente recusado, desvio sem evento mantém
o bloqueio, equivalência sem evento e `prepare` com identidade Radar intacta.

## 3. Cinco tickers oficiais (sessão 09/10/2026)

Janela 2025-07-16 → 2026-10-09, 311 barras (mínimo 200), sessões iguais ao
calendário B3, volume > 0, 8 features, contrato Radar V4 (`technical_input`) ok.
Fonte: COTAHIST TPMERC 010 / CODBDI 02 × fator yfinance;
COTAHIST_A2025 `6cc0ad85…`, COTAHIST_A2026 `d55b48e4…`.

| Ticker | Evento na janela | Vol. 21d | Raiz oficial | Diferença máx. vs. input congelado |
|---|---|---|---|---|
| PETR4 | nenhum | 0,392 | PREPARED, aguarda autorização Radar | 1,8e-7 (revisão de `Adj Close` do provedor; features idênticas) |
| VALE3 | nenhum | 0,238 | PREPARED, aguarda autorização Radar | 1,2e-7 (idem) |
| ITUB4 | bonificação 1,03 em 26/12/2025, corroborada | 0,429 | **sem input**: bloqueio original; preparo normalizado pendente de ação do operador | — |
| WEGE3 | nenhum | 0,215 | PREPARED, aguarda autorização Radar | 2,9e-7 (idem) |
| BBAS3 | nenhum | 0,545 | PREPARED, aguarda autorização Radar | 2,1e-7 (idem) |

BBAS3 tem volatilidade 21d acima de 0,50: pela regra existente, o Risk do Radar
vetará por `HARD_ASSET_VOLATILITY_RULE` sem chamar o LLM de Risk.

Raiz isolada `data/platform/v71-radar-qualification` (ignorada pelo Git): os
cinco foram preparados com o extrator normalizado, `checked_input` íntegro.
Não se gravou na raiz oficial porque `last_prepare.json` e o COTAHIST em cache
estão no baseline V7; o comando do operador está no runbook.

## 4. Preflights

| Módulo | Resultado |
|---|---|
| Radar oficial 09/10 | não pronto: quatro `gemini_api_key_missing` (Radar lê só o ambiente do processo), ITUB4 sem input |
| Radar isolado 09/10 | sem chave: bloqueado; com chave fictícia: pronto, reserva US$ 3,31776, estimativa US$ 0,14625, orçamento 0/5; nenhum claim |
| Global PM oficial | `INSUFFICIENT_DATA`: cinco pareceres ausentes, motivo por ticker; teto de uma chamada US$ 0,159744 |
| Global PM sintético V7 | `already_claimed_replay_only`: nenhuma segunda chamada possível |
| Fluxo fake completo | prepare → preflight → run (fake E) → VALID_PROPOSAL, duplicado recusado, replay sem nova chamada (`test_complete_fake_flow_duplicate_and_replay`) |
| Autorizações | token Radar recusado no Global PM e vice-versa (`test_radar_and_global_authorizations_are_independent`) |
| GETs | sete rotas sem escrita nem inferência, transporte Gemini bloqueado (`test_get_routes_never_infer_or_write`) |

## 5. Visão Geral

Hero compactado; bloco **Atenção necessária** (`id="readiness"`, link de
navegação preservado) derivado em `platform_api.attention()`: próxima ação,
última decisão, aprovação humana, próximo pregão, estado dos dados e
pendências. Substitui os painéis duplicados de decisão, supervisão, calendário
e alertas. Em 1440 px os cartões de carteira começam dentro da primeira dobra (900 px);
em 420 px os cinco itens aparecem na primeira tela. Sem rolagem horizontal em
1440, 640 e 420 (`scrollWidth == clientWidth`).

## 6. Bloqueios remanescentes

- ITUB4 permanece sem input na raiz oficial até o operador executar o preparo
  normalizado; nenhum parecer oficial existe (0/5).
- Radar/Global PM exigem `GEMINI_API_KEY` no ambiente do processo.
- Reconciliação H2/Buy & Hold de 13/10 só ocorre dentro do `run` pago de 13/10.
- O botão "Preparar" de `/radar` usa o extrator selado; tickers com bonificação
  na janela exigem o comando normalizado.
- Calendário prevê, não confirma, o pregão; não há intradiário.

## 7. Verificação em árvore limpa (após os commits de código)

Saídas gravadas fora do repositório durante a execução e copiadas depois.

| Verificação | Resultado |
|---|---|
| [preflight H2 original](preflight_h2_clean.txt) | `treatment_identity: true`, input 09/10 congelado, chave presente; **NOT READY** por `not_yet_decided: false` (09/10 já decidida, impede repetir a inferência). `ledger_reconciles` falha por intervalo vazio: o ledger já está marcado em 09/10; após o `prepare` de 13/10 o intervalo passa a 10/10→13/10. |
| [supervisão verify](supervision_verify.txt) | `ok: true`, 1 evento, sem erros |
| [diagnóstico](check_platform.txt) | integridade H2 íntegra; próxima ação: aprovar ou rejeitar a supervisionada até 13/10/2026 10:00 BRT |
| [integridade](integrity.json) | quatro baselines sem alteração; identidade `dc118ce9…acb98`; decisão `27e51c94…a09ddc` |
