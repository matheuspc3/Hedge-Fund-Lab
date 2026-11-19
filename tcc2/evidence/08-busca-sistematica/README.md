# Busca sistemática do Capítulo 3 (Trabalhos Relacionados)

Atende ao guia do curso (*Trabalho de Conclusão EIC BCC*, capítulo de trabalhos
relacionados): string de busca, base, critérios de inclusão e exclusão e
priorização.

- **Data das buscas:** 19/11/2026, no arXiv (API pública `export.arxiv.org`) e no
  OpenAlex (API pública `api.openalex.org`, sem chave).
- **Por que o OpenAlex:** o guia recomenda a Scopus, "o que não descarta a utilização
  de outras bases". Em 19/11/2026 o login CAFe do CEFET/RJ (`cafe.cefet-rj.br`) não
  respondia, então a Scopus ficou inacessível. O OpenAlex indexa periódicos e anais
  revisados por pares e cobre a limitação do arXiv, que só tem preprints.
- **Scopus:** opcional; se o acesso CAFe voltar, as strings estão no fim deste arquivo.
- **Período coberto:** submissões de 01/01/2023 a 19/11/2026.

## Strings usadas no arXiv

Sintaxe da API do arXiv (`abs:`, `ti:`, `submittedDate`). **Não funciona na Scopus
nem na busca do Portal CAPES**; as strings da Scopus estão no fim deste arquivo.

**Principal** (agentes baseados em LLM que decidem negociação ou carteira):

```
(abs:"language model" OR abs:"language models" OR abs:LLM OR abs:LLMs OR abs:GPT
 OR abs:"foundation agent" OR abs:"foundation model")
AND (abs:agent OR abs:agents OR abs:"multi-agent" OR abs:multiagent)
AND (ti:trading OR ti:trader OR ti:portfolio OR ti:stock OR ti:stocks
 OR ti:investment OR ti:investing OR ti:financial OR ti:finance OR ti:market OR ti:markets)
AND submittedDate:[202301010000 TO 202611192359]
```

Refinamento registrado: a primeira versão exigia os termos financeiros no resumo
(não no título) e não incluía "foundation agent". Retornou 1.087 resultados, com
muito ruído de segurança e engenharia de software, e não recuperava o FinAgent,
cujo resumo usa "foundation agent" em vez de "LLM". A versão acima substituiu-a.

**Secundária** (contaminação temporal e viés de antecipação em LLMs financeiros):

```
(abs:"large language model" OR abs:"large language models" OR abs:LLM OR abs:LLMs OR abs:GPT)
AND (abs:"look-ahead" OR abs:lookahead OR abs:contamination OR abs:"knowledge cutoff" OR abs:memorization)
AND (abs:stock OR abs:stocks OR abs:financial OR abs:finance)
AND submittedDate:[202301010000 TO 202611192359]
```

## Resultados no arXiv

| Busca | Retornados | Incluídos (título e resumo) | Levantamentos | Excluídos |
|---|---:|---:|---:|---:|
| Principal | 474 | 160 | 14 | 300 |
| Secundária | 84 | 54 | 4 | 26 |

Exclusões da principal por motivo: E1 mercado não financeiro 71; E2 só previsão ou
sentimento 22; E3 benchmark ou ferramenta sem decisão de negociação 68; E4 sem
avaliação empírica 14; E5 LLM não decide a operação 26; E6 outro motivo 99 (quase
todos: tema financeiro sem decisão de negociação, como perguntas e respostas,
recuperação de documentos e crédito). Dos 160 incluídos, 75 são multiagentes.

Critérios completos em `CRITERIOS.md`.

## OpenAlex

Mesmos termos, na sintaxe do OpenAlex (busca booleana com radicalização, sem
curingas), a partir de 01/01/2023. Na principal, o primeiro bloco usa o filtro
`title_and_abstract.search` e o bloco financeiro, `title.search`; a secundária usa só
`title_and_abstract.search`. Comando exato:

```
python openalex_search.py resultados_principal_openalex.tsv '("language model" OR LLM OR LLMs OR GPT OR "foundation agent" OR "foundation model") AND (agent OR agents OR "multi-agent" OR multiagent)' 'trading OR trader OR portfolio OR stock OR stocks OR investment OR investing OR financial OR finance OR market OR markets'
python openalex_search.py resultados_secundaria_openalex.tsv '("language model" OR LLM OR LLMs OR GPT) AND ("look-ahead" OR lookahead OR contamination OR "knowledge cutoff" OR memorization) AND (stock OR stocks OR financial OR finance)'
python dedup_openalex.py resultados_principal_openalex.tsv resultados_principal_arxiv.tsv para_triagem_principal_openalex.tsv
python dedup_openalex.py resultados_secundaria_openalex.tsv resultados_secundaria_arxiv.tsv para_triagem_secundaria_openalex.tsv
```

Do OpenAlex entram na triagem só os trabalhos com fonte principal revisada
(periódico, anais de congresso ou série de livros) que não estão nos resultados do
arXiv. A comparação usa o id do arXiv e o título normalizado; versões publicadas com
título diferente do preprint escapam (ex.: StockAgent na ACM TIST), então a
sobreposição real é um pouco maior que a contada.

| Busca | Retornados | Fonte revisada | Já no arXiv | Triados | Incluídos | Levantamentos | Excluídos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Principal | 1.382 | 544 | 115 | 429 | 57 | 36 | 336 |
| Secundária | 295 | 100 | 22 | 78 | 20 | 2 | 56 |

Os trabalhos citados também aparecem no OpenAlex, com a versão publicada: FinCon e
FinBen (NeurIPS), FinAgent e FINSABER (KDD), FinMem (AAAI Symposium) e Lopez-Lira e
Tang (Journal of Financial Economics, 2026; preprint de 2023).

## Totais (arXiv + OpenAlex)

| Busca | Incluídos | Levantamentos |
|---|---:|---:|
| Principal | 217 | 50 |
| Secundária | 74 | 6 |

**Validação da string:** todos os trabalhos de agentes LLM de negociação já citados
no Cap. 3 aparecem na busca principal (TradingAgents, FinCon, FinMem, FinAgent,
StockAgent, TradingGPT, FINSABER, FinBen e o levantamento de Xia et al.);
Glasserman e Lin e Lopez-Lira e Tang aparecem na secundária. Conferência feita
com `match_cited.py`.

## Como a triagem foi feita

A triagem por título e resumo foi feita em 19/11/2026 com modelos de linguagem
(Claude Haiku), em lotes, seguindo os critérios fixos de `CRITERIOS.md`, e
conferida por amostragem. Na dúvida entre incluir e excluir, a regra foi incluir e
marcar "dúvida" no motivo (52 casos na principal do arXiv e 28 na do OpenAlex).
No OpenAlex, 74 dos 429 trabalhos triados não têm resumo na base; foram decididos
pelo título. **Pendente:** revisão dos
autores, começando pelos itens marcados "dúvida" e pelos incluídos que forem
discutidos no texto.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `resultados_principal_arxiv.tsv` | 474 resultados: id, data, categorias, título, resumo |
| `resultados_secundaria_arxiv.tsv` | 84 resultados, mesmo formato |
| `triagem_principal.tsv` | decisão, código, multiagente e motivo de cada resultado |
| `triagem_secundaria.tsv` | idem para a secundária |
| `CRITERIOS.md` | critérios de inclusão e exclusão |
| `arxiv_search.py` | reproduz a busca: `python arxiv_search.py <nome> "<string>" <saida.tsv>` |
| `match_cited.py` | confere quais trabalhos citados aparecem nos resultados |
| `resultados_*_openalex.tsv` | resultados brutos do OpenAlex: id, DOI, id arXiv, ano, tipo e nome da fonte, título, resumo |
| `para_triagem_*_openalex.tsv` | os que entraram na triagem (fonte revisada, fora do arXiv) |
| `triagem_*_openalex.tsv` | decisão, código, multiagente e motivo de cada um |
| `openalex_search.py` | reproduz a busca no OpenAlex |
| `dedup_openalex.py` | filtra fonte revisada e remove o que já está no arXiv |

O arXiv recebe submissões continuamente; uma nova execução das strings traz
resultados posteriores a 19/11/2026. Os arquivos acima são o retrato da data.

## Strings para a Scopus (pendente)

Acesso: Portal de Periódicos CAPES → Acesso CAFe → CEFET/RJ → login → Acervo →
Lista de bases → Scopus (Elsevier). No site `scopus.com`, usar **Advanced document
search** (não a caixa de busca do Portal CAPES). Colar cada string em uma linha.

Busca avançada:

```
TITLE-ABS-KEY(("language model*" OR llm* OR gpt* OR "foundation agent*")
  AND (agent* OR "multi-agent" OR multiagent))
AND TITLE(trading OR trader* OR portfolio* OR stock* OR invest* OR financ* OR market*)
AND PUBYEAR > 2022
```

```
TITLE-ABS-KEY(("language model*" OR llm* OR gpt*)
  AND ("look-ahead" OR lookahead OR contamination OR "knowledge cutoff" OR memoriz*)
  AND (stock* OR financ*))
AND PUBYEAR > 2022
```

Registrar: data, número de resultados de cada string e a exportação em CSV (título,
resumo, DOI). A triagem segue os mesmos critérios; resultados já presentes no arXiv
contam uma vez só.
