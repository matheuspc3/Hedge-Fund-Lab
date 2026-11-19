# Revisão Geral da Monografia — TCC 2 (Hedge-fund-lab)

**Monografia avaliada:** *Hedge-fund-lab: Laboratório Quantitativo de Backtesting baseado em Sistemas Multiagentes* (Lucas Pereira da Silva e Matheus Pereira de Carvalho; orientador: Eduardo Soares Ogasawara, D.Sc.; banca: Renato Campos Mauro, D.Sc., e Gilberto Gil Fidelis Gomes Passos, M.Sc.).  
**Escopo auditado:** `tcc2/main.tex`, `tcc2/chapters/01-introducao.tex` a `07-conclusao.tex`, `tcc2/chapters/tabelas/*.tex`, `tcc2/figures/*.tex`, `tcc2/references.bib`, `tcc2/eic-bcc-tcc.cls`, `tcc2/apalike.bst`, `tcc2/main.pdf` (86 páginas; 74 numeradas), `tcc2/main.log`, `tcc2/main.blg`, além da conferência integral contra `METRICAS_REPLAY.md`, `BOOTSTRAP_REPLAY.md`, `evolucao_replay_v1_v2_v3_tcc.md`, `H2_METHODOLOGICAL_FREEZE_V1.md`, `equity_diario.csv`, o código-fonte em `src/`, `scripts/` e `dashboard/` e o guia oficial `Trabalho de Conclusao EIC BCC.pdf`.

---

## 1. Veredito Geral

**Nota atual: 7,4 / 10.** O núcleo científico é sólido e raro em TCC de graduação: a distinção entre a execução pré-especificada (v1) e as iterações exploratórias dentro da amostra (v2/v3) é honesta, os números do replay conferem com as fontes seladas até o centavo e a inferência via *bootstrap* estacionário pareado é reprodutível. O que impede a nota máxima são defeitos graves de acabamento no PDF compilado, um erro factual sobre `H_real`, 12 referências arXiv ilocalizáveis, a subestrutura desatualizada do Capítulo 2 e o excesso de inventário de código no Capítulo 4.

**As 5 mudanças que mais elevam a nota (em ordem de impacto):**
1. **Consertar os quatro defeitos críticos do PDF compilado:** ativar os acrônimos (`\gls{}` + `makeglossaries`) para eliminar a página em branco da Lista de Acrônimos (p. 8 do PDF); substituir todos os `\paragraph{}` que geram numeração `5.3.0.0.1` no Sumário e no corpo; recompilar com hifenização em português ativa (`babel-portuges`, eliminando cortes como `trabal-hos`, `sim-ulação` e `mod-elo`); e eliminar as colisões/estouros de margem das Tabelas 3.1 (+21,5 pt) e 6.1 (+25,5 pt) e dos caminhos em `\texttt` (+33,5 pt).
2. **Corrigir o erro factual sobre `H_real` e alinhar hipóteses e objetivos:** corrigir a confusão entre o *snapshot* completo (2.649 barras, 2016–2026), o conjunto elegível `|E|` (1.519 sessões, 2018–2024) e `H_real` (apenas 4 sessões de *Hardening*) em `04-arquitetura.tex:72` e `05-metodologia.tex:188`; alinhar o enunciado declarativo de H1/H2 entre Cap. 1 e Cap. 5; e responder explicitamente, um a um, aos seis objetivos específicos na Conclusão.
3. **Corrigir as 61 referências em `references.bib`:** incluir `doi = {10.48550/arXiv.<id>}` (ou identificador no campo `journal`) nas 12 entradas arXiv que hoje imprimem apenas `"arXiv, YYYY."` sob o `apalike.bst`, proteger com `{...}` as 17 quebras de capitalização (`Bloomberggpt`, `Tradinggpt`, `u.s.`, `1/n`, `sharpe`, `llm`), corrigir `de Silva, Harindra` e `López de Prado` e sanar o aviso do BibTeX em `FinMem2024`.
4. **Reequilibrar Cap. 2 e Cap. 4:** remover *Factor Investing* (2.4, não usado) e a duplicação com Cap. 3 em 2.6, adicionando fundamentação de *bootstrap* estacionário, multiplicidade (Holm / interseção–união) e propriedades do Sharpe sob retornos negativos; enxugar o Cap. 4 (~5.450 palavras) movendo inventários de módulos/constantes para Apêndice e priorizando a carteira multiativos antes do legado de ativo único.
5. **Padronizar figuras, tabelas e lacunas de clareza científica:** adicionar `Fonte:` ABNT a todas as 6 figuras e 5 tabelas que hoje não a trazem, incluir 2 figuras metodológicas no Cap. 5, definir matematicamente as 8 *features* adimensionais, explicitar na Seção 6.6 que o acompanhamento prospectivo opera a versão **v1** e esclarecer a discrepância de 0,01 de arredondamento entre as Tabelas 6.2 e 6.4.

---

## 2. Placar por Capítulo

| Capítulo | Nota (0–10) | Maior problema | Esforço p/ 10 |
|---|---:|---|:---:|
| **Cap. 0 — Pré-textuais, Resumo e Abstract** (`main.tex`) | **6,5** | Página em branco na Lista de Acrônimos (0 usos de `\gls`); Sumário poluído por `x.y.0.0.z` e título `SUMÁRIO` desalinhado; macros de rascunho (`\warn`/`\verify`/`\remarks`); Resumo omite o resultado da v2 | **P** |
| **Cap. 1 — Introdução** (`01-introducao.tex`) | **7,8** | H1 e H2 redigidas como tarefas ("Será avaliado se..."), divergindo do enunciado declarativo no Cap. 5; ausência de declaração de uso de IA (manual EIC/BCC, Seção 2.5); parágrafo 4 excessivamente longo (190 palavras) | **P** |
| **Cap. 2 — Fundamentação Teórica** (`02-fundamentacao.tex`) | **6,0** | Resquícios do TCC 1 (*Factor Investing* nunca usado; subseção única 2.1.1; subseção de 1 frase em 2.5.2); falta fundamentação de *bootstrap* estacionário e multiplicidade; 4 `\citep` sintaticamente incorretos; variáveis não definidas nas equações; duplicação com Cap. 3 | **G** |
| **Cap. 3 — Trabalhos Relacionados** (`03-relacionados.tex`) | **8,0** | Colisão textual severa (`MultiagenteCustos` e `RastreabilidadeReferências`) e estouro de +21,5 pt na Tabela 3.1, que flutua para o meio da Seção 3.8; falta explicitar critérios de seleção da literatura; tensão redacional entre L50 e L100 sobre o estatuto da v1 | **M** |
| **Cap. 4 — Arquitetura e Implementação** (`04-arquitetura.tex`) | **7,0** | Erro factual sobre `H_real` (1.519 vs 2.649 barras); extensão desproporcional (~5.447 palavras / 17 págs.) em tom de inventário de código; estouro de +33,5 pt em `\texttt`; `--` convertido em travessão em `–references-only`; seta colidindo na Fig. 4.2; falta definição das 8 *features* e `Fonte:` nas figuras/tabelas | **G** |
| **Cap. 5 — Metodologia Experimental** (`05-metodologia.tex`) | **8,0** | 16 usos de `\paragraph{}` gerando entradas `5.x.0.0.y` no Sumário; repetição do erro factual `H_real` (L188); zero figuras metodológicas; página 48 quase vazia com 1 linha viúva; protocolo original citado 7 vezes antes de ser explicado na Seção 5.7 | **M** |
| **Cap. 6 — Resultados e Discussão** (`06-resultados.tex`) | **8,2** | 14 usos de `\paragraph{}` gerando `6.x.0.0.y`; Tabela 6.1 estourando margem (+25,5 pt); ausência de `Fonte:` nas Figs. 6.1–6.3 e cabeçalhos sem negrito nas Tabelas 6.2–6.4; discrepância de 0,01 não explicada entre Tabelas 6.2 e 6.4; Seção 6.6 não explicita que o piloto diário usa v1 e induz ambiguidade na base de $-17{,}61\%$ | **M** |
| **Cap. 7 — Conclusão** (`07-conclusao.tex`) | **7,8** | Não fecha explicitamente cada um dos 6 objetivos específicos do Cap. 1 (exigência do manual EIC/BCC, p. 13); 4 usos de `\paragraph{}` gerando `7.2.0.0.y`; repetição quase literal das limitações de 5.8 e 6.5; "cerca de US\$ 8,63" | **P** |
| **Referências** (`references.bib` / `main.bbl`) | **6,0** | 12 preprints arXiv impressos apenas como `"arXiv, YYYY."` sem ID nem link; 17 erros de capitalização no título; `Silva, H.` em vez de `de Silva, H.`; `Lopez de Prado` sem acento; aviso BibTeX em `FinMem2024`; p. 74 isolada com 1 única referência | **P** |

---

## 3. Problemas Macro (Eixos 1 e 5)

### 3.1 Narrativa, encadeamento e fios soltos

A linha mestra (problema → laboratório → replay pareado em três versões → inferência negativa sobre superioridade → achado arquitetural sobre especialização e governança → acompanhamento prospectivo) é clara e defensável. O mérito de relatar resultados negativos sem forçar significância estatística é o ponto mais forte do texto.

Entretanto, **quatro fios soltos e cicatrizes da migração TCC 1 → TCC 2** comprometem a unidade narrativa:
1. **Desconexão entre o que o Cap. 2 prepara e o que os Caps. 4–6 usam:** o Cap. 2 dedica a Seção 2.4 inteira a *Factor Investing* (modelos de 3 e 5 fatores de Fama-French), conceito que **nunca reaparece** no sistema nem nos experimentos (o manual EIC/BCC, p. 8, orienta explicitamente: *"Limite-se exclusivamente aos temas utilizados em seu trabalho"*). Em contrapartida, o Cap. 2 **não fundamenta** três pilares teóricos essenciais do Cap. 5: *bootstrap* estacionário (Politis e Romano, 1994), controle de multiplicidade (Holm, 1979) / teste de interseção–união, e a patologia algébrica do índice de Sharpe sob retornos médios negativos (que explica o resultado de H1 e o único $p_+ < 0{,}05$ bruto da v3 contra a SMA 50/200).
2. **Protagonismo invertido no Cap. 4 e atraso explicativo no Cap. 5:** o estudo empírico do TCC 2 é o Replay Contínuo multiativos (que **não** usa o grafo LangGraph nem `engine.py` nem SQLAlchemy), mas o Cap. 4 passa suas primeiras seis seções (4.1–4.6, págs. 19–24) descrevendo SQLAlchemy, `H_real`, `engine.py` e o grafo LangGraph de ativo único antes de chegar ao sistema que de fato gerou os resultados (Seção 4.7, p. 24). No Cap. 5, ocorre o simétrico: o "protocolo original" é invocado sete vezes nas Seções 5.5 e 5.6 (págs. 41–44) como origem do Sharpe congelado e do Bootstrap A, mas só é explicado ao leitor na Seção 5.7 (p. 45).
3. **Redundância em três camadas de limitações:** praticamente os mesmos sete tópicos de ameaças/limitações são reescritos com frases quase idênticas na Seção 5.8 (págs. 46–48), na Seção 6.5 (págs. 61–62) e na Seção 7.4 (p. 67). No Cap. 5 devem ficar as ameaças de *desenho*; no Cap. 6, como elas se *manifestaram empiricamente* nos números observados (ex.: a Bollinger vencer por R\$ 4.819,69, as 27 vendas residuais da v3); no Cap. 7, uma síntese condensada de no máximo meia página vinculada diretamente aos trabalhos futuros.
4. **Fio solto do acompanhamento prospectivo na Conclusão:** o Objetivo Específico 6 (Cap. 1, L22) é *"Operar a carteira multiativos em acompanhamento diário prospectivo, como base para a avaliação livre de contaminação"*. A Seção 6.6 apresenta 23 pregões reais (Multiagentes em $-23{,}94\%$ vs Buy \& Hold em $-17{,}61\%$), mas a Conclusão (Cap. 7) cita o ciclo diário apenas de passagem na Seção 7.1 e **não sintetiza esse resultado empírico preliminar** nem informa em 6.6 que a carteira diária executa a arquitetura **v1**.

### 3.2 Mapa de Rastreabilidade: Objetivos, Perguntas e Hipóteses → Resposta

| Elemento formulado no Cap. 1 | Onde é entregue / respondido | Resposta explícita no texto? | Diagnóstico |
|---|---|---|---|
| **Objetivo Geral:** desenvolver o Hedge-fund-lab, laboratório quantitativo para *backtesting* baseado em sistemas multiagentes (`01-introducao.tex:8`) | Caps. 4, 5 e 6; fechado em `7.1` e `7.6` | **Sim** | Entregue e rastreável; o título e o objetivo ainda enfatizam *backtesting*, embora o estudo empírico seja replay retrospectivo multiativos + operação diária (convém mencionar ambos sem perder o vínculo com o título). |
| **Obj. Esp. 1:** construir pipeline reproduzível da B3 (COTAHIST), correção de proventos e calendário próprio (`01:17`) | Seção 4.2 (`04:42-78`) | **Parcial em Cap. 7** (`7.1`, p. 64) | Entregue em 4.2, mas Cap. 7 não o enumera explicitamente; contém erro factual de `H_real` em `04:72` e não explicita que os fatores Yahoo do replay não são *point-in-time* no fechamento. |
| **Obj. Esp. 2:** implementar motor de *backtesting* e livro contábil de eventos auditável com custos, proventos e métricas do protocolo (`01:18`) | Seções 4.3, 4.5, 5.5 | **Parcial em Cap. 7** (`7.1`, p. 64) | Fio ligeiramente frouxo: o replay não usa `engine.py` (motor de *backtesting*), Sortino e giro não são congelados no protocolo (`05:131,144`) e o giro do replay difere de `metrics.py`. Convém registrar essa nuance no fechamento do Obj. 2. |
| **Obj. Esp. 3:** desenvolver sistema multiagente baseado em LLMs nas versões de ativo único (LangGraph) e multiativos (`01:19`) | Seções 4.6, 4.7, 4.10 | **Parcial em Cap. 7** (`7.1`, p. 64) | Implementado e descrito, mas em Cap. 7 falta o balanço explícito por objetivo exigido pelo manual EIC/BCC (p. 13). |
| **Obj. Esp. 4:** estabelecer desenho experimental pareado e causal, com métrica primária e regra estatística, sem vazamento nos dados (`01:20`) | Seções 4.8, 5.2–5.6 | **Parcial em Cap. 7** (`7.1–7.2`, págs. 64–65) | Entregue; merece destaque explícito na prestação de contas dos objetivos que a causalidade cobre os *dados de entrada*, não o conhecimento prévio do LLM. |
| **Obj. Esp. 5:** executar o Replay Contínuo Abr–Nov/2026 e analisar a evolução arquitetural entre v1, v2 e v3 (`01:21`) | Seções 4.9, 4.10, 6.1–6.5; fechado em `7.2–7.3` | **Sim** | Plenamente entregue com auditorias reproduzíveis. |
| **Obj. Esp. 6:** operar a carteira multiativos em acompanhamento diário prospectivo (`01:22`) | Seções 4.11, 5.7.3, 6.6 | **Fraco em Cap. 7** (`7.1`, L12) | Operacionalizado (23 pregões em 6.6), mas Cap. 7 não resume o resultado preliminar (Multiagentes v1 em $-23{,}94\%$ vs Buy \& Hold em $-17{,}61\%$) nem fecha formalmente o objetivo. |
| **Pergunta Principal:** como projetar ambiente comparável e se a arquitetura multiagente produz decisões mais robustas (`01:6`) | Caps. 4–6; respondida explicitamente em `7.2` (`07:18`) | **Sim** | Resposta direta em duas partes (ambiente realizado + ausência de evidência de superioridade). |
| **Pergunta Secundária (Arquitetural):** mantidos modelo, topologia, dados e execução, quanto do comportamento depende da especialização e da governança determinística (`01:12`) | Seção 6.4; respondida explicitamente em `7.3` (`07:28-40`) | **Sim** | Bem respondida com quatro achados descritivos e qualificada contra atribuição causal por pilar isolado. |
| **H1:** estratégias de *momentum*/*trend following* superam *equal weight* em Sharpe líquido (`01:28`, `05:44`) | Seção 6.3.1 (`06:68-74`); respondida em `7.2` (`07:20`) | **Sim** | **H0 não rejeitada:** SMA 50/200 vs Equal Weight 63d, $\hat{\Delta} = -0{,}71$, $p_+ = 0{,}881$, IC 90\% $[-1{,}75;\ 0{,}31]$. Redação divergente entre Cap. 1 ("Será avaliado se...") e Cap. 5. |
| **H2:** sistema multiagente LLM supera *benchmarks* em Sharpe líquido e critérios complementares (`01:29`, `05:45`) | Seções 6.3.2–6.3.3 (`06:75-88`); respondida em `7.2` (`07:22,26`) | **Sim** | **H0 não rejeitada na v1 (pré-especificada):** 4 contrastes negativos e 1 positivo não significativo contra SMA 50/200 ($\hat{\Delta} = +0{,}14$, $p_+ = 0{,}432$; todos $p_+$ Holm = 1,000). v2 e v3 são estritamente descritivas; v3 vs SMA ($p_+ = 0{,}024$) não sobrevive a Holm ($0{,}121$) nem tem estatuto de teste. |
| **H0:** não há diferença estatisticamente significativa entre as abordagens (`01:30`, `05:46`) | Seção 6.3.4 (`06:89-92`); respondida em `7.2` (`07:24`) | **Sim** | **Não rejeitada** em H1 e H2 (v1); texto esclarece corretamente que não rejeitar H0 não prova igualdade dado o baixo poder ($EP \approx 1{,}3$). |

### 3.3 Equilíbrio entre capítulos e plano de redistribuição

Contagem real de palavras no corpo (excluindo comandos LaTeX, tabelas e gráficos TikZ/pgfplots) e páginas no PDF atual:

| Capítulo | Palavras atuais | Págs. atuais | Diagnóstico | Ação recomendada | Págs. estimadas pós-ajuste |
|---|---:|---:|---|---|---:|
| Cap. 1 — Introdução | ~1.204 | 3 | Adequado | Manter extensão; incluir subseção curta de uso de IA (manual EIC/BCC) | 3,5 |
| Cap. 2 — Fundamentação | ~1.822 | 7 | **Subdimensionado e desalinhado** | Cortar 2.4 *Factor Investing* ($-0{,}5$ p.), enxugar 2.6 ($-0{,}8$ p.) e fundir 2.5.2 ($-0{,}2$ p.); expandir com *bootstrap* estacionário, testes múltiplos/Holm/interseção–união e propriedades do Sharpe sob retornos negativos ($+2{,}5$ p.) | 8–9 |
| Cap. 3 — Relacionados | ~2.493 | 8 | Equilibrado | Incluir parágrafo com critério de seleção da literatura ($+0{,}3$ p.) e corrigir Tabela 3.1 | 8 |
| Cap. 4 — Arquitetura | ~5.447 | 17 | **Inflado (25\% do texto; tom de README/inventário)** | Mover Tabela 4.3 (constantes v3), inventário de arquivos de `src/experiments` (4.12) e detalhes de empacotamento/exportação/rotas (4.9.5, 4.13) para **Apêndice A** ($-4$ p.); condensar legado de ativo único (4.6) ($-1{,}5$ p.); adicionar fórmulas das 8 *features* ($+0{,}5$ p.) | 11–12 (+ Apêndice A de ~4 p.) |
| Cap. 5 — Metodologia | ~4.107 | 13 | Sólido, mas sem figuras | Remover `\paragraph`, enxugar repetições com Cap. 4 ($-1$ p.) e incluir 2 figuras metodológicas ($+1{,}5$ p.) | 13 |
| Cap. 6 — Resultados | ~4.566 | 15 | Núcleo forte | Enxugar repetição de 6.5 com 5.8 ($-1$ p.) e incluir 1–2 figuras novas ($+1{,}5$ p.) | 15 |
| Cap. 7 — Conclusão | ~1.891 | 5 | Adequado | Condensar 7.4 (evitando cópia de 5.8) e incluir prestação de contas explícita dos 6 objetivos específicos | 5 |

### 3.4 Propostas de reordenação de seções

- **Capítulo 2:** consolidar na ordem progressiva do experimento: `2.1 Eficiência e Adaptação de Mercados` (absorver 2.1.1 ou criar 2.1.1 EMH e 2.1.2 Críticas Comportamentais e AMH, eliminando a subseção única) → `2.2 Carteiras de Referência e Estratégias Quantitativas` (Buy \& Hold, Equal Weight, Análise Técnica — tendência e reversão — e Markowitz/Mínima Variância, **excluindo** 2.4 *Factor Investing* e fundindo 2.5.2 com 2.8) → `2.3 Sistemas Multiagentes Baseados em Modelos de Linguagem` (conceitos estruturais sem repetir resultados de artigos do Cap. 3) → `2.4 Backtesting e Riscos Metodológicos` (*overfitting*, *data snooping*, PBO, contaminação temporal) → `2.5 Métricas de Desempenho e Inferência Estatística` (Retorno, Sharpe — incluindo comportamento com retorno negativo e erro-padrão de Lo —, Sortino, *Maximum Drawdown*, *turnover*/custos, *bootstrap* estacionário de Politis–Romano e controle de multiplicidade de Holm / interseção–união).
- **Capítulo 4:** após `4.1 Visão Geral`, `4.2 Pipeline de Dados` e `4.3 Persistência e Livro Contábil`, apresentar diretamente o núcleo empírico (`4.4 Carteira Multiagente Multiativos`, `4.5 Relógio Causal`, `4.6 Arquitetura do Replay Contínuo`, `4.7 Evolução entre Versões v1–v3`, `4.8 Operação Diária`), reunindo `4.9 Legado de Ativo Único (LangGraph) e Camada de Experimentos` e `4.10 Interface de Acompanhamento` ao final. Hoje o leitor lê 6 páginas de ativo único antes de ver o objeto central do TCC 2.
- **Capítulo 5:** mover `5.7 Protocolo Confirmatório Planejado` (enxugado) para logo após `5.1 Caracterização da Pesquisa` (como `5.2 Transição do Protocolo Original para o Replay e Acompanhamento Prospectivo`). Isso elimina as sete referências antecipadas ("conforme o protocolo original") que hoje deixam o leitor no escuro entre as páginas 38 e 44.

### 3.5 Rigor científico, honestidade v1 vs v2/v3 e reprodutibilidade

**Conformidade com `WRITING_RULES.md`:**
- *Sem afirmação de superioridade sem evidência:* **OK.**
- *Separação entre teste sintético (`MockLLMClient`) e experimento real:* **OK** (`04-arquitetura.tex:342` e `05-metodologia.tex:14` separam com rigor).
- *Sem números inventados:* **OK** para todos os números do replay e do acompanhamento diário! Todos os valores patrimoniais, retornos, Sharpes, Sortinos, MDDs, operações, custos, caixas, RSIs, placares de votos, proventos e valores-$p$ foram conferidos por script contra `METRICAS_REPLAY.md`, `BOOTSTRAP_REPLAY.md`, `evolucao_replay_v1_v2_v3_tcc.md`, `daily.csv` e `equity_diario.csv`, com **paridade exata**. (O único erro numérico/factual de dado é `H_real` em `04:72` e `05:188`, detalhado em `C4-01` e `C5-02`.)

**Três pontos de atenção sobre honestidade v1 vs v2/v3 e rigor:**
1. **Omissão da v2 no Resumo e no Abstract (`main.tex:56,61`):** o Resumo informa que v1 terminou em $-17{,}82\%$ e salta direto para v3 ($+0{,}07\%$), omitindo que a v2 ($-14{,}26\%$) também ficou em último lugar abaixo das cinco referências. Incluir a v2 em uma cláusula de 5 palavras torna o resumo mais equilibrado e impede a impressão de que a primeira correção já superou os *benchmarks*.
2. **Tensão redacional sobre o estatuto da v1 (`03-relacionados.tex:50` vs `03:100` e `05:79`):** em `03:50` lê-se *"trata o replay retrospectivo como estudo exploratório"*, sem distinguir ali a v1 (pré-especificada com decisão inferencial condicionada ao replay) de v2/v3 (exploratórias dentro da amostra). Padronizar o vocabulário em todo o documento: *replay retrospectivo* (como um todo, sujeito à limitação de contaminação do modelo), dentro do qual a *v1* é pré-especificada para decisão inferencial condicionada, *v2/v3* são iterações exploratórias dentro da amostra e a *avaliação confirmatória livre de contaminação* cabe exclusivamente ao acompanhamento prospectivo.
3. **Quem decide na v3 — o LLM ou o compilador/regras de prompt?** Na v3, as cinco lentes impõem faixas numéricas explícitas de reversão à média (`RSI < 38`, `RSI > 64`, `bb_lower_gap <= 0,035`) e o compilador executou **80 ajustes** (56 em `CORE_FLOOR_STEP_SELL`) ao longo de 81 operações. Embora a Seção 6.4.3 reconheça que "a governança determinística moldou o resultado tanto quanto os sinais", o rigor científico pede explicitar duas perguntas abertas: (i) qual a fração de propostas diárias do gestor alteradas pelo compilador na v3, e (ii) se o ganho observado decorre do raciocínio do LLM ou de regras determinísticas de reversão à média codificadas em linguagem natural (reforçado pelo fato de a Bollinger 20/2 pura superar a v3 por R\$ 4.819,69 com custo zero de inferência).

**Lacunas de reprodutibilidade e limitações ausentes:**
- **Definição matemática das 8 *features* adimensionais ausente:** `04-arquitetura.tex:150` lista `rsi`, `sma50_gap`, `sma200_gap`, `bb_upper_gap`, `bb_lower_gap`, `bb_width`, `macd_ratio` e `macd_signal_ratio`, e `04:336-339` fixa limiares numéricos exatos (`bb_lower_gap < 0,035`, `sma200_gap > -0,08`, `bb_upper_gap >= -0,02`), mas **em nenhum ponto da monografia há a fórmula dessas 8 grandezas** (nem mesmo o sinal convencionado de `bb_upper_gap` e `bb_lower_gap`, que existe no documento mestre §1.4 mas ficou fora da monografia!). Sem essas definições, o experimento não é reproduzível a partir do texto.
- **Equações omitidas em 5.5:** explicitar que os retornos diários são simples ($r_t = \mathrm{PL}_t/\mathrm{PL}_{t-1} - 1$, com $\mathrm{PL}_0 = \text{R\$ } 100.000{,}00$ em 02/04/2026) e incluir as fórmulas do retorno anualizado ($( \mathrm{PL}_{153}/\mathrm{PL}_0 )^{252/153} - 1$), volatilidade anualizada ($\hat{\sigma}_r\sqrt{252}$) e *Maximum Drawdown* ($\min_t (\mathrm{PL}_t/\max_{s\le t}\mathrm{PL}_s - 1)$).
- **Duas limitações relevantes ausentes em 5.8 / 7.4:** (a) **viés de seleção e sobrevivência do universo** (cinco ações *blue chips* líquidas escolhidas *ex post*, sem empresas deslistadas ou de baixa liquidez, em contraste direto com \citet{FINSABER2026} citado no Cap. 3); e (b) **custo de oportunidade sob taxa livre de risco brasileira (CDI):** com $r_f = 0$, a v3 exibe Sharpe positivo ($+0{,}09$) com retorno de $+0{,}07\%$ em 153 pregões; sob CDI positivo (~10–15\% a.a., cerca de 6–9\% no período), seu retorno excedente e seu Sharpe tornam-se marcadamente negativos (assim como o de todas as demais carteiras, inclusive a Bollinger 20/2 em $+4{,}89\%$).

---

## 4. Achados Detalhados por Capítulo (Eixos 2 e 3)

### Padrões transversais de escrita (registrados uma vez com todas as ocorrências)

Para evitar repetição mecânica, os cinco padrões sistemáticos de escrita e formatação que atravessam vários capítulos estão consolidados abaixo; achados específicos de cada capítulo seguem na sequência.

1. **PADRÃO T1 (Crítico) — Acrônimos declarados nunca usados com `\gls{}` (Lista de Acrônimos em branco):** `main.tex:19-27` declara 9 acrônimos (`tcc`, `llm`, `etl`, `emh`, `amh`, `mas`, `rsi`, `sma`, `macd`), mas há **zero** ocorrências de `\gls`, `\glspl`, `\acrshort`, `\acrlong` ou `\acrfull` em toda a monografia. Como consequência, `main.acn` tem 0 bytes, `main.acr` não existe e a **página 8 do PDF está completamente em branco**. Além disso, diversos acrônimos recorrentes no texto não são declarados em `main.tex` nem expandidos no primeiro uso: `B3` (Brasil, Bolsa, Balcão), `COTAHIST`, `OHLCV` (`04:77`), `RAW` (`04:77`), `JCP` (`04:217`, Juros sobre Capital Próprio — nunca expandido!), `SLSQP` (`04:242`, *Sequential Least Squares Programming* — nunca expandido!), `SHA-256` (`04:77`), `HTTP` (`04:21`), `JSON` (`04:368`), `CSRF` (`04:368`), `CSV` (`04:258`), `DQN`/`TDQN`/`PPO` (`03:10`), `LSTM` (`03:18`), `CFA` (`03:26`), `CVaR` (`03:35`), `ARIMA` (`03:48`), `GSM8K` (`03:54`), `MAR` (`02:140`, expandido só em `05:124`), `MDD` (`metricas-replay.tex:11`, nunca definido como sigla no texto), `PREABE` (`04:216`). **Ação:** (a) substituir o uso manual das 9 siglas por `\gls{...}` (ou `\glspl{llm}`); (b) declarar em `main.tex` as siglas técnicas efetivamente usadas no texto (ex.: `B3`, `COTAHIST`, `OHLCV`, `JCP`, `SLSQP`, `MDD`, `MAR`, `CVaR`, `LSTM`, `PPO`, `DQN`, `HTTP`, `JSON`, `CSV`, `CSRF`, `SHA-256`); (c) remover `etl` e `mas` da lista caso não sejam usadas no corpo (hoje `ETL` e `MAS` **não aparecem uma única vez** no texto!); (d) executar `makeglossaries main` (ou `makeindex -s main.ist -t main.alg -o main.acr main.acn`) no pipeline de compilação.
2. **PADRÃO T2 (Crítico) — Uso indevido de `\paragraph{}` gerando numeração `x.y.0.0.z` no Sumário e no corpo:** a classe `eic-bcc-tcc.cls:558-559` define `\setcounter{secnumdepth}{5}` e `\setcounter{tocdepth}{5}` e formata `\paragraph` como seção quinária numerada. Como os autores usaram `\paragraph{...}` diretamente sob `\section` ou `\subsection`, surgiram **34 entradas quebradas com zeros intermediários** no Sumário e no corpo (`5.3.0.0.1`–`5.3.0.0.4`, `5.5.0.0.1`–`5.5.0.0.5`, `5.8.0.0.1`–`5.8.0.0.7`, `6.2.0.0.1`–`6.2.0.0.5`, `6.4.3.0.1`–`6.4.3.0.7`, `6.5.0.0.1`–`6.5.0.0.2`, `7.2.0.0.1`–`7.2.0.0.4`), além de 13 avisos do `hyperref`. **Ação:** trocar todos os `\paragraph{Título.}` por `\paragraph*{Título.}` (ou `\noindent\textbf{Título.}` — que preserva o recuo de 1,5 cm se usado `\textbf{Título.}` no início do parágrafo), ou promover a `\subsection` / `\subsubsection` onde couber divisão formal.
3. **PADRÃO T3 (Médio) — Inconsistência sistemática de itálico em estrangeirismos:** o texto mistura sistematicamente termos em inglês ora em itálico, ora em romano. **Regra proposta:** colocar em `\textit{...}` todo termo estrangeiro não dicionarizado no português (inclusive *replay*, *pipeline*, *framework*, *features*, *frontend*, *stack*, *gates*, *spread*, *z-score*, *momentum*, *backtesting*, *bootstrap*, *drawdown*, *benchmark*, *overfitting*), exceto nomes próprios de bibliotecas/plataformas/carteiras (Chart.js, LangGraph, Buy \& Hold, Equal Weight 63d, Bootstrap A). Desvios encontrados:
   - `replay`: itálico 2× (`04:84`, `05:14`), romano 95× (decidir: como nome próprio da campanha "Replay Contínuo" fica em romano; como termo comum "o *replay*" fica em itálico — hoje `main.tex:56`, `01:10,33,37`, `03:50,56,98`, `04:215,349`, `05:18,49,75,79,81,113,170,196,219`, `06:11,13,18,179,184,194,199,204`, `07:12,14,18,47,53,61` usam em romano).
   - `pipeline` (romano 9×: `01:8,17,37`, `04:33,40,42,44,68,150`, `07:10`), `framework` (romano 2×: `04:40,368`), `frontend` (romano: `04:22,366`), `stack` (romano: `04:14`), `gates` (romano: `04:364`), `corpus` (romano: `03:46`, `05:205` — palavra latina, deve ir em itálico: `\textit{corpus}`).
   - `features`: itálico 1× (`05:205`), romano 7× (`04:109,150,152,156,180,270`).
   - `momentum`: itálico 8× (`02:78`, `05:44,75,217`, `07:20,63`), romano 4× (`01:28`, `02:16,50,56`).
   - `spread`: itálico 5× (`04:216`, `05:190,213`, `06:196`, `07:51`), romano 1× (`02:143`).
   - `z-score`: itálico 3× (`03:33,37,74`), romano 1× (`02:60`).
   - `drawdown`: itálico 18×, romano 2× (`replay-drawdown.tex:9,35`).
   - `Sharpe ratio` / `Sortino ratio`: itálico minúsculo em `02:133,140`, romano maiúsculo `Sharpe Ratio`/`Sortino Ratio` em `01:28,29`, `04:98`, `05:44,45,56,115,124`, `07:10`, e `índice de Sharpe` em `03:8,18,37`.
   - `Buy \& Hold`: itálico em `04:242`, romano em 47 ocorrências; `Buy and Hold` em `02:30,31` e `04:90`.
4. **PADRÃO T4 (Médio) — Inconsistência lexical e de nomes de entidades:**
   - `superajuste` (`main.tex:56`, `01:4,35`) vs `sobreajuste` (`03:12,50`, `05:207`, `07:48`) → padronizar **sobreajuste**.
   - `Bootstrap A` (10×) vs `\textit{bootstrap} A` (`bootstrap-replay.tex:4`) → padronizar **Bootstrap A**.
   - `Equal Weight 63d` (26×) vs `Equal Weight` (`main.tex:56,61`, `06:58`) vs `pesos iguais` (`03:84`, `04:92,242`, `05:75,108,217`, `06:68,71,92`) → usar **Equal Weight 63d** para a carteira do replay (definindo na primeira menção que é a carteira de pesos iguais rebalanceada a cada 63 pregões) e "pesos iguais" apenas para o conceito genérico.
   - `Mínima Variância 252/63` (16×) vs `Mínima Variância` (`main.tex:56`, `05:75`, `06:58`) vs `mínima variância` (`03:84`, `04:90,92,242`) → idem.
   - `piso núcleo` (`04:337`, `06:177,179`) vs `piso de posição-núcleo` (`06:165,175`, `07:36,64`) → padronizar **piso de posição-núcleo** (ou definir "piso núcleo" uma vez e manter).
   - `valor-$p$` / `valores-$p$` (10×) vs `p-valores` (`bootstrap-replay.tex:33`) → padronizar **valor-$p$ / valores-$p$**.
   - `TCC1` (`05:16,41`) → **TCC 1** (ou `\gls{tcc}~1`).
   - `R\$ 2.000,00` (`04:301`) vs `R\$ 2.000` (`04:288`, `06:138,147,151,179`) e `R\$ 100.000,00` vs `R\$ 100 mil` (`main.tex:56`, `replay-patrimonio.tex:35`) → padronizar casas decimais de valores monetários em prosa (ex.: com `,00` em especificações contratuais e tabelas; sem `,00` apenas quando acompanhado de "mil").
   - Uso frequente de códigos internos `DP-11`, `DP-20`, `DP-27`, `DP-30`, `DP-31`, `DP-33`, `DP-34`, `DP-35`, `DP-36`, `DP-37` (25 ocorrências em Caps. 4, 5 e 6) como se o leitor conhecesse `docs/DIRECAO_DO_PROJETO.md`: a banca lê o PDF, não o repositório. Explicar a regra substantiva no texto e, se desejar manter o rastreio, mover o mapeamento `DP-n` para nota de rodapé ou Apêndice.
5. **PADRÃO T5 (Médio) — Referências internas a arquivos/caminhos em fontes de tabelas e legendas:** `Tabela 6.1` (`06:36`) e `Tabela 6.5` (`06:126`) citam *"Fonte: documento mestre do replay (`evolucao_replay_v1_v2_v3_tcc.md`, Seção 1.2), a partir de `operacoes_v3.csv`"*, e `Tabelas 6.2–6.4` citam `daily.csv das campanhas REPLAY-01 a REPLAY-03`. Em uma monografia impressa, a fonte deve seguir a ABNT ("Fonte: elaborado pelos autores com base nos dados oficiais da B3 (COTAHIST) e nos registros das campanhas do Replay Contínuo."), podendo citar o repositório ou apêndice de artefatos de forma limpa.

---

### Capítulo 0 — Elementos Pré-Textuais, Resumo e Abstract (`main.tex`)

- **C0-01** · **Severidade:** Crítico  
  **Local:** `main.tex:19-27` e `main.tex:67` (p. 8 do PDF — página em branco)  
  **Trecho:** `\newacronym{tcc}{TCC}{Trabalho de Conclusão de Curso}` ... `\listofacronymspage`  
  **Problema:** Nenhum acrônimo é referenciado via `\gls{...}` em toda a monografia, deixando `main.acn` com 0 bytes e produzindo uma **página completamente em branco** no lugar da Lista de Acrônimos (p. 8 do PDF). Além disso, `etl` e `mas` estão declarados mas nunca ocorrem como siglas no texto, enquanto siglas usadas (`B3`, `COTAHIST`, `OHLCV`, `JCP`, `SLSQP`, `MDD`, `MAR`, `CVaR`, `LSTM`, `PPO`, `DQN`, `HTTP`, `JSON`, `CSV`, `CSRF`, `SHA-256`) não estão declaradas.  
  **Correção proposta:** Declarar os acrônimos usados em `main.tex`, remover os não usados (`etl`, `mas`), empregar `\gls{...}` no corpo (ou `\glsaddall` caso prefira controlar manualmente as expansões, embora `\gls{}` seja o recomendado pelo manual EIC/BCC, p. 4) e incluir `makeindex -s main.ist -t main.alg -o main.acr main.acn` (ou `makeglossaries main`) na compilação.

- **C0-02** · **Severidade:** Alto  
  **Local:** `main.tex:37` (efeito em todo o PDF, e.g., págs. 20, 23, 24, 25, 31, 34, 41, 53 do texto / págs. 32–65 do PDF)  
  **Trecho:** `\usepackage[htt]{hyphenat} % hifeniza \texttt e permite quebra após \_`  
  **Problema:** Gera 31 avisos `Font shape T1/cmtt/... undefined` no `main.log` e faz o LaTeX inserir um hífen literal logo após o sublinhado ao quebrar identificadores de código (`b3_-calendar.py`, `technical_-analyst.py`, `HARD_ASSET_VOLATILITY_-RULE`, `NO_-ANALYSIS`, `H2_SCIENTIFIC_SHARPE_-DEFINITION_V1`), corrompendo visualmente os nomes de arquivos e constantes.  
  **Correção proposta:** Remover `\usepackage[htt]{hyphenat}` e usar `\usepackage{xurl}` / `\path{...}` (do pacote `url`, já carregado pela classe) ou `\texttt` com `\allowbreak` após `_` (definindo `\let\oldunderscore\_\renewcommand{\_}{\oldunderscore\allowbreak}` em macro própria `\code{...}`), que quebra a linha após `_` **sem** inserir hífen espúrio e sem alertas de fonte.

- **C0-03** · **Severidade:** Alto  
  **Local:** `main.tex:43` (p. 9 do PDF — Sumário)  
  **Trecho:** `\renewcommand{\cfttoctitlefont}{\hspace{0.4\textwidth}\large\bfseries}`  
  **Problema:** Enquanto `LISTA DE FIGURAS` e `LISTA DE TABELAS` usam `\hfill` (ficando centralizadas), `SUMÁRIO` usa `\hspace{0.4\textwidth}` fixo e aparece visivelmente deslocado para a esquerda no PDF (p. 9).  
  **Correção proposta:** Substituir `main.tex:43` por:
  ```latex
  \renewcommand{\cfttoctitlefont}{\hfill\large\bfseries}
  \renewcommand{\cftaftertoctitle}{\hfill}
  ```

- **C0-04** · **Severidade:** Alto  
  **Local:** `main.tex:56` e `main.tex:61` (págs. 4 e 5 do PDF — Resumo e Abstract)  
  **Trecho:** `A v1 terminou em $-17{,}82\%$, abaixo das cinco referências, e nenhum de seus contrastes rejeitou a hipótese nula; a SMA 50/200 tampouco superou a Equal Weight. A v3 terminou em $+0{,}07\%$, acima de quatro referências e abaixo da Bollinger 20/2 ($+4{,}89\%$), resultado otimista por construção.`  
  **Problema:** O Resumo (266 palavras, dentro do limite de 500 da ABNT NBR 6028 e do manual EIC/BCC) e o Abstract (251 palavras) apresentam a v1 e a v3, mas **omitem completamente o resultado da v2** ($-14{,}26\%$, ainda abaixo das cinco referências), suavizando involuntariamente a trajetória iterativa. Além disso, `main.tex:56` escreve `replay` sem itálico enquanto `backtesting` e `bootstrap` estão em itálico, e `main.tex:61` traduz `R\$ 100 mil` como `BRL 100,000` (adequado), mas `Equal Weight` e `Mínima Variância` aparecem sem os sufixos `63d` e `252/63` adotados no resto do texto.  
  **Correção proposta:** Ajustar o trecho no Resumo (e espelhar no Abstract) para:
  > `A v1 terminou em $-17{,}82\%$ e a v2 em $-14{,}26\%$, ambas abaixo das cinco referências, e nenhum contraste da v1 rejeitou a hipótese nula; a SMA 50/200 tampouco superou a Equal Weight 63d. A v3 terminou em $+0{,}07\%$, acima de quatro referências e abaixo da Bollinger 20/2 ($+4{,}89\%$), resultado otimista por construção.`
  E grafar `\textit{replay}` em `main.tex:56` (e adicionar `63d` / `252/63` na enumeração das referências).

- **C0-05** · **Severidade:** Médio  
  **Local:** `main.tex:9-11` e `main.tex:38-40` (preâmbulo)  
  **Trecho:** `\newcommand{\warn}[1]{{\color{red} {#1}}}` / `\newcommand{\verify}[1]{{\color{blue} {#1}}}` / `\newcommand{\remarks}[2]{{\color{red} #1\ (\textit{#2})}}` e `% ponytail: a classe usa...`  
  **Problema:** Macros mortas de rascunho (herdadas do TCC 1) e comentário interno de agente (`% ponytail:`) permanecem no arquivo principal da versão de defesa.  
  **Correção proposta:** Remover as linhas 9–11 (não usadas em nenhum capítulo) e reescrever o comentário das linhas 38–40 em nota técnica neutra (`% Contorno para incompatibilidade de \MakeUppercase sem argumento no tocloft (MiKTeX 2026).`).

- **C0-06** · **Severidade:** Baixo  
  **Local:** `main.tex:57` e `main.tex:62` (págs. 4 e 5 do PDF)  
  **Trecho:** `\palavraschave{Análise Quantitativa. Sistemas Multiagentes. Large Language Models. Backtesting. Mercado Acionário Brasileiro.}`  
  **Problema:** No Resumo em português, os termos estrangeiros `Large Language Models` e `Backtesting` nas palavras-chave estão em romano, enquanto no parágrafo logo acima aparecem em itálico; além disso, pela ABNT NBR 6028:2021 (atualização vigente — *verificar no manual do CEFET/RJ* qual edição adotam, pois o PDF EIC/BCC 2025 exemplifica ponto final e maiúsculas iniciais), a separação passou a ponto e vírgula em minúsculas. Mantendo o padrão do template EIC/BCC (ponto final), recomenda-se ao menos pôr `\textit{Large Language Models}` e `\textit{Backtesting}` em itálico nas palavras-chave em português.  
  **Correção proposta:** `\palavraschave{Análise Quantitativa. Sistemas Multiagentes. \textit{Large Language Models}. \textit{Backtesting}. Mercado Acionário Brasileiro.}`

---

### Capítulo 1 — Introdução (`chapters/01-introducao.tex`)

- **C1-01** · **Severidade:** Crítico  
  **Local:** `chapters/01-introducao.tex:28-29` (p. 3 do texto / p. 15 do PDF)  
  **Trecho:** `\item \textbf{H1:} Será avaliado se estratégias baseadas em momentum e \textit{trend following} apresentam desempenho superior...` e `\item \textbf{H2:} Será avaliado se o sistema multiagente baseado em LLMs apresenta desempenho superior...`  
  **Problema:** Dois defeitos simultâneos: (1) metodologicamente, *"Será avaliado se..."* não é uma hipótese científica falseável, mas uma meta/questão de pesquisa em voz passiva futura (já inadequada num TCC 2 concluído); (2) **inconsistência direta com o Capítulo 5 (`05-metodologia.tex:44-45`)**, onde H1 e H2 já estão redigidas na forma declarativa correta (*"estratégias baseadas em momentum e trend following apresentam desempenho superior..."*), embora ambos os capítulos digam preservar as hipóteses do TCC 1!  
  **Correção proposta:** Uniformizar `01-introducao.tex:28-29` com a formulação declarativa do Cap. 5 (mantendo exatamente o conteúdo proposicional do TCC 1, apenas removendo o invólucro "Será avaliado se"):
  ```latex
  \item \textbf{H1:} Estratégias baseadas em \textit{momentum} e \textit{trend following} apresentam desempenho superior ao \textit{equal weight} em termos de índice de Sharpe líquido.
  \item \textbf{H2:} O sistema multiagente baseado em \glspl{llm} apresenta desempenho superior ajustado ao risco em relação aos \textit{benchmarks} considerados, tomando como critério principal o índice de Sharpe líquido e, como critérios complementares, o índice de Sortino, o \textit{Maximum Drawdown} e o \textit{turnover}.
  ```

- **C1-02** · **Severidade:** Alto  
  **Local:** `chapters/01-introducao.tex:37` (final do Cap. 1 — p. 3 do texto / p. 15 do PDF)  
  **Trecho:** (ausência de seção/nota sobre uso de IA)  
  **Problema:** O guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, Seção 2.5, p. 7) recomenda explicitamente declarar na Introdução como ferramentas de IA generativa foram utilizadas na elaboração da monografia, quando aplicável. Dada a natureza do tema (agentes LLM) e a organização do repositório, omitir essa declaração pode gerar questionamento desnecessário da banca.  
  **Correção proposta:** Verificar com o orientador e, se aplicável, adicionar ao final do Capítulo 1 um parágrafo ou subseção curta de transparência seguindo o modelo do manual EIC/BCC (p. 7), distinguindo o uso de LLMs como *objeto de estudo* do eventual apoio de ferramentas de IA na revisão textual/organização, sob autoria e verificação integral dos discentes.

- **C1-03** · **Severidade:** Médio  
  **Local:** `chapters/01-introducao.tex:8` e `01-introducao.tex:10` (págs. 1–2 do texto / págs. 13–14 do PDF)  
  **Trecho:** L8: *"Para viabilizar essa análise empírica, o trabalho desenvolve um artefato metodológico que integra... permitindo uma mensuração rigorosa..."* (frases de 76 e 190 palavras no parágrafo L10).  
  **Problema:** Períodos excessivamente longos (uma frase de 76 palavras na L8; uma frase de 78 palavras na L10 dentro de um parágrafo de 190 palavras que mistura duas ideias centrais distintas: o abandono do protocolo confirmatório original e a definição do Replay Contínuo + acompanhamento prospectivo). O manual EIC/BCC (p. 1) exige uma única ideia central por parágrafo e frases curtas.  
  **Correção proposta:** Quebrar L10 em dois parágrafos: o primeiro encerrando a transição do protocolo original para o Replay Contínuo e apresentando o universo/período/referências; o segundo apresentando as três versões (v1 pré-especificada vs v2/v3 exploratórias) e o papel do acompanhamento prospectivo iniciado em 14/10/2026.

- **C1-04** · **Severidade:** Médio  
  **Local:** `chapters/01-introducao.tex:18` (p. 2 do texto / p. 14 do PDF)  
  **Trecho:** `\item Implementar um motor de \textit{backtesting} e um livro contábil de eventos auditável que incorporem custos de transação, proventos e as métricas de risco definidas no protocolo experimental;`  
  **Problema:** Contradição sutil com `05-metodologia.tex:131,144`: no protocolo experimental, apenas o Sharpe foi congelado como definição científica; Sortino e *turnover* são parâmetros técnicos do módulo (e o giro do replay difere da função `turnover` do motor).  
  **Correção proposta:** Trocar o trecho final por: `"...e as métricas de desempenho e risco empregadas na avaliação experimental;"`.

- **C1-05** · **Severidade:** Baixo  
  **Local:** `chapters/01-introducao.tex:4,6,8,35` (págs. 1 e 3 do texto / págs. 13 e 15 do PDF)  
  **Trecho:** `superajuste` (L4, L35), `pipeline` (L8, L17, L37 sem itálico), `replay` (L10, L33, L37 sem itálico), `momentum` (L28 sem itálico), ausência de seções internas no Cap. 1.  
  **Problema:** Aplica-se aos Padrões T3 e T4; além disso, o Cap. 1 é o único capítulo sem subdivisão em seções (o manual EIC/BCC, págs. 6–7, sugere Motivação, Definição do Problema, Objetivos e Estrutura — opcional, mas facilita a leitura).  
  **Correção proposta:** Uniformizar `sobreajuste`, `\textit{pipeline}`, `\textit{replay}` e `\textit{momentum}`; opcionalmente subdividir o Cap. 1 em `1.1 Motivação e Problema`, `1.2 Objetivos e Hipóteses` e `1.3 Organização do Trabalho`.

*Balanço micro do Cap. 1:* **19 parágrafos/itens revisados** (10 parágrafos em prosa + 9 itens de lista); **9 apresentaram problemas** (L4, L6, L8, L10, L17, L18, L28, L29, L35/37 — principalmente enunciação de H1/H2, extensão de períodos, desalinhamento menor do Obj. 2 e padrão de estrangeirismos).

---

### Capítulo 2 — Fundamentação Teórica (`chapters/02-fundamentacao.tex`)

- **C2-01** · **Severidade:** Crítico  
  **Local:** `chapters/02-fundamentacao.tex:6,20,82,88` (págs. 4 e 7 do texto / págs. 16 e 19 do PDF)  
  **Trecho:** L6: `formalizada por \citep{Fama1970}` · L20: `Estudos de \citep{Shiller2000} e \citep{Thaler1993}` · L82: `O modelo de três fatores de \citep{FamaFrench1993}` · L88: `Posteriormente, \citep{FamaFrench2015} expandiram o modelo.`  
  **Problema:** Erro gramatical e de citação LaTeX: `\citep` gera citação entre colchetes (`formalizada por [Fama, 1970]`, `Estudos de [Shiller, 2000] e [Thaler, 1993]`, `Posteriormente, [Fama and French, 2015] expandiram`), tornando a frase sintaticamente defeituosa ao transformar a citação parentética em sujeito ou complemento preposicionado.  
  **Correção proposta:** Substituir `\citep` por `\citet` (ou `\citeonline`) nas quatro ocorrências: `formalizada por \citet{Fama1970}`, `Estudos de \citet{Shiller2000} e \citet{Thaler1993}`, `O modelo de três fatores de \citet{FamaFrench1993}` e `Posteriormente, \citet{FamaFrench2015} expandiram o modelo.` (Caso a Seção 2.4 seja removida conforme C2-02, L82 e L88 desaparecem.)

- **C2-02** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:80-89` (p. 7 do texto / p. 19 do PDF)  
  **Trecho:** `\section{FACTOR INVESTING E MODELOS DE PRECIFICAÇÃO DE ATIVOS}` ... `R_i - R_f = \beta_m (R_m - R_f) + \beta_s SMB + \beta_v HML`  
  **Problema:** Seção de apenas 7 linhas herdada do TCC 1 sobre *Factor Investing* (Fama-French 3 e 5 fatores), tema que **não é utilizado em nenhum módulo, estratégia ou experimento do Hedge-fund-lab** (violando a orientação explícita do manual EIC/BCC, p. 8: *"Limite-se exclusivamente aos temas utilizados em seu trabalho"*). Além disso, nenhum símbolo da Equação (2.6) ($R_i, R_f, \beta_m, R_m, \beta_s, SMB, \beta_v, HML$) é definido.  
  **Correção proposta:** **Excluir integralmente a Seção 2.4** (e remover `FamaFrench1993` e `FamaFrench2015` de `references.bib` caso deixem de ser citados; manter `Gu2020`, que já é citado e discutido adequadamente no Cap. 3, L16).

- **C2-03** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:122-143` (págs. 9–10 do texto / págs. 21–22 do PDF)  
  **Trecho:** Seções 2.7 e 2.8 (ausência de base teórica para inferência estatística)  
  **Problema:** O trabalho decide suas hipóteses H1, H2 e H0 por **bootstrap estacionário pareado** \citep{Politis1994}, **teste de interseção–união**, **procedimento sequencial de Holm** \citep{Holm1979} e **estatística assintótica do Sharpe** \citep{Lo2002}, além de depender de forma decisiva do comportamento do Sharpe sob retornos médios negativos. Nenhum desses conceitos é fundamentado no Capítulo 2 — eles caem de paraquedas apenas no Capítulo 5!  
  **Correção proposta:** Acrescentar ao Cap. 2 uma seção `2.8 Inferência Estatística e Comparação Múltipla em Séries Financeiras` (1,5–2 páginas) apresentando: (i) dependência serial em retornos financeiros e o *bootstrap* estacionário de \citet{Politis1994}; (ii) erro-padrão do Sharpe em amostras finitas \citep{Lo2002} e anomalia de ordenação sob retornos negativos; (iii) inflação do erro de tipo I em múltiplas comparações, ajuste de \citet{Holm1979} e lógica do teste de interseção–união.

- **C2-04** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:106-121` vs `chapters/03-relacionados.tex:26-34` (págs. 8–9 e 13 do texto / págs. 20–21 e 25 do PDF)  
  **Trecho:** L120: `\citet[p. 1]{FinCoT2025} evidenciam que... a acurácia de alinhamento financeiro de modelos gerais de ponta se eleva drasticamente, com melhorias reportadas de 63,2\% para 80,5\%.`  
  **Problema:** (1) A Seção 2.6 duplica quase literalmente o conteúdo de `Xia2026`, `Li2023`, `Xing2024` e `FinCoT2025` (inclusive a exata estatística "63,2% para 80,5%") que volta a aparecer na Seção 3.3–3.4 do capítulo seguinte; (2) cada subseção 2.6.1, 2.6.2 e 2.6.3 é o resumo de um único artigo isolado, sem diálogo entre autores; (3) apenas esses 4 parágrafos usam paginação em citações indiretas (`p. 1`, `p. 5, p. 9` — esta última com `p.` duplicado); (4) o advérbio `"drasticamente"` é enfático/não acadêmico e `pré-definidos` viola o VOLP (**predefinidos**).  
  **Correção proposta:** Reescrever a Seção 2.6 de forma puramente conceitual (sem repetir resultados empíricos de artigos específicos, que pertencem ao Cap. 3), explicando os blocos teóricos: arquitetura multiagente baseada em LLMs (papéis/personas), agregação por votação/autoconsistência vs debate, raciocínio estruturado (*Chain-of-Thought*) e governança determinística de saídas estruturadas. Remover o `p. 1` / `p. 5, p. 9` das paráfrases e substituir `"se eleva drasticamente"` e `"pré-definidos"`.

- **C2-05** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:44-77, 94-96, 133-137` (págs. 6–10 do texto / págs. 18–22 do PDF)  
  **Trecho:** Eqs. (2.1)–(2.5), (2.7) e (2.8): `MA_t = ...`, `Momentum_t = ...`, `BB_{upper} = MA + k\sigma`, `\sigma_p^2 = w^T \Sigma w`, `R_{acum} = ...`, `S = \frac{E[R_p - R_f]}{\sigma_p}`.  
  **Problema:** (1) Variáveis não definidas no texto: $P_t$, $n$, $k$, $w$, $\Sigma$, $R_p$, $R_f$, $\sigma_p$, $R_t$ e $T$ aparecem sem definição explícita; (2) palavras de múltiplas letras em modo matemático sem `\text{}`/`\mathrm{}` (`MA`, `Momentum`, `BB_{upper}`, `BB_{lower}`, `R_{acum}`) renderizam como produto de variáveis em itálico; (3) a Eq. (2.8) apresenta o Sharpe populacional sem anualização, enquanto a Eq. (5.2) usa o estimador amostral anualizado por $\sqrt{252}$ com $r_f=0$, sem ponte explícita entre as duas notações; (4) `Sortino`, `Maximum Drawdown` e `turnover` em 2.8.2–2.8.3 ficam sem equações (enquanto o Cap. 5 dá a equação de Sortino e Giro).  
  **Correção proposta:** Usar `\mathrm{SMA}_t`, `\mathrm{BB}_{\mathrm{sup}}`, `\mathrm{BB}_{\mathrm{inf}}`, `R_{\mathrm{acum}}`, definir cada variável imediatamente após sua equação com `\noindent em que ...` (eliminando `onde` na L66), e alinhar a notação de Sharpe/Sortino/MDD com o Cap. 5 (ou deixar as definições teóricas em 2.8 e referenciá-las em 5.5).

- **C2-06** · **Severidade:** Médio  
  **Local:** `chapters/02-fundamentacao.tex:4-24` e `02-fundamentacao.tex:103-104` (págs. 4 e 8 do texto / págs. 16 e 20 do PDF)  
  **Trecho:** `2.1 HIPÓTESE DE EFICIÊNCIA DE MERCADO` → única subseção `2.1.1 Críticas Comportamentais...`; `2.5.2 Relação Risco-Retorno` (1 frase única de 25 palavras).  
  **Problema:** (1) Violação da ABNT NBR 6024: a seção 2.1 possui apenas uma subseção (2.1.1); (2) a subseção 2.5.2 tem uma única frase trivial que repete a abertura da Seção 2.8 (`02:130`); (3) a L24 afirma sem citação que *"modelos adaptativos e multiagentes podem capturar padrões dinâmicos e interpretar contextos que estratégias estáticas ou puramente matemáticas não conseguem identificar"* — afirmação forte e especulativa em desacordo com o próprio resultado empírico do trabalho!  
  **Correção proposta:** (1) Criar `2.1.1 Fundamentos da Hipótese de Eficiência de Mercado` antes da atual `2.1.2` (ou eliminar o nível de subseção em 2.1); (2) remover `2.5.2` fundindo sua ideia em `2.8`; (3) moderar L24 para:
  > `Sob essa perspectiva, investiga-se se sistemas adaptativos baseados em inteligência artificial e modelos de linguagem conseguem integrar sinais heterogêneos de modo mais flexível que regras estáticas, hipótese cuja validade depende de verificação empírica rigorosa.`

- **C2-07** · **Severidade:** Médio  
  **Local:** `chapters/02-fundamentacao.tex:28,31` (p. 5 do texto / p. 17 do PDF)  
  **Trecho:** L28: `...facilita o contraste com abordagens mais complexas \citep{Markowitz1952, Clarke2006, LopezDePrado2018}.` · L31: `\textit{Buy and Hold}... após a consideração de risco e custos operacionais \citep{LopezDePrado2018, Bailey2017}.`  
  **Problema:** Citações imprecisas: `Markowitz1952` e `Clarke2006` não tratam de "benchmarks simples menos dependentes de estimação" (ao contrário, tratam de otimização por variância — quem defende o *benchmark* ingênuo sem estimação é `DeMiguel2009`!). E `Bailey2017` trata de *Probability of Backtest Overfitting*, não de *Buy and Hold*.  
  **Correção proposta:** Em L28, citar `\citep{DeMiguel2009, LopezDePrado2018}`; em L31, citar `\citep{LopezDePrado2018}` para o rigor de custos/risco em *backtesting* e retirar `Bailey2017` da definição de *Buy and Hold*.

- **C2-08** · **Severidade:** Médio  
  **Local:** `chapters/02-fundamentacao.tex:12,66,124,143` (págs. 4, 6, 9, 10 do texto / págs. 16, 18, 21, 22 do PDF)  
  **Trecho:** L12: `Forma semi-forte`; L66: `onde $\mu$ representa a média móvel e $\sigma$ o desvio padrão.`; L124: `risco de \textit{overfitting}, onde resultados positivos`; L143: `(corretagem, spread e emolumentos)`.  
  **Problema:** Quatro deslizes gramaticais/ortográficos: (1) `semi-forte` perdeu o hífen no Acordo Ortográfico (**semiforte**); (2) `onde` nas linhas 66 e 124 não se refere a lugar físico (correto: **em que**); (3) `desvio padrão` sem hífen em L66 diverge de `desvio-padrão` em L133; (4) `spread` sem itálico em L143 diverge das 5 ocorrências em itálico nos Caps. 4–7. Além disso, `02:38-42` cita `\citet{Brock1992}` duas vezes seguidas com a mesma ideia e `02:130` e `02:140` têm parágrafos curtos de 1–2 frases.  
  **Correção proposta:** Corrigir para `Forma semiforte`, `\noindent em que $\mu$ representa a média móvel e $\sigma$, o desvio-padrão.`, `risco de \textit{overfitting}, no qual resultados positivos`, e `(corretagem, \textit{spread} e emolumentos)`.

*Balanço micro do Cap. 2:* **37 parágrafos/itens revisados** (34 parágrafos em prosa + 3 itens de lista); **24 apresentaram problemas** (citações `\citep` mal-empregadas, variáveis não definidas, seção *Factor Investing* irrelevante, duplicação com Cap. 3, subseção única, ortografia/regência e ausência de fundamentação estatística).

---

### Capítulo 3 — Trabalhos Relacionados (`chapters/03-relacionados.tex`)

- **C3-01** · **Severidade:** Crítico  
  **Local:** `chapters/03-relacionados.tex:62-90` (p. 17 do texto / p. 29 do PDF — Tabela 3.1)  
  **Trecho:** `\begin{tabular}{>{\raggedright\arraybackslash}p{1.9cm} ... p{1.8cm} ... p{2.0cm} ...}`  
  **Problema:** (1) **Colisão literal de palavras no cabeçalho da Tabela 3.1 no PDF:** `"MultiagenteCustos"` (estouro de `9,36 pt`) e `"RastreabilidadeReferências"` (estouro de `21,51 pt`), além de a tabela ultrapassar a margem direita; (2) a tabela flutua para a p. 17, **interrompendo uma frase da Seção 3.8** (`"...sobre a mesma [Tabela 3.1] trajetória de mercado..."`) em vez de permanecer na Seção 3.7 (`Quadro Comparativo`); (3) a linha do Hedge-fund-lab escreve `"pesos iguais, mínima variância"` em vez dos nomes oficiais `Equal Weight 63d` e `Mínima Variância 252/63`.  
  **Correção proposta:** (1) Usar `\scriptsize` ou ambiente `tabularx` com `\textwidth` (ou rotacionar com `sidewaystable` / ajustar larguras para soma $\le 14{,}8\text{ cm}$ descontando `14\tabcolsep`), abreviando os cabeçalhos problemáticos (`Multiagente` → `Multi-agente` ou largura `2.0cm`; `Rastreabilidade das decisões` → `Rastreabilidade` em `2.3cm` ou `\hspace{0pt}` para permitir hifenização na primeira palavra da célula!); (2) manter a tabela na Seção 3.7 (usando `\usepackage{placeins}` + `\FloatBarrier` ao fim da Seção 3.7 ou `[ht!]` após ajustar altura); (3) substituir `"pesos iguais, mínima variância"` por `"Equal Weight 63d, Mínima Variância 252/63"`.

- **C3-02** · **Severidade:** Alto  
  **Local:** `chapters/03-relacionados.tex:50` vs `03-relacionados.tex:100` (págs. 15 e 18 do texto / págs. 27 e 30 do PDF)  
  **Trecho:** L50: `Por isso, o projeto reserva a avaliação confirmatória de agentes ao acompanhamento prospectivo e trata o replay retrospectivo como estudo exploratório.` · L100: `apenas a versão pré-especificada (v1) recebe decisão inferencial sobre as hipóteses, e a avaliação plenamente confirmatória dos agentes, livre de contaminação, permanece reservada ao acompanhamento prospectivo.`  
  **Problema:** Leve contradição interna no próprio capítulo: na L50, todo o replay é classificado genericamente como "estudo exploratório", o que entra em tensão com a L100 (e os Caps. 1, 5 e 6), onde a v1 é distinguida como execução pré-especificada com decisão inferencial sobre H2. Um membro da banca focado em metodologia apontará imediatamente essa oscilação.  
  **Correção proposta:** Alinhar L50 com L100:
  > `Por isso, no replay retrospectivo, apenas a versão pré-especificada (v1) recebe decisão inferencial condicionada ao período, tratando-se as iterações subsequentes (v2 e v3) como exploratórias e reservando-se a avaliação plenamente confirmatória, livre de contaminação do modelo, ao acompanhamento prospectivo.`

- **C3-03** · **Severidade:** Médio  
  **Local:** `chapters/03-relacionados.tex:4` (p. 11 do texto / p. 23 do PDF)  
  **Trecho:** `Este capítulo revisa a literatura que dialoga diretamente com o Hedge-fund-lab, organizada em seis frentes...`  
  **Problema:** O capítulo faz um excelente mapeamento temático com síntese crítica ao final de cada seção (ponto positivo!), mas não informa **como os trabalhos foram selecionados** (bases consultadas, recorte temporal, critérios de inclusão/exclusão), elemento explicitamente sugerido pelo manual do curso (`Trabalho de Conclusao EIC BCC.pdf`, p. 9).  
  **Correção proposta:** Acrescentar 3–4 linhas ao parágrafo introdutório de `03-relacionados.tex:4` explicando o critério de curadoria (busca direcionada em periódicos de finanças quantitativas, conferências de IA/ML — NeurIPS, ICML, ICLR, KDD, EMNLP — e preprints recentes no arXiv até 2026, priorizando estudos com negociação em circuito fechado, arquiteturas multiagentes baseadas em LLMs e auditorias de contaminação/sobreajuste).

- **C3-04** · **Severidade:** Médio  
  **Local:** `chapters/03-relacionados.tex:10, 18, 26, 35` (págs. 11–13 do texto / págs. 23–25 do PDF)  
  **Trecho:** L10: `DQN`, `TDQN`, `PPO`; L18: `LSTM`; L26: `CFA`; L35: `CVaR`; L48: `ARIMA`, `XGBoost`; L54: `GSM8K`.  
  **Problema:** Oito siglas técnicas aparecem sem expansão no primeiro uso e sem entrada na Lista de Acrônimos. Além disso, L26 repete quase palavra por palavra o resultado do `FinCoT2025` ("63,2% para 80,5%") já citado em `02-fundamentacao.tex:120` (que deve sair do Cap. 2 conforme C2-04).  
  **Correção proposta:** Expandir na primeira ocorrência (ex.: *Deep Q-Network* — DQN; *Proximal Policy Optimization* — PPO; *Long Short-Term Memory* — LSTM; *Conditional Value at Risk* — CVaR; *Chartered Financial Analyst* — CFA) e incluí-las na Lista de Acrônimos se recorrentes.

- **C3-05** · **Severidade:** Baixo  
  **Local:** `chapters/03-relacionados.tex:28` (p. 13 do texto / p. 25 do PDF)  
  **Trecho:** `O levantamento de \citet{Xia2026} sistematiza 185 estudos... Entre os 80 estudos empíricos analisados em detalhe...`  
  **Problema:** Os números 185/80 correspondem à **versão 2** (`arXiv:2605.19337v2`, out./2026), ao passo que o PDF arquivado localmente em `tcc2/referencia/` é a versão 1 (`v1`, mai./2026, com 77/19 estudos) e `references.bib` não indica a versão.  
  **Correção proposta:** Atualizar `references.bib` para explicitar `arXiv:2605.19337v2` (e substituir a cópia de arquivo em `tcc2/referencia/` se desejado pelos autores, fora do escopo desta revisão).

*Balanço micro do Cap. 3:* **25 parágrafos revisados**; **8 apresentaram problemas** (L4 critério de busca, L10/18/26/35/48/54 siglas sem expansão, L50 tensão sobre estatuto do replay, L62–90 colisão/flutuação da Tabela 3.1). No geral, é um dos capítulos mais bem escritos da monografia.

---

### Capítulo 4 — Arquitetura e Implementação (`chapters/04-arquitetura.tex`)

- **C4-01** · **Severidade:** Crítico  
  **Local:** `chapters/04-arquitetura.tex:72` (p. 20 do texto / p. 32 do PDF)  
  **Trecho:** `A série de preço científica de referência (\texttt{H\_real}) corresponde ao ativo PETR4.SA, com 1519 sessões no intervalo de 2018-01-12 a 2024-02-28, cobrindo 2649 barras oficiais.`  
  **Problema:** **Erro factual triplo**, verificado diretamente em `H2_METHODOLOGICAL_FREEZE_V1.md` (Seções 7 e 8 e Emenda 1, linhas 131–198 e 420–432): (1) `H_real` **não** é a série de preços de referência, mas sim um conjunto de **4 sessões reais** extraídas nos quantis 0,20, 0,40, 0,60 e 0,80 para a fase de *Hardening* (`H = 8 H_syn + 4 H_real`); (2) **1.519 sessões** (12/01/2018 a 28/02/2024) é o conjunto de sessões elegíveis de desenvolvimento (`|E|`), que atendem ao histórico mínimo de 504 sessões; (3) **2.649 barras oficiais** correspondem ao *snapshot* completo de PETR4.SA (de **04/01/2016 a 31/08/2026**), e não ao intervalo 2018–2024 (que tem apenas 1.519 sessões — é aritmeticamente impossível 1.519 sessões "cobrirem" 2.649 barras!). Além disso, mistura formato de data ISO (`2018-01-12`) quando o resto do trabalho usa `DD/MM/AAAA`.  
  **Correção proposta:** Substituir L72 por:
  > `O \textit{snapshot} científico de referência para o caminho de ativo único (\texttt{PETR4.SA}) reúne 2.649 barras oficiais no intervalo de 04/01/2016 a 31/08/2026. Desse conjunto, 1.519 sessões (de 12/01/2018 a 28/02/2024) satisfazem o requisito mínimo de 504 sessões prévias de aquecimento para a janela de desenvolvimento, da qual foram reservadas quatro sessões reais (\texttt{H\_real}) para a etapa de \textit{Hardening}.`

- **C4-02** · **Severidade:** Crítico  
  **Local:** `chapters/04-arquitetura.tex:74, 113, 262` (págs. 20, 23 e 30 do texto / págs. 32, 35 e 42 do PDF)  
  **Trecho:** L74: `\texttt{src/backtesting/b3\_calendar.py}` (+33,49 pt!); L113: `\texttt{src/agents/graph.py}` (+11,42 pt); L262: `\texttt{/laboratory/replay/v2/}` (+6,50 pt).  
  **Problema:** Três estouros visíveis de margem direita (até 33,5 pt ≈ 1,2 cm além da mancha gráfica na p. 20!) somados à inserção de hífens falsos após `_` (`b3_-calendar.py`) causada por `hyphenat`.  
  **Correção proposta:** Além de remover `hyphenat` (C0-02), reformular a ordem das palavras ou tirar caminhos longos para parênteses/apêndice; por exemplo, em L74:
  > `O calendário de negociação é implementado pela classe \texttt{B3Calendar} (no módulo \texttt{b3\_calendar.py} de \texttt{src/backtesting}), que aplica as regras históricas de feriados da B3 e reproduz as 2.649 sessões oficiais.`

- **C4-03** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:150` e `04-arquitetura.tex:336-339` (págs. 24 e 32–33 do texto / págs. 36 e 44–45 do PDF)  
  **Trecho:** L150: `oito features adimensionais (\texttt{rsi}, \texttt{sma50\_gap}, \texttt{sma200\_gap}, \texttt{bb\_upper\_gap}, \texttt{bb\_lower\_gap}, \texttt{bb\_width}, \texttt{macd\_ratio} e \texttt{macd\_signal\_ratio})`  
  **Problema:** **Lacuna crítica de reprodutibilidade:** o texto cita essas oito *features* e aplica limiares numéricos exatos sobre elas em L336–339 (`bb_lower_gap < 0,035`, `bb_upper_gap >= -0,02`, `sma200_gap > -0,08`), mas **nunca define matematicamente nenhuma das oito variáveis** nem sua convenção de sinal (ex.: `bb_upper_gap` negativo significa fechamento abaixo da banda superior; `bb_lower_gap` positivo significa fechamento acima da banda inferior). Sem isso, um leitor não consegue interpretar nem reproduzir as regras da v3.  
  **Correção proposta:** Incluir em 4.7.1 (ou em tabela concisa/Apêndice A referenciado em 4.7.1) a definição matemática exata das oito *features* adimensionais e da volatilidade anualizada de 21 pregões, indicando a convenção de sinal de cada *gap*.

- **C4-04** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:126-135` (p. 23 do texto / p. 35 do PDF — Figura 4.2)  
  **Trecho:** `\draw[arr] (rm) -- node[above, sloped, pos=0.55, font=\footnotesize] {veredito = \texttt{APROVADO}} (pm);`  
  **Problema:** No PDF (p. 35), o rótulo inclinado `veredito = APROVADO` **colide com a borda superior da caixa `portfolio_manager`**; além disso, nenhuma das três figuras do capítulo (4.1, 4.2 e 4.3) nem nenhuma das três tabelas (4.1, 4.2 e 4.3) possui indicação de **Fonte:** abaixo (padrão ABNT NBR 14724).  
  **Correção proposta:** Na Fig. 4.2, usar caminho ortogonal (`(rm.west) -| node[above, pos=0.25, font=\footnotesize] {veredito = \texttt{APROVADO}} (pm.north)`), eliminando a colisão e a rotação; adicionar `\par\smallskip\footnotesize Fonte: elaborado pelos autores.` abaixo das Figuras 4.1–4.3 e das Tabelas 4.1–4.3.

- **C4-05** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:242` (p. 28 do texto / p. 40 do PDF)  
  **Trecho:** `podem ser produzidas isoladamente (\texttt{--references-only})`  
  **Problema:** No PDF (p. 40), o duplo hífen `--` dentro de `\texttt{--references-only}` sofreu ligadura de fonte T1 e foi renderizado como **travessão curto** (`–references-only`), produzindo uma *flag* de linha de comando sintaticamente inválida! Na mesma linha, `\textit{Buy \& Hold}` está em itálico (única ocorrência no texto) e `pesos iguais e mínima variância` destoam dos nomes oficiais `Equal Weight 63d` e `Mínima Variância 252/63`.  
  **Correção proposta:** Trocar `\texttt{--references-only}` por `\texttt{-{}-references-only}` (ou descrever em prosa *"em modo exclusivo de referências"*, sem nome de *flag* de CLI no corpo!), retirar o itálico de `Buy \& Hold` e usar `Equal Weight 63d` e `Mínima Variância 252/63`.

- **C4-06** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:4` e todo o capítulo (págs. 19–35 do texto / págs. 31–47 do PDF)  
  **Trecho:** L4: `O conteúdo foi produzido a partir de auditoria do código-fonte (\texttt{src/}, \texttt{dashboard/}, \texttt{tests/}, \texttt{scripts/}) e dos documentos técnicos do projeto, sem reexecução de experimentos.`  
  **Problema:** (1) **Tom de relatório de auditoria técnica / README**, não de monografia acadêmica ("produzido a partir de auditoria do código-fonte... sem reexecução de experimentos" soa como parecer de um agente externo auditando o repositório, e não dos próprios autores descrevendo o sistema que construíram!); (2) extensão excessiva (~5.447 palavras / 17 páginas, com >45 nomes literais de arquivos `.py`, funções e constantes internas).  
  **Correção proposta:** Reescrever L4 em voz acadêmica autoral:
  > `Este capítulo apresenta a arquitetura e a implementação do Hedge-fund-lab, limitando-se estritamente aos componentes efetivamente construídos e verificados no sistema.`
  E executar a redução estrutural proposta na Seção 3.3 (mover inventário de `src/experiments`, detalhes de empacotamento/rotas e Tabela 4.3 para Apêndice A).

- **C4-07** · **Severidade:** Médio  
  **Local:** `chapters/04-arquitetura.tex:272-333` (págs. 31–32 do texto / págs. 43–44 do PDF — Tabelas 4.2 e 4.3)  
  **Trecho:** Tabela 4.2: `R\$ 2.000`, `(\texttt{strict=False})`; Tabela 4.3: coluna `Valor` mistura `0,30`, `2.000,00`, `8`, `0,25/0,15` sem coluna de unidade.  
  **Problema:** Na Tabela 4.3, a coluna `Valor` mistura frações decimais (`0,30` em vez de `30%`), reais (`2.000,00`), sessões inteiras (`8`) e pares (`0,25/0,15`) sem unidade explícita no cabeçalho ou nos valores. Na Tabela 4.2, a notação `R$ 2.000` difere de `R$ 2.000,00` usada no texto logo abaixo (`04:301`), e `\texttt{strict=False}` é jargão de código que pode ser expresso em linguagem arquitetural ("ajusta e registra violações de regra").  
  **Correção proposta:** Na Tabela 4.3 (se mantida no corpo ou movida ao Apêndice A), explicitar unidades em cada valor (`30\%`, `22\%`, `R\$ 2.000,00`, `8\%`, `45\%`, `8 pregões`, `25\%`, `35\%`, `12\%`, `25\% / 15\%`).

- **C4-08** · **Severidade:** Médio  
  **Local:** `chapters/04-arquitetura.tex:48-70` (p. 21 do texto / p. 33 do PDF — Figura 4.1)  
  **Trecho:** Diagrama TikZ mostrando apenas `COTAHIST B3` + `yfinance` → `B3OfficialAdjustedExtractor` → `SQLite (SQLAlchemy)`.  
  **Problema:** A Figura 4.1 retrata apenas o *pipeline* científico do caminho legado de ativo único (`src/pipeline` + SQLAlchemy), mas **não mostra a separação RAW B3 vs fator ajustado Yahoo** da base local multiativos (`DP-27`, L77) que de fato alimenta o Replay Contínuo e o acompanhamento diário! O leitor fica com um diagrama apenas do caminho que não chegou ao Teste Final.  
  **Correção proposta:** Ampliar a Fig. 4.1 (ou criar uma segunda ramificação clara no mesmo diagrama) exibindo a saída dupla da base multiativos: (i) preços **RAW B3** → execução e marcação no livro de eventos SQLite; (ii) preço ajustado (**RAW B3 $\times$ fator Yahoo**) → cálculo de indicadores e sinais.

- **C4-09** · **Severidade:** Baixo  
  **Local:** `chapters/04-arquitetura.tex:14, 152, 217, 252, 349-355` (págs. 19, 24, 27, 29, 34 do texto)  
  **Trecho:** L14: `Stack implementado` (anglicismo sem itálico no título da Tabela 4.1); L72/74: `1519` e `2649` sem ponto de milhar vs `8.192` (`04:146`) com ponto de milhar; L152: `10001 a 10005` sem ponto (aceitável por serem códigos/sementes, mas manter critério); L351: `"alerta de tese velha"` (jargão informal do projeto sem definição no texto!).  
  **Problema:** Um membro da banca lerá `"alerta de tese velha"` (`04:215, 351`) sem saber o que significa quantitativamente (DP-33 define como desvio $> 3\sigma$ desde o fechamento ajustado anterior!).  
  **Correção proposta:** Trocar `Stack implementado` por `Pilha tecnológica implementada` (ou `\textit{Stack} implementado`), uniformizar separador de milhar (`1.519` e `2.649`), e definir brevemente `"alerta de tese velha"` na primeira ocorrência (`04:215` ou `351`: *"alerta de defasagem de tese, disparado quando a cotação se afasta mais de $3\sigma$ do fechamento anterior"*).

*Balanço micro do Cap. 4:* **70 parágrafos/itens revisados** (62 parágrafos em prosa + 8 itens de lista); **29 apresentaram problemas** (erro factual `H_real`, estouros de margem em `\texttt`, ligadura `–references-only`, falta de fórmulas das 8 *features*, tom de relatório de auditoria, referências a `DP-n` não autossuficientes, "alerta de tese velha" indefinido, inconsistência de estrangeirismos e excesso de granularidade de arquivos `.py`).

---

### Capítulo 5 — Metodologia Experimental (`chapters/05-metodologia.tex`)

- **C5-01** · **Severidade:** Crítico  
  **Local:** `chapters/05-metodologia.tex:75, 77, 79, 83, 115, 124, 133, 135, 137, 205, 207, 209, 211, 213, 215, 217` (págs. 39–47 do texto / págs. 51–59 do PDF)  
  **Trecho:** `\paragraph{H1.}`, `\paragraph{Sharpe Ratio líquido (critério primário).}`, `\paragraph{Contaminação do modelo e antecipação de informação.}` (16 ocorrências).  
  **Problema:** Ver Padrão T2: gera 16 entradas deformadas `5.3.0.0.1` a `5.8.0.0.7` no Sumário e no corpo, mais 6 avisos do `hyperref`.  
  **Correção proposta:** Substituir os 16 `\paragraph{...}` por `\noindent\textbf{...}` (ou transformar os 4 blocos de 5.3 e os 5 de 5.5 em `\subsection` reais sem ponto final no título, e os 7 de 5.8 em `\begin{itemize}` ou `\textbf{...}` sem numeração no Sumário).

- **C5-02** · **Severidade:** Crítico  
  **Local:** `chapters/05-metodologia.tex:188` (p. 45 do texto / p. 57 do PDF)  
  **Trecho:** `A série de desenvolvimento (\texttt{H\_real}) tinha 1519 sessões, de 12/01/2018 a 28/02/2024.`  
  **Problema:** Repete o mesmo erro factual de `C4-01`: `H_real` não é a série de desenvolvimento de 1.519 sessões, mas o subconjunto de 4 sessões reais reservadas para *Hardening* dentro do conjunto elegível de 1.519 sessões (`|E|`) do *snapshot* de 2.649 barras.  
  **Correção proposta:** Reescrever para:
  > `A janela elegível de desenvolvimento reunia 1.519 sessões (12/01/2018 a 28/02/2024), extraídas do \textit{snapshot} de 2.649 sessões de PETR4.SA, das quais quatro sessões reais (\texttt{H\_real}) foram reservadas para a etapa de \textit{Hardening}.`

- **C5-03** · **Severidade:** Alto  
  **Local:** `chapters/05-metodologia.tex:41-47` vs `chapters/01-introducao.tex:25-31` (p. 38 do texto / p. 50 do PDF)  
  **Trecho:** `As hipóteses do TCC1 são preservadas: \item \textbf{H1:} estratégias baseadas em \textit{momentum}...`  
  **Problema:** O texto de H1 e H2 em `05-metodologia.tex:44-45` é declarativo (correto!), mas **não coincide literalmente** com `01-introducao.tex:28-29` ("Será avaliado se..."). Além disso, grafa `TCC1` sem espaço (L16, L41).  
  **Correção proposta:** Corrigir o Cap. 1 para coincidir exatamente com o enunciado declarativo do Cap. 5 (C1-01) e grafar `TCC 1` (ou primeira etapa do `\gls{tcc}`).

- **C5-04** · **Severidade:** Alto  
  **Local:** `chapters/05-metodologia.tex:63-73, 113` (págs. 38 e 41 do texto / págs. 50 e 53 do PDF)  
  **Trecho:** Tabela 5.1 (`Overfull \hbox 8.17pt too wide`), Tabela 5.2 (`1.86pt`), e L113 `\texttt{tcc2/scripts/metricas\_replay.py}` (`13.30pt too wide`).  
  **Problema:** Estouro de margem direita na Tabela 5.1 (colunas somam `14.6cm + 8\tabcolsep > \textwidth`) e na linha 113; além disso, nenhuma das duas tabelas (5.1 e 5.2) possui linha de `Fonte:` (ABNT).  
  **Correção proposta:** Reduzir a largura das colunas da Tabela 5.1 em `0.4cm` no total (ou usar `tabularx` com `\textwidth`), adicionar `\par\smallskip\footnotesize Fonte: elaborado pelos autores.` às Tabelas 5.1 e 5.2, e reformular L113 para evitar `\texttt` longo no fim da linha (ex.: `O cálculo reprodutível das métricas do replay é executado pelo script \texttt{metricas\_replay.py} (em \texttt{tcc2/scripts/}), que valida por asserções...`).

- **C5-05** · **Severidade:** Alto  
  **Local:** `chapters/05-metodologia.tex:170` e `05-metodologia.tex:219` (págs. 43–44 e 47–48 do texto / págs. 55–56 e 59–60 do PDF)  
  **Trecho:** L170: parágrafo monolítico de **276 palavras** (da p. 43 à p. 44); L219: última frase do capítulo isolada sozinha na **página 48** (`inferencial restrita aos contrastes pré-especificados e sujeita às ameaças acima.`).  
  **Problema:** (1) L170 empilha três ideias centrais distintas em um bloco de 276 palavras (adaptação de $R=3$ para $R=1$; teste inverso $p_- / U_{95}$; consequências de baixo poder e limitações do *bootstrap* não studentizado); (2) a página 48 do texto (p. 60 do PDF) é uma página inteira em branco contendo **uma única linha viúva**!  
  **Correção proposta:** Dividir L170 em três parágrafos coesos (~90 palavras cada), e ao remover os `\paragraph{}` que hoje inserem `1.5em` extras de espaçamento vertical em 16 pontos do capítulo (C5-01), a linha viúva da p. 48 desaparecerá naturalmente (caso persista, adicionar `\widowpenalty=10000\clubpenalty=10000` no preâmbulo ou enxugar 1 linha em 5.8).

- **C5-06** · **Severidade:** Médio  
  **Local:** `chapters/05-metodologia.tex:113-145` (págs. 41–42 do texto / págs. 53–54 do PDF)  
  **Trecho:** Eq. (5.4): `\text{Giro} = \frac{C / 0{,}0003}{\overline{PL}}`; L133–135 sem fórmulas de MDD, retorno anualizado e volatilidade; L36 sem fórmula explícita do retorno diário simples.  
  **Problema:** (1) Na Eq. (5.4), `PL` está em itálico matemático (`\overline{PL}` = produto $P \cdot L$) em vez de `\overline{\mathrm{PL}}`; (2) para reprodutibilidade integral (Eixo 5), faltam as fórmulas curtas do retorno diário simples ($r_t = \mathrm{PL}_t/\mathrm{PL}_{t-1} - 1$), retorno anualizado, volatilidade anualizada e *Maximum Drawdown*; (3) L144 explica que o arredondamento ao centavo gera erro de até R\$ 16,67 por operação (`0,005 / 0,0003 = 16,666...`) — excelente detalhe! — mas deveria indicar que sobre 86 operações o erro máximo acumulado no volume é insignificante frente a R\$ 614,7 mil (<0,25\%).  
  **Correção proposta:** Corrigir `\overline{\mathrm{PL}}` na Eq. (5.4), explicitar $r_t = \mathrm{PL}_t/\mathrm{PL}_{t-1} - 1$ em L36 e incluir as fórmulas compactas de MDD e retorno anualizado em 5.5.

- **C5-07** · **Severidade:** Baixo  
  **Local:** `chapters/05-metodologia.tex:194` (p. 45 do texto / p. 57 do PDF)  
  **Trecho:** `autorizada apenas pelo autor e sem ratificação acadêmica.`  
  **Problema:** O trabalho tem **dois autores** (Lucas e Matheus); `"pelo autor"` no singular gera dúvida e soa impessoalmente inconsistente.  
  **Correção proposta:** Substituir `"autorizada apenas pelo autor"` por `"executada internamente pelos autores, sem ratificação formal da orientação"`.

*Balanço micro do Cap. 5:* **64 parágrafos/itens revisados** (40 parágrafos em prosa + 24 itens de lista); **24 apresentaram problemas** (16 `\paragraph` no Sumário, erro factual `H_real`, estouros de margem, parágrafo de 276 palavras, linha viúva na p. 48, `PL` em itálico matemático, falta de figuras metodológicas e singular "pelo autor").

---

### Capítulo 6 — Resultados e Discussão (`chapters/06-resultados.tex`, `tabelas/*.tex`, `figures/*.tex`)

- **C6-01** · **Severidade:** Crítico  
  **Local:** `chapters/06-resultados.tex:52, 54, 56, 58, 60, 167, 169, 171, 173, 175, 177, 179, 184, 186` (págs. 50–61 do texto / págs. 62–73 do PDF)  
  **Trecho:** `\paragraph{Patrimônio e retorno.}`, `\paragraph{Diversidade do comitê.}`, `\paragraph{O que os resultados permitem afirmar.}` (14 ocorrências).  
  **Problema:** Ver Padrão T2: produz 14 entradas quebradas (`6.2.0.0.1`–`6.2.0.0.5`, `6.4.3.0.1`–`6.4.3.0.7`, `6.5.0.0.1`–`6.5.0.0.2`) no Sumário e no corpo, mais 5 avisos do `hyperref`.  
  **Correção proposta:** Substituir os 14 `\paragraph{...}` por `\textbf{...}` (ou promover `6.5.0.0.1` e `6.5.0.0.2` a `\subsection{O que os resultados permitem afirmar}` e `\subsection{O que os resultados não permitem afirmar}`).

- **C6-02** · **Severidade:** Crítico  
  **Local:** `chapters/06-resultados.tex:25-36` (p. 49 do texto / p. 61 do PDF — Tabela 6.1)  
  **Trecho:** `\begin{tabular}{lrrr}` com cabeçalhos `Referência de entrada, 02/04 (R\$)` e `Fechamento, 12/11 (R\$)`.  
  **Problema:** A Tabela 6.1 ultrapassa a margem direita em **25,55 pt (~0,9 cm)** no PDF (p. 61), visivelmente desalinhada da mancha do texto. Além disso, sua `Fonte:` (L36) cita arquivos internos do repositório (`evolucao_replay_v1_v2_v3_tcc.md`, `operacoes_v3.csv`) desconhecidos pelo leitor da monografia.  
  **Correção proposta:** Abreviar cabeçalhos ou quebrar em duas linhas (`\textbf{Entrada (02/04)}` / `\textbf{(R\$)}` ou `Referência 02/04 (R\$)` e `Fechamento 12/11 (R\$)`) com `\setlength{\tabcolsep}{6pt}`, eliminando totalmente o estouro; alterar a fonte para: `Fonte: elaborado pelos autores com base nas cotações oficiais de fechamento da B3 (COTAHIST).`

- **C6-03** · **Severidade:** Alto  
  **Local:** `chapters/06-resultados.tex:204-208` (págs. 62–63 do texto / págs. 74–75 do PDF — Seção 6.6)  
  **Trecho:** `O Buy \& Hold não negociou após a montagem da cesta; sua trajetória, de R\$ 99.835,33 em 14/10 para R\$ 82.391,17 em 16/11 ($-17{,}61\%$), reflete apenas a variação de preços dos cinco ativos. A Multiagentes realizou 19 operações após a entrada e terminou em R\$ 76.059,11 ($-23{,}94\%$). ... Nas duas carteiras, o \textit{drawdown} máximo do período coincide com a perda acumulada, pois o último fechamento é também o vale.`  
  **Problema:** **Três lacunas importantes para a banca:** (1) a Seção 6.6 **não informa qual versão da arquitetura multiagente** estava operando no acompanhamento prospectivo (o código em `dashboard/daily_cycle.py` confirma que é a arquitetura **v1**, sem as regras de v2/v3 — omissão crítica, porque a banca certamente perguntará se $-23{,}94\%$ foi o desempenho da v3 fora da amostra!); (2) a frase `"de R$ 99.835,33 em 14/10 para R$ 82.391,17 em 16/11 (-17,61%)"` induz o leitor a achar que $-17{,}61\%$ é a variação entre 99.835,33 e 82.391,17 (que seria **$-17{,}47\%$**!), quando na verdade $-17{,}61\%$ e $-23{,}94\%$ são medidos sobre o capital inicial de **R\$ 100.000,00** (ancorado no fechamento de 13/10/2026); (3) consequentemente, a frase final sobre o *drawdown* máximo coincidir com a perda acumulada só é verdadeira se a curva incluir o ponto inicial de R\$ 100.000,00 antes de 14/10 (se começar em 14/10, o *drawdown* máximo é $-17{,}47\%$ e $-23{,}82\%$, não $-17{,}61\%$ e $-23{,}94\%$).  
  **Correção proposta:** Reescrever o trecho para:
  > `A carteira Multiagentes do acompanhamento prospectivo opera a arquitetura original (equivalente à v1 do replay, sem as intervenções exploratórias de v2 e v3). O Buy \& Hold não negociou após a montagem da cesta inicial (ancorada em R\$ 100.000,00 ao fechamento de 13/10); sua trajetória — de R\$ 99.835,33 no fechamento de 14/10 para R\$ 82.391,17 em 16/11 ($-17{,}61\%$ sobre o capital inicial) — reflete apenas a variação de preços dos cinco ativos. A Multiagentes realizou 19 operações após a entrada e terminou em R\$ 76.059,11 ($-23{,}94\%$ sobre o capital inicial). ... Nas duas carteiras, tomando-se o capital inicial de R\$ 100.000,00 como pico de partida, o \textit{drawdown} máximo coincide com a perda acumulada, pois o último fechamento (16/11) é também o menor patrimônio da série.`

- **C6-04** · **Severidade:** Alto  
  **Local:** `chapters/tabelas/metricas-replay.tex:11,35` e `chapters/tabelas/bootstrap-replay.tex:4,10,33` (págs. 50 e 53 do texto / págs. 62 e 65 do PDF)  
  **Trecho:** Tabelas 6.2, 6.3 e 6.4 geradas por script, mais `06-resultados.tex:78,85`.  
  **Problema:** (1) **Discrepância aparente de 0,01 em 9 de 16 linhas** entre subtrair os Sharpes arredondados da Tabela 6.2 e ler o $\Delta$ da Tabela 6.4 (ex.: na Tabela 6.2, v3 = `0,09` e SMA 50/200 = `-1,42`, cuja diferença aparente é `1,51`, mas a Tabela 6.4 traz `1,50`, porque $0{,}0862 - (-1{,}4173) = 1{,}5035 \to 1{,}50$; ocorre o mesmo em `v1 vs Boll`, todas as 5 linhas de `v2`, e 4 linhas de `v3`). Um avaliador com calculadora questionará isso se não houver nota explícita! (2) Cabeçalhos das Tabelas 6.2, 6.3 e 6.4 não estão em **negrito**, destoando das outras 8 tabelas da monografia; (3) as legendas das Tabelas 6.2 e 6.4 não têm argumento curto `\caption[...]{...}`, gerando entradas de 5–7 linhas na Lista de Tabelas (p. 7 do PDF); (4) `bootstrap-replay.tex:4` grafa `\textit{bootstrap} A` (em vez de `Bootstrap A`), e a linha 33 usa `p-valores` (em vez de `valores-$p$`).  
  **Correção proposta:** Atualizar os geradores (`metricas_replay.py` e `bootstrap_replay.py`) para: (i) acrescentar na nota da Tabela 6.4: *"As diferenças $\Delta$ são calculadas sobre os índices de Sharpe sem arredondamento prévio, podendo diferir em 0,01 da subtração direta dos valores arredondados da Tabela 6.2."*; (ii) colocar cabeçalhos em `\textbf{...}`; (iii) usar `\caption[Título curto]{Título completo}` nas Tabelas 6.2, 6.3 e 6.4; (iv) padronizar `Bootstrap A`, `valores-$p$` e texto de `Fonte:` sem nomes de CSV internos.

- **C6-05** · **Severidade:** Alto  
  **Local:** `figures/replay-patrimonio.tex`, `figures/replay-drawdown.tex`, `figures/replay-caixa.tex` (págs. 51 e 59 do texto / págs. 63 e 71 do PDF — Figuras 6.1, 6.2 e 6.3)  
  **Trecho:** `xlabel={Pregão (2026)}`, `xticklabels={abr,mai,jun,jul,ago,set,out,nov}`, `ylabel={Drawdown (\%)}`, sem linha de `Fonte:`.  
  **Problema:** (1) Nenhuma das três figuras traz indicação de `Fonte:` abaixo da legenda (ABNT NBR 14724); (2) o eixo X exibe rótulos de meses (`abr` a `nov`), mas seu título diz `Pregão (2026)` (deveria ser `Mês (2026)` ou `Período (2026)`); (3) na Fig. 6.2, `Drawdown` está sem itálico tanto no eixo Y quanto na legenda; (4) na Fig. 6.1 e 6.2, a sobreposição de 8 curvas em tons de preto/cinza dificulta distinguir `Buy & Hold` de `Equal Weight 63d` e `SMA 50/200` de `v2` entre junho e agosto (embora a distinção P&B entre Multiagentes em preto e referências em cinza seja elogiável!).  
  **Correção proposta:** (i) Adicionar `\par\smallskip\footnotesize Fonte: elaborado pelos autores com base nos registros das campanhas do Replay Contínuo (153 pregões).` às três figuras; (ii) alterar `xlabel={Mês (2026)}`; (iii) grafar `\textit{Drawdown}` na Fig. 6.2; (iv) considerar painel duplo (ou leve paleta colorida acessível que preserve os estilos de traço/marcador em P&B) ou destacar apenas as 3 versões + Buy \& Hold + Bollinger 20/2 em um gráfico principal e manter as 8 curvas no complementar.

- **C6-06** · **Severidade:** Médio  
  **Local:** `chapters/06-resultados.tex:152, 195` (págs. 58 e 62 do texto / págs. 70 e 74 do PDF)  
  **Trecho:** L152: `evitaram cerca de R\$ 827,34 de perda adicional`; L195: `Cada campanha realizou cerca de 4.703 chamadas lógicas ao modelo, com custo conhecido estimado de US\$ 7,44 (v1), US\$ 8,92 (v2) e US\$ 8,63 (v3)... A v3 consumiu, assim, cerca de US\$ 8,63`.  
  **Problema:** (1) Usar `"cerca de"` antes de valores precisos até o centavo (`R$ 827,34`, `US$ 8,63`) ou de uma contagem exata (`4.703` — sendo v1=4.703, v2=4.702, v3=4.703) é impropriedade quantitativa; (2) na L195 e na Tabela 6.5 (L123), informa-se apenas o *custo conhecido estimado* (US\$ 7,44 / 8,92 / 8,63), omitindo a *exposição total do orçamento* incluindo reservas por tentativas de resposta incerta (US\$ 8,11 na v1, US\$ 10,03 na v2 e US\$ 8,63 na v3, conforme `evolucao_replay_v1_v2_v3_tcc.md`, §5.9).  
  **Correção proposta:** L152: `evitaram perda adicional estimada em R\$ 827,34 até 12/11`; L195: `As campanhas realizaram 4.703 (v1), 4.702 (v2) e 4.703 (v3) chamadas lógicas ao modelo, com custo conhecido estimado de US\$ 7,44 (exposição total de US\$ 8,11 com reservas de incerteza), US\$ 8,92 (US\$ 10,03) e US\$ 8,63 (US\$ 8,63), respectivamente, não deduzido do patrimônio.`

- **C6-07** · **Severidade:** Médio  
  **Local:** `chapters/06-resultados.tex:46-52` (págs. 50–52 do texto / págs. 62–64 do PDF)  
  **Trecho:** Fim da p. 50 (`6.2.0.0.1 Patrimônio e retorno.` + 4 linhas) interrompido pela página de floats p. 51 (Figs. 6.1 e 6.2), retomando no meio da lista na p. 52.  
  **Problema:** A leitura do primeiro parágrafo interpretativo da Seção 6.2 fica partida ao meio por duas figuras de página inteira. Além disso, na L52 e L165/175 há mistura de sinal `+` em texto (`+4,89\%`, `+R\$ 3.222,19`) com `$-$` em modo matemático (`$-4{,}19\%$`, `$-$R\$ 4.819,69`), e na L175 `84,4\%` usa 1 casa decimal enquanto todas as demais porcentagens usam 2 casas (`84,40\%`).  
  **Correção proposta:** Colocar as Figs. 6.1 e 6.2 após o fechamento do parágrafo "Patrimônio e retorno" (ou ao fim de 6.2), padronizar sinais (`$+$` / `$-$`) e grafar `84,40\%`.

- **C6-08** · **Severidade:** Baixo  
  **Local:** `chapters/06-resultados.tex:126` (p. 56 do texto / p. 68 do PDF — Tabela 6.5)  
  **Trecho:** `Posição entre as seis carteiras: 6.ª | 6.ª | 2.ª` e `Fonte: documento mestre do replay (evolucao_replay_v1_v2_v3_tcc.md...)`  
  **Problema:** (1) `Fonte:` cita documento interno não anexado à monografia (Padrão T5); (2) no texto de `06:52` as carteiras são ordenadas entre **oito** (3 versões + 5 referências), enquanto a Tabela 6.5 ordena dentro de cada campanha de **seis** (versão + 5 referências) — vale esclarecer na nota da tabela ("posição dentro da respectiva campanha de seis carteiras") para não confundir o leitor; (3) ordinais `6.ª` / `2.ª` usam ponto (padrão luso; no Brasil prefere-se `6ª` / `2ª`, mas manter consistência com `4751.ª` em `05:164`).  
  **Correção proposta:** Ajustar nota e `Fonte:` da Tabela 6.5 para `Fonte: elaborado pelos autores a partir dos registros auditados das campanhas do Replay Contínuo. Posição relativa às seis carteiras de cada campanha; pareceres completos: 765 (v1), 760 (v2) e 745 (v3).`

*Balanço micro do Cap. 6:* **55 parágrafos/itens revisados** (38 parágrafos em prosa + 17 itens de lista); **23 apresentaram problemas** (14 `\paragraph` no Sumário, estouro da Tabela 6.1, falta de versão v1 e ambiguidade de base em 6.6, discrepância não explicada de 0,01 entre Tabelas 6.2 e 6.4, falta de `Fonte:` em Figs. 6.1–6.3, `"cerca de"` + centavos, exposição total de orçamento omitida e fontes internas).

---

### Capítulo 7 — Conclusão (`chapters/07-conclusao.tex`)

- **C7-01** · **Severidade:** Crítico  
  **Local:** `chapters/07-conclusao.tex:20, 22, 24, 26` (págs. 65–66 do texto / págs. 77–78 do PDF)  
  **Trecho:** `\paragraph{H1.}`, `\paragraph{H2.}`, `\paragraph{H0.}`, `\paragraph{Versões exploratórias.}`  
  **Problema:** Ver Padrão T2: gera 4 entradas `7.2.0.0.1`–`7.2.0.0.4` no Sumário e no corpo, mais 2 avisos do `hyperref`.  
  **Correção proposta:** Substituir por `\textbf{H1.}`, `\textbf{H2.}`, `\textbf{H0.}` e `\textbf{Versões exploratórias.}` no início dos respectivos parágrafos (ou promovê-los a `\subsection` sem ponto final).

- **C7-02** · **Severidade:** Alto  
  **Local:** `chapters/07-conclusao.tex:8-15` (p. 64 do texto / p. 76 do PDF — Seção 7.1)  
  **Trecho:** `O trabalho desenvolveu o Hedge-fund-lab...` (síntese genérica sem checagem explícita dos 6 objetivos específicos).  
  **Problema:** O manual oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, p. 13) determina: *"Nas conclusões, analisa-se o que era desejado (definido na introdução com os objetivos), comparando com o que foi alcançado pelo TCC, descrevendo como os objetivos foram alcançados e o porquê de algum objetivo não ter sido alcançado."* O Capítulo 7 responde muito bem às perguntas e hipóteses, mas **não retoma explicitamente os 6 objetivos específicos** do Cap. 1 (especialmente o Obj. 2, cujas métricas não congeladas divergem parcialmente do protocolo, e o Obj. 6, cujos 23 pregões prospectivos da Seção 6.6 ficam ausentes da Conclusão).  
  **Correção proposta:** Incluir na Seção 7.1 uma tabela compacta ou lista objetiva `Objetivo específico → Atendimento e evidência` fechando explicitamente os 6 objetivos do Cap. 1 (incluindo o registro preliminar dos 23 pregões do acompanhamento prospectivo em 14/10–16/11/2026: Multiagentes v1 em $-23{,}94\%$ vs Buy \& Hold em $-17{,}61\%$).

- **C7-03** · **Severidade:** Médio  
  **Local:** `chapters/07-conclusao.tex:22` (p. 65 do texto / p. 77 do PDF)  
  **Trecho:** `a v1 teve o maior \textit{drawdown} máximo entre as seis carteiras ($-22{,}90\%$) e o maior giro (6,78 vezes o patrimônio médio).`  
  **Problema:** No Cap. 6 (`06:54,56,80`), o texto refere-se a "oito carteiras" (v1, v2, v3 + 5 referências); aqui escreve "seis carteiras" (a campanha v1 + 5 referências). Embora ambas sejam verdadeiras (v1 foi pior nos dois conjuntos), a troca súbita de "oito" para "seis" sem explicação gera ruído.  
  **Correção proposta:** Escrever: `"a v1 teve o maior \textit{drawdown} máximo ($-22{,}90\%$) e o maior giro (6,78 vezes o patrimônio médio) tanto entre as seis carteiras de sua campanha quanto no conjunto das oito trajetórias analisadas."`

- **C7-04** · **Severidade:** Médio  
  **Local:** `chapters/07-conclusao.tex:42-55` (p. 67 do texto / p. 79 do PDF — Seção 7.4)  
  **Trecho:** Lista de 7 limitações reproduzindo quase integralmente `05-metodologia.tex:205-217` e `06-resultados.tex:188-197`.  
  **Problema:** Terceira repetição quase literal da mesma lista de limitações em 22 páginas, além de repetir `"cerca de US\$ 8,63"` (L51) e omitir as duas limitações apontadas na Seção 3.5 (viés de seleção/sobrevivência do universo de 5 *blue chips* e efeito do CDI positivo sobre $r_f=0$).  
  **Correção proposta:** Condensar 7.4 em dois parágrafos sintéticos (agrupando limitações de *validade interna* — contaminação, ajuste *in-sample*, intervenções em bloco, $R=1$ — e de *validade externa/realismo* — amostra única, 5 *blue chips* sem deslistadas, execução simplificada e $r_f=0$ frente ao CDI), corrigindo `"cerca de US\$ 8,63"` para `"custo conhecido estimado de US\$ 8,63"`.

- **C7-05** · **Severidade:** Baixo  
  **Local:** `chapters/07-conclusao.tex:6` (p. 64 do texto / p. 76 do PDF)  
  **Trecho:** `Este capítulo sintetiza o que foi construído, responde à pergunta de pesquisa, às hipóteses H1, H2 e H0 e à pergunta arquitetural formuladas no Capítulo~\ref{cha:introducao}, e registra as limitações do estudo e os trabalhos futuros que delas decorrem.`  
  **Problema:** Meta-texto introdutório dispensável (frase-roteiro que apenas lê em voz alta os títulos das seções 7.1–7.5 logo abaixo).  
  **Correção proposta:** Remover L6 ou iniciar diretamente com a síntese substantiva da Seção 7.1 (o mesmo vale para `06-resultados.tex:13`).

*Balanço micro do Cap. 7:* **31 parágrafos/itens revisados** (18 parágrafos em prosa + 13 itens de lista); **11 apresentaram problemas** (4 `\paragraph` no Sumário, falta de fechamento explícito dos 6 objetivos, oscilação seis vs oito carteiras, repetição de limitações com "cerca de US$ 8,63", meta-texto em L6 e omissão do resultado preliminar prospectivo).

---

## 5. Figuras e Tabelas (Eixo 4)

### 5.1 Inventário do que existe

| Elemento | Cap. / Pág. PDF | Citado antes? | Interpretado no texto? | Legenda autoexplicativa? | Fonte ABNT abaixo? | Problemas no PDF |
|---|---|:---:|:---:|:---:|:---:|---|
| **Fig. 4.1** (`fig:pipeline`) | Cap. 4 / p. 33 | Sim (p. 32) | Parcial (só ativo único) | Sim (mas longa na LOF) | **Não (Falha)** | Omite a ramificação multiativos RAW vs ajustado (`DP-27`); sem `Fonte:`. |
| **Fig. 4.2** (`fig:grafo-langgraph`) | Cap. 4 / p. 35 | Sim (p. 35) | Sim | Sim (mas longa na LOF) | **Não (Falha)** | Rótulo `veredito = APROVADO` **colide** com a caixa `portfolio_manager`; sem `Fonte:`. |
| **Fig. 4.3** (`fig:fluxo-multiativos`) | Cap. 4 / p. 38 | Sim (p. 36) | Sim | Sim (muito boa; longa na LOF) | **Não (Falha)** | Boa clareza e P&B; apenas `anal-istas` mal hifenizado (resolvido ao recompilar em PT) e sem `Fonte:`. |
| **Fig. 6.1** (`fig:replay-patrimonio`) | Cap. 6 / p. 63 | Sim (p. 62) | Sim | Sim | **Não (Falha)** | P&B legível mas 8 curvas emboladas (BH vs EW e v2 vs SMA); eixo X diz `Pregão (2026)` com rótulos de meses; sem `Fonte:`. |
| **Fig. 6.2** (`fig:replay-drawdown`) | Cap. 6 / p. 63 | Sim (p. 62) | Sim | Sim | **Não (Falha)** | Mesmo emaranhado de 8 curvas; `Drawdown` sem itálico no eixo e legenda; eixo X `Pregão (2026)`; sem `Fonte:`. |
| **Fig. 6.3** (`fig:replay-caixa`) | Cap. 6 / p. 71 | Sim (p. 70) | Sim | Sim | **Não (Falha)** | Excelente leitura em P&B! Apenas eixo X `Pregão (2026)` e sem `Fonte:`. |
| **Tab. 3.1** (`tab:relacionados`) | Cap. 3 / p. 29 | Sim (p. 28) | Sim | Sim | Sim | **Crítico:** colisão `MultiagenteCustos` e `RastreabilidadeReferências`; estouro +21,5 pt; flutua para o meio da Seção 3.8. |
| **Tab. 4.1** (`tab:stack`) | Cap. 4 / p. 31 | Sim (p. 31) | Sim | Sim | **Não (Falha)** | Leve overfull (+1,24 pt); `Stack` sem itálico; sem `Fonte:`. |
| **Tab. 4.2** (`tab:evolucao-versoes`) | Cap. 4 / p. 43 | Sim (p. 43) | Sim | Sim | **Não (Falha)** | Muito útil e bem composta; falta `Fonte:` e padronizar `R$ 2.000,00`. |
| **Tab. 4.3** (`tab:constantes-v3`) | Cap. 4 / p. 44 | Sim (p. 44) | Sim | Sim | **Não (Falha)** | Sem unidade na coluna `Valor` (mistura fração, R$ e pregões); candidata a **Apêndice A**; sem `Fonte:`. |
| **Tab. 5.1** (`tab:met-hipoteses`) | Cap. 5 / p. 50 | Sim (p. 50) | Sim | Sim | **Não (Falha)** | Estouro +8,17 pt; sem `Fonte:`. |
| **Tab. 5.2** (`tab:met-referencias`) | Cap. 5 / p. 53 | Sim (p. 52) | Sim | Sim | **Não (Falha)** | Estouro +1,86 pt; sem `Fonte:`. |
| **Tab. 6.1** (`tab:res-mercado`) | Cap. 6 / p. 61 | Sim (p. 61) | Sim | Sim | Sim (mas interna) | **Crítico:** estouro +25,55 pt; fonte cita arquivo `.md`/`.csv` interno. |
| **Tab. 6.2** (`tab:replay-risco`) | Cap. 6 / p. 62 | Sim (p. 62) | Sim | Sim (longa na LOT) | Sim (mas interna) | Cabeçalhos sem negrito; `\resizebox` reduz a fonte; sigla `MDD` não definida antes; fonte cita `daily.csv`. |
| **Tab. 6.3** (`tab:replay-operacoes`) | Cap. 6 / p. 62 | Sim (p. 62) | Sim | Sim (longa na LOT) | Sim (mas interna) | Cabeçalhos sem negrito; `\resizebox`; coluna `Giro` sem unidade (`×`); fonte cita `daily.csv`. |
| **Tab. 6.4** (`tab:replay-bootstrap`) | Cap. 6 / p. 65 | Sim (p. 65) | Sim | Sim (7 linhas na LOT!) | Sim (mas interna) | Cabeçalhos sem negrito; falta nota sobre arredondamento de 0,01 vs Tab. 6.2; `\textit{bootstrap} A` e `p-valores` inconsistentes. |
| **Tab. 6.5** (`tab:res-evolucao`) | Cap. 6 / p. 68 | Sim (p. 68) | Sim | Sim | Sim (mas interna) | Muito clara! Apenas limpar `Fonte:` interna e esclarecer "6 carteiras da campanha". |

### 5.2 Arquivos órfãos encontrados em `tcc2/figures/` e `tcc2/images/`

Três arquivos de imagem estão no diretório da monografia mas **não são referenciados em nenhum `.tex`**:
- `tcc2/figures/figure.png` (94 KB — imagem placeholder do template EIC/BCC) → **excluir**.
- `tcc2/images/grafo-langgraph.png` (104 KB — substituída pelo diagrama TikZ da Fig. 4.2) → **excluir** (ou arquivar fora de `images/`).
- `tcc2/images/pipeline-etl.png` (45 KB — diagrama legado do Prefect/PostgreSQL do TCC 1, substituído pela Fig. 4.1) → **excluir**.

### 5.3 Figuras que faltam (propostas concretas)

Hoje há 6 figuras, concentradas apenas nos Caps. 4 e 6; os Caps. 1, 2, 3, 5 e 7 não têm nenhuma. Os Caps. 1, 2, 3 e 7 não exigem figuras obrigatoriamente (no Cap. 3 a Tabela 3.1 cumpre bem o papel comparativo), mas o **Capítulo 5** e o **Capítulo 6** ganham enorme clareza com três figuras objetivas:

1. **Nova Fig. 5.1 (Cap. 5, Seção 5.2) — *Linha do tempo e desenho experimental pareado do estudo***
   - **Conteúdo:** diagrama TikZ em duas faixas horizontais: (a) eixo temporal situando o aquecimento dos indicadores (450 dias corridos), o corte de conhecimento declarado do `gemini-3.8-flash` (mar./2026), a janela do Replay Contínuo (06/04–12/11/2026, 153 pregões), as datas reais de execução de v1/v2/v3 (13, 15 e 16/11/2026 — deixando visualmente evidente a natureza retrospectiva!) e a janela do acompanhamento diário prospectivo (14/10–16/11/2026 em diante); (b) diagrama pareado mostrando o capital/cesta inicial comum dividindo-se nas 6 carteiras (Multiagentes v1/v2/v3 + 5 referências) → série de 153 retornos pareados → Bootstrap A (H1 e H2 v1 inferenciais; v2/v3 descritivos).
   - **Fonte dos dados:** parâmetros do protocolo e datas registradas em `05-metodologia.tex` e `evolucao_replay_v1_v2_v3_tcc.md`.
2. **Nova Fig. 6.4 (Cap. 6, Seção 6.4) — *Evolução do perfil do comitê (distribuição de placares 5–0, 4–1, 3–2 e sem consenso) e inversão do RSI médio de compra e venda entre v1, v2 e v3***
   - **Conteúdo:** gráfico `pgfplots` em dois painéis lado a lado (P&B com hachuras/tons de cinza): esquerda — barras empilhadas dos placares do comitê (83,01\% → 15,13\% → 4,03\% de unanimidade 5–0); direita — barras pareadas do RSI médio de compras vs vendas executadas (60,51/36,06 → 58,54/40,98 → 39,26/69,00). Visualiza instantaneamente o achado central da pergunta arquitetural!
   - **Fonte dos dados:** Seções 5.4 e 5.5 de `tcc2/evidence/04-replay-abril-novembro/relatorios/evolucao_replay_v1_v2_v3_tcc.md` (já resumidos na Tabela 6.5).
3. **Nova Fig. 6.5 (Cap. 6, Seção 6.6) — *Trajetória preliminar do acompanhamento diário prospectivo (14/10 a 16/11/2026, 23 pregões)***
   - **Conteúdo:** gráfico de linhas `pgfplots` (P&B) comparando Multiagentes (v1) vs Buy \& Hold (e indicando que SMA 50/200 e Bollinger 20/2 coincidem com Buy \& Hold por ausência de sinal), destacando a vantagem até 23/10 (+R\$ 2.265,83) e o recuo a partir de 26/10 até 16/11 (R\$ 76.059,11 vs R\$ 82.391,17).
   - **Fonte dos dados:** `tcc2/evidence/06-operacao-diaria/serie-diaria-20261117/equity_diario.csv`.

*(Opcional para o Cap. 4, Seção 4.13 ou Apêndice A: incorporar a captura real da interface do explorador já existente em `tcc2/evidence/04-replay-abril-novembro/telas/preview-desktop.jpg`, caso tenha boa resolução em impressão.)*

---

## 6. Referências (Eixo 6)

### 6.1 Integridade cruzada
- **Total em `references.bib`:** 61 entradas únicas.
- **Total citado no texto:** 61 entradas únicas.
- **Citações sem entrada no `.bib`:** 0 (**OK**).
- **Entradas órfãs no `.bib`:** 0 (**OK**). *(Atenção: se a Seção 2.4 for removida conforme C2-02, lembrar de remover `FamaFrench1993` e `FamaFrench2015` de `references.bib` para não virarem órfãs.)*

### 6.2 Entradas com problemas em `references.bib` (confirmadas em `main.bbl` e no PDF, págs. 69–74)

1. **Crítico — 12 artigos arXiv sem identificador nem URL no PDF (`apalike.bst` descarta `eprint`, `archivePrefix`, `url` e `note`):**
   - `Glasserman2023`, `Jiang2017`, `Li2023`, `FinRL2020`, `LopezLira2023`, `Schulman2017`, `Wu2023`, `Xia2026`, `TradingAgents2024`, `FinBen2024`, `Xing2024`, `StockAgent2024`.
   - **Como aparece no PDF hoje:** `Wu, S., ... Bloomberggpt: A large language model for finance. arXiv, 2023.` (impossível localizar sem o código `arXiv:2303.17564`).
   - **Correção pronta:** como `tcc2/apalike.bst` **imprime o campo `doi`** como `\url{https://doi.org/...}` (exatamente como já funciona em `FinCoT2025`!), adicionar `doi = {10.48550/arXiv.<eprint>}` a todas as 12 entradas arXiv **e** atualizar `journal = {arXiv preprint arXiv:<eprint>}` (no caso de `Xia2026`, especificar `arXiv:2605.19337v2`).
2. **Alto — 6 conferências/periódicos sem DOI nem link no PDF (também afetados pela omissão de `url` e `note` em `apalike.bst`):**
   - `Golchin2024` (ICLR 2024 — sem páginas nem DOI; adicionar `doi = {10.48550/arXiv.2308.08493}` se aplicável ou verificar OpenReview), `Wang2023` (ICLR 2023 — idem, `10.48550/arXiv.2203.11171`), `Li2024` (TMLR 2024 — sem `volume`, `pages` nem `doi`), `Du2024` (ICML/PMLR 2024 — tem `url` no `.bib`, ignorada pelo `.bst`), `Smit2024` (ICML/PMLR 2024 — idem), `Holm1979` (sem DOI; *verificar DOI oficial da revista se desejar uniformizar*).
3. **Alto — 17 quebras de capitalização em 16 entradas no PDF (falta de `{...}` no `references.bib`):**
   - `Clarke2006` (`u.s.` → `{U.S.}`), `DeMiguel2009` (`1/n` → `1/{N}`), `Li2023` (`Tradinggpt:` → `{TradingGPT}:`), `FinRL2020` (`Finrl:` → `{FinRL}:`), `Lo2002` (`sharpe` → `{Sharpe}`), `Sharpe1994` (`sharpe` → `{Sharpe}`), `Magdon2004` (`brownian` → `{Brownian}`), `LopezLira2023` (`chatgpt` → `{ChatGPT}` e `return` após `?` → `{Return}`), `FinCoT2025` (`Fincot:` → `{FinCoT}:`), `Wu2023` (`Bloomberggpt:` → `{BloombergGPT}:`), `Xia2026` (`llm` → `{LLM}`), `TradingAgents2024` (`Tradingagents:` → `{TradingAgents}:`), `FinBen2024` (`Finben:` → `{FinBen}:`), `Xing2024` (`llm` → `{LLM}`), `FinMem2024` (`Finmem:` → `{FinMem}:`), `FinCon2024` (`Fincon:` → `{FinCon}:`). *(Nota: `Bollinger2001` em `@book` não sofreu quebra porque `format.btitle` preserva caixa, mas convém proteger por segurança.)*
4. **Alto — Erros em nomes de autores:**
   - `Clarke2006` (`references.bib:152`): `Silva, Harindra` → **corrigir para `de Silva, Harindra`** (sobrenome composto oficial do autor: Roger Clarke, Harindra de Silva e Steven Thorley).
   - `Bailey2017` (`references.bib:220`): `Lopez de Prado, Marcos` (sem acento) diverge de `L{\'o}pez de Prado, Marcos` em `LopezDePrado2018` (`references.bib:174`) → padronizar com acento.
5. **Médio — Aviso BibTeX e campos de edição/local:**
   - `FinMem2024` (`references.bib:483-484`): declara simultaneamente `volume = {3}` e `number = {1}` em `@inproceedings`, gerando `Warning--can't use both volume and number fields in FinMem2024` em `main.blg:8` → remover `number = {1}`.
   - `SuttonBarto2018` (`references.bib:183`): `edition = {2}` renderiza `"2 edition"` (p. 72 do texto / p. 84 do PDF) → alterar para `edition = {2nd}`.
   - `FinCon2024` (`references.bib:499-506`): falta o campo `pages` (NeurIPS 2024, vol. 37).
   - Todos os 7 livros (`Shiller2000`, `Thaler1993`, `Wilder1978`, `Bollinger2001`, `LopezDePrado2018`, `SuttonBarto2018`, `Harris2003`) não trazem o campo `address` (local de publicação, exigido pela ABNT NBR 6023).

### 6.3 ABNT NBR 10520 / NBR 6023 vs classe institucional (`eic-bcc-tcc.cls` + `apalike.bst`)

Há uma divergência herdada do próprio template institucional do CEFET/RJ:
- O guia `Trabalho de Conclusao EIC BCC.pdf` (págs. 4 e 14) exemplifica citações em português com parênteses `(Autor e Autor 2023)` e referências em padrão ABNT NBR 6023 (`AUTOR, A.; AUTOR, B. Título. Cidade: Editora, 2023.`).
- Contudo, a classe oficial `eic-bcc-tcc.cls` (linhas 63 e 680) impõe `\RequirePackage[square,authoryear]{natbib}` e `\bibliographystyle{apalike}`, gerando citações com **colchetes e conectivo inglês `"and"`** (`[Fama and French, 1992]`, `Moody and Saffell [2001]`) e referências em inglês (`pages`, `In`, `and`, título em minúsculas, sobrenome em caixa mista).
- **Recomendação (sem impor alteração à classe):** não altere `eic-bcc-tcc.cls` sem anuência do orientador (como manda o próprio template); **verifique com o Prof. Eduardo Ogasawara** se a banca aceita a saída padrão do `eic-bcc-tcc.cls` (`apalike` + colchetes) ou se prefere `abntex2cite` / `abntex2-alf`. Independentemente da resposta, todas as correções em `references.bib` da Seção 6.2 são obrigatórias.

### 6.4 Diálogo entre autores na Fundamentação e nos Trabalhos Relacionados

- **Cap. 3 (Trabalhos Relacionados):** bom diálogo entre autores — agrupa estudos por linha metodológica, contrasta forças e fragilidades ao fim de cada seção (3.1 a 3.6), posiciona o Hedge-fund-lab na Tabela 3.1 (Seção 3.7) e fecha com síntese comparativa explícita (Seção 3.8).
- **Cap. 2 (Fundamentação Teórica):** as subseções `2.6.1` (só `Li2023`), `2.6.2` (só `Xing2024`) e `2.6.3` (só `FinCoT2025`) são resumos de um único artigo cada, sem diálogo entre autores e duplicando o Cap. 3 (tratado em `C2-04`).

---

## 7. Conformidade CEFET/RJ / ABNT (Eixo 7)

Autoridade primária: `tcc2/eic-bcc-tcc.cls` e o manual oficial `Trabalho de Conclusao EIC BCC.pdf`. Itens fora do controle dos autores (como o erro de digitação `"Undergratuade Thesis"` na linha 319 de `eic-bcc-tcc.cls`, o `74.` sem `"f."` no cabeçalho do resumo, ou o espaçamento do hífen na LOF/LOT) não são cobrados dos autores.

| Item | Referência / Norma | Status | Evidência e ação necessária |
|---|---|:---:|---|
| Capa e Folha de rosto | `eic-bcc-tcc.cls` / EIC-BCC | **OK** | Completas (págs. 1–2 do PDF): instituição, curso, autores, título, natureza, orientador com titulação (`D.Sc.`), local e ano (2026). |
| Ficha catalográfica (`ficha.pdf`) | EIC-BCC (p. 3 do manual) | **OK (pré-defesa)** | Ausente antes da defesa; o manual oficial (p. 3) confirma que só é solicitada à Biblioteca Central **após** a defesa e as correções finais. Lembrar de incluir `ficha.pdf` na versão final depositada. |
| Dedicatória e Agradecimentos | EIC-BCC (págs. 4–5 do manual) | **OK (facultativo)** | Elementos facultativos — **verificar no manual/com autores**: tornam-se obrigatórios caso tenha havido bolsa ou apoio financeiro (manual, p. 5). |
| Termo de aprovação | `eic-bcc-tcc.cls` / EIC-BCC (p. 6) | **OK** | Presente (p. 3 do PDF), com título, discentes, linha de data e banca completa (orientador + interno + externo com titulações). |
| Resumo (parágrafo único, limite, estrutura) | ABNT NBR 6028 / EIC-BCC (p. 7) | **OK (com ressalva)** | Parágrafo único, **266 palavras** (limite: 150–500 ABNT / até 500 EIC-BCC), sem citações, com contexto, objetivo, método, resultados e conclusão. Ressalva: omitiu resultado da v2 (`C0-04`). |
| Palavras-chave (3 a 5, formato do template) | EIC-BCC (p. 7) / ABNT NBR 6028 | **OK (polimento)** | 5 palavras-chave separadas e finalizadas por ponto (formato do template). Verificar se a Coordenação adota NBR 6028:2021 (ponto e vírgula) ou mantém o ponto do manual EIC/BCC; pôr estrangeirismos em itálico (`C0-06`). |
| Abstract e Keywords | EIC-BCC (p. 8) | **OK (com ressalva)** | **251 palavras**, fiel ao Resumo; mesmas ressalvas de `C0-04`. |
| Lista de Figuras e Lista de Tabelas | EIC-BCC (págs. 9–10) | **Falha parcial** | Números e páginas batem 100% com o corpo, mas legendas longas (Figs. 4.1–4.3, Tabelas 6.2 e 6.4) geram blocos de 5–7 linhas na LOF/LOT. Usar `\caption[curto]{longo}`. |
| Lista de Acrônimos | EIC-BCC (p. 11 do PDF; Seção 1.4.3, págs. 3–4 do texto) | **Falha (Crítico)** | **Página 8 do PDF em branco** (`main.acn` = 0 bytes, zero `\gls{}`). Ver `C0-01` e Padrão T1. |
| Sumário (hierarquia e alinhamento) | ABNT NBR 6024 / EIC-BCC | **Falha (Crítico)** | Título `SUMÁRIO` deslocado à esquerda (`C0-03`); **34 entradas `x.y.0.0.z`** geradas por `\paragraph{}` (`C5-01`, `C6-01`, `C7-01`), inflando o Sumário para 4 páginas. |
| Numeração e capitalização de seções | ABNT NBR 6024 | **Falha** | Seção `2.1` possui **subseção única** (`2.1.1`, `C2-06`); subseções alternam *Title Case* no Cap. 2 e *Sentence case* nos Caps. 4–6; `\section` alterna CAIXA ALTA nos Caps. 2–3 e *Title Case* nos Caps. 4–7 no código `.tex`. |
| Declaração de uso de IA | EIC-BCC (Seção 2.5, p. 7) | **Verificar no manual / com orientador** | Recomendada explicitamente no manual oficial EIC/BCC (p. 7) quando há uso de IA na revisão/organização textual; ausente na monografia (`C1-02`). |
| Fontes abaixo de figuras e tabelas | ABNT NBR 14724 | **Falha** | Ausente em **todas as 6 figuras** (4.1–4.3, 6.1–6.3) e em **5 tabelas** (4.1, 4.2, 4.3, 5.1, 5.2); as Tabelas 6.1–6.5 citam arquivos internos de repositório. |
| Comentários `TODO`, `\warn`, `\verify`, `\remarks` | `WRITING_RULES.md` | **Falha menor** | **Nenhum `TODO`** nem texto colorido aparece no PDF ou nos capítulos (o TODO anteriormente existente em `02-fundamentacao.tex` já foi removido), mas as macros mortas `\warn`, `\verify`, `\remarks` e o comentário `% ponytail:` ainda constam em `main.tex:9-11,38` (`C0-05`). |
| Ajustes manuais em `main.tex` | Layout PDF | **Falha** | `\usepackage[htt]{hyphenat}` gera 31 avisos de fonte e hífens falsos após `_` (`C0-02`); `\cfttoctitlefont` desalinhou `SUMÁRIO` (`C0-03`). `\emergencystretch=3em` não causou efeito adverso visível. |
| Layout visual do PDF (margens, viúvas, hifenização) | Tipografia / ABNT | **Falha (Crítico)** | Hifenização em inglês no PDF atual (`main.log:66`); 4 estouros graves (>10 pt) em Tabelas 3.1 e 6.1 e caminhos `\texttt`; página 48 com 1 linha viúva; página 74 com 1 referência; colisão textual na Tabela 3.1 e na Fig. 4.2. |

---

## 8. Avisos de Compilação (`tcc2/main.log` e `tcc2/main.blg`)

Foi feita a leitura integral de `tcc2/main.log` (1.712 linhas) e `tcc2/main.blg` (50 linhas), além de uma **recompilação de teste em cópia isolada** (sem alterar nenhum arquivo versionado em `tcc2/`):

- **Recompilação (`latexmk` vs `pdflatex`):** `latexmk` não executa no ambiente atual porque o MiKTeX não encontra o interpretador `perl`. A compilação direta com `pdflatex` → `bibtex` → `pdflatex` → `pdflatex` completa com código de saída `0` (86 páginas), **sem referências indefinidas, sem citações indefinidas e sem rótulos duplicados**.
- **Aviso CRÍTICO no `tcc2/main.log` atual (linha 66):**
  `Package babel Warning: No hyphenation patterns were preloaded for the language 'brazilian' into the format. I will use the patterns loaded for \language=0 instead.`  
  Esse aviso fez o PDF atual hifenizar todo o texto em português com regras do inglês (`trabal-hos`, `sim-ulação`, `mod-elo`, `ver-ificada`, `de-scrito`, `cal-endário`, `anal-istas`, `refer-ência`, `req-uisição`, `sub-stituição`). **Boa notícia:** na recompilação isolada feita hoje, o MiKTeX já carregou `\l@portuguese (\language56)` (`babel-portuges 2026/01/24`), portanto uma simples recompilação já elimina todas essas hifenizações erradas!
- **Acrônimos (`main.acn` = 0 bytes):** `glossaries` não indexou nenhum acrônimo porque `\gls{}` não é chamado; após corrigir `C0-01`, rodar `makeindex -s main.ist -t main.alg -o main.acr main.acn` entre os passos do `pdflatex` (dispensando Perl do `makeglossaries`).
- **10 ocorrências de `Overfull \hbox` em `tcc2/main.log` (distribuídas em 9 locais)** (agravadas porque a classe define `\hfuzz=5pt` e `\hbadness=20000`, escondendo avisos menores e todos os *underfulls*):
  1. `03-relacionados.tex:70` (p. 29 PDF) — **`+21,51 pt`** (`Rastreabilidade` colidindo com `Referências` na Tab. 3.1) e **`+9,36 pt`** (`Multiagente` colidindo com `Custos`).
  2. `04-arquitetura.tex:74-75` (p. 32 PDF) — **`+33,49 pt`** (`src/backtesting/b3_-`).
  3. `06-resultados.tex:25-36` (p. 61 PDF) — **`+25,55 pt`** (Tabela 6.1).
  4. `05-metodologia.tex:113-114` (p. 53 PDF) — **`+13,30 pt`** (`tcc2/scripts/metricas_-`).
  5. `04-arquitetura.tex:113-114` (p. 35 PDF) — **`+11,42 pt`** (`src/agents/graph.py:`).
  6. `05-metodologia.tex:63-73` (p. 50 PDF) — **`+8,17 pt`** (Tabela 5.1).
  7. `04-arquitetura.tex:262-263` (p. 42 PDF) — **`+6,50 pt`** (`/laboratory/replay/v2/`).
  8. `05-metodologia.tex:95-106` (p. 53 PDF) — `+1,86 pt` (Tabela 5.2).
  9. `04-arquitetura.tex:17-38` (p. 31 PDF) — `+1,24 pt` (Tabela 4.1).
- **13 avisos do `hyperref`** (`Difference (2/3) between bookmark levels is greater than one`, linhas 1544–1655 do log: 6 no Cap. 5, 5 no Cap. 6 e 2 no Cap. 7) — todos causados por `\paragraph{}` sem `\subsection`/`\subsubsection` intermediárias (`C5-01`, `C6-01`, `C7-01`).
- **31 avisos `LaTeX Font Warning: Font shape T1/cmtt/... undefined`** (linhas 1307–1429 e 1671) + aviso do `hyphenat` (linha 1175) — todos eliminados ao remover `\usepackage[htt]{hyphenat}` (`C0-02`).
- **1 aviso do BibTeX (`main.blg:8`):** `Warning--can't use both volume and number fields in FinMem2024`.
- **Aviso da classe (informativo, fora do controle dos autores):** `Package babel Warning: Name 'brazil' is deprecated` (`eic-bcc-tcc.cls:20`).

---

## 9. Perguntas Prováveis da Banca sem Resposta (ou Parcialmente Respondidas) no Texto

### Orientador — Prof. Eduardo Soares Ogasawara, D.Sc. (Engenharia de Experimentos, Ciência de Dados, Padrão EIC/BCC)
1. **"Vocês afirmam no Cap. 4 e no Cap. 5 que `H_real` é uma série de 1.519 sessões cobrindo 2.649 barras oficiais. Como 1.519 sessões cobrem 2.649 barras, e o que exatamente é `H_real` no protocolo?"**
   - *Brecha:* erro factual confirmado em `04:72` e `05:188` (`C4-01`, `C5-02`).
   - *Como blindar:* corrigir os dois trechos distinguindo *snapshot* (2.649 barras, 2016–2026), janela elegível `|E|` (1.519 sessões, 2018–2024) e `H_real` (4 sessões reais do *Hardening*).
2. **"Qual foi o protocolo de busca e os critérios de inclusão/exclusão que levaram exatamente aos trabalhos do Capítulo 3?"**
   - *Brecha:* `03-relacionados.tex` não declara bases, termos de busca nem critério de seleção (item destacado no guia EIC/BCC, p. 9).
   - *Como blindar:* adicionar parágrafo de escopo/curadoria na abertura do Cap. 3 (`C3-03`).
3. **"Por que o Capítulo 7 não presta contas, um a um, dos seis objetivos específicos propostos no Capítulo 1 — em particular o Objetivo 6 (acompanhamento diário) e o descompasso parcial do Objetivo 2?"**
   - *Brecha:* `7.1` faz síntese corrida sem rastreamento explícito dos 6 objetivos (`C7-02`).
   - *Como blindar:* incluir quadro/lista de fechamento dos 6 objetivos em `7.1`.
4. **"Em que medida ferramentas de IA generativa auxiliaram na escrita ou codificação da monografia?"**
   - *Brecha:* ausência da declaração recomendada na Seção 2.5 do manual EIC/BCC (p. 7) (`C1-02`).
   - *Como blindar:* incluir nota transparente na Introdução sob anuência do orientador.

### Membro Interno — Prof. Renato Campos Mauro, D.Sc. (Computação, IA, Sistemas Multiagentes, Rigor Estatístico)
5. **"Na v3, vocês colocaram faixas numéricas explícitas de reversão à média nas cinco lentes e o compilador determinístico interveio 80 vezes em 81 operações. Quanto do resultado da v3 vem de fato do raciocínio do LLM e quanto vem de um conjunto de regras determinísticas disfarçadas em *prompt*?"**
   - *Brecha:* o texto admite em 6.4.3 que "a governança determinística moldou o resultado tanto quanto os sinais", mas não quantifica quantos pregões/ações do gestor passaram sem modificação do compilador nem discute um controle determinístico puro equivalente às 5 lentes da v3 (uma regra de votação de 5 indicadores sem LLM).
   - *Como blindar:* registrar na Seção 6.5 (Discussão) e em 7.5 (Trabalhos Futuros) que um controle determinístico codificando diretamente as mesmas 5 lentes sem LLM seria o experimento ideal para isolar o valor marginal do modelo de linguagem.
6. **"Como a carteira multiativos substituiu o grafo LangGraph por um fluxo próprio em `scripts/` e `dashboard/`, qual é o papel real do LangGraph na contribuição empírica do TCC 2?"**
   - *Brecha:* o Cap. 1 (L8, L19) dá peso semelhante aos dois caminhos e o Cap. 4 dedica 6 páginas iniciais ao caminho de ativo único antes de mostrar que o replay não usa LangGraph.
   - *Como blindar:* explicitar logo no Cap. 1 e reordenar o Cap. 4 (Seção 3.4) deixando claro que o caminho LangGraph foi a arquitetura inicial de ativo único (da qual se reutilizaram o nó de comitê técnico e os esquemas Pydantic), enquanto o núcleo empírico do TCC 2 é a orquestração multiativos.
7. **"Com temperatura 1,0 e apenas uma execução por versão ($R=1$), como vocês garantem que a diferença entre v1 e v2 (+3,56 p.p., concentrada em um único ativo) ou parte do ganho da v3 não é apenas variância estocástica entre rodadas?"**
   - *Brecha:* a limitação de $R=1$ é citada, mas não há nenhuma ordem de grandeza da sensibilidade estocástica observada nos ensaios anteriores (ou nas votações por semente da v1, onde 83,01\% de unanimidade sugere baixa variância na v1, mas na v2/v3 com 45–66\% de placares 3–2 a sensibilidade a um único voto flutuante é muito maior!).
   - *Como blindar:* acrescentar em 6.5 essa observação analítica precisa: na v2 (65,66\% de placares 3–2) e na v3 (45,10\% de 3–2), uma única flutuação estocástica de voto inverte o consenso, aumentando a incerteza não capturada sob $R=1$.
8. **"No Bootstrap A com $n=153$ pregões, o poder é tão baixo ($EP \approx 1{,}3$) que nem uma diferença de 2,00 pontos de Sharpe (R\$ 22,7 mil entre Bollinger e v1) é significativa a 5\%. Quantos pregões seriam necessários para ter poder razoável, e que informação o teste estatístico efetivamente agrega nessa janela?"**
   - *Brecha:* o texto menciona $EP \approx 1{,}3$, mas não traduz em horizonte mínimo aproximado (para distinguir $\Delta S = 0{,}5$ com poder de 80\% sob $\alpha=0{,}05$ unilateral, mesmo com correlação moderada, seriam necessários vários anos de pregões — e com $R=1$ ainda falta a variância entre execuções).
   - *Como blindar:* incluir duas frases na Seção 5.6.1 explicitando que o Bootstrap A na janela de 153 pregões funciona sobretudo como freio contra falsos positivos (mostrando que diferenças grandes em reais ainda caem dentro da margem de erro amostral), e que poder estatístico para efeitos moderados exige horizontes plurianuais.

### Membro Externo — Gilberto Gil Fidelis Gomes Passos, M.Sc. (Finanças Quantitativas, Mercado Brasileiro, Prática Operacional)
9. **"Qual versão da arquitetura (v1, v2 ou v3) está rodando no acompanhamento prospectivo da Seção 6.6 que perdeu $-23{,}94\%$ contra $-17{,}61\%$ do Buy \& Hold? E por que o texto diz 'de R\$ 99.835,33 para R\$ 82.391,17 (-17,61%)' se essa variação é de $-17{,}47\%$?"**
   - *Brecha:* ambos os pontos estão ausentes/ambíguos em `06-resultados.tex:204-206` (`C6-03`).
   - *Como blindar:* aplicar exatamente a reescrita de `C6-03`.
10. **"No Brasil de 2026, o CDI paga dois dígitos ao ano e a Bollinger manteve 49\% do patrimônio em caixa não remunerado (e a v2, 25\% em média e 46\% no fim). Como ficaria a ordenação de retorno e de Sharpe se o caixa rendesse CDI e o Sharpe usasse $r_f = \text{CDI}$ em vez de $r_f = 0$?"**
    - *Brecha:* `05:122` e `06:196` mencionam qualitativamente que $r_f > 0$ reduziria todos os Sharpes, mas não discutem o **efeito diferencial de remunerar o caixa**: remunerar caixa ao CDI favoreceria fortemente as carteiras com alto caixa médio (Bollinger 20/2 com 49,06\%, SMA 50/200 com 31,39\% e v2 com 24,69\%), ampliando ainda mais a vantagem da Bollinger 20/2 sobre a v3 (14,94\% de caixa médio), enquanto $r_f = \text{CDI}$ tornaria o Sharpe da v3 (retorno de +0,07\% em 153 pregões) claramente negativo!
    - *Como blindar:* adicionar um parágrafo curto sobre esse efeito diferencial na Seção 6.5 (sem inventar números de CDI, apenas explicando a direção econômica inequívoca) e reforçar em 7.5.
11. **"Por que escolheram exatamente essas cinco ações (*blue chips* de alta liquidez do Ibovespa) e não um universo mais amplo ou sorteado? Isso não introduz viés de seleção/sobrevivência e concentração setorial (dois bancos + duas commodities + uma industrial)?"**
    - *Brecha:* o universo fixo de 5 ações é apresentado como dado (`05:27`), sem justificar o critério de escolha nem registrar viés de seleção/sobrevivência e correlação intrassetorial (BBAS3 e ITUB4 pertencem ao setor bancário; PETR4 e VALE3 são commodities exportadoras) em 5.8.
    - *Como blindar:* justificar brevemente o universo em 5.2 (alta liquidez na B3 e diversidade entre bancos, commodities e indústria, limitada pelo orçamento de inferência de 31 chamadas/pregão para 5 ativos) e registrar viés de seleção/sobrevivência em 5.8.
12. **"As 27 vendas da v3 abaixo de R\$ 2.000 (22 abaixo de R\$ 500, chegando a lotes de 1 a 9 ações) exigem mercado fracionário na B3 (sufixo `F`), que tem *spread* maior e liquidez menor que o lote padrão de 100 ações. Sem lote mínimo nem *spread*, a comparação com Buy \& Hold e Bollinger (24 operações cheias) não superestima a v3?"**
    - *Brecha:* `06:179` menciona corretamente que seria inviável com custo fixo ou lote mínimo, mas não menciona o **mercado fracionário da B3** (lote padrão = 100 ações) e o consequente custo de *spread* diferenciado que atinge justamente a v3 (e as compras residuais da v1).
    - *Como blindar:* incluir uma frase em `06:179` e `05:213` mencionando explicitamente que operações abaixo de 100 ações na B3 transitam pelo mercado fracionário, com menor liquidez e *spread* tipicamente mais amplo que o lote padrão.

---

## 10. Plano de Correção em Lotes

Ordem priorizada pelo critério: **primeiro bloqueadores de banca (Críticos), depois maior ganho de nota por hora investida**.

### Lote 1 — Correções Críticas e Bloqueadores de Defesa (Esforço estimado: 4–6 h · ganho estimado: +1,2 ponto)
1. Corrigir o erro factual sobre `H_real` (1.519 vs 2.649 barras) em `04-arquitetura.tex:72` e `05-metodologia.tex:188` (`C4-01`, `C5-02`).
2. Substituir todos os **34 `\paragraph{}`** nos Caps. 5, 6 e 7 por `\textbf{}` ou `\subsection` (`C5-01`, `C6-01`, `C7-01`), zerando os 13 avisos do `hyperref` e as entradas `x.y.0.0.z` do Sumário (também elimina a linha viúva da p. 48).
3. Ativar a **Lista de Acrônimos**: declarar siglas faltantes, remover `etl`/`mas`, aplicar `\gls{}` no corpo e rodar `makeindex -s main.ist -t main.alg -o main.acr main.acn` (`C0-01`, Padrão T1).
4. Consertar o alinhamento de `SUMÁRIO` (`C0-03`), remover `\usepackage[htt]{hyphenat}` (`C0-02`) e eliminar os 4 estouros graves de margem: **Tabela 3.1** (`C3-01` + `\FloatBarrier`), **Tabela 6.1** (`C6-02`), **Tabela 5.1** (`C5-04`) e os caminhos `\texttt` em `04:74,113,262` e `05:113` (`C4-02`, `C5-04`).
5. Alinhar H1/H2 no Cap. 1 com a redação declarativa do Cap. 5 (`C1-01`) e corrigir os 4 `\citep` sintaticamente quebrados no Cap. 2 (`C2-01`).
6. Recompilar o PDF com hifenização em português ativa (`babel-portuges`, já funcional no MiKTeX local) e conferir visualmente a remoção de todas as quebras em inglês.

### Lote 2 — Referências, Tabelas/Figuras e Clareza Científica de Alto Impacto (Esforço estimado: 4–5 h · ganho estimado: +0,8 ponto)
1. Corrigir `references.bib`: adicionar `doi = {10.48550/arXiv.<id>}` e `journal = {arXiv preprint arXiv:<id>}` nas 12 entradas arXiv, proteger as 17 capitalizações com `{...}`, corrigir `de Silva, Harindra`, `López de Prado`, `FinMem2024` (`number`) e `SuttonBarto2018` (`2nd`), e preencher `address` nos livros (Seção 6.2).
2. Atualizar `metricas_replay.py` e `bootstrap_replay.py` (ou suas saídas `.tex`): cabeçalhos em negrito nas Tabelas 6.2–6.4, `\caption[curto]{longo}`, nota sobre a diferença de 0,01 de arredondamento, `Fonte:` ABNT limpa (sem `.csv`/`.md` internos), `Bootstrap A`, `valores-$p$` e `xlabel={Mês (2026)}` + `Fonte:` nas Figuras 6.1–6.3 (`C6-04`, `C6-05`).
3. Corrigir a Seção 6.6 (explicitar versão **v1** no acompanhamento prospectivo e esclarecer a base de R\$ 100.000,00 para $-17{,}61\%$ / $-23{,}94\%$, `C6-03`), a ligadura `–references-only` (`C4-05`), a colisão da Fig. 4.2 (`C4-04`) e adicionar `Fonte:` às Figuras 4.1–4.3 e Tabelas 4.1–4.3 e 5.1–5.2.
4. Incluir o resultado da **v2** no Resumo e no Abstract (`C0-04`), fechar explicitamente os **6 objetivos específicos** na Seção 7.1 (`C7-02`), e excluir os 3 arquivos órfãos (`figures/figure.png`, `images/grafo-langgraph.png`, `images/pipeline-etl.png`).

### Lote 3 — Reequilíbrio Estrutural e Figuras Novas (Esforço estimado: 6–8 h · ganho estimado: +0,5 ponto)
1. Reformar o **Cap. 2**: remover Seção 2.4 (*Factor Investing*, `C2-02`), eliminar subseção única 2.1.1 e micro-subseção 2.5.2 (`C2-06`), desduplicar 2.6 frente ao Cap. 3 (`C2-04`), definir variáveis nas equações (`C2-05`) e acrescentar fundamentação de *bootstrap* estacionário, multiplicidade (Holm / interseção–união) e propriedades do Sharpe sob retornos negativos (`C2-03`).
2. Reequilibrar o **Cap. 4**: mover inventário de módulos/constantes (4.12, 4.9.5, Tabela 4.3) para **Apêndice A**, colocar a carteira multiativos antes do legado de ativo único, definir matematicamente as 8 *features* adimensionais (`C4-03`), atualizar Fig. 4.1 com a ramificação multiativos (`C4-08`) e ajustar o tom da abertura (`C4-06`).
3. Reordenar `5.7` para o início do **Cap. 5**, adicionar a **Fig. 5.1** (linha do tempo + desenho pareado) e as **Figs. 6.4 e 6.5** (placares/RSI v1–v3 e acompanhamento prospectivo de 23 pregões), e enxugar a tripla repetição de limitações entre 5.8, 6.5 e 7.4 (incorporando viés de seleção/sobrevivência, efeito diferencial do CDI e mercado fracionário B3).

### Lote 4 — Polimento Editorial e Verificação Final Pré-Defesa (Esforço estimado: 2–3 h · ganho estimado: +0,1 ponto)
1. Aplicar os Padrões T3 e T4 em toda a monografia (`sobreajuste`, itálico uniforme em estrangeirismos, `Buy \& Hold`, `Equal Weight 63d`, `Mínima Variância 252/63`, `piso de posição-núcleo`, `TCC 1`, correções ortográficas de `C2-08`, remoção de `"cerca de"` antes de valores exatos em `C6-06` e `C7-04`).
2. Remover macros de rascunho de `main.tex:9-11` (`C0-05`), incluir nota de uso de IA se acordado com o orientador (`C1-02`), adicionar breve critério de seleção da literatura no Cap. 3 (`C3-03`) e ajustar espaçamento para evitar a última referência órfã isolada na p. 74.
3. **Aceite final de compilação:** zero erros, zero `Overfull \hbox > 5 pt`, zero avisos de `hyperref` bookmark, zero avisos de `babel` hyphenation, zero avisos de `bibtex`, Lista de Acrônimos povoada e conferência visual página a página do PDF final.
