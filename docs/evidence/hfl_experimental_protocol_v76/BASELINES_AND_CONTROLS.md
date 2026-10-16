# Baselines e controles

Planejados para as campanhas C3 (descritiva) e C4 (prospectiva). Nenhum foi
calculado: não há ledger paper nem dados posteriores congelados.

## 1. Princípio

Todos os métodos recebem **o mesmo universo, as mesmas sessões, os mesmos
preços, os mesmos custos, o mesmo horizonte, as mesmas regras de execução paper
e a mesma informação disponível no instante da decisão** (dados até o
fechamento de t). Quando um controle usa menos informação que o Global PM
(por exemplo, ignora os pareceres), isso é declarado como parte do tratamento,
e não como vantagem escondida.

## 2. Controles

| Id | Controle | Informação usada | Regra | Pergunta que ajuda a responder |
|---|---|---|---|---|
| `ALWAYS_CASH` | Sempre em caixa | nenhuma | 100% caixa em todas as sessões | o Global PM faz algo além de não operar? Linha de base do custo de oportunidade |
| `EQUAL_WEIGHT_ELIGIBLE` | Igualmente ponderada nos elegíveis | recomendação final e veto dos pareceres | peso igual entre ativos com COMPRA aprovada, limitado a 40% por ativo e 85% de exposição; resto em caixa; rebalanceia a cada decisão | o LLM agrega algo a uma regra trivial sobre os mesmos sinais? |
| `SIGNAL_RULE_DETERMINISTIC` | Regra determinística sobre os sinais técnicos | os mesmos pareceres | COMPRA aprovada → peso-alvo fixo de 15%; VENDA com posição → zera; MANTER → mantém; veto → sem operação | efeito do gestor LLM em relação a uma política simples com a mesma informação |
| `BUY_AND_HOLD_EQUAL_WEIGHT` | Buy and hold igualmente ponderado | nenhuma | 17% em cada um dos 5 ativos (85% de exposição) na primeira sessão; mantém | referência passiva de mercado no universo |
| `FIXED_WEIGHTS` | Pesos fixos | nenhuma | pesos fixados no pré-registro, rebalanceados na mesma frequência | sensibilidade à escolha de pesos |

Todos passam pela **mesma contabilidade V5** (custódia, caixa liquidado,
custos, liquidação D+2, concentração 40%, exposição 85%) e pelo mesmo ledger
paper, em raízes separadas. As regras que dependem dos pareceres (veto; compra
só com COMPRA) se aplicam ao Global PM, a `EQUAL_WEIGHT_ELIGIBLE` e a
`SIGNAL_RULE_DETERMINISTIC`. Os controles passivos (`BUY_AND_HOLD_EQUAL_WEIGHT`,
`FIXED_WEIGHTS`, `ALWAYS_CASH`) ignoram os pareceres por definição e por isso
não passam por essas regras. A diferença é declarada como parte do controle.

## 3. Variantes do próprio Global PM (só como tratamentos novos)

Comparar o Global PM sob condições de informação diferentes (por exemplo, sem os
textos do Risk LLM, ou só com métricas verificáveis) exige **tratamentos
novos**, versionados, cada um com identidade, prompt e contratos próprios.
Não é uma variação do V2.

## 4. Como avaliar o efeito adicional do Global PM

- **Unidade de comparação:** a mesma sessão; diferenças pareadas por sessão
  entre o Global PM e cada controle.
- **Métrica primária (se pré-registrada):** diferença de retorno acumulado ou
  de retorno por sessão contra `SIGNAL_RULE_DETERMINISTIC`, o controle de mesma
  informação.
- **Inferência:** só com teste pareado definido no pré-registro e número de
  sessões compatível; com 20 decisões, a análise é descritiva.
- **Atribuição causal:** só ao efeito "gestor LLM × regra determinística sobre
  os mesmos pareceres". A arquitetura multiagentes como um todo não tem
  controle sem agentes nesta campanha, e não se afirma causalidade sobre ela.

## 5. Taxa livre de risco e frequência

- Frequência: retornos diários de fechamento a fechamento.
- Taxa livre de risco: CDI diário oficial ou zero, **escolhido no
  pré-registro** antes de qualquer dado; o caixa do ledger rende zero, então o
  custo de oportunidade é medido contra a taxa escolhida.
- Sharpe só com ≥ 60 sessões; indefinido com volatilidade zero (`ALWAYS_CASH`).
