# Primeiro replay real multiativos: 06–17/04/2026

Produzido em 12/11/2026 · DP-35 / REPLAY-01 · Gemini 3.8 Flash.

**Dez pregões marcados, sete análises completas, três sem análise final e uma operação.** O resultado é exploratório e inclui as falhas; não equivale a dez decisões completas nem a um estudo prospectivo.

| Resultado | Multiagentes | Buy & Hold |
|---|---:|---:|
| Capital hipotético inicial | R$ 100.000,00 | R$ 100.000,00 |
| Patrimônio final | R$ 102.503,49 | R$ 102.498,88 |
| Retorno líquido de custos de negociação | 2,50349% | 2,49888% |
| Caixa final | R$ 31,34 | R$ 116,48 |
| Custos de negociação | R$ 0,03 | R$ 0,00 |

Diferença final: **R$ 4,61**, ou **0,00461 ponto percentual** do capital inicial. Não demonstra superioridade. O patrimônio vem quase integralmente da mesma cesta inicial; o gestor fez apenas uma compra pequena. O custo da API é separado do capital simulado e não foi debitado do patrimônio.

## Decisões, operação e trajetória

Nas sete análises completas, o gestor manteve as posições em seis e propôs uma compra em 13/04. A compra de **1 VALE3** usou OPEN RAW B3 de **R$ 85,11** e custo de **R$ 0,03**, reduzindo o caixa de R$ 116,48 para R$ 31,34. A posição de VALE3 passou de 239 para 240 unidades e foi propagada até o fim. Os demais ativos ficaram constantes. Não houve vendas nem novos direitos de proventos no bloco inspecionado.

| Pregão | Análise final | Operações | Multiagentes (R$) | Buy & Hold (R$) |
|---|---|---:|---:|---:|
| 2026-04-06 | Completa — manter | 0 | 100.462,77 | 100.462,77 |
| 2026-04-07 | Sem análise — conexão interrompida | 0 | 100.434,35 | 100.434,35 |
| 2026-04-08 | Completa — manter | 0 | 102.540,06 | 102.540,06 |
| 2026-04-09 | Completa — manter | 0 | 103.304,74 | 103.304,74 |
| 2026-04-10 | Sem análise — conexão interrompida | 0 | 104.295,72 | 104.295,72 |
| 2026-04-13 | Compra de 1 VALE3 | 1 | 104.605,20 | 104.602,98 |
| 2026-04-14 | Sem análise — conexão interrompida | 0 | 104.848,07 | 104.844,91 |
| 2026-04-15 | Completa — manter | 0 | 103.097,85 | 103.094,55 |
| 2026-04-16 | Completa — manter | 0 | 102.809,62 | 102.807,32 |
| 2026-04-17 | Completa — manter | 0 | 102.503,49 | 102.498,88 |

Os dias sem análise continuaram com as posições reais do livro e a marcação RAW do pregão. Não receberam votos, risco, gestor ou decisão HOLD fabricados. Em 07/04 faltou um voto de ITUB4; em 10/04, um voto de BBAS3; em 14/04, a resposta do risco de BBAS3. Os demais votos recebidos estão preservados. Todas as falhas foram `ProviderTransportError` / WinError 10054 (conexão encerrada pelo host remoto). Não houve nova tentativa dessas chamadas.

## Inferência, custo e tempo

- **305 tentativas HTTP**, 302 respostas com uso conhecido e 3 respostas incertas, contra o limite planejado de 310; um HTTP no máximo por chamada.
- Tokens conhecidos: **311238** de entrada, **55079** de saída e **6693** de thinking; total conhecido **373010**. Não é o total integral, pois três respostas não retornaram usage.
- Estimativa pelos tokens conhecidos: **US$ 0.4650735**. Limite adicional das três respostas incertas: **US$ 0,165888**; total com esse limite: **US$ 0.6309615**. Não é fatura, saldo ou confirmação de crédito promocional.
- Teto autorizado: **US$ 34.78**; reserva conservadora planejada US$ 34,77504.
- Soma de latências registradas: **1187.1 s** (19 min 47 s); média **3.89 s** por tentativa. Tempo corrido da autorização ao último fechamento: **25.2 min**, incluindo revisões técnicas e retomadas.
- Modelo solicitado e reportado pelo provedor: `gemini-3.8-flash`; isso não identifica um build imutável da API.

Tarifas [Standard oficiais](https://aistudio.google.com/docs/pricing#gemini-3.8-flash), verificadas em 12/11/2026: US$ 0,75/1M entrada e US$ 3,75/1M saída incluindo thinking. A ausência do contador de thinking só foi reconciliada como zero quando o total devolvido igualava entrada + saída.

## Base, equivalência e limites

Mesmo saldo inicial nas duas carteiras: R$ 100 mil de referência, unidades inteiras próximas de 20% por ativo e R$ 116,48 de caixa. Posições: BBAS3 855; ITUB4 461; PETR4 415; VALE3 239; WEGE3 397. Saldo inicial hipotético pelo fechamento de 02/04, registrado no início de 06/04, como adaptação do cadastro DP-20; não é fill histórico. O aquecimento de 450 dias alimenta indicadores, sem patrimônio anterior. Portanto, o retorno apresentado parte dessa base de referência e inclui a variação até o primeiro fechamento de 06/04.

Reutilizados: cinco analistas por ativo, consenso/risco do Radar, `WalletClient`/prompt/schema do gestor atual, validação de quantidades e sinais, `auction_orders.plan` e o livro atual. Custos de 0,03% por movimentação; entrada hipotética sem custos igual nas duas carteiras. Buy & Hold sem rebalanceamento ou reinvestimento.

Dados RAW B3 e ajustes Yahoo coletados posteriormente, com fontes/hashes no bundle. Caixa econômico da aplicação atual, sem liquidação de corretora D+2. Aprovação às 09h é hipotética; execução usa OPEN RAW como proxy diário. Não se reconstituem prévia intradiária, alerta de tese velha, spread, impacto ou slots 12h/16h. Três falhas reduziram a cobertura a sete análises completas. O [corte declarado de março de 2026](https://deepmind.google/models/model-cards/gemini-3-8-flash/) não certifica ausência de conhecimento posterior.

## Verificação e arquivos

**PASS** no check real: dez marcações reconstruídas a partir do livro, mesma base inicial, estado anterior conferido por sessão, sete propostas e quóruns completos validados, inputs anteriores ao alvo, OPEN/custo da compra, três dias sem decisão fabricada, máximo de uma tentativa HTTP por chamada e teto agregado. Check offline anterior: dez sessões, 310 chamadas simuladas e 13 operações; não foi usado como resultado real. Regressão de gestor/contabilidade: 63 passed, 1 skipped e nove subtestes. Radar: 15 passed e uma falha histórica de integridade CRLF já documentada.

Não houve escrita na carteira de outubro, ledger H2, serviço Railway, deploy ou push. O runner permaneceu com o hash congelado. Um adaptador isolado de relatório/revisão tratou os JSON de falha sem selo do Radar, preservando o código e manifest que geraram as inferências. O código efetivamente usado foi copiado para `runtime/` na raiz do ensaio.

Raiz dos artefatos: `C:/Users/LUCAS/.codex/worktrees/b507/Hedge-Fund-Lab/data/cache/historical-replay/april-2026-flash/`.

- [Relatório estruturado](../data/cache/historical-replay/april-2026-flash/report.json)
- [Verificação real](../data/cache/historical-replay/april-2026-flash/checks.json)
- [Manifest](../data/cache/historical-replay/april-2026-flash/manifest.json)
- [Autorização do teto](../data/cache/historical-replay/april-2026-flash/authorization.json)
- [Contrato e comandos](../docs/REPLAY_MULTIATIVOS.md)

Cada sessão tem inputs, bancos de chamadas, propostas/decisões ou revisão da falha e patrimônio; o livro isolado está em `book/manual.sqlite3`.

Próximo passo: usar este pacote como evidência exploratória no TCC, com as três lacunas e as premissas declaradas. Não ampliar período/modelos nem prometer benefício financeiro com base nesta amostra.
