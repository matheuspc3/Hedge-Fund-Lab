# Revisão geral do texto — TCC 2 Hedge-fund-lab

Revisão integral de `tcc2/main.tex`, dos sete capítulos, das tabelas geradas
(`chapters/tabelas/`), das figuras, de `references.bib`, do `main.pdf`
versionado (86 páginas) e do `main.log`. Nenhum arquivo do projeto foi
alterado; a recompilação de controle foi feita numa cópia fora do repositório.

- **Base revisada:** commit `81a1092`; `tcc2/main.pdf` e `tcc2/main.log` de
  19/11/2026 01:14, compilados com TeX Live 2026 (Arch Linux).
- **Recompilação de controle:** cópia de `main.tex`, classe, `.bst`, `.bib`,
  `chapters/`, `figures/` e `images/` compilada com MiKTeX (pdflatex, bibtex,
  makeglossaries e mais dois pdflatex). Resultado: 86 páginas, mesmos avisos,
  exceto a hifenização (ver P-01).
- **Páginas:** "p. N" é o número impresso no rodapé/cabeçalho. A página física
  do PDF é N + 12 (p. 20 = PDF 32). Pré-textuais ocupam PDF 1–12.
- **Severidade:** Crítico (banca derruba / erro factual) · Alto (compromete
  clareza ou rigor) · Médio · Baixo (polimento). Preferências de estilo vêm
  marcadas como "(estilo)" e ficam em Baixo, salvo quando atrapalham a leitura.
- **Regras locais:** o guia oficial do curso está no repositório
  (`tcc2/source/tcc1/docs/Trabalho de Conclusao EIC BCC.pdf`, também em
  `docs/faculdade/`) e foi usado como referência, citado como "guia" com a
  página impressa. Onde nem o guia nem o modelo resolvem, está escrito
  "verificar no manual do CEFET/RJ". As regras ABNT citadas foram conferidas em
  guias de bibliotecas universitárias (links na Seção 7).
- **Versão anterior:** este arquivo substitui uma revisão gerada em outra
  sessão, que continua em `REVISAO_GERAL_TEXTO - Copia.md`. Os achados dela que
  conferi na fonte foram incorporados (C4-04, C5-25, C4-31 e os itens baseados
  no guia).

---

## 1. Veredito geral

**Nota atual: 7,3/10.** Núcleo científico bom e honesto (números do replay
conferem com as fontes; Bootstrap A reproduzível; v1 negativa registrada como
tal), rebaixado por defeitos visíveis no PDF, erros factuais e itens que o guia
do curso pede. As cinco mudanças de maior impacto, em ordem:

1. **Consertar o PDF:** hifenização portuguesa, 34 `\paragraph` numerados ("5.3.0.1"), lista de acrônimos vazia, 10 estouros de margem, "R$" separado do valor.
2. **Corrigir erros factuais e unificar o estatuto:** `H_real` (4 sessões, não 1.519), direção da contaminação, "número de agentes", PETR4, "avaliação H1/H2", base dos % do prospectivo; v1 inferencial condicionada, v2/v3 exploratórias, prospectivo só com a v1.
3. **Cumprir o guia do curso:** declaração de uso de IA, protocolo de busca no Cap. 3, lacuna e resultados na Introdução, objetivos fechados um a um na Conclusão.
4. **Reequilibrar:** Cap. 4 de 17 para ~10 páginas (resto em apêndices); Cap. 2 ganha inferência estatística e conceitos de LLM.
5. **Fechar lacunas para a banca externa:** caixa sem remuneração (Bollinger com 49% e SMA com 31% de caixa médio), critério e data dos cinco ativos, fonte do corte do modelo, imposto sobre ganho de capital, citações na Introdução.

---

## 2. Placar por capítulo

| Capítulo | Nota | Maior problema | Esforço p/ 10 |
|---|---|---|---|
| 0 — Resumo e Abstract | 8,0 | "acompanhamento prospectivo, já em curso" sugere que a avaliação decisiva está andando, mas o ciclo diário opera a arquitetura da v1 | P |
| 1 — Introdução | 6,0 | nenhuma citação; faltam a declaração de uso de IA, a lacuna e os resultados que o guia pede; contribuição enunciada de dois modos | M |
| 2 — Fundamentação | 6,0 | não fundamenta a inferência que decide as hipóteses; seção de *factor investing* sem uso; `\citep` como sujeito de frase | M–G |
| 3 — Trabalhos Relacionados | 7,5 | falta o protocolo de busca sistemática que o guia pede; cabeçalhos sobrepostos na Tabela 3.1; "trata o replay como estudo exploratório" | P–M |
| 4 — Arquitetura | 5,5 | `H_real` descrito como 1.519 sessões (são 4); 17 páginas em tom de auditoria de código; "avaliação H1/H2 sobre PETR4" | G |
| 5 — Metodologia | 7,5 | repete o erro de `H_real`; direção da contaminação; viés do caixa não remunerado sem sentido declarado; "autorizada apenas pelo autor"; universo sem critério | M |
| 6 — Resultados | 8,0 | "número de agentes importa menos" não testado; PETR4; base dos percentuais no prospectivo; exposição em caixa não discutida | M |
| 7 — Conclusão | 7,5 | não fecha objetivo por objetivo, como o guia pede; repete a direção da contaminação; "regra de decisão fixada antes do replay" omite o mapeamento posterior | P |
| Pré/pós-textuais e PDF | 6,0 | hifenização inglesa, `\paragraph` numerado, lista de acrônimos vazia, 10 overfull | P–M |
| Referências | 6,5 | 12 entradas arXiv sem identificador; 16 títulos com maiúsculas perdidas; coletânea de Thaler como obra de autor | P |

---

## 3. Problemas macro (eixos 1 e 5)

### 3.1 Narrativa e fios soltos

A história fecha: problema (avaliar agentes LLM com rigor) → laboratório →
replay pareado → v1 negativa → v2/v3 exploratórias → acompanhamento
prospectivo. Caps. 5, 6 e 7 estão bem amarrados, com tabelas e texto
consistentes. Os fios soltos são:

| ID | Fio solto | Onde nasce | O que fazer |
|---|---|---|---|
| FS-1 | *Factor investing* e modelo de três fatores nunca voltam | 2.4 (`02-fundamentacao.tex:80–88`) | cortar a seção (−0,5 p.) ou reduzir a uma frase em 2.1 |
| FS-2 | *Momentum* nunca é testado (H1 vira "uma regra de tendência") | 2.3.1, H1 em 1:28 | o Cap. 5 (5.8, "Alcance de H1") já reconhece; anunciar já em 1:33 (C1-09) |
| FS-3 | Caminho de ativo único, motor de *backtesting*, `indicator_family_control` e camada de experimentos: construídos para o protocolo não executado, ~4 p., ausentes dos resultados | 4.4–4.6, 4.12 | condensar em 1 p. e mover o resto para apêndice (C4-01) |
| FS-4 | "permite medir o custo de implementação" — nunca medido | 4.7.5 (`04:168`) | medir (descritivo) ou cortar a oração (C4-30) |
| FS-5 | CoT/FinCoT e heterogeneidade de papéis (2.6.2–2.6.3): a v3 é justamente raciocínio estruturado por lentes de domínio, mas 6.5/7.3 não fecham o laço | 2.6.3 | uma frase em 6.5 (C6-23) |
| FS-6 | Anonimização como mitigação (3.5): o sistema já anonimiza analistas e risco, mas o texto não usa isso | 3.5, 5.8 | C4-08 e C5-02 |
| FS-7 | Contribuição "extensível" (1:35) não é demonstrada na conclusão, embora haja evidência (v2/v3 por vinculação de módulo, sem editar fontes seladas, 4.9.1) | 1:35 | citar em 7.1 (C7-10) |
| FS-8 | Objetivo 1, "pipeline reprodutível": a reprodução do replay é por arquivamento das respostas, não por nova inferência; o texto não diz | 1:17 | C4-09 |

Resultado sem preparo prévio: o RSI é eixo central da análise de resultados
(Tabela 6.5, Seção 6.4.3), mas o Cap. 2 não dá sua fórmula nem a janela
(C2-10).

### 3.2 Objetivos e hipóteses → onde são respondidos → resposta

| Item da introdução | Onde é respondido | Resposta no texto | Situação |
|---|---|---|---|
| Pergunta de pesquisa (ambiente comparável e controlado; decisões "mais robustas") | 7.2, 1.º parágrafo (`07:18`) | descreve o ambiente; "não há evidência de que a arquitetura multiagente produza decisões superiores" | **Parcial**: "robustas" nunca é definido (C1-02) |
| Pergunta secundária (arquitetural) | 6.4 e 7.3 | o comportamento "dependeu fortemente" da composição do comitê e das regras | Respondida, de forma descritiva; ancorar nos indicadores de comportamento, não no patrimônio de execuções únicas (C7-03) |
| Obj. 1 — pipeline COTAHIST, proventos, calendário | 4.2, 7.1 | implementado | Respondido como descrição; reprodutibilidade não demonstrada (FS-8) |
| Obj. 2 — motor de *backtesting* e livro de eventos | 4.3, 4.5, 7.1 | ambos implementados | Respondido; o motor não roda o replay e não há verificação de paridade motor × livro (C4-29) |
| Obj. 3 — sistema multiagente, ativo único e multiativos | 4.6, 4.7, 7.1 | implementados | Respondido; ativo único fora dos experimentos (FS-3) |
| Obj. 4 — desenho pareado "e causal", métrica e regra definidas | 4.8, 5.2–5.6 | desenho pareado, relógio causal, Bootstrap A | Respondido; "causal" excede o desenho (C1-05); mapeamento das hipóteses feito depois do replay (C7-02) |
| Obj. 5 — executar o replay e analisar a evolução | Cap. 6 | executado (v1, v2, v3) | Respondido |
| Obj. 6 — acompanhamento diário prospectivo | 4.11, 5.7.3, 6.6 | 23 pregões; Multiagentes −23,94% × Buy & Hold −17,61% | Respondido; não diz que opera a arquitetura v1 (C4-17) |
| H1 | 6.3.1 e 7.2 | H0 não rejeitada (Δ = −0,71; p₊ = 0,881; IC 90% [−1,75; 0,31]) | Respondida explicitamente |
| H2 | 6.3.2 e 7.2 | H0 não rejeitada na v1 (cinco contrastes; Holm = 1,000) | Respondida explicitamente |
| H0 | 6.3.4 e 7.2 | não rejeitada nas duas famílias | Respondida explicitamente |
| Contribuições (1:35): laboratório reproduzível/auditável/extensível; comparação entre gerações; medida da homogeneidade; governança registrada; resultados negativos | 6.4, 6.5, 7.3, 7.6 | entregues, exceto "extensível", não demonstrado | Quase completa (FS-7) |

**Falta na conclusão:** um parágrafo que feche os seis objetivos, um a um
(C7-04).

### 3.3 Equilíbrio entre capítulos

| Cap. | Páginas impressas | % do texto (68 p.) | Proposta |
|---|---|---|---|
| 1 | 3 (1–3) | 4% | +1 p.: motivação com citações; contribuição em um só lugar |
| 2 | 7 (4–10) | 10% | +2 a 3 p.: inferência estatística (1–1,5 p.) e conceitos de LLM, agentes, CoT e contaminação (1 p.); −0,5 p. de *factor investing* |
| 3 | 8 (11–18) | 12% | manter; −0,5 p. de redundância com o Cap. 2 |
| 4 | 17 (19–35) | 25% | −6 a −7 p. para apêndices |
| 5 | 13 (36–48) | 19% | −1 p. (5.7.1 condensado); + figuras de desenho e linha do tempo |
| 6 | 15 (49–63) | 22% | manter; + interpretação das figuras e uma figura de placares/RSI |
| 7 | 5 (64–68) | 7% | +0,5 p. para fechar objetivos |

O Cap. 4 (~6,3 mil palavras e 17 páginas) não se justifica no tamanho atual.
Ele descreve arquivos, identificadores, códigos de erro, rotas HTTP, reservas
de orçamento com seis casas decimais e o processo de publicação de pacotes.
Isso documenta o software, mas não sustenta a tese. A Fundamentação (~2 mil
palavras), ao contrário, não cobre o método estatístico que decide as
hipóteses.

**Cortes e movimentações no Cap. 4 (estimativa):**

| Trecho | Destino | Páginas |
|---|---|---|
| Tabela 4.1 ("Stack") | Apêndice A; no lugar, figura de componentes (F-3) | 0 |
| ¶ `H_real` + histórico do calendário (`04:72–74`) | 5.7.1 / Apêndice B | −0,3 |
| detalhes de SQLite (`BEGIN IMMEDIATE`, `synchronous=FULL`, `Decimal`) (`04:84`) | Apêndice A | −0,2 |
| 4.4 e 4.5 | fundir em "Carteiras de referência" + 1 parágrafo sobre o motor | −0,7 |
| 4.6 (ativo único) | 1 parágrafo + Figura 4.2, ou Apêndice B inteiro | −1,0 |
| último período de 4.7.3 (`pilot_paper.bind`, gestor consultivo) | cortar | −0,15 |
| códigos de erro de 4.8 (`decision_input_lookahead`…) | Apêndice A | −0,2 |
| 4.9.1, 4.9.3 a 4.9.5 (manifestos, *lock*, artefatos JSON, reservas, exportadores, `publish_replay`, rotas) | 2 a 3 frases por subseção + Apêndice C | −1,8 |
| contêiner e rede privada (`04:355`) | 1 frase | −0,3 |
| 4.12 | Apêndice B | −0,8 |
| **Total** | | **≈ −5,5 a −6,5** |

### 3.4 Ordem das seções

- **Cap. 2.** Hoje 2.2 justifica a Equal Weight pela ausência de "matriz de
  covariância", conceito apresentado só em 2.5. Ordem proposta: 2.1 EMH e AMH
  → 2.2 Análise técnica (tendência, reversão, RSI, MACD e Bollinger com
  fórmulas) → 2.3 Teoria de portfólio e carteiras de referência (Markowitz,
  mínima variância, Buy & Hold, Equal Weight) → 2.4 *Backtesting*, sobreajuste
  e contaminação temporal (conceito) → 2.5 Métricas → **2.6 Inferência
  estatística na comparação de estratégias (nova)** → 2.7 LLMs e sistemas
  multiagentes (conceitos; resultados específicos ficam no Cap. 3).
- **Cap. 4.** 4.1 Visão geral (figura de componentes) → 4.2 Dados (COTAHIST,
  fator de ajuste, base congelada) → 4.3 Livro contábil de eventos → 4.4
  Carteira multiagente (comitê, risco, gestor, compilador, execução) → 4.5
  Relógio causal → 4.6 Carteiras de referência → 4.7 Mecanismo do replay
  (trajetória única, *fail-closed*, diário de chamadas, orçamento) → 4.8
  Evolução v1→v2→v3 → 4.9 Operação diária e interface (fundir 4.11 e 4.13).
  Caminho de ativo único e camada de experimentos: Apêndice B.
- **Cap. 5.** O leitor só descobre em 5.7 (p. 45) por que o protocolo
  planejado não foi executado, mas 5.1 (p. 36) já invoca DP-31 e DP-37.
  Proposta: 5.1 Caracterização → 5.2 Do protocolo planejado ao replay (5.7.1
  e 5.7.2 condensados em meia página; detalhes no Apêndice B) → 5.3 Desenho →
  5.4 Hipóteses → 5.5 Referências → 5.6 Métricas → 5.7 Inferência → 5.8
  Acompanhamento prospectivo → 5.9 Ameaças, com subseções em vez de
  `\paragraph`.
- **Cap. 6:** manter. **Cap. 7:** inserir "Atendimento aos objetivos" antes de
  7.2.

### 3.5 v1 confirmatória × v2/v3 exploratórias

O tratamento é honesto na maior parte: o resumo diz "resultado otimista por
construção"; 5.3, 6.3.3 e 7.2 recusam estatuto de teste aos contrastes da
v2/v3; o único p₊ < 0,05 (v3 × SMA) é corretamente rebaixado (Holm 0,121,
referência de pior Sharpe, origem exploratória). Pontos em que o texto deixa a
v3 ou o replay parecerem mais do que a evidência permite:

1. **Vocabulário de estatuto inconsistente (Alto).** "Trata o replay
   retrospectivo como estudo exploratório" (`03:50`), "autorizada como
   extensão exploratória" (`04:230`), "caráter exploratório" (`05:14`),
   "natureza retrospectiva e exploratória" (`05:196`) convivem com
   "Principal" e decisão inferencial para H1 e H2-v1 (Tabela 5.1, `06:11`). A
   banca pergunta: "se o replay é exploratório, por que decide H2?". Texto
   canônico para usar nos Caps. 1, 3, 4, 5 e 7:

   > A v1 é a execução pré-especificada e recebe decisão inferencial,
   > condicionada à possível contaminação do modelo. A v2 e a v3 são iterações
   > ajustadas dentro da amostra e recebem apenas descrição. A única avaliação
   > livre de contaminação é o acompanhamento prospectivo, em curso desde
   > 14/10/2026 com a arquitetura da v1; a avaliação da v3 com regras
   > congeladas é trabalho futuro.

2. "Apenas duas carteiras tiveram retorno positivo" (`06:52`) põe a v3
   (+0,07%, Sharpe 0,09 com erro-padrão 1,28) ao lado da Bollinger (+4,89%)
   (C6-05).
3. "A governança determinística moldou o resultado tanto quanto os sinais"
   (`06:177`, `07:36`) quantifica o que o desenho, sem ablação, não mede
   (C6-04).
4. "Conduzido de modo a evitar o viés de superajuste" (`01:35`): v2 e v3 são
   ajuste dentro da amostra; o trabalho expõe o sobreajuste, não o evita
   (C1-04).
5. "Dependeu fortemente" (`07:30`) ancorado na diferença de patrimônio entre
   execuções únicas com temperatura 1,0 (C7-03).
6. Resumo e abstract: "já em curso" (C0-01).

### 3.6 Rigor e coerência científica — lista consolidada

| ID | Questão | Severidade | Achado |
|---|---|---|---|
| M-01 | Direção da contaminação afirmada ("favorece os agentes") contra o efeito de distração que o próprio Cap. 3 cita | Crítico | C5-02 |
| M-02 | Analistas e risco não recebem ticker, data nem preço (código), mas o texto não usa isso | Alto | C4-08 |
| M-03 | Caixa sem remuneração e r_f = 0: viés com direção conhecida, não declarada | Alto | C5-04, C6-07 |
| M-04 | Universo de cinco ativos sem critério e sem data de escolha | Alto | C5-08 |
| M-05 | Corte de conhecimento "março de 2026" sem fonte | Alto | C3-04 |
| M-06 | "Fixadas antes de qualquer observação" × dois pilotos sobre o mesmo período | Médio | C1-06, C5-07 |
| M-07 | Validação provisória "autorizada apenas pelo autor" e resultados omitidos | Alto | C5-05 |
| M-08 | Acompanhamento prospectivo roda a v1; o texto não diz | Alto | C0-01, C4-17, C5-19 |
| M-09 | Imposto sobre ganho de capital ausente; JCP tributado | Médio | C4-11 |
| M-10 | Reprodutibilidade: features sem fórmula; *prompts* fora do texto; reprodução por arquivamento não declarada | Médio | C4-07, C4-09, Q-14 |
| M-11 | Graus de liberdade da v3 (≥ 17 limiares novos) não dimensionados | Médio | C4-23 |
| M-12 | Poder do acompanhamento prospectivo não quantificado | Médio | C7-08 |
| M-13 | "Regra de decisão fixada antes do replay" omite o mapeamento posterior (H1 → SMA × EW; família H2 de 5 contrastes) | Médio | C7-02 |
| M-14 | Exposição média (caixa) explica parte da ordenação em mercado de queda | Alto | C6-07 |
| M-15 | Fatores de ajuste adquiridos depois do período: falta argumentar se vazam para as features | Médio | C4-05 |
| M-16 | `H_real` descrito como a série de 1.519 sessões; o congelamento define 4 sessões | Crítico | C4-04, C5-25 |

**Limitações pedidas no roteiro de revisão:** amostra curta, cinco ativos,
contaminação, iterações no mesmo período e custos estão em 5.8 e 7.4.
Múltiplas comparações estão em 5.6.2, mas não em 7.4. Faltam em 7.4: seleção
do universo, sentido do viés do caixa, imposto sobre ganho de capital e
"prospectivo só com a v1" (C7-05).

**Reprodutibilidade:** o Bootstrap A está impecável (B, semente, bloco médio,
fórmula de p₊, posto de L₉₅, tratamento de degenerescência). Sharpe,
custos (0,03% sobre o bruto), caixa e proventos (data-com, pagamento, JCP
líquido de 15%) também estão. Faltam a fórmula das oito features, o texto dos
*prompts* (analista v5, lentes v2/v3, risco, gestor v1/v2/v3) e a declaração
de que a reprodução se faz a partir das respostas arquivadas.

### 3.7 Verificação numérica feita

- Resumo, abstract, Caps. 1, 6 e 7 conferidos contra `METRICAS_REPLAY.md`,
  `BOOTSTRAP_REPLAY.md`, `chapters/tabelas/*.tex`, o documento mestre
  (`evidence/04-replay-abril-novembro/relatorios/evolucao_replay_v1_v2_v3_tcc.md`)
  e `evidence/06-operacao-diaria/serie-diaria-20261117/equity_diario.csv`.
- **Replay: nenhuma divergência de valor.** Conferidos também, por
  aritmética: diferenças de patrimônio (4.819,69; 11.276,25; 11.200,68;
  10.198,07; 4.252,52; 14.323,79; 17.888,65; 22.708,34; 3.564,86), variações
  da Tabela 6.1, cesta inicial (855 × 23,39 + … = R$ 99.883,52), Sharpes
  implícitos nos contrastes, Holm (v1 = 1,000; v3 = 0,121), amplitudes dos
  intervalos (2,06 a 4,88), percentuais de placares (somam 745 na v3) e
  chamadas (4.703; 4.702; 4.703) e custos de inferência (7,44; 8,92; 8,63).
- **Acompanhamento prospectivo: uma divergência de base** (C6-01). Os valores
  em reais conferem com o CSV.
- **Fontes de verdade com texto desatualizado** (Médio; o repositório é
  público e a banca pode consultá-lo):
  - `METRICAS_REPLAY.md:5` diz "As três versões da Multiagentes foram
    ajustadas a partir das auditorias desta mesma janela" (a v1 não foi) e,
    na linha 36, "sem que o replay seja um teste de H2" (a monografia decide
    H2 pela v1).
  - `METRICAS_REPLAY.md:37` mantém um `TODO(redator)` sobre Lo (2002), já
    resolvido.
  - `MATRIZ_EVIDENCIAS.md` §1 marca H1, H2 e H0 como PENDENTE e §4 aponta
    "`05-metodologia.tex` (L61)", linha que não existe mais.
  - `MATRIZ_EVIDENCIAS.md:33` registra "H_real PETR4.SA, 1519 sessões",
    provável origem do erro de C4-04: o congelamento
    (`H2_METHODOLOGICAL_FREEZE_V1.md` §7) define `H_real` como 4 sessões e
    1.519 como o conjunto elegível `|E|`.

---

## 4. Achados detalhados

### 4.0 Padrões transversais (registrados uma vez; ocorrências listadas)

**P-01** · **Alto** · build do PDF; `main.log:66–71`; o PDF inteiro
- **Trecho:** log: "No hyphenation patterns were preloaded for the language
  'Portuguese' … Now I will use the patterns preloaded for \language=0
  instead"; PDF: "ver-ificada" (p. 21), "req-uisição" (p. 64),
  "extrap-olação" (p. 42), "mod-elo" (p. 12–13), "refer-ência" (p. 1),
  "anal-istas" (Figura 4.3, p. 26).
- **Problema:** o PDF versionado foi compilado sem padrões de hifenização do
  português; toda a monografia está hifenizada com regras inglesas. São erros
  de divisão silábica visíveis em muitas páginas.
- **Correção:** recompilar onde os padrões existem. Na recompilação de
  controle com MiKTeX, o log mostra "Hyphen rules for 'brazil' set to
  \l@portuguese" e a p. 21 sai "ve-rificada". No Arch, instalar o pacote de
  idioma português do TeX Live (no Arch, `texlive-langportuguese`) e rodar
  `fmtutil-sys --all`. Antes de entregar, conferir no log que o aviso sumiu.

**P-02** · **Alto** · `05:75,77,79,83,115,124,133,135,137,205–217`;
`06:52–60,167–179,184,186`; `07:20–26`; sumário (PDF 10–11) e corpo
(p. 39–65)
- **Trecho:** "5.3.0.1 H1.", "5.5.0.1 Sharpe Ratio líquido (critério
  primário).", "6.4.3.0.5 Resultado por ativo.", "7.2.0.4 Versões
  exploratórias."
- **Problema:** a classe numera `\paragraph` e o põe no sumário
  (`secnumdepth`/`tocdepth` 5). Como não há `\subsubsection`, a numeração
  pula um nível e aparece o "0". São 34 entradas em itálico, terminadas em
  ponto, no sumário. A numeração progressiva da NBR 6024 não admite nível
  vazio. O `hyperref` acusa o mesmo defeito: "Difference (3) between bookmark
  levels is greater than one" (13 avisos).
- **Correção:** trocar `\paragraph{…}` por `\paragraph*{…}` (não numerado,
  fora do sumário) e conferir o resultado. Alternativa: `\textbf{H1.}` no
  início do parágrafo. Nas ameaças (5.8), promover as sete a `\subsection`
  (5.8.1–5.8.7).

**P-03** · **Alto** · `main.tex:19–27`; pré-textual (PDF 8 em branco)
- **Trecho:** `\newacronym{llm}{LLM}{Large Language Model}` …; nenhum `\gls`
  no texto.
- **Problema:** os nove acrônimos declarados nunca são usados via `\gls`.
  Com `glossaries`, a lista só imprime entradas usadas: a "LISTA DE
  ACRÔNIMOS" não aparece e sobra uma página em branco (PDF 8). LLM aparece 32
  vezes como texto cru, e "Large Language Models (LLMs)" é definido duas
  vezes (`01:6` e `02:108`). Acrônimos usados e não declarados: B3,
  COTAHIST, OHLCV, JCP, CVaR, DQN, TDQN, PPO, KDJ, LSTM, MDD, MAR, CFA, HAD,
  CSRF, HTTP, IA, SLSQP, DP. Declarados e sem uso: ETL e MAS.
- **Correção:** usar `\gls{llm}` na primeira ocorrência de cada capítulo (ou
  em todas) e `\glsaddall` no preâmbulo como rede de segurança; declarar os
  ausentes, por exemplo
  `\newacronym{jcp}{JCP}{Juros sobre Capital Próprio}`,
  `\newacronym{mdd}{MDD}{\textit{Maximum Drawdown}}`,
  `\newacronym{cvar}{CVaR}{\textit{Conditional Value at Risk}}`; remover ETL
  e MAS se continuarem sem uso; padronizar a expansão de LLM em português ou
  em itálico.

**P-04** · **Médio** · estrangeirismos, todos os capítulos. Decisão proposta:
termo estrangeiro comum em itálico; nome próprio de carteira, software ou
procedimento em redondo.

| Termo | Hoje | Decisão |
|---|---|---|
| replay | redondo ~98 vezes; itálico 2 (`04:84`, `05:14`) | `\textit{replay}`; "Replay Contínuo Abril–Novembro de 2026" em redondo (nome próprio) |
| pipeline | redondo 12 vezes | `\textit{pipeline}` |
| momentum | redondo 4 (`01:28`, `02:16,50,56`), itálico 8 | `\textit{momentum}`; não traduzir como "momento" (`03:16`) |
| features | redondo 7 (Cap. 4), itálico em `05:205` | `\textit{features}` ou "atributos" |
| framework, stack, lock, runners, frontend | redondo (`04:40,368`, Tab. 4.1, títulos 4.9.1 e 4.13) | itálico ou português ("arcabouço", "pilha", "trava", "executores", "interface") |
| Buy and Hold / Equal Weight como estratégia | itálico (`02:31,34`) | `\textit{buy and hold}`, `\textit{equal weight}` em minúsculas; Buy \& Hold e Equal Weight 63d em redondo quando designam carteiras |
| Buy \& Hold como carteira | redondo, exceto `\textit{Buy \& Hold}` em `04:242` | redondo |
| Mean Reversion / mean reversion | `02:60` maiúsculas; `02:78` minúsculas | `\textit{mean reversion}` |
| z-score | redondo `02:60`; itálico `03:33` | `\textit{z-score}` |
| spread | redondo `02:143`; itálico nos demais | `\textit{spread}` |
| a priori | redondo `05:219` | `\textit{a priori}` |
| bootstrap | itálico; "Bootstrap A" em redondo; "\textit{bootstrap} A" na legenda da Tabela 6.4 | `\textit{bootstrap}` (termo) e "Bootstrap A" (nome) |
| Sharpe Ratio / Sharpe ratio / índice de Sharpe / Sharpe | as quatro formas | "índice de Sharpe" na primeira ocorrência; depois "Sharpe" |
| Sortino Ratio / Sortino ratio | `01:29` redondo; `02:140` itálico | "índice de Sortino" |
| Large Language Models | itálico no texto; redondo nas palavras-chave | manter itálico também nas palavras-chave, ou traduzir |

**P-05** · **Médio** · nomes e termos com mais de uma grafia

| Conceito | Variantes encontradas | Decisão |
|---|---|---|
| sobreajuste | "superajuste" (resumo, `01:4,35`); "sobreajuste" (`03:12,50`, `05:207`, `07:48`) | "sobreajuste (\textit{overfitting})" |
| etapa anterior | "etapa anterior do trabalho" (`01:10,25`); "TCC1" (`05:16,41`); "TCC 1" (`WRITING_RULES.md`) | "TCC 1" |
| Equal Weight 63d | "Equal Weight" (resumo, abstract); "pesos iguais" (13×; Tab. 3.1; `04:92,242`); "carteira igualmente ponderada" (`04:90`) | "Equal Weight 63d" como nome; "pesos iguais" só como conceito |
| Mínima Variância 252/63 | "mínima variância" (`04:90,242`; Tab. 3.1) | idem |
| Bandas de Bollinger | "Bandas" (`02:68`, `04:88`); "bandas" (`03:48`) | "bandas de Bollinger" (substantivo comum) |
| Multiagentes (carteira) | "carteira Multiagentes"; "carteira multiagente"; "MA v1" (Tab. 6.4) | "carteira Multiagentes" como nome; nunca "MA" (C6-12) |
| H0 | "H0" no texto; "$H_0$" na nota da Tabela 6.4 | "H0" |
| versões | "v1" no texto; "V1" nos títulos (caixa alta da classe) | aceitável, imposto pela classe |

**P-06** · **Médio** · 34 linhas com "R\$ n" ou "US\$ n" quebráveis
(Caps. 1, 4–7)
- **Trecho:** p. 52 "e R$ / 4.819,69"; p. 54 "R$ / 22.708,34"; p. 57
  "R$ / 5.443,38"; p. 58 "(+R$ / 10.198,07)"; p. 59 "R$ / 21,48"; p. 62
  "US$ / 8,63".
- **Problema:** o símbolo da moeda fica no fim de uma linha e o valor no
  começo da seguinte.
- **Correção:** substituir globalmente `R\$ ` por `R\$~` e `US\$ ` por
  `US\$~`; fazer o mesmo em "DP-~27" (p. 20, 63), ou retirar os DP do texto
  (P-08).

**P-07** · **Médio** · 328 `\texttt` nos capítulos, a maioria no Cap. 4;
caminhos quebrados com hífen inserido
- **Trecho:** "b3_-calendar.py" (p. 20), "continuous_replay_-data.py"
  (p. 20), "technical_-analyst.py" (p. 23–24), "auction_or-ders.py::plan"
  (p. 25), "dash-board/dividends_api.py" (p. 27),
  "manager_con-text_changed_before_transport" (p. 27),
  "H2_SCIEN-TIFIC_SHARPE_DEFINITION_V1" (p. 22; também na Lista de Tabelas e
  na legenda da Tabela 6.2).
- **Problema:** o `hyphenat` com a opção `htt` quebra `\texttt` inserindo
  "-", que o leitor toma como parte do nome. Três desses parágrafos ainda
  estouram a margem (P-13).
- **Correção:** reduzir identificadores no texto (C4-01). Para caminhos
  restantes, usar `\path{scripts/continuous_replay_data.py}` (pacote `url`,
  já carregado pela classe), que quebra em "/" e "_" sem inserir hífen.

**P-08** · **Médio** · 30 ocorrências de "DP-n" (Caps. 4–6)
- **Trecho:** "(DP-27)" (`04:77`), "DP-30" (`04:217`), "a DP-37, que reabre a
  DP-31" (`05:18`), "(DP-11)" (Tab. 5.2).
- **Problema:** identificadores internos do repositório; a banca não tem o
  documento de direção, e DP-31 só é explicada em `05:194`, oito páginas
  depois da primeira menção.
- **Correção:** trocar pelo conteúdo ("a decisão de projeto que restringe a
  avaliação de agentes ao regime prospectivo") ou criar um apêndice "Decisões
  de projeto citadas" com uma linha por DP (11, 20, 27, 30, 31, 33–37) e a
  data.

**P-09** · **Baixo** · datas: `04:72` usa ISO ("2018-01-12 a 2024-02-28");
o resto usa dd/mm/aaaa. **Correção:** "12/01/2018 a 28/02/2024".

**P-10** · **Baixo (estilo)** · frases acima de 60 palavras que atrasam a
leitura: `01:8` (3.ª frase, ~100 palavras), `01:10`, `01:35`, `05:9`, `05:170`
(parágrafo de ~330 palavras), `06:11`. **Correção:** dividir; propostas
concretas em C1-03 e C5-11.

**P-11** · **Médio** · fonte abaixo de figuras e tabelas
- **Problema:** Tabelas 3.1 e 6.1–6.5 têm "Fonte:"; Tabelas 4.1–4.3, 5.1 e
  5.2 e as seis figuras não têm. O exemplo do guia (p. 2–3) não usa linha de
  fonte, mas a NBR 14724 exige a fonte abaixo da ilustração, mesmo quando é
  produção dos autores. O defeito aqui é a inconsistência interna: metade dos
  floats tem, metade não.
- **Correção:** acrescentar após cada float, por exemplo
  `{\footnotesize Fonte: elaborado pelos autores.}` e, nas figuras do replay,
  `{\footnotesize Fonte: elaborado pelos autores a partir de \texttt{daily.csv} das campanhas REPLAY-01 a REPLAY-03.}`.
  As figuras 6.x e as Tabelas 6.2–6.4 são geradas por
  `scripts/metricas_replay.py` e `scripts/bootstrap_replay.py`: a mudança
  precisa ir para o gerador, não para o `.tex`.

**P-12** · **Baixo** · legendas longas inteiras nas listas (PDF 6–7)
- **Trecho:** Lista de Tabelas: legenda da Tabela 6.4 com seis linhas;
  "H2_SCIENTIFIC_-SHARPE_DEFINITION_V1" quebrado.
- **Correção:** legenda curta opcional, por exemplo
  `\caption[Comparações pareadas de Sharpe pelo Bootstrap A]{…legenda longa…}`;
  idem para as Figuras 4.1–4.3 e 6.1 e as Tabelas 6.2 e 6.3.

**P-13** · **Médio** · 10 caixas que estouram a margem (`main.log`, iguais
no MiKTeX)

| Local | Excesso | Página |
|---|---|---|
| `03:70` cabeçalho "Multiagente" | 9,4 pt | 17 |
| `03:70` cabeçalho "Rastreabilidade" | 21,5 pt | 17 |
| `04:17–38` Tabela 4.1 | 1,2 pt | 19 |
| `04:74` "(src/backtesting/b3_-…" | 33,5 pt | 20 |
| `04:113` "…graph.py:" | 11,4 pt | 23 |
| `04:262` rotas `/laboratory/replay/…` | 6,5 pt | 30 |
| `05:63–73` Tabela 5.1 | 8,2 pt | 38 |
| `05:95–106` Tabela 5.2 | 1,9 pt | 41 |
| `05:113` "src/backtesting/metrics.py. O cálculo…" | 13,3 pt | 41 |
| `06:25–36` Tabela 6.1 | 25,5 pt | 49 |

Correções nos achados C3-01, C4-15, C5-16 e C6-14. A classe define
`\hfuzz=5pt`, então excessos menores podem não aparecer no log.

**P-14** · **Médio** · parágrafos curtos demais para o padrão do guia
- **Regra:** o guia do curso (p. 1) pede frases curtas e parágrafos com pelo
  menos três frases e uma única ideia central.
- **Parágrafos de uma frase:** `01:12`, `02:24`, `02:98`, `02:104`, `02:130`,
  `04:10`, `04:72`, `04:98`, `04:113`, `04:310`, `05:131`, `05:168`, `06:167`,
  `07:6`. **De duas frases:** `01:33`, `02:22`, `02:48`, `02:56`, `02:66`,
  `02:88`, `02:124`, `03:60`, `04:88`, `04:111`, `04:220`, `06:208`.
- **Correção:** fundir com o parágrafo vizinho de mesma ideia (por exemplo,
  `02:104` na abertura de 2.8, `05:168` em `05:151`, `06:167` com `06:169`) ou
  desenvolver. O problema inverso, frases longas demais, está em P-10.

---

### Cap. 0 — Resumo e Abstract (`main.tex:55–63`; PDF 4–5)

Resumo: 265 palavras, parágrafo único, com objetivo, método, resultados e
conclusão (dentro da faixa de 150 a 500 palavras da NBR 6028:2021). Abstract:
250 palavras, fiel ao resumo, frase a frase.

**C0-01** · **Alto** · `main.tex:56` e `:61` · PDF 4–5
- **Trecho:** "A avaliação livre de contaminação do modelo depende do
  acompanhamento prospectivo, já em curso." / "…depends on the prospective
  daily tracking already under way."
- **Problema:** o ciclo diário opera a arquitetura da v1
  (`dashboard/daily_cycle.py:44` importa `wallet_manager_api`, com o
  compilador original; nenhum módulo da v2/v3), com Multiagentes em −23,94%
  contra −17,61% do Buy & Hold após 23 pregões (6.6). A conclusão propõe
  congelar a v3 para avaliação prospectiva como trabalho futuro (`07:61`). O
  leitor entende que a avaliação decisiva da arquitetura relatada já está em
  andamento.
- **Correção (resumo):** "A avaliação livre de contaminação depende do
  acompanhamento prospectivo: a arquitetura da v1 é acompanhada diariamente
  desde 14/10/2026, e a avaliação da v3 com regras congeladas fica como
  trabalho futuro."
  **(abstract):** "A contamination-free evaluation depends on prospective
  tracking: the v1 architecture has been tracked daily since 14 October 2026,
  and a frozen-rule evaluation of v3 is left for future work."

**C0-02** · **Médio** · `main.tex:56`
- **Trecho:** "O estudo empírico é um replay retrospectivo de 153 pregões"
- **Problema:** "replay" em redondo no mesmo parágrafo em que *backtesting* e
  *bootstrap* estão em itálico (P-04).
- **Correção:** `um \textit{replay} retrospectivo`.

**C0-03** · **Baixo** · `main.tex:56` · "superajuste" → "sobreajuste" (P-05).

**C0-04** · **Baixo** · `main.tex:57`, `:62`
- **Trecho:** "Palavras-chave: Análise Quantitativa. Sistemas Multiagentes.
  Large Language Models. Backtesting. Mercado Acionário Brasileiro."
- **Problema:** termos em inglês sem destaque numa lista em português. Cinco
  palavras-chave, separadas e terminadas por ponto, é o limite do guia do curso
  (três a cinco).
- **Correção:** "Modelos de Linguagem de Grande Escala" e "*Backtesting*", ou
  manter em inglês com `\textit{}`.

**C0-05** · **Baixo** · `eic-bcc-tcc.cls:319` · PDF 5
- **Trecho:** "Undergratuade Thesis – Federal Center of Technological
  Education."
- **Problema:** erro de digitação ("Undergraduate") e nome da instituição
  truncado, gerados pela classe institucional; o mesmo erro aparece no abstract
  do próprio guia.
- **Correção:** não editar a classe sem autorização; comunicar ao orientador
  ou ao mantenedor do modelo. Se houver permissão, corrigir para
  "Undergraduate Thesis – Federal Center of Technological Education Celso
  Suckow da Fonseca".

**C0-06** · **Baixo** · cabeçalho do resumo gerado pela classe: "2026. 74.
Trabalho de Conclusão de Curso" — a ABNT usaria "74 f." ou "74 p.", mas o
resumo-modelo do guia usa o mesmo formato da classe; manter.

**C0-07** · **Médio** · `main.tex:56` e `:61` · PDF 4–5
- **Trecho:** "A avaliação de estratégias quantitativas em mercados não
  estacionários é sujeita a custos, dependência de regime e superajuste. Este
  trabalho apresenta o Hedge-fund-lab…"
- **Problema:** a página de resumo do modelo (guia) pede contextualização,
  lacuna (*gap*), objetivo, metodologia e resultados. A lacuna da literatura
  não aparece.
- **Correção:** inserir após a primeira frase: "Avaliações de agentes baseados
  em LLMs em negociação costumam usar janelas curtas, ações norte-americanas e
  pouco controle de custos e do conhecimento prévio do modelo." (sustentada por
  3.4–3.8). No abstract: "Evaluations of LLM-based trading agents often rely
  on short windows, U.S. equities and little control of costs and of the
  model's prior knowledge." O resumo continua abaixo de 500 palavras.

Cap. 0: 2 parágrafos (resumo, abstract) e 2 listas de palavras-chave
revisados; 4 com problema.

---

### Cap. 1 — Introdução (`01-introducao.tex`; p. 1–3)

**C1-01** · **Alto** · `01:4–37` · p. 1–3
- **Trecho:** o capítulo inteiro tem zero `\cite`.
- **Problema:** afirmações empíricas sem suporte: "abordagens clássicas de
  análise técnica … frequentemente apresentam limitações … pelo risco de
  superajuste" (`:4`); deliberação multiagente com LLMs (`:6`); "viés de
  superajuste que caracteriza boa parte da literatura aplicada" (`:35`). A
  Introdução é a primeira coisa que a banca lê.
- **Correção (`:4`, pronta para colar):**
  > O mercado financeiro impõe desafios à construção e à avaliação de
  > estratégias quantitativas, sobretudo em cenários de alta volatilidade e
  > não estacionariedade \citep{Lo2004}. Abordagens clássicas de análise
  > técnica continuam úteis como referência, mas seu desempenho varia entre
  > regimes, e a escolha de regras e parâmetros sobre o mesmo histórico
  > produz resultados superestimados \citep{White2000, Bailey2017}. Essa
  > constatação motiva um ambiente experimental que organize dados, regras de
  > decisão e critérios de avaliação de forma rigorosa, como condição prévia à
  > investigação de desempenho superior.

  Em `:6`, depois de "(LLMs)": `\citep{TradingAgents2024, Xia2026}`. Em
  `:35`, ver C1-04.

**C1-02** · **Médio** · `01:6` · p. 1
- **Trecho:** "se uma arquitetura multiagente baseada em LLMs produz decisões
  de investimento mais robustas do que abordagens tradicionais"
- **Problema:** "robustas" nunca é operacionalizado. H2 fala em "desempenho
  superior ajustado ao risco"; a conclusão (`07:18`) traduz "robustez" por
  "decisões superiores" sem dizer.
- **Correção:** "…produz decisões de investimento com desempenho ajustado ao
  risco, líquido de custos, superior ao de abordagens tradicionais, quando
  submetida a critérios explícitos de risco, custo e consistência
  operacional?" (a pergunta muda de redação, não de objeto; as hipóteses ficam
  intactas).

**C1-03** · **Médio** · `01:8` × `01:35` · p. 1, 3
- **Trecho:** "Como contribuição principal, propõe-se a avaliação comparativa
  entre metodologias clássicas…" × "A contribuição deste trabalho é menos a
  antecipação de um resultado de desempenho superior e mais o estabelecimento
  de uma base técnica e metodológica…"
- **Problema:** duas "contribuições principais" diferentes; a 3.ª frase de
  `:8` tem ~100 palavras.
- **Correção:** apagar a frase "Como contribuição principal…" e reescrever o
  restante de `:8`:
  > Com esse propósito, o objetivo geral é desenvolver o Hedge-fund-lab, um
  > laboratório quantitativo para \textit{backtesting} de estratégias de
  > investimento baseado em sistemas multiagentes. O laboratório integra um
  > \textit{pipeline} de dados construído sobre os registros oficiais de
  > negociação da B3 (COTAHIST), persistidos em banco relacional, a um sistema
  > multiagente com papéis de análise técnica, gestão de risco e gestão de
  > carteira. Esse sistema tem duas versões: um grafo LangGraph para um único
  > ativo e uma carteira multiativos com capital compartilhado. Ambas executam
  > sobre mecanismos próprios de simulação e contabilidade, que permitem medir
  > o desempenho frente às carteiras de referência.

  Manter `:35` como o único enunciado de contribuição.

**C1-04** · **Alto** · `01:35` · p. 3
- **Trecho:** "e com o registro de resultados negativos, conduzido de modo a
  evitar o viés de superajuste que caracteriza boa parte da literatura
  aplicada."
- **Problema:** v2 e v3 são ajuste dentro da amostra (`05:81`); o trabalho
  separa e rotula o sobreajuste, não o evita. A frase dá à banca a deixa:
  "vocês evitaram o sobreajuste fazendo três versões no mesmo período?".
- **Correção:** "…; e com o registro de resultados negativos e a separação
  explícita entre a execução pré-especificada (v1) e as iterações ajustadas
  dentro da amostra (v2 e v3), que expõe, em vez de ocultar, o risco de
  sobreajuste documentado na literatura \citep{White2000, Bailey2017}."

**C1-05** · **Médio** · `01:20` · p. 2
- **Trecho:** "Estabelecer um desenho experimental pareado e causal"
- **Problema:** "causal" excede o desenho: uma trajetória, uma execução
  estocástica por versão, intervenções em bloco (o próprio `05:211` fala em
  "fatores de confusão").
- **Correção:** "Estabelecer um desenho experimental pareado, com relógio
  causal de informação, métrica primária e regra de decisão estatística
  definidas, que permita…"

**C1-06** · **Médio** · `01:10` · p. 2
- **Trecho:** "a v1, pré-especificada, cujas regras foram fixadas antes de
  qualquer observação de seu desempenho no replay"
- **Problema:** antes da campanha contínua houve dois pilotos com a mesma
  arquitetura sobre subjanelas do período: 06–17/04 e 20/04–05/05, este
  escolhido "pela queda observada" (`docs/DIRECAO_DO_PROJETO.md`, DP-37,
  13/11). O próprio `05:79` os menciona.
- **Correção:** "a v1, pré-especificada, cujas regras foram fixadas antes da
  campanha contínua e não foram alteradas após dois ensaios curtos sobre
  subjanelas do mesmo período".

**C1-07** · **Médio** · `01:28–30` × `05:44–46` · p. 3, 38
- **Trecho:** "H1: Será avaliado se estratégias…" × "H1: estratégias baseadas
  em momentum … apresentam desempenho superior…"
- **Problema:** as hipóteses "preservadas integralmente" têm duas redações.
  O `evidence/LEIA-ME.md` registra três versões do texto do TCC 1 e "falta
  decidir qual é a versão entregue".
- **Correção:** fixar a versão entregue do TCC 1, copiar o enunciado
  literalmente no Cap. 1 e, no Cap. 5, remeter ao Cap. 1 em vez de reescrever
  ("As hipóteses enunciadas na Seção 1 são operacionalizadas como…").

**C1-08** · **Baixo** · `01:28` · "momentum" em redondo e "trend following"
em itálico na mesma linha → `\textit{momentum}` (P-04).

**C1-09** · **Médio** · `01:33` · p. 3
- **Trecho:** "No replay, H1 é operacionalizada pelo contraste de Sharpe entre
  a SMA 50/200 e a Equal Weight 63d"
- **Problema:** a introdução não avisa que *momentum* não é testado; a banca
  descobre na p. 47.
- **Correção:** acrescentar: "Como nenhuma referência implementa
  \textit{momentum} transversal ou de série temporal, H1 é respondida apenas
  para uma regra de tendência (Seção~\ref{sec:met-ameacas})."

**C1-10** · **Baixo (estilo)** · `01:4` · "antes da busca por desempenho
superior imediato" → "como condição prévia à investigação de desempenho
superior" (incluído em C1-01).

**C1-11** · **Baixo** · `01:37` · o resumo da estrutura do Cap. 2 omite
"*factor investing*" e "*backtesting* e riscos metodológicos". Atualizar
depois da reorganização (3.4).

**C1-12** · **Alto** · capítulo inteiro (ausência) · p. 1–3
- **Trecho:** não há.
- **Problema:** o guia do curso (seção 2.5, p. 7) pede declarar explicitamente
  como ferramentas de IA generativa foram usadas na elaboração do texto, se for
  o caso. O repositório indica uso de agentes na escrita (`tcc2/WRITING_RULES.md`,
  `tcc2/agent-reports/`). Num trabalho cujo objeto é LLM, a omissão vira
  pergunta certa da banca.
- **Correção:** parágrafo ou subseção ao fim do Cap. 1, adaptando o modelo do
  guia ao que de fato ocorreu (os autores definem o conteúdo): "Durante a
  elaboração deste trabalho, foram utilizadas ferramentas de IA generativa para
  [revisão de linguagem, organização do texto, auditoria do código, redação de
  rascunhos — ajustar]. Todo o conteúdo técnico, as decisões metodológicas, os
  resultados e as conclusões foram verificados pelos autores, e as afirmações
  empíricas remetem a artefatos versionados no repositório. O modelo de
  linguagem avaliado (\texttt{gemini-3.8-flash}) é objeto do estudo, e não
  ferramenta de redação."

**C1-13** · **Médio** · `01:4–37` · p. 1–3
- **Problema:** o guia (p. 6) diz que a introdução reúne motivação, definição
  do problema, objetivos, principais resultados alcançados e estrutura, e que a
  motivação deve deixar clara a lacuna da literatura. O Cap. 1 não declara a
  lacuna (ela só aparece no Cap. 3) nem antecipa os resultados.
- **Correção:** (a) na motivação: "Sistemas multiagentes com LLMs para
  negociação vêm sendo avaliados em janelas curtas, quase sempre em ações
  norte-americanas e sem controle do conhecimento que o modelo tem do período
  \citep{TradingAgents2024, FINSABER2026, Xia2026}." (b) antes de `01:37`:
  > No \textit{replay}, a versão pré-especificada terminou em $-17{,}82\%$,
  > abaixo das cinco referências, e nenhum contraste rejeitou H0; a SMA 50/200
  > também não superou a Equal Weight 63d. A v3, exploratória, terminou em
  > $+0{,}07\%$, acima de quatro referências e abaixo da Bollinger 20/2. Não há,
  > portanto, evidência de superioridade dos agentes, e a avaliação livre de
  > contaminação depende do acompanhamento prospectivo.

Cap. 1: 10 parágrafos e 9 itens de lista revisados; 9 parágrafos e 2 listas
com problema.

---

### Cap. 2 — Fundamentação Teórica (`02-fundamentacao.tex`; p. 4–10)

**C2-01** · **Médio** · `02:6`, `:20` (duas vezes), `:82`, `:88` · p. 4, 7
- **Trecho:** "formalizada por [Fama, 1970]"; "Estudos de [Shiller, 2000] e
  [Thaler, 1993] demonstram"; "O modelo de três fatores de [Fama and French,
  1993]"; "Posteriormente, [Fama and French, 2015] expandiram"
- **Problema:** `\citep` usado onde o autor é sujeito da frase; o PDF fica
  com a citação entre colchetes no meio da oração.
- **Correção:** `formalizada por \citet{Fama1970}`;
  `\citet{Shiller2000} e \citet{Thaler1993} documentam que vieses…`;
  `O modelo de três fatores de \citet{FamaFrench1993}`;
  `Posteriormente, \citet{FamaFrench2015} ampliaram o modelo para cinco fatores, acrescentando rentabilidade e investimento.`

**C2-02** · **Alto** · `02:24` · p. 4
- **Trecho:** "Essa perspectiva fornece suporte teórico para o uso de sistemas
  baseados em inteligência artificial e modelos de linguagem, uma vez que
  modelos adaptativos e multiagentes podem capturar padrões dinâmicos e
  interpretar contextos que estratégias estáticas … não conseguem
  identificar."
- **Problema:** salto lógico (a AMH diz que a eficiência varia; não diz que
  LLMs capturam padrões), sem citação, e contrariado pelos próprios
  resultados (as regras estáticas venceram).
- **Correção:**
  > Essa perspectiva motiva, mas não garante, o uso de sistemas adaptativos:
  > se a eficiência varia no tempo, regras fixas podem perder validade entre
  > regimes, e sistemas capazes de reinterpretar o contexto tornam-se
  > candidatos à avaliação empírica \citep{Lo2004}. Se essa capacidade se
  > traduz em desempenho ajustado ao risco é o que este trabalho testa.

**C2-03** · **Médio** · `02:80–88` (Seção 2.4) · p. 7
- **Trecho:** `R_i - R_f = \beta_m (R_m - R_f) + \beta_s SMB + \beta_v HML`
- **Problema:** seção sem uso posterior (FS-1); equação sem α_i e ε_i; SMB e
  HML não definidos.
- **Correção:** cortar a seção (preferível) ou escrever
  `R_{i,t} - R_{f,t} = \alpha_i + \beta_m (R_{m,t} - R_{f,t}) + \beta_s \mathit{SMB}_t + \beta_v \mathit{HML}_t + \varepsilon_{i,t}`,
  definir SMB (*small minus big*) e HML (*high minus low*) e dizer por que o
  trabalho não faz atribuição a fatores.

**C2-04** · **Alto** · capítulo inteiro (estrutura)
- **Problema:** o Cap. 5 decide as hipóteses com bootstrap estacionário,
  erro-padrão do Sharpe e controle de multiplicidade (Holm, interseção-união),
  mas a Fundamentação não tem uma linha sobre inferência. Politis e Romano,
  Holm e Lo (2002) aparecem pela primeira vez no Cap. 5.
- **Correção:** nova seção "Inferência estatística na comparação de
  estratégias" (1 a 1,5 p.): (i) erro amostral do Sharpe e baixo poder em
  janelas curtas \citep{Lo2002}; (ii) dependência serial e bootstrap por
  blocos estacionário \citep{Politis1994}; (iii) mineração de dados e testes
  de habilidade superior \citep{White2000, Hansen2005}; (iv) multiplicidade e
  procedimento de Holm \citep{Holm1979}; (v) opcional, o teste robusto de
  diferença de Sharpe de Ledoit e Wolf (2008), para justificar por que o
  protocolo herdado usa a forma básica não studentizada (verificar e incluir
  no `.bib`).

**C2-05** · **Médio** · `02:116`, `:120` × `03:26`; `02:108,112` × `03:28,33`
· p. 8–9, 13
- **Trecho:** "a acurácia de alinhamento financeiro de modelos gerais de
  ponta se eleva drasticamente, com melhorias reportadas de 63,2% para
  80,5%" (Cap. 2) × "elevou a acurácia de um modelo geral de 63,2% para
  80,5%" (Cap. 3).
- **Problema:** os mesmos trabalhos (FinCoT, Xing, Li 2023, Xia 2026)
  aparecem nos dois capítulos, e a descrição do FinCoT diverge: plural "de
  ponta" e "drasticamente" no Cap. 2, um modelo no Cap. 3. A redação do Cap.
  2 exagera.
- **Correção:** no Cap. 2, manter só os conceitos (personas, debate, CoT) com
  uma citação cada e mover resultados para o Cap. 3. Em `02:120`:
  "\citet{FinCoT2025} propõem guiar o raciocínio por roteiros definidos por
  especialistas (FinCoT), com ganho de acurácia em questões no estilo CFA
  (Seção~3.3)."

**C2-06** · **Médio** · `02:120` · p. 9
- **Trecho:** "Enquanto abordagens de Zero-shot Chain-of-Thought permitem
  respostas mais livres"
- **Problema:** CoT e *zero-shot* CoT sem as referências de origem.
- **Correção:** citar Wei et al. (2022), "Chain-of-Thought Prompting Elicits
  Reasoning in Large Language Models" (NeurIPS), e Kojima et al. (2022),
  "Large Language Models are Zero-Shot Reasoners" (NeurIPS). Conferir os
  dados antes de incluir no `.bib`.

**C2-07** · **Médio** · `02:112` · p. 8
- **Trecho:** "A literatura sobre sistemas multiagentes parte da hipótese de
  que a decomposição do processo decisório em papéis especializados…"
- **Problema:** "a literatura sobre sistemas multiagentes" sem nenhuma obra de
  sistemas multiagentes; a única citação é um artigo de *trading*.
- **Correção:** citar uma obra de referência da área (por exemplo, Wooldridge,
  *An Introduction to MultiAgent Systems*, 2. ed., Wiley, 2009; verificar
  antes de incluir).

**C2-08** · **Médio** · `02:108` · p. 8
- **Trecho:** "Ainda assim, a literatura recente sugere que o ganho potencial
  desses sistemas depende menos do uso isolado de um LLM e mais da forma como
  memória, especialização funcional e mecanismos de verificação são
  organizados"
- **Problema:** "a literatura sugere" sem citação.
- **Correção:** fechar a frase com `\citep{Li2023, Xing2024, TradingAgents2024}`.

**C2-09** · **Médio** · `02:126` · p. 9
- **Trecho:** "Bailey et al. [2017] demonstram que a probabilidade de
  encontrar estratégias aparentemente lucrativas (Probability of Backtest
  Overfitting) aumenta significativamente…"; "resultado puramente
  estatístico"
- **Problema:** definição errada da PBO; "puramente estatístico" é impreciso.
- **Correção:**
  > \citet{Hansen2005} complementa com um teste de habilidade preditiva
  > superior, que evita atribuir ao método um desempenho fruto do acaso.
  > \citet{Bailey2017} definem a probabilidade de sobreajuste do
  > \textit{backtest} (PBO) como a probabilidade de que a configuração
  > escolhida como a melhor dentro da amostra tenha desempenho abaixo da
  > mediana fora dela, e mostram que ela cresce com o número de configurações
  > testadas.

**C2-10** · **Médio** · `02:68–78` · p. 6–7
- **Trecho:** "O RSI busca medir a intensidade dos movimentos recentes…";
  `BB_{upper} = MA + k\sigma`; "A esses indicadores soma-se o MACD"
- **Problema:** o RSI é eixo central da análise de resultados (Tab. 6.5:
  63,17/35,07 → 35,11/68,96), mas não tem fórmula nem janela; as bandas não
  definem n, k nem σ; o MACD não tem fórmula nem citação.
- **Correção:**
  `\mathrm{RSI}_t = 100 - \dfrac{100}{1 + \mathrm{RS}_t}`, com
  `\mathrm{RS}_t` a razão entre as médias de ganhos e de perdas em n = 14
  pregões \citep{Wilder1978} (confirmar a janela em `src/indicators/rsi.py`);
  `\mathrm{BB}^{\pm}_t = \mathrm{SMA}_{20,t} \pm k\,\sigma_{20,t}`, com k = 2
  ("Bollinger 20/2"); `\mathrm{MACD}_t = \mathrm{EMA}_{12,t} - \mathrm{EMA}_{26,t}`,
  sinal = `\mathrm{EMA}_9(\mathrm{MACD})` (confirmar em `macd.py`; buscar
  referência de Appel antes de citar).

**C2-11** · **Baixo** · notação (`02:45,53,71,75,85,95,133`)
- **Trecho:** `MA_t`, `Momentum_t`, `R_{acum}`, `BB_{upper}`, `SMB`, `HML`,
  `w^T \Sigma w`
- **Problema:** nomes de várias letras em itálico matemático (lidos como
  produto M·A); subscritos em inglês; w e Σ sem definição.
- **Correção:** `\mathrm{SMA}_t`, `\mathrm{Mom}_t`, `R_{\text{acum}}`,
  `\mathrm{BB}^{\text{sup}}_t`; após a eq. 2.7: "em que w é o vetor de pesos e
  Σ a matriz de covariância dos retornos".

**C2-12** · **Médio** · `02:101` · p. 7–8
- **Trecho:** "No contexto do mercado acionário brasileiro, pode funcionar como
  um benchmark conservador [Clarke et al., 2006]"
- **Problema:** Clarke et al. estudam o mercado norte-americano (o título diz
  "U.S. Equity Market"). Falta a formulação do problema usada no replay
  ("somente comprados").
- **Correção:**
  > Em ações norte-americanas, a carteira de mínima variância obteve retorno
  > ajustado ao risco competitivo com volatilidade menor
  > \citep{Clarke2006}. Ela resolve
  > $\min_w w^\top \Sigma w$ sujeito a $\mathbf{1}^\top w = 1$ e $w \geq 0$
  > e, neste trabalho, serve como referência conservadora.

**C2-13** · **Médio** · `02:103–104` (2.5.2) · p. 8
- **Trecho:** subseção "Relação Risco-Retorno" com uma frase.
- **Correção:** fundir a frase na abertura de 2.8 e apagar a subseção.

**C2-14** · **Baixo** · `02:18` · a seção 2.1 tem uma única subseção (2.1.1).
Incorporar o texto de 2.1.1 ao corpo de 2.1 ou criar 2.1.1 "Formas de
eficiência" e 2.1.2 "Críticas e AMH".

**C2-15** · **Médio** · `02:28` · p. 5
- **Trecho:** "…seleção de sinais [Markowitz, 1952; Clarke et al., 2006; López
  de Prado, 2018]"
- **Problema:** Markowitz (1952) não sustenta que *benchmarks* simples sejam
  base comparativa.
- **Correção:** `\citep{DeMiguel2009, LopezDePrado2018}`.

**C2-16** · **Baixo** · `02:12` · "semi-forte" → "semiforte" (prefixo "semi"
+ consoante que não seja h, r ou s, pelo Acordo Ortográfico).

**C2-17** · **Baixo (estilo)** · `02:22` "Neste modelo" → "Nessa proposta";
`02:66` e `02:124` "onde" (não locativo) → "em que"; `02:63` "desvio padrão"
→ "desvio-padrão" (como em `02:133`); `02:92` "teoria financeira moderna"
logo após "Teoria Moderna de Portfólio" → "das bases da teoria financeira".

**C2-18** · **Médio** · `02:140` · p. 10
- **Trecho:** "um limite aceitável (MAR)"; "Ambas as métricas são cruciais para
  avaliar a estabilidade do sistema de agentes frente a crises do mercado
  brasileiro."
- **Problema:** acrônimo sem expansão; afirmação forte e sem objeto (não há
  crise no período definida no texto).
- **Correção:** "um retorno mínimo aceitável (\textit{minimum acceptable
  return}, MAR)"; "Ambas complementam o Sharpe ao medir perdas, e não apenas
  variabilidade."

**C2-19** · **Médio** · `02:133–136` · p. 9–10
- **Trecho:** `S = \frac{E[R_p - R_f]}{\sigma_p}`
- **Problema:** o denominador deve ser o desvio do retorno excedente; não se
  menciona anualização nem que o trabalho usa r_f = 0 (Cap. 5).
- **Correção:** `S = \frac{E[R_p - R_f]}{\sigma(R_p - R_f)}` e a frase "Na
  forma diária anualizada usada neste trabalho, com $r_f = 0$, ver
  Equação~\eqref{eq:met-sharpe}."

**C2-20** · **Baixo** · `02:26–34` · títulos e texto usam "Buy and Hold" e
"Equal Weight" como estratégia; o resto da monografia usa "Buy \& Hold" e
"Equal Weight 63d" como carteiras. Definir em 2.2: "estratégia de comprar e
manter (\textit{buy and hold}), referida como Buy \& Hold quando designa a
carteira de referência" (P-04/P-05).

**C2-21** · **Baixo** · `02:116` · `\citep[p. 5, p. 9]{Xing2024}` →
`\citep[p.~5, 9]{Xing2024}`.

**C2-22** · **Médio** · ordem das seções (2.2 antes de 2.5): ver 3.4.

Cap. 2: 34 parágrafos e 3 itens revisados; 21 com problema (9 só de forma).

---

### Cap. 3 — Trabalhos Relacionados (`03-relacionados.tex`; p. 11–18)

Boa revisão: cobre RL, ML, LLMs, SMA, contaminação e deliberação, dialoga
entre autores e termina com quadro comparativo e posicionamento. Achados:

**C3-01** · **Médio** · `03:68–86` (Tabela 3.1) · p. 17
- **Trecho:** cabeçalhos "Multiagente" e "Rastreabilidade das decisões"
- **Problema:** as palavras não cabem nas colunas `p{1.8cm}` e `p{2.0cm}`
  (overfull de 9,4 pt e 21,5 pt) e invadem as vizinhas: o PDF mostra
  "MultiagenteCustos" e "RastreabilidadeReferências". A tabela ocupa a página
  sozinha, com espaço vazio em cima.
- **Correção:** no cabeçalho, `\textbf{Multi\-agente}` e
  `\textbf{Rastrea\-bilidade das decisões}`, ou abreviar
  ("Multiag.", "Rastreab."); se quiser folga, `\begin{table}[p]` com
  `sidewaystable` (pacote `rotating`) em paisagem.

**C3-02** · **Médio** · `03:58` · p. 16
- **Trecho:** `\section{QUADRO COMPARATIVO}` com o float "Tabela 3.1"
- **Problema:** a seção chama de quadro o que o documento numera como tabela.
  Na prática ABNT/IBGE, informação textual é quadro; a classe não tem
  ambiente de quadro.
- **Correção:** renomear a seção para "Comparação com o Hedge-fund-lab"
  (verificar no manual do CEFET/RJ se quadros devem ter numeração própria).

**C3-03** · **Alto** · `03:50` · p. 15
- **Trecho:** "Por isso, o projeto reserva a avaliação confirmatória de agentes
  ao acompanhamento prospectivo e trata o replay retrospectivo como estudo
  exploratório."
- **Problema:** conflita com a decisão inferencial dada à v1 (Tabela 5.1,
  "Principal"; 6.3.2). Ver 3.5.
- **Correção:** "Por isso, o projeto trata o \textit{replay} como evidência
  retrospectiva: a v1, pré-especificada, recebe decisão inferencial
  condicionada à possível contaminação; v2 e v3 são exploratórias; e a
  avaliação livre de contaminação fica reservada ao acompanhamento
  prospectivo."

**C3-04** · **Alto** · `03:50`; também `05:26`, `05:194`, `05:205`, `07:47`
· p. 15, 37, 45, 46, 67
- **Trecho:** "O corte de conhecimento declarado pelo provedor é anterior ao
  período do replay"; "(março de 2026)"
- **Problema:** o fato que define o início do período (06/04/2026, "posterior
  ao corte") e sustenta toda a discussão de contaminação não tem fonte; só
  relatórios internos o repetem.
- **Correção:** nota de rodapé ou referência à documentação oficial do modelo
  (página do `gemini-3.8-flash` no provedor) com "Disponível em: <URL>.
  Acesso em: dd nov. 2026." Usar a mesma fonte para as tarifas de `04:252`.

**C3-05** · **Médio** · `03:92` e linha da Tabela 3.1 (`03:84`) · p. 16–17
- **Trecho:** "As diferenças do Hedge-fund-lab estão … na contabilização
  conjunta dos custos de operação e de inferência"; "Sim (0,03% e custo de
  inferência)"
- **Problema:** `05:32` diz que o custo de inferência "é contabilizado em
  orçamento separado e não é deduzido do patrimônio". "Conjunta" é falso.
- **Correção:** "na contabilização explícita dos custos de operação,
  deduzidos do patrimônio, e de inferência, registrados por chamada em
  orçamento próprio"; na tabela: "Sim (0,03% no patrimônio; inferência em
  orçamento à parte)".

**C3-06** · **Médio** · `03:92` · p. 16
- **Trecho:** "O controle da contaminação temporal permanece, na melhor das
  hipóteses, parcial em todos os trabalhos com LLMs, inclusive no presente."
- **Problema:** `03:24` relata que Lopez-Lira e Tang avaliam manchetes
  posteriores ao corte de conhecimento, um controle completo (dado o corte).
- **Correção:** "…parcial em todos os trabalhos do quadro, inclusive no
  presente."

**C3-07** · **Médio** · `03:39` · p. 14
- **Trecho:** "(cinco analistas técnicos, um analista de risco e um gestor)"
- **Problema:** lê-se como sete agentes no total; são cinco analistas e um
  analista de risco por ativo e um gestor global (até 31 chamadas por pregão).
- **Correção:** "(por ativo, cinco analistas técnicos e um analista de risco;
  um gestor global para a carteira)".

**C3-08** · **Baixo** · `03:12` "sobreajuste", `03:16` "momento", `03:8`
"índice de Sharpe": alinhar com P-04/P-05.

**C3-09** · **Baixo** · `03:10,26,33,35,54` · DQN, TDQN, PPO, KDJ, CFA, CVaR
e GSM8K sem expansão. Expandir na primeira ocorrência ou declarar (P-03).

**C3-10** · **Médio** · `03:50` · p. 15
- **Trecho:** "o relógio causal garante que cada decisão use apenas dados até o
  fechamento do pregão anterior"
- **Problema:** conceito usado antes de ser definido (Seção 4.8).
- **Correção:** acrescentar `(Seção~\ref{sec:arq-relogio})`.

**C3-11** · **Médio (sugestão)** · Tabela 3.1 · p. 17
- **Problema:** a tabela omite a dimensão que mais diferencia este trabalho:
  pré-especificação e teste estatístico. Também não registra repetições.
- **Correção:** coluna "Inferência e repetições", preenchida só com o que
  consta nos textos citados (FinCon: "mediana de cinco repetições", `03:35`;
  Hedge-fund-lab: "bootstrap estacionário pareado; v1 pré-especificada; uma
  execução por versão"; demais: "—").

**C3-12** · **Baixo** · `03:84` · na linha do Hedge-fund-lab, "pesos iguais,
mínima variância" ao lado de "Buy & Hold, SMA 50/200, Bollinger 20/2" →
"Equal Weight 63d, Mínima Variância 252/63".

**C3-13** · **Médio (sugestão)** · capítulo · só Nelson et al. (2017) trata da
B3. O membro externo tende a perguntar por evidência nacional sobre regras
técnicas ou LLMs no mercado brasileiro. Incluir um ou dois estudos nacionais
verificados (sem inventar; checar em periódicos como Revista Brasileira de
Finanças e Revista Brasileira de Economia).

**C3-14** · **Alto** · `03:4` (abertura do capítulo) · p. 11
- **Trecho:** "Este capítulo revisa a literatura que dialoga diretamente com o
  Hedge-fund-lab, organizada em seis frentes"
- **Problema:** o guia do curso (p. 1 e 9) pede que os trabalhos relacionados
  venham "por meio de um mapa sistemático": string(s) de busca, base(s)
  consultada(s) (Scopus recomendada), critérios de inclusão e exclusão e
  parâmetros de priorização. O capítulo não diz como os trabalhos foram
  encontrados. A tabela comparativa, também pedida, existe (3.7).
- **Correção:** parágrafo de método logo após `03:4`, com os dados reais da
  busca (os autores precisam fornecê-los; não reconstruir de memória): "Os
  trabalhos foram identificados por busca nas bases [Scopus, arXiv, …], com as
  strings [por exemplo, ("large language model" OR LLM) AND (trading OR
  portfolio) AND (agent* OR "multi-agent")], no período [ano–ano], em [data].
  Incluíram-se [critérios] e excluíram-se [critérios]; a priorização considerou
  [aderência ao tema, presença de avaliação empírica, citações].
  Complementaram-se os resultados com as referências clássicas citadas pelos
  trabalhos selecionados."

Cap. 3: 25 parágrafos revisados (mais a tabela); 12 com problema.

---

### Cap. 4 — Arquitetura e Implementação (`04-arquitetura.tex`; p. 19–35)

**C4-01** · **Alto** · capítulo inteiro; `04:4` · p. 19–35
- **Trecho:** "Este capítulo descreve a arquitetura e a implementação do
  Hedge-fund-lab tal como observadas no repositório. O conteúdo foi produzido
  a partir de auditoria do código-fonte … sem reexecução de experimentos."
- **Problema:** os autores descrevem o próprio sistema como auditores
  externos. O capítulo lista arquivos (`04:46,109,360`), identificadores e
  códigos de erro (`04:222,236`), reservas com seis casas (`04:252`), rotas
  (`04:262`) e o processo de publicação de pacotes. São 17 páginas, um quarto
  do texto (3.3).
- **Correção:** reestruturar como em 3.3 e 3.4. Nova abertura:
  > Este capítulo descreve a arquitetura do Hedge-fund-lab: os dados, o livro
  > contábil, a carteira multiagente, o relógio causal, o mecanismo do
  > \textit{replay} e a evolução entre versões. O mapeamento entre componentes
  > e arquivos do repositório está no Apêndice~A.

**C4-02** · **Crítico** (erro factual) · `04:6` · p. 19
- **Trecho:** "O primeiro, de ativo único, é o grafo LangGraph de src/agents,
  utilizado na avaliação H1/H2 sobre PETR4"
- **Problema:** H1 (SMA × Equal Weight) exige mais de um ativo e nunca foi
  avaliada nesse caminho (`MATRIZ_EVIDENCIAS.md` §1); o protocolo de H2 sobre
  PETR4 não teve *Freeze* nem Teste Final (`05:194`).
- **Correção:** "O primeiro, de ativo único, é o grafo LangGraph de
  \texttt{src/agents}, construído para o protocolo confirmatório de H2 sobre
  PETR4 planejado na etapa anterior; suas fases de desenvolvimento foram
  executadas, mas o Teste Final não (Seção~\ref{sec:met-protocolo})."

**C4-03** · **Alto** · `04:40`, `04:364` (também `04:98`)
- **Trecho:** "módulos de src/ que integram a proveniência dos experimentos
  H2"; "sem alterar os gates da avaliação H2"
- **Problema:** "H2" designa duas coisas: o protocolo de ativo único não
  executado e a hipótese respondida pela v1 do replay. A banca confunde.
- **Correção:** chamar o primeiro de "protocolo de ativo único (H2-PETR4)" ou
  "protocolo planejado" em todo o capítulo.

**C4-04** · **Crítico** (erro factual) · `04:72–74` · p. 20
- **Trecho:** "A série de preço científica de referência (H_real) corresponde
  ao ativo PETR4.SA, com 1519 sessões no intervalo de 2018-01-12 a 2024-02-28,
  cobrindo 2649 barras oficiais."; "A versão anterior do calendário apresentava
  divergências…, corrigidas na versão atual."
- **Problema:** o congelamento metodológico
  (`evidence/03-metodo-h2/H2_METHODOLOGICAL_FREEZE_V1.md`, §7 e Amendment 1)
  define três objetos distintos, que a frase funde: (i) o *snapshot* COTAHIST ×
  fator do yfinance, com 2.649 barras = 2.649 sessões oficiais (2016-01 a
  2026-08); (ii) o conjunto elegível `|E|`, com 1.519 sessões de 12/01/2018 a
  28/02/2024, cada uma com ao menos 504 sessões de histórico; (iii) `H_real`,
  apenas **4 sessões** de `|E|`, escolhidas pelos quantis 0,2/0,4/0,6/0,8
  (09/04/2019, 30/06/2020, 17/09/2021 e 07/12/2022) e reservadas ao diagnóstico
  do *Hardening* (H = 8 H_syn + 4 H_real). Chamar `|E|` de `H_real` é erro
  factual; o histórico de correção do calendário não tem valor para a tese; a
  data está em ISO.
- **Correção:** levar o trecho para 5.7.1 ou Apêndice B, assim:
  > A série de PETR4 do protocolo de ativo único vem de um \textit{snapshot}
  > oficial do COTAHIST, ajustado pelo fator do yfinance, com 2.649 barras, uma
  > por sessão oficial de 2016 a agosto de 2026. Dela, 1.519 sessões (de
  > 12/01/2018 a 28/02/2024), cada uma com ao menos 504 sessões de histórico,
  > formam o conjunto elegível de âncoras; quatro dessas sessões, escolhidas
  > por quantis e sem olhar o mercado, compõem o conjunto de diagnóstico
  > \texttt{H\_real}.

  Apagar a frase sobre a versão anterior do calendário.

**C4-05** · **Médio** · `04:44`, `04:77` · p. 20
- **Trecho:** "os fatores de ajuste foram adquiridos depois do período e,
  portanto, não constituem uma representação point-in-time."
- **Problema:** a banca de finanças pergunta se isso vaza informação para os
  sinais. O texto não responde.
- **Correção (se confirmada no código):** "Como as oito \textit{features} são
  razões invariantes à escala (distâncias relativas às médias e às bandas,
  RSI e razões do MACD), um fator de ajuste posterior, que multiplica
  igualmente toda a janela de cálculo, não altera os sinais; só proventos com
  data-com dentro da janela, já conhecidos em $t-1$, modificam a série."
  Confirmar em `features.py` que todas as features são razões e que o fator
  de um evento futuro é uniforme na janela.

**C4-06** · **Médio** · `04:84` · p. 21
- **Trecho:** "são recalculados a cada leitura pela reprodução ordenada dos
  eventos (replay)"
- **Problema:** "replay" também é o nome do experimento.
- **Correção:** "pela reprodução ordenada dos eventos (\textit{event
  sourcing})".

**C4-07** · **Médio** · `04:150` · p. 24
- **Trecho:** "oito features adimensionais (rsi, sma50_gap, sma200_gap,
  bb_upper_gap, bb_lower_gap, bb_width, macd_ratio e macd_signal_ratio)"
- **Problema:** os nomes não bastam para reproduzir; as travas da v3 usam
  limiares sobre essas grandezas (`bb_lower_gap` < 0,035; `sma200_gap` >
  −0,08).
- **Correção:** tabela (no capítulo ou no Apêndice A) "Features entregues aos
  analistas", com nome, fórmula e janela, por exemplo
  `sma50_gap = P_t / \mathrm{SMA}_{50,t} - 1`,
  `bb_width = (\mathrm{BB}^{+} - \mathrm{BB}^{-}) / \mathrm{SMA}_{20}`,
  `macd_ratio = \mathrm{MACD}_t / P_t`, conferidas em
  `src/agents/features.py`.

**C4-08** · **Alto** (argumento que falta) · `04:152` · p. 24
- **Trecho:** "Os analistas recebem apenas as features do ativo: posições da
  carteira e dia-alvo não entram em seus prompts."
- **Problema:** o texto subestima o desenho. O código mostra que o caminho
  científico não envia ticker, data nem preço aos analistas
  (`src/agents/technical_analyst.py:116–126`: "identidade e calendário abrem
  um canal de memorização do modelo"); o analista de risco recebe só sinal,
  features e métricas de risco (`scripts/multiasset_radar.py:601–608`). Só o
  gestor recebe tickers, datas e preços. Isso localiza o canal de
  contaminação e protege as conclusões sobre o comitê (unanimidade, perfil do
  RSI).
- **Correção:** "Os analistas e o analista de risco recebem apenas
  \textit{features} adimensionais: ticker, data e preço não entram em seus
  \textit{prompts}, o que fecha, nessas etapas, o canal de memorização do
  período. Apenas o gestor recebe tickers, datas e preços (Seção 4.7.3)." Usar
  em 5.8 e 6.5 (C5-02).

**C4-09** · **Médio** · `04:146`, `04:152`, 4.9.4 · p. 24, 29–30
- **Trecho:** "temperatura 1,0"; "sementes 10001 a 10005"
- **Problema:** o leitor pode supor que sementes tornam a inferência
  repetível. Não está dito que a reprodução é feita a partir das respostas
  arquivadas.
- **Correção:** ao fim de 4.9.4: "A reprodução dos resultados parte das
  respostas arquivadas no diário de chamadas; uma nova inferência, mesmo com
  as mesmas sementes e temperatura 1,0, não garante respostas idênticas."

**C4-10** · **Médio** · `04:216` · p. 27
- **Trecho:** "Cada operação posterior à entrada paga custo de 0,03% sobre o
  valor bruto"
- **Problema:** o número central de custo não tem justificativa nem fonte.
- **Correção:** dizer de onde vem (por exemplo, "próximo da soma das tarifas
  de negociação e de liquidação da B3 para pessoa física, sem corretagem") e
  citar a tabela de tarifas da B3 com data de acesso (conferir o valor antes).

**C4-11** · **Médio** · `04:217` · p. 27
- **Trecho:** "o JCP é creditado líquido de 15% de imposto"
- **Problema:** o JCP é tributado, mas o ganho de capital não; o tratamento
  tributário é assimétrico e não aparece nas ameaças (5.8) nem nas limitações
  (7.4).
- **Correção:** no item 4: "Não há imposto sobre ganho de capital."; em 5.8 e
  7.4, acrescentar a assimetria e seu efeito (favorece estratégias com mais
  vendas realizadas com lucro).

**C4-12** · **Médio** · `04:113`, Figura 4.2 (`04:132`) · p. 23
- **Trecho:** "só encaminha a decisão ao gestor de portfólio quando o veredito
  consolidado é APROVADO"; aresta "caso contrário" → "fim"
- **Problema:** não se diz qual é a decisão final quando há veto.
- **Correção:** "…caso contrário, a decisão final é MANTER" e rótulo da
  aresta "caso contrário (MANTER)", se for o que `src/agents/graph.py` faz.

**C4-13** · **Médio** · Figura 4.3 (`04:170–204`) · p. 26
- **Trecho:** caixa "Comitê técnico: 5 anal-istas, consenso ≥ 3 de 5";
  `det/.style={box, fill=black!6}`
- **Problema:** quebra feia dentro da caixa (agravada por P-01); 6% de cinza
  some na impressão P&B, e a legenda depende da diferença entre caixas
  sombreadas e brancas.
- **Correção:** `fill=black!15` (ou borda tracejada nas etapas com LLM);
  quebras manuais:
  `Comitê técnico: 5 analistas\\consenso $\geq$ 3 de 5`,
  `Risco do ativo: regra dura ($>$50\% a.a.)\\ou modelo consultivo`.

**C4-14** · **Baixo** · Figura 4.2 (`04:126`, `04:130`) · p. 23 · o nó
`portfolio_manager` deslocado 28 mm à esquerda descentraliza a figura, e o
rótulo inclinado "veredito = APROVADO" quase encosta na caixa do
`risk_manager`. Alinhar `ta → rm → pm` na vertical, pôr "fim" à direita e
posicionar o rótulo com `pos=0.4` ou `above left`.

**C4-15** · **Médio** · `04:74` (+33,5 pt), `04:113` (+11,4 pt), `04:262`
(+6,5 pt) · p. 20, 23, 30
- **Problema:** linhas invadem a margem direita (P-13), visível na p. 20 em
  "b3_-".
- **Correção:** `\path{src/backtesting/b3_calendar.py}`,
  `\path{src/agents/graph.py}`, rotas com `\path{}`; ou retirar os caminhos
  (C4-01).

**C4-16** · **Médio** · caminhos `\texttt` quebrados com hífen (P-07).

**C4-17** · **Alto** · `04:349–355` (Operação Diária) · p. 33–34
- **Trecho:** "Fora do replay, a mesma carteira multiativos é operada
  diariamente sobre dados correntes"
- **Problema:** não diz qual versão está em operação. O código mostra a v1:
  `dashboard/daily_cycle.py:44` importa `wallet_manager_api` (compilador
  estrito original), sem módulos da v2/v3. Isso muda a leitura do resumo
  (C0-01) e de 6.6.
- **Correção:** "O ciclo diário opera a arquitetura da v1 (comitê com
  \textit{prompt} único, veto simétrico e compilador estrito); as regras da v2
  e da v3 existem apenas nos executores do \textit{replay}."

**C4-18** · **Baixo** · `04:215`, `04:351` · "alerta de tese velha" é jargão
sem definição. Definir na primeira ocorrência (por exemplo, "alerta de tese
desatualizada, emitido quando…", conforme o código).

**C4-19** · **Baixo (estilo)** · `04:240` (também `05:29`) · "sem alegação de
execução a mercado" → "registrada como posição inicial, sem simular execução
a mercado".

**C4-20** · **Médio** · `04:252` · p. 29
- **Trecho:** "US$ 0,110592 por chamada de analista ou de risco e US$
  0,159744 por chamada do gestor"; "teto agregado único de US$ 34,78"
- **Problema:** detalhe de implementação sem valor para a tese; o teto não é
  explicado; as tarifas por milhão de *tokens* não têm fonte.
- **Correção:** "Cada campanha tem teto de US$~34,78, autorizado pelos autores
  antes da execução; antes de cada requisição, reserva-se o custo máximo da
  chamada e, ao receber a resposta, contabiliza-se o custo pelos
  \textit{tokens} informados, às tarifas publicadas pelo provedor (fonte e
  data)." Valores por chamada vão para o Apêndice A.

**C4-21** · **Baixo** · `04:254` · "respostas que ecoem a credencial de acesso
interrompem a execução" — detalhe de segurança; cortar.

**C4-22** · **Médio** · `04:258–262` (4.9.5) · p. 30 · exportadores, ZIP,
`publish_replay.py` e rotas. Reduzir a: "Cada campanha é exportada em pacote
selado por \textit{hash} e publicada para consulta somente leitura, com as
curvas, os votos, os pareceres, as operações e as chamadas arquivadas
(Apêndice~C)." Ver também C4-25.

**C4-23** · **Médio** · `04:342` · p. 33
- **Trecho:** "a evolução descrita nesta seção é tratada como iteração de
  engenharia dentro da amostra"
- **Problema:** a frase é correta, mas não dimensiona o ajuste. A v3 acrescenta
  ao menos 17 limiares numéricos novos: 7 constantes da Tabela 4.3 (0,22;
  0,08; 0,45; 8; 0,25; 0,35; 0,12), 5 nas travas (RSI 40 e 62, 0,035, −0,08,
  −0,02), 3 no *Trim-on-Strength* (RSI 63, lucro 2%, peso 14%) e 2 no
  *Dip-Rebalance* (RSI 46, 0,04), além das faixas proibidas escritas nas cinco
  lentes.
- **Correção:** acrescentar: "A v3 introduz ao menos dezessete limiares
  numéricos escolhidos com conhecimento do período (Tabela~4.3 e travas desta
  seção), além das faixas definidas no texto das lentes; esse número dimensiona
  os graus de liberdade da iteração dentro da amostra."

**C4-24** · **Baixo** · `04:366` · título "Frontend e Operação" repete
"Operação" de 4.11 → "Interface de Acompanhamento".

**C4-25** · **Médio** (figura que falta) · 4.13 · p. 35 · a interface é o
produto ("a carteira como tela inicial"), mas não há imagem. Há captura
pronta em `tcc2/evidence/04-replay-abril-novembro/telas/preview-desktop.jpg`
("candidata a figura", segundo o `LEIA-ME`). Proposta em F-4.

**C4-26** · **Baixo** · `04:4` e capítulo · identificadores DP-n (P-08).

**C4-27** · **Baixo** · Tabela 4.1 (`04:14,19`) · "Stack implementado" e
"Tecnologia observada" → "Tecnologias da implementação" e "Tecnologia
utilizada"; acrescentar fonte (P-11).

**C4-28** · **Baixo** · `04:111` · "O método de decisão é o
self-consistency" — citar `\citep{Wang2023}` e dizer que é análogo (instâncias
independentes que votam), não idêntico (amostragem de caminhos de raciocínio).

**C4-29** · **Médio** · `04:100` · p. 22
- **Trecho:** "O Replay Contínuo multiativos não utiliza engine.py"
- **Problema:** o objetivo 2 promete um motor de *backtesting*, mas o
  experimento usa o livro de eventos. A banca pergunta como se sabe que os
  dois concordam.
- **Correção:** citar o teste de paridade, se existir; se não, dizer que a
  contabilidade do replay é validada pelas auditorias de paridade das
  referências e pelos *asserts* de `metricas_replay.py` (Seção 4.9.2), e não
  pelo motor.

**C4-30** · **Baixo** · `04:168` · "o que permite medir o custo de
implementação" — medido em lugar nenhum; cortar ou medir (descritivo).

**C4-31** · **Baixo** · `04:242` · p. 28
- **Trecho:** `\texttt{--references-only}`, impresso como "–references-only"
- **Problema:** com codificação T1, `--` vira travessão também na fonte
  monoespaçada, e a opção de linha de comando sai errada.
- **Correção:** `\texttt{-{}-references-only}`.

Cap. 4: 58 parágrafos e 12 itens revisados; 32 com problema.

---

### Cap. 5 — Metodologia Experimental (`05-metodologia.tex`; p. 36–48)

O capítulo mais forte em rigor: hipóteses operacionalizadas, regra de
decisão completa, multiplicidade tratada (interseção-união e Holm) e ameaças
explícitas.

**C5-01** · **Alto** · `\paragraph` numerado (P-02) · p. 39–47.

**C5-02** · **Crítico** (afirmação refutada pelo próprio texto) · `05:205`;
repetida em `06:191` e `07:47` · p. 46, 61, 67
- **Trecho:** "A contaminação, se existir, favorece a carteira Multiagentes e
  não afeta as referências determinísticas nem, portanto, o contraste de H1."
- **Problema:** o Cap. 3 (`03:46`, p. 14) relata que, dentro da janela de
  treinamento, manchetes anonimizadas superaram as originais (efeito de
  distração), sobretudo em empresas grandes \citep{Glasserman2023}. Os cinco
  ativos são justamente grandes empresas. O conhecimento do período pode
  ajudar (antecipação) ou atrapalhar (distração): a direção líquida não é
  identificável. Um examinador derruba a frase com o Cap. 3 na mão. A segunda
  metade (não afeta referências nem H1) está correta.
- **Correção (`05:205`, trecho final):**
  > Além disso, preços, fatores de ajuste e proventos foram adquiridos depois
  > do período e não constituem um arquivo \textit{point-in-time}. O sentido
  > da contaminação, se existir, é indeterminado: o viés de antecipação
  > favoreceria a carteira Multiagentes, mas o efeito de distração documentado
  > por \citet{Glasserman2023}, mais forte em empresas grandes, pode
  > prejudicá-la. Como analistas e analista de risco não recebem ticker, data
  > nem preço (Seção~4.7.1), esse canal fica restrito ao gestor. A
  > contaminação não afeta as referências determinísticas nem, portanto, o
  > contraste de H1.

  **(`06:191`):** "…O gestor, único papel que recebe tickers, datas e preços,
  é o canal exposto. A contaminação pode favorecer ou prejudicar a carteira
  Multiagentes; não afeta as referências e, portanto, o contraste de H1
  \citep{Glasserman2023, Golchin2024}."
  **(`07:47`):** "…A contaminação, se existir, pode favorecer ou prejudicar a
  carteira Multiagentes; por isso, nem um resultado favorável nem um
  desfavorável do replay constituem evidência prospectiva. As referências
  determinísticas e o contraste de H1 não são afetados."

**C5-03** · **Alto** · `05:205` · "Os analistas técnicos recebem apenas
features adimensionais, sem o dia-alvo" — omite que também não recebem ticker
nem preço, e que o analista de risco também não. Resolvido no texto de C5-02
(evidência em C4-08).

**C5-04** · **Alto** · `05:122`, `05:213` · p. 42, 47
- **Trecho:** "A taxa livre de risco nula é coerente com a contabilidade da
  simulação, na qual o caixa não é remunerado, mas ignora o custo de
  oportunidade de uma taxa de juros positiva."; "O caixa não é remunerado"
- **Problema:** o viés tem direção conhecida e não é declarada. Penaliza as
  carteiras com mais caixa médio (Bollinger 20/2, 49,06%; SMA 50/200, 31,39%;
  v2, 24,69%; v3, 14,94%; v1, 12,98%) em relação às sempre investidas (Buy &
  Hold, Equal Weight e Mínima Variância, abaixo de 1%, Tabela 6.3). Para H1,
  a SMA ficou 1,00 p.p. abaixo da Equal Weight em retorno, com caixa médio
  30,7 p.p. maior: bastaria um CDI acumulado acima de ~3,3% no período (cerca
  de 5,4% a.a., aproximação sem capitalização) para inverter a diferença
  descritiva. Com a Selic de 2026 em patamar bem acima disso (confirmar no
  Banco Central), a leitura descritiva de H1 muda de sinal. A vantagem da
  Bollinger sobre a v3 cresceria.
- **Correção (acrescentar em 5.8, "Custo e execução simplificados"):**
  > A ausência de remuneração do caixa não é neutra: penaliza as carteiras com
  > mais caixa médio (Bollinger 20/2, 49,06\%; SMA 50/200, 31,39\%) em relação
  > às sempre investidas (Buy \& Hold, Equal Weight 63d e Mínima Variância
  > 252/63, abaixo de 1\%). Como o caixa médio da SMA 50/200 supera o da Equal
  > Weight 63d em cerca de 30,7 pontos percentuais, um CDI acumulado acima de
  > aproximadamente 3,3\% no período bastaria para inverter a diferença
  > descritiva de retorno entre as duas (1,00 ponto percentual); o contraste
  > de Sharpe de H1, calculado com $r_f = 0$ e caixa sem rendimento, deve ser
  > lido com essa ressalva.

  Opcional e fora da regra de decisão: uma sensibilidade descritiva com o CDI
  do período (BCB/SGS, série 12) nos retornos e Sharpes.

**C5-05** · **Alto** · `05:194` · p. 45
- **Trecho:** "a Validação chegou a ser executada em caráter provisório e
  descritivo, autorizada apenas pelo autor e sem ratificação acadêmica."
- **Problema:** "o autor" (singular) numa monografia de dois autores; "sem
  ratificação acadêmica" soa como execução à revelia do orientador; os
  resultados provisórios são omitidos, o que pode parecer seletividade.
- **Correção:** "a Validação foi executada em caráter provisório e
  descritivo, sem a aprovação formal prevista no protocolo; seus resultados
  não são usados para decidir as hipóteses e estão registrados em
  \texttt{tcc2/evidence/03-metodo-h2/H2\_V6\_OA1\_VALIDATION\_SCIENTIFIC\_SUMMARY.md}."
  Por transparência, considerar um parágrafo-resumo desses resultados em
  apêndice.

**C5-06** · **Médio** · `05:194` · p. 45
- **Trecho:** "Terceiro, o custo de inferência de três execuções por fase
  sobre janelas anuais."
- **Problema:** frase sem verbo.
- **Correção:** "Terceiro, o custo de inferência de três execuções por fase,
  sobre janelas anuais, excedia o orçamento do projeto."

**C5-07** · **Médio** · `05:79` · p. 39
- **Trecho:** "As regras da v1 foram, portanto, fixadas antes de qualquer
  observação de seu desempenho no replay"; "embora não tenha sido ajustada a
  ele"
- **Problema:** os dois pilotos (06–17/04 e 20/04–05/05) são *replays* da
  mesma arquitetura sobre o período, observados antes da campanha contínua; o
  segundo foi escolhido pela queda observada. "Não tenha sido ajustada" é
  afirmação sem evidência citada.
- **Correção:** "As regras da v1 foram fixadas antes da campanha contínua e
  não foram alteradas após os dois ensaios curtos (06–17/04, escolhido antes
  de medir retorno; e 20/04–05/05, escolhido pela queda observada, como
  estresse exploratório). A pré-especificação refere-se ao \textit{replay}, e
  não ao mercado: a arquitetura foi desenvolvida em 2026, com parte do período
  já transcorrida, e não há registro de ajuste da v1 a ele."

**C5-08** · **Alto** · `05:27` · p. 37
- **Trecho:** "Universo: BBAS3, ITUB4, PETR4, VALE3 e WEGE3, fixo durante todo
  o período"
- **Problema:** não há critério nem data de escolha. O universo foi fixado
  pela DP-07 no documento de direção, antes do replay, mas durante o período
  que ele cobre (confirmar a data). Escolher ações conhecendo parte de sua
  trajetória é ameaça de seleção, e é a primeira pergunta do membro externo.
- **Correção:** "Universo: BBAS3, ITUB4, PETR4, VALE3 e WEGE3, fixado pela
  DP-07 em [data], com o critério de [critério dos autores — por exemplo,
  liquidez e representatividade setorial], antes do \textit{replay}, e mantido
  durante todo o período, inclusive quando a posição em um ativo é zerada." Em
  5.8, novo item "Seleção do universo": a escolha ocorreu durante o período;
  como é comum às seis carteiras, afeta os níveis mais que as comparações
  pareadas, mas pode favorecer regras de reversão se os ativos tiverem
  oscilado sem tendência.

**C5-09** · **Médio** · `05:18` · p. 36
- **Trecho:** "como extensão exploratória autorizada pela DP-37, que reabre a
  DP-31 apenas para essa reconstrução"
- **Problema:** DP-31 só é explicada em `05:194` (p. 45) (P-08).
- **Correção:** "…autorizada pela DP-37, que abre exceção à DP-31 — decisão de
  projeto que restringe a avaliação de agentes ao regime prospectivo — apenas
  para essa reconstrução…"

**C5-10** · **Médio** · `05:16` (também `06:97`) · p. 36
- **Trecho:** "de modo que as diferenças observadas pertencem às regras de
  decisão"
- **Problema:** verbo impróprio e afirmação forte demais para uma execução por
  versão.
- **Correção:** "de modo que as diferenças observadas são atribuíveis às
  regras de decisão, condicionalmente à trajetória e à execução observadas."

**C5-11** · **Médio** · `05:168–170` · p. 43–44
- **Problema:** um parágrafo de uma frase (Politis e Romano) seguido de outro
  de ~330 palavras com três assuntos.
- **Correção:** citar Politis e Romano em `05:151` ("…\textit{bootstrap}
  estacionário temporal pareado \citep{Politis1994}…") e apagar `05:168`;
  dividir `05:170` em (a) adaptação do estimador ("O protocolo original…
  mesma sequência de índices."), (b) intervalo complementar ("Como
  complemento descritivo… bilateral de 90\%.") e (c) limitações ("Duas
  consequências… otimalidade demonstrada.").

**C5-12** · **Baixo (sugestão)** · `05:170` · citar Ledoit e Wolf (2008) como
alternativa robusta (studentizada) e dizer que o trabalho mantém a forma
básica por herança do protocolo (verificar antes de incluir no `.bib`).

**C5-13** · **Médio** · `05:144` · p. 42
- **Trecho:** "Essa medida de turnover difere … da definição do protocolo
  original"
- **Problema:** troca de métrica depois do protocolo; a banca pode ler como
  escolha *a posteriori*.
- **Correção:** acrescentar "A mudança não afeta a decisão sobre as hipóteses,
  pois o giro é critério descritivo."

**C5-14** · **Baixo** · `05:131` · "Esses parâmetros são valores técnicos do
módulo, não política científica congelada." → "Esses parâmetros seguem os
valores padrão da implementação e não fazem parte da regra de decisão."

**C5-15** · **Médio** · `05:219` · p. 48
- **Trecho:** "inferencial restrita aos contrastes pré-especificados e sujeita
  às ameaças acima." (única linha da página)
- **Problema:** página com uma linha, depois de quase uma página inteira de
  texto.
- **Correção:** fundir `05:219` com `05:217` ou encurtar o parágrafo;
  `\enlargethispage{\baselineskip}` na p. 47 como último recurso. A
  reorganização de 5.8 em subseções (P-02) também desloca a quebra.

**C5-16** · **Médio** · Tabela 5.1 (`05:63`, +8,2 pt) e Tabela 5.2 (`05:95`,
+1,9 pt) · p. 38, 41 · larguras somam mais que a mancha (16 cm). Usar
`p{1.8cm} p{4.4cm} p{3.2cm} p{4.4cm}` na 5.1 e `p{2.6cm} p{8.6cm} p{3.4cm}`
na 5.2, ou `\setlength{\tabcolsep}{4pt}`.

**C5-17** · **Baixo** · `05:16`, `05:41` · "TCC1" → "TCC 1" (P-05).

**C5-18** · **Médio** · `05:46` × `05:56` · p. 38
- **Trecho:** "H0: não há diferença estatisticamente significativa" × "hipótese
  nula unilateral Δ ≤ 0"
- **Problema:** o enunciado (bilateral, sobre significância) e a
  operacionalização (unilateral, sobre o parâmetro) não estão ligados.
- **Correção:** após `05:56`: "Na operacionalização, H0 é a hipótese nula
  unilateral $\Delta_{A,B} \leq 0$ de cada contraste, coerente com o enunciado
  de superioridade de H1 e H2."

**C5-19** · **Médio** · `05:200` · p. 46
- **Trecho:** "iniciado em 14/10/2026 com carteiras Multiagentes e Buy & Hold
  de mesma cesta inicial"
- **Problema:** omite a versão da arquitetura e as carteiras SMA e Bollinger
  acrescentadas (6.6).
- **Correção:** "iniciado em 14/10/2026 com a arquitetura da v1, nas carteiras
  Multiagentes e Buy \& Hold, às quais se somaram SMA 50/200 e Bollinger 20/2
  sobre a mesma cesta".

**C5-20** · **Baixo** · `05:219` · "a priori" → `\textit{a priori}`.

**C5-21** · **Médio** · `05:213` · imposto sobre ganho de capital ausente
(C4-11).

**C5-22** · **Médio (sugestão)** · 5.8 inteira · converter as ameaças em
tabela operacional:

| Ameaça | Sentido provável do viés | Resultados afetados |
|---|---|---|
| Contaminação do modelo | indeterminado (antecipação × distração); canal só no gestor | v1, v2, v3; não H1 |
| Ajuste dentro da amostra | favorece v2 e v3 | v2, v3 |
| Execução única, temperatura 1,0 | indeterminado | v1, v2, v3 |
| Caixa sem remuneração | penaliza carteiras com caixa (Bollinger, SMA, v2) | H1 (descritivo), Bollinger × v3 |
| Custo só proporcional, sem custo fixo | favorece muitas ordens pequenas | v3, v1 |
| Sem imposto sobre ganho de capital | favorece quem realiza lucro | v3, Bollinger |
| Cesta inicial imposta | aproxima Equal Weight do Buy & Hold | H1 |
| Seleção do universo durante o período | indeterminado | todas (níveis) |

**C5-23** · **Baixo** · `05:113` · overfull de 13,3 pt na p. 41
("src/backtesting/metrics.py. O cálculo…") → `\path{}` (P-07).

**C5-24** · **Baixo** · `05:188` · "autoridades não cumulativas", "CAL-A",
"CAL-B", "pseudo-\textit{live}" sem definição. Definir em meia linha cada ou
explicar com a linha do tempo F-1.

**C5-25** · **Crítico** (erro factual) · `05:188` · p. 45
- **Trecho:** "A série de desenvolvimento (H_real) tinha 1519 sessões, de
  12/01/2018 a 28/02/2024."
- **Problema:** o mesmo erro de C4-04: 1.519 sessões são o conjunto elegível
  `|E|`; `H_real` são 4 sessões reservadas ao *Hardening*
  (`H2_METHODOLOGICAL_FREEZE_V1.md` §7).
- **Correção:** "O conjunto elegível de âncoras tinha 1.519 sessões, de
  12/01/2018 a 28/02/2024, cada uma com ao menos 504 sessões de histórico; o
  diagnóstico do \textit{Hardening} usava 8 estados sintéticos e 4 sessões
  reais (\texttt{H\_real}), excluídas dos demais conjuntos." Corrigir também
  `MATRIZ_EVIDENCIAS.md:33`, provável origem do erro.

Cap. 5: 43 parágrafos e 21 itens revisados; 20 com problema.

---

### Cap. 6 — Resultados e Discussão (`06-resultados.tex` e `tabelas/`; p. 49–63)

Todos os números do replay batem com as fontes (3.7). Achados:

**C6-01** · **Crítico** (divergência numérica de apresentação) · `06:206` ·
p. 63
- **Trecho:** "sua trajetória, de R$ 99.835,33 em 14/10 para R$ 82.391,17 em
  16/11 (−17,61%)"; "terminou em R$ 76.059,11 (−23,94%)"
- **Problema:** os percentuais usam o capital inicial (R$ 100.000,00) como
  base, mas a frase apresenta R$ 99.835,33 como ponto de partida. Quem refaz a
  conta a partir do texto obtém −17,47% e −23,82%. Os valores em reais batem
  com `equity_diario.csv`.
- **Correção:** "…de R\$~99.835,33 no fechamento de 14/10 para R\$~82.391,17
  em 16/11, perda de 17,61\% sobre o capital inicial de R\$~100.000,00
  (17,47\% desde o primeiro fechamento)…"; "…e terminou em R\$~76.059,11
  (−23,94\% sobre o capital inicial)."

**C6-02** · **Crítico** (erro factual interno) · `06:175` · p. 60
- **Trecho:** "PETR4 (+R$ 3.222,19), WEGE3 (+R$ 1.991,89) e ITUB4 (+R$
  1.435,82) passaram a resultado positivo"
- **Problema:** `06:156` afirma que, na v2, PETR4 "foi o único ativo sem saída
  total e o único com resultado positivo". PETR4 não "passou" a positivo na
  v3.
- **Correção:** "WEGE3 (+R\$~1.991,89) e ITUB4 (+R\$~1.435,82) passaram a
  resultado positivo, e PETR4 permaneceu positivo (+R\$~3.222,19); WEGE3 e
  ITUB4 respondem por…"

**C6-03** · **Alto** · `06:184` · p. 61
- **Trecho:** "Quarto, a comparação entre v1, v2 e v3 indica que, em um comitê
  de instâncias do mesmo modelo, o número de agentes importa menos que a
  diferença entre as funções atribuídas a eles"
- **Problema:** o número de agentes foi mantido em cinco por ativo nas três
  versões; o desenho não testa o efeito do número.
- **Correção:** "Quarto, mantido o número de agentes, a diversidade efetiva do
  comitê dependeu da diferenciação das funções atribuídas a eles: sementes
  distintas não produziram diversidade, e lentes duplicadas formaram blocos de
  voto que reproduziram o viés do bloco majoritário."

**C6-04** · **Alto** · `06:177` (também `07:36`) · p. 60, 66
- **Trecho:** "a governança determinística moldou o resultado tanto quanto os
  sinais."
- **Problema:** quantifica ("tanto quanto") o que o desenho, sem ablação, não
  mede (o próprio `05:211` diz que a contribuição de cada pilar não é
  identificável).
- **Correção:** "a governança determinística também moldou o resultado: 80
  ajustes, 56 deles limitando vendas, alteraram a proposta bruta do gestor. O
  desenho, sem ablação, não permite medir quanto do ganho se deve a ela e
  quanto aos sinais." Em `07:36`, mesma troca.

**C6-05** · **Médio** · `06:52` · p. 52
- **Trecho:** "Apenas duas carteiras tiveram retorno positivo, ambas com
  perfil de compra em fraqueza e venda em força"
- **Problema:** põe a v3 (+0,07%; Sharpe 0,09 com erro-padrão 1,28) ao lado
  da Bollinger (+4,89%); a v3 terminou no zero a zero.
- **Correção:** "Apenas a Bollinger 20/2 teve retorno claramente positivo
  (+4,89\%); a v3 terminou praticamente no zero a zero (+0,07\%). Ambas compram
  em fraqueza e vendem em força (Seção~\ref{sec:res-v3})."

**C6-06** · **Médio** · `06:58` · p. 52
- **Trecho:** "a Bollinger 20/2 manteve em média 49,06% do patrimônio em
  caixa, a SMA 50/200 terminou com 39,29% e a v2, com 45,86%"
- **Problema:** compara média com valor final na mesma frase.
- **Correção:** "Em média, a Bollinger 20/2 manteve 49,06\% do patrimônio em
  caixa e a SMA 50/200, 31,39\%; nas três versões da Multiagentes, o caixa
  médio ficou entre 12,98\% e 24,69\%. Buy \& Hold, Equal Weight 63d e Mínima
  Variância 252/63 permaneceram investidas (caixa médio abaixo de 1\%)."

**C6-07** · **Alto** (discussão que falta) · 6.2 e 6.5 · p. 50–62
- **Problema:** num período de queda (Buy & Hold −11,21%), a exposição média
  explica parte da ordenação, e o texto não discute isso. A Bollinger, com
  metade do patrimônio em caixa, perderia menos mesmo sem acerto de timing;
  a v3, com 85% investido em média, ficou 11,28 p.p. acima do Buy & Hold, o
  que aponta para o perfil de execução e os proventos, e não para menor
  exposição. Soma-se o viés do caixa sem remuneração (C5-04).
- **Correção (novo item em 6.5, "O que os resultados não permitem afirmar"):**
  > \textbf{Exposição ao mercado.} Em um período de queda, a exposição média
  > explica parte da ordenação: a Bollinger 20/2 manteve, em média, metade do
  > patrimônio em caixa, o que, por si só, atenuaria a perda do Buy \& Hold.
  > Já a v3 manteve em média 85\% do patrimônio investido e, ainda assim,
  > terminou 11,28 pontos percentuais acima do Buy \& Hold, diferença associada
  > à inversão do perfil de execução e à captura dos proventos
  > (Seção~\ref{sec:res-v3}). A ausência de remuneração do caixa
  > (Seção~\ref{sec:met-ameacas}) penaliza as carteiras com mais caixa, o que
  > tende a subestimar a vantagem da Bollinger 20/2.

**C6-08** · **Médio** · `06:44` · p. 50–51
- **Trecho:** "As Figuras 6.1 e 6.2 mostram as curvas de patrimônio e de
  drawdown."
- **Problema:** as figuras são citadas, mas não interpretadas; o texto só
  repete números das tabelas.
- **Correção:** 2 ou 3 frases com o que as curvas mostram e as tabelas não,
  por exemplo: "Na Figura~\ref{fig:replay-patrimonio}, a v1 se afasta das
  referências a partir de meados de abril e atinge o vale em 12/08; a v3 fica
  acima do Buy \& Hold durante quase todo o período; e o recuo de outubro,
  entre 05/10 e 05/11, atinge todas as carteiras investidas." Conferir a
  leitura visual antes de colar (as datas vêm da Tabela 6.2).

**C6-09** · **Médio** · Figura 6.1 (`figures/replay-patrimonio.tex`) · p. 51
- **Problema:** oito séries; as cinco referências são cinza com padrões
  parecidos (fina sólida, traço-ponto, marcadores a cada 15 pontos). Em P&B,
  Buy & Hold, SMA e Equal Weight se confundem.
- **Correção (no gerador `scripts/metricas_replay.py`):** dois painéis — (a)
  v1, v2, v3 e Buy & Hold; (b) as cinco referências — ou destacar v1, v3,
  Buy & Hold e Bollinger e deixar as demais em cinza claro sem legenda;
  `mark repeat=8`.

**C6-10** · **Baixo** · Figuras 6.1–6.3 · rótulos "ago" e "nov" do eixo x
ficam mais altos que os outros. Acrescentar ao `axis`:
`xticklabel style={text height=1.5ex, text depth=0.25ex}`.

**C6-11** · **Médio** · figuras sem fonte (P-11).

**C6-12** · **Médio** · Tabela 6.4 (`tabelas/bootstrap-replay.tex:14–30`) ·
p. 53
- **Trecho:** "MA v1 vs Buy & Hold"
- **Problema:** "MA" não é definido e colide com "MA" = média móvel (eq. 2.1).
- **Correção (no gerador `scripts/bootstrap_replay.py`):** "v1 vs Buy \&
  Hold" (a coluna "Hipótese" já diz que é a carteira Multiagentes) ou
  "Multiag. v1".

**C6-13** · **Médio** · Tabelas 6.2–6.4 (`\resizebox{\textwidth}`) · p. 50,
53
- **Problema:** o encolhimento deixa as três tabelas com corpo menor que as
  demais (~7 pt); "MDD" não é definido.
- **Correção (no gerador):** tirar `\resizebox`; usar `\small`,
  `\setlength{\tabcolsep}{3pt}` e cabeçalhos curtos ("Ret.\ (\%)", "Ret.\
  a.a.\ (\%)", "Vol.\ a.a.\ (\%)"); na legenda: "MDD: \textit{drawdown}
  máximo".

**C6-14** · **Médio** · Tabela 6.1 (`06:25–36`), overfull de 25,5 pt · p. 49
- **Problema:** a tabela passa ~0,9 cm da margem direita.
- **Correção:** cabeçalhos curtos: `\textbf{Ativo} & \textbf{02/04 (R\$)} &
  \textbf{12/11 (R\$)} & \textbf{Var. (\%)}`, e "preço de entrada em 02/04"
  na legenda.

**C6-15** · **Médio** · quebra entre "R$" e valor (P-06).

**C6-16** · **Baixo** · `06:152` · "cerca de R$ 827,34" — "cerca de" com
centavos → "R\$~827,34".

**C6-17** · **Baixo** · `06:195` · "Cada campanha realizou cerca de 4.703
chamadas lógicas" → "As campanhas realizaram 4.703 (v1), 4.702 (v2) e 4.703
(v3) chamadas lógicas" (documento mestre, tabela de orçamento). Opcional:
custo em reais como fração do capital, para dar escala.

**C6-18** · **Baixo** · `06:175` · "ficou abaixo do Buy & Hold (−R$
4.255,30)" → "ficou abaixo do resultado do Buy \& Hold nesse ativo
(−R\$~4.255,30)".

**C6-19** · **Baixo** · `06:184` · "patrimônio final R$ 17.888,65 acima da
linha de base" → "acima da v1" (o Buy & Hold também é chamado de linha de
base).

**C6-20** · **Baixo** · `06:171` · "PETR4 (R$ 43,18 para R$ 46,43)" →
"PETR4 (compra a R\$~43,18; venda a R\$~46,43)".

**C6-21** · **Médio** · `06:204` · p. 62–63
- **Trecho:** "O ciclo diário autônomo (DP-34) … foi adotado a partir de
  20/10/2026."
- **Problema:** não diz como as decisões de 14 a 19/10 foram aprovadas nem que
  a arquitetura é a da v1.
- **Correção:** "Entre 14 e 19/10, as propostas foram aprovadas manualmente na
  interface; a partir de 20/10, pelo ciclo autônomo; nos dois casos, com a
  arquitetura da v1." (confirmar nos registros diários).

**C6-22** · **Baixo (estilo)** · `06:13` · o parágrafo de organização repete
o da Introdução; pode ficar com uma frase.

**C6-23** · **Baixo** · 6.5 · fechar o laço com 2.6 (FS-5): "As lentes da v3,
com faixas em que certos sinais são proibidos, são uma forma de raciocínio
estruturado por critérios de domínio, na linha de \citet{FinCoT2025}, e de
heterogeneidade de papéis \citep{Xing2024}."

**C6-24** · **Baixo** · `06:132` · "descartou a hipótese de ativo esquecido"
→ "descartou a possibilidade de algum ativo ter deixado de ser analisado".

**C6-25** · **Médio** · `06:73` · p. 54
- **Trecho:** "a menor volatilidade da SMA aprofundou seu Sharpe negativo"
- **Problema:** não diz por que a volatilidade é menor (31,39% de caixa médio)
  nem a ressalva do caixa sem remuneração.
- **Correção:** acrescentar: "A menor volatilidade decorre, em boa parte, do
  caixa médio de 31,39\%, que no \textit{replay} não rende juros
  (Seção~\ref{sec:met-ameacas})."

Cap. 6: 38 parágrafos e 17 itens revisados; 16 com problema.

---

### Cap. 7 — Conclusão (`07-conclusao.tex`; p. 64–68)

Responde H1, H2 e H0 de forma explícita, com números corretos, e trata as
versões exploratórias com o cuidado certo.

**C7-01** · **Crítico** · `07:47` · direção da contaminação (C5-02).

**C7-02** · **Médio** · `07:18` · p. 64–65
- **Trecho:** "métrica primária e regra de decisão fixadas antes do replay"
- **Problema:** a métrica e o Bootstrap A são anteriores; o mapeamento de H1
  em SMA × Equal Weight e a família de cinco contrastes de H2 com Holm foram
  definidos na redação, depois do replay (`05:75`, `05:178`).
- **Correção:** "…métrica primária e regra de decisão herdadas do protocolo
  anterior ao \textit{replay} (o mapeamento das hipóteses nos contrastes foi
  definido na redação, sem seleção entre alternativas; Seção~\ref{sec:met-hipoteses})…"

**C7-03** · **Médio** · `07:30` · p. 66
- **Trecho:** "Nesta trajetória, portanto, o comportamento da carteira
  multiagente dependeu fortemente da composição do comitê e das regras
  determinísticas"
- **Problema:** com uma execução por versão e temperatura 1,0, a diferença de
  patrimônio inclui a variabilidade entre execuções; os indicadores de
  comportamento são evidência mais forte.
- **Correção:** "…dependeu fortemente da composição do comitê e das regras
  determinísticas, como indicam a queda da unanimidade (83,01\% → 4,03\%) e a
  inversão do perfil de execução; a diferença de patrimônio (R\$~17.888,65)
  inclui, além das intervenções, a variabilidade de uma única execução por
  versão."

**C7-04** · **Alto** (estrutura) · 7.1–7.2
- **Problema:** os seis objetivos específicos (`01:16–23`) não são fechados um
  a um. O guia do curso (p. 13) pede justamente isso: comparar o que era
  desejado nos objetivos com o que foi alcançado, dizer como e explicar o que
  não foi.
- **Correção:** parágrafo em 7.1: "Os objetivos específicos foram atendidos:
  (1) o \textit{pipeline} sobre o COTAHIST, com fator de ajuste e calendário
  próprio (Seção~4.2); (2) o motor de \textit{backtesting} e o livro de eventos
  (Seções~4.3 e 4.5), este último usado no \textit{replay}; (3) os dois
  caminhos multiagentes (Seções~4.6 e 4.7); (4) o desenho pareado com relógio
  causal e regra de decisão (Cap.~5); (5) o \textit{replay} nas três versões
  (Cap.~6); e (6) o acompanhamento prospectivo, em curso desde 14/10/2026 com
  a arquitetura da v1 (Seção~6.6)."

**C7-05** · **Médio** · `07:44–54` · p. 67
- **Problema:** faltam limitações que o texto já reconhece ou deveria
  reconhecer: seleção do universo durante o período; viés do caixa sem
  remuneração (com direção); imposto sobre ganho de capital; múltiplas
  comparações e graus de liberdade da v3; fatores de ajuste não
  *point-in-time*; acompanhamento prospectivo só com a arquitetura v1.
- **Correção:** acrescentar itens curtos, por exemplo "\textbf{Tributação e
  caixa.} O caixa não rende juros, o que penaliza as carteiras com mais caixa,
  e não há imposto sobre ganho de capital, embora o JCP seja tributado."

**C7-06** · **Baixo** · `07:22` · "o maior drawdown máximo entre as seis
carteiras" × `06:80` "entre as oito carteiras" → "oito".

**C7-07** · **Baixo** · `07:51` · "(cerca de US$ 8,63 na v3)" →
"(US\$~8,63 na v3)".

**C7-08** · **Médio** · `07:61` · p. 68
- **Trecho:** "Congelar as regras da v3 … e avaliá-las no acompanhamento diário
  prospectivo"
- **Problema:** não quantifica o horizonte necessário; a banca pergunta
  "quantos pregões?".
- **Correção:** acrescentar: "Estendendo a aproximação de \citet{Lo2002} ao
  contraste entre duas carteiras com correlação $\rho$ e Sharpe diário
  pequeno, o erro-padrão anualizado da diferença é cerca de
  $\sqrt{252 \cdot 2(1-\rho)/n}$; para chegar a 0,5, seriam necessários cerca de
  400 pregões com $\rho = 0{,}8$ e cerca de 1.000 com $\rho = 0{,}5$." A
  extensão ao contraste é a variância da diferença de Sharpes de Jobson e
  Korkie (1981), que deve ser conferida e citada; conferir também as
  correlações observadas no replay.

**C7-09** · **Baixo (estilo)** · `07:6` · meta-texto de abertura; pode cair.

**C7-10** · **Baixo** · `07:71` · "cumpriu o papel de laboratório": dar a
evidência de extensibilidade (v2 e v3 implementadas por vinculação de módulo,
sem editar as fontes seladas, Seção 4.9.1).

Cap. 7: 17 parágrafos e 13 itens revisados; 8 com problema.

---

## 5. Figuras e tabelas

### 5.1 Inventário

| Float | Página | Citado antes? | Interpretado? | Fonte abaixo? | Legível em P&B? | Observação |
|---|---|---|---|---|---|---|
| Tabela 3.1 | 17 | sim (p. 16) | sim | sim | sim | cabeçalhos sobrepostos (C3-01) |
| Tabela 4.1 | 19 | sim | parcial | não | sim | mover para apêndice (C4-01) |
| Figura 4.1 | 21 | sim (p. 20) | não | não | sim | simples; pode virar parte de F-3 |
| Figura 4.2 | 23 | sim | sim | não | sim | descentrada; aresta de veto sem decisão (C4-12, C4-14) |
| Figura 4.3 | 26 | sim (p. 24) | sim | não | **duvidoso** | cinza a 6%; "anal-istas" (C4-13) |
| Tabela 4.2 | 31 | sim | sim | não | sim | boa |
| Tabela 4.3 | 32 | sim | sim | não | sim | identificadores longos; ok para transparência |
| Tabela 5.1 | 38 | sim | sim | não | sim | +8,2 pt (C5-16) |
| Tabela 5.2 | 41 | sim (p. 40) | sim | não | sim | +1,9 pt |
| Tabela 6.1 | 49 | sim | sim | sim | sim | +25,5 pt (C6-14) |
| Tabela 6.2 | 50 | sim | sim | sim | sim | `\resizebox`; "MDD" (C6-13) |
| Tabela 6.3 | 50 | sim | sim | sim | sim | `\resizebox` |
| Figura 6.1 | 51 | sim (p. 50) | **não** | não | **parcial** | 8 séries (C6-08, C6-09) |
| Figura 6.2 | 51 | sim (p. 50, antes da 6.1) | parcial | não | parcial | citada antes da 6.1 (`06:39`) |
| Tabela 6.4 | 53 | sim | sim | sim | sim | "MA v1" (C6-12) |
| Tabela 6.5 | 56 | sim (p. 56) | sim | sim | sim | boa |
| Figura 6.3 | 59 | sim (p. 58) | sim | não | sim | boa |

Capítulos 1, 2, 3 (exceto a tabela), 5 e 7 não têm figura.

### 5.2 Figuras novas propostas

| ID | Capítulo | Título | Conteúdo | Fonte dos dados |
|---|---|---|---|---|
| F-1 | 5 (ou 1) | Linha do tempo do estudo | janelas do protocolo planejado (desenvolvimento 2018–2024; Validação 09/2024–08/2025; Teste Final 09/2025–08/2026), corte declarado do modelo (03/2026), período do replay (06/04–12/11/2026), pilotos (06–17/04; 20/04–05/05), início do acompanhamento prospectivo (14/10), ciclo autônomo (20/10), execuções das campanhas (13, 15 e 16/11) | `05:188–200`, `docs/DIRECAO_DO_PROJETO.md` (DP-37) |
| F-2 | 5 | Desenho experimental do replay | três campanhas × seis carteiras; referências compartilhadas com paridade; famílias de contrastes (H1: SMA × EW; H2-v1: 5 contrastes, inferencial; v2/v3: descritivos); Bootstrap A | Tabela 5.1, 4.9.2 |
| F-3 | 4 | Componentes do Hedge-fund-lab | dados (COTAHIST + fator) → base congelada → comitê/risco/gestor (LLM) → compilador → planejador → livro de eventos → exportação e explorador; ciclo diário em paralelo | 4.1–4.11 (substitui a Tabela 4.1 no corpo) |
| F-4 | 4 | Explorador do replay | captura das curvas e da inspeção de votos e pareceres | `tcc2/evidence/04-replay-abril-novembro/telas/preview-desktop.jpg` |
| F-5 | 6 | Distribuição dos placares do comitê por versão | barras empilhadas: 5–0, 4–1, 3–2, sem consenso (v1: 83,01/9,15/7,84/0; v2: 15,13/8,03/65,66/11,18; v3: 4,03/36,64/45,10/14,23 %) | Tabela 6.5 e texto de 6.4 (4–1 da v1 e da v2 por diferença; conferir em `dados/auditoria-v*`) |
| F-6 | 6 | Perfil de execução por versão | RSI médio das compras e das vendas executadas (v1 60,51/36,06; v2 58,54/40,98; v3 39,26/69,00), em gráfico de halteres | Tabela 6.5 |

Opcional: F-7, contribuição de cada ativo ao resultado de v1, v2, v3 e Buy &
Hold (`dados/auditoria-v3/atribuicao_v1_v2_v3.csv`).

### 5.3 O que sobra, cabe melhor de outra forma ou está órfão

- **Sobra no corpo:** Tabela 4.1 e Figura 4.1 (levar ao apêndice ou fundir
  em F-3).
- **Frase que cabe melhor como tabela:** as ameaças de 5.8 (tabela em C5-22).
- **Arquivos órfãos:** `tcc2/figures/figure.png` (versionado e não usado);
  `tcc2/images/grafo-langgraph.png` e `tcc2/images/pipeline-etl.png` (não
  usados pelo TCC 2, que desenha em TikZ; as cópias do TCC 1 em `referencia/`
  e `source/tcc1/` têm suas próprias pastas `images/`).
- **Comandos sem uso:** `\warn`, `\verify` e `\remarks` (`main.tex:9–11`)
  nunca aparecem nos capítulos; podem sair.

---

## 6. Referências

Todas as 61 chaves citadas existem em `references.bib` e todas as 61 entradas
são citadas: não há órfãs nem chaves duplicadas. O BibTeX dá um aviso (veja
o item 6).

1. **arXiv sem identificador (Alto).** O `.bst` local não imprime `eprint`,
   `url` nem `note`, e a lista mostra apenas "arXiv, 2023.", sem como
   localizar o trabalho: Glasserman2023, Jiang2017, Li2023, FinRL2020,
   LopezLira2023, Schulman2017, Wu2023, Xia2026, TradingAgents2024,
   FinBen2024, Xing2024, StockAgent2024 (12). As notas de FinCoT2025,
   FINSABER2026, Golchin2024, Wang2023 e Li2024 também não aparecem.
   **Correção:** pôr o identificador no campo que o estilo imprime, por
   exemplo `journal = {arXiv preprint arXiv:2309.17322}`, ou acrescentar `doi =
   {10.48550/arXiv.2309.17322}` (o estilo imprime DOI, como no FinCoT). Para
   ABNT, recomenda-se ainda "Disponível em … Acesso em …" (ver item 7).
2. **Maiúsculas perdidas nos títulos (Médio).** O estilo converte títulos de
   artigos para minúsculas; o PDF mostra "the u.s. equity market", "the 1/n
   portfolio strategy", "Tradinggpt", "Finrl", "The statistics of sharpe
   ratios", "Can chatgpt forecast … ? return predictability", "brownian
   motion", "Fincot", "The sharpe ratio", "Bloomberggpt", "When llm agents",
   "Tradingagents", "Finben", "heterogeneous llm agents", "Finmem", "Fincon"
   (16). **Correção:** proteger com chaves: `{U.S.}`, `{1/N}`,
   `{TradingGPT}`, `{FinRL}`, `{Sharpe}`, `{ChatGPT}`, `{Return}`,
   `{Brownian}`, `{FinCoT}`, `{BloombergGPT}`, `{LLM}`, `{TradingAgents}`,
   `{FinBen}`, `{FinMem}`, `{FinCon}`.
3. **Thaler1993 (Médio).** *Advances in Behavioral Finance* é coletânea
   organizada por Thaler: usar `editor = {Thaler, Richard H.}` no lugar de
   `author`. E a frase de `02:20` ("Estudos de … Thaler … demonstram") deve
   tratar a obra como coletânea.
4. **Livros sem local de publicação (Baixo).** Bollinger2001, Harris2003,
   LopezDePrado2018, Shiller2000, SuttonBarto2018, Thaler1993, Wilder1978:
   acrescentar `address` (a ABNT pede "Local: Editora, ano"). Sutton e Barto
   saem como "MIT Press, 2 edition, 2018": usar `edition = {2nd}` ou adaptar
   ao formato ABNT ("2. ed.").
5. **Grafia do autor (Baixo).** "Lopez de Prado" em Bailey2017 e "López de
   Prado" em LopezDePrado2018: padronizar `L{\'o}pez de Prado` e o nome
   completo dos coautores ("Bailey, David H.", "Borwein, Jonathan M.").
6. **Aviso do BibTeX (Baixo).** "can't use both volume and number fields in
   FinMem2024": remover `number` ou passar para `note`.
7. **Faltas (Médio):** Wei et al. (2022) e Kojima et al. (2022) para CoT
   (C2-06); uma obra de sistemas multiagentes (C2-07); documentação do modelo
   e tarifas (C3-04, C4-20); tabela de tarifas da B3 (C4-10). Opcionais:
   Ledoit e Wolf (2008); Sullivan, Timmermann e White (1999), sobre mineração
   de dados em regras técnicas com bootstrap, que conversa diretamente com
   Brock et al. (1992); Jobson e Korkie (1981). Conferir cada uma antes de
   incluir.
8. **Padrão de citação: divergência dentro do material institucional.** A
   classe e o `apalike.bst` do TCC 2 são idênticos aos do modelo distribuído
   com o guia (`tcc2/source/tcc1/`). Eles carregam `natbib` com `square` e
   geram "[Fama, 1970]", "Lo [2004]" e "and" entre dois autores ("[Fama and
   French, 1992]"). O próprio guia, porém, descreve `\cite` produzindo "(Autor
   e Autor 2023)" (p. 4), e a NBR 10520:2023 usa parênteses, sobrenome só com
   a inicial maiúscula e "e" ou ";" em português. Prevalece o modelo; levar a
   divergência ao orientador antes de mexer. Se ele preferir o formato do guia,
   `\setcitestyle{round}` no preâmbulo troca colchetes por parênteses sem tocar
   na classe; o "and" vem do `.bst`.
9. **Formato das referências: mesma divergência.** O `apalike` gera estilo
   norte-americano ("Fama, E. F. and French, K. R.", "pages", "volume … of",
   "In"), enquanto o guia diz que as referências seguem a ABNT e mostra
   "AUTOR, A.; AUTOR, B. **Título do Livro**. Cidade: Editora, 2023." (p. 4 e
   14). Mesma recomendação: decidir com o orientador; sem decisão, o estilo do
   modelo prevalece. Em qualquer caso, os identificadores arXiv (item 1) e os
   locais de editora (item 4) devem entrar.
10. **Diálogo entre autores (eixo 6).** A Fundamentação tem trechos de
    resumo de artigo único: 2.6.1 (só Li et al.), 2.6.2 (só Xing), 2.6.3 (só
    FinCoT). Os Trabalhos Relacionados dialogam bem e terminam com tabela
    comparativa e posicionamento explícito (3.7 e 3.8).

---

## 7. Conformidade CEFET/RJ / ABNT

Regras do curso: guia oficial (`tcc2/source/tcc1/docs/Trabalho de Conclusao
EIC BCC.pdf`), citado pelas páginas impressas. Fontes de apoio às regras ABNT
citadas: NBR 6028:2021, resumo de trabalhos
acadêmicos com 150 a 500 palavras em parágrafo único
([UFPB](https://www.ufpb.br/secretariado/contents/documentos/2021_ABNT6028Resumo.pdf));
NBR 10520:2023, sobrenome em maiúsculas e minúsculas dentro e fora dos
parênteses
([Unifor](https://unifor.br/web/bibliotecaunifor/abnt-nbr-10520-2023-saiba-o-que-mudou-com-a-atualizacao-da-norma-de-citacoes),
[FURB](https://www10.furb.br/arquivos/assets/files/Citacoes-em-documentos.pdf)).

| Item | Situação | Observação |
|---|---|---|
| Capa | OK | gerada pela classe |
| Folha de rosto | OK | "Orientador:" justificado com espaço largo (classe) |
| Ficha catalográfica | **Pendente** | prevista no modelo (guia, página da ficha): solicitar à Biblioteca Central por chamado depois da defesa e das correções e substituir `ficha.pdf`; hoje não há nem o marcador do modelo |
| Folha de aprovação | OK | "Termo de aprovação" da classe |
| Resumo | OK, com ressalva | 265 palavras (guia: até 500), parágrafo único, sem citações; falta a lacuna que o modelo pede (C0-07) |
| Palavras-chave | OK | 5, separadas por ponto; termos em inglês sem itálico (C0-04) |
| Abstract e keywords | OK | 250 palavras, fiel; erro "Undergratuade" vem da classe (C0-05) |
| Lista de figuras | OK, com ressalva | legendas longas (P-12) |
| Lista de tabelas | OK, com ressalva | idem; identificador quebrado com hífen |
| Lista de acrônimos | **Falha** | vazia, com página em branco; o guia (p. 3–4) prevê a lista e o uso de `\gls` na primeira ocorrência (P-03) |
| Sumário | **Falha** | 34 entradas "x.y.0.z" (P-02) |
| Numeração progressiva (NBR 6024) | **Falha** | nível vazio pelo `\paragraph`; seção 2.1 com uma única subseção (C2-14) |
| Títulos descrevem o conteúdo | OK, com ressalvas | "Quadro comparativo" com Tabela (C3-02); "Frontend e Operação" (C4-24) |
| Fonte sob figuras e tabelas | **Inconsistente** | o exemplo do guia não usa linha de fonte; a NBR 14724 usa; hoje metade dos floats tem e metade não (P-11) |
| Posição das legendas | OK | figuras com legenda abaixo e tabelas com legenda acima, como no exemplo do guia (p. 2–3); a NBR 14724 põe a identificação da figura acima, mas prevalece o modelo |
| Margens, espaçamento, fonte | OK | impostos pela classe (3/2/3/2 cm; 1,5; 12 pt) |
| Citações autor-data | **Divergência no material institucional** | a classe gera colchetes e "and"; o guia descreve "(Autor e Autor 2023)" (Seção 6, item 8) |
| Referências | **Divergência no material institucional** | o `.bst` do modelo gera estilo APA; o guia mostra ABNT; arXiv sem identificador é falha em qualquer padrão (Seção 6, itens 1 e 9) |
| Declaração de uso de IA (guia, seção 2.5) | **Falha** | ausente (C1-12) |
| Introdução com lacuna e principais resultados (guia, p. 6) | **Falha** | C1-13 |
| Mapa sistemático nos trabalhos relacionados (guia, p. 9) | **Falha** | sem protocolo de busca (C3-14); a tabela comparativa existe |
| Conclusão objetivo a objetivo (guia, p. 13) | **Falha** | C7-04 |
| Parágrafos com pelo menos três frases (guia, p. 1) | **Falha pontual** | 14 parágrafos de uma frase (P-14) |
| `TODO`, `\warn`, `\verify`, `\remarks`, cor no PDF | OK | nenhum uso. O "TODO" em `02-fundamentacao.tex` é falso positivo: a sequência está dentro de "METODOLÓGICOS" (`02:122`). Comandos definidos e sem uso (`main.tex:9–11`) |
| Hifenização | **Falha** | padrões ingleses no PDF versionado (P-01) |
| Linhas na margem | **Falha** | 10 overfull (P-13) |
| Viúvas e órfãs | **Falha pontual** | p. 48 com uma linha só (C5-15) |
| Página quase vazia antes de float | OK | Tabela 3.1 ocupa página própria com espaço acima (aceitável); fins de capítulo normais |
| Float longe da citação | OK | Tabela 5.2 corta o parágrafo, mas fica na página seguinte |
| Ajustes manuais em `main.tex` | OK | `\renewcommand` dos títulos das listas e do sumário reproduzem o padrão da classe sem defeito visível; `\emergencystretch` não causa espaços estranhos; o `hyphenat [htt]` causa P-07 |
| Agradecimentos, dedicatória | Opcional | ausentes; o guia torna os agradecimentos obrigatórios se houve apoio financeiro (bolsa ou financiamento do projeto) |

---

## 8. Avisos de compilação (`main.log`)

| Aviso | Quantidade | Relevância | Ação |
|---|---|---|---|
| babel: "No hyphenation patterns were preloaded for the language 'Portuguese'" | 1 | **Alta**: hifenização inglesa no PDF inteiro | P-01; no MiKTeX o aviso não aparece |
| `Overfull \hbox` | 10 | **Média**: texto e tabelas na margem | P-13 |
| hyperref: "Difference (3)/(2) between bookmark levels" | 13 | Média: sintoma do `\paragraph` numerado | P-02 |
| babel: "Name 'brazil' is deprecated" | 1 | Baixa: vem da classe (`[brazil]{babel}`) | comunicar ao mantenedor |
| LaTeX Font: "Font shape T1/cmtt/b/n undefined" e variantes | 36 linhas | Baixa: `\texttt` em negrito ou versalete substituído (efeito do `hyphenat [htt]`, que avisa disso) | ignorar ou reduzir `\texttt` em legendas em negrito |
| BibTeX: "can't use both volume and number fields in FinMem2024" | 1 | Baixa | Seção 6, item 6 |
| Referências ou citações indefinidas | 0 | — | — |
| Rótulos duplicados | 0 | — | — |
| `\hfuzz=5pt` e `\hbadness=20000` na classe | — | escondem caixas pouco cheias e excessos menores que 5 pt | ciente |

---

## 9. Perguntas prováveis da banca sem resposta no texto

| # | Quem tende a perguntar | Pergunta | Onde o texto fica devendo |
|---|---|---|---|
| Q-1 | Externo | "Com a Selic em patamar elevado, por que o caixa não rende CDI? Isso não penaliza Bollinger e SMA e muda a leitura de H1?" | 5.5 e 5.8 só dizem "ignora o custo de oportunidade" (C5-04) |
| Q-2 | Externo | "Por que essas cinco ações? Quando e com que critério? Vocês já sabiam como elas se comportaram em 2026?" | sem critério nem data (C5-08) |
| Q-3 | Externo | "O JCP foi tributado e o ganho de capital não. E a isenção de R$ 20 mil mensais em vendas?" | ausente (C4-11) |
| Q-4 | Externo | "A contaminação favorece mesmo os agentes? O trabalho de Glasserman e Lin que vocês citam mostra o contrário em empresas grandes." | contradição interna (C5-02) |
| Q-5 | Interno | "Qual é o corte de conhecimento do modelo e onde isso está documentado?" | sem fonte (C3-04) |
| Q-6 | Orientador | "Se a DP-31 diz que avaliação retrospectiva com o modelo é contaminada, por que H2 é decidida pelo replay? O que o replay permite concluir que o prospectivo não permite?" | resposta espalhada por 5.1, 5.7 e 6.5; falta um parágrafo direto (3.5) |
| Q-7 | Interno | "Se rodarem a v1 de novo com temperatura 1,0, sai o mesmo resultado? Qual a variância entre execuções?" | só diz que não há repetições; não diz que a reprodução é por arquivo (C4-09) |
| Q-8 | Orientador | "Quantos pregões de acompanhamento prospectivo são precisos para ter poder? 23 pregões dizem algo?" | não quantificado (C7-08) |
| Q-9 | Externo | "Quanto da decisão é do LLM e quanto do compilador? Na v3 houve 80 ajustes para 81 operações. O gestor importa?" | não há contagem de propostas aceitas sem ajuste |
| Q-10 | Externo | "A v3 foi desenhada sabendo que a Bollinger ganhou e codifica reversão à média. Por que não comparar com uma Bollinger submetida às mesmas regras de carteira, para isolar o valor do LLM?" | 6.5 admite que a v3 expressa reversão à média; o controle "regras sem LLM" não aparece nem como trabalho futuro |
| Q-11 | Interno | "O motor de *backtesting* do objetivo 2 não roda o replay. Como garantir que livro e motor concordam? Para que serve o motor?" | C4-29 |
| Q-12 | Interno | "Os analistas sabem qual ação estão analisando?" | o código diz que não; o texto não diz (C4-08) |
| Q-13 | Externo | "Os fatores de ajuste adquiridos depois do período vazam informação para os sinais?" | C4-05 |
| Q-14 | Interno | "Quais são os *prompts*? Sem eles, o experimento é reproduzível?" | os *prompts* não estão no texto nem em apêndice; incluir no apêndice ou citar os arquivos com *hash* |
| Q-15 | Orientador | "Por que a Fundamentação não apresenta o método estatístico que decide as hipóteses?" | C2-04 |
| Q-16 | Externo | "0,03% de custo é realista? Corretagem, *spread*, emolumentos? Lote padrão de 100 ações ou mercado fracionário?" | C4-10 |
| Q-17 | Interno | "Quantos testes automatizados o laboratório tem e o que cobrem?" | 4.1 cita pytest e *asserts* sem números; relatar a contagem real |
| Q-18 | Orientador / Interno | "Vocês usaram IA para escrever a monografia? Como e com que verificação?" | sem a declaração que o guia pede (C1-12) |
| Q-19 | Interno | "Como os trabalhos relacionados foram selecionados? Qual string, base e critério?" | sem protocolo de busca (C3-14) |
| Q-20 | Interno | "O que é `H_real`? O texto diz 1.519 sessões, o congelamento diz 4." | erro factual (C4-04, C5-25) |

---

## 10. Plano de correção

| Lote | Conteúdo | Achados | Esforço |
|---|---|---|---|
| **0 — Crítico e defeitos visíveis** | recompilar com hifenização portuguesa e conferir o log; `\paragraph` → `\paragraph*`; lista de acrônimos com `\gls`/`\glsaddall` e acrônimos novos; `R\$~` e `US\$~` globais; `H_real` (`04:72`, `05:188`); PETR4; base dos % no prospectivo; `04:6`; direção da contaminação nos três lugares; "número de agentes"; 10 overfull | P-01, P-02, P-03, P-06, P-13, C4-04, C5-25, C6-01, C6-02, C4-02, C5-02/C7-01, C6-03, C3-01, C6-14, C5-16 | 3–4 h |
| **1 — Alto, rigor, coerência e guia do curso** | vocabulário de estatuto (resumo, Caps. 1, 3, 4, 5, 7); resumo e abstract "já em curso" e lacuna no resumo; declaração de uso de IA; lacuna e resultados na Introdução; protocolo de busca no Cap. 3 (depende dos dados reais da busca); caixa sem remuneração e exposição; universo; fonte do corte; redação da Validação; pré-especificação × pilotos; anonimização dos analistas; "tanto quanto os sinais"; citações na Introdução e contribuição única; fechamento por objetivo; limitações novas; v1 no ciclo diário | 3.5, C0-01, C0-07, C1-12, C1-13, C3-14, C5-04, C6-07, C5-08, C3-04, C5-05, C5-07/C1-06, C4-08, C6-04, C1-01, C1-03, C1-04, C7-04, C7-05, C4-17, C5-19 | 1 a 1,5 dia |
| **2 — Estrutura** | Cap. 4 para ~10–11 p. com Apêndices A, B e C; figuras F-3 e F-4; Cap. 2 reorganizado com a seção de inferência e os conceitos de LLM, sem *factor investing*; F-1 e F-2 no Cap. 5; tabela de ameaças; reordenar 5.7 | C4-01, C4-03 a C4-07, C4-20 a C4-22, C2-03, C2-04, C2-05, C2-22, C5-22, 3.3, 3.4 | 2–3 dias |
| **3 — Referências e citações** | `\citep` → `\citet` (5 lugares); identificadores arXiv (12); chaves de caixa (16); Thaler como editor; locais de editora; FinMem; López de Prado; referências faltantes; decidir o padrão de citação com o orientador e o manual | C2-01, C2-06, C2-07, C2-15, Seção 6 | 3–4 h |
| **4 — Polimento** | estrangeirismos e nomes; notação das equações; frases longas; legendas curtas; fonte sob os floats; legibilidade da Figura 6.1, rótulos do eixo, cinza da Figura 4.3; tabelas sem `\resizebox` e sem "MA" (nos geradores); comandos sem uso e arquivos órfãos; alinhar `METRICAS_REPLAY.md` e `MATRIZ_EVIDENCIAS.md` com o texto | P-04, P-05, P-07 a P-12, P-14, C2-10, C2-11, C4-13, C4-31, C6-09 a C6-13, 3.7, 5.3 | 1 dia |

Ordem sugerida: Lote 0 e Lote 1 antes de qualquer reorganização, porque os
textos novos do Lote 1 já nascem na estrutura que o Lote 2 vai mover; depois
Lote 2, Lote 3 e Lote 4. Recompilar e reler o PDF inteiro ao fim de cada
lote, conferindo no log hifenização, overfull e avisos do hyperref.
