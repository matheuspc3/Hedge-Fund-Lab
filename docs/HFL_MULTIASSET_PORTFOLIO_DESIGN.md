# HFL-MULTIASSET-PORTFOLIO-V1

Status: projeto para uma próxima entrega. Nenhum executor, carteira compartilhada
ou ordem multiativos é implementado na Premium V4. Este tratamento é novo e
exige identidade, manifesto, custos, limites e autorização próprios. Não altera
H2 v6, Validation OA-1, Final Test ou Forward PETR4.

## Fronteiras e responsabilidades

`Pareceres individuais selados + estado compartilhado marcado → Risk global →
proposta global → validação determinística → aprovação humana → execução virtual
prospectiva → reconciliação e histórico`.

O radar fornece sinais consultivos. O gestor global poderá descartá-los ou
manter caixa, documentando a razão. Confiança dos agentes não é probabilidade,
score de qualidade, retorno esperado ou fórmula de dimensionamento. O Risk
global acrescenta avaliação agregada; não remove um veto individual sem uma
política explícita, versionada e aprovada. Uma venda nunca obriga uma compra.

Separar três registros: **decisão dos agentes**, **aprovação humana** e
**execução virtual**. Apenas a última modifica posições. Consulta e replay não
modificam carteira, não criam ordens e não chamam provedores.

## Contratos de estado, independentes de armazenamento

Todos os registros têm `schema_version`, `identity`, `portfolio_id`, `sequence`,
`record_id`, `created_at`, `previous_record_sha256` e `sha256`. Datas de sessão
são ISO; instantes incluem timezone. Valores monetários e quantidades são
strings decimais, calculadas com `Decimal`, nunca floats binários. Moeda BRL.
Hashes usam JSON canônico UTF-8 e regras de serialização versionadas.

Exemplo de estado (preços brutos oficiais, nenhuma dívida/alavancagem):

```json
{
  "schema_version": 1,
  "identity": "HFL-MULTIASSET-PORTFOLIO-V1",
  "portfolio_id": "paper-shared-001",
  "sequence": 14,
  "as_of_session": "2026-10-09",
  "cash": {
    "settled": "20000.00",
    "reserved": "0.00",
    "available": "20000.00",
    "receivables": []
  },
  "positions": [
    {"ticker": "PETR4", "quantity": "1000", "reserved_quantity": "0",
     "average_cost": "45.00", "raw_mark": "50.00", "market_value": "50000.00",
     "weight": "0.50", "realized_pnl_net": "0.00", "unrealized_pnl": "5000.00"},
    {"ticker": "VALE3", "quantity": "500", "reserved_quantity": "0",
     "average_cost": "62.00", "raw_mark": "60.00", "market_value": "30000.00",
     "weight": "0.30", "realized_pnl_net": "0.00", "unrealized_pnl": "-1000.00"}
  ],
  "equity": "100000.00",
  "cash_weight": "0.20",
  "marks_source_sha256": "<sha256>",
  "limits_sha256": "<sha256>",
  "committee_refs": [
    {"identity": "HFL-MULTIASSET-RADAR-V1", "ticker": "PETR4",
     "session": "2026-10-09", "input_sha256": "<sha256>", "result_sha256": "<sha256>"}
  ]
}
```

`equity = settled_cash + receivables + sum(market_value) - liabilities`; na V1,
passivos só podem ser custos já reconhecidos, nunca financiamento. Caixa
reservado continua no patrimônio, mas não em `available`. Contas a receber
compõem patrimônio e possuem peso próprio de caixa indisponível; não são
capacidade de compra. `available = settled - reserved - accrued_cost_buffer`.

Marcações e execução usam preço bruto oficial. Séries ajustadas servem às
features e risco, não à contabilidade de unidades. Eventos corporativos entram
em eventos explícitos (desdobramento/grupamento, dividendos a receber/pagos,
bonificações), com fonte, data efetiva, fator e hashes. Bloquear ativos cujo
evento não possa ser reconciliado. Não multiplicar uma posição bruta pelo
preço ajustado nem inventar barras de sessões sem negócio.

Metodologia proposta de custo médio: compras incorporam preço bruto e custos
de aquisição; vendas baixam custo proporcional pelo custo médio anterior;
resultado realizado líquido = receita bruta menos custos de venda e custo
baixado. Resultado não realizado = marcação menos custo remanescente.
Dividendos são fluxo separado. Arredondamento monetário, impostos e
tratamento de frações de eventos exigem política contábil versionada antes da
implementação; não inferir esses valores de um LLM. V1 negocia unidades
inteiras no fracionário; frações não negociáveis de eventos ficam segregadas.

## Contrato de proposta e exemplos

Uma `PortfolioProposal` vincula `state_sha256`, todos os pareceres e marcas,
`decision_session`, `not_before_session`, `expires_at`, `risk_report_sha256`,
`target_weights`, `target_cash_weight`, `operations` e `reasoning`.
Cada operação tem `operation_id`, `ticker`, `side`, `quantity`,
`limit_price`, `cost_ceiling`, `funding_source`, `priority` e `dependencies`.
Manter ativos e permanecer em caixa são escolhas explícitas, inclusive um
plano com `operations: []`. Alvos são intenção; execução nunca presume que
uma quantidade alcança exatamente um peso depois de gaps e custos.

Exemplos sobre o estado acima (valores ilustrativos, sem recomendação):

| Decisão | Intenção e efeito |
| --- | --- |
| Manter tudo | PETR4 50%, VALE3 30%, caixa 20%; nenhuma operação |
| Vender parcialmente e manter caixa | PETR4 40%, VALE3 30%, caixa 30%; vender 200 PETR4 a uma marca hipotética de 50; recebível líquido, sem compra automática |
| Zerar PETR4 | PETR4 0%, VALE3 30%, caixa 70%; vender até 1000 unidades disponíveis; caixa só fica utilizável após liquidação |
| Comprar usando caixa | Aumentar VALE3 até um alvo permitido usando apenas os 20.000 liquidados, descontados custos e reservas; arredondar quantidade para baixo |
| Permanecer integralmente em caixa | Alvos dos ativos 0%, caixa 100%; vender posições elegíveis, sem novas compras |
| Rotação futura | Vender PETR4; compra de WEGE3 com dependência explícita do evento de liquidação e nova aprovação se a proposta expirar |
| Rebalancear | Reduzir posições acima do limite e aumentar outras com caixa já disponível; execução parcial produz estado novo e revalidação |

Exemplo mínimo de venda sem reinvestimento:

```json
{
  "identity": "HFL-MULTIASSET-PORTFOLIO-V1",
  "state_sha256": "<sha256>",
  "decision_session": "2026-10-09",
  "not_before_session": "2026-10-13",
  "target_weights": {"PETR4": "0.40", "VALE3": "0.30"},
  "target_cash_weight": "0.30",
  "operations": [{"operation_id": "<stable-id>", "ticker": "PETR4",
    "side": "SELL", "quantity": "200", "limit_price": "49.00",
    "cost_ceiling": "20.00", "funding_source": null,
    "priority": 1, "dependencies": []}],
  "reasoning": "Reduzir exposição e manter os recursos em caixa após liquidação."
}
```

Os pesos do exemplo são intenções à marca de decisão, antes de custos. Para
aprovar, o simulador projeta novamente custos e patrimônio pós-operação,
recalcula pesos e verifica concentração; nunca valida apenas o peso declarado.

## Regras determinísticas e Risk global

1. Pesos-alvo não negativos; ativos mais caixa = 1 exatamente na representação
   decimal. Se arredondamento gerar resíduo, atribuí-lo ao caixa, nunca a uma
   posição escondida. Sem short, crédito ou alavancagem na V1.
2. Caixa e quantidade são reservados atomicamente. Compra exige caixa
   **liquidado disponível** suficiente para preço-limite, custos e buffer.
   Venda exige quantidade disponível, sem incluir unidades reservadas.
3. Validar concentração por ativo, setor quando metadados confiáveis estiverem
   disponíveis, exposição total, turnover e custos. Limites são configuração
   explícita do novo tratamento, não herança silenciosa da H2 v6.
4. Risk calcula volatilidade de carteira com covariância de retornos ajustados
   alinhados e pesos observados, histórico e janela declarados. Ausência de
   histórico simultâneo suficiente bloqueia a métrica/decisão aplicável; não
   preencher preços, correlações ou volatilidades com zero. Limites e janela
   deverão ser aprovados antes de implementação, sem retuning no Final Test.
5. Só consumir pareceres completos, íntegros, da mesma sessão, fonte e versão
   compatível. Nunca misturar sintético e oficial. Sem parecer de uma posição,
   aplicar política explícita de manutenção/redução, nunca excluir a posição
   do patrimônio para facilitar o plano.
6. Proposta, aprovação e execução têm IDs separados e chaves únicas. Ordem
   já reservada, executada, cancelada ou de resultado incerto não é reenviada.
   Recuperar exclusivamente pelo journal, sem inferência substituta.
7. Execução exige relógio prospectivo, sessão elegível, autorização vigente,
   marcas válidas e input/state hashes ainda correspondentes. Não executar
   em pregões passados nem retroceder o ledger. Replay histórico é somente
   cálculo offline em artefatos separados.
8. Aprovação humana vincula hashes, quantidades máximas, faixas de preço,
   custo máximo, prazo e dependências. Aprovação vencida ou estado alterado
   exige revalidação e nova aprovação; uma aprovação não autoriza chamada LLM.
9. Toda execução parcial produz evento, saldo e posição; revalidar as operações
   restantes contra esse novo estado antes de qualquer alteração adicional.

## Ordem de execução, pregão e liquidação

Prioridade determinística: reconciliar eventos e liquidações; cancelar reservas
vencidas; processar reduções de exposição aprovadas; processar compras com caixa
já liquidado; marcar e consolidar o estado. Vendas e compras no mesmo pregão
são permitidas **apenas** quando as compras já têm financiamento independente
nas reservas de caixa liquidado. Não fazer netting implícito de venda contra
compra. Uma venda não cria caixa disponível no instante do trade.

Cada venda gera `CashReceivable` com `trade_id`, valor líquido, sessão de
negociação, sessão de liquidação esperada e regra/calendário de origem.
A próxima versão deve definir e verificar o calendário/prazo de liquidação
aplicável, sem assumir que o dinheiro está disponível em T ou fixar um prazo
genérico para todo evento. Apenas `SettlementConfirmed` converte recebível em
caixa utilizável. Compra dependente de venda fica aguardando liquidação,
rechecagem de preço/custos e aprovação válida. Pode ser cancelada sem afetar
a venda. Pode não existir compra seguinte.

## Arquivos, transações e migração

Raiz futura: `data/portfolio/hfl_multiasset_v1/<portfolio_id>/`. Manter snapshots
de estado, propostas imutáveis, aprovações, journal de reservas e eventos de
execução/liquidação. Publicar checkpoint por rename atômico após fsync; journal
durável precede qualquer efeito. Um lock global por carteira protege validação,
reserva e atualização. Não modificar os diretórios do radar ou do Forward.

Na migração para PostgreSQL, os mesmos contratos podem virar tabelas de
`portfolios`, `positions`, `cash_movements`, `proposals`, `approvals`,
`orders`, `fills` e `settlements`. Chaves únicas preservam idempotência;
transação e bloqueio da linha da carteira substituem o lock local. Snapshots
e JSONs exportados preservam hashes e referências históricas. Sem SQL,
FastAPI, React ou Docker novos nesta entrega.

## Plano incremental e critérios de aceitação

1. Aprovar metodologia contábil, contratos, limites, calendário de liquidação
   e identidade; criar estados e eventos puramente sintéticos.
2. Implementar validador e simulador determinísticos offline: compras, vendas
   parciais, zeragem, caixa, rebalanceamento, gaps, custos, eventos corporativos,
   reservas, liquidação e recuperação. Nenhum LLM ou alteração de carteira real.
3. Implementar leitura de pareceres selados e proposta global consultiva, com
   Risk global e orçamento independente. Testar explicitamente venda sem compra.
4. Acrescentar aprovação humana vinculada e execução **virtual prospectiva**
   atrás de autorização separada. Exercitar crashes antes/depois de cada commit,
   concorrência, ordens duplicadas e execução parcial.
5. Qualificar offline e só então autorizar um piloto novo. Comparações com H2
   são exploratórias; o tratamento congelado permanece intacto.

Critérios essenciais: nenhuma compra usa recebível não liquidado; nenhum plano
negativo/alavancado é aceito; nenhuma venda excede unidades disponíveis;
consulta/replay não executa ordem; nenhuma ordem duplicada; nenhuma execução
retroativa; estados e quantidades reconstruíveis exclusivamente dos eventos.
