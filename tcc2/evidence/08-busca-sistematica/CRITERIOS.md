# Critérios de triagem por título e resumo

Cada linha do lote é um trabalho do arXiv: id, data, categorias, título, resumo.
Classifique CADA linha, sem pular nenhuma, com base só no título e no resumo.

## Busca principal (lotes 00 a 03): agentes baseados em LLM que decidem negociação ou carteira

INCLUI quando as duas condições valem:
- I1: um LLM (ou agente/modelo de fundação baseado em linguagem) toma ou recomenda
  decisões de negociação, alocação de carteira ou investimento em ativos financeiros
  (ações, cripto, futuros, câmbio, fundos);
- I2: há avaliação empírica dessas decisões (backtest, simulação de mercado, negociação
  real ou simulada) com resultado financeiro (retorno, Sharpe, drawdown etc.).

LEVANTAMENTO: revisão, survey ou mapeamento da literatura sobre LLMs/agentes em
finanças ou negociação (registrar separadamente, não é INCLUI nem EXCLUI).

EXCLUI, com o primeiro código que se aplicar:
- E1: o "mercado" não é financeiro (mercado de agentes, leilão genérico, energia,
  publicidade, trabalho, economia simulada sem ativos financeiros);
- E2: só previsão (preço, retorno, volatilidade) ou classificação de sentimento, sem
  decisão de negociação/carteira avaliada;
- E3: benchmark, dataset ou ferramenta sem tarefa de decisão de negociação/carteira;
- E4: sem avaliação empírica (posição, visão, proposta conceitual);
- E5: o LLM não decide nem recomenda a operação (ex.: só gera fatores, código, relatórios
  ou explicações, e outro modelo decide);
- E6: outro motivo (descreva).

## Busca secundária (lote_sec): contaminação temporal / viés de antecipação em LLMs aplicados a finanças

INCLUI quando o trabalho mede, discute ou mitiga o efeito de o modelo já conhecer
dados ou desfechos do período avaliado (look-ahead bias, contaminação, memorização,
corte de conhecimento) em tarefa financeira.
LEVANTAMENTO: revisão sobre o tema.
EXCLUI: E1 tema não financeiro; E2 "contaminação"/"look-ahead" em outro sentido
(ex.: vazamento em features clássicas sem LLM, poluição ambiental); E6 outro motivo.

## Saída

Arquivo TSV com cabeçalho `id	decisao	codigo	multiagente	motivo`:
- decisao: INCLUI, EXCLUI ou LEVANTAMENTO;
- codigo: I (para INCLUI), L (para LEVANTAMENTO) ou E1..E6;
- multiagente: S se o sistema tem mais de um agente LLM com papéis distintos, N caso
  contrário, - se não se aplica;
- motivo: no máximo 15 palavras, em português.
Uma linha por trabalho do lote, mesma ordem, mesmo id. Na dúvida entre INCLUI e
EXCLUI, prefira INCLUI e escreva "dúvida" no motivo.

## Lotes do OpenAlex (oa_lote_*)

Mesmos critérios. As colunas do lote são id, doi, ano, fonte, título e resumo.
Quando o resumo estiver vazio, decida pelo título: se ele indicar com clareza um
LLM ou agente de linguagem decidindo negociação ou carteira, marque INCLUI com
"dúvida: sem resumo" no motivo; caso contrário, EXCLUI com o código adequado.
