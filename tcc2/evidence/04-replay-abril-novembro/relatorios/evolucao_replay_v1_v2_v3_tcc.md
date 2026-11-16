# Evolução experimental do Replay Contínuo Abril–Novembro de 2026: v1 → v2 → v3

**Documento mestre para o TCC** · 16/11/2026 · DP-37 / `REPLAY-01`, `REPLAY-02` e `REPLAY-03` (regras de referência DP-36) · material-base de capítulo (`TCC-02/03`).

**Natureza:** reconstrução histórica exploratória, produzida depois do fechamento do período. Os resultados são descritivos e valem para esta trajetória; não constituem evidência prospectiva nem demonstração de superioridade (DP-09, DP-31, DP-37).

[Direção e decisões](../docs/DIRECAO_DO_PROJETO.md) · [Roadmap](../docs/ROADMAP.md) · [Auditoria da v1 e plano da v2](auditoria_posicoes_replay_2026-04_2026-11.md) · [Relatório v2](replay_continuo_v2_2026-04_2026-11.md) · [Relatório v3](replay_continuo_v3_2026-04_2026-11.md)

---

## Resumo

Três gerações de uma mesma carteira multiagente foram executadas sobre a mesma trajetória de mercado: 153 pregões da B3, de 06/04/2026 a 12/11/2026, com cinco ações (BBAS3, ITUB4, PETR4, VALE3, WEGE3), capital inicial de R$ 100.000,00 e cinco carteiras de referência determinísticas idênticas até o centavo nas três campanhas. A topologia de agentes (cinco analistas técnicos, um analista de risco e um gestor, todos em `gemini-3.8-flash`) ficou fixa; variaram os prompts dos analistas, a regra de agregação e de veto, o contexto entregue ao gestor e as regras determinísticas de compilação da proposta.

A linha de base (v1) terminou em R$ 82.178,71 (−17,82%), abaixo das cinco referências. A auditoria dessa campanha isolou cinco achados empíricos, agrupados em quatro gargalos. A v2 corrigiu os gargalos mecânicos e terminou em R$ 85.743,57 (−14,26%; +3,56 p.p.), ainda em último lugar, limitada por viés pró-tendência no comitê, saídas integrais seguidas de recompra mais cara e 45,86% do patrimônio parado em caixa no fechamento. A v3 substituiu os analistas duplicados por cinco especialistas distintos e deu ao gestor memória contábil de posição, piso de posição-núcleo e venda escalonada; terminou em R$ 100.067,36 (+0,07%; +17,89 p.p. sobre a v1 e +14,32 p.p. sobre a v2), acima de quatro das cinco referências e abaixo apenas da Bollinger 20/2.

| Indicador | v1 (`REPLAY-01`) | v2 (`REPLAY-02`) | v3 (`REPLAY-03`) |
|---|---:|---:|---:|
| Patrimônio final (R$) | 82.178,71 | 85.743,57 | 100.067,36 |
| Retorno no período | −17,8213% | −14,2564% | +0,0674% |
| Posição entre as seis carteiras | 6ª | 6ª | 2ª |
| Operações pós-entrada (compras / vendas) | 86 (50 / 36) | 38 (22 / 16) | 81 (29 / 52) |
| Saídas totais (posição zerada) | 9 | 10 | 0 |
| Unanimidade 5-0 no comitê | 83,01% | 15,13% | 4,03% |
| RSI médio nas compras / vendas executadas | 60,51 / 36,06 | 58,54 / 40,98 | 39,26 / 69,00 |
| Ativos com preço médio de venda > compra | 1 de 5 | 1 de 5 | 5 de 5 |
| Caixa no fechamento (% do patrimônio) | 1,64% | 45,86% | 0,75% |
| Eventos de proventos recebidos | 9 de 20 | 9 de 20 | 20 de 20 |
| Exposição de orçamento (US$; teto 34,78) | 8,10799425 | 10,03082025 | 8,62763550 |

O ganho da v3 é um resultado dentro da amostra: as regras foram desenhadas depois de observar as duas campanhas anteriores no mesmo período, cada versão foi executada uma única vez e as intervenções entraram em bloco. A seção 6 trata o que esses números permitem e não permitem afirmar.

---

## 1. Desenho experimental controlado e metodologia

### 1.1 Pergunta e natureza do estudo

A pergunta que organiza as três campanhas é arquitetural: mantidos o modelo, a quantidade de agentes, os dados e as regras de execução, quanto do comportamento de uma carteira multiagente depende da especialização dos analistas e da governança determinística aplicada sobre a proposta do gestor?

O estudo é um replay retrospectivo. A DP-31 estabelece que agentes de IA só são avaliados de forma prospectiva, porque o modelo pode conhecer o desfecho do período; a DP-37 reabre essa regra apenas para este replay exploratório, sem substituir o acompanhamento diário e sem afirmar ausência de contaminação. As campanhas v2 e v3 foram autorizadas por Lucas como extensões da mesma decisão (versões 25 e 26 do documento de direção), com a condição de preservar integralmente as versões anteriores.

### 1.2 Período, universo, capital e cesta inicial

| Elemento | Definição |
|---|---|
| Período | 06/04/2026 a 12/11/2026, 153 pregões da B3, sem reset entre pregões |
| Estados diários | 918 = 153 pregões × 6 carteiras, todos reconciliados nas três campanhas |
| Universo | BBAS3, ITUB4, PETR4, VALE3, WEGE3, fixo mesmo com posição zerada |
| Capital | R$ 100.000,00 independentes por carteira, sem aportes ou retiradas |
| Cesta inicial comum | 855 BBAS3, 461 ITUB4, 415 PETR4, 239 VALE3, 397 WEGE3 |
| Regra da cesta | 20% do capital por ativo, em ações inteiras, ao fechamento de referência de 02/04/2026, com custo zero e sem alegação de execução a mercado |

A cesta inicial é imposta ao experimento e não escolhida pelos agentes. Os preços de referência da entrada e os fechamentos de 12/11 dão o contexto de mercado do período: quatro dos cinco ativos caíram.

| Ativo | Referência de entrada (02/04) | Fechamento final (12/11) | Variação de preço |
|---|---:|---:|---:|
| BBAS3 | R$ 23,39 | R$ 15,48 | −33,82% |
| VALE3 | R$ 83,55 | R$ 63,95 | −23,46% |
| PETR4 | R$ 48,15 | R$ 44,70 | −7,17% |
| ITUB4 | R$ 43,30 | R$ 41,68 | −3,74% |
| WEGE3 | R$ 50,31 | R$ 51,65 | +2,66% |

Fontes: custo médio inicial em `operacoes_v3.csv`; fechamentos de PETR4, ITUB4, BBAS3 e WEGE3 nos relatórios de auditoria e da v2; o de VALE3 foi obtido pela identidade contábil das carteiras Buy & Hold e Multiagentes v3 (as duas resultam em R$ 63,95). A variação é só de preço, sem proventos.

### 1.3 Relógio causal de cada pregão

Cada pregão-alvo `t` usa exclusivamente dados até o fechamento do pregão anterior (`reference_session`). O preflight das versões v2 e v3 recusa qualquer entrada cuja sessão seja igual ou posterior ao dia-alvo (`decision_input_lookahead`).

```text
fechamento de t-1  →  8 features técnicas + volatilidade de 21 dias, por ativo
                   →  5 analistas técnicos por ativo  →  consenso (≥ 3 de 5)
                   →  analista de risco por ativo (regra dura ou LLM consultivo)
                   →  gestor da carteira: uma ação por ativo (BUY / SELL / HOLD)
                   →  compilador determinístico: validação e, em v2/v3, ajuste
abertura de t      →  execução ao OPEN RAW B3, custo de 0,03%
fechamento de t    →  marcação das seis carteiras e crédito de proventos pagos
```

A aprovação é hipotética, às 09:00 do dia-alvo. A abertura usa o preço `PREABE` como aproximação diária, sem microestrutura do leilão, spread, impacto ou liquidação em D+2.

### 1.4 Topologia multiagente fixa: 5 + 1 + 1

| Papel | Chamadas por pregão | Contrato comum às três versões |
|---|---:|---|
| Analistas técnicos | 25 (5 por ativo) | `gemini-3.8-flash`, temperatura 1,0, `thinking_level` baixo, até 8.192 tokens de saída, sementes 10001 a 10005; resposta estruturada com sinal (COMPRA, VENDA ou MANTER), confiança autodeclarada e códigos de evidência; base `TECHNICAL_SYSTEM_PROMPT_V5` |
| Analista de risco | até 5 (1 por ativo) | Regra dura sem chamada ao modelo quando a volatilidade anualizada de 21 dias supera 50% (`HARD_ASSET_VOLATILITY_RULE`, veredito VETADO); caso contrário, parecer consultivo do modelo (`ADVISORY_LLM`), APROVADO ou VETADO |
| Gestor da carteira | 1 | Recebe carteira, preços RAW de referência, pareceres e custo; devolve exatamente uma ação por ativo, com quantidade inteira |

O consenso técnico exige fração mínima de 0,6, ou seja, pelo menos três dos cinco votos no mesmo sinal; sem isso, o sinal encaminhado é MANTER com confiança zero. As oito features são adimensionais: `rsi`, `sma50_gap`, `sma200_gap`, `bb_upper_gap`, `bb_lower_gap`, `bb_width`, `macd_ratio` e `macd_signal_ratio`. Um `bb_upper_gap` negativo indica fechamento abaixo da banda superior; um `bb_lower_gap` positivo, fechamento acima da banda inferior.

O teto teórico é de 31 chamadas por pregão, 4.743 na campanha. As 40 ocorrências da regra dura de volatilidade dispensam a chamada de risco, o que leva a 4.703 chamadas lógicas esperadas: 3.825 técnicas, 725 de risco e 153 do gestor.

A decisão de manter 5 + 1 + 1 nas três versões foi deliberada. O conjunto de features é fechado, de modo que mais analistas tenderiam a repetir leituras; cada dois analistas adicionais custariam 1.530 chamadas a mais na campanha; e a quantidade constante de agentes isola a variável experimental, que passa a ser a composição do comitê e a governança, e não o volume de inferência.

### 1.5 O que ficou constante e o que foi manipulado

| Dimensão | v1 | v2 | v3 |
|---|---|---|---|
| Período, universo, capital, cesta inicial | iguais | iguais | iguais |
| Modelo, temperatura, sementes, quórum 3 de 5 | iguais | iguais | iguais |
| Features de entrada e regra dura de volatilidade | iguais | iguais | iguais |
| Prompt de risco e esquemas de resposta | iguais | iguais | iguais |
| Execução, custos, proventos e orçamento | iguais | iguais | iguais |
| Cinco carteiras de referência | calculadas | paridade exata | paridade exata |
| Prompt dos analistas | um único prompt para os cinco | prompt base + 3 lentes (2 + 2 + 1) | prompt base + 5 lentes distintas |
| Guardas de extremo no consenso | não | não | sim (`ANTI_BOTTOM_SELL_GUARD`, `ANTI_TOP_CHASE_GUARD`) |
| Efeito do veto de risco | VETADO vira MANTER | VETADO bloqueia só compras (R7) | igual à v2 |
| Contexto do gestor | carteira, preços, pareceres | igual à v1 | acrescenta `position_memory` |
| Prompt do gestor | `PROMPT` original | `PROMPT_V2` (4 regras) | `PROMPT_V3` (7 regras) |
| Compilador da proposta | estrito: violação invalida o dia | ajusta e registra (`strict=False`) | ajusta e registra (`strict=False`) |

As versões v2 e v3 são adaptadores isolados (`scripts/continuous_replay_v2.py` e `scripts/continuous_replay_v3.py`) que reutilizam contabilidade, livro, planejador de leilão, transporte e orçamento da v1 por vinculação (`pilot_paper.bind`), sem editar as fontes congeladas. Cada versão tem identidade (`HFL-CONTINUOUS-EXPLORATORY-REPLAY-V1`, `-V2`, `-V3`), raiz de armazenamento e pacote exportado próprios.

### 1.6 Carteiras de referência e paridade

As cinco referências são determinísticas, não chamam modelos e foram concluídas antes de qualquer inferência paga, sob bloqueio de rede (`no_network()`).

| Carteira | Regra | Proventos |
|---|---|---|
| Buy & Hold | Mantém a cesta inicial, sem rebalanceamento (DP-11) | Ficam em caixa, sem reinvestimento |
| SMA 50/200 | Cruzamento de médias de 50 e 200 pregões; parcela independente de 20% do capital por ativo; compra com o saldo da parcela quando zerada e venda integral no sinal de saída (DP-36) | Ficam em caixa |
| Bollinger 20/2 | Bandas de 20 pregões e 2 desvios, com a mesma mecânica de parcelas independentes (DP-36) | Ficam em caixa |
| Equal Weight 63d | Rebalanceia para pesos iguais a cada 63 pregões | Em caixa, fora do capital reinvestível |
| Mínima Variância 252/63 | Janela de 252 retornos, rebalanceamento a cada 63 pregões, somente comprada, otimizador SLSQP com objetivo reescalado | Em caixa, fora do capital reinvestível |

Sinais das regras usam o fechamento B3 multiplicado pelo fator Yahoo da versão congelada; operações e patrimônio usam preços RAW B3; a execução ocorre na abertura do pregão seguinte, sem posição vendida nem alavancagem. A auditoria comparativa confirma igualdade de patrimônio, caixa, recebíveis, custos e posições finais das cinco referências entre v1 e v2 e entre v1 e v3 (`reference_parity_v1_v2` e `reference_parity_v1_v3`, todos verdadeiros). Qualquer diferença entre as três campanhas pertence, portanto, à carteira Multiagentes.

### 1.7 Contabilidade, custos e proventos

- Ações inteiras, sem crédito, sem venda a descoberto e sem frações.
- Custo de 0,03% sobre o valor bruto de cada operação posterior à entrada; não há custo fixo nem lote mínimo de bolsa.
- Proventos seguem a DP-30: direito pela posição na data-com, JCP líquido de 15% de imposto, crédito em caixa somente no pagamento. Entre a data-com e o pagamento o valor aparece como recebível, que compõe o patrimônio mas não o caixa disponível.
- O caixa não é remunerado.
- Patrimônio = posições marcadas a mercado + caixa + recebíveis. A identidade foi reconstruída de forma independente nos 918 estados de cada campanha.

### 1.8 Orçamento, persistência e semântica fail-closed

O teto agregado é único por campanha, US$ 34,78, incluindo retentativas, incerteza e chamadas em voo. Antes de cada requisição HTTP é gravada uma reserva durável (US$ 0,110592 por chamada de analista ou risco e US$ 0,159744 por chamada do gestor). Cada chamada lógica admite no máximo duas tentativas físicas, todas preservadas. O custo conhecido é estimado a partir dos tokens devolvidos pelo provedor, a US$ 0,75 por milhão de tokens de entrada e US$ 3,75 por milhão de tokens de saída e de raciocínio; não é fatura oficial.

Quando o comitê não se completa ou a proposta do gestor não passa na validação, o pregão é registrado como `NO_ANALYSIS`: nenhuma ordem é enviada, as posições vigentes são preservadas, as seis carteiras são marcadas a mercado normalmente e a campanha segue. Nada é fabricado para preencher a lacuna.

### 1.9 Procedimento iterativo

Cada geração seguiu o mesmo ciclo: executar a campanha, auditar por script com verificações por `assert` (hashes dos pacotes, reconstrução de quantidades, caixa, custos e patrimônio), formular o diagnóstico, implementar as intervenções em adaptador isolado, qualificar offline (`tests/check_continuous_replay_v2.py`, `tests/check_continuous_replay_v3.py`), obter autorização de orçamento e executar de novo. As versões anteriores permaneceram intactas, com hashes conferidos a cada nova auditoria.

---

## 2. Linha de base v1 (`REPLAY-01`): R$ 82.178,71, −17,82%

### 2.1 Arquitetura original

Na v1 os cinco analistas recebem o mesmo prompt de sistema (`TECHNICAL_SYSTEM_PROMPT_V5`, versão 5) e os mesmos códigos de evidência; diferem apenas pela semente. A recomendação encaminhada ao gestor é o sinal técnico quando o risco aprova e MANTER quando veta (`scripts/multiasset_radar.py::committee`).

O prompt do gestor declara: "Ativo VETADO: HOLD obrigatório; comprar exige parecer COMPRA; vender exige parecer VENDA". O compilador (`dashboard/wallet_manager_api.py::compile_proposal`) aplica essas regras de forma estrita:

- o universo deve estar completo e sem tickers repetidos;
- HOLD exige quantidade zero;
- BUY exige recomendação COMPRA e risco APROVADO; SELL exige recomendação VENDA e risco APROVADO;
- vendas não podem exceder a posição e o caixa não pode ficar negativo.

Qualquer violação lança erro e invalida o pregão. Não há teto de peso por ativo, valor mínimo por ordem, nem memória do preço médio das posições.

### 2.2 Resultado

A Multiagentes v1 encerrou em R$ 82.178,71 (−17,8213%), R$ 6.612,40 abaixo do Buy & Hold (R$ 88.791,11) e R$ 22.708,34 abaixo da Bollinger 20/2 (R$ 104.887,05), com 86 operações posteriores à entrada (50 compras e 36 vendas), R$ 184,40 de custos e 9 saídas totais. Os 153 pregões foram concluídos sem lacunas, com 4.703 chamadas lógicas.

### 2.3 Os cinco achados empíricos

**Achado 1 — Trava de caixa e impossibilidade de rebalancear ativos em MANTER.** Os cinco ativos foram analisados em todos os pregões (765 pareceres ativo-pregão), o que afasta a hipótese de ativo esquecido. O problema era de financiamento: o caixa livre ficou abaixo de R$ 200 em 69 dos 153 pregões, e o compilador proibia reduzir uma posição cuja recomendação não fosse VENDA. VALE3 foi zerada em 01/07 e permaneceu fora por 94 pregões até o fim da campanha, apesar de 14 recomendações de COMPRA aprovadas pelo risco entre 25/08 e 14/09, todas respondidas com HOLD. ITUB4 ficou zerada por 44 pregões e recebeu 27 recomendações consecutivas de COMPRA (03/09 a 16/10) respondidas com HOLD, com caixa entre R$ 15,26 e R$ 155,12; só voltou em 19/10, quando WEGE3 recebeu parecer de VENDA e liberou caixa.

**Achado 2 — Compra no topo e venda no fundo em quatro dos cinco ativos.** O preço médio das compras posteriores à entrada superou o das vendas em WEGE3 (R$ 47,41 contra R$ 44,79), ITUB4 (R$ 44,07 contra R$ 40,61), VALE3 (R$ 83,46 contra R$ 78,85) e PETR4 (R$ 44,77 contra R$ 42,81). As features médias dos 765 pareceres mostram a causa: o sinal de COMPRA (273 casos) saía com RSI médio de 63,17, preço 7,82% acima da média de 50 pregões e a 2,51% da banda superior; o de VENDA (223 casos) saía com RSI médio de 35,07, preço 8,64% abaixo da média de 50 pregões e a 3,38% da banda inferior. Nas operações executadas, o RSI médio foi 60,51 nas compras e 36,06 nas vendas. O caso mais severo foi WEGE3: o papel subiu no período e rendeu R$ 603,40 ao Buy & Hold e R$ 5.454,99 à Bollinger 20/2, mas a Multiagentes perdeu R$ 5.443,38 em três ciclos de saída e reentrada.

**Achado 3 — Veto de volatilidade bloqueando saídas defensivas.** Houve 41 vetos de risco (25 em BBAS3, 12 em ITUB4 e 4 em PETR4), dos quais 40 pela regra dura de volatilidade e 1 pelo modelo. Em 25 pares ativo-pregão havia consenso técnico de VENDA com posição aberta (12 em BBAS3 e 12 em ITUB4, de 27/10 a 12/11, e 1 em PETR4, em 05/11), mas a conversão de VETADO em MANTER impediu a redução. O controle que deveria conter risco impedia a saída exatamente quando a volatilidade disparava.

**Achado 4 — Concentração extrema e compras residuais.** Em 101 dos 153 pregões (66,01%) a carteira teve apenas dois ativos com peso de pelo menos 2% do patrimônio. Os picos de peso no fechamento foram 77,49% em VALE3 (03/06), 71,40% em PETR4 (30/10) e 66,05% em WEGE3 (06/07). No extremo oposto, a auditoria lista oito compras com valor de referência inferior a R$ 2.000, entre elas 3, 3 e 7 ações de BBAS3 em setembro e 11 ações de WEGE3 em 27/07.

**Achado 5 — Falta de diversidade real no comitê.** Das 765 votações, 635 (83,01%) foram unânimes em 5-0 (237 em COMPRA, 203 em MANTER e 195 em VENDA) e nenhuma ficou sem consenso. Com o mesmo modelo, o mesmo prompt e as mesmas evidências, variar a semente não produziu diversidade: os cinco analistas se comportaram como um único classificador de tendência atrasado.

Um sexto elemento, qualitativo, aparece na auditoria: ao recusar a recompra de uma ação de VALE3, o gestor alegou "custo transacional desproporcional" e "lote", barreiras que o contrato não impõe, e nos mesmos dias comprou três ações de BBAS3. A preferência por tamanho de ordem não seguia regra quantitativa explícita.

### 2.4 Dos achados aos gargalos

| Gargalo | Achados | Causa raiz no contrato da v1 |
|---|---|---|
| 1. Trava de caixa | 1 | Venda só com recomendação VENDA; sem redução de posição sobrealocada em MANTER |
| 2. Concentração e ordens residuais | 4 | Sem teto de peso por ativo e sem valor mínimo por ordem |
| 3. Veto simétrico | 3 | VETADO convertido em MANTER, inclusive para vendas |
| 4. Comitê homogêneo e pró-cíclico | 2 e 5 | Cinco analistas idênticos, variando apenas a semente |

---

## 3. Iteração v2 (`REPLAY-02`): R$ 85.743,57, −14,26%, +3,56 p.p.

### 3.1 Os quatro ajustes

Constantes em `scripts/continuous_replay_v2.py`: `MAX_ASSET_WEIGHT = 0.30`, `MIN_TRADE_BRL = 2000.00`, `TRIM_MIN_WEIGHT_BEFORE = 0.25` e `TRIM_MIN_WEIGHT_AFTER = 0.15`.

**Ajuste 1 — Trim-to-Fund (gargalo 1).** Passa a ser permitida a venda parcial de um ativo com recomendação MANTER ou COMPRA quando três condições se cumprem: peso antes da operação acima de 25% do patrimônio; peso projetado depois da venda de pelo menos 15%, sem zerar; e a cesta contém ao menos uma compra válida (COMPRA com risco APROVADO) ou o ativo já está acima de 30%.

**Ajuste 2 — Teto de 30% e ordem mínima de R$ 2.000 (gargalo 2).** Nenhuma compra pode levar o peso projetado do ativo acima de 30% do patrimônio anterior à operação, e nenhuma compra pode ter valor bruto inferior a R$ 2.000,00. Vendas não têm valor mínimo.

**Ajuste 3 — Risco assimétrico R7 (gargalo 3).** O veredito VETADO passa a bloquear apenas compras. Se o consenso técnico for VENDA, a recomendação continua VENDA mesmo sob veto (`committee_v2`), e o gestor pode reduzir ou zerar a posição.

**Ajuste 4 — Três lentes no comitê (gargalo 4).** Cada analista recebe o prompt base acrescido de uma lente:

| Analistas | Lente | Foco e restrições |
|---|---|---|
| 1 e 2 | `LENTE_TENDENCIA_ESTRUTURAL` | Tendência e momentum (`sma50_gap`, `sma200_gap`, MACD); cautela contra COMPRA com RSI acima de 65 ou `bb_upper_gap` acima de −0,02 |
| 3 e 4 | `LENTE_REVERSAO_BOLLINGER_RSI` | Reversão à média; esticado (RSI > 65 ou `bb_upper_gap` > −0,02) nunca é COMPRA; sobrevendido (RSI < 38 ou `bb_lower_gap` < 0,04) não é VENDA |
| 5 | `LENTE_REGIME_EQUILIBRIO` | Regime de volatilidade e largura das bandas como árbitro entre tendência e osciladores |

Além dos quatro ajustes, o compilador mudou de comportamento: em vez de invalidar o pregão, `compile_proposal_v2(..., strict=False)` reduz ou converte em HOLD as ações que violam as regras e registra cada ajuste com ticker, valores de origem e destino e motivo. Compras são ainda limitadas ao caixa disponível depois das vendas.

### 3.2 Resultado

A Multiagentes v2 encerrou em R$ 85.743,57 (−14,2564%), R$ 3.564,86 acima da v1, com 38 operações (queda de 55,8% no giro) e R$ 119,87 de custos (queda de 35,0%). Continuou R$ 3.047,54 abaixo do Buy & Hold e R$ 19.143,48 abaixo da Bollinger 20/2, e terminou posicionada em apenas dois ativos (455 PETR4 e 490 WEGE3), com R$ 39.321,44 em caixa.

### 3.3 O que a v2 resolveu

| Gargalo | Evidência na v1 | Evidência na v2 | Leitura |
|---|---|---|---|
| 1. Trava de caixa | Nenhuma redução em MANTER; VALE3 fora por 94 pregões | Duas reduções em PETR4: 50 ações a R$ 49,06 em 15/09 (peso de 32,02% para 29,33%) e 90 ações a R$ 57,60 em 15/10 (de 31,69% para 26,46%); VALE3 reentrou em 01/09 | A regra funcionou onde foi acionada; PETR4 passou de −R$ 1.783,77 para +R$ 1.812,50 |
| 2. Concentração e ordens residuais | Pico de 77,49%; 8 compras abaixo de R$ 2.000; 52 pregões com 3 ou mais ativos relevantes | Máximo de 29,98% em proposta de compra e 32,23% por deriva de preço; nenhuma compra abaixo de R$ 2.000; 99 pregões com 3 ou mais ativos relevantes; 26 ajustes do compilador (15 de teto e 11 de ordem mínima) | Concentração anômala e ordens residuais eliminadas |
| 3. Veto simétrico | 25 casos de VENDA bloqueada sob veto; nenhuma venda executada sob veto | 12 casos de VENDA sob veto e duas saídas executadas: 630 ITUB4 a R$ 42,05 em 27/10 e 330 BBAS3 a R$ 17,31 em 09/11 | As duas saídas evitaram cerca de R$ 827,34 líquidos de perda adicional até 12/11 |
| 4. Comitê homogêneo | 83,01% de unanimidade | 15,13% de unanimidade; 499 placares de consenso mínimo e 85 sem consenso | Diversidade real de votos, mas com efeito limitado no perfil de execução |

Na reauditoria feita com o auditor da v3, as duas reduções de PETR4 foram classificadas como realizações em força (RSI de 74,39 e 78,77), embora tenham sido admitidas pelo critério de peso da v2. Em 15/09 a venda financiou compras de BBAS3 e ITUB4 na mesma cesta; em 15/10 foi admitida pela cláusula de peso acima de 30%.

A melhora da v2 concentrou-se em um único ativo: o ganho de R$ 3.596,27 em PETR4 supera o ganho total de R$ 3.564,86, e os outros quatro ativos somados pioraram R$ 31,41.

### 3.4 O que ainda limitou o retorno

**Viés pró-tendência nos placares 3-2.** A quebra da unanimidade não mudou o momento das decisões na mesma proporção. Os dois analistas de tendência e os dois de reversão divergiram em 632 dos 760 pareceres, e o desempate coube ao analista 5, cuja lente de regime também pondera a estrutura de médias e o MACD. O resultado foram 499 placares de consenso mínimo (65,66%) e um perfil ainda pró-cíclico: COMPRA com RSI médio de 57,42 e preço 5,16% acima da média de 50 pregões; VENDA com RSI médio de 38,67 e preço 7,23% abaixo dela. Nas execuções, RSI médio de 58,54 nas compras e 40,98 nas vendas. A atribuição do desempate ao bloco de tendência é a interpretação registrada no diagnóstico; os dados confirmam a contagem dos placares e o perfil resultante, não o voto de cada cadeira.

**Dez saídas totais com recompra mais cara (whipsaw).** Das 16 vendas da v2, 10 zeraram a posição (8 por consenso técnico e 2 sob R7). O padrão repetiu o achado 2 da v1:

| Ativo | Vendas até zerar a posição | Compras seguintes |
|---|---|---|
| WEGE3 | R$ 43,86 (14/05); R$ 43,30 (17/07); R$ 45,06 (27/10) | R$ 46,40 e R$ 46,30 (02 e 03/07); R$ 47,00 a R$ 48,05 (27 a 31/07); R$ 49,67 e R$ 50,90 (05 e 10/11) |
| VALE3 | R$ 74,18, R$ 73,42 e R$ 73,99 (13 a 15/07), depois de comprar a R$ 83,00 em 18/05; R$ 73,70 e R$ 73,98 (17 e 21/09) | R$ 77,87 (01/09) |
| ITUB4 | R$ 39,86 (25/05); R$ 40,45 e R$ 38,92 (11 e 17/08) | R$ 41,95 a R$ 43,23 (08/07 a 05/08); R$ 41,50 a R$ 42,79 (10 a 22/09) |

O preço médio de compra superou o de venda em WEGE3 (R$ 47,85 contra R$ 44,09), VALE3 (R$ 79,00 contra R$ 73,90), ITUB4 (R$ 42,54 contra R$ 40,54) e BBAS3 (R$ 22,24 contra R$ 20,67). O contraste é PETR4, único ativo sem saída total e único com resultado positivo.

**Arrasto de caixa (cash drag).** O teto de 30% por ativo, combinado com a queda das recomendações de COMPRA (de 273 na v1 para 106 na v2, contra 537 MANTER), deixou capital ocioso: caixa médio de 24,69% do patrimônio, 65 pregões com mais de 30% em caixa, máximo de 67,74% e 45,86% no fechamento. Com dois ativos em carteira e teto de 30% cada, pelo menos 40% do capital fica estruturalmente parado, sem remuneração.

A v2 também registrou a primeira lacuna da série, em 26/06, por falha de transporte (seção 5.9).

---

## 4. Iteração v3 (`REPLAY-03`): R$ 100.067,36, +0,07%

### 4.1 Racional: mudar a composição, não a quantidade

O diagnóstico da v2 apontou dois problemas de desenho. No comitê, lentes duplicadas formavam blocos de voto, e o árbitro pendia para um deles. No gestor, a ausência de memória contábil e de limite para o tamanho das vendas permitia liquidar uma posição inteira no fundo e recomprá-la mais cara dias depois. A v3 mantém 5 + 1 + 1 e ataca os dois pontos: cinco cadeiras com especialidades diferentes e um gestor que conhece o preço médio das posições e está sujeito a piso e a venda escalonada.

Constantes em `scripts/continuous_replay_v3.py`:

| Constante | Valor | Papel |
|---|---:|---|
| `MAX_ASSET_WEIGHT` | 0,30 | Teto de peso projetado em compra por COMPRA |
| `DIP_REBALANCE_MAX_WEIGHT` | 0,22 | Teto de peso em compra de recomposição em MANTER |
| `MIN_TRADE_BRL` | 2.000,00 | Valor bruto mínimo de compra |
| `CORE_FLOOR_WEIGHT` | 0,08 | Piso de posição-núcleo após venda técnica normal |
| `MAX_NORMAL_SELL_FRACTION` | 0,45 | Fração máxima da posição vendida por pregão em venda normal |
| `ANTI_WHIPSAW_COOLDOWN_SESSIONS` | 8 | Janela, em pregões, da regra contra recompra mais cara |
| `CASH_DRAG_THRESHOLD` | 0,25 | Caixa sobre patrimônio que habilita a recomposição em MANTER |
| `STRENGTH_TRIM_MAX_FRACTION` | 0,35 | Fração máxima de uma realização em força |
| `STRENGTH_TRIM_MIN_WEIGHT_AFTER` | 0,12 | Peso mínimo após realização em força |
| `TRIM_MIN_WEIGHT_BEFORE` / `TRIM_MIN_WEIGHT_AFTER` | 0,25 / 0,15 | Limites do Trim-to-Fund, herdados da v2 |

### 4.2 Pilar 1 — Cinco lentes especialistas e travas de extremo

Cada analista recebe o prompt base e uma lente única, sem duplicatas:

| Analista | Lente | Regra central |
|---|---|---|
| 1 | `LENTE_BANDAS_BOLLINGER` | COMPRA perto ou abaixo da banda inferior (`bb_lower_gap` ≤ 0,035); VENDA perto ou acima da superior (`bb_upper_gap` ≥ −0,015); MANTER dentro do canal |
| 2 | `LENTE_EXAUSTAO_RSI_MACD` | RSI < 38: COMPRA ou MANTER, nunca VENDA; RSI > 64: VENDA ou MANTER, nunca COMPRA |
| 3 | `LENTE_VALOR_RELATIVO_SMA50` | Desconto sobre a média de 50 (`sma50_gap` < −0,02, com `sma200_gap` > −0,06) favorece COMPRA ou MANTER; prêmio esticado (`sma50_gap` > 0,05 e RSI > 60) nunca é COMPRA |
| 4 | `LENTE_ESTRUTURA_LONGA_SMA200` | Acima da média de 200, correções são secundárias (MANTER ou COMPRA, sem VENDA prematura salvo RSI > 70); VENDA só com `sma200_gap` < −0,03 e `sma50_gap` < 0 |
| 5 | `LENTE_ASSIMETRIA_RISCO_RETORNO` | Compara o espaço até a banda superior com a distância da inferior: mais espaço para cima e RSI < 55, nunca VENDA; mais espaço para baixo e RSI > 60, nunca COMPRA |

Duas travas determinísticas atuam sobre consensos mínimos de exatamente três votos (`committee_v3`):

- `ANTI_BOTTOM_SELL_GUARD`: consenso de VENDA por três votos é revertido para MANTER quando o RSI é inferior a 40 ou `bb_lower_gap` é inferior a 0,035, desde que `sma200_gap` seja superior a −0,08.
- `ANTI_TOP_CHASE_GUARD`: consenso de COMPRA por três votos é revertido para MANTER quando o RSI é superior a 62 ou `bb_upper_gap` é superior a −0,02.

### 4.3 Pilar 2 — Memória de posição, piso núcleo, venda escalonada e anti-whipsaw

**Memória contábil.** `compute_position_memory` reconstrói, a partir do livro, e entrega ao gestor por ativo: quantidade, preço médio de compra (`avg_buy_price`), retorno não realizado (`unrealized_return_pct`), sessão e preço da última venda (`last_sell_session`, `last_sell_price`) e pregões decorridos desde ela (`sessions_since_last_sell`).

**Piso núcleo e venda escalonada.** Em venda técnica normal (recomendação VENDA com risco APROVADO), o compilador limita a quantidade a 45% da posição atual, arredondada para cima, e exige que a posição remanescente represente pelo menos 8% do patrimônio. Quando a proposta do gestor excede um dos limites, a quantidade é reduzida ao máximo permitido e o ajuste é registrado como `CORE_FLOOR_STEP_SELL`. A saída integral fica reservada à emergência R7 (VENDA sob VETADO).

**Anti-whipsaw.** É recusada a compra de um ativo vendido nos últimos 8 pregões quando o preço de referência atual supera o preço da última venda (`ANTI_WHIPSAW_HIGHER_REBUY`).

### 4.4 Pilar 3 — Trim-on-Strength e Trim-to-Fund

A v3 admite duas formas de venda parcial em ativo com recomendação MANTER ou COMPRA:

- **Trim-on-Strength:** ativo esticado (RSI ≥ 63 ou `bb_upper_gap` ≥ −0,02), em lucro de pelo menos 2% sobre o preço médio e com peso acima de 14%; venda de até 35% da posição, mantendo peso de pelo menos 12%, sem exigir compra na cesta.
- **Trim-to-Fund:** a regra da v2, para ativo com peso acima de 25%, mantendo pelo menos 15%, quando há compra válida na cesta ou peso acima de 30%.

### 4.5 Pilar 4 — Dip-Rebalance contra o arrasto de caixa

Quando o caixa inicial do pregão supera 25% do patrimônio, o gestor pode comprar um ativo em MANTER com risco APROVADO, desde que esteja descontado (`sma50_gap` negativo com RSI de até 46, ou `bb_lower_gap` de até 0,04). A compra respeita teto de 22% de peso projetado, ordem mínima de R$ 2.000,00 e a regra anti-whipsaw. Permanecem o teto de 30% para compras por COMPRA e a ordem mínima de compra.

### 4.6 Resultado e inversão do perfil de execução

A Multiagentes v3 encerrou em R$ 100.067,36 (+0,0674%), com R$ 17.888,65 a mais que a v1 e R$ 14.323,79 a mais que a v2. Ficou acima do Buy & Hold (+R$ 11.276,25), da SMA 50/200 (+R$ 11.200,68), do Equal Weight (+R$ 10.198,07) e da Mínima Variância (+R$ 4.252,52), e abaixo da Bollinger 20/2 (−R$ 4.819,69).

**O sinal passou a apontar para o lado oposto.** A relação entre sinal e estado técnico do ativo, pró-cíclica nas duas primeiras versões, inverteu-se:

| Medida | v1 | v2 | v3 |
|---|---:|---:|---:|
| RSI médio do sinal COMPRA | 63,17 | 57,42 | 35,11 |
| RSI médio do sinal VENDA | 35,07 | 38,67 | 68,96 |
| RSI médio das compras executadas | 60,51 | 58,54 | 39,26 |
| RSI médio das vendas executadas | 36,06 | 40,98 | 69,00 |
| Diferença de RSI (compras − vendas executadas) | +24,45 | +17,56 | −29,74 |

Nas execuções da v3, as compras ocorreram com preço 3,69% abaixo da média de 50 pregões e a 0,93% da banda inferior; as vendas, com preço 11,09% acima da média de 50 pregões e a 0,52% da banda superior.

**Nenhuma saída total.** A v3 não zerou nenhuma posição (9 saídas na v1 e 10 na v2) e manteve os cinco ativos com peso de pelo menos 2% em todos os 153 pregões.

**Preço médio de venda acima do de compra nos cinco ativos.** PETR4 (R$ 43,18 → R$ 46,43), WEGE3 (R$ 48,13 → R$ 48,61), ITUB4 (R$ 42,14 → R$ 44,47), BBAS3 (R$ 20,37 → R$ 21,48) e VALE3 (R$ 75,77 → R$ 81,13). Alguns ciclos ilustram o padrão: PETR4 comprada a R$ 38,12, R$ 38,20 e R$ 37,89 entre 25/06 e 02/07 e vendida a R$ 43,40 e R$ 42,37 em 23 e 24/07; BBAS3 comprada a R$ 19,39, R$ 18,90 e R$ 18,20 entre 12 e 14/08 e vendida a R$ 21,26 e R$ 22,57 em 02 e 03/09.

**Captura integral de proventos.** Por nunca zerar posições antes das datas-com, a carteira recebeu os 20 eventos de proventos do período (R$ 1.425,30 líquidos), contra 9 eventos na v1 (R$ 567,02) e 9 na v2 (R$ 509,28).

**Fim do arrasto de caixa.** O caixa médio caiu de 24,69% para 14,94% e o caixa final, de 45,86% para 0,75% (R$ 751,17).

**Resultado por ativo.** Três ativos passaram a positivo: PETR4 (+R$ 3.222,19), WEGE3 (+R$ 1.991,89) e ITUB4 (+R$ 1.435,82). WEGE3 e ITUB4 respondem por R$ 12.089,35 dos R$ 14.323,79 ganhos sobre a v2 (84,4%). BBAS3 (−R$ 1.997,86) e VALE3 (−R$ 4.584,68) permaneceram negativos: são os dois papéis que mais caíram no período, e o piso núcleo obriga a manter exposição a eles. Em VALE3 a v3 teve o pior resultado das três versões e ficou abaixo do Buy & Hold (−R$ 4.255,30); a carteira comprou o papel a R$ 73,70, R$ 73,98, R$ 72,40 e R$ 68,16 entre setembro e outubro, e ele fechou a R$ 63,95.

### 4.7 Mecanismos efetivamente acionados

Nem todos os mecanismos implementados chegaram a atuar. A distinção importa para a atribuição causal.

| Mecanismo | Acionamentos na v3 | Observação |
|---|---:|---|
| Cinco lentes especialistas | 745 pareceres | Unanimidade de 4,03%; 715 pareceres não unânimes |
| `CORE_FLOOR_STEP_SELL` | 56 ajustes | Principal intervenção do compilador |
| `MAX_ASSET_WEIGHT_CAP` | 12 ajustes | Teto de 30% em compras |
| `MIN_TRADE_BRL` | 9 ajustes | Ordem mínima de compra |
| `INSUFFICIENT_CASH` | 2 ajustes | Compras reduzidas ao caixa disponível |
| Dip-Rebalance | 2 compras e 1 ajuste de teto | 50 WEGE3 em 17/04 (R$ 2.455,00) e 32 VALE3 em 21/09 (R$ 2.367,36) |
| `ANTI_BOTTOM_SELL_GUARD` e `ANTI_TOP_CHASE_GUARD` | 0 | Nenhum consenso mínimo caiu nas faixas de extremo |
| Trim-on-Strength e Trim-to-Fund | 0 | Nenhuma venda em MANTER ou COMPRA |
| Anti-whipsaw (ajuste do compilador) | 0 | A regra constava do prompt do gestor; nenhuma proposta precisou ser cortada |
| Saída R7 sob veto | 0 | Nenhum dos 46 vetos coincidiu com consenso técnico de VENDA |

Três leituras decorrem dessa tabela. As 52 vendas da v3 ocorreram todas sob consenso técnico de VENDA com risco aprovado, dosadas pelo piso núcleo; o comitê antecipou a realização e dispensou o Trim-on-Strength. As travas de extremo não foram acionadas, porque as lentes sozinhas já evitaram vender no fundo e comprar no topo. E o R7 não foi usado porque os picos de volatilidade ocorreram em quedas, nas quais o comitê da v3 deixou de votar VENDA. O efeito observado deve-se, portanto, à combinação de lentes, piso núcleo, venda escalonada, teto, ordem mínima e recomposição, e não aos mecanismos que permaneceram dormentes.

---

## 5. Tabelas comparativas completas

Salvo indicação, os valores vêm de `output/auditoria-replay-v3/comparacao_v1_v2_v3.json`, dos CSVs da mesma pasta, de `output/auditoria-replay-v2/comparacao_v1_v2.json` e de `output/auditoria-replay-20261115/verificacao.json`. Valores marcados com † foram lidos dos `daily.csv` ou `dividends.csv` dos pacotes selados de cada versão, que não constam nesses JSONs.

### 5.1 Patrimônio, retorno e custos das oito carteiras

| # | Carteira | Patrimônio final (R$) | Retorno (%) | Caixa (R$) | Recebíveis (R$) | Custos (R$) | Operações (C / V) | Saídas totais |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Bollinger 20/2 | 104.887,05 | +4,8870 | 1.507,33 | 8,24 | 151,26 | 24 (12 / 12) | 12 |
| 2 | **Multiagentes v3** | **100.067,36** | **+0,0674** | 751,17 | 283,95 | 120,07 | 81 (29 / 52) | 0 |
| 3 | Mínima Variância 252/63 | 95.814,84 | −4,1852 | 1.581,00 | 1.058,91 | 27,94 | 14 (8 / 6) | 1 |
| 4 | Equal Weight 63d | 89.869,29 | −10,1307 | 1.423,03 | 623,64 | 5,11 | 15 (9 / 6) | 0 |
| 5 | SMA 50/200 | 88.866,68 | −11,1333 | 34.912,62 | 579,70 | 32,23 | 6 (2 / 4) | 4 |
| 6 | Buy & Hold | 88.791,11 | −11,2089 | 1.418,18 | 583,45 | 0,00 | 0 | 0 |
| 7 | Multiagentes v2 | 85.743,57 | −14,2564 | 39.321,44 | 775,13 | 119,87 | 38 (22 / 16) | 10 |
| 8 | Multiagentes v1 | 82.178,71 | −17,8213 | 1.346,54 | 1.459,03 | 184,40 | 86 (50 / 36) | 9 |

As cinco referências são idênticas nas três campanhas. Posições finais da Multiagentes: v1 com 13 BBAS3, 380 ITUB4, 920 PETR4 e 430 WEGE3; v2 com 455 PETR4 e 490 WEGE3; v3 com 332 BBAS3, 166 ITUB4, 486 PETR4, 459 VALE3 e 695 WEGE3.

Diferença da Multiagentes para cada referência, em R$ e em pontos percentuais de retorno:

| Referência | v1 (R$) | v1 (p.p.) | v2 (R$) | v2 (p.p.) | v3 (R$) | v3 (p.p.) |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold | −6.612,40 | −6,6124 | −3.047,54 | −3,0475 | +11.276,25 | +11,2763 |
| SMA 50/200 | −6.687,97 | −6,6880 | −3.123,11 | −3,1231 | +11.200,68 | +11,2007 |
| Equal Weight 63d | −7.690,58 | −7,6906 | −4.125,72 | −4,1257 | +10.198,07 | +10,1981 |
| Mínima Variância 252/63 | −13.636,13 | −13,6361 | −10.071,27 | −10,0712 | +4.252,52 | +4,2526 |
| Bollinger 20/2 | −22.708,34 | −22,7083 | −19.143,48 | −19,1434 | −4.819,69 | −4,8196 |

Evolução entre gerações: v2 − v1 = +R$ 3.564,86 (+3,5649 p.p.); v3 − v2 = +R$ 14.323,79 (+14,3238 p.p.); v3 − v1 = +R$ 17.888,65 (+17,8887 p.p.).

| Complemento † | v1 | v2 | v3 |
|---|---:|---:|---:|
| Menor patrimônio de fechamento (R$) | 80.833,37 | 84.536,05 | 91.337,03 |
| Maior patrimônio de fechamento (R$) | 104.843,58 | 104.844,91 | 109.275,01 |

### 5.2 Resultado por ativo

Resultado contábil por ativo em R$, incluindo a cesta inicial, proventos e custos.

| Ativo | v1 | v2 | v3 | Δ v2 − v1 | Δ v3 − v2 | Δ v3 − v1 | Buy & Hold | Bollinger 20/2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PETR4 | −1.783,77 | +1.812,50 | +3.222,19 | +3.596,27 | +1.409,69 | +5.005,96 | −443,38 | −3.553,45 |
| WEGE3 | −5.443,38 | −4.858,70 | +1.991,89 | +584,68 | +6.850,59 | +7.435,27 | +603,40 | +5.454,99 |
| ITUB4 | −4.527,86 | −3.802,94 | +1.435,82 | +724,92 | +5.238,76 | +5.963,68 | −555,18 | +2.433,76 |
| BBAS3 | −1.633,20 | −2.850,25 | −1.997,86 | −1.217,05 | +852,39 | −364,66 | −6.558,43 | −41,24 |
| VALE3 | −4.433,08 | −4.557,04 | −4.584,68 | −123,96 | −27,64 | −151,60 | −4.255,30 | +592,99 |
| **Total** | **−17.821,29** | **−14.256,43** | **+67,36** | **+3.564,86** | **+14.323,79** | **+17.888,65** | **−11.208,89** | **+4.887,05** |

A v3 supera o Buy & Hold em quatro dos cinco ativos (exceção: VALE3) e a Bollinger 20/2 em apenas um (PETR4). Em relação à v1, melhora em três ativos e piora em BBAS3 e VALE3.

### 5.3 Preços médios, quantidades e permanência por ativo

Preços médios em R$ das operações posteriores à entrada; a cesta inicial não entra no preço médio de compra.

| Ativo | v1 compra / venda | v2 compra / venda | v3 compra / venda | Bollinger compra / venda |
|---|---:|---:|---:|---:|
| BBAS3 | 20,99 / 21,31 | 22,24 / 20,67 | 20,37 / 21,48 | 19,59 / 22,50 |
| ITUB4 | 44,07 / 40,61 | 42,54 / 40,54 | 42,14 / 44,47 | 41,04 / 43,04 |
| PETR4 | 44,77 / 42,81 | 41,02 / 54,55 | 43,18 / 46,43 | 47,90 / 41,20 |
| VALE3 | 83,46 / 78,85 | 79,00 / 73,90 | 75,77 / 81,13 | 70,28 / 81,12 |
| WEGE3 | 47,41 / 44,79 | 47,85 / 44,09 | 48,13 / 48,61 | 45,85 / 49,08 |
| Venda > compra | 1 de 5 | 1 de 5 | 5 de 5 | 4 de 5 |

Diferença relativa entre o preço médio de venda e o de compra:

| Ativo | v1 | v2 | v3 |
|---|---:|---:|---:|
| BBAS3 | +1,52% | −7,06% | +5,45% |
| ITUB4 | −7,85% | −4,70% | +5,53% |
| PETR4 | −4,38% | +32,98% | +7,53% |
| VALE3 | −5,52% | −6,46% | +7,07% |
| WEGE3 | −5,53% | −7,86% | +1,00% |

Vender acima do preço médio de compra não equivale a resultado positivo no ativo: BBAS3 e VALE3 seguem negativos na v3 porque a cesta inicial (R$ 23,39 e R$ 83,55) e as posições remanescentes foram marcadas a preços muito inferiores no fechamento.

| Ativo | Compras: nº / quantidade (v1 · v2 · v3) | Vendas: nº / quantidade (v1 · v2 · v3) | Pregões em carteira (v1 · v2 · v3) | Saídas totais (v1 · v2 · v3) | Quantidade final (v1 · v2 · v3) |
|---|---|---|---|---|---|
| BBAS3 | 4 / 713 · 3 / 330 · 4 / 1.215 | 6 / 1.555 · 2 / 1.185 · 9 / 1.738 | 76 · 56 · 153 | 2 · 2 · 0 | 13 · 0 · 332 |
| ITUB4 | 10 / 1.070 · 9 / 1.260 · 4 / 552 | 6 / 1.151 · 4 / 1.721 · 9 / 847 | 74 · 93 · 153 | 2 · 3 · 0 | 380 · 0 · 166 |
| PETR4 | 10 / 1.620 · 1 / 180 · 5 / 1.290 | 6 / 1.115 · 2 / 140 · 19 / 1.219 | 133 · 153 · 153 | 1 · 0 · 0 | 920 · 455 · 486 |
| VALE3 | 8 / 710 · 2 / 436 · 7 / 612 | 7 / 949 · 5 / 675 · 8 / 392 | 59 · 82 · 153 | 1 · 2 · 0 | 0 · 0 · 459 |
| WEGE3 | 18 / 2.383 · 7 / 1.622 · 9 / 1.047 | 11 / 2.350 · 3 / 1.529 · 7 / 749 | 109 · 107 · 153 | 3 · 3 · 0 | 430 · 490 · 695 |

Episódios de saída integral e reentrada:

| Versão | Ativo | Saída | Reentrada | Pregões zerado |
|---|---|---|---|---:|
| v1 | BBAS3 | 28/04 | 22/07 | 59 |
| v1 | BBAS3 | 13/08 | 09/09 | 18 |
| v1 | ITUB4 | 07/05 | 26/06 | 35 |
| v1 | ITUB4 | 14/08 | 19/10 | 44 |
| v1 | PETR4 | 23/06 | 21/07 | 20 |
| v1 | VALE3 | 01/07 | não retornou | 94 |
| v1 | WEGE3 | 06/05 | 19/06 | 31 |
| v1 | WEGE3 | 21/07 | 27/07 | 4 |
| v1 | WEGE3 | 22/10 | 05/11 | 9 |
| v2 | BBAS3 | 05/05 | 15/09 | 93 |
| v2 | BBAS3 | 09/11 (R7) | não retornou | 4 |
| v2 | ITUB4 | 25/05 | 08/07 | 31 |
| v2 | ITUB4 | 17/08 | 10/09 | 17 |
| v2 | ITUB4 | 27/10 (R7) | não retornou | 12 |
| v2 | VALE3 | 15/07 | 01/09 | 34 |
| v2 | VALE3 | 21/09 | não retornou | 37 |
| v2 | WEGE3 | 14/05 | 02/07 | 34 |
| v2 | WEGE3 | 17/07 | 27/07 | 6 |
| v2 | WEGE3 | 27/10 | 05/11 | 6 |
| v3 | — | nenhuma saída total | — | — |

### 5.4 Distribuição de votos e unanimidade do comitê

O total de pareceres considera os pregões com análise completa: 765 na v1, 760 na v2 (exclui 26/06) e 745 na v3 (exclui as quatro lacunas).

| Placar do sinal vencedor | v1 (n = 765) | v2 (n = 760) | v3 (n = 745) |
|---|---:|---:|---:|
| 5-0 (unanimidade) | 635 (83,01%) | 115 (15,13%) | 30 (4,03%) |
| 4-1 | 70 (9,15%) | 61 (8,03%) | 273 (36,64%) |
| 3-2 (consenso mínimo) | 60 (7,84%) | 499 (65,66%) | 336 (45,10%) |
| Sem consenso (vira MANTER) | 0 | 85 (11,18%) | 106 (14,23%) |
| Pareceres não unânimes | 130 | 645 | 715 |

Variação da unanimidade: −67,88 p.p. da v1 para a v2, −11,10 p.p. da v2 para a v3 e −78,98 p.p. da v1 para a v3. O auditor da v2 mede ainda a divergência específica entre lentes de tendência e de reversão: 120 pareceres na v1 e 632 na v2.

| Sinal técnico de consenso | v1 | v2 | v3 |
|---|---:|---:|---:|
| COMPRA | 273 (35,69%) | 106 (13,95%) | 219 (29,40%) |
| MANTER | 269 (35,16%) | 537 (70,66%) | 412 (55,30%) |
| VENDA | 223 (29,15%) | 117 (15,39%) | 114 (15,30%) |

Na v1, o consenso técnico e a recomendação após o risco, por ativo (COMPRA / MANTER / VENDA):

| Ativo | Consenso técnico | Após o risco |
|---|---|---|
| BBAS3 | 38 / 46 / 69 | 29 / 67 / 57 |
| ITUB4 | 59 / 48 / 46 | 59 / 60 / 34 |
| PETR4 | 70 / 74 / 9 | 69 / 76 / 8 |
| VALE3 | 35 / 59 / 59 | 35 / 59 / 59 |
| WEGE3 | 71 / 42 / 40 | 71 / 42 / 40 |

### 5.5 Perfil técnico dos sinais e das execuções

Médias das features no momento do sinal. Os gaps estão em percentual do preço.

| Versão | Sinal | Casos | RSI | Gap SMA50 | Gap SMA200 | Gap banda superior | Gap banda inferior |
|---|---|---:|---:|---:|---:|---:|---:|
| v1 | COMPRA | 273 | 63,17 | +7,82% | +13,72% | −2,51% | +14,50% |
| v1 | MANTER | 269 | 47,81 | −1,13% | +8,31% | −6,37% | +5,51% |
| v1 | VENDA | 223 | 35,07 | −8,64% | −5,93% | −13,92% | +3,38% |
| v2 | COMPRA | 106 | 57,42 | +5,16% | +9,78% | −4,27% | +10,88% |
| v2 | MANTER | 537 | 50,40 | +0,40% | +8,15% | −6,77% | +8,15% |
| v2 | VENDA | 117 | 38,67 | −7,23% | −6,59% | −11,90% | +5,37% |
| v3 | COMPRA | 219 | 35,11 | −7,68% | +0,33% | −12,61% | +1,52% |
| v3 | MANTER | 412 | 51,65 | +0,46% | +5,80% | −6,07% | +8,53% |
| v3 | VENDA | 114 | 68,96 | +11,71% | +18,46% | −1,41% | +19,26% |

| Versão | Execução | Operações | RSI | Gap SMA50 | Gap SMA200 | Gap banda superior | Gap banda inferior |
|---|---|---:|---:|---:|---:|---:|---:|
| v1 | Compra | 50 | 60,51 | +5,28% | +11,91% | −2,87% | +13,46% |
| v1 | Venda | 36 | 36,06 | −5,87% | +2,43% | −11,57% | +0,32% |
| v2 | Compra | 22 | 58,54 | +4,10% | +4,19% | −4,45% | +13,39% |
| v2 | Venda | 16 | 40,98 | −3,69% | +0,67% | −13,17% | +6,67% |
| v3 | Compra | 29 | 39,26 | −3,69% | +3,20% | −10,35% | +0,93% |
| v3 | Venda | 52 | 69,00 | +11,09% | +19,95% | −0,52% | +18,54% |

### 5.6 Concentração, caixa e proventos

| Métrica | v1 | v2 | v3 |
|---|---:|---:|---:|
| Pregões com 2 ativos de peso ≥ 2% | 101 | 54 | 0 |
| Pregões com 3 ativos de peso ≥ 2% | 29 | 36 | 0 |
| Pregões com 4 ativos de peso ≥ 2% | 8 | 40 | 0 |
| Pregões com 5 ativos de peso ≥ 2% | 15 | 23 | 153 |
| Pregões com 3 ou mais ativos de peso ≥ 2% | 52 | 99 | 153 |
| Peso máximo de um ativo no fechamento | 77,49% (VALE3) | 32,23% (WEGE3) | 35,87% (WEGE3) |
| Peso máximo de BBAS3 | 20,70% | 20,70% | 29,32% |
| Peso máximo de ITUB4 | 35,57% | 31,90% | 29,82% |
| Peso máximo de PETR4 | 71,40% | 31,72% | 30,39% |
| Peso máximo de VALE3 | 77,49% | 30,64% | 30,25% |
| Peso máximo de WEGE3 | 66,05% | 32,23% | 35,87% |
| Caixa médio sobre o patrimônio | 12,98% | 24,69% | 14,94% |
| Caixa máximo sobre o patrimônio | 73,24% † | 67,74% | 57,91% † |
| Pregões com caixa acima de 30% | 28 † | 65 | 25 |
| Pregões com caixa abaixo de R$ 200 | 69 | 19 † | 7 † |
| Caixa no fechamento (R$) | 1.346,54 | 39.321,44 | 751,17 |
| Caixa no fechamento sobre o patrimônio | 1,64% | 45,86% | 0,75% |
| Compras abaixo de R$ 2.000 | 8 | 0 | 0 |
| Eventos de proventos recebidos (de 20) | 9 | 9 | 20 |
| Proventos líquidos recebidos (R$) | 567,02 | 509,28 | 1.425,30 |
| Eventos de proventos nas seis carteiras | 97 | 97 | 108 |

O teto de 30% incide sobre o peso projetado no momento da compra; a deriva posterior dos preços explica os máximos de 32,23% na v2 e 35,87% na v3. O texto do relatório da v2 cita sete compras abaixo de R$ 2.000 na v1; os dois JSONs de auditoria listam oito, número adotado aqui.

### 5.7 Veto de risco e regra R7

| Métrica | v1 | v2 | v3 |
|---|---:|---:|---:|
| Pares ativo-pregão vetados | 41 | 48 | 46 |
| Vetos pela regra dura de volatilidade | 40 | 40 | 40 (implícito nas 725 chamadas de risco) |
| Vetos do modelo | 1 | 8 | não detalhado na auditoria |
| Vetados com consenso técnico de VENDA | 25 | 12 | 0 |
| Vendas executadas sob veto | 0 | 2 | 0 |
| Saídas totais sob R7 / demais saídas totais | 0 / 9 | 2 / 8 | 0 / 0 |

### 5.8 Ajustes determinísticos do compilador

| Ajuste ou mecanismo | v1 | v2 | v3 |
|---|---:|---:|---:|
| Modo do compilador | estrito | ajuste registrado | ajuste registrado |
| `CORE_FLOOR_STEP_SELL` | não existe | não existe | 56 |
| `MAX_ASSET_WEIGHT_CAP` | não existe | 15 | 12 |
| `MIN_TRADE_BRL` | não existe | 11 | 9 |
| `INSUFFICIENT_CASH` | não existe | 0 | 2 |
| `DIP_REBALANCE_WEIGHT_CAP` | não existe | não existe | 1 |
| `ANTI_WHIPSAW_HIGHER_REBUY` | não existe | não existe | 0 |
| **Total de ajustes registrados** | **0** | **26** | **80** |
| Reduções Trim-to-Fund executadas | 0 | 2 | 0 |
| Realizações Trim-on-Strength executadas | não existe | não existe | 0 |
| Compras Dip-Rebalance executadas | não existe | não existe | 2 |
| Reversões pelas travas de extremo do comitê | não existe | não existe | 0 |
| Ajustes de caixa no planejador de leilão | 0 | 0 | 0 |

Na v3, 27 das 52 vendas tiveram valor bruto inferior a R$ 2.000 (22 abaixo de R$ 500), somando R$ 7.970,68, contagem feita sobre `operacoes_v3.csv`. São vendas residuais produzidas pelo piso núcleo: com a posição próxima de 8% do patrimônio, cada novo sinal de VENDA libera apenas as poucas ações que excedem o piso (em outubro, por exemplo, PETR4 foi vendida em lotes de 1 a 9 ações durante a alta de R$ 53,16 a R$ 59,30). A ordem mínima vale apenas para compras.

### 5.9 Orçamento, tokens e execução

| Métrica | v1 | v2 | v3 |
|---|---:|---:|---:|
| Execução real (horário de São Paulo) | 13/11, concluída às 22:28 | 15/11, 18:33 a 23:39 | 16/11, 02:59 a 08:33 |
| Chamadas lógicas | 4.703 | 4.702 | 4.703 |
| Tentativas físicas HTTP | 4.709 | 4.711 | 4.703 |
| Chamadas com retentativa | 6 | 9 | 0 |
| Máximo de tentativas por chamada | 2 | 2 | 1 |
| Chamadas com uso de tokens reconciliado | 4.703 | 4.701 | 4.703 |
| Tentativas de resultado incerto | 6 | 10 | 0 |
| Tokens de entrada | 4.904.993 | 5.416.162 | 5.559.614 |
| Tokens de saída | 887.456 | 871.426 | 808.129 |
| Tokens de raciocínio | 116.730 | 425.315 | 380.651 |
| Tokens totais | 5.909.179 | 6.712.903 | 6.748.394 |
| Custo conhecido estimado (US$) | 7,44444225 | 8,92490025 | 8,62763550 |
| Reserva por incerteza (US$) | 0,663552 | 1,105920 | 0 |
| Exposição total (US$) | 8,10799425 | 10,03082025 | 8,62763550 |
| Pico de exposição antes de um HTTP (US$) | 8,26302975 | 10,18479150 | 8,78072850 |
| Teto autorizado (US$) | 34,78 | 34,78 | 34,78 |
| Modelo devolvido pelo provedor | `gemini-3.8-flash` | `gemini-3.8-flash` | `gemini-3.8-flash` |
| Auditoria de orçamento | PASS | PASS | PASS |

O número de chamadas lógicas é praticamente o mesmo nas três versões, como previsto pela topologia fixa. O volume de tokens da v3 é 14,2% maior que o da v1, por causa das lentes nos prompts dos analistas, da memória de posição no contexto do gestor e do maior uso de raciocínio; o custo conhecido estimado é 15,9% maior. Os valores são estimativas a partir do uso informado pelo provedor, não fatura.

Operações registradas nos pacotes, incluindo as 30 compras iniciais das seis carteiras: 175 na v1, 127 na v2 e 170 na v3. Decisões de regras das referências: 608 em todas.

### 5.10 Lacunas e tratamento fail-closed

| Versão | Pregões com análise completa | Lacunas | Data | Etapa | Causa | Tratamento |
|---|---:|---:|---|---|---|---|
| v1 | 153 | 0 | — | — | 6 retentativas de transporte, todas recuperadas | — |
| v2 | 152 | 1 | 26/06 | Comitê (risco de BBAS3) | `ProviderTransportError` (`WinError 10054`) nas duas tentativas, depois de cinco votos técnicos válidos (4 VENDA e 1 MANTER) | `NO_ANALYSIS`; chamada do gestor suprimida; posição preservada (415 PETR4, 335 VALE3, caixa de R$ 46.945,27) |
| v3 | 149 | 4 | 01/07, 01/09 e 02/10 | Validação da proposta do gestor | O gestor devolveu `SELL` com quantidade `"0"` para ativos junto ao piso núcleo; o contrato contábil exige inteiro positivo em BUY e SELL | `NO_ANALYSIS`; nenhuma ordem; posições preservadas |
| v3 | | | 01/10 | Validação da proposta do gestor | Duas ações para PETR4 e WEGE3 omitida (`manager_complete_unique_universe_required`) | `NO_ANALYSIS`; nenhuma ordem; posições preservadas |

As lacunas da v2 e da v3 têm naturezas diferentes. A da v2 é de infraestrutura, anterior à decisão. As quatro da v3 ocorreram depois de chamadas pagas e bem-sucedidas, na validação determinística da resposta: em três delas o modelo expressou "não vender" como venda de quantidade zero, efeito colateral do próprio piso núcleo. Normalizar `BUY` ou `SELL` de quantidade zero para `HOLD` antes da validação, com ajuste registrado, eliminaria três das quatro; a alteração fica como lição para uma eventual versão futura e não foi aplicada, para preservar a v3. Em todos os casos os 918 estados diários foram reconciliados.

---

## 6. Discussão científica, contribuições e limitações formais

### 6.1 Interpretação dos resultados

**Diversidade exige especialização.** Na v1, cinco instâncias do mesmo modelo com o mesmo prompt concordaram em 83,01% dos pareceres, mesmo em temperatura 1,0 e com sementes diferentes. A variação estocástica não substituiu a diversidade de critério. Com três lentes a unanimidade caiu para 15,13% e, com cinco, para 4,03%. Para a engenharia de comitês de modelos de linguagem, o resultado sugere que o número de agentes importa menos que a diferença entre as funções que lhes são atribuídas.

**Diversidade com blocos reproduz o viés do bloco majoritário.** A v2 mostra que quebrar a unanimidade não basta. Com duas cadeiras de tendência, duas de reversão e um árbitro, o perfil de execução mudou pouco (RSI médio de 58,54 nas compras e 40,98 nas vendas). Só com cinco critérios distintos o sinal passou a ocorrer no extremo oposto do oscilador.

**Governança determinística separa julgamento de execução.** A melhora da v1 para a v2 veio de regras de carteira aplicadas pelo compilador, e a v3 ampliou esse papel. O modelo propõe; o compilador limita, ajusta e registra. Os 80 ajustes da v3 mostram que a proposta bruta do gestor violava as regras com frequência, sobretudo ao pedir vendas maiores que o permitido, e que a governança moldou o resultado tanto quanto os sinais.

**Permanecer posicionado teve valor nesta trajetória.** Com zero saídas totais, a v3 capturou os 20 eventos de proventos e evitou o ciclo de sair no fundo e recomprar mais caro, responsável pelas perdas em WEGE3 e ITUB4 nas versões anteriores. O mesmo piso tem custo quando a queda persiste: VALE3 e BBAS3 seguiram negativos, e em VALE3 a v3 ficou abaixo do Buy & Hold.

**Uma regra simples ainda venceu.** A Bollinger 20/2, determinística e sem custo de inferência, terminou R$ 4.819,69 acima da v3. As lentes da v3 codificam, em boa medida, a lógica de reversão à média que caracteriza essa referência, que já era conhecida como a de melhor resultado quando a v3 foi desenhada. A leitura cautelosa é que a arquitetura multiagente se mostrou capaz de expressar uma política de reversão com governança de carteira, não que tenha descoberto uma política superior.

**Dependência de regime.** O período favoreceu reversão à média: quatro dos cinco ativos caíram e a referência de tendência (SMA 50/200) ficou próxima do Buy & Hold. Em mercado de tendência persistente, vender força e comprar fraqueza poderia inverter a ordenação das versões.

### 6.2 Contribuições

1. **Desenho de comparação controlada entre gerações de uma arquitetura multiagente**, com modelo, topologia, dados, execução e orçamento constantes e cinco referências reproduzidas com paridade exata, o que confina as diferenças à carteira em estudo.
2. **Método de diagnóstico empírico reprodutível**: auditorias por script, com reconstrução independente dos 918 estados diários e verificação por hash, que transformaram um resultado negativo (v1) em cinco achados acionáveis.
3. **Evidência de homogeneidade em comitês de modelos idênticos** e de sua redução por lentes especialistas, medida pela distribuição de placares.
4. **Padrão de governança determinística sobre a proposta do modelo**, em que o compilador ajusta e registra cada intervenção, com trilha de auditoria por ação.
5. **Veto de risco assimétrico (R7)**, que impede compras sem bloquear a redução de exposição, corrigindo um controle que agravava o risco que deveria conter.
6. **Memória contábil, piso núcleo e venda escalonada** como mecanismos contra saídas integrais e recompras mais caras, com efeito mensurável em saídas totais, preços médios e captura de proventos.
7. **Infraestrutura de execução auditável**: teto agregado com reserva durável antes de cada requisição, tentativas preservadas, tratamento fail-closed de lacunas e preservação integral das versões anteriores.
8. **Registro honesto de resultados negativos**: duas das três gerações ficaram abaixo de todas as referências, e os relatórios das três permanecem lado a lado.

### 6.3 Limitações formais (DP-36 / DP-37)

**Limites do contrato do replay.**

1. **Reconstrução retrospectiva sem arquivo point-in-time.** Preços, fatores de ajuste e proventos foram adquiridos depois do período; não se afirma que estavam disponíveis, naquela forma, em cada data de decisão.
2. **Possível contaminação do modelo.** O corte de conhecimento declarado do `gemini-3.8-flash` (março de 2026) não garante que o modelo desconheça o período. É a razão pela qual a DP-31 restringe a avaliação de agentes ao modo prospectivo.
3. **Alias de modelo não imutável.** As três campanhas rodaram em 13, 15 e 16/11 sob o mesmo alias, sem garantia de que o ponto de controle servido fosse idêntico. É um fator de confusão entre versões que o desenho não elimina.
4. **Execução simulada.** A abertura usa `PREABE` como aproximação, sem spread, impacto de mercado, microestrutura do leilão ou liquidação em D+2. A aprovação é hipotética às 09:00; a rotina diária real (prévia de cotação, alerta de tese velha, novas tentativas às 12h e 16h) não foi reconstituída.
5. **Simplificações contábeis.** Caixa sem remuneração, JCP tributado a 15%, custo proporcional de 0,03% sem custo fixo, cesta inicial hipotética a custo zero.
6. **Regras de referência (DP-36).** Os sinais usam fechamento B3 multiplicado pelo fator Yahoo de uma versão congelada, sem afirmar disponibilidade histórica desse ajuste. O primeiro sinal das referências usa o primeiro fechamento da campanha, enquanto a primeira decisão dos agentes usa o fechamento anterior.

**Ameaças à validade da comparação entre versões.**

7. **Iteração dentro da amostra.** A v2 e a v3 foram desenhadas depois de observar as campanhas anteriores nos mesmos 153 pregões. Limiares como RSI 38 e 64, piso de 8% e fração de 45% foram escolhidos com conhecimento do período e do desempenho das referências. Não há amostra de validação separada; o resultado da v3 pode refletir sobreajuste a esta trajetória.
8. **Uma execução por versão.** Com temperatura 1,0, cada campanha é uma realização de um processo estocástico. Sem repetições, não há estimativa de variância nem intervalo de confiança para as diferenças.
9. **Intervenções em bloco, sem ablação.** Cada versão mudou vários fatores ao mesmo tempo. O efeito de cada pilar não é identificável, e parte dos mecanismos da v3 nunca foi acionada (seção 4.7).
10. **Lacunas diferentes por versão.** A v1 não teve lacunas, a v2 teve uma e a v3 teve quatro. O efeito dos pregões sem decisão sobre o resultado não foi medido.
11. **Escopo reduzido.** Cinco ações, um intervalo de 153 pregões e um único regime de mercado.
12. **Métricas descritivas.** Este documento compara patrimônio final, giro, concentração e perfil de execução. Não apresenta medidas de retorno ajustado ao risco nem testes de significância.
13. **Efeitos colaterais da v3.** Pouco mais da metade das vendas foi residual (27 de 52; seção 5.8), o que seria inviável com custos fixos ou lotes mínimos. O piso núcleo impõe exposição a ativos em queda.
14. **Custo comparado.** A v3 consumiu cerca de US$ 8,63 em inferência para ficar abaixo de uma regra determinística sem custo de modelo.

**O que os resultados permitem afirmar.** Nesta trajetória e sob estas regras, a especialização das lentes e a governança de carteira mudaram de forma mensurável o comportamento da carteira multiagente: menos unanimidade, inversão do momento de compra e venda, fim das saídas totais, menor concentração e patrimônio final R$ 17.888,65 acima da linha de base.

**O que não permitem afirmar.** Que a v3 seja superior às referências fora deste período; que a ordenação se repita em outro regime; que algum pilar isolado seja responsável pelo ganho; ou que o resultado represente benefício financeiro esperado. Conforme a direção do projeto, benefício financeiro é hipótese a investigar, não conclusão.

### 6.4 Trabalhos futuros

- Avaliar a v3 congelada de forma prospectiva, no acompanhamento diário, sem novos ajustes de parâmetro.
- Fazer ablações: cada pilar isolado sobre a v2, para identificar a contribuição de cada mecanismo.
- Repetir as campanhas com sementes diferentes para estimar a variância entre execuções.
- Testar em outros períodos e regimes, inclusive de tendência persistente.
- Normalizar ações de quantidade zero para `HOLD` e reforçar a unicidade do universo na resposta do gestor, para eliminar as lacunas de validação.
- Estudar um valor mínimo para vendas e um piso núcleo condicionado à tendência de longo prazo.
- Remunerar o caixa por uma taxa de referência, para medir o custo de oportunidade com mais precisão.

### 6.5 Fontes, reprodutibilidade e preservação

| Item | v1 | v2 | v3 |
|---|---|---|---|
| Motor | `scripts/continuous_replay.py` | `scripts/continuous_replay_v2.py` | `scripts/continuous_replay_v3.py` |
| Auditoria | `scripts/audit_replay_positions.py` | `scripts/audit_replay_v2_comparison.py` | `scripts/audit_replay_v3_comparison.py` |
| Relatório | [auditoria e plano](auditoria_posicoes_replay_2026-04_2026-11.md) | [relatório v2](replay_continuo_v2_2026-04_2026-11.md) | [relatório v3](replay_continuo_v3_2026-04_2026-11.md) |
| Dados de auditoria | `output/auditoria-replay-20261115/verificacao.json` | `output/auditoria-replay-v2/comparacao_v1_v2.json` | `output/auditoria-replay-v3/comparacao_v1_v2_v3.json` |
| `explorer.json` (SHA-256) | `88c3a0e1…` | `4f517224…` | `0df082bd…` |
| `calls.json` (SHA-256) | `b5ef9585…` | `f5c01345…` | no manifesto do pacote |
| Situação das três auditorias | PASS | PASS | PASS |

Os rótulos históricos "DP-35/36" que aparecem em scripts e recibos do replay correspondem à DP-37, conforme a tabela de correspondência do documento de direção; os artefatos selados mantêm os identificadores com que foram produzidos. Este documento não altera nenhum arquivo das três campanhas: consolida os relatórios e as auditorias existentes, e os números aqui apresentados podem ser conferidos nas fontes da tabela acima.
