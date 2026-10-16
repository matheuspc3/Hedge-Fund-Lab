# Rascunho para o TCC — resultados exploratórios do Radar e do Gestor Global

> Texto preliminar para revisão da orientação. Numeração de seções, figuras e
> tabelas a ajustar ao documento final. Marcadores **[REFERÊNCIA PENDENTE]**
> indicam onde falta literatura; nenhuma referência foi inventada. Os valores
> citados são verificáveis em `docs/evidence/hfl_scientific_consolidation_v75/`.

## X. Avaliação exploratória multiativo

### X.1 Delimitação

Esta seção relata uma avaliação exploratória, separada do experimento H2 v6
descrito no capítulo anterior. Os dois não compartilham hipóteses, métricas nem
critérios de decisão, e os resultados de um não são usados para interpretar o
outro. O objetivo aqui é descrever o comportamento de uma cadeia de agentes
baseados em LLM (comitês técnicos, avaliação de risco individual e um gestor
global de carteira) e o papel de um validador determinístico independente
sobre as propostas do gestor. Não se avalia rentabilidade nem desempenho
preditivo.

### X.2 Procedimento

Foram usados dados oficiais da B3 (COTAHIST), com fator de ajuste de proventos,
para cinco ações (PETR4, VALE3, ITUB4, WEGE3 e BBAS3) na sessão de 09/10/2026.
Para cada ativo, um comitê de cinco analistas técnicos, instâncias do modelo
`gemini-3.8-flash` com temperatura 1,0, emitiu votos de COMPRA, MANTER ou VENDA
com base em indicadores calculados deterministicamente (médias móveis, MACD,
RSI e bandas de Bollinger). Os votos foram agregados por maioria qualificada
(limiar de 0,6). Em seguida, uma etapa de risco individual emitiu parecer
APROVADO ou VETADO: um modelo de linguagem consultivo, ou uma regra
determinística quando a volatilidade anualizada de 21 sessões excedia 50%.

Os cinco pareceres oficiais, selados por hash, foram entregues a um gestor
global, também implementado com o mesmo modelo de linguagem, que deveria
propor uma alocação coordenada de uma carteira hipotética de R$ 100.000,00
inteiramente em caixa. A proposta, uma resposta estruturada com schema estrito,
foi submetida a um validador determinístico que não altera nenhum campo do
modelo, e a um motor de simulação contábil com regras de caixa liquidado,
custódia, liquidação em D+2, custos e limites de risco. A execução de ordens
permaneceu desabilitada.

As inferências ocorreram em 12/10/2026, sobre dados congelados da sessão de
09/10/2026. Uma primeira tentativa de executar os comitês falhou por um defeito
de infraestrutura local (uma proteção de rede ativa em todo o processo), sem
receber nenhuma resposta do provedor. Essa tentativa foi preservada como
incidente e não é contada como comitê. Os resultados abaixo vêm da execução de
recuperação, que usa o mesmo tratamento e dados equivalentes dentro de
tolerâncias declaradas.

### X.3 Resultados dos comitês

Os cinco comitês concluíram, com 25 votos válidos em 25 e 29 chamadas ao
provedor sem erro (Tabela X.1).

**Tabela X.1 — Pareceres do Radar (sessão 09/10/2026)**

| Ativo | Votos (C/M/V) | Sinal técnico | Risco | Recomendação final |
|---|---|---|---|---|
| PETR4 | 5/0/0 | COMPRA | APROVADO | COMPRA |
| VALE3 | 0/0/5 | VENDA | APROVADO | VENDA |
| ITUB4 | 5/0/0 | COMPRA | APROVADO | COMPRA |
| WEGE3 | 1/4/0 | MANTER | APROVADO | MANTER |
| BBAS3 | 5/0/0 | COMPRA | VETADO | MANTER |

O veto de BBAS3 resultou da regra determinística de volatilidade (54,48% contra
o limite de 50% da política didática do laboratório) e converteu a recomendação
COMPRA em MANTER.

### X.4 Gestor global: tratamento V1

Na primeira inferência do gestor (tratamento V1), o modelo propôs manter 100% do
patrimônio em caixa, sem operações. Justificou a decisão com o veto de BBAS3, a
ausência de custódia de VALE3, a neutralidade de WEGE3 e indicadores de
sobrecompra em ITUB4 e PETR4. A simulação contábil isolada considerou a proposta
válida. O validador, porém, rejeitou a resposta (`REJECTED_BY_VALIDATOR`, código
`explanation_selection_inconsistent`): o modelo retirou ITUB4 e PETR4 da lista
de ativos não selecionados e os declarou em um campo que o contrato V1 reservava
a compras dependentes da liquidação de vendas. Não havia operações, portanto
esse campo deveria estar vazio.

A análise posterior mostrou que o contrato V1 definia o campo apenas no código
do validador; nem o prompt nem o schema explicavam sua semântica. O modelo
interpretou "adiamento" como adiamento de investimento, quando o contrato o
definia como dependência de liquidação. Uma cópia da resposta, modificada só em
memória para corrigir as duas listas, passaria pelo validador V1. Esse
contrafactual é diagnóstico: não constitui nova inferência e não altera a
classificação da resposta original, que permanece rejeitada. Os dados não
permitem atribuir a divergência exclusivamente ao prompt, ao schema ou à
variabilidade do modelo.

### X.5 Gestor global: tratamento V2

A correção foi feita como um tratamento novo e versionado (V2), sem alterar o
V1. O contrato V2 define explicitamente a lista de não selecionados (derivável
da ação de cada ativo), troca o campo ambíguo por uma lista de identificadores
de operações dependentes de liquidação, cria um campo consultivo para
observações futuras sem efeito financeiro, exige que números citados como fatos
correspondam a métricas congeladas no contexto e aplica o veto também aos pesos
propostos. O contrato foi qualificado antes com respostas sintéticas, que não
são resultados do modelo.

Na primeira inferência V2, com os mesmos cinco pareceres, o modelo novamente
propôs 100% em caixa, sem operações. Listou os cinco ativos como não
selecionados, registrou ITUB4 e PETR4 apenas como observações consultivas, com
o sinal igual ao do parecer, e deixou vazia a lista de operações dependentes de
liquidação. As 13 métricas citadas conferiram com o contexto. O validador
classificou a resposta como válida (`VALID_PROPOSAL`).

### X.6 Comparação e uso computacional

A Tabela X.2 resume as duas inferências. A intenção econômica foi a mesma; o
que diferiu foi a conformidade da resposta ao contrato de cada tratamento.

**Tabela X.2 — Inferências do gestor global**

| | V1 | V2 |
|---|---|---|
| Caixa proposto | 100% | 100% |
| Operações | 0 | 0 |
| Validação financeira | válida | válida |
| Validação global | rejeitada | válida |
| Tokens (entrada / saída / total) | 18.794 / 2.519 / 21.313 | 20.623 / 2.880 / 23.503 |
| Piso de custo observado | US$ 0,0235 | US$ 0,0263 |

O provedor não informou os tokens de raciocínio interno em nenhuma das duas
chamadas. Por isso os valores monetários são apenas limites inferiores
calculados com os tokens informados, não custo efetivamente cobrado. As
diferenças de consumo entre V1 e V2 não medem a eficiência dos tratamentos:
trata-se de duas chamadas únicas com contratos distintos.

### X.7 Discussão

Os resultados ilustram a separação entre a decisão substantiva de um modelo de
linguagem e a aderência formal de sua resposta a um contrato verificável. No
tratamento V1, uma decisão plausível foi rejeitada por inconsistência formal; o
validador funcionou como barreira independente da geração
**[REFERÊNCIA PENDENTE: validação de saídas estruturadas de LLMs]**. A evolução
para o V2 tornou explícita a semântica dos campos e permitiu que uma resposta
com a mesma intenção satisfizesse o contrato.

A aprovação, contudo, não certifica a argumentação textual. A resposta V1
continha afirmações sem suporte nos dados fornecidos (por exemplo, um
"rompimento" da banda de Bollinger contrariado pelos números e referências a
setor econômico ausentes do contexto). A resposta V2, embora sem essas
afirmações, ainda descreveu o limite interno de volatilidade como
"regulamentar" e usou linguagem preditiva ("risco de correção imediata"). Também
se observou propagação de erro entre agentes: a expressão sobre a banda de
Bollinger veio do parecer de risco produzido por outro modelo
**[REFERÊNCIA PENDENTE: propagação de erros em sistemas multiagentes com LLM]**.

Por fim, manter a carteira em caixa é uma decisão admissível, mas satisfaz
trivialmente limites de exposição e custo. A aprovação V2 não exercitou as
regras de liquidação, custódia e dimensionamento de operações, avaliadas até
aqui apenas com casos sintéticos.

### X.8 Limitações

A avaliação cobre uma única sessão de mercado e duas inferências do gestor, uma
por tratamento, com amostragem estocástica. Não houve repetição independente.
O tratamento V2 foi desenhado após a observação da falha do V1, o que
caracteriza evolução orientada por diagnóstico, e não validação confirmatória.
A carteira é hipotética, as políticas de risco são didáticas e nenhuma ordem
foi executada; não há, portanto, resultado financeiro a relatar.

### X.9 Síntese

A investigação exploratória identificou uma inconsistência entre a semântica
produzida pelo modelo de linguagem e o contrato de validação determinística.
Após evolução versionada do contrato, uma nova inferência foi classificada como
válida pelas invariantes do tratamento V2, mantendo-se a independência entre
geração da proposta e validação financeira. Os resultados não permitem inferir
superioridade estatística ou financeira entre os tratamentos, nem benefício
causal da arquitetura multiagentes; essas questões exigem os experimentos
descritos como trabalhos futuros.
