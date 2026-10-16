# H2-V6-FORWARD-PAPER — Forward Test prospectivo em paper trading

**Classificação:** avaliação prospectiva **exploratória**. Não é Validation, não é
Final Test, não é inferência confirmatória, não autoriza retuning e não envia
ordem real (não há código de corretora). Resultados daqui nunca alteram
parâmetros, prompts, manifesto, checkpoint ou artefatos selados da H2 v6.

Entrypoint: [`scripts/run_h2_v6_forward.py`](../scripts/run_h2_v6_forward.py).
Teste offline: [`tests/test_h2_v6_forward.py`](../tests/test_h2_v6_forward.py).

## Por que um entrypoint novo

`scripts/run_agent_daily.py`/`DailyAgentRunner` **não** é a H2 v6: usa o grafo
legado com 30 analistas, limiar 5/6, sizing próprio, `integer` e sem journal.
O forward reaproveita só o que é idêntico à Validation OA-1:

| Peça | Origem (inalterada) |
|---|---|
| Identidade | `verify_manifest` do manifesto candidato (hash de todo `src/`, ambiente, árvore limpa) + `PARTICIPANT_SHA256` |
| Participante | `build_with_client(spec)`: 5 Technical Analysts, consenso 0.6, Risk v2, Portfolio, prompt técnico v5, `gemini-3.8-flash`, T=1.0, thinking LOW |
| Journal | `CallBank` + `DurableGeminiClient` (reserva FULL antes do HTTP; bytes crus e registro antes da entrega; recuperação só por replay) |
| Execução | `ExecutionEngine._settle`, `fractional_notional`, custos-base 5 bps + 0,032%, capital R$ 100.000 |
| Dados | `B3OfficialAdjustedExtractor` (COTAHIST oficial × fator yfinance), histórico desde 2016-01-01 como o snapshot |
| Calendário | `B3Calendar` v2 |

Nada foi adicionado em `src/` (o manifesto inventaria todo `src/**/*.py`).

## Ciclo diário

```text
prepare    (grátis)  baixa dados e congela sessions/<S>/input.json + bars.csv
preflight  (offline) rede bloqueada; identidade, calendário, dados, reconciliação prevista, custo
run --confirm <12 hex de input.json>   reconcilia abertura/fechamento e decide S (pago)
```

S = última sessão cujo fechamento ocorreu (18:00 BRT). A decisão de S vale para a
abertura (10:00 BRT) da sessão seguinte T. No fechamento de T, o próximo `run`
liquida o pendente ao preço de abertura de T, marca o patrimônio no fechamento e
decide T.

## Causalidade

- `bars.csv` termina exatamente em S e coincide sessão a sessão com o calendário
  B3 desde o início; barra futura ou faltante recusa o `prepare`.
- A barra de S vem do COTAHIST oficial, publicado só após o pregão; a barra bruta
  oficial é registrada ao lado da ajustada.
- O LLM recebe só features adimensionais de `bars.loc[:S]` (sem data, ticker ou
  nível de preço no prompt), como na Validation.
- `run` é recusado a partir da abertura-alvo; uma decisão concluída depois dela
  vira `LATE_NOT_EXECUTABLE` (sem ordem).
- O gate antes de cada HTTP reconfere manifesto e `input.json`.
- Decisões só para S > 2026-08-31 (depois de toda janela reservada). O snapshot
  reservado não é lido.

## Uma inferência por sessão

`decision.json` é write-once e o preflight o exige ausente; lock exclusivo
`state.json.lock`; `provider.sqlite` por sessão: se já houve reserva, o cliente
só faz replay e nunca chama o provedor de novo (chamada incerta falha fechada).

## Persistência (`data/forward/h2_v6_paper/`, fora do git)

```text
state.json                      carteira, pico, pendente, curva, B&H sombra, decisões (troca atômica)
sessions/<S>/input.json         write-once: sessão, alvo, prazo, fetched_at, fechamento, barras bruta/ajustada, hashes COTAHIST
sessions/<S>/bars.csv           write-once: OHLCV exato usado (2016-01-04..S)
sessions/<S>/provider.sqlite    CallBank: reservas, tentativas, envelopes crus, registros
sessions/<S>/provider_journal.jsonl  export do CallBank
sessions/<S>/llm_trace.jsonl    trace canônico do participante
sessions/<S>/decision.json      write-once: votos, consenso, Risk, Portfolio, intents, carteira no fechamento, generated_at, hashes
sessions/<S>/reconciliation.json write-once: execuções na abertura e marcações das sessões novas
```

## Diferenças declaradas em relação a uma fase científica

- Falha de provedor não aborta o mundo real: a sessão fica `FAILED`, sem ordem
  (posição mantida), e é reportada à parte. Na Validation ela abortaria o run.
- Sessão sem `run` antes da abertura seguinte fica `MISSED` (posição mantida).
- Proventos reescalam a série de retorno total; o ledger preserva o valor marcado
  no último fechamento (`units *= close_antigo / close_novo`).
- Calendário verificado contra o COTAHIST até 2026-08-31; depois disso vale a
  regra, conferida a cada `prepare` contra as barras oficiais.
- B&H sombra compra na primeira abertura após a primeira decisão, com os mesmos custos.

## Custo estimado (preço/médias do runner OA-1)

Por sessão: ~5,2 chamadas lógicas, ~US$ 0,008 esperado, orçamento prudente
US$ 0,02, teto teórico US$ 1,32 (7 chamadas × 6 tentativas × 8192 tokens de
saída). ~US$ 0,17 por 21 pregões. Preço introdutório do Gemini 3.8 Flash até
2026-12-31; reconfirmar no billing.
