# HFL V7.2 — official multiasset Radar ready

Qualificação de 12/10/2026, branch `#1-Update`, sem push. Nenhuma chamada
Gemini, aprovação, operação, Validation ou Final Test. Nenhuma gravação nas
raízes oficiais: todo preparo novo ocorreu em raízes isoladas (ignoradas pelo Git).
Runbook: [HFL_OPERATIONS_RUNBOOK.md](../../HFL_OPERATIONS_RUNBOOK.md).

| Evidência | Conteúdo |
|---|---|
| [ui_path_isolated_prepare.json](ui_path_isolated_prepare.json) | `POST /api/radar/prepare` real (servidor com `install()`), cinco ativos, dados reais, raiz isolada com cópia dos quatro inputs oficiais |
| [diagnosis_official.json](diagnosis_official.json) | Cinco tickers oficiais, sessão 09/10, regra V2 |
| [diagnosis_other_bonus.json](diagnosis_other_bonus.json) | ITUB3, MGLU3, RADL3, KLBN4 (EDB), EGIE3 |
| [diagnosis_itub4_two_events.json](diagnosis_itub4_two_events.json) | Janela até 29/05/2026 com duas bonificações (18/03 e 26/12/2025) |
| [preservation.json](preservation.json) | Quatro baselines históricos sob a política de ciclo de vida |
| [check_platform.txt](check_platform.txt) | Diagnóstico somente leitura |
| [regression.txt](regression.txt), [ruff.txt](ruff.txt) | Regressão e lint |
| `radar-*.jpg`, `radar-inputs-*.jpg`, `landing-1440.jpg` | Capturas via DevTools em 1440, 640 e 420 px (raiz oficial) |

## 1. Diagnóstico inicial

| Caminho | Antes da V7.2 |
|---|---|
| UI `/radar` → `POST /api/radar/prepare` → `radar_api.post` → `radar.prepare(values, ROOT, end, mode)` | instancia `radar.RadarExtractor` por ticker: extrator original, ITUB4 bloqueado |
| `run_multiasset_radar.py prepare` | mesma chamada: original |
| `radar_corporate_events.py prepare` (V7.1) | `extractor=` compartilhado: normalizado, comportamento diferente da UI |

`multiasset_radar.py`, `radar_api.py` e `run_multiasset_radar.py` estão nos
baselines V5/V6/V7, e o teste V4 preservado afirma que, ao importar o servidor,
`radar.RadarExtractor.download` é o do extrator B3 original.

Estado da raiz oficial (inalterado): quatro inputs (PETR4, VALE3, WEGE3, BBAS3),
um evento PREPARED cada, nenhum claim, reserva ou journal; `last_prepare.json`
`2414ff96…` registra o bloqueio do ITUB4; cache COTAHIST 2026 `d55b48e4…`.

## 2. Integração

`radar_corporate_events.install()` religa `radar.RadarExtractor` para o
normalizador. É chamado em `server.main()` (só no processo real da UI, não no
import) e no CLI `prepare`, que em seguida executa **a mesma chamada** da thread
da API. Uma implementação, nenhuma condição por ticker, `extractor=` preservado.
`ORIGINAL` guarda o extrator selado para o diagnóstico. Limite documentado
(`ponytail:`): religa um global do módulo; o caminho de evolução é um parâmetro
`extractor` no `radar_api` quando ele for reselado.

## 3. Normalização (`RADAR_CORPORATE_EVENTS_V2`)

- Restaura o `Close` nominal do yfinance só para evento que a B3 confirma como
  **bonificação** na mesma sessão: ESPECI com marca ex contendo "B" (EB, EDB,
  EJB) **e** mudança de DISMES; razão > 1.
- Confere as duas sessões vizinhas a cada evento, depois a guarda anual original
  com a tolerância original (1e-3).
- Bloqueia: split sem DISMES, dividendo (EJ), razão ≤ 1 (grupamento), data
  divergente, fator incompatível, ajuste sem evento, evento sem barra B3.
- Vários eventos: processados do mais recente ao mais antigo (validado com dados
  reais do ITUB4: 1,10 em 18/03/2025 e 1,03 em 26/12/2025).
- Preços brutos (`raw_bar`), volume oficial e `Adj Close` não são alterados. O
  input registra tipo, data-ex, razão, `price_factor_before_ex_date`, ESPECI,
  DISMES, fechamentos B3 e hash do módulo em `source.corporate_events`.
- Sem evento: idêntico bit a bit ao extrator original (os quatro tickers sem evento).

## 4. Cinco ativos (sessão 09/10/2026)

Dados reais, 311 barras desde 16/07/2025, calendário B3 completo, 8 features,
manifesto Radar `77d75777…` (família compatível com o Global PM).

| Ticker | Raiz oficial hoje | Preparo V7.2 (raiz isolada, endpoint real) | Normalização | Vol. 21d / limite |
|---|---|---|---|---|
| PETR4 | input congelado | reutilizado byte a byte | não necessária | 0,392 / 0,50 |
| VALE3 | input congelado | reutilizado byte a byte | não necessária | 0,238 / 0,50 |
| ITUB4 | sem input (bloqueio de 11/10) | **congelado** | bonificação 26/12/2025 ×1,03, `PN EB N1`, DISMES 362→363 | 0,429 / 0,50 |
| WEGE3 | input congelado | reutilizado byte a byte | não necessária | 0,215 / 0,50 |
| BBAS3 | input congelado | reutilizado byte a byte | não necessária | **0,545 / 0,50: restrição** |

Raiz isolada após o preparo: **5 inputs prontos; 0/5 pareceres oficiais**;
preflight do lote com chave fictícia pronto para os cinco (reserva US$ 3,31776,
estimativa US$ 0,14625, orçamento 0/5); Global PM bloqueado
(`complete_radar_opinion_required`); nenhum claim ou reserva. Antes/depois: só
`last_prepare.json`, `job.json` e cache COTAHIST (OPERATIONAL) mudaram; três
arquivos novos do ITUB4 (NEW); nenhuma violação.

BBAS3: input íntegro ≠ parecer favorável. A UI e o diagnóstico mostram
"Restrição individual" e "Risk ainda não avaliado"; o teste com comitê fake
confirma veto `HARD_ASSET_VOLATILITY_RULE`, recomendação MANTER, parecer
completo e elegível para o Global PM com veredito VETADO. Limites inalterados.

## 5. `last_prepare.json`

Ponteiro/relatório da **última chamada** de `prepare`, sobrescrito a cada uma.
Não é índice nem referência por ticker. A visibilidade e a elegibilidade vêm dos
inputs congelados (`analyses/*/*/input.json`), portanto preparar um ativo não
oculta os demais. Nenhum índice novo foi necessário; a UI e o diagnóstico o
tratam como dica, não como autoridade.

## 6. Ciclo de vida

`scripts/check_preservation.py` (somente leitura por padrão) classifica cada
arquivo de baseline alterado em OPERATIONAL (com motivo), LEDGER (conferir com o
runner) ou VIOLATION (código 2). `--snapshot`/`--since` registram o antes/depois
de uma operação autorizada. Baselines históricos não foram editados; hoje:
0 alterações nos quatro (10.766 a 11.094 arquivos).

## 7. Testes

`tests/test_radar_corporate_events.py` (19, offline): bonificação ITUB4, outros
marcadores (EB/EDB/EJB), dois eventos, sete bloqueios (sem DISMES, dividendo,
grupamento, data, fator, sem evento, calendário), preços brutos, equivalência
CLI/API, quatro existentes + ITUB4, falha parcial, idempotência, ponteiro,
cache operacional, inputs imutáveis, preflight com cinco, BBAS3, pareceres
ausentes, bloqueio Global PM, CSRF/Origin, GET sem escrita, `server.main()`
instala, política de ciclo de vida. Mutações (regra de marca, `install()`,
ordem dos eventos) derrubam a suíte. Regressão relevante: **252 passed, 38 subtests**; Ruff e sintaxe JS limpos; baselines sem alteração.

## 8. Pendências para a primeira chamada Gemini real

1. Operador prepara o ITUB4 na raiz oficial (comando no runbook) ou prepara os
   cinco já para 13/10 após o fechamento.
2. `GEMINI_API_KEY` no ambiente do processo do servidor/CLI (Radar não lê `.env`).
3. Preflight do lote e autorização paga própria (teto US$ 3,31776; BBAS3 usa 5
   chamadas porque o Risk veta por regra, sem chamada de Risk).
4. Global PM só após todos os pareceres da mesma sessão, contexto perto do uso
   e autorização separada; execução multiativos continua indisponível.
