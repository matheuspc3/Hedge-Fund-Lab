# Desenho fora da amostra (campanhas C3 retrospectiva e C4 prospectiva)

Nada aqui foi executado. As sessões abaixo saem de uma regra determinística
sobre o calendário; **nenhum preço ou retorno foi consultado para escolhê-las**.

## 1. Amostra de desenvolvimento (excluída)

| Item | Sessão | Motivo |
|---|---|---|
| Radar recovery-01, Global PM V1 e V2 | 09/10/2026 | o contrato V2 foi desenhado depois de observar a falha da V1 nesta sessão |

## 2. Janelas proibidas

| Janela | Período | Motivo |
|---|---|---|
| H2 VALIDATION | 02/09/2024 – 29/08/2025 | isolamento do H2 v6 |
| H2 FINAL_TEST | 01/09/2025 – 31/08/2026 | holdout bloqueado do H2 (PETR4 está no universo multiativo). Rodar agentes sobre essas sessões exporia o pesquisador ao comportamento do sistema no holdout e comprometeria a cegueira do Final Test |

As janelas são lidas de `src/experiments/h2_evaluation.PHASE_WINDOWS`. O
validador do protocolo rejeita qualquer sessão dentro delas
(`session_in_h2_window`).

## 3. C3 — retrospectiva fora da amostra de desenvolvimento

| Item | Definição |
|---|---|
| Período de referência | 01/09/2026 – 08/10/2026 (depois da janela H2 e antes da sessão de desenvolvimento) |
| Sessões elegíveis | 27, pelo calendário B3 do projeto (`B3Calendar`), menos a sessão de desenvolvimento |
| Seleção | permutação uniforme semeada (`random.Random(7606)`) das 27; as **10 primeiras** formam a amostra; as seguintes, na ordem, são as substituições pré-registradas |
| Amostra | 01/09, 04/09, 10/09, 11/09, 14/09, 17/09, 29/09, 05/10, 06/10, 07/10 (2026) |
| Ordem de substituição | 15/09, 08/09, 18/09, 25/09, 08/10, 21/09, 24/09, 09/09, 22/09, 03/09, 01/10, 02/09, 28/09, 16/09, 02/10, 30/09, 23/09 |
| Entradas permitidas na seleção | `b3_calendar`, `cotahist_session_presence`, `seed`; qualquer entrada com "future", "forward", "return", "post_session", "next_" é recusada (`forbidden_selection_input`) |
| Universo | PETR4, VALE3, ITUB4, WEGE3, BBAS3 (fixo) |
| Dados | COTAHIST oficial da B3 (`TPMERC 010`, `CODBDI 02`) + fator de ajuste, pelo preparo normalizado do Radar (`radar_runs.py prepare`) |
| Integridade | cada sessão precisa existir no COTAHIST para os 5 ativos; o calendário do projeto só está auditado contra o COTAHIST até 31/08/2026, então **a presença das 10 sessões deve ser conferida antes do uso** (bloqueio `COTAHIST_SESSION_VERIFICATION`) |
| Janela de indicadores | a do tratamento Radar V1 (SMA50/200, MACD, RSI, Bollinger, volatilidade de 21 sessões, risco com 60 retornos); cada input exige histórico suficiente, ou o preparo bloqueia |
| Ajustes corporativos | `RADAR_CORPORATE_EVENTS_V2`; evento não resolvido → input `BLOCKED` → sessão excluída e substituída pela próxima da ordem |
| Calendário oficial | `B3Calendar` + conferência no COTAHIST |
| Informação no instante da decisão | só dados até o fechamento da sessão t (`decision_information_cutoff = SESSION_CLOSE`) |
| Abertura e encerramento hipotéticos | se houver avaliação financeira: execução hipotética na abertura oficial de t+1, conforme [PAPER_TRADING_PROTOCOL.md](PAPER_TRADING_PROTOCOL.md) |
| Custos | política didática congelada (`fee_rate` 0,1%) |
| Horizonte | 5 sessões após cada decisão (descritivo; cada decisão começa de carteira S0) |
| Benchmarks | [BASELINES_AND_CONTROLS.md](BASELINES_AND_CONTROLS.md), mesmas sessões, custos e regras |
| Exclusões | sessão ausente no COTAHIST; input `BLOCKED`; comitês incompletos (< 5 pareceres) impedem o Global PM oficial (origem não `VERIFIED`) |
| Substituição | só mecânica, pela ordem acima, e só por exclusão de dados; nunca depois de ver resultados do modelo |
| Interrupção | integridade falhou; mudança de `modelVersion`; orçamento esgotado; desvio de protocolo |
| Chamadas e reserva | 50 comitês (≤ 300 chamadas) + 10 Global PM; reserva US$ 34,77504 |

**Natureza:** C3 é **retrospectiva**. Os preços dessas sessões já eram
conhecidos quando o protocolo foi escrito. É "fora da amostra de
desenvolvimento", não "prospectiva". Ameaças específicas: o pesquisador conhece
o comportamento do mercado no período, e o modelo pode ter visto informações
públicas sobre esses dias. A seleção às cegas por semente reduz o viés de
escolha, mas não cria independência temporal: sessões vizinhas são
correlacionadas.

## 4. C4 — prospectiva

Só é prospectiva uma decisão registrada e congelada **antes** dos preços que a
avaliam. Antes da primeira decisão, congelam-se em versão nova do protocolo
(estado `FROZEN_FOR_FUTURE_EVALUATION`):

| Item congelado | Valor proposto |
|---|---|
| Universo | os 5 ativos |
| Tratamentos | `HFL-MULTIASSET-GLOBAL-PM-V2` (contratos `159fd196…`) e `HFL-MULTIASSET-RADAR-V1` (manifesto `77d75777…`) |
| Frequência | uma decisão por sessão B3, após o fechamento e antes da abertura seguinte |
| Número de decisões | 20 sessões consecutivas a partir da primeira sessão após o congelamento |
| Regras de entrada e acompanhamento | [PAPER_TRADING_PROTOCOL.md](PAPER_TRADING_PROTOCOL.md) |
| Métricas | dimensão E do [METRIC_CATALOG.json](METRIC_CATALOG.json), com taxa livre de risco escolhida antes |
| Benchmarks | [BASELINES_AND_CONTROLS.md](BASELINES_AND_CONTROLS.md) |
| Orçamento | 100 comitês + 20 Global PM; reserva US$ 69,55008; teto autorizado por humano antes |
| Falhas | sessão sem decisão válida → carteira mantida (sem operação) e falha registrada; nunca reexecutar depois de ver a abertura |

Prova de anterioridade: `result.json` (`completed_at`) e claim selados antes da
abertura de t+1, mais um hash publicado no histórico Git local antes da
abertura. O validador recusa o rótulo `PROSPECTIVE` para sessões já
conhecidas (`prospective_label_on_known_session`).

## 5. Dependências antes de C3/C4

1. Revisão humana e congelamento do pré-registro.
2. Conferência das sessões no COTAHIST.
3. Autorização humana de orçamento Radar (exposição agregada já acima do teto
   local).
4. Para C4: ledger paper multiativo separado (não existe).
