# Pesquisa: munição histórica e de contexto para os agentes

**18/10/2026.**
Vinculada a DP-27 (visão de recortes, indicadores e padrões consultáveis pelos
agentes) e DP-31 (agentes avaliados só de forma prospectiva; munição em fase de
pesquisa documental). Documento de pesquisa: **não implementa nada, não aprova
fonte, gasto nem protocolo**. As decisões ficam com Lucas (seção 6).
[Direção](DIRECAO_DO_PROJETO.md) · [Roadmap](ROADMAP.md) · [Estado atual](ESTADO_ATUAL.md).

## Sumário executivo

1. Recomendo começar pela **munição que já está no disco**: base B3 desde 2000
   (OHLC, preço médio, negócios, volume financeiro), CDI e proventos. Ela vira um
   **resumo determinístico selado por sessão** (opção A), calculado só com dados ≤ t.
2. O resumo entra **primeiro no gestor da carteira**, que já vê ticker e datas. Os cinco
   analistas técnicos continuam cegos (sem ativo e sem data, prompt V5 selado).
3. Todo número de padrão do tipo "5 de 6 vezes" sai com taxa base, n e intervalo de
   Wilson. 5/6 dá IC 95% de [43,6%; 97,0%]: não distingue de moeda honesta.
4. Fontes externas verificadas e abertas (BCB/Copom/Focus/PTAX, IBGE, CVM, TSE,
   Tesouro) ficam para uma fase 2. Cada uma tem semântica de data própria.
5. Avaliação honesta no TCC: braço sombra pareado (mesmo contexto, com e sem resumo),
   com métricas de processo pré-registradas. Superioridade financeira não é
   demonstrável com 5 ativos e semanas de pregões.
6. Restrições reais: o teto acumulado de US$ 5 do gestor (cerca de 31 chamadas
   reservadas) e DP-25/26/28, que hoje proíbem dados Yahoo/Ibovespa como input dos agentes.

## 0. Ponto de partida: o que os agentes recebem hoje

Conferido no código em 18/10/2026.

| Agente | Recebe | Não recebe | Garantias |
|---|---|---|---|
| 5 analistas técnicos (prompt V5, `technical_prompt_v5.py`) | 8 razões adimensionais da sessão t (gaps SMA50/200, Bollinger, MACD/close, RSI) e um vocabulário fechado de evidências | Identidade do ativo, data, nível de preço, qualquer série anterior; o prompt manda "ignore news, external knowledge" | `features.py`: adimensionalidade (nível ajustado vaza proventos futuros) e quantização canônica para o hash do prompt |
| Risco (`multiasset_radar.RISK_PROMPT`) | Consenso, features, volatilidade 21d | Carteira, caixa, eventos | Limite determinístico de volatilidade 0,5 |
| Gestor da carteira (APP-05, `wallet_manager_api.py`) | Carteira (caixa, posições, revisão), **tickers**, **sessão de referência**, **dia-alvo**, preços CLOSE RAW, pareceres, custo declarado | Notícias, macro, histórico além dos pareceres | Contexto selado com `sha256`; `contracts()` congela prompt, schema, config e código; consentimento pago e financeiro separados; teto `root_budget_usd` = US$ 5 **acumulado** |

Garantias de tempo que a munição precisa herdar:

- `input.json` imutável por ativo/sessão, com hash do histórico e do manifesto
  (`multiasset_radar.prepare`).
- Sessão fechada só após 18:00 America/Sao_Paulo (`last_closed`). É o **corte de preparo**.
- `market_base_api.merged(ticker, as_of)` só devolve linhas ≤ as_of. Ressalva já
  marcada no código: o fator de ajuste Yahoo vem do snapshot mais recente, **não é
  as-of** (`series`, comentário `ponytail:`).
- Análises com dia-alvo passado são classificadas `HISTORICAL_REANALYSIS` (DP-22).

Consequência de desenho. Existem **dois tipos de munição**:

- **Anônima e adimensional:** percentil de volatilidade, distância à máxima de 252
  sessões, z-score de volume. Não revela ativo nem data e poderia, numa versão
  futura do prompt técnico, ir aos analistas.
- **Identificada ou de calendário:** "eleição em 12 sessões", "Copom amanhã", "VALE3
  publicou ITR". Revela data e ativo, logo só cabe no gestor.

Restrições já aceitas que pesam aqui:

- DP-25 e DP-26: o acervo Yahoo "não substitui dados congelados dos agentes" e
  "não vira input dos agentes".
- DP-28: o Ibovespa entra "sem marcar patrimônio nem alimentar agentes".
- "Fora do foco imediato" inclui notícias/sentimento e novos ativos.

Usar Ibovespa, Brent ou S&P na munição exige, portanto, **decisão explícita** (seção 6).

## 1. Inventário de tópicos rastreáveis

**Regra de disponibilidade proposta.** Um dado entra no resumo da sessão t somente
se o seu **instante de publicação** for anterior ao corte de preparo (18:00 de t).
Quando a fonte só informa a data, sem horário, vale publicação ≤ t−1. Em estatísticas
de janela de evento, o "dia 0" é a primeira sessão após a publicação. Na operação
prospectiva, gravar também o nosso `acquired_at`, como já faz a base B3 (DP-27).

**Legenda:** V = verificado por sondagem em 18/10/2026; P = verificado em parte;
S = suposição (conhecimento prévio, não sondado nesta pesquisa).

### 1.1 Tabela de fontes

| # | Tópico | Fonte e acesso | Profundidade / granularidade | Data de referência × publicação | Revisão | Termos / custo | Esforço | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | Decisões Copom e meta Selic | [BCB `historicotaxasjuros`](https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros) (JSON) | Reunião 1 (26/06/1996) até a 281 (16/09/2026), 289 registros; por reunião | `DataReuniaoCopom` = 2º dia; anúncio após o pregão (~18h30, S); `DataInicioVigencia` = dia seguinte. Dia 0 de mercado = sessão seguinte à reunião | Não revisa | Dados abertos BCB, gratuito | Baixo | V |
| 2 | Atas do Copom | [BCB `copom/atas`](https://www.bcb.gov.br/api/servico/sitebcb/copom/atas?quantidade=2) | Desde a reunião 21; texto em página | `dataReferencia` = reunião; `dataPublicacao` cerca de 6 dias depois (281: 16/09 → 22/09) | Não | Aberto | Baixo (metadados); alto se ler o texto | V |
| 3 | Calendário futuro do Copom | Página do BCB | Anual, publicado com antecedência | Agendado: conhecível desde a publicação do calendário | Raro | Aberto | Baixo (manual) | S |
| 4 | Selic diária, câmbio, IPCA no SGS | [BCB SGS](https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=01/10/2026&dataFinal=17/10/2026) (séries 11, 432, 1, 433…) | Diária ou mensal, décadas | Varia por série; o CDI (SGS 12) do dia d só sai no dia útil seguinte (ESTADO_ATUAL, 17/10) | Raríssima | [ODbL](https://dadosabertos.bcb.gov.br/) | Baixo (reusar `reference_rates_api`) | P: SGS 12 respondeu 200 e já está na base; depois de uma rajada de sondagens a API passou a devolver a página "Requisição inválida". **Limitar a taxa de requisições.** IDs das outras séries: S |
| 5 | IPCA (e IPCA-15) | [IBGE SIDRA t/1737](https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/63/p/last%202); IPCA-15 na tabela 3065 (S) | Mensal; IPCA desde 1979 (S) | Mês m publicado por volta do dia 10 de m+1, às 9h (S). Sondagem: setembro/2026 = 0,82% já publicado | Não revisa o índice | Aberto IBGE | Baixo | V (série); S (horário) |
| 6 | Calendário de divulgações IBGE | [IBGE calendário API](https://servicodados.ibge.gov.br/api/v3/calendario/?qtd=3) | 2.432 itens, inclusive datas futuras, com `data_divulgacao` dd/mm/aaaa hh:mm | Agendado: conhecível na publicação do calendário | Datas podem mudar | Aberto | Baixo | V (endpoint geral); o filtro por produto `ipca` voltou vazio |
| 7 | Focus: expectativas | [BCB Olinda Expectativas](https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?%24top=2&%24format=json) | Desde 30/04/1999; semanal (anuais, mensais, Top5) | `Data` = sexta da coleta (última: 09/10/2026); relatório sai na segunda seguinte, logo **disponível em `Data` + 1 dia útil** | Não | ODbL | Baixo | V (profundidade e semântica de `Data`); horário de segunda: S |
| 8 | PTAX | [BCB Olinda PTAX](https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/) | Diária, décadas (S) | `dataHoraCotacao` com instante (~13:04 do mesmo dia) | Não | ODbL | Baixo | V |
| 9 | Curva de juros (proxy) | [Tesouro Direto: preços e taxas](https://www.tesourotransparente.gov.br/ckan/dataset/taxas-dos-titulos-ofertados-pelo-tesouro-direto) (CSV) | Por título e vencimento; desde 2002 (S) | "Taxa Compra/Venda **Manhã**" da `Data Base` D; arquivo atualizado em D+1 às 10:34 (sondagem). Conservador: usar D ≤ t−1 | Não | ODbL | Médio (montar vértices) | V |
| 10 | Curva DI × pré B3 / DI1 | Taxas referenciais B3 (`www2.bmf.com.br`) | Diária, desde os anos 2000 (S) | Fechamento do dia | Não | Termos B3 | Médio | **Não verificado**: o host não respondeu |
| 11 | Eleições: calendário | Constituição: 1º domingo de outubro e último domingo de outubro | Bienal (federal/estadual de 4 em 4 anos) | Conhecível com anos de antecedência | — | — | Trivial (tabela manual) | S (regra constitucional) |
| 12 | Eleições: resultados e totalização | [TSE dados abertos, `resultados-2022`](https://dadosabertos.tse.jus.br/dataset/resultados-2022); "Histórico de totalização Presidente" | Por pleito; a totalização tem **carimbo de data/hora por lote** | 2º turno 2022: 98% das seções às **19:42:08 de 30/10/2022** (Lula 59,0 mi × Bolsonaro 57,2 mi); 100% à 00:18 de 31/10. Dia 0 de mercado = 31/10/2022 | Não | CC-BY | Baixo | V |
| 13 | Grandes eventos fiscais (arcabouço, PECs, meta) | Sem fonte estruturada; Congresso/Tesouro em texto | Pontual | Rótulo frequentemente ex-post (ver seção 2) | — | — | Alto (curadoria) | S |
| 14 | ITR/DFP: datas e números | [CVM dados abertos ITR](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/) / [DFP](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/) | ITR desde 2011, DFP desde 2010; trimestral | `DT_REFER` = fim do trimestre; `DT_RECEB` = **só data**, sem hora (VALE 2T26: v1 e v2 em 30/07, v3 em 31/07; PETR 1T26: 11/05) | **Sim**: o índice lista todas as versões, mas os arquivos de demonstrações trazem **só a última** (VALE 2T26 só v3). O "PENÚLTIMO" exercício pode vir reapresentado | [ODbL](https://dados.cvm.gov.br/) | Médio | V |
| 15 | Fatos relevantes, comunicados, projeções | [CVM IPE](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/) | Desde 2003; por documento, com categoria, assunto e link | `Data_Entrega` só data; `Versao` > 1 em 3.480 linhas de 2026. Fatos relevantes de 2026 até 18/10: PETR 19, VALE 13, BBAS 9, ITUB 6, WEG 0. Exemplo: VALE "Modificação de Projeções Divulgadas" em 23/02/2026 | Reapresentações versionadas | ODbL | Baixo (metadados); alto (conteúdo, que é quase notícia) | V |
| 16 | Calendário de eventos corporativos | CVM IPE, categoria "Calendário de Eventos Corporativos" | Anual por companhia | Datas **agendadas** de ITR/DFP/AGO. WEG: calendário 2026 entregue em 24/02/2026 (v2) | Reapresentável | ODbL | Baixo | V |
| 17 | Proventos | Base local `dividends_api` (B3) | Cerca de 12 meses | `approved_on` (anúncio) = conhecível; `data_com`; `payment_date` | Snapshots selados | Já em uso | Zero | V (local) |
| 18 | Proventos com histórico longo | Outro endpoint B3 (sem data de pagamento, ESTADO_ATUAL) ou IPE "Aviso aos Acionistas" | Anos | Anúncio pela entrega na CVM | — | — | Médio | S |
| 19 | Negociação de administradores (art. 11) | CVM IPE, categoria "Valores Mobiliários negociados e detidos" | Mensal; 7.359 entregas em 2026 | Defasagem de semanas | — | ODbL | Médio | V (categoria) |
| 20 | Brent | Yahoo `BZ=F` | Desde 30/07/2007; diária | Fechamento ICE em Londres, antes do fim do pregão B3 (S) | Contrato contínuo com rolagem | Termos Yahoo (uso pessoal); DP-25/26/28 | Baixo (reusar `stock_history_api`) | V |
| 21 | Minério de ferro | Yahoo `TIO=F` **parado desde 11/08/2021**; alternativa FRED `PIORECRUSDM` (FMI, mensal) | — | Mensal, com defasagem de semanas (S) | Pode revisar | FRED: chave grátis para a API (S) | Médio | V (Yahoo parado); FRED **não verificado** (tempo esgotado) |
| 22 | S&P 500, VIX, juro de 10 anos dos EUA, USD/BRL | Yahoo `^GSPC` (desde 1928), `^VIX` (desde 1990), `^TNX`, `BRL=X` (desde 12/2003) | Diária | Fechamento NY 16:00 ET = 17:00 BRT no horário de verão dos EUA e **18:00 BRT** fora dele, exatamente no corte. Conservador: usar t−1 | Raro | Termos Yahoo; DP-28 | Baixo | V (profundidade); horários S |
| 23 | Microestrutura própria | Base local COTAHIST (`market_base_api.parse`) | Desde 2000; diária: OHLC, preço médio, negócios, quantidade, volume financeiro | Fechamento de t, público após o pregão | Conflitos marcados (`conflict`) | B3, uso local (DP-27) | **Zero de fonte** | V (local) |
| 24 | Ibovespa | Yahoo `^BVSP` local | Desde 1993 | Fechamento de t | Yahoo reescreve | DP-28 veta alimentar agentes | Zero | V (local) |
| 25 | Estatísticas de padrões e sazonalidade | Derivadas de 23 | Desde 2000 | Calculadas as-of | — | — | Médio (o difícil é a estatística) | — |
| 26 | Setor/pares | Dentro do universo: ITUB4 e BBAS3 (bancos), PETR4, VALE3, WEGE3 | Desde 2000 | As-of | — | — | Baixo | — |
| 27 | Pares fora do universo (BBDC4, PRIO3…) | COTAHIST já baixado traz todos os papéis | Desde 2000 | As-of | — | B3 local | Baixo, mas é "novo ativo" como dado | S |

### 1.2 O que importa em cada grupo

**Macro e monetário.** É o grupo com melhor semântica de tempo. Copom, PTAX e Focus
trazem a data do fato e uma regra de publicação estável. Detalhes que mudam a regra:

- A decisão do Copom sai depois do fechamento, logo afeta a sessão seguinte.
- O Focus com `Data` sexta só existe na segunda.
- O CDI do dia d só é publicado em d+1.
- O IPCA tem calendário oficial, então o evento "IPCA amanhã" é conhecível.

Valor esperado para os agentes:

- Distância ao próximo Copom.
- Surpresa da decisão em relação à mediana do Focus da semana anterior. É o número
  macro mais informativo e totalmente causal.
- Variação da expectativa de Selic no Focus.

**Fiscal e político.** Datas de eleição são as mais limpas do projeto: fixadas pela
Constituição e com resultado carimbado pelo TSE. Eventos fiscais não têm fonte
estruturada, e o próprio nome do evento costuma nascer depois. Por isso, fora da
fase inicial.

**Companhia.** A CVM resolve as datas (ITR/DFP, fato relevante, calendário anual),
mas só com **granularidade de dia**. Pontos de atenção:

- **Números contábeis sofrem reapresentação.** O arquivo de dados guarda só a última
  versão, então reconstruir "o que se sabia em t" exige guardar snapshots a partir de
  agora ou aceitar viés de reapresentação no passado.
- **Conteúdo de fatos relevantes é texto, próximo de notícia** ("Fora do foco").
  Recomendo usar só metadados: categoria, data e assunto.

**Commodities e global.** Úteis para VALE3 e PETR4, mas todos dependem do Yahoo (termos
de uso pessoal, DP-28) ou do FRED (não verificado aqui). O minério de ferro diário não
tem fonte gratuita confirmada. Prioridade baixa.

**Microestrutura e padrões.** Já estão no disco, com as-of garantido por `merged()`.
Exemplos de sinais:

- Volume financeiro e número de negócios em z-score contra 60 sessões.
- Gap de abertura contra o fechamento anterior.
- Amplitude (high−low)/close.
- Regime de volatilidade em percentil histórico do próprio ativo.
- Drawdown desde o pico.
- Distância às máximas e mínimas de N sessões.

Custo de fonte zero, nenhuma licença nova, nenhuma decisão de DP reaberta.

## 2. Recortes temporais e eventos

### 2.1 Representação

Cada evento é um registro imutável, selado como os demais. Campos:

| Campo | Significado |
|---|---|
| `id`, `nome`, `classe` | Ex.: `ELEICAO_2022_2T`, classe `AGENDADO` |
| `ativos` | Universo afetado (todos, ou um ticker) |
| `inicio`, `fim` | Período coberto. Para evento pontual, `fim` = `inicio` |
| `conhecivel_desde` | Instante em que **a existência e a data** do evento eram públicas (calendário) |
| `ocorrido_em` | Instante do fato (ex.: 19:42:08 de 30/10/2022) |
| `dia0_mercado` | Primeira sessão B3 que podia reagir |
| `rotulo_conhecivel_desde` | Instante em que **o nome/classificação** passou a existir |
| `fonte`, `url`, `sha256`, `rotulador`, `versao` | Proveniência. Quem rotulou (fonte oficial, regra mecânica ou Lucas) e quando |

Classes e regra de uso pelos agentes:

| Classe | Exemplo | Conhecível quando | Pode entrar no resumo de t? |
|---|---|---|---|
| **Agendado** | Eleições 2022 (02/10 e 30/10), Copom 282, ITR VALE 3T26 pelo calendário CVM, IPCA de outubro | Desde a publicação do calendário; a eleição, anos antes | **Sim**, inclusive como evento futuro ("em k sessões") |
| **Observado pontual** | Resultado do 2º turno 2022, decisão do Copom 281, fato relevante | No instante da publicação | Sim, se publicado antes do corte de t |
| **Regime mecânico as-of** | "Drawdown > 20% desde o pico de 252 sessões", "volatilidade 21d acima do percentil 90 histórico" | Em cada t, pela regra | Sim. Só o **início** e a duração até t, nunca o fim |
| **Rótulo narrativo ex-post** | "Crise da Covid", "Joesley Day", "bear market 2015–16" | Datas e nomes fixados depois; o fim de uma crise só se sabe meses depois | **Não** como input. Só como lente de análise no texto do TCC |

Notas:

- "Joesley Day" ilustra a armadilha. O fato se tornou público na noite de 17/05/2017 e
  o pregão de 18/05/2017 acionou circuit breaker. O nome, porém, foi dado depois, e
  nada no dia anterior permitia anunciá-lo. Datas conforme registro público
  amplamente citado, **não verificadas nesta pesquisa**.
- Um regime mecânico substitui a "crise" sem hindsight: diz "em queda de 34% desde o
  pico, há 18 sessões", mas não sabe que o fundo foi no dia seguinte.

### 2.2 Uso pelos agentes

O resumo traz três blocos curtos por ativo:

1. **Calendário à frente** (só agendados):
   - "Copom 282 em 3 sessões."
   - "Data-com JCP ITUB4 em 5 sessões (anunciado em …)."
   - "1º turno em 12 sessões."
2. **Eventos recentes observados**, publicados antes do corte:
   - "Fato relevante VALE3 entregue em t−2 (assunto: …)."
   - "Copom reduziu a Selic em 0,25 p.p.; a mediana Focus esperava −0,25."
3. **Estatística da classe do evento**, sempre com n e intervalo:
   - "Nos 6 pleitos presidenciais 2002–2022, o retorno de 10 sessões após o 2º turno
     foi positivo em k de 6 [IC …]; taxa base de janelas de 10 sessões: …%."

Com a base desde 2000, há no máximo 6 eleições presidenciais e cerca de 200 reuniões
do Copom. A estatística eleitoral é **descritiva por construção**. A do Copom tem
amostra razoável.

## 3. Estatística de padrões ("5 de 6 vezes")

### 3.1 Definições precisas (sem elas, "linha X" não é testável)

**Linha** L_t, calculada só com dados até t−1. Opções pré-declaradas:

- Máxima ou mínima de N sessões.
- Pivô de topo confirmado após k sessões. O pivô só existe k sessões depois, e essa
  defasagem é obrigatória.
- Média móvel de N sessões.
- Número redondo.

**Toque** em t, com tolerância ε e versão "primeira aproximação":

- `high_t ≥ L_t·(1−ε)` e `high_{t−1} < L_{t−1}·(1−ε)`.
- Usar máxima intradiária ou fechamento é escolha declarada. A máxima conta toques
  que o fechamento não confirma.

**Reação** ("começa a cair"): retorno de fechamento a fechamento de t a t+h abaixo de
zero, ou abaixo de −c·σ_21. Horizonte h fixo, por exemplo 10 sessões.

**Independência:** depois de um toque, ignorar novos toques por um intervalo
(cooldown) ≥ h. Sem isso, um mesmo episódio conta várias vezes e o n é inflado.

**Taxa base** p₀: frequência do mesmo desfecho em **todas** as janelas de h sessões
do mesmo ativo e período. Quedas de 10 sessões acontecem por volta de 45–50% das vezes
(S, a medir). O que interessa é o *lift* p̂/p₀, não p̂.

### 3.2 Incerteza

O intervalo de Wilson a 95% (z = 1,96) é o adequado para n pequeno:

| Observado | p̂ | Wilson 95% | Leitura |
|---|---|---|---|
| 5 de 6 | 83% | **[43,6%; 97,0%]** | Inclui 50% e a taxa base. P(≥5 de 6 \| p=0,5) = 10,9% |
| 10 de 12 | 83% | [55,2%; 95,3%] | Exclui 50% por pouco, **antes** de corrigir comparações múltiplas |
| 20 de 24 | 83% | [64,2%; 93,3%] | Começa a ser evidência, se pré-registrado |

Para que o limite inferior do Wilson passe de 50%, com p̂ verdadeiro de 70%, são
necessários cerca de 23 eventos independentes. Com 60%, cerca de 95. Em 26 anos de um
ativo, com cooldown de 10 a 20 sessões, padrões de "toque" raramente passam de 30 a 60
eventos.

### 3.3 Mineração de dados

Uma família modesta já é grande:

- 5 ativos × 4 tipos de linha × 3 valores de N × 3 horizontes × 2 tolerâncias = 360 testes.
- A α = 5%, cerca de 18 "padrões significativos" aparecem por acaso.

Pior: um padrão **notado olhando o gráfico** ("VALE3 sempre bate em X") vem de uma
família implícita de tamanho desconhecido (jardim de caminhos que se bifurcam). Regras
propostas:

1. **Família fechada e pré-registrada.** Lista de padrões, parâmetros e desfecho
   decidida antes de olhar resultados. Mudanças geram nova versão, e a anterior é preservada.
2. **Controle de FDR** (Benjamini–Hochberg a 10%) sobre a família inteira. Ou, mais
   simples, exibir tudo e rotular força com base em ICs corrigidos.
3. **Fora da amostra em blocos de tempo.** Descoberta 2000–2015, validação 2016–2022,
   reserva 2023 até a data de registro. O padrão só é "candidato" se sobreviver à validação.
4. **Validação prospectiva.** A partir da data de registro, contar acertos novos.
   É a evidência mais limpa possível neste projeto e combina com DP-31.
5. Um padrão notado por Lucas vira **hipótese datada**. Só os eventos posteriores à
   data em que foi anotado contam como teste.

### 3.4 Cálculo as-of e armadilhas específicas desta base

- **Nível ajustado não é as-of.** `series()` usa o fator Yahoo do snapshot mais
  recente. Uma "linha X" desenhada hoje sobre o preço ajustado de 2015 **não era o
  preço que o mercado via** e muda a cada novo provento.
  - Usar RAW B3 corrigido só por desdobramentos e grupamentos.
  - Ou medir tudo em razões dentro da janela, com a mesma disciplina de `features.py`.
  - Ou escolher o snapshot de fator com `fetched_at` ≤ t (melhoria já anotada no código).
- **Trocas de código e classe:** ITAU4→ITUB4 em 20/05/2009 e WEGE4→WEGE3 em 01/06/2007
  (DP-29). Estatísticas que atravessam a troca devem declarar isso. Liquidez dos anos
  2000 (BBAS3, WEGE) é outra.
- **Sobrevivência:** o universo de 2026 é de sobreviventes, com WEG e VALE como
  vencedoras de longo prazo. Taxas base de alta ficam enviesadas para cima.
- **Linhas com `conflict: true`** ou lacunas: excluir e contar a exclusão.
- **Teste de invariância** (o "check" exigido pelo AGENTS.md). O resumo de t calculado
  com a base cortada em t deve ser **idêntico em bytes** ao calculado com a base
  completa e `as_of = t`. Acrescentar linhas futuras falsas não pode mudar nada.

### 3.5 Exemplo trabalhado (desenho, não resultado)

> **Padrão P-01 (pré-registrado).** "VALE3: primeira aproximação da máxima de 252
> sessões seguida de queda em 10 sessões."
>
> - L_t = máxima RAW, corrigida por desdobramentos, de t−252 a t−1.
> - Toque: `high_t ≥ 0,995·L_t` e sem toque nas 20 sessões anteriores.
> - Desfecho: `close_{t+10} < close_t`.
> - Taxa base: fração de todas as janelas de 10 sessões com queda, no mesmo período.
> - Descoberta 2000–2015, validação 2016–2022, reserva desde 2023.
> - Saída: n, k, p̂, Wilson, p₀, lift, p com correção BH na família e rótulo de força.
>
> Texto que iria ao gestor: "P-01 (VALE3): k de n toques terminaram em queda em 10
> sessões (p̂ …%, IC 95% …–…%); taxa base …%; força: **inconclusiva**; validação
> 2016–2022: k'/n'. Hoje o fechamento está a 1,8% da máxima de 252 sessões."
> Os números ficam em branco de propósito: calculá-los antes de registrar a família
> já seria mineração.

Armadilhas desse exemplo:

- O LLM tende a ler "k de n" como regra. O resumo precisa trazer o rótulo de força
  calculado de forma determinística: "inconclusivo" quando o IC contém p₀.
- Janelas de 10 sessões de toques próximos se sobrepõem, mesmo com cooldown de 20 em
  regimes de alta forte. Isso exige verificação.

## 4. Como os agentes consumiriam a munição

### 4.1 Três arquiteturas

| Critério | **A. Resumo selado por sessão** | **B. Ferramenta sobre API local as-of** | **C. Notas curadas com recuperação** |
|---|---|---|---|
| O que é | Construtor determinístico gera `brief.json` por sessão e ativo no preparo; o hash entra no contexto selado | O modelo chama funções (`stats(ticker, pattern, as_of)`) durante a inferência | Textos escritos (por Lucas ou por modelo) recuperados por similaridade |
| Reprodutibilidade | **Total.** Mesmos bytes, mesmo hash, replay idêntico | Parcial. O caminho de consultas varia (temperatura 1,0); replay exige gravar cada chamada e resposta | Baixa. Depende do índice, do embedding e da redação |
| Auditoria | Brief visível na tela **antes** do consentimento pago | Só depois da inferência | Notas escritas hoje sobre 2022 carregam o desfecho (hindsight no texto) |
| Antecipação | Controlada no construtor (`merged(as_of)`), testável | Controlada no servidor ao fixar `as_of`, mas a superfície é maior | Alta e difícil de testar |
| Custo e latência | +1–2 mil tokens por ativo; uma chamada | Várias idas e voltas por decisão; `max_http_attempts_per_call = 1` e o contrato de saída estruturada atual não suportam laço de ferramentas | Embeddings (novo provedor/gasto) + tokens |
| Encaixe nas portas atuais | Direto: `prepare → seal → preflight → consentimento` | Exige refazer orçamento (número de chamadas desconhecido) e o `CallBank` | Exige provedor novo ("Fora do foco") |
| Esforço | Baixo a médio | Alto | Médio a alto |

**Recomendação: A.**

- B só se justifica se o resumo se mostrar estreito demais, e mesmo então como
  "B congelado": o construtor pré-calcula um cardápio fechado e o modelo escolhe
  itens, sem consultas livres.
- C fica fora: reintroduz notícia e hindsight.

### 4.2 Onde e como entra (opção A)

- **Primeiro destinatário: o gestor da carteira.** Ele já recebe ticker e datas,
  decide quantidades e custa uma chamada por proposta. `prompt_input` ganharia o campo
  `brief`.
- `contracts()` passa a incluir a versão do construtor. Isso muda o contrato e exige
  identidade nova (por exemplo `HFL-WALLET-MANAGER-V2`), preservando a V1.
- **Analistas técnicos: não agora.** O contrato V5 (sem identidade, sem data, sem
  conhecimento externo) é parte da evidência H2 selada. Uma versão futura poderia
  receber **só a munição anônima** (percentis e regimes adimensionais) num prompt
  versionado próprio, sem tocar o V5.
- **Formato:**
  - Lista de itens `{id, tipo, enunciado, números, n, ic, taxa_base, as_of, fontes_sha256}`.
  - O prompt manda **citar os `id` usados**, tratar o resumo como dado e não instrução,
    e não afirmar fatos fora dele.
  - Tamanho limitado: `input_bytes_max` = 65.536 bytes no gestor. Alvo de até 2 KB por
    ativo, cerca de 10 KB no total.
- **Custo:**
  - Cerca de 6 mil tokens extras × US$ 0,75/M = US$ 0,005 por chamada (teto de preço:
    US$ 0,009). O custo de tokens é desprezível.
  - O limite real é a **reserva**: cada chamada do gestor reserva cerca de US$ 0,16
    contra o teto **acumulado** de US$ 5 (`used_budget` soma todas as autorizações).
    Isso dá cerca de 31 chamadas ao todo, antes de qualquer A/B.

### 4.3 Contaminação pelo conhecimento do modelo

- **Prospectivo (DP-31) resolve o problema central.** O modelo não conhece o futuro de
  sessões posteriores ao seu treino. Conhecer 2022 não é vazamento quando a decisão é
  de 2026: é contexto legítimo.
- **Reanálises históricas (DP-22) são o ponto fraco.** Com resumo, ticker e data
  passada, o modelo pode "lembrar" o desfecho. Proposta:
  - Sem resumo em `HISTORICAL_REANALYSIS`.
  - Ou com resumo, mas marcadas **não avaliáveis** e excluídas de qualquer métrica.
- **Memória não auditável.** Mesmo sem resumo, o gestor já pode trazer narrativas
  memorizadas ("VALE3 sofre com a China"). O resumo melhora a auditoria: troca memória
  difusa por números verificáveis e citáveis. A métrica "afirmações não suportadas"
  (seção 5) mede o resto.
- **Identidade e data no texto aumentam a ativação de memória.** É mais um motivo para
  não dar munição identificada aos analistas cegos.

## 5. Avaliação no TCC

### 5.1 Desenho

**Braço sombra pareado.** Na mesma análise, com o mesmo quórum, carteira e preços, o
gestor é chamado duas vezes:

- **Controle:** contexto atual.
- **Tratamento:** contexto + resumo.

Só a proposta que Lucas aprovar é aplicada à carteira Multiagentes. A outra é
registrada e simulada de forma determinística num livro sombra, sem fill real, como
contrafactual.

Alternativa: uma **terceira carteira** paper ("Multiagentes + munição") com R$ 100 mil.
É mais visível no produto, mas mexe no grupo de comparação (DP-03/10/18) e dobra as
aprovações financeiras.

**Piso de ruído A/A.** Com temperatura 1,0, duas chamadas idênticas já divergem.
Algumas sessões com duas chamadas de **controle** medem essa divergência basal. Sem
ela, qualquer diferença com e sem resumo é ininterpretável.

**Pré-registro.** Documento datado antes da 1ª sessão, com:

- Versões do construtor e do prompt.
- Família de padrões.
- Métricas e horizonte.
- Número de sessões.
- Regra de exclusão (sessão com dado ausente, falha do provedor).
- Regra de parada.

Nada é ajustado no meio do caminho sem nova versão.

### 5.2 Métricas pré-registradas sugeridas

| Métrica | Tipo | Por quê |
|---|---|---|
| Taxa de divergência de ação/quantidade, tratamento × controle, contra o piso A/A | Primária (processo) | Mede se o resumo **muda** decisões além do acaso |
| Taxa de citação de itens do resumo e coerência citação × ação | Processo | Mostra se o gestor usa a munição |
| Afirmações factuais não suportadas pelo contexto (checagem semiautomática por `id`) | Processo/segurança | Contaminação e alucinação |
| Acerto direcional em h = 5 sessões das ações BUY/SELL contra a taxa base, com Wilson | Secundária | Única métrica de resultado com n razoável, ainda pequena |
| Trajetória das duas carteiras (sombra): retorno, giro, custos | Descritiva | Ilustração, nunca prova (DP-09) |
| Custo e latência por sessão | Operacional | Viabilidade |

### 5.3 Realidade do tamanho de amostra

- **20 sessões** (revisão DP-14): 20 decisões pareadas e até 100 decisões
  ativo-sessão por braço, fortemente correlacionadas entre ativos e com horizontes
  sobrepostos.
- **Retorno da carteira.** Supondo desvio-padrão diário de 0,3% para a diferença entre
  as duas carteiras (S; partem da mesma base e diferem só pelas negociações), detectar
  0,05% ao dia (cerca de 13% a.a.) com 80% de poder e α = 5% exige
  n ≈ (2,8·0,3/0,05)² ≈ **280 sessões**, mais de um ano. Detectar 0,02% ao dia
  (cerca de 5% a.a.) exige cerca de 1.800 sessões. **Inviável no TCC.**
- **Orçamento.** Com braço sombra e A/A, o teto de US$ 5 rende cerca de 12–15 sessões
  pareadas. É preciso decidir orçamento antes de prometer amostra.

**Afirmações defensáveis:**

- "O resumo mudou X% das decisões contra Y% de divergência basal, IC …"
- "O gestor citou a munição em Z% das propostas; W afirmações não suportadas."
- "O pipeline é causal: o resumo de t é idêntico com e sem dados posteriores (teste)."

**Não defensáveis:** "a munição melhora o retorno", "o padrão P-01 funciona".

## 6. Caminho em fases

| Fase | Entrega | Esforço aproximado | Riscos | Pronto quando |
|---|---|---|---|---|
| **F0** | Este documento + decisões de Lucas + nova DP | Feito / 1 conversa | Escopo crescer antes de qualquer sinal | Decisões 1–9 respondidas |
| **F1 — munição local mínima** | Construtor determinístico `brief` só com a base no disco: regimes de volatilidade e drawdown, z-score de volume/negócios, gaps, distância a máximas/mínimas, proventos agendados (`approved_on`/`data_com`), comparação entre os 5 ativos. 3–5 padrões pré-registrados com Wilson e taxa base. Selado no contexto do gestor V2, exibido antes do consentimento. Um teste de invariância as-of | 2–4 dias de agente | Fator Yahoo não as-of (usar RAW/razões); prompt do gestor muda de identidade | Teste as-of passa; brief ≤ 10 KB; tela mostra o brief; gestor V1 intacto |
| **F2 — calendário de eventos** | Tabela de eventos com `conhecivel_desde`/`dia0_mercado`: Copom (BCB), IPCA (IBGE), Focus, eleições (TSE), calendário e entregas CVM (só metadados). Estatística de janela de evento | 3–5 dias | Limite de taxa do BCB; datas CVM sem hora; reapresentações | Cada evento com fonte, hash e regra de disponibilidade testada |
| **F3 — contexto global** | Brent, S&P, VIX, USD/BRL, curva Tesouro | 2 dias | Termos Yahoo; DP-25/26/28 precisam de exceção; horário NY × corte 18h | Decisão explícita de DP antes de começar |
| **F4 — avaliação** | Pré-registro + braço sombra + A/A por N sessões | Contínuo | Orçamento; ruído; amostra | N sessões cumpridas sem desvio do protocolo |
| Depois, só com sinal | Munição anônima aos analistas (prompt V6 próprio); "B congelado"; fundamentos ITR/DFP com snapshots datados | — | Quebra de comparabilidade com V5 | Resultado de F4 justificar |

**Menor passo valioso: F1 + F4 em paralelo.**

- Nenhuma fonte nova nem DP de dados reaberta.
- Reusa `merged(as_of)`, selos, contexto e consentimentos.
- Responde à pergunta que importa ("o gestor usa e muda decisões com munição
  verificável?") antes de investir em macro e eventos.

## Verificação, limites e incertezas desta pesquisa

Sondagens leves em 18/10/2026, sem gravar nada no repositório. Saídas temporárias
ficaram fora do projeto.

- **Verificados:** Copom (decisões e atas), Focus, PTAX, IBGE (SIDRA e calendário
  geral), CVM (ITR, DFP, IPE e licença), TSE (resultados, totalização e licença),
  Tesouro Direto (taxas e licença), Yahoo (profundidade de `BZ=F`, `^GSPC`, `^VIX`,
  `^TNX`, `BRL=X`; `TIO=F` parado) e licença ODbL do portal BCB.
- **Parcialmente verificado:** SGS. A série 12 respondeu e já está na base; depois de
  uma rajada de sondagens, o host passou a responder com a página de bloqueio.
- **Não verificados:**
  - B3 taxas referenciais DI: host sem resposta.
  - FRED: tempo esgotado.
  - Horários de publicação do IPCA e do Focus.
  - IDs SGS além do 12.
  - Calendário anual do Copom.
  - Endpoint B3 de proventos longos.
- **Não calculado:** nenhum padrão foi medido. Números em 3.2 e 5.3 são aritmética
  sobre hipóteses declaradas.

## Decisões para Lucas

1. **Abordagem.** Aceitar a opção A (resumo determinístico selado por sessão) como
   única nesta etapa, deixando B (ferramentas) e C (notas) para depois de evidência?
2. **Destinatário.** Começar só pelo gestor da carteira (nova identidade, V1
   preservada) e manter os analistas técnicos cegos?
3. **Escopo da F1.** Restringir a primeira munição aos dados já no disco (B3, CDI,
   proventos), sem novas fontes?
4. **Exceção às DP-25/26/28.** Ibovespa, CDI e séries Yahoo podem entrar no resumo
   como **contexto** (não marcação)? Se não, F1 usa só B3 e proventos, e F3 fica bloqueada.
5. **Padrões.** Aprovar a regra: família fechada pré-registrada, sempre com n, Wilson,
   taxa base e rótulo de força; padrões notados no gráfico viram hipóteses datadas,
   testadas só depois.
6. **Avaliação.** Braço sombra pareado (recomendado) ou terceira carteira paper "com
   munição" no grupo de comparação?
7. **Orçamento.** O teto acumulado de US$ 5 do gestor rende cerca de 31 chamadas. Ampliar
   (quanto) para comportar tratamento + controle + A/A por um número pré-definido de
   sessões, ou aceitar cerca de 12–15 sessões pareadas?
8. **Reanálises históricas.** Sem resumo, ou com resumo e excluídas de qualquer métrica?
9. **Fase 2.** Autorizar, quando chegar a hora, coleta local de BCB (Copom, Focus, PTAX,
   SGS com limite de taxa), IBGE, TSE e CVM só com metadados (sem conteúdo de fatos
   relevantes, que é quase notícia)?
10. **Registro.** Registrar as escolhas acima como nova DP (DP-32), atualizando o item
    T4 do plano e o roadmap?
