# H2 v6 — Deliberação sobre o Amendment de Avaliação

**Estado: proposta de aprovação; confirmação formal pendente.**

Registro da deliberação recebida nesta conversa, na branch `#1-Update`.
Não é assinatura, aprovação formal, System Freeze ou autorização de execução.
Nenhuma assinatura ou concordância de terceiro foi presumida.

Documento-base preservado:
[H2_V6_EVALUATION_AMENDMENT_PROPOSAL.md](H2_V6_EVALUATION_AMENDMENT_PROPOSAL.md),
commit `00aa8ec`.
SHA256 dos bytes observados do documento-base:
`23d6f9464ffbcbbdacc44ecd0d59f39b2cdaa3d5e8b5b873faf73f0653607244`.

## 1. Decisões selecionadas, sujeitas à confirmação formal

| Item | Deliberação recebida |
|---|---|
| SF-B1 | H0₂: ΔSharpe ≤ 0; HA₂: ΔSharpe > 0. B&H primário; um contraste confirmatório no Final Test, condicionado às trajetórias LLM observadas. H1 multiativo preservada. |
| SF-B2 | Exatamente três runs LLM por fase, chamadas científicas independentes entre runs, mesma identidade do tratamento v6, dados, parâmetros e custos. Não selecionar ou substituir run por desempenho. |
| SF-B3 | Média aritmética dos três Sharpes individuais; publicação integral dos runs e dos resumos definidos no documento-base. |
| SF-B4 | **Candidato A selecionado na deliberação:** stationary bootstrap temporal pareado, basic centrado, B=5000, α=0.05, seed estatística=20261008, bloco médio=10. Aceitar e declarar suas limitações. A alternativa B não foi selecionada. |
| SF-B5 | Buy & Hold primário, SMA Regime 50/200 e Bollinger Estado 20/2 secundários, conforme os contratos exatos da proposta, inclusive inicialização, igualdade, bandas colapsadas e settlement. |
| SF-B6 | Sortino com MAR diário zero/rf anual zero, flags e valor econômico ausente nas degenerações; turnover pelo nocional absoluto efetivamente executado/capital inicial. |

As fórmulas, rank 4751, empates, correção +1, guards de degeneração, specs
candidatas e hashes continuam os do documento-base. Selecionar A nesta
deliberação não altera seu status para APPROVED ou FROZEN.

## 2. Confirmações humanas pendentes

| Responsável | Estado recebido | Assinatura/concordância registrada |
|---|---|---|
| Autor | Aprovação pendente de assinatura | Nenhuma |
| Coautor | Aprovação pendente de assinatura | Nenhuma |
| Orientador | Ciência e concordância pendentes de registro | Nenhuma |

Não preencher nomes de signatários, datas de aprovação ou manifestações em nome
dessas pessoas. A assinatura anterior da revisão CAL-B4 tem outro objeto e
não aprova este amendment. Um commit deste registro também não é assinatura
humana do amendment. A confirmação futura deverá identificar o documento e
a política de custos abaixo; ela permanece proposta para confirmação.

## 3. Formalização proposta: sensibilidade de custos e replay inválido

Escopo exclusivamente descritivo, por fase, com spread_bps em `{0,5,10,20}`,
brokerage_fixed=0 e tax_rate=0.00032. Capital inicial R$100.000 e execução
fracionária preservados. O cenário primário continua 5 bps; nunca selecionar
custo, tratamento ou parâmetro pelo resultado dessa análise.

A sensibilidade não autoriza novas inferências Gemini. A alteração de custos
pode mudar caixa, quantidade, patrimônio, pico de patrimônio, drawdown e
requisições posteriores de Risk/Portfolio. Portanto, conservar os prompts
fixos não basta para validar replay completo. O fluxo existente em
`src/agents/participant.py` usa o patrimônio realizado no estado de risco;
`ReplayLLMClient`, em `src/agents/llm_trace.py`, confere a identidade dos
requests e a completude do trace.

Contrato proposto para implementação e qualificação offline:

1. **Baseline 5 bps:** reutilizar os artifacts íntegros de cada run primário;
   não criar uma nova realização LLM nem duplicar artificialmente replicações.
2. **Demais cenários LLM:** executar o motor sob os custos do cenário somente
   com replay exato do trace daquele run, sem transporte de rede ou fallback
   live. Recalcular causalmente estado, quantidades e custos pelo motor; não
   forçar as ordens/quantidades da trajetória original.
3. **Replay completo válido:** todas as identidades científicas requisitadas
   devem corresponder ao trace, com provider/model, opções, prompts, schema,
   papel/analista/sessão; nenhum registro pode faltar ou sobrar. Motor,
   snapshot, calendário, tratamento, limites e settlement devem corresponder
   aos contratos. Publicar como contrafactual condicional ao replay das
   respostas observadas, sem afirmar que são novas realizações do provedor.
4. **Replay inválido:** na primeira divergência, falta, sobra ou falha de
   integridade, interromper esse cenário e registrar
   `COST_SENSITIVITY_NOT_ESTIMABLE — EXACT_REPLAY_INVALID`, com motivo,
   run/cenário e primeira identidade afetada. Retornos, equity final, Sharpe,
   Sortino, drawdown e demais métricas completas desse cenário ficam ausentes
   (`null`/N/A), nunca zero. Evidência de diagnóstico parcial não é resultado
   financeiro completo e não entra em ranking ou agregação.
5. **Sem substituição:** não ignorar diferenças de estado/request, enfraquecer
   matcher, corrigir respostas, fazer nova chamada, rerun orientado por resultado
   ou substituir o cenário por contabilidade de custos com trades fixados.
   Essa última análise responde a outra pergunta e não é fallback autorizado
   por esta proposta.
6. **Agregação dos três runs:** calcular resumo LLM de um cenário somente se
   os três replays forem completos e válidos. Se qualquer um for inválido,
   resumo daquele cenário = N/A, publicando as disposições individuais sem
   selecionar o subconjunto válido. Não alterar a agregação primária 5 bps.
7. **Benchmarks determinísticos:** podem ter execuções completas por cenário
   com o mesmo snapshot, indicadores e regras, sem LLM; preservar instâncias
   novas, custos e limites. Não copiar métricas entre cenários. Falha de
   integridade também produz ausência de resultado completo.
8. **Completude científica:** todas as combinações pré-declaradas devem ter
   uma disposição registrada, completa ou não estimável com motivo. Replay
   inválido de cenário descritivo não invalida por si só um run primário íntegro
   e não vira gate de desempenho para o Final. Uma falha que também comprometa
   a identidade/integridade do baseline impede release.

Esta política não foi aplicada a dados reais. Não houve cálculo de outcomes
CAL-B4, Validation ou Final. O fallback não estimável e sua publicação exigem
testes sintéticos antes de qualificação da camada definitiva.

## 4. Condições para a próxima etapa

- Preservar integralmente tratamento v6, prompts, schemas, vocabulary,
  validator, checker, Risk/Portfolio, parâmetros e evidências históricas.
- Validation permanece descritiva, sem seleção de parâmetros ou contraste
  confirmatório adicional. Final continua separado e único confirmatório.
- Release Validation → Final depende apenas de integridade, completude e
  identidade congelada; Sharpe, p-valor, superioridade e sinal do retorno não
  fundamentam esse release.
- Concluir e testar a camada de avaliação antes de um System Freeze definitivo:
  adapters identificados, agregação/pareamento, candidato A, métricas/flags,
  política de custos acima, três identidades de run, completude, phase boundaries
  e guard de release. O self-check sintético anterior não equivale à integração
  ou qualificação completa dessa camada.
- Não declarar System Freeze definitivo antes das confirmações formais e da
  qualificação. Não executar Validation/Final antes de autorização específica.
  As autorizações de development/CAL-B4 não se estendem a essas fases.

## 5. Situação registrada nesta tarefa

Novo artifact documental de deliberação. O documento-base e o protótipo
permanecem preservados; nenhuma camada produtiva foi alterada neste registro.
Não declarar `EVALUATION COMPLETE`, `APPROVED`, `FROZEN` ou `READY FOR VALIDATION`.

CAL-B4: `CAL_B4_PASS — SANITY CHECK ONLY`, one-shot consumida.
`SYSTEM_CALIBRATION_COMPLETE=True`; tratamento final=6. Validation e Final Test
permanecem NOT EXECUTED; System Freeze não executado. Zero chamadas externas
nesta tarefa.

Estado mantido:
`H2_V6 EVALUATION AMENDMENT PROPOSED — AWAITING AUTHOR APPROVAL`.

Próxima etapa: obter as confirmações formais sem presumir assinaturas e
qualificar a camada de avaliação correspondente às escolhas confirmadas, antes
de retomar o System Freeze. Esta deliberação não é autorização live.
