# Lacunas de pesquisa

Perguntas que os registros atuais não respondem, priorizadas por valor
científico (V) e viabilidade operacional (O), de 1 (baixo) a 3 (alto). Nenhuma
foi iniciada. Experimentos pagos exigem decisão humana, orçamento e preflight
próprios.

| Prioridade | Pergunta | V | O | Evidência necessária | Observações |
|---|---|---|---|---|---|
| 1 | Com que frequência o tratamento V2 produz respostas conformes sobre o **mesmo** contexto congelado? | 3 | 3 | N inferências V2 repetidas sobre `c4879f28…` (novo contexto com a mesma origem, ou preparo idêntico) | Estima a variância do modelo sob contrato fixo; custo por chamada da ordem de centavos de dólar (ver COST_ACCOUNTING) |
| 2 | O contrato V2 mantém a conformidade em sessões **não vistas** durante seu desenvolvimento? | 3 | 2 | Radar + Global PM V2 em sessões novas, com hipóteses pré-registradas | Responde à ameaça de seleção posterior (T10) |
| 3 | O tratamento V1, repetido no mesmo contexto, reproduz a confusão de listas? | 2 | 3 | N inferências V1 sobre o contexto V1 (novo registro do mesmo tratamento) | Separa erro sistemático do contrato de evento amostral; não reclassifica a primeira inferência |
| 4 | Quais componentes do contrato V2 (definições no prompt, nomes de campo, watchlist) explicam a diferença? | 3 | 1 | Desenho fatorial com tratamentos versionados por célula | Custo e número de tratamentos crescem rapidamente |
| 5 | As invariantes de operações (liquidação, custódia, sizing, custos) se sustentam em respostas reais? | 3 | 2 | Sessões em que o gestor proponha operações | Hoje só exercitadas com respostas sintéticas |
| 6 | Qual a taxa de afirmações sem suporte no texto livre, e ela diminui com o contrato V2? | 2 | 2 | Rubrica de auditoria pré-definida, dois avaliadores, várias respostas | A V7.5 tem só duas respostas auditadas |
| 7 | Erros factuais de agentes anteriores (Risk LLM) se propagam ao gestor com que frequência? | 2 | 2 | Rastreamento de afirmações entre pareceres e resposta global em várias sessões | Caso observado: "rompimento de Bollinger" em ITUB4 |
| 8 | Qual foi o custo efetivamente cobrado das chamadas? | 1 | 3 | Console de faturamento do provedor para 12/10/2026 | Fecha a contabilidade; não exige nova inferência |
| 9 | As decisões do gestor têm valor preditivo ou de controle de risco? | 3 | 1 | Protocolo prospectivo com muitas sessões, linha de base e métricas definidas a priori | Exige desenho estatístico próprio; fora do escopo atual |
| 10 | A divergência entre gestor e comitês (ex.: não comprar com COMPRA 5/5) é sistemática? | 2 | 2 | Muitas sessões com sinais favoráveis | Uma sessão não distingue política de acaso |

## Itens que dependem só de documentação

- Coletar a literatura marcada como **[REFERÊNCIA PENDENTE]** no relatório e
  no rascunho do TCC.
- Decidir com a orientação se a nota de auditoria do agregado de pensamento do
  Radar ([COST_ACCOUNTING.md](COST_ACCOUNTING.md), seção 3) deve virar errata
  formal.
- Decidir se a proposta metodológica para as duas falhas legadas de
  preservação (registrada na V7.3, seção 12) será aprovada; até lá, elas
  continuam vermelhas.
