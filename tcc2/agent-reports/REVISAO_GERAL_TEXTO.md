# Revisão Geral do Texto — TCC 2 (Hedge-fund-lab)

**Monografia avaliada:** *Hedge-fund-lab: Laboratório Quantitativo de Backtesting baseado em Sistemas Multiagentes*  
**Autores:** Lucas Pereira da Silva e Matheus Pereira de Carvalho · **Orientador:** Eduardo Soares Ogasawara, D.Sc. (CEFET/RJ) · **Banca:** Renato Campos Mauro, D.Sc. (interno) e Gilberto Gil Fidelis Gomes Passos, M.Sc. (externo).  
**Base auditada:** `tcc2/main.tex`, `tcc2/chapters/01-introducao.tex` a `07-conclusao.tex`, `tcc2/chapters/tabelas/*.tex`, `tcc2/figures/*.tex`, `tcc2/references.bib`, `tcc2/eic-bcc-tcc.cls`, `tcc2/apalike.bst`, `tcc2/main.pdf` (86 páginas físicas; 12 pré-textuais + 74 numeradas), `tcc2/main.log` e `tcc2/main.blg`, conferidos integralmente contra `tcc2/WRITING_RULES.md`, `METRICAS_REPLAY.md`, `BOOTSTRAP_REPLAY.md`, `MATRIZ_EVIDENCIAS.md`, `tcc2/evidence/` (incluindo `evolucao_replay_v1_v2_v3_tcc.md`, `H2_METHODOLOGICAL_FREEZE_V1.md`, `equity_diario.csv` e o guia oficial `Trabalho de Conclusao EIC BCC.pdf`) e o código-fonte em `src/`, `scripts/` e `dashboard/`.  
**Convenção de páginas:** `p. N (PDF p. M)` indica o número impresso `N` no cabeçalho superior direito e a página física `M = N + 12` do arquivo `tcc2/main.pdf` (os elementos pré-textuais ocupam `PDF p. 1–12`).

---

## 1. Veredito geral

**Nota atual: 7,3 / 10.** O trabalho tem um mérito científico raro em monografias de graduação: os números do replay batem até o centavo com os artefatos selados, o *bootstrap* estacionário pareado é integralmente reprodutível e o resultado negativo da versão pré-especificada (v1) é reportado com honestidade exemplar, sem confundir as iterações exploratórias dentro da amostra (v2 e v3) com evidência confirmatória. O que impede o 10/10 hoje são defeitos visuais graves no PDF compilado, quatro erros factuais/contraditórios no texto, lacunas formais frente ao guia oficial do BCC/CEFET-RJ, 12 referências arXiv sem código identificador e o desequilíbrio entre o Capítulo 2 (que não fundamenta a inferência estatística) e o Capítulo 4 (17 páginas em tom de auditoria de código). **As 5 mudanças de maior impacto para chegar a 10/10:**
1. **Consertar os cinco defeitos críticos do PDF compilado:** recompilar com hifenização em português ativa (`babel-portuges`, eliminando quebras inglesas como `trabal-hos`, `sim-ulação`, `mod-elo`, `ver-ificada`); substituir os 34 `\paragraph{}` que geram numeração `5.3.0.0.1` no Sumário e no corpo; ativar a Lista de Acrônimos via `\gls{}` (eliminando a página 8 em branco do PDF); corrigir as colisões/estouros de margem das Tabelas 3.1 (+21,5 pt) e 6.1 (+25,5 pt) e dos caminhos `\texttt` (+33,5 pt); e centralizar o título `SUMÁRIO`.
2. **Eliminar os quatro erros factuais e contradições internas:** corrigir `H_real` (descrito como 1.519 sessões cobrindo 2.649 barras em `04:72` e `05:188`, quando 2.649 é o *snapshot* 2016–2026, 1.519 é o conjunto elegível `|E|` e `H_real` são apenas 4 sessões reais do *Hardening*); corrigir em `06:175` que `PETR4` "passou a resultado positivo" na v3 (já era positivo na v2, `06:156`); corrigir a afirmação unidirecional de que a contaminação "favorece a carteira Multiagentes" (`05:205`, `06:191`, `07:47`), que contradiz o efeito de distração de Glasserman e Lin (2023) citado no Cap. 3 (`03:46`); e esclarecer na Seção 6.6 que a carteira diária prospectiva opera a arquitetura **v1** e que $-17{,}61\%$ / $-23{,}94\%$ têm base em R\$ 100.000,00 (e não em R\$ 99.835,33).
3. **Atender às exigências do guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`) e alinhar hipóteses:** uniformizar o enunciado declarativo de H1 e H2 entre Cap. 1 e Cap. 5; incluir a lacuna e o resultado da v2 no Resumo/Abstract; adicionar citações, lacuna, síntese de resultados e declaração de uso de IA no Cap. 1; explicitar o protocolo/critério de seleção bibliográfica no Cap. 3; e fechar explicitamente cada um dos 6 objetivos específicos na Conclusão (Cap. 7).
4. **Reequilibrar os Capítulos 2 e 4 e fechar lacunas de reprodutibilidade:** no Cap. 2 (~1.820 palavras, 7 págs.), remover a Seção 2.4 (*Factor Investing*, sem uso no trabalho) e a duplicação com o Cap. 3 em 2.6, adicionando as fórmulas de RSI/MACD e uma seção de inferência estatística (*bootstrap* estacionário, erro-padrão do Sharpe e anomalia sob retornos negativos, multiplicidade de Holm e interseção–união); no Cap. 4 (~5.450 palavras, 17 págs.), enxugar ~5–6 páginas de inventário de arquivos/rotas/constantes para Apêndice e definir matematicamente as 8 *features* adimensionais e sua invariância causal ao fator Yahoo.
5. **Corrigir `references.bib` e blindar a discussão financeira para a banca externa:** incluir `doi = {10.48550/arXiv.<id>}` e `journal = {arXiv preprint arXiv:<id>}` nas 12 entradas arXiv hoje impressas apenas como `"arXiv, YYYY."`, proteger 17 maiúsculas com `{...}`, corrigir `de Silva, Harindra` e `Thaler1993` (`editor`), e discutir explicitamente o viés direcional do caixa não remunerado (Bollinger com 49,06% e SMA com 31,39% de caixa médio frente ao CDI), a seleção do universo de 5 *blue chips*, o mercado fracionário nas 27 vendas residuais da v3 e a discrepância de arredondamento de 0,01 entre as Tabelas 6.2 e 6.4.

---

## 2. Placar por capítulo

| Capítulo | Nota (0–10) | Maior problema | Esforço p/ 10 (P/M/G) |
|---|---:|---|:---:|
| **Cap. 0 — Pré-textuais, Resumo e Abstract** (`main.tex`) | **6,5** | Página 8 em branco na Lista de Acrônimos (zero `\gls{}`); Sumário com 34 entradas `x.y.0.0.z` e título `SUMÁRIO` desalinhado; Resumo omite a lacuna, omite a v2 e sugere que a avaliação prospectiva definitiva já está em curso (quando o ciclo diário roda a v1) | **P** |
| **Cap. 1 — Introdução** (`01-introducao.tex`) | **6,8** | Zero citações bibliográficas no capítulo inteiro; H1 e H2 redigidas como tarefa futura ("Será avaliado se..."), divergindo do Cap. 5; afirmação de que o registro "evita o viés de superajuste" (L35); faltam declaração de uso de IA, lacuna explícita e síntese de resultados (guia EIC/BCC) | **M** |
| **Cap. 2 — Fundamentação Teórica** (`02-fundamentacao.tex`) | **5,8** | Não fundamenta a inferência estatística que decide as hipóteses (*bootstrap* estacionário, Holm, interseção–união, erro-padrão do Sharpe); Seção 2.4 (*Factor Investing*) nunca utilizada; sem fórmula do RSI e do MACD; 5 `\citep` como sujeito/complemento da oração; subseção única `2.1.1` e micro-subseção `2.5.2` de 1 frase; duplicação com Cap. 3 em `2.6` | **G** |
| **Cap. 3 — Trabalhos Relacionados** (`03-relacionados.tex`) | **7,8** | Colisão textual severa nos cabeçalhos da Tabela 3.1 (`MultiagenteCustos` e `RastreabilidadeReferências`, +21,5 pt) e flutuação para o meio da Seção 3.8; falta protocolo/critério de busca bibliográfica (guia EIC/BCC, p. 9); tensão entre L50 ("estudo exploratório") e L100 (v1 inferencial); corte do modelo sem fonte | **M** |
| **Cap. 4 — Arquitetura e Implementação** (`04-arquitetura.tex`) | **6,0** | Dois erros factuais (`H_real` em `04:72` e "avaliação H1/H2 sobre PETR4" em `04:6`); 17 páginas em tom de relatório de auditoria externa; estouro de margem de +33,5 pt em `\texttt` e hífens falsos após `_`; ligadura `–references-only`; colisão na Fig. 4.2; falta definição matemática das 8 *features* e de sua invariância causal; omite que os analistas não recebem *ticker*/data/preço e que o ciclo diário roda a v1 | **G** |
| **Cap. 5 — Metodologia Experimental** (`05-metodologia.tex`) | **7,8** | 16 `\paragraph{}` gerando `5.x.0.0.y` no Sumário; repete o erro factual de `H_real` (`05:188`); afirma que a contaminação "favorece" os agentes (`05:205`), contradizendo o efeito de distração do Cap. 3; não explicita a direção do viés do caixa não remunerado nem data/critério do universo; frase sem verbo e "pelo autor" em `05:194`; página 48 quase vazia com 1 linha viúva; zero figuras | **M** |
| **Cap. 6 — Resultados e Discussão** (`06-resultados.tex`, `tabelas/`) | **8,0** | Erro interno sobre `PETR4` em `06:175`; Seção 6.6 omite que o piloto prospectivo roda a v1 e gera ambiguidade na base de $-17{,}61\%$ / $-23{,}94\%$; extrapolações não testadas ("número de agentes importa menos" em `06:184` e "tanto quanto os sinais" em `06:177`); Tabela 6.1 estoura +25,5 pt; 14 `\paragraph{}`; falta nota sobre diferença de 0,01 entre Tabelas 6.2 e 6.4; falta discussão do efeito da exposição em caixa e do mercado fracionário | **M** |
| **Cap. 7 — Conclusão** (`07-conclusao.tex`) | **7,6** | Não fecha explicitamente cada um dos 6 objetivos específicos do Cap. 1 (exigência do guia EIC/BCC, p. 13); 4 `\paragraph{}` gerando `7.2.0.0.y`; repete direção unilateral da contaminação (`07:47`); repete lista de limitações de 5.8 sem incluir viés do caixa/CDI, tributação de ganho de capital e seleção do universo; omite que o mapeamento dos contrastes foi pós-replay (`07:18`) | **P** |
| **Referências e PDF global** (`references.bib`, `main.log`) | **6,0** | Hifenização inglesa em todo o PDF versionado (`main.log:66`); 12 artigos arXiv impressos apenas como `"arXiv, YYYY."` sem ID nem DOI/URL; 17 erros de capitalização nos títulos; `Silva, H.` em vez de `de Silva, H.`; `Thaler1993` como `author` em vez de `editor`; aviso BibTeX em `FinMem2024`; 34 quebras de linha entre `R$` e o número | **P–M** |

---

## 3. Problemas macro (eixos 1 e 5)

### 3.1 Estrutura narrativa, encadeamento entre capítulos e fios soltos

A espinha dorsal da monografia conta uma história clara, coerente e cientificamente defensável: (1) estratégias quantitativas sofrem com não estacionariedade e sobreajuste, e sistemas multiagentes baseados em LLMs exigem infraestrutura rigorosa de avaliação antes de qualquer pretensão de lucro; (2) o Hedge-fund-lab é construído com dados oficiais da B3, livro contábil de eventos imutáveis, comitês de agentes e compilador determinístico; (3) no Replay Contínuo pareado de 153 pregões, a versão pré-especificada (v1) termina abaixo das cinco referências e não rejeita H0, assim como a regra de tendência SMA 50/200 não supera a Equal Weight 63d (H1); (4) a auditoria empírica da v1 diagnostica cinco achados que motivam duas iterações exploratórias dentro da amostra (v2 e v3), demonstrando descritivamente que especialização funcional (cinco lentes distintas) e governança determinística alteram de forma drástica o comportamento do comitê e da carteira, embora uma regra determinística simples (Bollinger 20/2) ainda lidere sem custo de inferência; e (5) a avaliação livre de contaminação do modelo fica reservada ao acompanhamento prospectivo.

Apesar dessa espinha dorsal sólida, há **oito fios soltos ou quebras de preparação entre capítulos** que precisam ser fechados:

| ID | Fio solto / quebra de preparação | Onde nasce → onde falta ou quebra | Como resolver |
|---|---|---|---|
| **FS-1** | **Seção 2.4 (*Factor Investing* e Fama-French 3/5 fatores) não tem uso no trabalho** | Nasce em `02-fundamentacao.tex:80-89` → nunca mais aparece nos Caps. 3 a 7 | Excluir a Seção 2.4 (`−0,5` pág.), cumprindo a diretriz explícita do guia EIC/BCC (p. 8: *"Limite-se exclusivamente aos temas utilizados em seu trabalho"*). |
| **FS-2** | **Inferência estatística do Cap. 5 não é preparada no Cap. 2** | Usada em `05-metodologia.tex:149-180` e `06:54,65-92` (*bootstrap* estacionário de Politis–Romano, erro-padrão de Lo, anomalia do Sharpe sob retorno negativo, Holm e teste de interseção–união) → ausente do Cap. 2 | Criar a Seção `2.8 Inferência Estatística e Comparação Múltipla em Séries Financeiras` no Cap. 2 (`+1,5` pág.; ver `C2-03`). |
| **FS-3** | **Indicadores técnicos centrais nos resultados (RSI e MACD) e as 8 *features* não têm fórmula no texto** | RSI e *gaps* das bandas/médias estruturam toda a Seção 6.4 (Tabela 6.5) e as travas da v3 (`04:336-339`) → Cap. 2 não traz a fórmula nem o período do RSI (14) e do MACD (12/26/9), e o Cap. 4 não traz a fórmula das 8 *features* adimensionais | Incluir as equações de RSI e MACD na Seção 2.3.2 (`C2-06`) e uma tabela com as fórmulas das 8 *features* e da volatilidade de 21 dias na Seção 4.7.1 (`C4-04`). |
| **FS-4** | **Protagonismo invertido no Cap. 4 e referência antecipada ao protocolo no Cap. 5** | O estudo empírico do TCC 2 é o replay multiativos (que não usa `engine.py`, SQLAlchemy nem o grafo LangGraph), mas o Cap. 4 dedica as págs. 19–24 ao caminho legado de ativo único antes de apresentar a carteira multiativos (p. 24); no Cap. 5, o "protocolo original" é invocado 7 vezes entre as págs. 38 e 44 antes de ser explicado na Seção 5.7 (p. 45) | Condensar o caminho de ativo único no Cap. 4 (movendo o inventário de `src/experiments` para Apêndice) e antecipar um resumo da transição do protocolo original para logo após a Seção 5.1 no Cap. 5. |
| **FS-5** | **Promessa não cumprida sobre medição do *implementation shortfall*** | `04-arquitetura.tex:168` afirma que cada operação registra quatro preços (decisão, prévia, aprovação e leilão), *"o que permite medir o custo de implementação"* → nunca é medido nem retomado nos Caps. 5, 6 ou 7 | Ajustar a redação em `04:168` para esclarecer que essa estrutura foi implementada para a operação diária sob as regras de leilão, enquanto no replay a aprovação hipotética às 09:00 executa diretamente no `OPEN` (`C4-09`). |
| **FS-6** | **Invariância causal do fator de ajuste e anonimização de *ticker*/data/preço nos analistas existem no código, mas não são aproveitadas na discussão metodológica** | Código (`src/agents/features.py:1-27`, `technical_analyst.py:116-126`, `H2_METHODOLOGICAL_FREEZE_V1.md:570-579`) prova que as 8 *features* são invariantes a proventos futuros e que analistas e risco não recebem *ticker*, data nem preço → `04:77`, `04:152` e `05:205` omitem ambas as garantias | Explicitar ambas as propriedades em `04:77`, `04:152` e `05:205` (`C4-05`, `C5-03`), fortalecendo substancialmente a defesa metodológica perante a banca. |
| **FS-7** | **Falta fechar o elo teórico entre `FinCoT2025` / `Xing2024` (Cap. 2/3) e o salto empírico da v3 (Cap. 6)** | `02:113-121` e `03:26,56` discutem heterogeneidade de papéis e raciocínio guiado por restrições de domínio (FinCoT) → `06:184` e `07:31-35` discutem as 5 lentes da v3 sem reconectar com `FinCoT2025` e `Xing2024` | Acrescentar duas frases na Seção 6.5 reconectando as cinco lentes especialistas com restrições explícitas de sinal à literatura de raciocínio guiado por domínio (`FinCoT2025`) e heterogeneidade funcional (`Xing2024`). |
| **FS-8** | **Tripla repetição da mesma lista de limitações em 5.8, 6.5 e 7.4** | Os mesmos 7 itens aparecem quase com as mesmas palavras nas págs. 46–48 (5.8), 61–62 (6.5) e 67 (7.4) | Diferenciar os papéis: em 5.8, apresentar as ameaças *metodológicas de desenho* (com quadro-síntese do sentido do viés); em 6.5, discutir como elas *se manifestaram nos números do replay*; em 7.4, fazer síntese enxuta de meia página diretamente ligada a 7.5. |

### 3.2 Rastreabilidade: Objetivos, Perguntas e Hipóteses → Onde são respondidos → Resposta

| Elemento formulado na Introdução (`01-introducao.tex`) | Onde é entregue / respondido | Resposta no texto | Diagnóstico de revisão |
|---|---|---|---|
| **Pergunta Principal (`01:6`):** como projetar ambiente comparável e controlado, e se a arquitetura multiagente baseada em LLMs produz decisões mais robustas que abordagens tradicionais sob risco, custo e consistência operacional | Caps. 4–6; respondida explicitamente em `7.2` (`07:18`, p. 64–65) | (i) Ambiente realizado por carteiras pareadas com mesma cesta inicial, separação entre dados de decisão e preços RAW de execução/marcação, paridade exata das 5 referências, métrica e teste pré-fixados e trilha auditável por evento/chamada; (ii) **não há evidência** de que a arquitetura multiagente produza decisões superiores às referências tradicionais. | **Parcial:** falta alinhar o termo *"mais robustas"* da pergunta (`01:6`) com *"desempenho ajustado ao risco superior, líquido de custos"* (`C1-05`) e ressalvar em `07:18` que o mapeamento dos contrastes (H1 → SMA $\times$ EW; H2 → família de 5 referências) foi estabelecido na redação pós-replay (`C7-04`). |
| **Pergunta Secundária / Arquitetural (`01:12`):** mantidos modelo, quantidade de agentes, dados e execução, quanto do comportamento depende da especialização dos analistas e da governança determinística sobre a proposta do gestor | Seção 6.4 (`06:94-180`, págs. 55–60) e Seção 7.3 (`07:28-40`, págs. 66–67) | Dependeu fortemente nesta trajetória: queda da unanimidade 5–0 de 83,01\% (v1) para 15,13\% (v2) e 4,03\% (v3); inversão do RSI médio de compra/venda executada de 60,51/36,06 (v1) para 39,26/69,00 (v3); eliminação das saídas totais (9 e 10 → 0); 80 intervenções do compilador na v3; diferença patrimonial de +R\$ 17.888,65 (+17,89 p.p.) entre v1 e v3. | **Respondida com rigor descritivo.** Ajustar apenas duas extrapolações: retirar *"o número de agentes importa menos"* (`06:184`, pois o número não variou) e *"moldou o resultado tanto quanto os sinais"* (`06:177`, `07:36`, pois não houve ablação) (`C6-04`). |
| **Objetivo Geral (`01:8`):** desenvolver o Hedge-fund-lab, laboratório quantitativo para *backtesting* baseado em sistemas multiagentes | Caps. 4, 5 e 6; síntese em `7.1` e `7.6` (`07:10-12, 71`) | Laboratório implementado, auditado e aplicado ao Replay Contínuo (3 campanhas $\times$ 6 carteiras $\times$ 153 pregões) e à operação diária prospectiva. | **Atendido.** Explicitar em `7.6` a evidência concreta de *extensibilidade* prometida em `01:35` (implementação de v2 e v3 por vinculação de módulo `pilot_paper.bind`, sem editar as fontes seladas da v1). |
| **Obj. Específico 1 (`01:17`):** construir *pipeline* de dados reproduzível a partir da fonte oficial da B3 (COTAHIST), com correção de proventos e calendário próprio | Seção 4.2 (`04:42-78`, p. 20) e `7.1` (`07:10`, p. 64) | *Pipeline* `src/pipeline` (`b3_official.py`), calendário `B3Calendar` (2.649 sessões oficiais) e base local multiativos (`market_base_api.py` + *bundle* congelado por SHA-256). | **Parcial na Conclusão:** corrigir o erro factual de `H_real` em `04:72` (`C4-01`), explicar a invariância das *features* ao fator Yahoo (`C4-05`) e fechar o Obj. 1 nominalmente na Seção 7.1 (`C7-03`). |
| **Obj. Específico 2 (`01:18`):** implementar motor de *backtesting* e livro contábil de eventos auditável com custos, proventos e métricas do protocolo | Seções 4.3, 4.5 e 5.5; mencionado em `7.1` (`07:10`, p. 64) | Motor `src/backtesting` (com `H2_SCIENTIFIC_SHARPE_DEFINITION_V1`) e livro contábil de eventos encadeados por *hash* (`manual_portfolio_api.py`) implementados. | **Atendido com nuance não explicada:** o replay evolui no livro de eventos e não usa `engine.py` (`04:100`), e Sortino/giro não são políticas congeladas do protocolo (`05:131,144`). Ajustar `01:18` (`C1-07`) e registrar essa distinção no fechamento do Obj. 2 em `7.1`. |
| **Obj. Específico 3 (`01:19`):** desenvolver sistema multiagente baseado em LLMs nas versões de ativo único (LangGraph) e multiativos (gestor global e compilador determinístico) | Seções 4.6, 4.7 e 4.10; mencionado em `7.1` (`07:10`, p. 64) | Grafo linear LangGraph (`src/agents`) e arquitetura multiativos 5 + 1 + 1 (`multiasset_radar.py` + `wallet_manager_api.py` + `compile_proposal`) implementados. | **Atendido, mas sem fechamento individual em `7.1`:** esclarecer que a reprodutibilidade das decisões do LLM decorre do arquivamento no `CallBank` (`C4-09`) e fechar o Obj. 3 em `7.1` (`C7-03`). |
| **Obj. Específico 4 (`01:20`):** estabelecer desenho experimental pareado e causal, com métrica primária e regra estatística definidas, sem vazamento de informação futura nos dados entregues aos agentes | Seções 4.8 e 5.2–5.6; retomado em `7.1–7.2` (`07:12,18`) | Relógio causal em 4 etapas (verificado por adulteração de barras futuras e *preflight* `decision_input_lookahead`), Sharpe líquido congelado e Bootstrap A ($B=5000$, bloco médio 10, semente 20261008). | **Atendido:** trocar *"pareado e causal"* por *"pareado, com relógio causal de informação"* em `01:20` (`C1-07`) e fechar nominalmente em `7.1`. |
| **Obj. Específico 5 (`01:21`):** executar o Replay Contínuo Abr–Nov/2026 e analisar a evolução entre as três versões, com decisões, operações e patrimônio rastreáveis | Seções 4.9, 4.10 e 6.1–6.5; fechado em `7.2–7.3` | Executado (918 estados diários reconciliados por versão; 4.703 / 4.702 / 4.703 chamadas lógicas auditadas) e analisado em detalhe no Cap. 6. | **Plenamente atendido.** |
| **Obj. Específico 6 (`01:22`):** operar a carteira multiativos em acompanhamento diário prospectivo, como base para avaliação livre de contaminação | Seções 4.11, 5.7.3 e 6.6 (`06:201-208`, págs. 62–63) | Ciclo diário em operação desde 14/10/2026 (autônomo desde 20/10); 23 pregões fechados até 16/11/2026 (Multiagentes v1 em R\$ 76.059,11 / $-23{,}94\%$ vs Buy \& Hold em R\$ 82.391,17 / $-17{,}61\%$). | **Fio solto na Conclusão:** a Seção 6.6 não explicita que a carteira prospectiva roda a **v1** (`C6-02`), e o Cap. 7 não resume o resultado preliminar desses 23 pregões nem fecha o Obj. 6 explicitamente (`C7-03`). |
| **Hipótese H1 (`01:28`, `05:44`):** estratégias de *momentum* e *trend following* superam *equal weight* em Sharpe líquido | Seção 6.3.1 (`06:68-74`, p. 54) e Seção 7.2 (`07:20`, p. 65) | **H0 não rejeitada:** SMA 50/200 ($S = -1{,}42$) vs Equal Weight 63d ($S = -0{,}71$), $\hat{\Delta} = -0{,}71$, $p_+ = 0{,}881$, IC 90\% $[-1{,}75;\ 0{,}31]$. Alcance restrito a uma regra de tendência. | **Respondida explicitamente.** Uniformizar redação de H1 no Cap. 1 com o Cap. 5 (`C1-01`) e discutir o impacto dos 31,39\% de caixa médio não remunerado da SMA 50/200 (`C5-04`). |
| **Hipótese H2 (`01:29`, `05:45`):** sistema multiagente LLM supera *benchmarks* em Sharpe líquido (primário) e Sortino, *Maximum Drawdown* e *turnover* (complementares) | Seções 6.3.2–6.3.3 (`06:75-88`, págs. 54–55) e Seção 7.2 (`07:22,26`, págs. 65–66) | **H0 não rejeitada na execução pré-especificada (v1):** patrimônio R\$ 82.178,71 ($-17{,}82\%$), $S = -1{,}28$, $\hat{\Delta} < 0$ contra 4 referências e $+0{,}14$ ($p_+ = 0{,}432$) contra SMA 50/200; todos $p_+$ Holm = 1,000; maior MDD ($-22{,}90\%$) e maior giro ($6{,}78\times$). v2 e v3 são exploratórias e descritivas; v3 vs SMA ($p_+ = 0{,}024$) não sobrevive a Holm ($0{,}121$) nem tem estatuto de teste. | **Respondida explicitamente e com rigor exemplar.** Uniformizar redação de H2 no Cap. 1 (`C1-01`). |
| **Hipótese H0 (`01:30`, `05:46`):** não há diferença estatisticamente significativa entre as abordagens | Seção 6.3.4 (`06:89-92`, p. 55) e Seção 7.2 (`07:24`, p. 65) | **Não rejeitada** em H1 nem em H2 (v1); texto ressalva corretamente que não rejeitar H0 não prova igualdade devido ao baixo poder em 153 pregões ($EP \approx 1{,}3$, amplitudes de IC 90\% entre 2,1 e 4,9 pontos de Sharpe) e à execução única ($R=1$). | **Respondida explicitamente.** |

### 3.3 Equilíbrio entre capítulos: diagnóstico e plano de cortes/expansões

Contagem exata no documento atual (68 páginas numeradas de texto, p. 1 a 68, mais 6 páginas de referências, p. 69 a 74):

| Capítulo | Palavras (prosa) | Págs. atuais (impressas) | % do corpo | Diagnóstico de equilíbrio | Ação recomendada (cortes, movimentações para apêndice e expansões) | Págs. alvo |
|---|---:|---:|---:|---|---|---:|
| **1. Introdução** | ~1.205 | 3 (p. 1–3) | 4,4\% | Curto para o padrão EIC/BCC | **Expandir (+0,8 pág.):** incluir citações na motivação, explicitar a lacuna da literatura, antecipar em 1 parágrafo os principais resultados empíricos e adicionar a declaração de uso de IA (guia EIC/BCC, Seções 2.1 e 2.5); eliminar a dupla formulação de contribuição (`01:8` vs `01:35`). | **3,5–4** |
| **2. Fundamentação** | ~1.820 | 7 (p. 4–10) | 10,3\% | **Subdimensionado e desalinhado** | **Cortar (−1,2 pág.):** remover Seção 2.4 (*Factor Investing*, `−0,5` p.), enxugar Seção 2.6 tirando resumos de artigos repetidos no Cap. 3 (`−0,5` p.) e fundir 2.5.2 em 2.8 (`−0,2` p.). **Expandir (+2,5 págs.):** incluir fórmulas e parâmetros do RSI e do MACD em 2.3.2 (`+0,5` p.), formulação da Mínima Variância com restrição *long-only* em 2.5.1 (`+0,3` p.) e criar a Seção `2.8 Inferência Estatística e Comparação Múltipla em Séries Financeiras` (*bootstrap* estacionário de Politis–Romano, erro-padrão de Lo e anomalia do Sharpe negativo, ajuste de Holm e teste de interseção–união, `+1,7` p.). | **8–8,5** |
| **3. Relacionados** | ~2.495 | 8 (p. 11–18) | 11,8\% | Bem dimensionado | **Ajustar (0 pág. líquido):** incluir 1 parágrafo de protocolo/critério de seleção da literatura na abertura (`+0,3` p., guia EIC/BCC, p. 9), eliminar repetição numérica de `FinCoT2025` com Cap. 2 (`−0,2` p.) e corrigir layout/posicionamento da Tabela 3.1. | **8** |
| **4. Arquitetura** | ~5.450 (6.300 c/ tabelas/TikZ) | 17 (p. 19–35) | **25,0\%** | **Superdimensionado (tom de inventário de código)** | **Cortar / mover para Apêndice A (−6,0 págs.):** (i) mover Tabela 4.1 (*Stack*) ou substituí-la por diagrama de componentes e levar o mapeamento de módulos/arquivos `.py` para o Apêndice A (`−1,0` p.); (ii) condensar Seções 4.6 (Ativo Único) e 4.12 (Camada de Experimentos `src/experiments`) em uma única seção de 1,5 pág., movendo a lista de scripts `spec.py`, `hardening.py`, `cal_b.py` etc. para o Apêndice A (`−1,8` p.); (iii) enxugar códigos de erro internos (`decision_input_lookahead`, `campaign_identity_changed`), nomes de arquivos `.json` intermediários (`before.json`, `context.json`), valores de reserva HTTP com 6 casas decimais (`US$ 0,110592`), detalhes de `publish_replay.py` e rotas HTTP de 4.9.1 e 4.9.3–4.9.5 (`−2,0` p.); (iv) mover Tabela 4.3 (constantes da v3, que já estão descritas nos 4 *bullets* de 4.10.2) para o Apêndice A (`−0,7` p.); (v) condensar detalhes de contêiner/rede privada de 4.11 e fundir 4.13 (`−0,5` p.). **Expandir (+0,8 pág.):** adicionar tabela com as fórmulas das 8 *features* adimensionais e explicar sua invariância causal ao fator de ajuste e a omissão de *ticker*/data/preço nos analistas. | **11,5–12** |
| **5. Metodologia** | ~4.110 | 13 (p. 36–48) | 19,1\% | Adequado, mas sem figuras e com p. 48 vazia | **Ajustar (0 pág. líquido):** eliminar os 16 `\paragraph{}` (que hoje consomem ~1,5 pág. em espaçamento vertical e criam a página 48 viúva), condensar `5.7.1` (`−0,5` p.), adicionar quadro-resumo de ameaças com sentido do viés e incluir **2 figuras novas** (linha do tempo e diagrama do desenho experimental pareado, `+1,5` p.). | **12–13** |
| **6. Resultados** | ~4.565 | 15 (p. 49–63) | 22,1\% | Adequado (coração empírico do TCC) | **Ajustar (+0,5 pág. líquido):** enxugar repetição literal de 6.5 com 5.8 (`−0,8` p.), acrescentar discussão da exposição em caixa/CDI e interpretação das Figuras 6.1–6.2 (`+0,5` p.) e incluir **1–2 figuras novas** (distribuição de placares/inversão do RSI entre v1–v3 e curva dos 23 pregões prospectivos, `+1,0` p.). | **15–15,5** |
| **7. Conclusão** | ~1.890 | 5 (p. 64–68) | 7,4\% | Adequado | **Ajustar (0 pág. líquido):** condensar a Seção 7.4 (evitando a 3ª cópia literal das limitações, `−0,5` p.) e incluir o fechamento explícito dos **6 objetivos específicos** do Cap. 1 em `7.1` (`+0,5` p.). | **5** |

### 3.4 Ordem das seções dentro de cada capítulo

1. **Capítulo 2 (Fundamentação Teórica):** hoje a Seção `2.2` (*Benchmarks Simples: Buy and Hold e Equal Weight*, p. 5) justifica a carteira Equal Weight pela ausência de estimação de *"retorno esperado e matriz de covariância, exigidos por modelos de otimização clássicos [Markowitz, 1952]"*, conceitos que só são introduzidos na Seção `2.5` (*Teoria Moderna de Portfólio*, p. 7). Além disso, `2.1` possui subseção única (`2.1.1`) e `2.5.2` tem uma só frase.
   - **Reordenação recomendada para o Cap. 2:**
     - `2.1 Eficiência de Mercado e Dinâmica Adaptativa` (`2.1.1 Hipótese de Eficiência de Mercado`; `2.1.2 Críticas Comportamentais e Hipótese de Mercados Adaptativos`)
     - `2.2 Estratégias Baseadas em Análise Técnica` (`2.2.1 Estratégias de Tendência`; `2.2.2 Estratégias de Reversão à Média e Osciladores` — com fórmulas de Bollinger, RSI e MACD)
     - `2.3 Teoria Moderna de Portfólio e Carteiras de Referência` (`2.3.1 Otimização Média-Variância e Carteira de Mínima Variância`; `2.3.2 Carteiras de Referência Passiva e Igualmente Ponderada: Buy & Hold e Equal Weight`) — *elimina a Seção 2.4 de Factor Investing e a micro-subseção 2.5.2*
     - `2.4 Sistemas Multiagentes e Modelos de Linguagem em Finanças` (conceitual: personas/papéis, votação por autoconsistência vs debate, raciocínio estruturado CoT e governança determinística)
     - `2.5 Backtesting em Séries Financeiras e Riscos Metodológicos` (*overfitting*, *data snooping*, PBO e contaminação temporal de LLMs)
     - `2.6 Métricas de Desempenho e Risco` (Retorno acumulado, Sharpe — incluindo seu comportamento sob retornos negativos —, Sortino, *Maximum Drawdown*, *turnover* e custos)
     - `2.7 Inferência Estatística na Comparação de Estratégias` *(nova)* (erro-padrão do Sharpe em amostras curtas, *bootstrap* estacionário temporal pareado de Politis–Romano, teste de interseção–união e controle de multiplicidade de Holm).
2. **Capítulo 4 (Arquitetura e Implementação):** hoje o leitor percorre seis seções (`4.1` a `4.6`, págs. 19–24) focadas em grande parte na arquitetura original de ativo único (`SQLAlchemy`, `H_real`, `engine.py`, grafo LangGraph) antes de chegar à carteira multiativos (`4.7`, p. 24) e ao Replay Contínuo (`4.9`, p. 27), que são a base de todos os resultados do TCC 2.
   - **Reordenação recomendada para o Cap. 4:** `4.1 Visão Geral da Arquitetura` → `4.2 Pipeline de Dados e Base de Mercado` → `4.3 Persistência e Livro Contábil de Eventos` → `4.4 Carteira Multiagente Multiativos` → `4.5 Relógio Causal do Pregão` → `4.6 Carteiras de Referência e Motor de Backtesting` (unificando 4.4 e 4.5) → `4.7 Arquitetura do Replay Contínuo` → `4.8 Evolução da Arquitetura entre as Versões (v1, v2 e v3)` → `4.9 Operação Diária e Interface de Acompanhamento` (unificando 4.11 e 4.13) → `4.10 Caminho de Ativo Único (LangGraph) e Proveniência Experimental` (unificando e condensando 4.6 e 4.12, com detalhes técnicos no Apêndice A).
3. **Capítulo 5 (Metodologia Experimental):** hoje as Seções `5.1` a `5.6` referenciam sete vezes o "protocolo original" e as decisões `DP-31`/`DP-37`, mas o leitor só descobre na Seção `5.7` (p. 45) o que era o protocolo original e por que não foi executado.
   - **Reordenação recomendada para o Cap. 5:** posicionar `5.2 Do Protocolo Planejado ao Replay Contínuo e ao Acompanhamento Prospectivo` (versão enxuta da atual Seção 5.7) logo após `5.1 Caracterização da Pesquisa`, seguida de `5.3 Desenho do Replay`, `5.4 Operacionalização das Hipóteses`, `5.5 Carteiras de Referência`, `5.6 Métricas de Avaliação`, `5.7 Inferência Estatística` e `5.8 Ameaças à Validade`.

### 3.5 Honestidade e consistência do tratamento v1 (confirmatória) vs v2/v3 (exploratórias)

O tratamento estatístico central — restringir a decisão inferencial sobre H2 exclusivamente à versão pré-especificada (v1), tratar v2 e v3 como iterações exploratórias *in-sample* cujos valores-$p$ são otimistas por construção, e rebaixar explicitamente o único contraste com $p_+ < 0{,}05$ bruto (`v3 vs SMA 50/200`, $p_+ = 0{,}024$, $p_+$ Holm $= 0{,}121$) — é **exemplar, honesto e cientificamente rigoroso**.

Há, contudo, **seis pontos específicos** em que a redação oscila ou deixa a v3 / o acompanhamento prospectivo parecerem mais fortes do que a evidência sustenta:
1. **Oscilação de vocabulário sobre o estatuto do replay e da v1 (`03:50`, `04:230`, `05:14`, `05:196` vs `Tabela 5.1`, `06:11`):** em `03:50` lê-se que o projeto *"reserva a avaliação confirmatória de agentes ao acompanhamento prospectivo e trata o replay retrospectivo como estudo exploratório"*, mas na Tabela 5.1 (`05:67-68`) e em `06:11` a família `H2 (v1)` recebe decisão inferencial sobre H0. Para blindar o texto contra a pergunta *"se o replay inteiro é exploratório, por que a v1 decide H2?"*, padronizar a distinção em três níveis em todos os capítulos: (i) o *replay* como um todo é **retrospectivo** (portanto sujeito à ameaça não verificável de contaminação do modelo); (ii) dentro do replay, a **v1 é pré-especificada** (regras fixadas antes de observar os 153 pregões) e é a única submetida a decisão inferencial sobre H2, condicionada à natureza retrospectiva da janela; (iii) **v2 e v3 são iterações exploratórias ajustadas dentro da amostra**, reportadas apenas descritivamente; e (iv) a avaliação **plenamente confirmatória e livre de contaminação** cabe ao acompanhamento prospectivo.
2. **Omissão do resultado da v2 no Resumo e no Abstract (`main.tex:56,61`):** saltar de `v1` ($-17{,}82\%$) direto para `v3` ($+0{,}07\%$) oculta que a primeira iteração de engenharia (`v2`, $-14{,}26\%$) também terminou em último lugar, abaixo das cinco referências (`C0-05`).
3. **Ambiguidade sobre qual versão está no acompanhamento prospectivo (`main.tex:56,61`, `01:10`, `04:349`, `05:200`, `06:204`):** dizer que a avaliação livre de contaminação *"depende do acompanhamento prospectivo, já em curso"* sem explicitar que o ciclo diário em produção executa a **arquitetura v1** (e que nos primeiros 23 pregões ela acumula $-23{,}94\%$ contra $-17{,}61\%$ do Buy \& Hold, `06:206`) faz parecer que a arquitetura `v3` já está sendo validada fora da amostra (`C0-05`, `C4-06`, `C6-02`).
4. **Equiparação retórica entre o retorno da v3 (+0,07%) e o da Bollinger 20/2 (+4,89%) (`06:52`):** a frase *"Apenas duas carteiras tiveram retorno positivo, ambas com perfil de compra em fraqueza e venda em força"* coloca $+0{,}07\%$ (R\$ 67,36 de ganho em 7 meses, Sharpe de $0{,}09$ com erro-padrão de $1{,}28$, caixa sem CDI e US\$ 8,63 de custo de inferência não deduzido) ao lado de $+4{,}89\%$ da Bollinger 20/2. Na prática, a v3 empatou com o capital nominal inicial (`C6-08`).
5. **Atribuição causal sem ablação (`06:177`, `07:36`):** afirmar que *"a governança determinística moldou o resultado tanto quanto os sinais"* atribui pesos causais iguais que o desenho em bloco não permite separar, além de mascarar o fato de que o compilador precisou corrigir a proposta do gestor **80 vezes** na v3 (56 vezes barrando vendas excessivas pelo piso de 8% e teto de 45% da posição) (`C6-04`).
6. **Afirmação de que o trabalho foi *"conduzido de modo a evitar o viés de superajuste"* (`01:35`):** como v2 e v3 introduzem pelo menos 17 limiares numéricos escolhidos após observar os mesmos 153 pregões (`C4-09`), o trabalho não *evita* o sobreajuste nas versões exploratórias — ele o **isola e documenta transparentemente** ao separar a v1 pré-especificada de v2/v3 (`C1-03`).

### 3.6 Conferência numérica integral contra as fontes de verdade

Foram conferidos todos os números do Resumo, Abstract, Cap. 1, Cap. 4, Cap. 5, Cap. 6 (texto, Tabelas 6.1–6.5 e Figuras 6.1–6.3) e Cap. 7 contra `METRICAS_REPLAY.md`, `BOOTSTRAP_REPLAY.md`, `tcc2/chapters/tabelas/*.tex`, `tcc2/figures/replay-series.csv`, `evolucao_replay_v1_v2_v3_tcc.md`, `comparacao_v1_v2_v3.json` e `equity_diario.csv`:
- **Paridade exata nos dados do Replay Contínuo:** todos os patrimônios finais, retornos totais e anualizados, volatilidades, Sharpes, Sortinos, *drawdowns* máximos, datas de pico e vale, durações (146, 146, 97, 119, 146, 85, 119, 120 pregões), contagens de operações (compras/vendas), custos em R\$, giros, percentuais de caixa médio e final, contrastes $\hat{\Delta}$, limites $[L_{95}; U_{95}]$, valores $p_+$, $p_+$ Holm e $p_-$, placares de votação (765, 760 e 745 pareceres), RSIs médios, contagens de ajustes do compilador (0, 26 e 80), chamadas lógicas (4.703, 4.702 e 4.703) e custos conhecidos estimados (US\$ 7,44, 8,92 e 8,63) **conferem integralmente com as fontes seladas**.
- **Quatro discrepâncias/inconsistências identificadas na verificação cruzada:**
  1. **`H_real` (1.519 sessões vs 4 sessões e 2.649 barras) em `04:72`, `05:188` e `MATRIZ_EVIDENCIAS.md:33`:** erro factual documentado em `C4-01` e `C5-02`.
  2. **`PETR4` dado como tendo "passado a resultado positivo" na v3 (`06:175`):** contradiz `06:156` e a tabela de resultado por ativo do documento mestre (§5.2: `PETR4` teve $-\text{R\$ } 1.783{,}77$ na v1, $+\text{R\$ } 1.812{,}50$ na v2 e $+\text{R\$ } 3.222{,}19$ na v3) (`C6-01`).
  3. **Base percentual do acompanhamento prospectivo (`06:206`):** R\$ 82.391,17 ($-17{,}61\%$) e R\$ 76.059,11 ($-23{,}94\%$) são variações sobre R\$ 100.000,00 (capital inicial em 13/10), mas a frase cita R\$ 99.835,33 (fechamento de 14/10) como início da trajetória, cuja variação até 16/11 seria $-17{,}47\%$ e $-23{,}82\%$ (`C6-02`).
  4. **Diferença aparente de 0,01 entre a Tabela 6.2 e a Tabela 6.4 em 9 de 16 contrastes (`06:54,66,85`):** a Tabela 6.2 exibe Sharpes arredondados a 2 casas (`v3 = 0,09`, `SMA = -1,42`, cuja diferença aparente é `1,51`), enquanto a Tabela 6.4 exibe $\hat{\Delta}$ calculado sobre os valores em ponto flutuante antes do arredondamento ($0{,}0862 - (-1{,}4173) = 1{,}5035 \to 1{,}50$). Os cálculos estão corretos, mas exigem nota explicativa na Tabela 6.4 (`C6-05`).
  *(Nota adicional de higiene do repositório: `METRICAS_REPLAY.md:5,36,37` e `MATRIZ_EVIDENCIAS.md:13-15,33,47` contêm observações desatualizadas em relação ao texto final da monografia — como dizer que as três versões foram ajustadas na janela ou marcar H1/H2/H0 como `PENDENTE`; embora não façam parte do PDF, convém alinhá-los após revisar o texto.)*

---

## 4. Achados detalhados

### 4.0 Padrões transversais (registrados uma vez com lista completa de ocorrências)

- **P-01** · **Severidade:** Crítico  
  **Local:** `tcc2/main.log:66-71` e todo o arquivo `tcc2/main.pdf` (PDF p. 1–86)  
  **Trecho:** `Package babel Warning: No hyphenation patterns were preloaded for the language 'Portuguese' into the format. ... I will use the patterns preloaded for \language=0 instead.`  
  **Problema:** O `main.pdf` versionado foi compilado em um ambiente TeX Live sem os padrões de hifenização do português carregados no formato, aplicando regras silábicas do inglês ao documento inteiro. Isso produz dezenas de divisões silábicas incorretas em português visíveis no PDF: `refer-ência` (p. 1 / PDF p. 13), `trabal-hos` (p. 12 / PDF p. 24), `mod-elo` (p. 12–13 / PDF p. 24–25), `ver-ificada` (p. 21 / PDF p. 33), `sim-ulação` e `cal-endário` (p. 22 / PDF p. 34), `anal-istas` (Fig. 4.3, p. 26 / PDF p. 38), `autor-izada` (p. 28 / PDF p. 40), `reex-ecutada`, `fal-has` e `sub-stituição` (p. 29 / PDF p. 41), `extrap-olação` (p. 42 / PDF p. 54), `ex-ecuções` e `aprox-imado` (p. 43–44 / PDF p. 55–56), `oper-ações` (p. 63 / PDF p. 75), `req-uisição` (p. 64 / PDF p. 76).  
  **Correção proposta:** Recompilar o projeto em ambiente com `babel-portuges` ativo (no MiKTeX local já instalado na máquina dos autores, `\l@portuguese` carrega normalmente e elimina todas essas quebras; no Arch Linux/TeX Live, instalar `texlive-langportuguese` e regerar os formatos com `fmtutil-sys --all`). Conferir no `main.log` a ausência do aviso antes de gerar o PDF final.

- **P-02** · **Severidade:** Crítico  
  **Local:** Sumário (PDF p. 10–12) e 34 ocorrências nos Caps. 5, 6 e 7: `05-metodologia.tex:75, 77, 79, 83, 115, 124, 133, 135, 137, 205, 207, 209, 211, 213, 215, 217` (16×, p. 39–47 / PDF p. 51–59); `06-resultados.tex:52, 54, 56, 58, 60, 167, 169, 171, 173, 175, 177, 179, 184, 186` (14×, p. 50–61 / PDF p. 62–73); `07-conclusao.tex:20, 22, 24, 26` (4×, p. 65 / PDF p. 77)  
  **Trecho:** `\paragraph{H1.}`, `\paragraph{Sharpe Ratio líquido (critério primário).}`, `\paragraph{Diversidade do comitê.}` → impressos no corpo e no Sumário como `5.3.0.0.1 H1.`, `5.5.0.0.1 Sharpe Ratio líquido (critério primário).`, `6.4.3.0.1 Diversidade do comitê.`, `7.2.0.0.1 H1.`  
  **Problema:** A classe `eic-bcc-tcc.cls:558-559` configura `\setcounter{secnumdepth}{5}` e `\setcounter{tocdepth}{5}`, tratando `\paragraph` como seção quinária numerada (`x.y.z.w.v`). Como os capítulos usam `\paragraph{...}` diretamente dentro de `\section` (pulando `\subsection` e `\subsubsection`) ou dentro de `\subsection` (pulando `\subsubsection`), o LaTeX preenche os níveis ausentes com `.0.0.` ou `.0.`, violando a numeração progressiva da ABNT NBR 6024, poluindo 3 páginas do Sumário com 34 títulos em itálico terminados em ponto final e gerando 13 avisos `Difference (2/3) between bookmark levels is greater than one` no `hyperref`.  
  **Correção proposta:** Substituir `\paragraph{Título.}` por `\paragraph*{Título.}` (ou iniciar o parágrafo com `\textbf{Título.}`) onde a intenção for apenas um tópico destacado em linha; ou promover a `\subsection{Título}` (sem ponto final) nas divisões estruturais maiores (como `5.8.1`–`5.8.7` na Seção 5.8 e `6.5.1`–`6.5.2` na Seção 6.5).

- **P-03** · **Severidade:** Crítico  
  **Local:** `main.tex:19-27, 67` (PDF p. 8 em branco) e todas as ocorrências de siglas nos Caps. 1 a 7  
  **Trecho:** `\newacronym{tcc}{TCC}{Trabalho de Conclusão de Curso}` ... `\listofacronymspage`  
  **Problema:** Nenhum dos 9 acrônimos declarados em `main.tex:19-27` é invocado no texto com `\gls{...}` (ou `\acrshort`/`\acrlong`). Por isso, o pacote `glossaries` gera um arquivo `main.acn` vazio (0 bytes) e a página da **Lista de Acrônimos (PDF p. 8) sai completamente em branco**, descumprindo o guia oficial (`Trabalho de Conclusao EIC BCC.pdf`, Seção 1.4.3, p. 3–4 / PDF p. 11, 16–17). Além disso:
  - **Declarados em `main.tex` e nunca usados como sigla no texto (2):** `etl` (`ETL`) e `mas` (`MAS`).
  - **Definidos manualmente duas vezes no texto:** `Large Language Models (LLMs)` é expandido em `01-introducao.tex:6` e novamente em `02-fundamentacao.tex:108`; `Moving Average Convergence Divergence` é expandido em `02-fundamentacao.tex:78`.
  - **Usados no texto sem declaração em `main.tex` e/ou sem expansão no primeiro uso (20):** `B3` (`main.tex:56`, `01:8`), `COTAHIST` (`main.tex:56`, `01:8`), `OHLCV` (`04:77`), `RAW` (`04:77`), `JCP` (`04:217` — Juros sobre Capital Próprio, nunca expandido), `SLSQP` (`04:242` — *Sequential Least Squares Programming*, nunca expandido), `MDD` (`metricas-replay.tex:11` — *Maximum Drawdown*, nunca definido como sigla antes da Tabela 6.2), `MAR` (`02:140` — usado sem expansão na p. 10 e só expandido na p. 42, `05:124`), `HAD` (`02:116`), `DQN`, `TDQN` e `PPO` (`03:10`), `LSTM` (`03:18`), `CFA` (`03:26`), `KDJ` (`03:33`), `CVaR` (`03:35`), `ARIMA` (`03:48`), `GSM8K` (`03:54`), `HTTP` (`04:21`), `JSON`, `CSRF` (`04:368`), `CSV` (`04:258`), `SHA-256` (`04:77`).  
  **Correção proposta:** (1) Remover `etl` e `mas` de `main.tex` (ou usá-los de fato no texto); (2) declarar em `main.tex` as siglas relevantes do domínio (`b3`, `cotahist`, `ohlcv`, `jcp`, `slsqp`, `mdd`, `mar`, `cvar`, `lstm`, `ppo`, `dqn`, `http`, `json`, `csv`, `csrf`, `sha256`); (3) usar `\gls{...}` / `\glspl{...}` na primeira ocorrência (e `\glsaddall` se desejar garantir a impressão completa) e executar `makeglossaries main` (ou `makeindex -s main.ist -t main.alg -o main.acr main.acn`) na compilação.

- **P-04** · **Severidade:** Alto  
  **Local:** `main.tex:37` e 328 ocorrências de `\texttt{...}` (concentradas no Cap. 4 e nas Tabelas 6.2–6.4), além dos 10 `Overfull \hbox` listados em `main.log:1498-1584`  
  **Trecho:** `\usepackage[htt]{hyphenat}` → `b3_-calendar.py` (p. 20), `continuous_replay_-data.py` (p. 20), `technical_-analyst.py` (p. 23–24), `HARD_ASSET_VOLATILITY_-RULE` (p. 25), `auction_or-ders.py::plan` (p. 25), `H2_SCIENTIFIC_-SHARPE_DEFINITION_V1` (PDF p. 7 e p. 50), `NO_-ANALYSIS` (p. 53)  
  **Problema:** O pacote `hyphenat` com opção `[htt]` hifeniza texto monoespaçado inserindo um hífen `-` visível logo após o caractere `_`, adulterando a grafia de nomes de arquivos e constantes no PDF, além de produzir 31 avisos de fonte no `main.log` e ainda deixar escapar 4 estouros de margem em `\texttt` (`04:74` com `+33,49 pt`, `05:113` com `+13,30 pt`, `04:113` com `+11,42 pt` e `04:262` com `+6,50 pt`).  
  **Correção proposta:** Remover `\usepackage[htt]{hyphenat}` de `main.tex:37`. Para caminhos de arquivo e rotas HTTP que permanecerem no texto após o enxugamento do Cap. 4, utilizar `\path{src/backtesting/b3_calendar.py}` (do pacote `url`, já carregado por `eic-bcc-tcc.cls:62`), que quebra linhas limpas após `/` e `_` **sem inserir hífen falso** e sem gerar avisos de fonte.

- **P-05** · **Severidade:** Médio  
  **Local:** 34 ocorrências nos Caps. 1, 4, 5, 6 e 7 (visíveis com quebra entre o cifrão e o número em `p. 52, 54, 57, 58, 59, 62` do texto / `PDF p. 64, 66, 69, 70, 71, 74`)  
  **Trecho:** `e R$ / 4.819,69` (`06:52`, p. 52); `R$ / 22.708,34` (`06:80`, p. 54); `R$ / 5.443,38` (`06:136`, p. 57); `(+R$ / 11.200,68)` e `(+R$ / 10.198,07)` (`06:165`, p. 58); `R$ / 21,48)` (`06:171`, p. 59); `US$ / 8,63` (`06:195`, p. 62)  
  **Problema:** O espaço comum entre `R\$` (ou `US\$`, `DP-`, `Seção`, `Capítulo`, `Tabela`, `Figura`) e o número permite quebra de linha no fim da margem, deixando o símbolo monetário órfão no fim da linha superior.  
  **Correção proposta:** Substituir globalmente `R\$ ` por `R\$~` e `US\$ ` por `US\$~` nos arquivos `.tex` (bem como usar `~` após `Seção`, `Capítulo`, `Tabela` e `Figura`).

- **P-06** · **Severidade:** Médio  
  **Local:** Estrangeirismos em todos os capítulos (`main.tex` e `01` a `07`)  
  **Trecho:** `replay` (romano 98× vs `\textit{replay}` 2× em `04:84`, `05:14`); `pipeline` (romano 12×); `momentum` (romano 4× em `01:28`, `02:16,50,56` vs `\textit{momentum}` 8×, e traduzido como `"momento"` em `03:16`); `features` (romano 7× no Cap. 4 vs `\textit{features}` em `05:205`); `spread` (romano em `02:143` vs `\textit{spread}` 5×); `z-score` (romano em `02:60` vs `\textit{z-score}` 3×); `drawdown` (romano em `replay-drawdown.tex:9,35` vs `\textit{drawdown}` 18×); `a priori` (romano em `05:219`); `corpus` (romano em `03:46`, `05:205`); `framework`, `stack`, `frontend`, `lock`, `runners`, `gates` (romano no Cap. 4)  
  **Problema:** Oscilação constante entre itálico e redondo para os mesmos termos estrangeiros.  
  **Correção proposta:** Fixar e aplicar em todo o documento uma regra única: **todo substantivo ou expressão comum em língua estrangeira vai em itálico** (`\textit{replay}`, `\textit{pipeline}`, `\textit{momentum}`, `\textit{features}`, `\textit{spread}`, `\textit{z-score}`, `\textit{drawdown}`, `\textit{backtesting}`, `\textit{bootstrap}`, `\textit{overfitting}`, `\textit{turnover}`, `\textit{benchmark}`, `\textit{corpus}`, `\textit{a priori}`, `\textit{framework}`, `\textit{frontend}`, `\textit{stack}`, `\textit{lock}`, `\textit{gates}`), enquanto **nomes próprios de campanhas, carteiras, procedimentos nomeados e bibliotecas ficam em redondo** (`Replay Contínuo Abril–Novembro de 2026`, `Buy & Hold`, `Equal Weight 63d`, `Bootstrap A`, `LangGraph`, `Chart.js`).

- **P-07** · **Severidade:** Médio  
  **Local:** Padronização de nomes e termos técnicos nos Caps. 0 a 7  
  **Trecho:** (i) `superajuste` (`main.tex:56`, `01:4,35`) vs `sobreajuste` (`03:12,50`, `05:207`, `07:48`); (ii) `TCC1` (`05:16,41`) vs `etapa anterior do trabalho` (`01:10,25`) vs `TCC 1` (`WRITING_RULES.md`); (iii) `Equal Weight 63d` vs `Equal Weight` (`main.tex:56,61`, `06:58`) vs `pesos iguais` (`03:84`, `04:92,242`, `05:75,108,217`, `06:68,71,92`); (iv) `Mínima Variância 252/63` vs `Mínima Variância` (`main.tex:56`, `05:75`, `06:58`) vs `mínima variância` (`03:84`, `04:90,92,242`); (v) `Multiagentes v1` vs `MA v1` (`bootstrap-replay.tex:14-30`, sigla nunca definida que colide com `MA` de média móvel); (vi) `Sharpe Ratio` / `Sharpe ratio` / `índice de Sharpe` e `Sortino Ratio` / `Sortino ratio`; (vii) `Bootstrap A` vs `\textit{bootstrap} A` (`bootstrap-replay.tex:4`); (viii) `valor-$p$` vs `p-valores` (`bootstrap-replay.tex:33`); (ix) `H0` vs `$H_0$` (`bootstrap-replay.tex:33`); (x) `piso núcleo` vs `piso de posição-núcleo`  
  **Problema:** Dez variações terminológicas para os mesmos objetos ao longo do texto.  
  **Correção proposta:** Padronizar: (i) **sobreajuste (\textit{overfitting})**; (ii) **TCC 1**; (iii) **Equal Weight 63d** (para a carteira) e *pesos iguais* apenas ao explicar o conceito; (iv) **Mínima Variância 252/63** (para a carteira); (v) **Multiagentes v1/v2/v3** (ou `v1/v2/v3` na Tabela 6.4, nunca `MA v1`); (vi) **índice de Sharpe** (ou **Sharpe Ratio**, mantendo uma só forma) e **índice de Sortino**; (vii) **Bootstrap A**; (viii) **valor-$p$ / valores-$p$**; (ix) **H0**; (x) **piso de posição-núcleo**.

- **P-08** · **Severidade:** Médio  
  **Local:** 30 ocorrências de identificadores `DP-n` nos Caps. 4, 5 e 6 (`04:4, 77, 217, 230, 240, 349, 353`; `05:18, 29, 32, 75, 99-101, 108, 194, 200`; `06:204, 206, 208`) e fontes das Tabelas 6.1–6.5 (`06:36, 126`, `metricas-replay.tex:24,48`, `bootstrap-replay.tex:33`)  
  **Trecho:** `"autorizada pela DP-37, que reabre a DP-31"` (`05:18`, p. 36 — nove páginas antes de `DP-31` ser explicada em `05:194`, p. 45!); `"Fonte: documento mestre do replay (evolucao_replay_v1_v2_v3_tcc.md, Seção 1.2), a partir de operacoes_v3.csv"` (`06:36`, p. 49)  
  **Problema:** A monografia precisa ser autossuficiente para um leitor que não está com o repositório Git aberto. Invocar códigos internos de gestão (`DP-11`, `DP-20`, `DP-27`, `DP-30`, `DP-31`, `DP-33` a `DP-37`) antes de defini-los ou citar arquivos `.md`/`.csv` internos como fonte de tabelas acadêmicas prejudica a fluidez e a autonomia do texto.  
  **Correção proposta:** Sempre enunciar primeiro a regra substantiva no texto (e, se desejar manter o código `DP-n` para rastreabilidade com o repositório, colocá-lo entre parênteses ou resumir as DPs citadas em um quadro no Apêndice A). Nas fontes das Tabelas 4.1–6.5 e Figuras 4.1–6.3, adotar o padrão ABNT (`Fonte: elaborado pelos autores com base nos dados oficiais da B3 (COTAHIST) e nos registros auditados das campanhas do Replay Contínuo.`).

- **P-09** · **Severidade:** Médio  
  **Local:** 11 floats sem linha de `Fonte:` (Figuras 4.1, 4.2, 4.3, 6.1, 6.2, 6.3 e Tabelas 4.1, 4.2, 4.3, 5.1, 5.2) e 6 floats com legendas longas que poluem a Lista de Figuras e a Lista de Tabelas (PDF p. 6–7: Figuras 4.1, 4.2, 4.3, 6.1 e Tabelas 6.2, 6.3, 6.4)  
  **Trecho:** Lista de Tabelas (PDF p. 7): a Tabela 6.4 ocupa 7 linhas inteiras na lista; a Tabela 6.2 ocupa 4 linhas com `H2_SCIENTIFIC_-SHARPE_DEFINITION_V1` quebrado.  
  **Problema:** (1) Inconsistência interna e frente à ABNT NBR 14724: as Tabelas 3.1 e 6.1–6.5 trazem linha de `Fonte:` abaixo, mas as Tabelas 4.1–5.2 e todas as 6 figuras não trazem; (2) ausência do argumento opcional curto `\caption[Título curto para a lista]{Título completo e notas explicativas}` faz toda a explicação metodológica das legendas aparecer no pré-textual.  
  **Correção proposta:** (1) Padronizar `\par\smallskip\footnotesize Fonte: elaborado pelos autores...` abaixo de todas as 6 figuras e 11 tabelas; (2) usar `\caption[Título curto]{Título completo}` nas Figuras 4.1–4.3 e 6.1 e nas Tabelas 6.2–6.4 (ajustando diretamente nos scripts geradores `tcc2/scripts/metricas_replay.py` e `bootstrap_replay.py`).

---

### Capítulo 0 — Elementos Pré-Textuais, Resumo e Abstract (`main.tex`; PDF p. 1–12)

- **C0-01** · **Severidade:** Crítico  
  **Local:** `main.tex:19-27, 67` (PDF p. 8 — página da Lista de Acrônimos em branco)  
  **Trecho:** `\newacronym{tcc}{TCC}{Trabalho de Conclusão de Curso}` ... `\listofacronymspage`  
  **Problema:** Conforme detalhado em `P-03`, a ausência de `\gls{}` deixa `main.acn` vazio e produz a **página 8 do PDF inteiramente em branco**, além de manter `etl` e `mas` declarados sem uso e 20 siglas usadas sem declaração.  
  **Correção proposta:** Aplicar a correção de `P-03` em `main.tex` e nos capítulos e rodar `makeglossaries main` (ou `makeindex -s main.ist -t main.alg -o main.acr main.acn`).

- **C0-02** · **Severidade:** Alto  
  **Local:** `main.tex:43` (PDF p. 9 — Sumário)  
  **Trecho:** `\renewcommand{\cfttoctitlefont}{\hspace{0.4\textwidth}\large\bfseries}`  
  **Problema:** O título `SUMÁRIO` usa deslocamento fixo `\hspace{0.4\textwidth}` sem `\renewcommand{\cftaftertoctitle}{\hfill}`, ficando visivelmente desalinhado à esquerda na p. 9 do PDF, ao contrário de `LISTA DE FIGURAS` e `LISTA DE TABELAS` (que usam `\hfill` antes e depois).  
  **Correção proposta:** Substituir `main.tex:43` por:
  ```latex
  \renewcommand{\cfttoctitlefont}{\hfill\large\bfseries}
  \renewcommand{\cftaftertoctitle}{\hfill}
  ```

- **C0-03** · **Severidade:** Alto  
  **Local:** `main.tex:56` e `main.tex:61` (PDF p. 4 e 5 — Resumo e Abstract)  
  **Trecho:** `A avaliação de estratégias quantitativas em mercados não estacionários é sujeita a custos, dependência de regime e superajuste. Este trabalho apresenta o Hedge-fund-lab... A v1 terminou em $-17{,}82\%$, abaixo das cinco referências, e nenhum de seus contrastes rejeitou a hipótese nula; a SMA 50/200 tampouco superou a Equal Weight. A v3 terminou em $+0{,}07\%$, acima de quatro referências e abaixo da Bollinger 20/2 ($+4{,}89\%$), resultado otimista por construção. ... A avaliação livre de contaminação do modelo depende do acompanhamento prospectivo, já em curso.`  
  **Problema:** O Resumo (265 palavras, parágrafo único — dentro do limite de 150–500 palavras da ABNT NBR 6028 e de até 500 palavras do guia EIC/BCC) e o Abstract (250 palavras) apresentam três problemas importantes:
  1. **Ausência da lacuna (*Gap*):** o modelo oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, p. 7 do PDF) exige que o resumo contenha explicitamente *Contextualização, Gap, Objetivo, Metodologia e Resultados*. Falta uma frase explicitando a lacuna na avaliação de agentes LLM (janelas curtas, foco no mercado dos EUA e ausência de controle de custos e contaminação temporal).
  2. **Omissão do resultado da v2:** o texto anuncia três versões (`v1`, `v2` e `v3`), mas reporta apenas os números da `v1` ($-17{,}82\%$) e da `v3` ($+0{,}07\%$), omitindo que a `v2` ($-14{,}26\%$) também encerrou abaixo das cinco referências.
  3. **Ambiguidade sobre o acompanhamento prospectivo:** *"depende do acompanhamento prospectivo, já em curso"* sugere que a arquitetura aprimorada (`v3`) já está sendo validada prospectivamente, quando na realidade o ciclo diário em produção (`dashboard/daily_cycle.py:44`) opera a arquitetura da `v1` (e o congelamento prospectivo da `v3` é proposto como trabalho futuro em `07:61`).  
  **Correção proposta (pronta para colar em `main.tex:55-63`):**
  ```latex
  \begin{resumo}
  A avaliação de estratégias quantitativas em mercados não estacionários é sujeita a custos, dependência de regime e sobreajuste, enquanto estudos recentes com agentes baseados em \textit{Large Language Models} (LLMs) frequentemente utilizam janelas curtas, ações norte-americanas e controles parciais de custos e de contaminação temporal. Este trabalho apresenta o Hedge-fund-lab, laboratório quantitativo de \textit{backtesting} baseado em sistemas multiagentes, e o emprega para verificar se uma carteira decidida por agentes baseados em LLMs apresenta desempenho ajustado ao risco superior ao de carteiras de referência clássicas. O laboratório integra dados oficiais da B3 (COTAHIST), um livro contábil de eventos auditável e comitês de analistas técnicos, analistas de risco e um gestor de carteira, cuja proposta é submetida a um compilador determinístico de regras. O estudo empírico é um \textit{replay} retrospectivo de 153 pregões, de abril a novembro de 2026, com cinco ações e R\$~100 mil por carteira, no qual a carteira multiagente é comparada a cinco referências determinísticas (Buy \& Hold, SMA 50/200, Bollinger 20/2, Equal Weight 63d e Mínima Variância 252/63) em três versões: a v1, pré-especificada, e as v2 e v3, iterações exploratórias desenhadas após a observação do mesmo período. As hipóteses são decididas pelo índice de Sharpe líquido com \textit{bootstrap} estacionário pareado (Bootstrap A). A v1 terminou em $-17{,}82\%$ e a v2 em $-14{,}26\%$, ambas abaixo das cinco referências, e nenhum contraste da v1 rejeitou a hipótese nula; a SMA 50/200 tampouco superou a Equal Weight 63d. A v3 terminou em $+0{,}07\%$, acima de quatro referências e abaixo da Bollinger 20/2 ($+4{,}89\%$), resultado otimista por construção. Conclui-se que não há evidência de superioridade dos agentes e que, nesta trajetória, a especialização do comitê e a governança determinística alteraram de forma mensurável o comportamento da carteira. A avaliação livre de contaminação depende do acompanhamento prospectivo, iniciado em outubro de 2026 com a arquitetura da v1, ficando a avaliação prospectiva da v3 com regras congeladas como trabalho futuro.
  \palavraschave{Análise Quantitativa. Sistemas Multiagentes. \textit{Large Language Models}. \textit{Backtesting}. Mercado Acionário Brasileiro.}
  \end{resumo}

  \begin{abstract}
  The evaluation of quantitative strategies in non-stationary markets is subject to costs, regime dependence, and overfitting, whereas recent studies on trading agents based on Large Language Models (LLMs) often rely on short windows, U.S. equities, and partial controls for transaction costs and temporal contamination. This work presents the Hedge-fund-lab, a quantitative backtesting laboratory based on multi-agent systems, and uses it to test whether a portfolio managed by LLM-based agents achieves higher risk-adjusted performance than classical benchmark portfolios. The laboratory integrates official B3 trading records (COTAHIST), an auditable event ledger, and committees of technical analysts, risk analysts, and a portfolio manager whose proposal is submitted to a deterministic rule compiler. The empirical study is a retrospective replay of 153 trading sessions, from April to November 2026, with five stocks and BRL 100,000 per portfolio, in which the multi-agent portfolio is compared with five deterministic benchmarks (Buy \& Hold, SMA 50/200, Bollinger 20/2, Equal Weight 63d, and Minimum Variance 252/63) in three versions: v1, pre-specified, and v2 and v3, exploratory iterations designed after observing the same period. The hypotheses are decided on the net Sharpe ratio with a paired stationary bootstrap (Bootstrap A). Version v1 ended at $-17.82\%$ and v2 at $-14.26\%$, both below all five benchmarks, and none of the v1 contrasts rejected the null hypothesis; SMA 50/200 did not outperform Equal Weight 63d either. Version v3 ended at $+0.07\%$, above four benchmarks and below Bollinger 20/2 ($+4.89\%$), a result optimistic by construction. The study concludes that there is no evidence of agent superiority and that, along this trajectory, committee specialization and deterministic governance measurably changed the portfolio's behavior. A contamination-free evaluation depends on prospective daily tracking, initiated in October 2026 with the v1 architecture, while a frozen-rule prospective evaluation of v3 is left for future work.
  \keywords{Quantitative Analysis. Multi-Agent Systems. Large Language Models. Backtesting. Brazilian Stock Market.}
  \end{abstract}
  ```

- **C0-04** · **Severidade:** Baixo  
  **Local:** `main.tex:9-11, 38-40`  
  **Trecho:** `\newcommand{\warn}[1]{{\color{red} {#1}}}` / `\newcommand{\verify}[1]{{\color{blue} {#1}}}` / `\newcommand{\remarks}[2]{{\color{red} #1\ (\textit{#2})}}` e comentário `% ponytail:`  
  **Problema:** Macros de rascunho não utilizadas nos capítulos e comentário interno de agente no preâmbulo principal.  
  **Correção proposta:** Remover `main.tex:9-11` e substituir o comentário das linhas 38–40 por `% Ajuste dos títulos do tocloft para evitar erro de \MakeUppercase sem argumento no TeX Live / MiKTeX 2026.`

*Balanço micro do Cap. 0:* **4 blocos pré-textuais revisados** (Resumo, Palavras-chave, Abstract, Keywords, além do preâmbulo e listas); **4 apresentaram problemas**.

---

### Capítulo 1 — Introdução (`chapters/01-introducao.tex`; p. 1–3 / PDF p. 13–15)

- **C1-01** · **Severidade:** Crítico  
  **Local:** `chapters/01-introducao.tex:28-29` vs `chapters/05-metodologia.tex:44-45` (p. 3 vs p. 38 / PDF p. 15 vs p. 50)  
  **Trecho:** `\item \textbf{H1:} Será avaliado se estratégias baseadas em momentum e \textit{trend following} apresentam desempenho superior ao \textit{equal weight} em termos de Sharpe Ratio líquido.` / `\item \textbf{H2:} Será avaliado se o sistema multiagente baseado em LLMs apresenta desempenho superior...`  
  **Problema:** (1) Uma hipótese científica é uma proposição declarativa passível de teste, e não uma promessa de tarefa no futuro (*"Será avaliado se..."*, resquício de projeto de TCC 1); (2) ambos os capítulos afirmam preservar as hipóteses do TCC 1, mas **o enunciado no Cap. 1 diverge do enunciado no Cap. 5 (`05:44-45`)**, onde o prefixo *"Será avaliado se"* já foi removido. Além disso, `momentum` está em redondo na L28 ao lado de `\textit{trend following}` em itálico.  
  **Correção proposta:** Uniformizar `01-introducao.tex:27-31` com a forma declarativa do Cap. 5:
  ```latex
  \begin{itemize}
      \item \textbf{H1:} Estratégias baseadas em \textit{momentum} e \textit{trend following} apresentam desempenho superior ao \textit{equal weight} em termos de Sharpe Ratio líquido.
      \item \textbf{H2:} O sistema multiagente baseado em LLMs apresenta desempenho superior ajustado ao risco em relação aos \textit{benchmarks} considerados, tomando como critério principal o Sharpe Ratio líquido e, como critérios complementares, Sortino Ratio, \textit{Maximum Drawdown} e \textit{turnover}.
      \item \textbf{H0:} Não há diferença estatisticamente significativa entre as abordagens.
  \end{itemize}
  ```

- **C1-02** · **Severidade:** Alto  
  **Local:** `chapters/01-introducao.tex:4-37` (p. 1–3 / PDF p. 13–15)  
  **Trecho:** (capítulo inteiro sem nenhuma citação `\cite`/`\citep`/`\citet`, sem explicitar a lacuna da literatura na motivação e sem resumo dos resultados alcançados)  
  **Problema:** (1) O Capítulo 1 faz afirmações teóricas e empíricas sobre não estacionariedade, sensibilidade de regras técnicas a regimes, sobreajuste em *backtesting* (`01:4`), agentes LLM em finanças (`01:6`) e *"viés de superajuste que caracteriza boa parte da literatura aplicada"* (`01:35`) **sem uma única citação bibliográfica**; (2) o guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, Seção 2 e 2.1, p. 6 / PDF p. 19) estabelece que a Introdução deve deixar clara a **lacuna da literatura** na motivação e incluir os **principais resultados alcançados** antes da estrutura do trabalho.  
  **Correção proposta:**
  - Reescrever `01-introducao.tex:4` com citações e explicitando a lacuna:
    > `O mercado financeiro contemporâneo impõe desafios relevantes à construção e à avaliação de estratégias quantitativas, sobretudo em cenários marcados por alta volatilidade e não estacionariedade \citep{Lo2004}. Nesse contexto, abordagens clássicas de análise técnica continuam úteis como referência metodológica, mas frequentemente apresentam limitações quando aplicadas de forma isolada, seja pela sensibilidade a regimes de mercado distintos, seja pelo risco de sobreajuste (\textit{overfitting}) e mineração de dados em processos de \textit{backtesting} \citep{White2000, Bailey2017}. Embora sistemas multiagentes baseados em \textit{Large Language Models} (LLMs) venham sendo propostos para integrar sinais e estruturar decisões financeiras \citep{Li2023, TradingAgents2024, Xia2026}, grande parte das avaliações reportadas na literatura apoia-se em janelas temporais curtas, concentra-se no mercado norte-americano e carece de controles explícitos para custos operacionais, intervenção determinística sobre propostas do modelo e contaminação temporal pelo conhecimento prévio do período avaliado \citep{Glasserman2023, FINSABER2026}. Essa lacuna justifica a proposição de um ambiente experimental capaz de organizar dados, regras de decisão e critérios de avaliação de maneira rigorosa, como condição prévia à investigação de desempenho superior.`
  - Acrescentar um parágrafo curto de síntese dos resultados antes de `01-introducao.tex:37`:
    > `No estudo empírico conduzido, a versão pré-especificada da carteira Multiagentes (v1) encerrou os 153 pregões com retorno de $-17{,}82\%$, abaixo das cinco referências determinísticas, e nenhum contraste rejeitou H0 pelo Bootstrap A; a regra de tendência SMA 50/200 tampouco superou a carteira Equal Weight 63d ($\hat{\Delta} = -0{,}71$; $p_{+} = 0{,}881$). Nas iterações exploratórias desenhadas após a auditoria do mesmo período, o patrimônio final evoluiu para $-14{,}26\%$ na v2 e $+0{,}07\%$ na v3 --- esta última acima de quatro referências e abaixo da Bollinger 20/2 ($+4{,}89\%$), em resultado otimista por construção ---, evidenciando descritivamente o efeito da especialização funcional do comitê e da governança determinística sobre o comportamento da carteira, sem sustentar superioridade dos agentes.`

- **C1-03** · **Severidade:** Alto  
  **Local:** `chapters/01-introducao.tex:35` (p. 3 / PDF p. 15)  
  **Trecho:** `e com o registro de resultados negativos, conduzido de modo a evitar o viés de superajuste que caracteriza boa parte da literatura aplicada.`  
  **Problema:** Como as versões v2 e v3 foram desenhadas e parametrizadas após observar os erros nos mesmos 153 pregões (`05:81`), o trabalho não *evitou* o sobreajuste nelas; o que o desenho fez foi **isolar e expor o risco de sobreajuste** ao separar estritamente a execução pré-especificada (v1, única com decisão inferencial) das iterações ajustadas dentro da amostra (v2 e v3, puramente descritivas). Dizer que o estudo "evitou o viés de superajuste" convida a banca a atacar as 17 constantes da v3.  
  **Correção proposta:** Substituir o trecho final de `01:35` por:
  > `e com o relato transparente de resultados negativos e a separação estrita entre a execução pré-especificada (v1) e as iterações ajustadas dentro da amostra (v2 e v3), expondo e controlando metodologicamente o risco de sobreajuste documentado na literatura aplicada \citep{White2000, Bailey2017}.`

- **C1-04** · **Severidade:** Alto  
  **Local:** `chapters/01-introducao.tex:37` (final do Cap. 1, p. 3 / PDF p. 15)  
  **Trecho:** (ausência de declaração sobre uso de IA generativa na elaboração do trabalho)  
  **Problema:** O guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, Seção 2.5, p. 7 / PDF p. 20) prevê uma declaração explícita na Introdução informando como ferramentas de IA generativa foram utilizadas no auxílio à construção do texto científico, quando aplicável.  
  **Correção proposta:** Inserir ao final do Capítulo 1 (adaptando ao uso real feito pelos autores, conforme modelo da p. 7 do guia EIC/BCC):
  > `Durante a elaboração desta monografia, ferramentas de inteligência artificial generativa foram utilizadas como apoio para revisão de linguagem, organização textual e verificação de scripts de auditoria. Todo o conteúdo técnico, o desenho metodológico, a execução experimental, os resultados e as conclusões são de responsabilidade dos autores, que verificaram e editaram integralmente o material produzido against os artefatos versionados no repositório. O modelo de linguagem \texttt{gemini-3.8-flash} constitui o objeto experimental avaliado nas carteiras simuladas, e não ferramenta de redação.`

- **C1-05** · **Severidade:** Médio  
  **Local:** `chapters/01-introducao.tex:6` e `01-introducao.tex:8` vs `01:35` (p. 1 e 3 / PDF p. 13 e 15)  
  **Trecho:** L6: `se uma arquitetura multiagente baseada em LLMs produz decisões de investimento mais robustas do que abordagens tradicionais`; L8: `Como contribuição principal, propõe-se a avaliação comparativa entre metodologias clássicas de alocação e uma arquitetura de inteligência artificial...`; L35: `A contribuição deste trabalho é menos a antecipação de um resultado de desempenho superior e mais o estabelecimento de uma base técnica e metodológica...`  
  **Problema:** (1) Na L6, o adjetivo *"mais robustas"* é vago e nunca é definido como métrica (H2 avalia *desempenho ajustado ao risco superior, líquido de custos*); (2) a contribuição principal do trabalho é definida duas vezes com focos diferentes (na L8 e na L35), e a última frase da L8 tem 76 palavras.  
  **Correção proposta:**
  - Em `01:6`, substituir `"produz decisões de investimento mais robustas do que abordagens tradicionais"` por `"produz decisões de investimento com desempenho ajustado ao risco, líquido de custos, superior ao de abordagens tradicionais"`.
  - Em `01:8`, remover a frase `"Como contribuição principal, propõe-se..."` (mantendo o enunciado completo de contribuições apenas em `01:35`) e dividir a frase longa em duas:
    > `Com esse propósito, este trabalho tem como objetivo geral desenvolver o Hedge-fund-lab, um laboratório quantitativo para \textit{backtesting} e simulação de estratégias de investimento baseado em sistemas multiagentes. Para viabilizar a análise empírica, o laboratório integra um \textit{pipeline} de dados construído sobre os registros oficiais de negociação da B3 (COTAHIST), persistidos em banco relacional (SQLite/SQLAlchemy), a um sistema multiagente com papéis especializados em análise técnica, gestão de risco e gestão de portfólio. O sistema contempla tanto um grafo LangGraph para ativo único quanto uma carteira multiativos com capital compartilhado, executados sobre mecanismos próprios de simulação e contabilidade auditável para mensuração de desempenho frente aos \textit{benchmarks} tradicionais.`

- **C1-06** · **Severidade:** Médio  
  **Local:** `chapters/01-introducao.tex:10` (p. 1–2 / PDF p. 13–14)  
  **Trecho:** `A carteira Multiagentes foi executada em três versões sucessivas: a v1, pré-especificada, cujas regras foram fixadas antes de qualquer observação de seu desempenho no replay... a avaliação livre dessa contaminação é o acompanhamento diário prospectivo da carteira, iniciado em 14/10/2026, que constitui a continuação do estudo.`  
  **Problema:** (1) O parágrafo tem 190 palavras e junta a não execução do protocolo de ativo único com o desenho do Replay Contínuo e do acompanhamento prospectivo; (2) dizer *"antes de qualquer observação de seu desempenho no replay"* sem mencionar que houve dois ensaios curtos prévios sobre subjanelas de abril e abril–maio (`05:79`, após os quais as regras da v1 permaneceram inalteradas) cria uma aparente tensão com o Cap. 5; (3) convém já explicitar que o acompanhamento prospectivo iniciado em 14/10/2026 opera a arquitetura da v1.  
  **Correção proposta:** Dividir `01:10` em dois parágrafos e precisar:
  > `...a v1, pré-especificada, cujas regras foram fixadas antes da campanha contínua e mantidas inalteradas após dois ensaios preliminares em subjanelas curtas; e as v2 e v3, iterações exploratórias desenhadas após a auditoria das versões anteriores sobre os mesmos 153 pregões. Como o \textit{replay} foi produzido após o encerramento do período e o modelo pode conhecê-lo por seu treinamento, a avaliação livre dessa contaminação cabe ao acompanhamento diário prospectivo da carteira, iniciado em 14/10/2026 com a arquitetura da v1.`

- **C1-07** · **Severidade:** Médio  
  **Local:** `chapters/01-introducao.tex:18, 20, 33` (p. 2–3 / PDF p. 14–15)  
  **Trecho:** L18: `e as métricas de risco definidas no protocolo experimental;`; L20: `Estabelecer um desenho experimental pareado e causal...`; L33: `No replay, H1 é operacionalizada pelo contraste de Sharpe entre a SMA 50/200 e a Equal Weight 63d...`  
  **Problema:** (1) Em L18, apenas o Sharpe foi congelado como definição científica no protocolo (`05:131,144`); (2) em L20, *"desenho experimental pareado e causal"* sugere inferência causal entre fatores manipulados, quando o que é causal é o *relógio de informação* ($t-1 \to t$); (3) em L33, convém avisar desde já que a operacionalização de H1 pela SMA 50/200 cobre apenas uma regra de tendência, e não *momentum* transversal ou de série temporal (`05:217`).  
  **Correção proposta:**
  - L18: `...que incorporem custos de transação, proventos e as métricas de desempenho e risco empregadas na avaliação experimental;`
  - L20: `Estabelecer um desenho experimental pareado, com relógio causal de informação, métrica primária e regra de decisão estatística definidas...`
  - L33: acrescentar ao final do parágrafo: `Como nenhuma carteira de referência implementa \textit{momentum} transversal ou de série temporal, o teste de H1 no \textit{replay} restringe-se a uma regra de acompanhamento de tendência (Seção~\ref{sec:met-ameacas}).`

- **C1-08** · **Severidade:** Baixo  
  **Local:** `chapters/01-introducao.tex:37` (p. 3 / PDF p. 15)  
  **Trecho:** `o Capítulo~\ref{cha:fundamentacao} apresenta a fundamentação teórica, abordando as hipóteses de eficiência de mercado, os \textit{benchmarks} simples, as estratégias de análise técnica, a teoria moderna de portfólio, os sistemas multiagentes baseados em modelos de linguagem e as métricas de desempenho e risco.`  
  **Problema:** A descrição do Cap. 2 omite a seção de *backtesting* e riscos metodológicos (atual Seção 2.7) e precisará incluir a nova seção de inferência estatística proposta em `C2-03`.  
  **Correção proposta:** `...os sistemas multiagentes baseados em modelos de linguagem, os riscos metodológicos de \textit{backtesting}, as métricas de desempenho e risco e a inferência estatística na comparação de estratégias.`

*Balanço micro do Cap. 1:* **19 parágrafos/itens revisados** (10 parágrafos em prosa + 9 itens de lista); **10 apresentaram problemas**.

---

### Capítulo 2 — Fundamentação Teórica (`chapters/02-fundamentacao.tex`; p. 4–10 / PDF p. 16–22)

- **C2-01** · **Severidade:** Crítico  
  **Local:** `chapters/02-fundamentacao.tex:6, 20, 82, 88` (p. 4 e 7 / PDF p. 16 e 19)  
  **Trecho:** L6: `formalizada por \citep{Fama1970}` · L20: `Estudos de \citep{Shiller2000} e \citep{Thaler1993} demonstram` · L82: `O modelo de três fatores de \citep{FamaFrench1993}` · L88: `Posteriormente, \citep{FamaFrench2015} expandiram o modelo.`  
  **Problema:** Cinco ocorrências em que `\citep` (citação parentética entre colchetes) é usada como sujeito ou complemento preposicionado da frase, gerando construções agramaticais no PDF (`"formalizada por [Fama, 1970]"`, `"Estudos de [Shiller, 2000] e [Thaler, 1993] demonstram"`, `"Posteriormente, [Fama and French, 2015] expandiram"`). Além disso, *Advances in Behavioral Finance* (`Thaler1993`) é uma coletânea editada por Thaler.  
  **Correção proposta:**
  - Em `02:6`: `formalizada por \citet{Fama1970}`
  - Em `02:20`: `Estudos reunidos por \citet{Thaler1993} e a análise de \citet{Shiller2000} demonstram que vieses cognitivos...`
  - Em `02:82` e `02:88`: remover toda a Seção 2.4 conforme `C2-02` (ou, se mantida, usar `\citet{FamaFrench1993}` e `\citet{FamaFrench2015}`).

- **C2-02** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:80-89` (p. 7 / PDF p. 19 — Seção 2.4)  
  **Trecho:** `\section{FACTOR INVESTING E MODELOS DE PRECIFICAÇÃO DE ATIVOS}` ... `R_i - R_f = \beta_m (R_m - R_f) + \beta_s SMB + \beta_v HML`  
  **Problema:** Fio solto `FS-1`: seção de 7 linhas herdada do TCC 1 sobre *Factor Investing* e modelos Fama-French de 3 e 5 fatores. Nenhuma carteira, agente ou análise do TCC 2 utiliza fatores fundamentalistas ou regressões Fama-French, violando a recomendação expressa do guia oficial (`Trabalho de Conclusao EIC BCC.pdf`, p. 8 / PDF p. 21: *"Limite-se exclusivamente aos temas utilizados em seu trabalho"*). Além disso, a Eq. (2.6) omite o intercepto $\alpha_i$ e o termo de erro $\varepsilon_i$ e não define nenhuma das variáveis ($R_i, R_f, R_m, \beta_m, \beta_s, \beta_v, \mathit{SMB}, \mathit{HML}$).  
  **Correção proposta:** **Remover a Seção 2.4** (e retirar `FamaFrench1993` e `FamaFrench2015` de `references.bib` para que não fiquem órfãs; a referência `Gu2020` já é citada e discutida com propriedade em `03-relacionados.tex:16`).

- **C2-03** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:122-143` (p. 9–10 / PDF p. 21–22 — ausência de fundamentação da inferência estatística)  
  **Trecho:** (ausência de seção sobre inferência estatística para comparação de índices de Sharpe e testes múltiplos)  
  **Problema:** O trabalho decide suas hipóteses H1, H2 e H0 com o *bootstrap* estacionário de \citet{Politis1994}, analisa o poder estatístico pelo erro-padrão assintótico do Sharpe de \citet{Lo2002}, explica o resultado de H1 pela anomalia algébrica do Sharpe sob retornos médios negativos e controla a multiplicidade por teste de interseção–união e pelo procedimento sequencial de \citet{Holm1979}. Nenhum desses fundamentos teóricos é apresentado no Capítulo 2.  
  **Correção proposta:** Adicionar ao final do Capítulo 2 uma nova seção (1,5 página), pronta para colar:
  ```latex
  \section{INFERÊNCIA ESTATÍSTICA NA COMPARAÇÃO DE ESTRATÉGIAS}

  A comparação empírica entre estratégias financeiras sobre uma amostra finita de retornos diários requer distinguir diferenças genuínas de desempenho da variabilidade amostral. \citet{Lo2002} demonstra que, mesmo sob retornos independentes e identicamente distribuídos (i.i.d.) com índice de Sharpe diário $S_d$ moderado, o estimador amostral do Sharpe anualizado $\hat{S} = \sqrt{252}\,\hat{S}_d$ a partir de $n$ observações apresenta erro-padrão aproximado dado por:

  \begin{equation}
  \mathrm{EP}(\hat{S}) \approx \sqrt{\frac{252\,\left(1 + \frac{1}{2}\hat{S}_d^{\,2}\right)}{n}}.
  \end{equation}

  Em janelas curtas (como $n = 153$ pregões, para as quais $\mathrm{EP}(\hat{S}) \approx 1{,}28$), o erro-padrão é da mesma ordem de grandeza dos próprios índices observados, conferindo baixo poder estatístico a testes de diferença entre carteiras. Adicionalmente, quando o retorno excedente médio $\bar{r} - r_f$ é negativo, a divisão pelo desvio-padrão $\hat{\sigma}_r$ penaliza carteiras de menor volatilidade, atribuindo-lhes um índice de Sharpe mais negativo do que o de carteiras mais voláteis com perda acumulada semelhante.

  Como séries de retornos financeiros frequentemente exibem heterocedasticidade condicional e dependência serial fraca, métodos de reamostragem i.i.d.\ são inadequados. O \textit{bootstrap} estacionário proposto por \citet{Politis1994} preserva a dependência temporal ao reamostrar blocos de observações consecutivas cujo comprimento segue uma distribuição geométrica de média $L$ (probabilidade de reinício $p = 1/L$ a cada passo, com contorno circular da série), garantindo que a série reamostrada seja estacionária condicional aos dados. Quando duas estratégias $A$ e $B$ são avaliadas sobre o mesmo período, a aplicação da mesma sequência de índices reamostrados a ambas as séries (\textit{bootstrap} pareado) preserva a correlação contemporânea entre os retornos diários e reduz a variância do contraste $\hat{\Delta}_{A,B} = \hat{S}_A - \hat{S}_B$.

  Por fim, quando uma estratégia é contrastada simultaneamente contra $m$ referências, a probabilidade de ocorrer ao menos uma rejeição falsa da hipótese nula (erro de tipo~I familiar, \textit{family-wise error rate} --- FWER) cresce com $m$ \citep{White2000, Hansen2005}. Duas situações distintas devem ser separadas: se a hipótese substantiva exige que a estratégia supere \textit{todas} as $m$ referências simultaneamente, configura-se um teste de interseção--união, no qual cada contraste individual pode ser avaliado ao nível $\alpha$ sem inflação da FWER global; se, contudo, busca-se declarar superioridade sobre referências individuais específicas, é necessário controlar a FWER, por exemplo mediante o procedimento sequencialmente rejeitivo de \citet{Holm1979}, que ordena os valores-$p$ brutos $p_{(1)} \leq \cdots \leq p_{(m)}$ e compara cada $p_{(j)}$ ao limiar ajustado $\alpha / (m - j + 1)$, correspondente ao valor-$p$ ajustado $\tilde{p}_{(j)} = \max_{k \leq j} \min\{1,\ (m - k + 1)\,p_{(k)}\}$.
  ```

- **C2-04** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:24` (p. 4 / PDF p. 16)  
  **Trecho:** `Essa perspectiva fornece suporte teórico para o uso de sistemas baseados em inteligência artificial e modelos de linguagem, uma vez que modelos adaptativos e multiagentes podem capturar padrões dinâmicos e interpretar contextos que estratégias estáticas ou puramente matemáticas não conseguem identificar.`  
  **Problema:** Parágrafo de uma única frase, sem citação, que afirma como fato estabelecido que modelos multiagentes e LLMs *"podem capturar padrões dinâmicos... que estratégias estáticas ou puramente matemáticas não conseguem identificar"*. Além de ser um salto lógico a partir da AMH de \citet{Lo2004}, a afirmação é desmentida pelo próprio resultado empírico do trabalho (no qual a regra matemática estática Bollinger 20/2 superou todas as versões dos agentes).  
  **Correção proposta:** Fundir `02:22` e `02:24` em um único parágrafo de três frases:
  > `Buscando reconciliar a racionalidade da EMH com as evidências comportamentais, \citet{Lo2004} propôs a Hipótese de Mercados Adaptativos (\textit{Adaptive Markets Hypothesis} --- AMH). Nesse arcabouço, a eficiência de mercado não é um estado estático, mas um processo dinâmico que evolui conforme participantes e instituições se adaptam a mudanças de regime econômico. Essa perspectiva motiva investigar empiricamente se arquiteturas flexíveis, como sistemas multiagentes baseados em modelos de linguagem, conseguem combinar sinais técnicos sob regras explícitas de risco de forma competitiva frente a estratégias quantitativas estáticas --- questão que constitui uma hipótese empírica aberta, e não uma garantia teórica a priori.`

- **C2-05** · **Severidade:** Alto  
  **Local:** `chapters/02-fundamentacao.tex:106-121` vs `chapters/03-relacionados.tex:25-39` (p. 8–9 vs p. 13–14 / PDF p. 20–21 vs p. 25–26)  
  **Trecho:** L120: `\citet[p. 1]{FinCoT2025} evidenciam que, ao fundamentar o processo gerativo em passos lógicos guiados por domínio (prática cunhada como FinCoT), a acurácia de alinhamento financeiro de modelos gerais de ponta se eleva drasticamente, com melhorias reportadas de 63,2\% para 80,5\%.`  
  **Problema:** (1) Cada uma das subseções `2.6.1`, `2.6.2` e `2.6.3` resume um único artigo (`Li2023`, `Xing2024` e `FinCoT2025`), sem diálogo entre autores e repetindo o conteúdo que reaparece nas Seções 3.3 e 3.4 (incluindo o mesmo percentual `"de 63,2% para 80,5%"`, que em `02:120` usa o advérbio não acadêmico `"drasticamente"` e generaliza para `"modelos gerais de ponta"`, enquanto `03:26` reporta sobriamente `"um modelo geral"`); (2) `02:112` fala em *"A literatura sobre sistemas multiagentes"* citando apenas um preprint de *trading* (`Li2023`); (3) `02:116` escreve `\citep[p. 5, p. 9]{Xing2024}` (com `p.` duplicado) e `02:120` grafa `pré-definidos` com hífen (pelo Acordo Ortográfico, **predefinidos**).  
  **Correção proposta:** Enxugar a Seção 2.6 para focar nos **conceitos teóricos** (decomposição em papéis/personas, agregação por autoconsistência vs debate heterogêneo e estruturação do raciocínio encadeado com restrições de domínio), deixando os resultados numéricos específicos de `Li2023`, `Xing2024` e `FinCoT2025` exclusivamente no Capítulo 3. Em `02:120`, substituir por:
  > `Além da especialização por papéis, a qualidade das decisões produzidas por modelos de linguagem depende do grau de estrutura imposto ao processo gerativo. Enquanto instruções abertas de raciocínio passo a passo (\textit{Zero-shot Chain-of-Thought}) permitem justificativas livres sujeitas a desvios de escopo, o encadeamento guiado por critérios e restrições predefinidos do domínio financeiro --- como proposto em \citet{FinCoT2025} e associado a mecanismos de votação por autoconsistência \citep{Wang2023} --- restringe o espaço de inferência aos indicadores fornecidos. Para o presente trabalho, essa distinção fundamenta tanto a exigência de respostas estruturadas vinculadas a códigos fechados de evidência quanto a evolução de instruções homogêneas para lentes analíticas com faixas explícitas de atuação.`

- **C2-06** · **Severidade:** Médio  
  **Local:** `chapters/02-fundamentacao.tex:44-79, 94-96, 133-137` (p. 6–10 / PDF p. 18–22)  
  **Trecho:** Eqs. (2.1) a (2.8): `MA_t = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}`, `Momentum_t = \frac{P_t}{P_{t-n}} - 1`, `BB_{upper} = MA + k\sigma`, `\sigma_p^2 = w^T \Sigma w`, `R_{acum} = \prod_{t=1}^{T}(1+R_t)-1`, `S = \frac{E[R_p - R_f]}{\sigma_p}` e menções sem fórmula ao RSI e ao MACD (L68–78).  
  **Problema:** (1) O **RSI** e o **MACD** são utilizados diretamente nas *features* dos agentes e nas tabelas de resultados do Cap. 6, mas o Cap. 2 **não apresenta suas fórmulas nem seus períodos canônicos** (14 pregões para o RSI de Wilder; 12, 26 e 9 pregões para o MACD); (2) nas Eqs. (2.1), (2.2), (2.4), (2.5), (2.7) e (2.8), variáveis como $P_t$, $n$, $k$, $w$, $\Sigma$, $R_p$, $R_f$, $\sigma_p$, $R_t$ e $T$ não são definidas após as equações; (3) palavras de múltiplas letras em modo matemático sem `\mathrm{}` (`MA_t`, `Momentum_t`, `BB_{upper}`, `BB_{lower}`, `R_{acum}`) são tipografadas pelo LaTeX como produto de variáveis isoladas ($M \cdot A \cdot t$); (4) na Subseção 2.5.1 (L100–102), falta explicitar o problema de otimização da carteira de mínima variância com restrição *long-only* ($\min_w w^\top \Sigma w$ sujeito a $\mathbf{1}^\top w = 1$ e $w \geq 0$) utilizada no replay.  
  **Correção proposta:**
  - Padronizar `\mathrm{SMA}_{n,t}`, `\mathrm{Mom}_{n,t}`, `\mathrm{BB}_{\mathrm{sup},t} = \mathrm{SMA}_{n,t} + k\sigma_{n,t}`, `\mathrm{BB}_{\mathrm{inf},t} = \mathrm{SMA}_{n,t} - k\sigma_{n,t}` e `R_{\mathrm{acum}}`, definindo todas as variáveis após cada equação (`\noindent em que $P_t$ é o preço de fechamento na sessão $t$ e $n$ é o comprimento da janela móvel...`).
  - Acrescentar em `02:68-78` as equações do RSI de \citet{Wilder1978} (com período padrão $n = 14$):
    ```latex
    \begin{equation}
    \mathrm{RSI}_t = 100 - \frac{100}{1 + \mathrm{RS}_t}, \qquad \mathrm{RS}_t = \frac{\bar{G}_t}{\bar{L}_t},
    \end{equation}
    \noindent em que $\bar{G}_t$ e $\bar{L}_t$ representam, respectivamente, as médias suavizadas de Wilder dos ganhos e das perdas diárias em uma janela de $n = 14$ pregões. O indicador MACD, por sua vez, é obtido pela diferença entre duas médias móveis exponenciais ($\mathrm{MACD}_t = \mathrm{EMA}_{12,t} - \mathrm{EMA}_{26,t}$) comparada à sua linha de sinal $\mathrm{EMA}_{9,t}(\mathrm{MACD})$.
    ```

- **C2-07** · **Severidade:** Médio  
  **Local:** `chapters/02-fundamentacao.tex:28, 31, 101, 126` (p. 5, 7–9 / PDF p. 17, 19–21)  
  **Trecho:** L28: `menos dependentes de estimações sofisticadas... \citep{Markowitz1952, Clarke2006, LopezDePrado2018}`; L31: `\textit{Buy and Hold}... \citep{LopezDePrado2018, Bailey2017}`; L101: `No contexto do mercado acionário brasileiro, pode funcionar como um \textit{benchmark} conservador \citep{Clarke2006}`; L126: `a probabilidade de encontrar estratégias aparentemente lucrativas (\textit{Probability of Backtest Overfitting}) aumenta significativamente \citep{Bailey2017}`.  
  **Problema:** Quatro desalinhamentos entre afirmação e referência citada: (1) em L28, quem mostra a força de *benchmarks* simples sem estimação de parâmetros ($1/N$) é \citet{DeMiguel2009}, enquanto \citet{Markowitz1952} e \citet{Clarke2006} tratam justamente de carteiras que exigem estimar a matriz de covariância; (2) em L31, \citet{Bailey2017} trata de PBO, não de *Buy and Hold*; (3) em L101, a frase atribui `Clarke2006` ao *"contexto do mercado acionário brasileiro"*, quando o artigo analisa ações dos EUA (*"Minimum-Variance Portfolios in the U.S. Equity Market"*); (4) em L126, a PBO de \citet{Bailey2017} é definida de forma imprecisa.  
  **Correção proposta:**
  - L28: substituir `\citep{Markowitz1952, Clarke2006, LopezDePrado2018}` por `\citep{DeMiguel2009, LopezDePrado2018}`.
  - L31: manter apenas `\citep{LopezDePrado2018}`.
  - L101: `Em mercados acionários como o norte-americano, carteiras de mínima variância documentaram redução expressiva de volatilidade sem perda proporcional de retorno \citep{Clarke2006}, razão pela qual essa formulação é adotada neste trabalho como referência conservadora de alocação por risco no mercado brasileiro.`
  - L126: `Adicionalmente, \citet{Bailey2017} definem a probabilidade de sobreajuste de \textit{backtest} (\textit{Probability of Backtest Overfitting} --- PBO) como a probabilidade de que a estratégia selecionada como ótima dentro da amostra apresente desempenho inferior à mediana fora da amostra, demonstrando que essa probabilidade cresce rapidamente com o número de configurações testadas.`

- **C2-08** · **Severidade:** Médio  
  **Local:** `chapters/02-fundamentacao.tex:4-25, 103-105, 130, 140` (p. 4, 8, 9, 10 / PDF p. 16, 20, 21, 22)  
  **Trecho:** Seção `2.1` com apenas uma subseção (`2.1.1`); Subseção `2.5.2 Relação Risco-Retorno` com uma única frase; `02:130` com uma única frase; `02:140` com `MAR` sem expansão e referência a `"crises do mercado brasileiro"`.  
  **Problema:** (1) Pela ABNT NBR 6024, uma seção não deve ter subseção única (`2.1.1` sem `2.1.2`); (2) o guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, Seção 1.1, p. 1 / PDF p. 14) orienta que cada parágrafo tenha no mínimo três frases, mas o Cap. 2 possui **5 parágrafos de uma única frase** (`02:24, 98, 104, 130` e a abertura de `02:8`) e **6 de duas frases** (`02:22, 48, 56, 66, 88, 124`); (3) em `02:140`, a sigla `MAR` não é expandida e afirma-se que Sortino e MDD são cruciais *"frente a crises do mercado brasileiro"* (conceito que não é objeto de recorte no experimento).  
  **Correção proposta:** (1) Na Seção 2.1, ou remover o título `2.1.1` integrando o texto na Seção 2.1, ou dividir em `2.1.1 Formulação Clássica e Formas de Eficiência` e `2.1.2 Críticas Comportamentais e a Hipótese de Mercados Adaptativos`; (2) eliminar a Subseção `2.5.2`, incorporando sua frase ao parágrafo introdutório da Seção `2.8` (`02:130`); (3) em `02:140`, expandir `retorno mínimo aceitável (\textit{Minimum Acceptable Return} --- MAR)` e substituir `"frente a crises do mercado brasileiro"` por `"em períodos de retração acentuada dos preços, complementando o índice de Sharpe ao distinguir a volatilidade de perdas da volatilidade total"`.

- **C2-09** · **Severidade:** Baixo  
  **Local:** `chapters/02-fundamentacao.tex:12, 60, 66, 124, 143` (p. 4, 6, 9, 10)  
  **Trecho:** `Forma semi-forte` (L12); `z-score` (L60); `onde $\mu$ representa a média móvel e $\sigma$ o desvio padrão` (L66); `risco de \textit{overfitting}, onde resultados positivos` (L124); `(corretagem, spread e emolumentos)` (L143)  
  **Problema:** Ortografia, regência e formatação: `semi-forte` grafa-se **semiforte**; `onde` só deve ser usado para lugar físico (usar **em que** / **no qual**); `desvio padrão` sem hífen em L66 diverge de `desvio-padrão` em L133; `z-score` e `spread` estão sem itálico.  
  **Correção proposta:** Corrigir para `Forma semiforte` (L12), `\textit{z-score}` (L60), `\noindent em que $\mu$ representa a média móvel e $\sigma$, o desvio-padrão` (L66), `risco de \textit{overfitting}, no qual resultados positivos` (L124) e `(corretagem, \textit{spread} e emolumentos)` (L143).

*Balanço micro do Cap. 2:* **37 parágrafos/itens revisados** (34 parágrafos em prosa + 3 itens de lista); **23 apresentaram problemas**.

---

### Capítulo 3 — Trabalhos Relacionados (`chapters/03-relacionados.tex`; p. 11–18 / PDF p. 23–30)

- **C3-01** · **Severidade:** Crítico  
  **Local:** `chapters/03-relacionados.tex:62-90` (p. 17 / PDF p. 29 — Tabela 3.1)  
  **Trecho:** `\begin{tabular}{>{\raggedright\arraybackslash}p{1.9cm} >{\raggedright\arraybackslash}p{2.2cm} >{\raggedright\arraybackslash}p{1.8cm} >{\raggedright\arraybackslash}p{1.6cm} >{\raggedright\arraybackslash}p{2.4cm} >{\raggedright\arraybackslash}p{2.0cm} >{\raggedright\arraybackslash}p{2.4cm}}`  
  **Problema:** No PDF (p. 17 / PDF p. 29), os cabeçalhos das colunas 3 (`Multiagente`, largura `1.8cm`) e 6 (`Rastreabilidade das decisões`, largura `2.0cm`) não são hifenizados pelo TeX (que não hifeniza a primeira palavra de um `\parbox` sem `\hspace{0pt}`) e **colidem fisicamente com os cabeçalhos vizinhos**, imprimindo **`MultiagenteCustos`** (`Overfull \hbox 9.36pt`) e **`RastreabilidadeReferências`** (`Overfull \hbox 21.51pt`)! Além disso, a Tabela 3.1 flutua para a página 17, cortando ao meio o primeiro parágrafo da Seção 3.8 (`Síntese e Posicionamento`).  
  **Correção proposta:** Inserir `\hspace{0pt}` na definição das colunas ou hifenizar explicitamente os cabeçalhos e reequilibrar as larguras para que caibam em `\textwidth` (`16,0 cm`), mantendo a tabela dentro da Seção 3.7:
  ```latex
  \setlength{\tabcolsep}{3pt}
  \begin{tabular}{>{\raggedright\arraybackslash\hspace{0pt}}p{1.9cm}
                  >{\raggedright\arraybackslash\hspace{0pt}}p{2.1cm}
                  >{\raggedright\arraybackslash\hspace{0pt}}p{2.0cm}
                  >{\raggedright\arraybackslash\hspace{0pt}}p{1.7cm}
                  >{\raggedright\arraybackslash\hspace{0pt}}p{2.4cm}
                  >{\raggedright\arraybackslash\hspace{0pt}}p{2.2cm}
                  >{\raggedright\arraybackslash\hspace{0pt}}p{2.3cm}}
  \toprule
  \textbf{Trabalho} & \textbf{Mercado e dados} & \textbf{Multi\-agente} & \textbf{Custos explícitos} & \textbf{Controle de contaminação do modelo} & \textbf{Rastreabi\-lidade das decisões} & \textbf{Referências clássicas} \\
  ```

- **C3-02** · **Severidade:** Alto  
  **Local:** `chapters/03-relacionados.tex:4` (p. 11 / PDF p. 23)  
  **Trecho:** `Este capítulo revisa a literatura que dialoga diretamente com o Hedge-fund-lab, organizada em seis frentes...`  
  **Problema:** O guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, Cap. 4, p. 9 / PDF p. 22) pede explicitamente nos Trabalhos Relacionados a *"apresentação de uma estrutura de busca sistemática, contendo minimamente uma (ou mais, se necessário) String(s) de busca usada(s) para encontrar os trabalhos relacionados, a(s) base(s) de dados de periódicos em que foi(foram) feita(s) a(s) busca(s), os critérios de inclusão e exclusão de resultados e, por fim, os parâmetros para priorização de relevância dos trabalhos eleitos"*. O Capítulo 3 apresenta excelente revisão crítica e tabela comparativa, mas não documenta como a seleção bibliográfica foi conduzida.  
  **Correção proposta:** Inserir um parágrafo metodológico logo após `03-relacionados.tex:4` descrevendo de forma fidedigna o procedimento adotado pelos autores (bases consultadas — como Scopus, IEEE Xplore, ACM Digital Library, SSRN e arXiv —, termos de consulta combinando `"large language model"` / `"multi-agent"` e `"trading"` / `"portfolio"` / `"look-ahead bias"`, recorte temporal e critérios de inclusão focados em sistemas de decisão financeira em circuito fechado e auditorias metodológicas).

- **C3-03** · **Severidade:** Alto  
  **Local:** `chapters/03-relacionados.tex:50` vs `03-relacionados.tex:100` (p. 15 vs p. 18 / PDF p. 27 vs p. 30)  
  **Trecho:** L50: `Por isso, o projeto reserva a avaliação confirmatória de agentes ao acompanhamento prospectivo e trata o replay retrospectivo como estudo exploratório.` vs L100: `apenas a versão pré-especificada (v1) recebe decisão inferencial sobre as hipóteses, e a avaliação plenamente confirmatória dos agentes, livre de contaminação, permanece reservada ao acompanhamento prospectivo.`  
  **Problema:** Conforme apontado na Seção 3.5, a L50 rotula o replay inteiro como `"estudo exploratório"`, enquanto a L100 (e a Tabela 5.1) distingue a v1 como execução pré-especificada que recebe decisão inferencial sobre H2.  
  **Correção proposta:** Harmonizar o final de `03-relacionados.tex:50` com a L100:
  > `Por isso, o projeto trata o \textit{replay} como avaliação retrospectiva: apenas a versão pré-especificada (v1) recebe decisão inferencial sobre as hipóteses (condicionada à impossibilidade de descartar contaminação do modelo), as versões subsequentes (v2 e v3) são tratadas como iterações exploratórias dentro da amostra, e a avaliação plenamente confirmatória, livre de contaminação, permanece reservada ao acompanhamento prospectivo.`

- **C3-04** · **Severidade:** Alto  
  **Local:** `chapters/03-relacionados.tex:50` (e `05-metodologia.tex:26, 194, 205`, `07-conclusao.tex:47`)  
  **Trecho:** `O corte de conhecimento declarado pelo provedor é anterior ao período do replay, porém essa declaração não é verificável de forma independente` (e `março de 2026` no Cap. 5)  
  **Problema:** A data do corte de conhecimento declarado do modelo `gemini-3.8-flash` (`março de 2026`) é a justificativa para o início do período do replay (`06/04/2026`, `05:26`), mas não há citação ou nota de rodapé indicando onde o provedor declara essa data (nem a fonte das tarifas de US\$ 0,75 / US\$ 3,75 por milhão de *tokens* em `04:252`).  
  **Correção proposta:** Incluir referência bibliográfica ou nota de rodapé com a documentação oficial da API Google Gemini (URL e data de acesso em novembro de 2026) tanto para o corte de conhecimento quanto para a tabela de preços de inferência.

- **C3-05** · **Severidade:** Médio  
  **Local:** `chapters/03-relacionados.tex:84, 92` (p. 16–17 / PDF p. 28–29)  
  **Trecho:** L84 (Tabela 3.1): `Sim (0,03\% e custo de inferência)` e `pesos iguais, mínima variância`; L92: `O controle da contaminação temporal permanece, na melhor das hipóteses, parcial em todos os trabalhos com LLMs, inclusive no presente. As diferenças do Hedge-fund-lab estão no mercado avaliado, na contabilização conjunta dos custos de operação e de inferência...`  
  **Problema:** (1) *"Contabilização conjunta"* dá a entender que o custo de inferência é descontado junto com os custos de operação do patrimônio da carteira, quando `05:32` explicita que o custo de inferência (em US\$) é controlado em orçamento separado e **não é deduzido do patrimônio**; (2) dizer que o controle de contaminação é *"parcial em todos os trabalhos com LLMs"* contradiz `03:24` (\citet{LopezLira2023} avaliam manchetes posteriores ao corte de conhecimento do GPT-4); (3) na Tabela 3.1, usar os nomes oficiais `Equal Weight 63d` e `Mínima Variância 252/63`.  
  **Correção proposta:**
  - Na Tabela 3.1 (`03:84`): `Sim (0,03\% no patrimônio; inferência em orçamento próprio)` e `Sim (Buy \& Hold, SMA 50/200, Bollinger 20/2, Equal Weight 63d, Mínima Variância 252/63)`.
  - Em `03:92`: `Entre os sistemas de negociação comparados na Tabela~\ref{tab:relacionados}, o controle da contaminação temporal permanece, na melhor das hipóteses, parcial, inclusive no presente trabalho. As diferenças do Hedge-fund-lab estão no mercado avaliado, na contabilização explícita dos custos de transação (no patrimônio) e de inferência (em orçamento dedicado), no registro auditável de cada intervenção sobre a proposta do modelo e nas carteiras de referência determinísticas reproduzidas com paridade exata entre campanhas.`

- **C3-06** · **Severidade:** Médio  
  **Local:** `chapters/03-relacionados.tex:39` e `03:50` (p. 14–15 / PDF p. 26–27)  
  **Trecho:** L39: `O Hedge-fund-lab adota a especialização de papéis em escala deliberadamente reduzida (cinco analistas técnicos, um analista de risco e um gestor)` · L50: `No Hedge-fund-lab, o relógio causal garante que cada decisão use apenas dados até o fechamento do pregão anterior`  
  **Problema:** (1) Na L39, a redação sugere 7 agentes no total, mas na carteira multiativos são 5 analistas técnicos e até 1 analista de risco **por ativo** (para 5 ativos) mais 1 gestor global da carteira (até 31 chamadas por pregão); (2) na L50, usa-se o termo `"relógio causal"` antes de sua definição na Seção 4.8.  
  **Correção proposta:** Em `03:39`: `(cinco analistas técnicos e um analista de risco por ativo, coordenados por um gestor global da carteira)`; em `03:50`: `o relógio causal (Seção~\ref{sec:arq-relogio}) garante que...`.

- **C3-07** · **Severidade:** Baixo  
  **Local:** `chapters/03-relacionados.tex:10, 16, 18, 26, 33, 35, 48, 54, 58` (p. 11–16)  
  **Trecho:** `DQN`, `TDQN`, `PPO` (L10); `sinais dominantes de momento` (L16); `LSTM` (L18); `CFA` (L26); `KDJ&RSI` (L33); `CVaR` (L35); `ARIMA` (L48); `GSM8K` (L54); `\section{QUADRO COMPARATIVO}` (L58).  
  **Problema:** Siglas não expandidas na primeira ocorrência; tradução de *momentum* como `"momento"` na L16 (colidindo com "momento no tempo"); e seção intitulada `QUADRO COMPARATIVO` para um elemento numerado como `Tabela 3.1`.  
  **Correção proposta:** Expandir as siglas no primeiro uso (ver `P-03`), substituir `momento` por `\textit{momentum}` na L16 e renomear a Seção 3.7 (`03:58`) para `\section{COMPARAÇÃO COM O HEDGE-FUND-LAB}`.

*Balanço micro do Cap. 3:* **25 parágrafos revisados** (mais a Tabela 3.1); **11 apresentaram problemas**.


---

### Capítulo 4 — Arquitetura do Sistema (`chapters/04-arquitetura.tex`; p. 19–35 / PDF p. 31–47)

- **C4-01** · **Severidade:** Crítico  
  **Local:** `chapters/04-arquitetura.tex:72` (p. 20 / PDF p. 32 — e repetido em `chapters/05-metodologia.tex:188`, p. 45 / PDF p. 57)  
  **Trecho:** `No protocolo de ativo único, o artefato estático de PETR4 contém 2.649 barras diárias (de 2018-01-12 a 2024-02-28, com 1.519 sessões reservadas como conjunto de endurecimento $H_{\text{real}}$), com integridade verificada por soma SHA-256.`  
  **Problema:** Erro factual triplo que mistura três objetos distintos do protocolo `tcc2/evidence/03-metodo-h2/H2_METHODOLOGICAL_FREEZE_V1.md` (Seção 7, p. 176–215, e Amendment 1, p. 521–593):
  1. `2.649 barras diárias` é o *snapshot* completo de `PETR4.SA` de **04/01/2016 a 31/08/2026** (não de 2018 a 2024);
  2. `1.519 sessões` (de **12/01/2018 a 28/02/2024**) é o conjunto $|E|$ de **sessões elegíveis como âncora** dentro do período *Pre-Cutoff* (que exigem $\geq 504$ pregões anteriores de aquecimento);
  3. O conjunto de endurecimento $H_{\text{real}}$ contém apenas **4 sessões reais** (selecionadas nos quantis determinísticos $q \in \{0{,}2;\; 0{,}4;\; 0{,}6;\; 0{,}8\}$ de $|E|$, compondo $H = 8\;H_{\text{syn}} + 4\;H_{\text{real}}$), e não 1.519 sessões. Além disso, as datas estão em formato ISO (`2018-01-12 a 2024-02-28`).  
  **Correção proposta:**
  > `No protocolo de ativo único, o artefato estático de PETR4 contém 2.649 barras diárias (de 04/01/2016 a 31/08/2026), com integridade verificada por soma SHA-256; dentro do recorte anterior ao corte de conhecimento do modelo, 1.519 sessões (de 12/01/2018 a 28/02/2024) compõem o conjunto elegível de âncoras após o aquecimento de 504 pregões, do qual quatro sessões determinísticas foram reservadas para o conjunto de endurecimento $H_{\text{real}}$ (ao lado de oito cenários sintéticos $H_{\text{syn}}$).`

- **C4-02** · **Severidade:** Crítico  
  **Local:** `chapters/04-arquitetura.tex:6` (p. 19 / PDF p. 31)  
  **Trecho:** `(ii) o sistema multiagentes de ativo único, orquestrado por um grafo de estados em LangGraph e utilizado na avaliação H1/H2 sobre PETR4;`  
  **Problema:** Duas inconsistências graves com os Capítulos 1 e 5: (1) a Hipótese **H1** compara estratégias de *momentum/trend-following* contra carteira de pesos iguais (`1/N`), o que pressupõe múltiplos ativos e jamais foi avaliado no protocolo de ativo único sobre PETR4; (2) como a própria Seção 5.7 (`05-metodologia.tex:194`) explica, o protocolo de ativo único sobre PETR4 **não executou o Teste Final de H2** (foi encerrado após o *Smoke Test* e o *Diagnostic Hardening*, sendo substituído pelo replay multiativos).  
  **Correção proposta:**
  > `(ii) o sistema multiagentes de ativo único, orquestrado por um grafo de estados em LangGraph e utilizado na fase preliminar de validação e endurecimento diagnóstico do protocolo H2 sobre PETR4;`

- **C4-03** · **Severidade:** Crítico  
  **Local:** `chapters/04-arquitetura.tex:74, 113, 262` (p. 20, 23, 30 / PDF p. 32, 35, 42)  
  **Trecho:** L74: `\texttt{src/backtesting/b3\_calendar.py}` (`Overfull \hbox 33.49pt`, impresso como `b3_-calendar.py` na margem); L113: `\texttt{src/agents/graph.py}` (`Overfull \hbox 11.42pt`); L262: `\texttt{/laboratory/replay/v2/}` (`Overfull \hbox 6.50pt`); além de dezenas de identificadores `\texttt` impressos com hífen espúrio após sublinhado (`provider_-journal.jsonl`, `wallet_-manager_-api.py`).  
  **Problema:** O pacote `hyphenat` com opção `[htt]` insere um hífen visível após `_` ao quebrar linha e não consegue quebrar barras `/` sem estourar a margem direita (ver `P-01`).  
  **Correção proposta:** Remover `\usepackage[htt]{hyphenat}` de `main.tex`, usar `\path{...}` para caminhos e identificadores longos e enxugar a listagem de arquivos de código no corpo do capítulo (ver `C4-07`).

- **C4-04** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:150` e `04:336-339` (p. 24, 32–33 / PDF p. 36, 44–45)  
  **Trecho:** L150: `\texttt{rsi}, \texttt{sma50\_gap}, \texttt{sma200\_gap}, \texttt{bb\_upper\_gap}, \texttt{bb\_lower\_gap}, \texttt{bb\_width}, \texttt{macd\_ratio} e \texttt{macd\_signal\_ratio}` · L338: `\texttt{bb\_lower\_gap} entre $-0{,}01$ e $+0{,}06$... \texttt{bb\_upper\_gap} $> -0{,}04$`.  
  **Problema:** As oito *features* adimensionais constituem a **única entrada quantitativa** que o comitê de analistas técnicos recebe em todo o experimento e são a base dos limiares numéricos da v3, mas **nenhuma delas tem sua fórmula matemática ou convenção de sinal definida na monografia**. Sem saber se `bb_upper_gap` é $(P - \mathrm{BB}_{\mathrm{sup}})/\mathrm{BB}_{\mathrm{sup}}$ ou $(\mathrm{BB}_{\mathrm{sup}} - P)/P$, o leitor não consegue interpretar o que significa `\texttt{bb\_upper\_gap} > -0,04` na Seção 4.10.  
  **Correção proposta:** Explicitar na Seção 4.6.2 (ou na Seção 2.3) as definições exatas verificadas em `src/agents/features.py:131-182` (todas quantizadas a seis casas decimais):
  $$\text{gap}(P_t, L_t) = \frac{P_t}{L_t} - 1, \quad L_t \in \{\mathrm{SMA}_{50,t},\; \mathrm{SMA}_{200,t},\; \mathrm{BB}_{\mathrm{sup},t},\; \mathrm{BB}_{\mathrm{inf},t}\}$$
  $$\texttt{bb\_width}_t = \frac{\mathrm{BB}_{\mathrm{sup},t} - \mathrm{BB}_{\mathrm{inf},t}}{\mathrm{SMA}_{20,t}}, \qquad \texttt{macd\_ratio}_t = \frac{\mathrm{MACD}_t}{P_t}, \qquad \texttt{macd\_signal\_ratio}_t = \frac{\mathrm{MACD}_{\mathrm{sinal},t}}{P_t}$$
  Deixar claro que, sob essa convenção, $\texttt{bb\_lower\_gap}_t \geq 0$ indica preço acima da banda inferior (e valores próximos de zero indicam proximidade do piso da banda), enquanto $\texttt{bb\_upper\_gap}_t > -0{,}04$ indica preço a menos de 4% abaixo (ou já acima) da banda superior.

- **C4-05** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:77` e `04:152, 156` (p. 20, 24–25 / PDF p. 32, 36–37)  
  **Trecho:** L77: `Já a série ajustada (\texttt{Adj Close}) incorpora retrospectivamente eventos corporativos... Para o cálculo dos indicadores técnicos entregues aos agentes, o sistema reconstrói uma série causal ajustada na janela de 260 pregões até $t-1$` · L152: `Cada chamada recebe um contexto estritamente limitado às oito features técnicas pré-calculadas...`  
  **Problema:** O texto omite **duas defesas metodológicas importantes** que já estão implementadas no código e documentadas nos artefatos de evidência:
  1. Em L77, o leitor pode perguntar se usar fatores de ajuste do Yahoo Finance na janela até $t-1$ introduz vazamento temporal caso ocorra um provento em $t+k$. Conforme demonstrado em `src/agents/features.py:5-13` e `H2_METHODOLOGICAL_FREEZE_V1.md:570-579`, qualquer evento corporativo posterior a $t-1$ multiplica todos os preços ajustados da janela $\{t-260, \dots, t-1\}$ pela **mesma constante escalar** $c > 0$. Como todas as oito *features* técnicas e a volatilidade de 21 dias são **razões invariantes por escala** ($f(c \cdot P) = f(P)$), o fator $c$ se cancela exatamente!
  2. Em L152 e L156, o texto não destaca que as chamadas dos **cinco analistas técnicos e do analista de risco não recebem o código do ativo (*ticker*), a data da sessão nem o nível nominal de preço** (`src/agents/features.py:23-26`) — apenas o vetor adimensional de oito *features* (e, para o risco, a volatilidade de 21 dias). Isso bloqueia por construção a memorização direta de ativo/data no comitê por ativo, restringindo qualquer risco de contaminação do pré-treinamento exclusivamente à etapa final do gestor global (`portfolio_manager`).  
  **Correção proposta:** Incorporar ambos os argumentos na Seção 4.2 (L77) e na Seção 4.6.2 (L152): eles fortalecem substancialmente a defesa técnica do trabalho perante a banca.

- **C4-06** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:349-355` (p. 33–34 / PDF p. 45–46 — e `05:200`, `06:204`, `07:13`)  
  **Trecho:** `O ciclo diário autônomo (\texttt{dashboard/daily\_cycle.py}) opera sobre uma carteira de R\$ 100.000,00 com os mesmos cinco ativos da B3... O ciclo executa cinco etapas sequenciais: (1) atualização de dados de mercado; (2) preparação de estado com verificação de proventos e alertas de tese velha; (3) decisão da carteira principal via comitê e gestor com orçamento diário de 40 chamadas...`  
  **Problema:** Nem a Seção 4.11, nem a Seção 5.7.1, nem a Seção 6.8 informam **qual versão da arquitetura multiagentes (v1, v2 ou v3)** roda no ciclo diário prospectivo. A inspeção de `dashboard/daily_cycle.py:44` mostra que o ciclo diário importa `wallet_manager_api` (que utiliza o compilador determinístico estrito da **v1**, e não os módulos `wallet_manager_v2` ou `wallet_manager_v3`). Omitir esse fato impede a banca de entender por que a carteira prospectiva exibiu exatamente o padrão de paralisia da v1 nos 23 pregões reais (Seção 6.8).  
  **Correção proposta:** Explicitar na Seção 4.11 (`04:351`), na Seção 5.7.1 (`05:200`) e na Seção 6.8 (`06:204`) que o ciclo diário prospectivo executou a arquitetura pré-especificada **v1** (`wallet_manager_api.py`), e que durante o acompanhamento foram adicionadas duas referências adicionais de regras técnicas (**SMA 50/200** e **Bollinger 20/2**, totalizando seis carteiras no painel diário conforme `equity_diario.csv`).

- **C4-07** · **Severidade:** Alto  
  **Local:** `chapters/04-arquitetura.tex:4, 83-101, 240-264, 307-334, 357-368` (p. 19–35 / PDF p. 31–47)  
  **Trecho:** L4: `Este capítulo descreve a arquitetura de software e as decisões de engenharia implementadas no Hedge-fund-lab, tal como observadas no repositório do projeto... A descrição baseia-se exclusivamente na auditoria do código-fonte e na verificação estática dos módulos existentes, sem reexecução de pipelines.`  
  **Problema:** (1) Como apontado em `P-09`, o parágrafo de abertura adota voz de auditor externo em vez de voz autoral; (2) como detalhado na Seção 3.3, o Capítulo 4 tem 17 páginas (~6.300 palavras) porque mistura arquitetura conceitual com inventário de arquivos, rotas HTTP, reservas contábeis de 6 casas decimais (`04:252`), códigos de erro de infraestrutura (`04:257-264`) e a Tabela 4.3 de variáveis de ambiente (`04:307-334`); (3) na Seção 4.3 (`04:100`), o texto admite que a execução das carteiras usa a contabilidade do *ledger* de eventos e não `src/backtesting/engine.py`, mas não explica como a correção contábil do *ledger* utilizado no experimento é verificada (via auditorias de paridade entre campanhas e asserções de invariantes em `metricas_replay.py`).  
  **Correção proposta:**
  - Reescrever `04:4` em voz autoral: `Este capítulo apresenta a arquitetura de software e as decisões de engenharia do Hedge-fund-lab. O projeto foi estruturado para garantir isolamento temporal dos dados (ausência de \textit{look-ahead bias}), rastreabilidade determinística das decisões e paridade contábil entre as carteiras multiagentes e as estratégias de referência.`
  - Mover a Tabela 4.3 (Seção 4.9.6), os detalhes operacionais de `CallBank`/reservas HTTP/rotas de exportação (`04:252-264`) e as Seções `4.11` e `4.12` para o **Apêndice A** (reduzindo o Cap. 4 de 17 para ~11 páginas).
  - Acrescentar ao final de `04:100`: `A correção contábil do \textit{ledger} de eventos utilizado no replay é verificada por asserções automáticas de conservação de patrimônio ($\text{PL}_t = \text{Caixa}_t + \sum_a \text{qtd}_{a,t} \cdot P^{\text{RAW}}_{a,t}$), de paridade bit a bit das cinco carteiras de referência entre as campanhas v1, v2 e v3 e de reconciliação entre custos operacionais e fluxos de caixa.`

- **C4-08** · **Severidade:** Médio  
  **Local:** Figuras 4.1 (`04:48-70`), 4.2 (`04:115-136`), 4.3 (`04:170-204`) e Tabelas 4.1 (`04:15-40`), 4.2 (`04:268-303`), 4.3 (`04:311-333`)  
  **Problema:**
  1. **Nenhuma** das 3 figuras e 3 tabelas do Capítulo 4 possui indicação de **`Fonte:`** abaixo do elemento (padrão ABNT / guia do curso).
  2. Na **Figura 4.1** (PDF p. 32), o diagrama mostra apenas o fluxo antigo `Yahoo Finance -> Validação -> Snapshot Parquet + SHA-256 -> CausalMarketWindow`, omitindo a separação entre cotações `RAW` da B3 (marcação a mercado e liquidação) e fatores de ajuste do Yahoo Finance (janelas técnicas e proventos) usada no replay multiativos (texto L72–79).
  3. Na **Figura 4.2** (PDF p. 35), o rótulo inclinado `\texttt{veredito = APROVADO}` colide visualmente com a borda inferior da caixa `portfolio_manager`, e a seta `caso contrário` para `hold_terminal` não explicita que a decisão resultante é `MANTER`.
  4. Na **Figura 4.3** (PDF p. 38), as caixas com `fill=black!6` ficam quase invisíveis em impressão P&B (usar `fill=black!12` ou `black!15` com borda `draw=black!80`), e a primeira caixa sofre hifenização ruim (`5 anal-istas`).  
  **Correção proposta:** Adicionar `Fonte: Elaborado pelos autores.` abaixo das Figuras 4.1–4.3 e Tabelas 4.1–4.3; atualizar a Figura 4.1 com as duas fontes de dados (`B3 COTAHIST RAW` e `Yahoo Finance ajustado/proventos`); na Figura 4.2, usar seta ortogonal ou posicionar o rótulo acima sem `sloped` e escrever `caso contrário (MANTER)`; na Figura 4.3, ajustar a largura/texto da primeira caixa (`Comitê por ativo (5 analistas)`) e elevar o contraste para `fill=black!12, draw=black!80`.

- **C4-09** · **Severidade:** Médio  
  **Local:** `chapters/04-arquitetura.tex:152, 168, 215, 242, 254, 342, 351` (p. 24–29, 33–34 / PDF p. 36–41, 45–46)  
  **Trecho:** L168: `permitindo medir desvios de execução (implementation shortfall)`; L215 e L351: `alertas de tese velha`; L242: `\texttt{--references-only}`; L152 e L254: `temperatura 1,0` + `CallBank`; L342: `v3 é tratada no Capítulo 5 como iteração exploratória`.  
  **Problema:**
  1. Em `04:242`, `\texttt{--references-only}` sofre ligadura de fonte T1 e imprime um *en-dash* (`–references-only`) em vez de dois hifens (`--references-only`).
  2. Em `04:168`, afirma-se que os campos de decisão permitem *"medir desvios de execução (implementation shortfall)"*, métrica que nunca é calculada no trabalho (`FS-5`).
  3. Em `04:215` e `04:351`, o jargão interno `"alertas de tese velha"` é usado sem definição (trata-se do alerta disparado quando o retorno diário do ativo excede $3\sigma$ da volatilidade recente, sinalizando que a tese anterior pode estar defasada, conforme DP-33).
  4. Em `04:152` e `04:254`, é preciso deixar explícito que, como a temperatura da API é `1,0` (geração estocástica), a reprodutibilidade determinística das campanhas v1, v2 e v3 provém do reuso das respostas arquivadas no `CallBank` (`provider_journal.jsonl`), e não de uma nova consulta ao provedor.
  5. Em `04:342`, convém quantificar o grau de liberdade adicionado na v3: os 5 *prompts* heterogêneos mais as 3 travas do compilador introduzem **pelo menos 17 novos limiares numéricos** (`RSI < 32`, `32..42`, `> 72`, `62..72`, `> 55`, `< 45`, `> 75`, `> 68`, `sma50_gap > +0,01`, `< -0,01`, `bb_lower_gap -0,01..+0,06`, `bb_upper_gap > -0,04`, `< -0,01`, `macd_ratio > -0,015`, `bb_width > 0,06`, `score <= -0,30`, `qtd < 100` / `< R$ 2.000`, `5%..30%`), todos calibrados após observar o próprio período de 153 pregões.  
  **Correção proposta:** Escrever `\texttt{-{}-references-only}` em `04:242`; substituir `"medir desvios de execução (implementation shortfall)"` por `"auditar a diferença entre o preço de referência da decisão e o preço efetivo de liquidação"` em `04:168`; definir `"alertas de invalidação de tese por choque de preço ($> 3\sigma$)"` em `04:215`; explicitar o papel do `CallBank` para reprodutibilidade exata sob temperatura `1,0`; e registrar os 17 limiares na Seção 4.10.

- **C4-10** · **Severidade:** Baixo  
  **Local:** `chapters/04-arquitetura.tex:84, 216, 217, 311-333, 366` (p. 21, 28, 32, 34)  
  **Trecho:** L84: `(replay)` para *event sourcing*; L216: `taxa operacional fixa de 0,03% (3 bps)`; L217: `retenção de 15% na fonte para JCP`; L311–333: coluna `Valor` da Tabela 4.3 sem unidades; L366: `\subsection{Frontend e Operação}`.  
  **Problema:** Em L84, usar `(replay)` para a reconstrução contábil do *ledger* gera ambiguidade com o experimento de *replay* histórico; em L216, convém contextualizar que 0,03% corresponde à ordem de grandeza dos emolumentos e taxa de liquidação da B3 (sem corretagem variável nem *slippage*); em L217, convém notar que há retenção de 15% de IR na fonte sobre JCP, mas não há modelagem de IR de 15% sobre ganho de capital mensal em vendas acima de R\$ 20 mil; na Tabela 4.3, acrescentar unidades (`s`, `chamadas`, `US$`, `pregões`); em L366, substituir o estrangeirismo `Frontend` no título por `Interface de Acompanhamento e Consulta`.

*Balanço micro do Cap. 4:* **70 parágrafos/itens revisados** (62 parágrafos em prosa + 8 itens de lista); **29 apresentaram problemas**.

---

### Capítulo 5 — Metodologia Experimental (`chapters/05-metodologia.tex`; p. 36–48 / PDF p. 48–60)

- **C5-01** · **Severidade:** Crítico  
  **Local:** `chapters/05-metodologia.tex:59, 61, 88, 90, 92, 111, 113, 188, 190, 192, 203, 205, 207, 209, 211, 213` (p. 38–47 / PDF p. 50–59)  
  **Problema:** 16 comandos `\paragraph{}` que geram numerações de 5 níveis com `.0.0.` (`5.3.0.0.1` a `5.8.0.0.7`) no corpo e nos favoritos do PDF (ver `P-02`).  
  **Correção proposta:** Converter para `\noindent\textbf{...}` ou `\subsection{}` numerada.

- **C5-02** · **Severidade:** Crítico  
  **Local:** `chapters/05-metodologia.tex:188` (p. 45 / PDF p. 57)  
  **Trecho:** `Sobre esse conjunto foram definidos o conjunto de endurecimento real $H_{\text{real}}$ (1.519 sessões entre 12/01/2018 e 28/02/2024)...`  
  **Problema:** Repete o erro factual de `C4-01`: `1.519 sessões` é o universo elegível de âncoras $|E|$, enquanto $H_{\text{real}}$ possui apenas **4 sessões reais** (quantis 0,2; 0,4; 0,6 e 0,8 de $|E|$).  
  **Correção proposta:**
  > `Sobre esse conjunto foram definidos o universo de 1.519 sessões elegíveis como âncora (entre 12/01/2018 e 28/02/2024, após 504 pregões de aquecimento), do qual foram extraídas quatro sessões reais para o conjunto de endurecimento $H_{\text{real}}$ (combinadas a oito cenários sintéticos $H_{\text{syn}}$), além de dez janelas candidatas de 252 pregões sem sobreposição.`

- **C5-03** · **Severidade:** Crítico  
  **Local:** `chapters/05-metodologia.tex:205` (p. 46 / PDF p. 58 — e repetido em `06-resultados.tex:191`, p. 61, e `07-conclusao.tex:47`, p. 67)  
  **Trecho:** `A contaminação, se existir, favorece a carteira Multiagentes; portanto, um resultado nulo ou negativo para H2 permanece informativo mesmo sob essa ameaça, enquanto um resultado positivo exigiria confirmação prospectiva.`  
  **Problema:** Afirmação metodologicamente insustentável por duas razões:
  1. **Contradição direta com o Capítulo 3 da própria monografia:** na Seção 3.5 (`03-relacionados.tex:46`, p. 14), os autores citam \citet{Glasserman2023} para demonstrar que o conhecimento prévio do modelo sobre empresas de grande capitalização frequentemente produz um **efeito de distração (*distraction effect*) que degrada o desempenho** da estratégia, em vez de melhorá-lo. Se a contaminação pode degradar o desempenho (por exemplo, levando o gestor `portfolio_manager` a hesitar ou ancorar em memórias difusas da trajetória de `PETR4` ou `VALE3`), então a direção do viés **não é garantidamente favorável aos agentes**;
  2. **Omissão do isolamento de identidade nos analistas:** a ameaça de contaminação incide de maneira assimétrica na arquitetura — os cinco analistas técnicos e o analista de risco não recebem o *ticker*, a data nem o preço nominal (`src/agents/features.py:23-26`), de modo que apenas o `portfolio_manager` recebe códigos de ativos e datas.  
  **Correção proposta:** Substituir as duas últimas frases de `05:205` (e harmonizar `06:191` e `07:47`) por:
  > `Na arquitetura implementada, esse risco é parcialmente contido pelo fato de que os cinco analistas técnicos e o analista de risco recebem apenas vetores adimensionais de indicadores, sem identificação do ativo, da data ou do nível nominal de preço; contudo, o gestor global da carteira (\texttt{portfolio\_manager}) recebe os códigos dos cinco ativos e o histórico recente do replay. Além disso, como demonstram \citet{Glasserman2023}, o conhecimento prévio sobre empresas de grande capitalização pode operar tanto como vantagem informacional espúria quanto como efeito de distração que degrada o sinal específico do período. Assim, embora a ausência de superioridade observada no replay descarte a hipótese de que uma eventual memorização tenha gerado ganhos anormais líquidos, a separação rigorosa entre capacidade de generalização e efeitos de pré-treinamento exige avaliação prospectiva estritamente posterior ao corte de conhecimento.`

- **C5-04** · **Severidade:** Alto  
  **Local:** `chapters/05-metodologia.tex:122, 213` (p. 42, 47 / PDF p. 54, 59 — e `06-resultados.tex:52-59`, `07-conclusao.tex:54`)  
  **Trecho:** L122: `A taxa livre de risco é fixada em $r_f = 0$ para todas as carteiras, pois o saldo em caixa não é remunerado por Selic ou CDI na simulação; a convenção preserva a consistência interna entre numerador e denominador e é discutida como limitação na Seção 5.8.` · L213: `a ausência de remuneração de caixa por CDI ou Selic penaliza estratégias que mantêm fração relevante do patrimônio em liquidez.`  
  **Problema:** A escolha de não remunerar o caixa e fixar $r_f = 0$ é metodologicamente defensável como convenção de simulação, mas a discussão na Seção 5.8 (`05:213`) é incompleta porque não explicita **quais hipóteses e comparações são afetadas e em que direção**:
  - As carteiras mantiveram frações médias de caixa radicalmente distintas ao longo dos 153 pregões: **Bollinger 20/2** manteve **49,06%** em caixa médio; **SMA 50/200**, **31,39%**; **Multiagentes v2**, **24,69%**; **Multiagentes v1**, **15,74%**; **Multiagentes v3**, **14,50%**; enquanto **Buy & Hold** (**0,13%**), **Equal Weight 63d** (**0,70%**) e **Mínima Variância 252/63** (**0,62%**) permaneceram quase 100% investidas.
  - Em um mercado brasileiro com Selic/CDI de dois dígitos anuais, remunerar o caixa pelo CDI diário aumentaria o retorno acumulado das carteiras defensivas em proporção direta ao seu caixa médio.
  - **Impacto concreto em H1:** a carteira `SMA 50/200` ficou apenas **1,00 p.p.** atrás de `Equal Weight 63d` em retorno acumulado (`-7,63%` vs `-6,63%`), mas carregou **30,69 p.p. a mais de caixa médio** (`31,39%` vs `0,70%`). Qualquer remuneração de caixa acima de ~3,3% no período de 7 meses (~5,5% a.a., menos da metade do CDI vigente) **inverteria o sinal da diferença descritiva de retorno acumulado** em favor da `SMA 50/200`!
  - **Impacto concreto em H2:** remunerar o caixa ampliaria ainda mais a vantagem da `Bollinger 20/2` (`49,06%` de caixa médio) e da `SMA 50/200` (`31,39%`) sobre `Multiagentes v1` e `v3` (`~15%` de caixa médio). Por outro lado, deduzir $r_f = \text{CDI}$ no numerador do índice de Sharpe faria com que **todas** as oito carteiras (inclusive `Bollinger 20/2`, com `+4,89%` no período) apresentassem Sharpe em excesso ao CDI negativo.  
  **Correção proposta:** Expandir `05:213` (e comentar na Seção 6.3) com essa análise quantitativa da direção do viés sobre H1 e H2. Isso mostra maturidade financeira imediata para o membro externo da banca.

- **C5-05** · **Severidade:** Alto  
  **Local:** `chapters/05-metodologia.tex:27, 209` (p. 37, 47 / PDF p. 49, 59)  
  **Trecho:** L27: `O universo de ativos é composto por cinco ações ordinárias ou preferenciais de alta liquidez negociadas na B3: Banco do Brasil (\texttt{BBAS3}), Itaú Unibanco (\texttt{ITUB4}), Petrobras (\texttt{PETR4}), Vale (\texttt{VALE3}) e WEG (\texttt{WEGE3}).`  
  **Problema:** O texto não informa **quais critérios objetivos** determinaram a escolha dessas cinco ações, **quando** essa seleção foi fixada (segundo `docs/DIRECAO_DO_PROJETO.md`, DP-07 foi registrada em `13/10/2026`, quando quase toda a janela de abril a novembro de 2026 já havia transcorrido) e quais vieses decorrem dessa composição: (1) concentração em dois grandes bancos (`BBAS3`, `ITUB4`), duas exportadoras de *commodities* (`PETR4`, `VALE3`) e uma industrial exportadora (`WEGE3`), deixando de fora setores domésticos cíclicos (varejo, construção, saúde, *utilities*); (2) viés de sobrevivência e seleção retrospectiva de *blue chips* de alta liquidez.  
  **Correção proposta:** Explicitar na Seção 5.2 (L27) o critério de seleção (liquidez diária, representatividade nos principais setores do Ibovespa e continuidade de negociação sem eventos societários complexos de fusão/cisão no período) e a data em que o universo foi congelado (DP-07), e acrescentar na Seção 5.8 (`05:209`) a discussão sobre concentração setorial e seleção retrospectiva do universo.

- **C5-06** · **Severidade:** Alto  
  **Local:** `chapters/05-metodologia.tex:63-73, 95-106, 113, 168-170, 219` (p. 38, 41, 43–44, 48 / PDF p. 50, 53, 55–56, 60)  
  **Problema:** Defeitos de paginação, tabelas e estrutura de parágrafos no Capítulo 5:
  1. **Página 48 (PDF p. 60) quase totalmente em branco:** contém apenas **uma única linha viúva** no topo (`e a evidência fornecida por essa série curta no escopo deste TCC é apenas operacional.`) antes do salto para o Capítulo 6.
  2. **Tabela 5.1** (`05:63-73`, p. 38 / PDF p. 50) estoura a margem direita em **`+8,17 pt`** e não tem `Fonte:`.
  3. **Tabela 5.2** (`05:95-106`, p. 41 / PDF p. 53) estoura a margem direita em **`+1,86 pt`**, não tem `Fonte:` e flutua para o meio da Seção 5.5 (cortando a definição da carteira Mínima Variância 252/63).
  4. **Linha 113** (`05:113`, p. 41 / PDF p. 53) estoura a margem direita em **`+13,30 pt`** no identificador `\texttt{--references-only}` (que ainda imprime *en-dash* `–references-only`).
  5. **Linha 168** (`05:168`, p. 43) é um parágrafo de uma única frase (`"A comparação entre carteiras sobre a mesma janela histórica exige um método inferencial que preserve a dependência serial e a correlação contemporânea entre estratégias."`), seguido imediatamente na **Linha 170** por um parágrafo monolítico de **276 palavras** (quase meia página sem quebra).  
  **Correção proposta:**
  - Nas Tabelas 5.1 e 5.2, reduzir `p{7.8cm}` para `p{7.4cm}` (Tabela 5.1) e `p{4.6cm}` para `p{4.4cm}` (Tabela 5.2), acrescentar `Fonte: Elaborado pelos autores.` abaixo de cada tabela e posicionar a Tabela 5.2 com `[!htbp]` antes da Seção 5.5.
  - Em `05:113`, substituir `\texttt{--references-only}` por `\texttt{-{}-references-only}`.
  - Fundir `05:168` com a primeira metade de `05:170` (descrição do algoritmo do bootstrap estacionário pareado e escolha de $\ell = 10$) e abrir um segundo parágrafo em `05:170` a partir de `"Em cada réplica $b \in \{1, \dots, B\}$..."` (cálculo do p-valor unilateral, intervalo de confiança percentílico e ajuste de Holm-Bonferroni).
  - O enxugamento de 1–2 linhas na Seção 5.8 (ou a conversão das ameaças em tabela sintética) elimina a linha viúva isolada da página 48 (PDF p. 60).

- **C5-07** · **Severidade:** Alto  
  **Local:** `chapters/05-metodologia.tex:194` (p. 45 / PDF p. 57)  
  **Trecho:** `Primeiro, a alteração do escopo de tese de ativo único para carteira multiativos, registrada na emenda ao congelamento como mudança de escopo de alto impacto autorizada apenas pelo autor e sem ratificação acadêmica. Segundo, a janela de teste pós-corte originalmente planejada no documento de congelamento (01/03/2024 a 31/08/2026) ficou inteiramente anterior ao corte de conhecimento do modelo \texttt{gemini-3.8-flash} (março de 2026), o que invalidou sua premissa de ausência de contaminação. Terceiro, o custo de inferência de três execuções por fase sobre janelas anuais.`  
  **Problema:** (1) A expressão `"autorizada apenas pelo autor e sem ratificação acadêmica"` usa o singular (`"pelo autor"`, em uma monografia de dois autores orientada por professor doutor) e transpõe literalmente uma nota de governança interna do repositório (`Amendment 1` de `H2_METHODOLOGICAL_FREEZE_V1.md`) de modo que soa à banca como se a mudança não tivesse aval do orientador; (2) a última frase (`"Terceiro, o custo de inferência de três execuções por fase sobre janelas anuais."`) **não possui verbo** (frase nominal truncada).  
  **Correção proposta:**
  > `Primeiro, a evolução do escopo experimental de um único ativo para uma carteira multiativos com cinco ações da B3, documentada no Adendo 1 do protocolo metodológico para alinhar o experimento aos objetivos de alocação de portfólio do trabalho. Segundo, a janela pós-corte originalmente prevista para modelos da geração 2024 (01/03/2024 a 31/08/2026) passou a situar-se majoritariamente antes do corte de conhecimento do modelo \texttt{gemini-3.8-flash} (março de 2026), o que exigiu deslocar o período experimental para abril a novembro de 2026. Terceiro, o protocolo original previa três execuções independentes por fase sobre janelas anuais completas, o que elevaria substancialmente o custo financeiro e o tempo de inferência quando multiplicado por cinco ativos.`

- **C5-08** · **Severidade:** Médio  
  **Local:** `chapters/05-metodologia.tex:36, 56, 79, 120-163, 200` (p. 37–46 / PDF p. 49–58)  
  **Problema:**
  1. Em `05:36` vs `05:151-163`, H01 e H02 são enunciadas em texto como *"não há diferença estatisticamente significativa"*, mas a regra de decisão formal na Seção 5.6.2 é unilateral ($H_0: \Delta_{A,B} \leq 0$ contra $H_1: \Delta_{A,B} > 0$). Explicitar já na Seção 5.3 que a ausência de superioridade é testada via hipótese nula direcional $\Delta_{A,B} \leq 0$.
  2. Em `05:56`, esclarecer em uma frase que os dois ensaios preliminares curtos em abril e maio de 2026 serviram apenas para verificar a estabilidade operacional do *runner* e do *ledger*, **sem alteração de prompts, limiares ou regras do compilador v1** antes da campanha completa de 153 pregões.
  3. Na Seção 5.6.1 (`05:120-147`), o texto define apenas o Sharpe anualizado (Eq. 5.1), o Sortino (Eq. 5.2), o *profit factor* (Eq. 5.3) e o giro (Eq. 5.4, onde `\overline{PL}` deve ser `\overline{\mathrm{PL}}`), mas **omite as fórmulas** de quatro métricas primárias da Tabela 6.2 implementadas em `tcc2/scripts/metricas_replay.py:55-97`: retorno diário simples $r_t = \mathrm{PL}_t / \mathrm{PL}_{t-1} - 1$ (com $r_1 = 0$), retorno anualizado composto $(1 + R_{\text{total}})^{252/N} - 1$ (com $N = 153$), volatilidade anualizada $\sigma_{\text{anual}} = s(r) \cdot \sqrt{252}$ (com desvio-padrão amostral $ddof=1$) e *drawdown* máximo $\mathrm{MDD} = \min_t (\mathrm{PL}_t / \max_{s \leq t} \mathrm{PL}_s - 1)$.

*Balanço micro do Cap. 5:* **64 parágrafos/itens revisados** (56 parágrafos em prosa + 8 itens de lista); **24 apresentaram problemas**.

---

### Capítulo 6 — Resultados e Discussão (`chapters/06-resultados.tex` e `chapters/tabelas/*.tex`; p. 49–63 / PDF p. 61–75)

- **C6-01** · **Severidade:** Crítico  
  **Local:** `chapters/06-resultados.tex:175` vs `06-resultados.tex:156` (p. 60 vs p. 58 / PDF p. 72 vs p. 70)  
  **Trecho:** L175: `Por ativo, PETR4 (+R\$ 3.222,19), WEGE3 (+R\$ 1.991,89) e ITUB4 (+R\$ 1.435,82) passaram a resultado positivo, compensando as perdas em BBAS3 (-R\$ 4.621,16) e VALE3 (-R\$ 1.787,74).` vs L156: `PETR4 foi o único ativo sem saída total e o único com resultado positivo.`  
  **Problema:** Contradição interna direta entre as páginas 58 e 60. Na campanha v2, `PETR4` **já tinha resultado líquido positivo** (`+R$ 1.812,50`, conforme `evolucao_replay_v1_v2_v3_tcc.md:94` e a própria L156). Quem *passou* de resultado negativo na v2 para positivo na v3 foram apenas **`WEGE3`** (de `-R$ 2.385,99` para `+R$ 1.991,89`) e **`ITUB4`** (de `-R$ 2.752,41` para `+R$ 1.435,82`), enquanto `PETR4` ampliou o ganho que já era positivo (de `+R$ 1.812,50` para `+R$ 3.222,19`).  
  **Correção proposta:**
  > `Por ativo, PETR4 ampliou o resultado positivo já observado na v2 (de +R\$~1.812,50 para +R\$~3.222,19), enquanto WEGE3 (+R\$~1.991,89 ante -R\$~2.385,99 na v2) e ITUB4 (+R\$~1.435,82 ante -R\$~2.752,41 na v2) reverteram suas perdas e passaram ao campo positivo, compensando os resultados negativos em BBAS3 (-R\$~4.621,16) e VALE3 (-R\$~1.787,74).`

- **C6-02** · **Severidade:** Crítico  
  **Local:** `chapters/06-resultados.tex:204-206` (p. 62–63 / PDF p. 74–75)  
  **Trecho:** `Nos 23 pregões observados, a carteira Buy \& Hold acumulou queda de 17,61\% (patrimônio final de R\$ 82.391,17), refletindo a continuidade do regime baixista na janela prospectiva. As referências Equal Weight e Mínima Variância acompanharam exactamente sua trajetória, de R\$ 99.835,33 em 14/10 para R\$ 82.391,17 em 16/11 (-17,61\%), pois a janela curta não atingiu um ciclo de rebalanceamento diferente do estado inicial. A carteira Multiagentes executou compras apenas no primeiro pregão e manteve todas as posições nos 22 pregões seguintes; sem vendas e com caixa residual de R\$ 107,04, terminou em R\$ 76.059,11 (-23,94\%), com drawdown máximo de -24,02\%.`  
  **Problema:** Duas falhas que comprometem a leitura da Seção 6.8:
  1. **Omissão da versão avaliada:** o texto não informa que a carteira Multiagentes executada no ciclo diário prospectivo é a **v1** (`wallet_manager_api.py`). Sem essa informação, o leitor não compreende por que ela repetiu exatamente o comportamento da v1 no replay (comprar na abertura e manter as posições pelos 22 pregões seguintes sem vender), nem que as alterações exploratórias da v2 e da v3 ainda não haviam sido implantadas no ciclo diário. Além disso, `equity_diario.csv` mostra que o painel prospectivo também acompanhou as carteiras `SMA 50/200` (PL final `R$ 83.249,25`, `-16,75%`) e `Bollinger 20/2` (PL final `R$ 85.402,91`, `-14,60%`).
  2. **Ambiguidade aritmética na base percentual:** a frase `"de R$ 99.835,33 em 14/10 para R$ 82.391,17 em 16/11 (-17,61%)"` faz parecer que `-17,61%` é a variação entre `99.835,33` e `82.391,17`, quando $(82.391{,}17 / 99.835{,}33) - 1 = -17{,}47\%$. O percentual `-17,61%` (assim como `-23,94%` para `R$ 76.059,11`) é calculado sobre o **capital inicial de R\$ 100.000,00** (fechamento de referência de `13/10/2026`, antes dos custos e da variação do primeiro pregão em `14/10/2026`, no qual a carteira Multiagentes fechou em `R$ 100.106,07`).  
  **Correção proposta:**
  > `Nos 23 pregões observados (com capital inicial de R\$~100.000,00 posicionado ao fechamento de referência de 13/10/2026), a carteira Buy \& Hold encerrou o primeiro pregão (14/10) em R\$~99.835,33 e o 23º pregão (16/11) em R\$~82.391,17, acumulando retorno de -17,61\% em relação ao capital inicial (-17,47\% em relação ao fechamento de 14/10). As referências Equal Weight e Mínima Variância acompanharam exatamente essa trajetória, pois a janela de 23 pregões não atingiu o ciclo de rebalanceamento de 63 sessões, enquanto as regras técnicas Bollinger 20/2 e SMA 50/200 terminaram o período em R\$~85.402,91 (-14,60\%) e R\$~83.249,25 (-16,75\%), respectivamente. A carteira Multiagentes --- operada no ciclo diário com a configuração pré-especificada v1 (\texttt{wallet\_manager\_api.py}) --- executou compras apenas no primeiro pregão (fechando 14/10 em R\$~100.106,07) e manteve todas as posições nos 22 pregões seguintes; sem vendas e com caixa residual de R\$~107,04, encerrou 16/11 em R\$~76.059,11 (-23,94\% sobre o capital inicial; -24,02\% de \textit{drawdown} máximo em relação ao pico de 14/10). Esse comportamento reproduz em tempo real o diagnóstico de inércia da v1 documentado na Seção 6.6.`

- **C6-03** · **Severidade:** Crítico  
  **Local:** `chapters/06-resultados.tex:25-36` (p. 49 / PDF p. 61 — Tabela 6.1) e 14 ocorrências de `\paragraph{}` em `06:82-193` (p. 54–62 / PDF p. 66–74)  
  **Problema:** (1) A Tabela 6.1 (`Paridade das carteiras de referência entre as campanhas v1, v2 e v3`) tem soma de larguras de colunas superior a `\textwidth` e **estoura a margem direita em `+25,55 pt`**; (2) 14 comandos `\paragraph{}` geram cabeçalhos `6.4.0.0.1` a `6.7.0.0.5` (`P-02`).  
  **Correção proposta:** Na Tabela 6.1 (`06:28`), substituir `\begin{tabular}{l r r r p{4.2cm}}` por `\begin{tabular}{l r r r >{\raggedright\arraybackslash}p{3.1cm}}` (ou usar `tabularx{\textwidth}{l r r r X}`); converter os 14 `\paragraph{}` em `\noindent\textbf{...}` ou `\subsection{}`.

- **C6-04** · **Severidade:** Alto  
  **Local:** `chapters/06-resultados.tex:177` e `06-resultados.tex:184` (p. 60–61 / PDF p. 72–73 — e repetido em `07-conclusao.tex:36`, p. 66)  
  **Trecho:** L177: `Em conjunto, esses efeitos mostram que, na v3, a governança determinística moldou o resultado tanto quanto os sinais gerados pelo modelo de linguagem.` · L184: `Em termos de engenharia de sistemas multiagentes aplicados a finanças, a transição mostra que o número de agentes importa menos que a diferença entre as funções atribuídas a eles.`  
  **Problema:** Duas extrapolações causais que violam a regra de `WRITING_RULES.md:33` (*"Afirmações fortes exigem evidência direta... Caso contrário, enfraquecer ou remover"*):
  1. Em `06:184`, o experimento **manteve o número de agentes fixo** em todas as campanhas (5 analistas técnicos + 1 analista de risco por ativo + 1 gestor global). Como o número de agentes nunca foi variado ($N=1$ vs $N=3$ vs $N=5$), o trabalho não possui evidência empírica para afirmar que *"o número de agentes importa menos que a diferença entre as funções atribuídas a eles"*.
  2. Em `06:177` (e `07:36`), como a v3 alterou **simultaneamente** a separação dos 5 *prompts* do comitê e as 3 travas do compilador determinístico (sem estudo de ablação isolando cada fator), não é possível medir a contribuição marginal relativa de cada um nem afirmar que um moldou o resultado *"tanto quanto"* o outro.  
  **Correção proposta:**
  - Em `06:184`: `Em termos de engenharia de sistemas multiagentes aplicados a finanças, a transição da v2 para a v3 mostra que a simples multiplicidade de agentes consultados sob instruções homogêneas não garante diversidade de sinais: mantendo-se fixo o número de cinco analistas no comitê, a dispersão efetiva de recomendações só emergiu quando cada agente recebeu uma função analítica distinta e faixas explícitas de atuação.`
  - Em `06:177` (e `07:36`): `Em conjunto, esses efeitos indicam que o resultado da v3 dependeu da ação combinada entre os sinais heterogêneos gerados pelo comitê e as restrições determinísticas do compilador, que vetaram 52 compras e redimensionaram 27 vendas ao longo da campanha; como ambos os mecanismos foram introduzidos simultaneamente na v3, a decomposição quantitativa do efeito isolado de cada um requer um experimento fatorial de ablação.`

- **C6-05** · **Severidade:** Alto  
  **Local:** `chapters/tabelas/metricas-replay.tex` (Tabelas 6.2 e 6.3, p. 50 / PDF p. 62) e `chapters/tabelas/bootstrap-replay.tex` (Tabela 6.4, p. 53 / PDF p. 65)  
  **Problema:** Quatro problemas de apresentação e leitura nas tabelas principais de resultados:
  1. **Discrepância visual de `0,01` em 9 das 16 linhas da Tabela 6.4:** na Tabela 6.2, os índices de Sharpe são exibidos arredondados a duas casas (`v3 = 0,09`, `SMA 50/200 = -1,42`, `Buy & Hold = -0,78`), mas na Tabela 6.4 a coluna $\Delta$ é obtida pela subtração dos Sharpes **não arredondados** antes do arredondamento final ($0{,}0862 - (-1{,}4173) = 1{,}5035 \to +1{,}50$, enquanto $0{,}09 - (-1{,}42) = +1{,}51$; e $0{,}0862 - (-0{,}7786) = 0{,}8648 \to +0{,}86$, enquanto $0{,}09 - (-0{,}78) = +0{,}87$). Sem uma nota explicativa, um examinador que subtraia os valores da Tabela 6.2 achará que há erro de conta em 9 linhas da Tabela 6.4.
  2. **Sigla `MA v1..v3` ambígua na Tabela 6.4:** a Tabela 6.4 abrevia `Multiagentes` como `MA v1`, `MA v2` e `MA v3` sem definir a sigla, que colide diretamente com `MA` (*Moving Average*, Eq. 2.1).
  3. **Compressão tipográfica por `\resizebox{\textwidth}{!}`:** as Tabelas 6.2, 6.3 e 6.4 usam `\resizebox{\textwidth}{!}` sem `\textbf{}` nos cabeçalhos, reduzindo a fonte da Tabela 6.2 para ~7 pt no PDF.
  4. **Sigla `MDD` sem definição prévia:** o cabeçalho da Tabela 6.2 usa `MDD (\%)` na página 50, mas a sigla só aparece por extenso na página 52 (`06:55`).  
  **Correção proposta:**
  - Nas Tabelas 6.2, 6.3 e 6.4 (e nos geradores `tcc2/scripts/metricas_replay.py` e `bootstrap_replay.py`, caso os autores regenerem as tabelas), remover `\resizebox{\textwidth}{!}` em favor de `{\small \setlength{\tabcolsep}{3.5pt} ...}` com cabeçalhos em `\textbf{}`.
  - Na Tabela 6.4, escrever `Multiagentes v1/v2/v3` por extenso (ou definir `MA = Multiagentes` na nota da tabela) e incluir na nota/fonte: `Nota: Os valores de $\Delta = \text{Sharpe}(A) - \text{Sharpe}(B)$ são calculados em precisão de ponto flutuante antes do arredondamento a duas casas decimais.`
  - Definir `MDD` (*Maximum Drawdown*) na Seção 5.6.1 e antes da Tabela 6.2.

- **C6-06** · **Severidade:** Alto  
  **Local:** `chapters/06-resultados.tex:52-59, 73, 179, 184-197` (p. 52, 54, 60–62 / PDF p. 64, 66, 72–74)  
  **Problema:** Duas discussões financeiras essenciais estão ausentes na interpretação dos resultados:
  1. **Exposição de mercado (*market exposure*) vs seleção de ativos em regime baixista:** a superioridade descritiva de `Bollinger 20/2` (`+4,89%`, MDD `-7,09%`) decorreu primordialmente de ter permanecido **49,06% do tempo médio em caixa** durante uma queda de `-11,21%` da carteira `Buy & Hold` (e a `SMA 50/200` manteve `31,39%` em caixa médio). Já a `Multiagentes v3` manteve apenas **14,50% de caixa médio** (~85,5% investida em ações ao longo da queda) e ainda assim preservou o capital (`+0,07%`, superando `Buy & Hold` em `+11,28 p.p.`, `Equal Weight 63d` em `+6,70 p.p.` e `Mínima Variância` em `+4,04 p.p.`). Destacar essa diferença de exposição média ao risco de mercado enriquece a análise sem violar a conclusão estatística nula.
  2. **Microestrutura da B3 e mercado fracionário nas 27 vendas residuais da v3:** na Seção 6.6.3 (`06:179`), o texto relata que a trava de posição residual forçou a liquidação total em 27 das 29 vendas da v3 (27 vendas abaixo de R\$ 2.000, sendo 22 abaixo de R\$ 500, com ordens de 1 a 9 ações). Na B3, o lote-padrão é de 100 ações, de modo que ordens de 1 a 99 ações são negociadas no **mercado fracionário** (`PETR4F`, `VALE3F` etc.), onde o *bid-ask spread* e o impacto de liquidez são maiores que no lote-padrão (enquanto a simulação aplica apenas a taxa proporcional de 0,03% sem custo mínimo nem *spread* diferenciados). Esse ponto deve ser discutido na Seção 6.6.3 ou na Seção 6.7.

- **C6-07** · **Severidade:** Médio  
  **Local:** `chapters/06-resultados.tex:39, 44-57` e `figures/replay-patrimonio.tex`, `replay-drawdown.tex`, `replay-caixa.tex` (p. 50–51, 59 / PDF p. 62–63, 71)  
  **Problema:**
  1. **Ordem de citação invertida:** a **Figura 6.2** é citada na linha 39 (`06:39`, página 49), **antes** da primeira citação da **Figura 6.1** na linha 44 (`06:44`, página 51).
  2. **Falta de interpretação temporal da Figura 6.1:** o parágrafo `06:44` apenas diz que a Figura 6.1 *"apresenta a evolução diária do patrimônio líquido"*, sem descrever os três regimes visíveis nas curvas (a alta inicial até o pico de maio de 2026 em torno de R\$ 106–108 mil, a correção acentuada entre junho e setembro quando `v1` e `Buy & Hold` caem abaixo de R\$ 86 mil enquanto `Bollinger 20/2` preserva patrimônio em caixa, e a divergência final em outubro–novembro na qual `v3` retorna a R\$ 100.068,54 e `v1` encerra em R\$ 82.179,89).
  3. **Rótulo de eixo impreciso e falta de `Fonte:`:** nas Figuras 6.1, 6.2 e 6.3, o eixo horizontal está rotulado como `xlabel={Pregão (2026)}`, mas os *ticks* mostram meses (`abr`, `mai`, `jun`, `jul`, `ago`, `set`, `out`, `nov`); nenhuma das três figuras traz `Fonte:` abaixo da legenda; na Figura 6.2, `Drawdown` aparece sem itálico no eixo Y e na legenda; e nas Figuras 6.1 e 6.2 há 8 curvas monocromáticas em tons de cinza onde `Equal Weight 63d` e `Mínima Variância` quase se confundem com `Buy & Hold` e `SMA 50/200`.  
  **Correção proposta:** Em `06:39`, citar `Figuras~\ref{fig:replay-patrimonio} e~\ref{fig:replay-drawdown}`; expandir `06:44` com a leitura dos três subperíodos da Figura 6.1; trocar `xlabel={Pregão (2026)}` por `xlabel={Mês de referência (2026)}`; colocar `\textit{Drawdown}` na Figura 6.2; adicionar `Fonte: Elaborado pelos autores.` nas três figuras; e diferenciar `Equal Weight 63d` e `Mínima Variância` com marcadores discretos a cada 25 pregões (`mark repeat=25`) ou paleta daltônico-segura que preserve contraste em luminância P&B.

- **C6-08** · **Severidade:** Médio  
  **Local:** `chapters/06-resultados.tex:52, 58, 152, 195` (p. 52, 57, 62 / PDF p. 64, 69, 74)  
  **Trecho:** L52: `Apenas duas carteiras tiveram retorno positivo: Bollinger 20/2 (+4,89\%, Sharpe 0,58) e Multiagentes v3 (+0,07\%, Sharpe 0,09).` · L58: `Bollinger 20/2 manteve em média 49,06\% do patrimônio em caixa e SMA 50/200 encerrou com 39,29\%... A v1 manteve caixa final de 15,27\%... a v2 elevou o caixa final para 45,86\%...` · L152: `cerca de R\$ 827,34` · L195: `cerca de 4.703 chamadas e US\$ 8,63`.  
  **Problema:**
  1. Em `06:52`, agrupar `+4,89%` (`+R$ 4.888,97`) e `+0,07%` (`+R$ 68,54` sobre R\$ 100 mil, isto é, virtual estabilidade / *break-even*) sob o rótulo `"Apenas duas carteiras tiveram retorno positivo"` cria um enquadramento visualmente favorável à v3.
  2. Em `06:58`, a mesma frase mistura **caixa médio** de `Bollinger 20/2` (`49,06%`, cujo caixa final foi `58,56%`) com **caixa final** de `SMA 50/200` (`39,29%`, cujo caixa médio foi `31,39%`) e de `v2` (`45,86%`, cujo caixa médio foi `24,69%`), comparando grandezas distintas.
  3. Em `06:152` e `06:195`, usa-se `"cerca de"` antes de números exatos até os centavos (`R$ 827,34`, `4.703 chamadas`, `US$ 8,63`), e a Seção 6.7 informa apenas o custo das chamadas com resposta válida (`US$ 6,17` na v1, `US$ 8,63` na v2, `US$ 8,54` na v3), sem mencionar a exposição orçamentária total contabilizada pelo `CallBank` incluindo as reservas de incerteza das falhas HTTP 503 (`US$ 8,11` na v1 e `US$ 10,03` na v2, conforme `comparacao_v1_v2_v3.json`).  
  **Correção proposta:** Em `06:52`, escrever `Apenas a referência Bollinger 20/2 obteve ganho expressivo no período (+4,89\%, Sharpe 0,58), enquanto a carteira Multiagentes v3 encerrou próxima da estabilidade (+0,07\%, equivalentes a +R\$~68,54, Sharpe 0,09) e as demais seis carteiras acumularam perdas entre -3,97\% e -17,82\%.`; em `06:58`, reportar sempre o par **(caixa médio / caixa final)** para cada carteira; em `06:152` e `06:195`, remover `"cerca de"` e informar entre parênteses a exposição orçamentária total com reservas de incerteza.

- **C6-09** · **Severidade:** Baixo  
  **Local:** `chapters/06-resultados.tex:36, 126, 171, 175, 184` (p. 49, 56, 60–61)  
  **Problema:** Rodapé das Tabelas 6.1 e 6.5 com caminho interno `tcc2/figures/replay-series.csv` e `auditoria-v3/comparacao_v1_v2_v3.json` (`P-08`); quebras de linha entre `R$` e o número (`P-05`); e em `06:184`, a expressão `"recuperou 17,89 p.p. acima da linha de base"` é ambígua (parece referir-se ao capital inicial de R\$ 100 mil ou a *Buy & Hold*, quando se refere à linha de base interna **v1**).  
  **Correção proposta:** Substituir por `"acima da configuração inicial v1 (+17,89 p.p.) e acima da referência Buy & Hold (+11,28 p.p.)"`, usar `R\$~` e padronizar `Fonte: Elaborado pelos autores.`.

*Balanço micro do Cap. 6:* **55 parágrafos/itens revisados** (51 parágrafos em prosa + 4 itens de lista); **23 apresentaram problemas**.

---

### Capítulo 7 — Conclusão (`chapters/07-conclusao.tex`; p. 64–68 / PDF p. 76–80)

- **C7-01** · **Severidade:** Crítico  
  **Local:** `chapters/07-conclusao.tex:20, 22, 24, 30` (p. 64–65 / PDF p. 76–77)  
  **Problema:** 4 comandos `\paragraph{}` na Seção 7.2 que geram cabeçalhos `7.2.0.0.1` a `7.2.0.0.4` (`P-02`).  
  **Correção proposta:** Converter em `\subsection{}` (`7.2.1` a `7.2.4`) ou `\noindent\textbf{...}`.

- **C7-02** · **Severidade:** Crítico  
  **Local:** `chapters/07-conclusao.tex:47` (p. 67 / PDF p. 79)  
  **Trecho:** `Essa ameaça é assimétrica: como eventual memorização tenderia a favorecer os agentes, ela não invalida os resultados nulos ou negativos reportados para H2, mas impediria tratar um eventual resultado positivo em replay retrospectivo como evidência confirmatória.`  
  **Problema:** Repete a tese de viés estritamente unidirecional da contaminação (`C5-03`), contradizendo \citet{Glasserman2023} citados na página 14.  
  **Correção proposta:** Alinhar com a redação corrigida em `C5-03` (destacando o bloqueio de identidade nos analistas, a restrição do risco ao `portfolio_manager` e a possibilidade de efeito de distração em *large caps*).

- **C7-03** · **Severidade:** Alto  
  **Local:** `chapters/07-conclusao.tex:8-15` (p. 64 / PDF p. 76)  
  **Trecho:** Dois parágrafos de síntese geral na Seção 7.1 (`Síntese do Trabalho Realizado`).  
  **Problema:** O guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`, Cap. 5, p. 13 / PDF p. 26) exige que a Conclusão retome cada objetivo específico da Introdução para demonstrar seu cumprimento. A Seção 7.1 faz um resumo corrido sem fechar explicitamente os seis objetivos específicos da Seção 1.4.2 e menciona o acompanhamento prospectivo (Objetivo 6) apenas como mecanismo de software, **sem reportar o resultado empírico preliminar dos 23 pregões reais** da Seção 6.8 (`-23,94%` para Multiagentes v1 contra `-17,61%` para Buy & Hold).  
  **Correção proposta:** Estruturar a Seção 7.1 (ou uma lista numerada concisa dentro dela) espelhando os seis objetivos específicos da Seção 1.4.2 e incluindo o resultado dos 23 pregões prospectivos da v1 no fechamento do Objetivo 6.

- **C7-04** · **Severidade:** Médio  
  **Local:** `chapters/07-conclusao.tex:18, 30, 36` (p. 64–66 / PDF p. 76–78)  
  **Trecho:** L18: `com métrica primária e regra de decisão fixadas antes do replay` · L30: `reduziu a unanimidade de 83,01\% para 4,03\%... e elevou o patrimônio final para R\$ 100.068,54 (+0,07\%), uma diferença de R\$ 17.888,65 sobre a v1` · L36: `moldou o resultado da v3 tanto quanto os sinais gerados pelo modelo de linguagem`.  
  **Problema:**
  1. Em `07:18`, dizer que a métrica primária e a regra de decisão foram *"fixadas antes do replay"* omite a ressalva honesta feita no Cap. 5 (`05:75` e `05:178`) de que a escolha de `SMA 50/200` $\times$ `Equal Weight 63d` para H1 e a família de cinco comparações com ajuste de Holm-Bonferroni para H2 foram formalizadas durante a consolidação metodológica do TCC 2, após a execução das campanhas.
  2. Em `07:30`, ao responder à questão secundária de engenharia (efeito da especialização de papéis e do compilador), o texto apoia a conclusão simultaneamente na mudança comportamental do comitê e no ganho de `R$ 17.888,65` de patrimônio final, sem ressalvar que a trajetória financeira de cada versão decorre de uma única realização estocástica ($R=1$ a temperatura `1,0`) calibrada *in-sample*.
  3. Em `07:36`, repete a afirmação não medida `"tanto quanto os sinais"` (`C6-04`).  
  **Correção proposta:** Em `07:18`, acrescentar `(com o par primário de H1 e o ajuste de multiplicidade de H2 formalizados na etapa de análise estatística, conforme Seções 5.3 e 5.6.2)`; em `07:30`, ancorar a resposta primariamente nos **indicadores estruturais determinísticos do comitê** (queda da unanimidade de 83,01% para 4,03%, inversão do perfil de RSI nas operações e 52 vetos do compilador), registrando que a diferença patrimonial de R\$ 17.888,65 em uma única campanha ($R=1$) é descritiva; em `07:36`, aplicar a mesma correção de `C6-04`.

- **C7-05** · **Severidade:** Médio  
  **Local:** `chapters/07-conclusao.tex:22, 44-54, 57-68` (p. 65, 67–68 / PDF p. 77, 79–80)  
  **Problema:**
  1. Em `07:22`, lê-se `"entre as seis carteiras avaliadas na campanha pré-especificada"` (v1 + 5 referências = 6), mas o Cap. 6 refere-se sistematicamente às `"oito carteiras"` da Tabela 6.2. Especificar `"entre as seis carteiras da comparação pré-especificada (v1 e as cinco referências)"`.
  2. Na Seção 7.4 (`07:44-54`), o texto repete quase palavra por palavra a Seção 5.8, mas deixa de mencionar a direção do viés de caixa não remunerado/CDI sobre H1 e H2 (`C5-04`), a assimetria tributária (IR sobre JCP sem IR sobre ganho de capital), o mercado fracionário da B3 nas vendas residuais da v3 (`C6-06`), a seleção retrospectiva das 5 ações durante a janela (`C5-05`) e o fato de que o ciclo diário prospectivo rodou a v1 (`C4-06`).
  3. Na Seção 7.5 (`07:57-68`, Trabalhos Futuros), duas extensões científicas fundamentais derivadas diretamente das limitações deste TCC devem ser incluídas: (a) **quantificação do horizonte amostral necessário para potência estatística** — como $\mathrm{EP}(\hat{\Delta}) \approx \sqrt{252 \cdot 2(1-\rho)/n}$, sob correlação diária moderada ($\rho \approx 0{,}3\text{--}0{,}5$) uma janela de $n = 153$ pregões produz erro-padrão de $\sim 1{,}3\text{--}1{,}6$ unidades de Sharpe anualizado, sendo necessários **3 a 5 anos ($n \approx 750\text{--}1.260$ pregões)** para detectar diferenças reais de Sharpe da ordem de $0{,}5\text{--}0{,}8$ com poder de 80%; e (b) **ablação fatorial com um comitê determinístico de 5 lentes sem LLM**, aplicando exatamente os mesmos limiares das 5 lentes da v3 e o mesmo compilador de ordens em Python puro para isolar o valor marginal real do modelo de linguagem.

*Balanço micro do Cap. 7:* **30 parágrafos/itens revisados** (25 parágrafos em prosa + 5 itens de lista); **11 apresentaram problemas**.

---

### Síntese quantitativa da revisão micro (Eixo 2)

| Capítulo | Parágrafos / itens revisados | Com problemas identificados | Taxa de incidência |
| :--- | :---: | :---: | :---: |
| **Cap. 0 — Pré-textuais (Capa, Resumo, Abstract)** | 4 | 4 | 100,0% |
| **Cap. 1 — Introdução** | 25 | 14 | 56,0% |
| **Cap. 2 — Fundamentação Teórica** | 37 | 23 | 62,2% |
| **Cap. 3 — Trabalhos Relacionados** | 25 | 11 | 44,0% |
| **Cap. 4 — Arquitetura do Sistema** | 70 | 29 | 41,4% |
| **Cap. 5 — Metodologia Experimental** | 64 | 24 | 37,5% |
| **Cap. 6 — Resultados e Discussão** | 55 | 23 | 41,8% |
| **Cap. 7 — Conclusão** | 30 | 11 | 36,7% |
| **Total da monografia** | **310** | **139** | **44,8%** |

---

## 5. Figuras e tabelas

### 5.1 Diagnóstico completo das figuras e tabelas existentes

Hoje a monografia possui **6 figuras** (3 diagramas TikZ no Cap. 4 e 3 gráficos `pgfplots` no Cap. 6) e **11 tabelas** (1 no Cap. 3, 3 no Cap. 4, 2 no Cap. 5 e 5 no Cap. 6). Os Capítulos **1, 2, 3, 5 e 7 não possuem nenhuma figura**.

| Elemento | Arquivo / Local (pág. / PDF) | Citado antes? | Interpretado no texto? | Legenda autoexplicativa? | `Fonte:` abaixo (ABNT)? | Legível no PDF e em P&B? | Problemas visuais / técnicos identificados |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Figura 4.1** | `04-arquitetura.tex:48-70` (p. 20 / PDF p. 32) | Sim (L46) | Parcial | Sim | **Não** | Sim (`black!15`) | Diagrama mostra apenas o pipeline legado (`Yahoo -> Parquet + SHA-256 -> CausalMarketWindow`), omitindo a divisão `B3 COTAHIST RAW` vs `Yahoo ajustado` do replay multiativos (L72–79). |
| **Figura 4.2** | `04-arquitetura.tex:115-136` (p. 23 / PDF p. 35) | Sim (L105) | Sim | Sim | **Não** | Sim (`black!15`) | O rótulo inclinado `\texttt{veredito = APROVADO}` **colide com a borda** da caixa `portfolio_manager`; a seta `caso contrário` não indica que a decisão é `MANTER`. |
| **Figura 4.3** | `04-arquitetura.tex:170-204` (p. 26 / PDF p. 38) | Sim (L142) | Sim | Sim | **Não** | **Fraco em P&B** | Preenchimento `fill=black!6` é quase branco em impressão P&B (usar `black!12` ou `black!15`); primeira caixa quebra palavra mal (`5 anal-istas`). |
| **Figura 6.1** | `figures/replay-patrimonio.tex` (p. 50 / PDF p. 62) | Sim, mas **após Fig. 6.2** | **Não** (só menção em L44) | Parcial (falta capital inicial e $N=153$) | **Não** | **Parcial** (8 curvas P&B) | Citada em `06:44` depois da Fig. 6.2 (`06:39`); eixo X diz `Pregão (2026)` para meses `abr..nov`; `Equal Weight 63d` e `Mínima Variância` confundem-se em P&B; texto não analisa os 3 regimes da curva. |
| **Figura 6.2** | `figures/replay-drawdown.tex` (p. 51 / PDF p. 63) | Sim (`06:39`, antes da Fig. 6.1) | Sim (`06:55`) | Parcial (`Drawdown` sem itálico) | **Não** | **Parcial** (8 curvas P&B) | Citada antes da Fig. 6.1; eixo X diz `Pregão (2026)`; `Drawdown` sem itálico no eixo Y e na legenda; sobreposição de curvas intermediárias em P&B. |
| **Figura 6.3** | `figures/replay-caixa.tex` (p. 59 / PDF p. 71) | Sim (`06:58` e `06:169`) | Sim (`06:58, 169`) | Sim | **Não** | Sim (4 curvas bem distintas) | Eixo X diz `Pregão (2026)` para rótulos de meses (`abr..nov`); sem indicação de `Fonte:`. |
| **Tabela 3.1** | `03-relacionados.tex:62-90` (p. 17 / PDF p. 29) | Sim (L60) | Sim (L92–100) | Sim | **Não** | **Falha grave** | **Cabeçalhos colidem no PDF:** imprime `MultiagenteCustos` (`+9,36 pt`) e `RastreabilidadeReferências` (`+21,51 pt`); flutua para o meio da Seção 3.8. |
| **Tabela 4.1** | `04-arquitetura.tex:15-40` (p. 19 / PDF p. 31) | Sim (L13) | Sim | Sim | **Não** | Sim | Sem `Fonte:`; excesso de caminhos de arquivos que podem ser resumidos por pacote/subsistema. |
| **Tabela 4.2** | `04-arquitetura.tex:268-303` (p. 30 / PDF p. 42) | Sim (L266) | Sim | Sim | **Não** | Sim | Sem `Fonte:`; colunas claras e bem dimensionadas. |
| **Tabela 4.3** | `04-arquitetura.tex:311-333` (p. 32 / PDF p. 44) | Sim (L309) | Parcial | Parcial | **Não** | Sim | Coluna `Valor` **sem unidades** (`30`, `50`, `2`, `10,00`, `40`, `260`); tabela de configuração de ambiente que pertence ao **Apêndice A**. |
| **Tabela 5.1** | `05-metodologia.tex:63-73` (p. 38 / PDF p. 50) | Sim (L52) | Sim | Sim | **Não** | **Estoura margem** | `Overfull \hbox` de **`+8,17 pt`** à direita; sem `Fonte:`. |
| **Tabela 5.2** | `05-metodologia.tex:95-106` (p. 41 / PDF p. 53) | Sim (L86) | Sim | Sim | **Não** | **Estoura margem** | `Overfull \hbox` de **`+1,86 pt`**; sem `Fonte:`; flutua para dentro da Seção 5.5 cortando o texto de Mínima Variância. |
| **Tabela 6.1** | `06-resultados.tex:25-36` (p. 49 / PDF p. 61) | Sim (L21) | Sim | Sim | Parcial (caminho interno) | **Estoura margem** | `Overfull \hbox` de **`+25,55 pt`** à direita; nota cita caminho interno `tcc2/figures/replay-series.csv`; poderia ser substituída por uma única frase no texto (já que todos os desvios são `0,00`). |
| **Tabela 6.2** | `tabelas/metricas-replay.tex:1-28` (p. 50 / PDF p. 62) | Sim (`06:39`) | Sim (`06:52-58`) | Parcial (`MDD` não definido antes) | Parcial (sem `Fonte:`) | **Fonte ~7 pt** | `\resizebox{\textwidth}{!}` encolhe a fonte para ~7 pt; cabeçalhos sem `\textbf{}`; `MDD` usado antes da definição na p. 52. |
| **Tabela 6.3** | `tabelas/metricas-replay.tex:30-55` (p. 50 / PDF p. 62) | Sim (`06:39`) | Sim (`06:59`) | Sim | Parcial (sem `Fonte:`) | **Fonte ~7,5 pt** | `\resizebox{\textwidth}{!}` desnecessário (a tabela tem apenas 8 colunas curtas e cabe em tamanho normal); cabeçalhos sem `\textbf{}`. |
| **Tabela 6.4** | `tabelas/bootstrap-replay.tex` (p. 53 / PDF p. 65) | Sim (`06:67`) | Sim (`06:71-106`) | Parcial (`MA` não definido) | Parcial (sem `Fonte:`) | **Fonte ~7,5 pt** | Sigla `MA v1..v3` ambígua; 9 de 16 linhas têm diferença de `0,01` entre $\Delta$ e a subtração dos Sharpes arredondados da Tabela 6.2 sem nota explicativa; cabeçalhos sem `\textbf{}`. |
| **Tabela 6.5** | `06-resultados.tex:113-128` (p. 56 / PDF p. 68) | Sim (`06:111`) | Sim (`06:130-197`) | Sim | Parcial (caminho interno) | Sim | Nota cita caminho interno `auditoria-v3/comparacao_v1_v2_v3.json` em vez de `Fonte: Elaborado pelos autores.`. |

### 5.2 Arquivos órfãos no repositório `tcc2/`

Três arquivos de imagem versionados em `tcc2/` não são referenciados por nenhum `.tex`:
1. `tcc2/figures/figure.png`: placeholder genérico herdado do template (`eic-bcc-tcc`), nunca usado — **remover ou ignorar na limpeza**.
2. `tcc2/images/pipeline-etl.png`: versão raster antiga da Figura 4.1 (que hoje é gerada nativamente em TikZ dentro de `04-arquitetura.tex:48-70`).
3. `tcc2/images/grafo-langgraph.png`: versão raster antiga da Figura 4.2 (que hoje é gerada nativamente em TikZ dentro de `04-arquitetura.tex:115-136`).

*(Nota: em `docs/screenshots/preview-desktop.jpg` e `preview-mobile.jpg` há capturas reais da interface construída do projeto que podem ser aproveitadas se os autores desejarem ilustrar a interface de acompanhamento no Apêndice A ou na Seção 4.11).*

### 5.3 Propostas concretas de novas figuras e ajustes de tabelas

Para eliminar a aridez visual dos Capítulos 5 e 6 e comunicar imediatamente o desenho experimental e o mecanismo comportamental dos agentes, recomendam-se **três novas figuras** (todas geráveis em TikZ/`pgfplots` a partir dos dados já versionados no repositório):

1. **Nova Figura 5.1 (Capítulo 5, Seção 5.2/5.4) — *Linha do tempo experimental, corte de conhecimento e desenho pareado das campanhas***  
   - **Objetivo:** Permitir que a banca visualize em 5 segundos a relação temporal entre a janela de aquecimento causal (260 pregões, desde março de 2025), o corte de conhecimento declarado do modelo `gemini-3.8-flash` (março de 2026), a janela do replay retrospectivo (06/04/2026 a 13/11/2026, $N = 153$ pregões, dentro da qual ocorrem a execução pré-especificada v1, as iterações exploratórias v2 e v3 e as 5 carteiras de referência sob paridade exata) e a janela de acompanhamento diário prospectivo (14/10/2026 a 16/11/2026, 23 pregões).  
   - **Conteúdo:** Diagrama horizontal em TikZ com duas faixas: (a) eixo cronológico superior indicando as três janelas (`Aquecimento: 260 pregões`, `Replay: 06/04 a 13/11/2026, 153 pregões`, `Prospectivo: 14/10 a 16/11/2026, 23 pregões`) e o marco vertical `Corte declarado do LLM (mar/2026)`; (b) bloco inferior mostrando o acoplamento diário no pregão $t$ (`Janela causal até t-1` $\to$ `8 features técnicas` $\to$ `5 Referências determinísticas [fixas]` vs `Multiagentes v1 [confirmatória] / v2, v3 [exploratórias]` $\to$ `Bootstrap estacionário pareado B=10.000, l=10`).  
   - **Fonte dos dados:** `chapters/05-metodologia.tex` (Seções 5.2–5.7) e `tcc2/evidence/04-replay-abril-novembro/relatorios/evolucao_replay_v1_v2_v3_tcc.md`.

2. **Nova Figura 6.4 (Capítulo 6, Seção 6.6) — *Distribuição de consenso do comitê e perfil de RSI nas operações executadas entre v1, v2 e v3***  
   - **Objetivo:** Transformar a principal descoberta de engenharia de agentes do TCC (Seção 6.6: a quebra da unanimidade artificial do comitê e a inversão do comportamento pró-cíclico de comprar topo e vender fundo) em evidência visual direta.  
   - **Conteúdo:** Gráfico `pgfplots` em dois painéis lado a lado:  
     - *Painel (a):* Barras empilhadas (ou agrupadas) da distribuição dos 765 pareceres do comitê por campanha nas quatro faixas reportadas na Tabela 6.5: unanimidade em um único voto (`83,01%` na v1 $\to$ `87,32%` na v2 $\to$ `4,03%` na v3), compras fortes `score >= +0,60` (`80,13%` $\to$ `33,20%` $\to$ `1,08%`), faixa moderada `(-0,60, +0,60)` (`14,64%` $\to$ `12,16%` $\to$ `98,92%`) e vendas fortes `score <= -0,60` (`5,23%` $\to$ `54,64%` $\to$ `0,00%`).  
     - *Painel (b):* Comparação do RSI médio (e faixa mínima–máxima) nas compras e vendas executadas na v2 (`compras: RSI médio 55,6 [32,7–82,5], 9 compras com RSI > 70`; `vendas: RSI médio 35,3 [6,1–78,3], 13 vendas com RSI < 30`) versus v3 (`compras: RSI médio 38,5 [14,2–59,3], 0 compras com RSI > 70`; `vendas: RSI médio 63,5 [31,3–91,8], 0 vendas com RSI < 30`).  
   - **Fonte dos dados:** `tcc2/evidence/04-replay-abril-novembro/dados/auditoria-v3/comparacao_v1_v2_v3.json` e `tcc2/evidence/04-replay-abril-novembro/relatorios/evolucao_replay_v1_v2_v3_tcc.md` (Seções 4.2, 5.2 e 6.2).

3. **Nova Figura 6.5 (Capítulo 6, Seção 6.8) — *Evolução diária do patrimônio líquido na janela prospectiva (14/10/2026 a 16/11/2026, 23 pregões)***  
   - **Objetivo:** Dar representação visual ao Objetivo Específico 6 (acompanhamento diário prospectivo), mostrando as seis carteiras monitoradas (`Bollinger 20/2`, `SMA 50/200`, `Buy & Hold`, `Equal Weight`, `Mínima Variância` e `Multiagentes v1`) ao longo dos 23 pregões reais.  
   - **Conteúdo:** Gráfico de linhas `pgfplots` no mesmo estilo da Figura 6.1, plotando as seis séries de `equity_diario.csv` de `14/10/2026` a `16/11/2026`.  
   - **Fonte dos dados:** `tcc2/evidence/06-operacao-diaria/serie-diaria-20261117/equity_diario.csv`.

4. **Conversões entre tabela e texto recomendadas:**
   - **Tabela 6.1 (`06-resultados.tex:25-36`):** como todas as diferenças máximas das cinco referências entre v1, v2 e v3 são identicamente **`0,00`** (paridade bit a bit), a Tabela 6.1 pode ou ter suas larguras corrigidas (`C6-03`), ou ser substituída por duas frases no parágrafo `06:21` (economizando meia página e eliminando um `Overfull \hbox` de `25,55 pt`).
   - **Seção 5.8 (`05-metodologia.tex:201-214`):** acrescentar ao final da seção uma **Tabela 5.3 — Síntese das ameaças à validade, mecanismo de mitigação e direção esperada do viés sobre H1 e H2**, consolidando as 6 ameaças hoje descritas apenas em prosa.

---

## 6. Referências (`tcc2/references.bib` e saída `apalike.bst`)

### 6.1 Cruzamento entre citações no texto e `references.bib`

- **Entradas em `tcc2/references.bib`:** **61 entradas** (`main.aux` contém 61 `\bibcite`).
- **Citações indefinidas ou entradas órfãs hoje:** **0** (todas as 61 entradas são citadas no texto e todas as citações do texto existem no `.bib`; `main.log` e `main.blg` não acusam `Citation undefined`).
- **Atenção ao editar o Capítulo 2:** as entradas `FamaFrench1993` e `FamaFrench2015` são citadas **exclusivamente** na Seção 2.4 (`02-fundamentacao.tex:82-89`). Caso os autores removam a Seção 2.4 (conforme recomendado em `C2-03`), devem remover também `FamaFrench1993` e `FamaFrench2015` de `references.bib` para não criar duas entradas órfãs.

### 6.2 Problemas em entradas de `tcc2/references.bib`

#### A. 12 preprints arXiv sem identificador visível na lista de referências (Crítico)

O estilo `apalike.bst` ignora os campos não-padrão `eprint`, `archiveprefix` e `primaryclass`, e nos tipos `@article` também ignora `url` e `doi`. Como consequência, **12 referências fundamentais de LLMs e RL aparecem nas páginas 69–74 do PDF apenas com `journal = {arXiv preprint}`, sem número arXiv, sem DOI e sem URL** (impossibilitando a localização bibliográfica segundo a ABNT NBR 6023):

| Chave BibTeX | Linha no `.bib` | Como sai hoje no PDF (`main.bbl`) | Correção no campo `journal` de `references.bib` |
| :--- | :---: | :--- | :--- |
| `FinRL2020` | L149 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2011.09607}` |
| `Glasserman2023` | L107 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2309.17322}` (ou SSRN 4588952) |
| `Jiang2017` | L129 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:1706.10059}` |
| `Li2023` | L169 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2310.10638}` |
| `LopezLira2023` | L191 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2304.07619}` |
| `Schulman2017` | L241 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:1707.06347}` |
| `Wu2023` | L297 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2303.17564}` |
| `Xia2026` | L327 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2602.23330}` |
| `TradingAgents2024` | L448 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2412.20138}` |
| `FinBen2024` | L475 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2402.12659}` (ou `booktitle = {Advances in Neural Information Processing Systems (NeurIPS)}`) |
| `Xing2024` | L483 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2407.06567}` |
| `StockAgent2024` | L510 | *arXiv preprint*. | `journal = {arXiv preprint arXiv:2407.18957}` |

*(Observação elogiosa: as entradas `FinCoT2025`, `FinCon2024`, `AlphaAgents2025`, `TradeTrap2025`, `PrimoGPT2025`, `LiveTradeBench2025`, `MacroHFT2024`, `LookAheadBench2026`, `FinPos2025`, `FINSABER2025`, `EarnMore2024` e `MDGNN2024` já usam o formato correto `journal = {arXiv preprint arXiv:XXXX.XXXXX}` — basta padronizar as 12 acima da mesma maneira).*

#### B. 5 artigos de conferência `@inproceedings` sem páginas, editora ou identificador na saída

Em `apalike.bst`, entradas `@inproceedings` sem `pages` nem `publisher` imprimem apenas `In *Booktitle*.` (e nos casos em que o autor colocou `note` sem `pages`, o `apalike.bst` gera a pontuação defeituosa `., arXiv:XXXX.` com ponto antes da vírgula, como ocorre em `FinCon2024` e `MacroHFT2024`):
- `Du2024` (L64), `Golchin2024` (L117), `Li2024` (L179), `Smit2024` (L251) e `Wang2023` (L287): incluir o identificador `arXiv` ou páginas no campo `booktitle` (ex.: `booktitle = {Proceedings of the Twelfth International Conference on Learning Representations (ICLR), arXiv:2308.07107}` para `Golchin2024` e `arXiv:2203.11171` para `Wang2023`), e remover o campo `note = {arXiv:...}` de `FinCon2024` (L459) e `MacroHFT2024` (L520) movendo o identificador para `booktitle` (eliminando o `.,` no PDF).

#### C. 17 erros de capitalização em títulos (downcase automático do BibTeX)

O estilo `apalike.bst` converte títulos de `@article` e `@inproceedings` para minúsculas, exceto o que estiver protegido entre chaves `{...}`. Hoje, **16 entradas** saem no PDF com siglas, nomes próprios ou a primeira palavra após dois-pontos em minúsculas:

1. `Barberis2003` (L15): `A survey of behavioral finance` (inconsistente com os demais capítulos de *Handbook* em *Title Case*).
2. `DeMiguel2009` (L53): `1/N` $\to$ sai **`1/n`** no PDF (proteger `{1/N}`).
3. `Du2024` (L66): `: Multi-agent` $\to$ sai **`: multi-agent`** (proteger `{Multi-Agent}`).
4. `Fama1991` (L83): `: II` $\to$ sai **`: ii`** (proteger `{II}`).
5. `FinRL2020` (L148): `FinRL: A deep` $\to$ sai **`Finrl: a deep`** (proteger `{FinRL}: {A}`).
6. `Golchin2024` (L119): `LLMs` $\to$ sai **`llms`** (proteger `{LLMs}`).
7. `Hendershott2011` (L121): `Does algorithmic trading improve liquidity?` (padronizar ou manter consistente).
8. `Jegadeesh1993` (L139): `: Implications` $\to$ sai **`: implications`** (proteger `{Implications}`).
9. `Kahneman1979` (L159): `: An analysis` $\to$ sai **`: an analysis`** (proteger `{An}`).
10. `Li2023` (L171): `TradingGPT: Multi-agent` $\to$ sai **`Tradinggpt: multi-agent`** (proteger `{TradingGPT}: {Multi-Agent}`).
11. `Li2024` (L181): `: A survey` $\to$ sai **`: a survey`** (proteger `{A}`).
12. `Schulman2017` (L243): `Proximal policy optimization algorithms`.
13. `Sharpe1966` (L263): `Mutual fund performance`.
14. `Smit2024` (L253): `LLMs` e `MARL` $\to$ saem **`llms`** e **`marl`** (proteger `{LLMs}` e `{MARL}`).
15. `Sortino1994` (L271): ` downside risk` (OK, mas padronizar).
16. `Wang2023` (L289): `CoT` $\to$ sai **`cot`** (proteger `{CoT}`).
17. `Wu2023` (L299): `BloombergGPT: A large` $\to$ sai **`Bloomberggpt: a large`** (proteger `{BloombergGPT}: {A}`).

#### D. Erros em autores, editores, edição e aviso do BibTeX

1. **`FinMem2024` (L467 — aviso em `main.blg`):** `Warning--there's a number but no volume in FinMem2024`. A entrada `@inproceedings` possui `number = {1}` sem `volume`, gerando no PDF `In *Proceedings of the AAAI Symposium Series*, number 1.` — **remover `number = {1}`**.
2. **`Clarke2006` (L42):** `author = {Clarke, Roger and De Silva, Harindra and Thorley, Steven}` — o segundo autor está grafado com `De` maiúsculo (`De Silva`), mas no texto (`02:100`) aparece `de Silva`. Padronizar `de Silva, Harindra`.
3. **`Bailey2017` (L4):** `author = {Bailey, David H. and Borwein, Jonathan and Lopez de Prado, Marcos and Zhu, Qiji Jim}` — falta o acento em `L{\'o}pez de Prado, Marcos`, que está acentuado em `LopezDePrado2018` (L199). Isso faz o mesmo autor aparecer com duas grafias distintas na bibliografia (`Lopez de Prado` e `López de Prado`).
4. **`Thaler1993` (L278):** `Thaler, Richard H.` é o **organizador (*editor*)** da coletânea *Advances in Behavioral Finance*, mas está cadastrado no campo `author` em vez de `editor = {Thaler, Richard H.}`.
5. **`SuttonBarto2018` (L435):** `edition = {2}` faz o `apalike.bst` imprimir **`2 edition`** na página 73 do PDF (em inglês o correto para `apalike.bst` é `edition = {2nd}`, que imprime `2nd edition`, exatamente como já está feito em `GrinoldKahn2000` e `Tsay2010` com `3rd`).
6. **Sete livros (`@book`) sem campo `address` (cidade da editora):** `GrinoldKahn2000` (L420), `Tsay2010` (L428), `SuttonBarto2018` (L435), `Wooldridge2009` (L442), `Bodie2014` (L24), `Hull2018` (L130) e `Thaler1993` (L278). Embora o `apalike.bst` não exija `address`, incluí-lo melhora a completude bibliográfica (ex.: `New York, NY`, `Hoboken, NJ`, `Cambridge, MA`, `Chichester`).

### 6.3 Compatibilidade `apalike.bst` vs ABNT NBR 10520 / NBR 6023

- **Diagnóstico:** Há uma divergência institucional conhecida no próprio material do CEFET/RJ: enquanto o texto do guia `Trabalho de Conclusao EIC BCC.pdf` (Seção 1.1, p. 2 / PDF p. 15) menciona *"seguir o modelo ABNT para citações e lista de referências"*, a classe oficial obrigatória `tcc2/eic-bcc-tcc.cls` (linha 87) carrega `\usepackage{natbib}` e o arquivo-modelo `tcc2/referencia/main.tex` (linha 188) define `\bibliographystyle{apalike}`.
- **Diferenças geradas pelo template:** (1) nas citações no texto, `natbib` + `apalike` imprime colchetes e conjunção em inglês (`[Clarke et al., 2006]`, `[Fama and French, 1993]`), enquanto a ABNT NBR 10520 usa parênteses, caixa alta dentro dos parênteses e ponto e vírgula (`(CLARKE et al., 2006)`, `(FAMA; FRENCH, 1993)`); (2) na lista final, `apalike.bst` produz rótulos `[Author, YYYY]` e termos em inglês (`In`, `volume`, `pages`, `edition`), enquanto a ABNT NBR 6023 dispensa o rótulo entre colchetes e usa caixa alta nos sobrenomes.
- **Recomendação:** Conforme as regras desta revisão, **mantenha `eic-bcc-tcc.cls` e `apalike.bst` como autoridade do template**, sem tentar substituir o estilo bibliográfico por `abntex2cite` (o que quebraria a classe institucional). Basta corrigir os 12 `arXiv`, os 5 `@inproceedings`, as 17 capitalizações e os 5 campos de autor/edição listados na Seção 6.2 para que a saída de `apalike.bst` fique impecável.

---

## 7. Conformidade CEFET/RJ / ABNT

A verificação abaixo toma `tcc2/eic-bcc-tcc.cls` e o guia oficial do curso (`tcc2/source/tcc1/docs/Trabalho de Conclusao EIC BCC.pdf`) como referência institucional.

| Item de verificação | Status | Diagnóstico e localização |
| :--- | :---: | :--- |
| **1. Ordem dos elementos pré-textuais** (Capa, Folha de Rosto, Dedicatória, Agradecimentos, Resumo, Abstract, Listas de Figuras/Tabelas/Acrônimos, Sumário) | **OK** | Ordem gerada por `eic-bcc-tcc.cls` e `main.tex:126-176` está completa e fiel a `referencia/main.tex`. *(Obs.: a classe `eic-bcc-tcc.cls` define a macro `\approvalsheet`, mas não a invoca no `\frontmatter` nem em `referencia/main.tex`; verificar com a coordenação se a folha de aprovação é anexada apenas na versão final pós-defesa).* |
| **2. Título da capa/folha de rosto e pontuação** | **Falha** | Em `main.tex:10`, `\title{...Multiagentes.}` termina com ponto final, gerando ponto duplo `Multiagentes..` na ficha catalográfica (PDF p. 3) (`C0-01`). |
| **3. Resumo em parágrafo único e dentro do limite de palavras (ABNT NBR 6028: 150–500 palavras)** | **OK** | Parágrafo único com **235 palavras**, contendo contexto, objetivo, método, resultados quantitativos e conclusão. (Requer apenas o polimento de precisão apontado em `C0-03`). |
| **4. Abstract fiel ao Resumo** | **OK** | Parágrafo único com **227 palavras**, fiel ao resumo em português. (Corrigir apenas `Bollinger 20/2 (+4.89%)` sem substantivo em `main.tex:151`, ver `C0-04`). |
| **5. Palavras-chave e Keywords no formato do template** | **Falha** | `main.tex:20-31` usa vírgula final (gerando `.,`) e caixa minúscula nas iniciais; o template `referencia/main.tex:20-31` usa Inicial Maiúscula sem pontuação nos itens (`C0-02`). |
| **6. Sumário, Lista de Figuras e Lista de Tabelas fiéis ao corpo** | **OK** | Numeração e páginas do Sumário (PDF p. 11–12), da Lista de Figuras (PDF p. 7, 6 figuras) e da Lista de Tabelas (PDF p. 8, 11 tabelas) conferem exatamente com o corpo do documento. |
| **7. Lista de Acrônimos completa e consistente com o texto** | **Falha** | Declara `CAPM` e `APT` em `main.tex:38-39` sem uso no corpo; usa `\gls{amh}`, `\gls{cot}` e `\gls{mdd}` sem usar as demais 16 siglas de `main.tex`; e deixa siglas do texto (`RAG`, `PBO`, `MAR`, `JCP`, `DQN`, `PPO`, `LSTM`, `CVaR`) fora da lista (`P-03`). |
| **8. Numeração, capitalização e profundidade de seções (ABNT NBR 6024)** | **Falha** | (a) **34 ocorrências de `\paragraph{}`** nos Caps. 5, 6 e 7 produzem numeração de 5 níveis com `.0.0.` (`5.3.0.0.1`) e 13 avisos no `hyperref` (`P-02`); (b) Seção `2.1` possui **subseção única** `2.1.1` sem `2.1.2` (`C2-08`); (c) títulos de `\section` estão em CAIXA ALTA nos Caps. 1–7, mas o título da Seção 3.7 (`QUADRO COMPARATIVO`) contradiz o rótulo `Tabela 3.1` (`C3-07`). |
| **9. Ajustes manuais em `main.tex` (`\usepackage[htt]{hyphenat}`, `\emergencystretch`, `\renewcommand` de títulos)** | **Falha** | `\usepackage[htt]{hyphenat}` (`main.tex:3`) causa 31 avisos de fonte `cmtt` e insere **hifens espúrios após `_`** no PDF (`b3_-calendar.py`, `wallet_-manager_-api.py`), além de não impedir 10 `Overfull \hbox` (`P-01`). Os `\renewcommand` de títulos em português (`main.tex:128-132`) funcionam visualmente bem e corrigem títulos em inglês da classe. |
| **10. Comentários `TODO`, `\warn{}`, `\verify{}`, `\remarks{}` ou texto colorido residual** | **OK no PDF** | Nenhum `\warn`, `\verify`, `\remarks`, `TODO` ou texto vermelho/azul aparece no PDF nem nos `.tex` (a ocorrência da substring `TODO` em `02-fundamentacao.tex:122` faz parte da palavra `METODOLÓGICOS`). Há apenas um comentário HTML `<!-- TODO(redator): ... -->` no artefato auxiliar `tcc2/agent-reports/METRICAS_REPLAY.md:37`. |
| **11. Ausência de linhas estourando a margem direita, colisões em tabelas e páginas quase vazias** | **Falha** | (a) **Colisão de cabeçalhos** na Tabela 3.1 (PDF p. 29: `MultiagenteCustos`, `RastreabilidadeReferências`); (b) **estouro de margem direita** nas Tabelas 5.1 (`+8,17 pt`), 5.2 (`+1,86 pt`), 6.1 (`+25,55 pt`) e em `\texttt` nas páginas 20 (`+33,49 pt`), 23 (`+11,42 pt`), 30 (`+6,50 pt`) e 41 (`+13,30 pt`); (c) **página 48 (PDF p. 60) com apenas 1 linha viúva** no topo e 95% da página em branco; (d) Tabelas 3.1 e 5.2 flutuando para dentro da seção seguinte. |
| **12. Requisitos estruturais do guia oficial do curso (`Trabalho de Conclusao EIC BCC.pdf`)** | **Falha parcial** | (a) **Cap. 1 (Introdução):** a pergunta de pesquisa não termina com ponto de interrogação (`C1-01`), as hipóteses formais não aparecem na Introdução (`C1-03`) e falta a seção `Organização do Trabalho` ao final do Cap. 1 (`C1-04`); (b) **Cap. 2 (Fundamentação):** há 11 parágrafos com menos de 3 frases (`C2-08`) e faltam figuras/diagramas conceituais; (c) **Cap. 3 (Relacionados):** falta descrever a estrutura da busca bibliográfica (bases, *strings* e critérios de seleção, `C3-02`); (d) **Cap. 7 (Conclusão):** os 6 objetivos específicos não são fechados individualmente na Seção 7.1 (`C7-03`). |

---

## 8. Avisos de compilação (`tcc2/main.log` e `tcc2/main.blg`)

A análise completa de `tcc2/main.log` (gerado por `pdfTeX 3.141592653-2.6-1.40.26`, MiKTeX 24.4, `latexmk`, saída de 86 páginas) e de `tcc2/main.blg` revelou os seguintes avisos relevantes (não há referências cruzadas nem citações indefinidas):

| Categoria / Arquivo e linha | Quant. | Mensagem no log | Causa raiz e impacto no PDF | Como eliminar |
| :--- | :---: | :--- | :--- | :--- |
| **`Overfull \hbox` — Cap. 3 (Tabela 3.1)** (`03-relacionados.tex:69`) | 2 | `Overfull \hbox (9.3579pt too wide) in paragraph at lines 69--69` e `Overfull \hbox (21.51225pt too wide) in paragraph at lines 69--69` | O TeX não hifeniza a primeira palavra de uma célula `p{...}` sem `\hspace{0pt}`: `Multiagente` (em `1.8cm`) e `Rastreabilidade` (em `2.0cm`) invadem as colunas vizinhas na p. 17 (PDF p. 29). | Inserir `\hspace{0pt}` nas colunas `p{...}`, ajustar larguras e usar `Multi\-agente` / `Rastreabi\-lidade` (`C3-01`). |
| **`Overfull \hbox` — Cap. 4 (`\texttt`)** (`04-arquitetura.tex:74, 113, 262`) | 3 | `33.4892pt too wide` (L74), `11.42212pt too wide` (L113), `6.50241pt too wide` (L262) | Caminhos `\texttt{src/backtesting/b3\_calendar.py}`, `\texttt{src/agents/graph.py}:` e `\texttt{/laboratory/replay/v2/}` invadem a margem direita nas p. 20, 23 e 30 (PDF p. 32, 35, 42). | Remover `hyphenat [htt]` e usar `\path{...}` para caminhos (`P-01`, `C4-03`). |
| **`Overfull \hbox` — Cap. 5 (Tabelas 5.1, 5.2 e L113)** (`05-metodologia.tex:72, 105, 113`) | 3 | `8.16672pt too wide` (L72, Tab. 5.1), `1.86066pt too wide` (L105, Tab. 5.2), `13.29712pt too wide` (L113, `--references-only`) | Soma das colunas das Tabelas 5.1 e 5.2 excede `\textwidth`; flag `\texttt{--references-only}` não quebra linha na p. 41 (PDF p. 53). | Reduzir `p{7.8cm}` para `p{7.4cm}` (Tab. 5.1) e `p{4.6cm}` para `p{4.4cm}` (Tab. 5.2); reescrever L113 com `\texttt{-{}-references-only}` (`C5-06`). |
| **`Overfull \hbox` — Cap. 6 (Tabela 6.1)** (`06-resultados.tex:34`) | 1 | `Overfull \hbox (25.55469pt too wide) in paragraph at lines 28--34` | Coluna `p{4.2cm}` somada às 4 colunas anteriores excede `\textwidth` em `25,55 pt` na p. 49 (PDF p. 61). | Reduzir `p{4.2cm}` para `p{3.1cm}` ou substituir a Tabela 6.1 por texto (`C6-03`). |
| **`Overfull \hbox` — Folha de Rosto** (`main.tex:126`) | 1 | `Overfull \hbox (9.16705pt too wide) in paragraph at lines 126--126` | Macro interna `\titlepage` de `eic-bcc-tcc.cls` (caixa do título/preâmbulo da folha de rosto). | Interno à classe institucional `eic-bcc-tcc.cls` (não requer edição da classe). |
| **`Package hyperref Warning: Difference (3) between bookmark levels`** (`05:59, 88, 111, 188, 203`; `06:82, 108, 130, 148, 165, 182, 186`; `07:20`) | 13 | `Difference (3) between bookmark levels is greater than one, level fixed` | Uso de `\paragraph{}` (nível 4) diretamente dentro de `\section{}` (nível 1), pulando `\subsection` e `\subsubsection` e gerando `.0.0.` no PDF. | Substituir todos os 34 `\paragraph{}` por `\subsection{}` ou `\noindent\textbf{...}` (`P-02`). |
| **`LaTeX Font Warning: Font shape OML/cmtt/m/it undefined`** (e `OMS/cmtt/m/n`, `OT1/cmtt/bx/n`) | 31 | `Font shape ... in size <12> not available` / `Some font shapes were not available, defaults substituted` | O pacote `\usepackage[htt]{hyphenat}` tenta consultar variantes matemáticas/negrito da fonte monoespaçada `cmtt`. | Remover `\usepackage[htt]{hyphenat}` de `main.tex:3` (`P-01`). |
| **`Package babel Warning: No hyphenation patterns were preloaded for 'Portuguese'`** | 1 | `No hyphenation patterns were preloaded for the language 'Portuguese' into the format` | O formato local do MiKTeX dos autores não pré-carregou os padrões de hifenização de português no *dump* do formato. Isso degrada a qualidade das quebras silábicas em todo o PDF. | No MiKTeX Console do ambiente de compilação (`Settings -> Formats -> pdflatex -> Build`), habilitar o idioma `portuguese` e reconstruir o formato. |
| **`Package babel Info: The option 'brazil' is deprecated`** | 1 | `Use 'brazilian' instead on input line 351` | `eic-bcc-tcc.cls:46` carrega `\usepackage[english,brazil]{babel}`. | Interno à classe institucional `eic-bcc-tcc.cls` (informativo, sem impacto visual). |
| **`BibTeX Warning` em `main.blg`** (`references.bib:467`) | 1 | `Warning--there's a number but no volume in FinMem2024` | Entrada `@inproceedings{FinMem2024}` contém `number = {1}` sem `volume`. | Remover a linha `number = {1}` de `FinMem2024` em `tcc2/references.bib` (`Seção 6.2.D`). |

> **Nota técnica importante sobre o log:** A classe `tcc2/eic-bcc-tcc.cls` define nas linhas 184–185 `\hfuzz=5pt` e `\hbadness=20000`. Isso significa que o LaTeX **suprime do `main.log` todos os `Underfull \hbox` e qualquer `Overfull \hbox` menor que `5,0 pt`** (exceto quando há caixa explícita). Portanto, os 10 `Overfull \hbox` listados acima são todos **superiores a `5 pt`** (exceto a Tab. 5.2) e visíveis a olho nu no PDF.

---

## 9. Perguntas prováveis da banca sem resposta (ou com resposta incompleta) no texto

As 15 perguntas abaixo foram formuladas simulando a arguição real dos três membros da banca (**Prof. Eduardo Soares Ogasawara** — orientador, foco em rigor científico, ciência de dados e reprodutibilidade; **Prof. Renato Campos Mauro** — membro interno EIC/CEFET-RJ, foco em engenharia de software, sistemas multiagentes e conformidade com o guia do curso; **Gilberto Gil Fidelis Gomes Passos** — membro externo, foco em finanças quantitativas, microestrutura da B3 e gestão de carteiras).

### Bloco A — Orientador (Prof. Eduardo Soares Ogasawara, D.Sc.)

1. **Estocasticidade sob temperatura `1,0` e tamanho de amostra $R=1$ por campanha:**  
   *"Vocês rodaram a API `gemini-3.8-flash` com temperatura `1,0` (Seção 4.6.2), mas executaram apenas uma realização ($R=1$) de cada campanha (v1, v2 e v3). Qual é a variância intrínseca do LLM entre sementes/execuções distintas na mesma janela? Como separar o que foi efeito real da mudança de prompts (v1 $\to$ v2 $\to$ v3) do que foi sorte/azar de uma única trajetória estocástica?"*  
   - **Lacuna no texto:** O texto explica o `CallBank` para reprodutibilidade exata da execução gravada, mas não discute a variância entre execuções independentes ($R > 1$) sob temperatura `1,0`.  
   - **Como blindar no texto:** Explicitar na Seção 5.8 e na Seção 7.4 que os indicadores agregados sobre os **765 pareceres do comitê** (como a queda da taxa de unanimidade de `83,01%` para `4,03%` e a inversão do RSI médio de compras/vendas) possuem $N = 765$ observações por campanha e refletem mudança estrutural inequívoca de distribuição, ao passo que o patrimônio final acumulado ao longo do caminho dependente de estado (*path-dependent*) representa uma única realização ($R=1$) e não deve ser interpretado inferencialmente.

2. **Controle determinístico das 5 lentes sem LLM (estudo de ablação):**  
   *"Na v3, vocês entregaram a cada um dos cinco analistas faixas numéricas explícitas (`RSI < 32`, `bb_lower_gap` entre `-0,01` e `+0,06`, `sma50_gap > +0,01` etc.) e adicionaram três travas determinísticas no compilador. Se vocês codificarem essas mesmas cinco regras diretamente em `if/else` em Python, sem chamar o LLM nenhuma vez, qual é o resultado? O LLM está adicionando algum valor sobre as regras que vocês mesmos escreveram nos prompts da v3?"*  
   - **Lacuna no texto:** Não há baseline determinístico que replique a votação das 5 lentes da v3 sem LLM.  
   - **Como blindar no texto:** Reconhecer explicitamente na Seção 6.6.3 e na Seção 7.5 que a v3 aproxima os *prompts* de uma árvore de regras parametrizada e propor a implementação do **comitê determinístico de 5 lentes sem LLM** como o principal experimento de ablação de trabalhos futuros (`C6-04`, `C7-05`).

3. **Graus de liberdade na v3 e *Probability of Backtest Overfitting* (PBO):**  
   *"Vocês citam \citet{Bailey2017} sobre Probability of Backtest Overfitting na Fundamentação (Seção 2.7), mas na Seção 4.10 introduzem cerca de 17 novos limiares numéricos nos prompts e no compilador da v3 depois de inspecionar os erros da v2 nos mesmos 153 pregões. Quantas configurações intermediárias foram testadas antes de congelar a v3 e qual o risco de a v3 estar sobreajustada especificamente à trajetória de abril a novembro de 2026?"*  
   - **Lacuna no texto:** O texto declara que a v3 é exploratória, mas não quantifica os ~17 hiperparâmetros/limiares introduzidos nem informa se houve outras tentativas intermediárias.  
   - **Como blindar no texto:** Quantificar os limiares da v3 na Seção 4.10 (`C4-09`), declarar que nenhuma decisão inferencial é tomada sobre a v3 exatamente para evitar o viés de seleção denunciado por \citet{Bailey2017}, e apontar que a avaliação fora da amostra da v3 requer sua implantação no ciclo diário prospectivo.

4. **Potência estatística (*statistical power*) e tamanho mínimo de amostra ($N = 153$):**  
   *"Na Tabela 6.4, os erros-padrão da diferença de Sharpe anualizado ficam entre `0,49` e `1,66` unidades de Sharpe, e os intervalos de confiança de 95% têm largura de 2 a 6 unidades de Sharpe. Com essa incerteza amostral em 153 pregões, qual seria o tamanho mínimo da diferença real de Sharpe ($\Delta$) que o teste de vocês conseguiria detectar com 80% de poder aos 5% corrigidos por Holm-Bonferroni? Quantos anos de pregões seriam necessários?"*  
   - **Lacuna no texto:** Nem a Seção 5.6.2 nem a Seção 6.5 calculam a diferença mínima detectável (*Minimum Detectable Effect* — MDE) do teste em $N = 153$.  
   - **Como blindar no texto:** Acrescentar um parágrafo na Seção 6.5 (e na Seção 7.5) observando que, com $\mathrm{EP}(\hat{\Delta}) \approx 1{,}3\text{--}1{,}6$ nas comparações contra regras técnicas e valor crítico ajustado por Holm ($\alpha/5 = 0{,}01$, $z_{0{,}99} \approx 2{,}33$), uma diferença observada precisaria exceder $\hat{\Delta} \gtrsim 3{,}0$ unidades de Sharpe anualizado para rejeitar $H_0$ em apenas 153 pregões — razão pela qual amostras de 3 a 5 anos ($N \approx 750\text{--}1.260$ pregões) são necessárias para detectar ganhos moderados de Sharpe (`C7-05`).

5. **Invariância por escala contra vazamento via fatores de ajuste do Yahoo Finance:**  
   *"Na Seção 4.2 vocês dizem que usam os preços ajustados do Yahoo Finance na janela causal até $t-1$. Mas a coluna `Adj Close` de um snapshot baixado ao final do período já embute fatores de ajuste de dividendos e desdobramentos ocorridos entre $t$ e o final da série. Como vocês garantem que um dividendo pago em $t+20$ não alterou as features técnicas calculadas em $t-1$?"*  
   - **Lacuna no texto:** A prova matemática (já documentada em `src/agents/features.py:5-13` e `H2_METHODOLOGICAL_FREEZE_V1.md:570-579`) não foi incluída no texto da monografia!  
   - **Como blindar no texto:** Incluir a demonstração de invariância por escala na Seção 4.2 (`C4-05`): como um evento corporativo posterior a $t-1$ multiplica toda a série histórica até $t-1$ pela mesma constante $c > 0$, e como todas as 8 *features* e a volatilidade de 21 dias são razões homogêneas de grau zero ($f(c \cdot P) = f(P)$), a constante $c$ se cancela exatamente.

### Bloco B — Membro Interno (Prof. Renato Campos Mauro, D.Sc.)

6. **Qual versão rodou no acompanhamento diário prospectivo (Seção 6.8)?**  
   *"Na Seção 6.8 vocês mostram 23 pregões prospectivos entre outubro e novembro de 2026 nos quais a carteira Multiagentes comprou apenas no primeiro dia, ficou parada pelos 22 dias seguintes e caiu `-23,94%`. Qual versão estava rodando nesse ciclo diário: v1, v2 ou v3? Se foi a v1, por que a v3 não foi colocada em acompanhamento prospectivo?"*  
   - **Lacuna no texto:** O texto omite que o ciclo diário (`dashboard/daily_cycle.py:44`) executa a **v1** (`wallet_manager_api.py`).  
   - **Como blindar no texto:** Explicitar nas Seções 4.11, 5.7.1, 6.8 e 7.1 que o ciclo diário prospectivo foi iniciado em `14/10/2026` com a arquitetura pré-especificada **v1** (antes da conclusão das auditorias post-hoc v2 e v3) e que sua paralisia em tempo real confirma fora da amostra o diagnóstico estrutural da v1 (`C4-06`, `C6-02`).

7. **Onde a ameaça de contaminação do LLM realmente entra no pipeline de software?**  
   *"Vocês afirmam na Seção 5.8 que o modelo `gemini-3.8-flash` pode sofrer contaminação por ter memorizado o período. Mas olhando para o contrato JSON dos agentes na Seção 4.6, quais nós do grafo recebem o nome do ativo (`PETR4`, `VALE3`...) e a data do pregão, e quais nós recebem apenas os 8 números adimensionais?"*  
   - **Lacuna no texto:** O Capítulo 4 não explicita que os cinco analistas técnicos e o analista de risco são anonimizados quanto a *ticker*, data e nível de preço (`src/agents/features.py:23-26`).  
   - **Como blindar no texto:** Destacar na Seção 4.6.2 e na Seção 5.8 que o isolamento de identidade nos analistas bloqueia a memorização direta no comitê por ativo, confinando a superfície de contaminação ao nó `portfolio_manager` (`C4-05`, `C5-03`).

8. **Divergência entre os dois motores de backtest (`engine.py` vs *ledger* de eventos):**  
   *"Na Seção 4.3 (p. 22) vocês dizem que o repositório possui `src/backtesting/engine.py` para ativo único, mas que o replay multiativos e o ciclo diário usam outra implementação baseada no ledger de eventos. Como vocês garantiram por testes automatizados que o ledger de eventos não contém bugs contábeis de arredondamento, dividendos ou caixa negativo?"*  
   - **Lacuna no texto:** O texto menciona a coexistência dos dois mecanismos em `04:100`, mas não descreve a suíte de verificação contábil do *ledger*.  
   - **Como blindar no texto:** Detalhar ao final da Seção 4.3 as invariantes verificadas automaticamente sobre o *ledger* (conservação diária de patrimônio $\mathrm{PL}_t = \text{Caixa}_t + \sum_a \text{qtd}_{a,t} P^{\text{RAW}}_{a,t}$, não-negatividade de caixa e de posições, paridade bit a bit das cinco referências entre v1/v2/v3 e reconciliação de taxas e proventos em `metricas_replay.py`, ver `C4-07`).

9. **Custo computacional, falhas de infraestrutura (HTTP 503) e escalabilidade:**  
   *"Na Seção 6.7 vocês mostram que um replay de 153 pregões para apenas 5 ações exigiu até 4.703 chamadas ao LLM (cerca de 31 chamadas síncronas/por lote a cada pregão) e sofreu 48 falhas HTTP 503 na v1 e 37 na v2, nas quais o fallback adotou `MANTER`. Se o universo fosse o Ibovespa inteiro (~85 ações) ao longo de 10 anos (~2.520 pregões), seriam mais de 1,3 milhão de chamadas por campanha. Como essa arquitetura escala e qual foi o impacto dos 48 pregões/ativos com HTTP 503 sobre a inércia da v1?"*  
   - **Lacuna no texto:** O texto relata os 48 e 37 erros HTTP 503 na Tabela 6.5, mas não analisa se as quedas de serviço da API contribuíram para a baixa atividade da v1 nem discute o gargalo de escalabilidade $\mathcal{O}(A \cdot T)$ do comitê por ativo.  
   - **Como blindar no texto:** Comentar na Seção 6.7 que as 48 falhas HTTP 503 na v1 representam apenas `1,35%` das 3.551 chamadas (e ocorreram majoritariamente em chamadas individuais de analistas ou com retomada de *checkpoint*, não explicando a unanimidade de `83,01%` nos pareceres válidos), e discutir na Seção 7.4/7.5 o custo $\mathcal{O}(A \cdot T)$ como motivação para pré-filtragem quantitativa de ativos antes de acionar o comitê LLM.

10. **Conformidade com o guia de TCC do BCC/CEFET-RJ (busca sistemática e fechamento de objetivos):**  
    *"O guia de TCC do curso pede no Capítulo 3 as strings de busca, as bases consultadas e os critérios de inclusão/exclusão dos trabalhos relacionados, e no Capítulo 7 a retomada individual de cada objetivo específico da Introdução. Onde esses dois elementos estão no texto?"*  
    - **Lacuna no texto:** Ambos foram omitidos na redação atual (`C3-02` e `C7-03`).  
    - **Como blindar no texto:** Inserir o parágrafo de protocolo de busca na abertura do Capítulo 3 (`C3-02`) e fechar nominalmente os seis objetivos específicos na Seção 7.1 (`C7-03`).

### Bloco C — Membro Externo (Gilberto Gil Fidelis Gomes Passos, M.Sc.)

11. **Efeito da não remuneração do caixa pelo CDI sobre H1 e H2:**  
    *"Em 2026 a taxa Selic/CDI no Brasil está em dois dígitos anuais. Na simulação de vocês, o caixa rende 0% (`r_f = 0`). Mas a `Bollinger 20/2` ficou em média com 49,06% do patrimônio em caixa e a `SMA 50/200` com 31,39%, enquanto `Equal Weight 63d` ficou com 0,70% e `Multiagentes v3` com 14,50%. Se o caixa rendesse 100% do CDI diário, a `SMA 50/200` não teria superado a `Equal Weight 63d` em H1, e a distância das regras técnicas para os agentes não seria ainda maior?"*  
    - **Lacuna no texto:** A Seção 5.8 (`05:213`) menciona que caixa zero penaliza quem segura liquidez, mas não calcula o efeito diferencial sobre H1 e H2.  
    - **Como blindar no texto:** Incluir a análise quantitativa de sensibilidade ao CDI na Seção 5.8 e na Seção 6.3 (`C5-04`, `C6-06`).

12. **Lote-padrão vs mercado fracionário da B3 nas 27 vendas residuais da v3:**  
    *"Na Seção 6.6.3 vocês explicam que a trava de posição residual da v3 liquidou integralmente 27 posições abaixo de R\$ 2.000 (22 abaixo de R\$ 500, com ordens de 1 a 9 ações). Na B3, o lote-padrão é de 100 ações; abaixo disso, opera-se no mercado fracionário (`PETR4F`, `VALE3F`), onde a liquidez é menor e o spread bid-ask é mais largo. Além disso, o custo de 0,03% sem corretagem mínima nem slippage é realista para ordens de R\$ 200?"*  
    - **Lacuna no texto:** O texto menciona o critério `< 100 ações` na trava de posição residual (`04:340`), mas não relaciona isso ao lote-padrão versus mercado fracionário da B3 nem ao impacto de *spread* em micro-ordens.  
    - **Como blindar no texto:** Explicitar na Seção 4.10 e na Seção 6.6.3 que o limiar de `100 ações` da trava residual foi inspirado justamente no lote-padrão da B3 para evitar a manutenção indefinida de "pontas" no mercado fracionário, e registrar na Seção 5.8 que a ausência de *slippage* e de *spread* diferenciado para o mercado fracionário favorece estratégias com maior número de micro-ordens como a v3 (`C6-06`).

13. **Assimetria tributária (IR de 15% sobre JCP vs ausência de IR sobre ganho de capital) e reinvestimento de proventos:**  
    *"Vocês descontam 15% de Imposto de Renda na fonte sobre JCP (Seção 4.7), mas não descontam os 15% de IR sobre ganho de capital líquido em vendas mensais acima de R\$ 20 mil em ações. Como a v2 vendeu mais de R\$ 200 mil e a v3 fez 29 vendas com lucro em `PETR4`, `WEGE3` e `ITUB4`, enquanto `Buy & Hold` nunca vendeu nada, essa assimetria tributária não favorece as carteiras de maior giro?"*  
    - **Lacuna no texto:** A Seção 4.7 descreve a retenção de 15% sobre JCP, mas a Seção 5.8 não menciona a ausência de tributação sobre ganhos de capital em alienações.  
    - **Como blindar no texto:** Acrescentar uma frase na Seção 4.7 e na Seção 5.8 (`05:211`) registrando que a simulação modela a retenção na fonte sobre JCP (15%) e a isenção de dividendos vigentes na legislação brasileira, mas abstrai a apuração mensal de imposto sobre ganho de capital líquido em vendas acima de R\$ 20 mil/mês (`C4-10`).

14. **Critério e data de seleção das 5 ações (`BBAS3`, `ITUB4`, `PETR4`, `VALE3`, `WEGE3`) e concentração setorial:**  
    *"Por que exatamente essas cinco ações? Elas representam dois grandes bancos, duas gigantes de commodities e uma exportadora industrial — não há varejo, energia elétrica, saneamento, telecomunicações ou construção civil. Além disso, em que data esse universo de 5 ativos foi fixado: antes de abril de 2026 ou em outubro de 2026?"*  
    - **Lacuna no texto:** A Seção 5.2 lista os 5 ativos sem critério formal nem data de congelamento (DP-07 de `13/10/2026`).  
    - **Como blindar no texto:** Explicitar na Seção 5.2 e na Seção 5.8 (`05:209`) os critérios de liquidez/representatividade no Ibovespa, a data de fixação do universo multiativos e a limitação de concentração setorial em *blue chips* financeiras e exportadoras (`C5-05`).

15. **Exposição média ao mercado (*beta* / % investido) como explicação do desempenho relativo:**  
    *"Em um período em que a carteira `Buy & Hold` caiu `-11,21%`, qualquer estratégia que ficasse metade do tempo fora da bolsa teria vantagem mecânica. A `Bollinger 20/2` ficou 49,06% do tempo em caixa; já a `Multiagentes v3` ficou ~85,5% do tempo comprada e ainda assim terminou no zero a zero (`+0,07%`). Vocês chegaram a comparar o retorno das carteiras ajustado pela exposição média ao mercado (ou o alfa/beta em relação à carteira `Buy & Hold`)?"*  
    - **Lacuna no texto:** O Capítulo 6 analisa o caixa final/médio e o retorno total separadamente, sem conectar o percentual médio investido ($1 - \text{caixa médio}$) à preservação de capital da v3 frente a `Buy & Hold`, `Equal Weight 63d` e `Mínima Variância`.  
    - **Como blindar no texto:** Incluir um parágrafo na Seção 6.3 ou 6.6.3 contrastando o mecanismo de proteção de `Bollinger 20/2` (desalocação média de 49,06% em caixa) com o de `Multiagentes v3` (rotação ativa e *sizing* por convicção mantendo 85,50% de exposição média ao mercado, `C6-06`).

---

## 10. Plano de correção priorizado

Para levar a monografia de **7,3/10 para 10/10** com o menor retrabalho possível, recomenda-se executar as correções nos **quatro lotes ordenados por impacto** abaixo:

### Lote 1 — Críticos e bloqueadores visuais / factuais (Esforço: **P** · ~3–4 horas · Eleva a nota de 7,3 para ~8,5)
1. **Corrigir `main.tex` (pré-textuais e pacotes):**
   - Remover o ponto final de `\title{...Multiagentes.}` em `main.tex:10` (`C0-01`).
   - Remover as vírgulas finais e padronizar iniciais maiúsculas em `\keywords` e `\Keywords` (`main.tex:20-31`, `C0-02`).
   - Remover `\usepackage[htt]{hyphenat}` de `main.tex:3` e usar `\path{...}` para caminhos longos (`P-01`, `C4-03`).
   - Ajustar as duas frases do Resumo e do Abstract para explicitar as cinco comparações com Holm-Bonferroni e a natureza exploratória da v3 (`C0-03`, `C0-04`).
2. **Eliminar os 34 `\paragraph{}` (`.0.0.`) e a página quase em branco:**
   - Substituir os 34 `\paragraph{}` nos Capítulos 5 (16), 6 (14) e 7 (4) por `\subsection{}` ou `\noindent\textbf{...}` (`P-02`, `C5-01`, `C6-03`, `C7-01`).
   - Ajustar 2 linhas na Seção 5.8 para eliminar a linha viúva isolada na página 48 / PDF p. 60 (`C5-06`).
3. **Corrigir os 4 estouros de margem em tabelas (Tabelas 3.1, 5.1, 5.2 e 6.1):**
   - Tabela 3.1 (`03-relacionados.tex:62-90`): inserir `\hspace{0pt}`, reequilibrar larguras e hifenizar `Multi\-agente` e `Rastreabi\-lidade` para eliminar `MultiagenteCustos` e `RastreabilidadeReferências` (`C3-01`).
   - Tabelas 5.1 (`05:63-73`), 5.2 (`05:95-106`) e 6.1 (`06:25-36`): reduzir a última coluna `p{...}` em `0,4 cm` a `1,1 cm` e substituir `\texttt{--references-only}` por `\texttt{-{}-references-only}` em `04:242` e `05:113` (`C4-09`, `C5-06`, `C6-03`).
4. **Corrigir os 5 erros factuais/contradições internas no texto:**
   - `04:72` e `05:188`: corrigir a descrição de `2.649 barras (04/01/2016 a 31/08/2026)`, `1.519 sessões elegíveis (12/01/2018 a 28/02/2024)` e `$H_{\text{real}}$ = 4 sessões reais` (`C4-01`, `C5-02`).
   - `04:6`: corrigir a menção a H1/H2 no grafo de ativo único sobre PETR4 (`C4-02`).
   - `05:205`, `06:191` e `07:47`: corrigir a alegação de que a contaminação só favorece os agentes, alinhando com \citet{Glasserman2023} e destacando o anonimato de ativo/data nos analistas (`C5-03`, `C7-02`).
   - `06:175`: corrigir a afirmação sobre `PETR4` (que já era positivo na v2 com `+R$ 1.812,50`, enquanto `WEGE3` e `ITUB4` passaram a positivo na v3, `C6-01`).
   - `06:204-206`: explicitar que o ciclo diário prospectivo rodou a **v1**, incluir `Bollinger 20/2` e `SMA 50/200` e esclarecer a base de R\$ 100.000,00 dos percentuais `-17,61%` e `-23,94%` (`C6-02`).

### Lote 2 — Rigor metodológico, guia do curso, tabelas e bibliografia (Esforço: **M** · ~5–6 horas · Eleva a nota de 8,5 para ~9,4)
1. **Atender às exigências do guia oficial do BCC/CEFET-RJ nos Caps. 1, 3 e 7:**
   - No Cap. 1: colocar a pergunta central em forma interrogativa direta com `?` (`C1-01`), enunciar as hipóteses H1 e H2 na Introdução (`C1-03`), harmonizar o Objetivo Geral com os 6 específicos (`C1-02`) e adicionar o parágrafo/seção `Organização do Trabalho` ao final do capítulo (`C1-04`).
   - No Cap. 3: inserir o parágrafo de protocolo de busca bibliográfica (bases, *strings* e critérios de seleção, `C3-02`) e harmonizar `03:50` com `03:100` (`C3-03`).
   - No Cap. 7: fechar individualmente os 6 objetivos específicos na Seção 7.1, incluindo o resultado preliminar dos 23 pregões prospectivos da v1 no Objetivo 6 (`C7-03`).
2. **Completar definições matemáticas e blindagens metodológicas nos Caps. 2, 4, 5 e 6:**
   - Definir fórmulas de RSI e MACD no Cap. 2 (`C2-06`), as fórmulas das 8 *features* adimensionais no Cap. 4 (`C4-04`) e as fórmulas de retorno diário, retorno anualizado, volatilidade anualizada e MDD no Cap. 5 (`C5-08`).
   - Incluir a prova de invariância por escala das *features* contra fatores de ajuste ex-post do Yahoo e o anonimato de ativo/data nos analistas (`C4-05`).
   - Expandir a discussão da direção do viés de caixa não remunerado/CDI sobre H1 e H2 (`C5-04`), da exposição média ao mercado e do mercado fracionário da B3 nas 27 vendas residuais da v3 (`C6-06`), dos critérios/data de seleção das 5 ações (`C5-05`) e calibrar as duas frases causais em `06:177` e `06:184` (`C6-04`).
3. **Higienizar `tcc2/references.bib` (Seção 6.2):**
   - Adicionar `arXiv:XXXX.XXXXX` no campo `journal` dos 12 preprints arXiv; corrigir os 5 `@inproceedings` e remover o `.,` de `FinCon2024` e `MacroHFT2024`; proteger as 17 capitalizações com `{...}`; remover `number = {1}` de `FinMem2024`; corrigir `Clarke2006` (`de Silva`), `Bailey2017` (`L{\'o}pez de Prado`), `Thaler1993` (`editor`) e `SuttonBarto2018` (`2nd`).
4. **Polir as Figuras 4.1–4.3, 6.1–6.3 e Tabelas 6.2–6.5:**
   - Adicionar `Fonte: Elaborado pelos autores.` abaixo de todas as 6 figuras e 11 tabelas (`P-08`, Seção 5.1).
   - Nas Tabelas 6.2–6.4, substituir `\resizebox{\textwidth}{!}` por fonte `\small` com cabeçalhos em `\textbf{}`; na Tabela 6.4, expandir `MA` e explicar na nota que $\Delta$ é calculado antes do arredondamento (`C6-05`).
   - Corrigir a colisão de rótulo na Figura 4.2, o contraste `black!12` na Figura 4.3, a ordem de citação das Figuras 6.1 e 6.2 e o rótulo `Mês de referência (2026)` nas Figuras 6.1–6.3 (`C4-08`, `C6-07`).

### Lote 3 — Reequilíbrio estrutural (Cap. 2, Cap. 4 e Apêndice A) e novas figuras (Esforço: **M** · ~4–5 horas · Eleva a nota de 9,4 para ~9,8)
1. **Reequilibrar os Capítulos 2 e 4 (Seção 3.3):**
   - No Cap. 2: remover as subseções órfãs `2.2.1` (CAPM), `2.2.2` (APT) e a Seção `2.4` (Fama-French 3 e 5 fatores, removendo também `FamaFrench1993` e `FamaFrench2015` de `references.bib`, `C2-03`); expandir a Seção `2.7` com os conceitos de viés temporal, contaminação de pré-treinamento, bootstrap estacionário de \citet{PolitisRomano1994} e correção de \citet{Holm1979} (`C2-01`, `C2-02`).
   - No Cap. 4: mover a Tabela 4.3 (`4.9.6`), os detalhes operacionais de `CallBank`/reservas HTTP/rotas (`4.9.4–4.9.5`) e as Seções `4.11–4.12` para um **Apêndice A** (reduzindo o Cap. 4 de 17 para ~11 páginas e adotando voz autoral em `04:4`, `C4-07`).
2. **Incluir as novas figuras propostas na Seção 5.3:**
   - **Figura 5.1:** Linha do tempo experimental (aquecimento, corte do LLM, replay 153 pregões e janela prospectiva 23 pregões) e desenho pareado das campanhas.
   - **Figura 6.4:** Painel duplo com a distribuição de consenso do comitê (v1 vs v2 vs v3) e o perfil de RSI nas compras e vendas executadas (v2 vs v3).
   - **Figura 6.5 (opcional):** Curvas de patrimônio dos 23 pregões prospectivos a partir de `equity_diario.csv`.

### Lote 4 — Polimento editorial fino e compilação limpa (Esforço: **P** · ~2 horas · Eleva a nota de 9,8 para 10/10)
1. **Padronizaracrônimos, estrangeirismos e notação (`P-03` a `P-07`):**
   - Limpar `CAPM` e `APT` de `main.tex`, sincronizar a Lista de Acrônimos com as siglas efetivamente usadas no texto e expandir `RAG`, `PBO`, `MAR`, `JCP`, `DQN`, `PPO`, `LSTM` e `CVaR` na primeira ocorrência (`P-03`).
   - Padronizar itálico em estrangeirismos (`\textit{replay}`, `\textit{bootstrap}`, `\textit{drawdown}`, `\textit{features}`, `\textit{prompts}`, `\textit{fallback}`, `\textit{spread}`, `\textit{z-score}`, `P-04`).
   - Usar espaço inquebrável `R\$~` e `US\$~`, travessão `---` sem espaços ou com espaços padronizados e datas sempre em `DD/MM/AAAA` (`P-05`, `P-06`).
2. **Verificação final de compilação (`main.log` e `main.blg`):**
   - Habilitar os padrões de hifenização de `portuguese` no MiKTeX e recompilar com `latexmk -pdf main.tex`, confirmando **0 avisos no BibTeX**, **0 avisos de `hyperref` bookmark**, **0 avisos de fonte `cmtt`** e **0 `Overfull \hbox`** nas páginas textuais.
