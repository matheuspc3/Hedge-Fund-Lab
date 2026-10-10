# H2 v6 — Síntese científica da Validation provisória OA-1

> **VALIDATION OA-1 — NÃO RATIFICADA ACADEMICAMENTE.** Execução autorizada somente pelo
> autor (`AUTHOR_PROVISIONAL_OPERATIONAL — NOT ACADEMICALLY RATIFIED`). Os resultados abaixo
> são **descritivos e exploratórios**: a Validation não é teste confirmatório, nenhuma
> inferência estatística foi realizada sobre ela e nada aqui seleciona estratégia, ajusta
> parâmetros ou autoriza o Final Test, que permanece bloqueado.

| Item | Valor |
|---|---|
| Data | 2026-10-09 (America/Sao_Paulo), branch `#1-Update` |
| Plano / manifesto candidato | `2808fe83f2a4…` / `dc118ce9…` (estado `CANDIDATE / NOT APPROVED / NOT FROZEN`) |
| Checkpoint selado | `docs/evidence/h2_v6_provisional/VALIDATION_PROVISIONAL_CHECKPOINT.json` (commit `bb9d202`) |
| Fonte dos números | `data/runs/h2_v6_provisional/VALIDATION` (`summary.json`, `cost_closure.json`, artifacts dos runs) |
| Análise detalhada | [H2_V6_OA1_VALIDATION_DIAGNOSTIC.md](H2_V6_OA1_VALIDATION_DIAGNOSTIC.md) e seu script de asserts |
| Visualização | dashboard `/h2`, abas Decisões, Comparações e Multiagente ([runbook](H2_V6_VALIDATION_PROVISIONAL_RUNBOOK.md#análise-pós-validation)) |

Legenda: **[F]** fato verificado nos artifacts selados; **[H]** hipótese interpretativa, não
demonstrada; **[L]** limitação ou ameaça à validade.

## 1. Objetivo e metodologia

A hipótese H2 investiga se uma arquitetura multiagente baseada em LLM (cinco Technical
Analysts, um Risk Manager e um Portfolio Manager) produz, em PETR4.SA, Sharpe superior ao
do Buy & Hold. O estimando registrado é
`Δ = média(Sharpe L01, L02, L03) − Sharpe(B&H)`, com `H0₂: Δ ≤ 0` e `HA₂: Δ > 0`,
condicionado às trajetórias observadas. O teste confirmatório (Bootstrap A, B = 5000,
α = 0,05) está reservado ao Final Test.

A metodologia separa a Validation (janela de desenvolvimento final, uso descritivo) do
Final Test (janela reservada, uso confirmatório). Esta síntese só reorganiza resultados já
selados: nenhuma chamada ao provedor, reexecução, replay ou leitura do snapshot (que
contém o período do Final Test) foi feita para produzi-la.

## 2. Configuração do experimento e protocolo de Validation

- **Tratamento H2 v6** (ParticipantSpec `7858beb4…`): modelo `gemini-3.8-flash`,
  temperatura 1,0, *thinking* `low`; 5 analistas com consenso ≥ 3/5 (limiar 0,6); sizing
  binário 0% / 100% (`long_target_weight = 1,0`). Risk: veto de COMPRA se volatilidade
  recente > 0,50, drawdown > 0,25 ou concentração ≥ 1,0; VENDA e MANTER são
  auto-aprovadas.
- **Execução:** decisão no fechamento de *t*, ordem na abertura de *t+1*; preços ajustados
  (*total return*); custo de 5 bps de spread + 0,032% sobre o nocional; capital inicial
  R$ 100.000.
- **Janela:** decisões de 2024-09-02 a 2025-08-28 (247 sessões), settlement em 2025-08-29.
- **Repetições:** R = 3 runs operacionalmente independentes (L01, L02, L03), executados em
  sequência (ver §5 para o que essa independência significa e o que não demonstra).
- **Benchmarks determinísticos:** Buy & Hold, SMA Regime 50/200 e Bollinger Estado 20/2.
- **Sensibilidade de custos:** grade 0, 5, 10 e 20 bps, por replay exato das respostas
  gravadas.
- **Protocolo OA-1:** rota operacional separada, autorizada somente pelo autor
  ([H2_V6_OPERATIONAL_AMENDMENT_OA1.md](H2_V6_OPERATIONAL_AMENDMENT_OA1.md); autorização
  em `1a0852f`). Preserva tratamento, parâmetros, custos, janela e R; não substitui
  aprovação do coautor, do orientador nem System Freeze, e não alcança o Final Test.

## 3. Resultados financeiros observados

Spread de 5 bps (baseline). Fonte: `summary.json`, idêntico bit a bit ao recálculo a
partir de `equity.csv` e `trades.csv` (diagnóstico §9).

| Participante | Retorno líquido | Retorno anualizado | Volatilidade | Sharpe | Sortino | MDD | Turnover | Ordens | Custos (R$) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H2 L01 | −24,02% | −24,44% | 16,32% | −1,634 | −2,024 | −25,36% | 10,56× | 12 | 866,29 |
| H2 L02 | −26,56% | −27,02% | 15,98% | −1,889 | −2,292 | −26,93% | 12,28× | 14 | 1.007,25 |
| H2 L03 | −26,56% | −27,02% | 15,98% | −1,889 | −2,292 | −26,93% | 12,28× | 14 | 1.007,25 |
| Buy & Hold | −6,64% | −6,77% | 22,91% | −0,191 | −0,255 | −21,06% | 1,00× | 1 | 81,93 |
| SMA Regime 50/200 | −13,42% | −13,67% | 18,39% | −0,707 | −0,924 | −19,48% | 1,87× | 2 | 152,99 |
| Bollinger Estado 20/2 | +13,79% | +14,09% | 16,37% | +0,887 | +1,256 | −19,32% | 7,26× | 7 | 595,59 |

- **[F]** Sharpe médio da H2: −1,804 (desvio-padrão entre runs 0,147). ΔSharpe individual
  frente ao B&H: −1,443, −1,698 e −1,698. **ΔSharpe médio: −1,613.** O bloco `statistics`
  registra `inference = DESCRIPTIVE_ONLY` e `confirmatory_contrasts = 0`.
- **[F]** Os três runs terminaram abaixo do capital inicial e em caixa desde 2025-08-11.

## 4. Comparação com benchmarks

- **[F]** Na janela, a H2 ficou abaixo dos três benchmarks em retorno e em Sharpe. A
  ordenação observada por Sharpe é Bollinger > B&H > SMA Regime > H2.
- **[F]** O ativo caiu −5,94% de fechamento a fechamento (30,1357 → 28,3469), com amplitude
  de 26,7% entre máxima e mínima e volatilidade anualizada de 22,9%.
- **[F] Sensibilidade de custos.** Benchmarks (determinísticos), retorno líquido em
  0 / 5 / 10 / 20 bps: B&H −6,60% / −6,64% / −6,69% / −6,78%; SMA Regime −13,33% /
  −13,42% / −13,51% / −13,68%; Bollinger +14,19% / +13,79% / +13,40% / +12,61%. Para a H2,
  os nove cenários fora de 5 bps estão selados como
  **`N/A — EXACT_REPLAY_INVALID`** (`COST_SENSITIVITY_NOT_ESTIMABLE`). Esses valores não
  foram interpolados, estimados nem substituídos.
- **[F] Causa estrutural dos N/A.** O replay diverge na chamada #67 (Portfolio Manager,
  2024-09-18), a primeira cujo prompt embute uma métrica dependente do patrimônio após
  custos (`current_drawdown`). Com outro spread o prompt muda e a identidade da requisição
  deixa de casar com a gravada. A reconstrução offline dos três SHA-256 confirma o
  mecanismo (diagnóstico §8).

## 5. Análise do comportamento dos agentes

O dashboard separa três conceitos: a camada **foi chamada**, **produziu uma decisão** e
**alterou a trajetória financeira**, ou seja, a ordem executada difere da que o consenso
técnico sozinho implicaria dada a posição em *t*.

| Camada | Chamada (L01 / L02 / L03) | Produziu decisão | Alterou a trajetória |
|---|---|---|---|
| Technical Analysts | 1.235 chamadas em cada run (5 × 247) | 247 consensos; 0 sessões sem maioria | 12 / 14 / 14 sessões originaram ordem |
| Risk Manager | 247 avaliações por regra; Risk LLM 6 / 7 / 7 | 171 / 169 / 171 aprovações; 76 / 78 / 76 vetos | **0 vetos efetivos** |
| Portfolio Manager | 80 / 78 / 80 chamadas | 80 / 78 / 80 decisões (COMPRA ou VENDA) | **0 decisões diferentes do consenso** |
| Execução | — | 12 / 14 / 14 ordens | 0 ordens diferentes da implicada pelo consenso |

- **[F]** Todos os vetos foram da regra `CONCENTRATION` sobre COMPRA com a carteira já em
  100% (`BUY_AT_TARGET_NOOP`): sem o veto também não haveria ordem. As regras de drawdown e
  de volatilidade nunca dispararam. O Risk LLM aprovou todas as compras.
- **[F]** O PM seguiu o consenso técnico em 100% das chamadas. **Nesta janela, Risk e
  Portfolio não tiveram contribuição incremental observada:** foram chamados e produziram
  decisões, mas nenhuma alterou a ordem executada, e a trajetória financeira foi função do
  consenso técnico e do sizing 0% / 100%. A constatação vale para a Validation analisada;
  não mostra que essas camadas sejam inócuas em outros regimes (§7).
- **[F]** Toda compra foi decidida com fechamento acima da SMA50 e toda venda com
  fechamento abaixo dela; as evidências mais citadas pelos analistas foram
  `CLOSE_ABOVE_SMA50` / `CLOSE_BELOW_SMA50`, seguidas dos sinais de MACD.
- **[F] Independência operacional das chamadas.** As perguntas técnicas são idênticas por
  construção (mesmo `identity_digest`), mas cada run fez suas próprias chamadas ao
  provedor: 3.963 `provider_response_id` distintos, nenhum envelope HTTP repetido entre runs
  e janelas de execução sem sobreposição. Não houve reutilização de respostas entre runs. A
  concordância de votos é semelhante entre todos os pares (L01×L02 93,4%; L01×L03 92,6%;
  L02×L03 93,5%).
- **[L]** "Independência" aqui é operacional: chamadas distintas, sem cache nem reuso. A
  independência estatística das respostas (por exemplo, ausência de correlação induzida
  pelo mesmo prompt e pelo mesmo modelo) não foi testada e não é afirmada.
- **[F] Trajetórias idênticas com respostas diferentes.** L02 e L03 têm `equity.csv` e
  `trades.csv` idênticos byte a byte, embora os votos difiram em 37 sessões e o resultado
  técnico em 10. Nenhuma dessas 10 sessões podia mudar a posição: foram VENDA × MANTER com
  a carteira em caixa ou COMPRA × MANTER com a carteira já comprada. L01 diverge de
  L02/L03 em só duas sessões consecutivas de maioria mínima (2025-02-13 e 2025-02-14).

## 6. Explicação observacional do desempenho

- **[F] A diferença para o B&H vem do calendário de exposição, não do retorno nos dias
  investidos.** A H2 ficou comprada no fechamento de 141 (L01) e 140 (L02/L03) das 247
  sessões. A tabela decompõe exatamente a diferença em log-retorno,
  `Σ_t [ln(1 + r_H2) − ln(1 + r_B&H)] = ln(P_H2(T) / P_B&H(T))`, classificando cada um dos
  247 retornos diários pelo estado da H2 no dia (diagnóstico §7, recalculado a partir de
  `equity.csv` e `trades.csv`):

  | Estado do dia | L01: Δ log (dias; ativo em log) | L02 = L03: Δ log (dias; ativo em log) |
  |---|---:|---:|
  | Comprada o dia inteiro | 0,0000 (135; −0,2711) | 0,0000 (133; −0,3076) |
  | Em caixa o dia inteiro | **−0,2522** (100; +0,2522) | **−0,2522** (100; +0,2522) |
  | Entrada na abertura | +0,0035 (6) | −0,0027 (7) |
  | Saída na abertura | +0,0428 (6) | +0,0149 (7) |
  | **Total = ln(P_H2 / P_B&H)** | **−0,2059** (razão 0,8139) | **−0,2400** (razão 0,7867) |

  - Nos dias comprados o dia inteiro, a contribuição é nula: a H2 estava 100% investida,
    como o B&H.
  - **Os dias em caixa são a principal contribuição negativa** (−0,2522 nos três runs): são
    os 100 pregões em que o ativo subiu +28,7% e a H2 não participou.
  - **Os dias de entrada e saída também entram na diferença final**, mas nesta janela
    compensaram parte dela: +0,0463 em L01 e +0,0122 em L02/L03. No dia de entrada a H2 perde
    o gap entre o fechamento anterior e a abertura; no dia de saída deixa de capturar o
    movimento da abertura ao fechamento. Os dois efeitos incluem o custo da ordem. Em
    L02/L03 as entradas somaram −0,0027, e a saída de 2025-02-14 sozinha contribuiu −0,0279,
    num dia de alta de 3,08%.
  - A diferença de −0,034 em log entre L01 e L02/L03 vem só desses dias de troca, ligados ao
    episódio de venda e recompra de 2025-02-14 / 2025-02-17.
- **[F] Timing desfavorável de entrada e saída.** L01 fez 6 ciclos e L02/L03 fizeram 7,
  com **um único ciclo lucrativo** em cada. Todas as recompras saíram acima do preço da
  venda anterior (+1,2% a +5,4%), e o ativo subiu em todos os períodos com pregões inteiros
  em caixa. Os custos somaram R$ 866 e R$ 1.007, menos de 1,1% do capital.
- **[F] Contraste com o Bollinger.** As exposições foram quase complementares: em 127
  pregões a H2 esteve comprada e o Bollinger em caixa (ativo −23,0%); o Bollinger comprou
  nas mesmas aberturas em que a H2 vendeu (2025-03-06 e 2025-08-11).
- **[F] Drawdown.** O MDD acima de 25% veio de uma queda de −6,15% num único pregão
  (2025-08-08) com 100% de exposição. `risk_max_drawdown = 0,25` é um limite de veto de
  COMPRA, não um stop; não houve violação de contrato (diagnóstico §6).
- **[H]** Num regime de oscilação em faixa como o da janela, regras de entrada condicionadas
  a "fechamento acima da SMA50 e MACD acima do sinal" tendem a comprar depois da alta e
  vender depois da queda. Os fatos acima são consistentes com essa leitura, mas ela não foi
  demonstrada causalmente: há um só ativo, uma só janela e nenhum teste de regime.

## 7. Limitações e ameaças à validade

- **[L] Natureza provisória.** OA-1 não é aprovação acadêmica. A janela de Validation
  ficou conhecida antes da ratificação; se coautor ou orientador exigirem mudança de
  tratamento, ela estará contaminada para o protocolo modificado (OA-1 §4.1).
- **[L] Sem inferência.** R = 3 e, como L02 = L03, apenas duas trajetórias financeiras
  distintas. Toda dispersão é descritiva; **a H2 não foi rejeitada estatisticamente**, e a
  Validation não deve ser lida como teste confirmatório.
- **[L] Validade externa.** Um ativo, uma janela de 247 sessões e um regime de mercado.
- **[L] Cobertura das camadas.** As regras de drawdown e volatilidade não foram
  exercitadas; a ausência de efeito de Risk e PM vale para esta janela, não para outros
  regimes.
- **[L] Sensibilidade de custos parcialmente não estimável** para a H2 sob replay exato.
- **[L] Explicabilidade.** O "porquê" de cada voto vem dos códigos de evidência e da
  justificativa estruturada registrados; o raciocínio interno do modelo não está nos
  artifacts.
- **[L] Preços na visualização.** Os fechamentos vêm da curva selada do B&H e as aberturas
  só dos dias com execução; o fechamento de 2024-09-02 não é recuperável. As SMA exibidas
  são reconstruídas dos *gaps* enviados aos analistas (6 casas decimais).
- **[L] Análise post-hoc.** Esta síntese e o diagnóstico foram feitos depois de observados
  os resultados; qualquer mudança de tratamento motivada por eles seria seleção sobre a
  Validation.
- **Discrepância de rótulo em `summary.json`.** O arquivo traz
  `amendment_status = "H2_V6 EVALUATION AMENDMENT PROPOSED — AWAITING AUTHOR APPROVAL"` ao
  lado de `amendment_id = "H2-V6-OA1"`. O valor é a constante herdada do *evaluation
  amendment* do candidato (`src/experiments/h2_evaluation.py`, `AMENDMENT_STATUS`), que a
  rota OA-1 não sobrescreve; a autorização de OA-1 está commitada em `1a0852f`. O arquivo
  é selado e **não foi alterado**; a leitura correta é a do campo `mode`
  (`AUTHOR_PROVISIONAL_OPERATIONAL — NOT ACADEMICALLY RATIFIED`).

## 8. Implicações para o TCC e próximos passos

- Para o TCC, a Validation OA-1 documenta, de forma rastreável, um caso em que a
  arquitetura multiagente operou sem falhas de integridade (journal, selos e hashes
  conferem) e ficou abaixo do B&H por timing de exposição, sem contribuição incremental
  observada de Risk e Portfolio nesta janela. É um resultado descritivo e provisório,
  apresentável como tal.
- O resultado não autoriza retuning: alterar limiares, sizing ou prompts com base nesta
  janela invalidaria o uso dela como Validation.
- Próximos passos dependem de decisão humana fora deste documento: manifestação do
  coautor e do orientador sobre OA-1 e sobre o candidato, eventual System Freeze e, só
  então, a autorização própria do Final Test, onde o teste confirmatório registrado será
  aplicado.
- Questões em aberto, para discussão e não para execução nesta janela: o papel de Risk e
  PM sob regimes que exercitem as regras de drawdown e volatilidade; e como estimar a
  sensibilidade a custos quando os prompts dependem do patrimônio.
