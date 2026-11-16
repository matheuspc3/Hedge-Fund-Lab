# Campanha contínua de seis carteiras — abril a novembro de 2026

DP-35/36 / REPLAY-01. Reconstrução exploratória produzida agora; não é evidência prospectiva ou demonstração de superioridade.

Período 2026-04-06–2026-11-12, 153 pregões. R$ 100.000 independentes por carteira, cesta inicial comum, ações inteiras, custos posteriores de 0,03%, proventos líquidos por componente em caixa no pagamento. As cinco referências foram concluídas antes da inferência.
A Multiagentes terminou R$ 6.612,40 abaixo do Buy & Hold. O maior patrimônio final nesta execução foi de Bollinger 20/2. A comparação não identifica causalidade nem valida superioridade fora desta trajetória.


| Carteira | Patrimônio final R$ | Retorno % | Caixa R$ | Recebíveis R$ | Custos R$ | Operações após entrada |
|---|---:|---:|---:|---:|---:|---:|
| Multiagentes | 82.178,71 | -17,8213 | 1.346,54 | 1.459,03 | 184,40 | 86 |
| Buy & Hold | 88.791,11 | -11,2089 | 1.418,18 | 583,45 | 0,00 | 0 |
| SMA 50/200 | 88.866,68 | -11,1333 | 34.912,62 | 579,70 | 32,23 | 6 |
| Bollinger 20/2 | 104.887,05 | 4,8870 | 1.507,33 | 8,24 | 151,26 | 24 |
| Equal Weight | 89.869,29 | -10,1307 | 1.423,03 | 623,64 | 5,11 | 15 |
| Mínima Variância | 95.814,84 | -4,1852 | 1.581,00 | 1.058,91 | 27,94 | 14 |

Análises diárias completas: 153/153. Lacunas: nenhuma. Uma falha preserva a posição; não se fabrica HOLD nem se substitui resposta inválida.

Orçamento agregado US$ 34.78, 4709 tentativas HTTP. Uso conhecido estimado US$ 7.44444225; reserva adicional incerta US$ 0.663552; exposição total US$ 8.10799425. Inclui todas as retomadas/retries desta campanha; não é fatura ou confirmação de saldo promocional.

Verificação: checks.json reconstrói estados diários, entradas iguais, fills RAW na abertura, custos de 0,03%, causalidade das janelas, 252 retornos de aquecimento e todos os componentes de proventos elegíveis, sem caixa antecipado. A preservação dos pilotos e do livro local de outubro é conferida por hashes.

SMA 50/200 e Bollinger 20/2: regras atuais da aplicação, parcelas independentes de 20%. Equal/Mínima: rebalanceamento a cada 63 pregões, Mínima com 252 retornos e sem shorts, mesmo objetivo e restrições do SLSQP, com escala normalizada por uma constante positiva; resultados/fallbacks preservados. Compras na abertura usam o mesmo ajuste proporcional ao caixa da Multiagentes. Buy & Hold/regras não reinvestem proventos. O gestor mantém o fluxo atual e pode realocar o caixa recebido sob seus sinais/gates.

Limites: dados/fatores/proventos reconstituídos agora, sem arquivo point-in-time; cutoff declarado de março/2026 não certifica ausência de contaminação; alias Gemini não imutável; PREABE diário é proxy da abertura, sem microestrutura, spread, impacto ou liquidação D+2; caixa não rende. A prévia intradiária e o alerta de tese velha não foram reconstruídos. JCP usa a hipótese de 15% do contrato atual, sem exceções fiscais. IA decide antes da abertura de D0 com referência anterior; regras começam no fechamento de D0. API em USD separada dos custos de negociação em BRL.

Os dois pilotos anteriores, outubro oficial, H2 e produção Railway permanecem separados. A coleta do Railway foi consultada somente em leitura e já estava atualizada até 12/11; o checkout do PC era a cópia pré-migração. Os 16 snapshots recentes conferem com a preparação.

Evidências e exportações: `data/cache/continuous-replay/april-november-2026-flash/`; manifestos versionados, inputs/CSV, SQLite de livro/chamadas/orçamento, recibos por sessão, respostas brutas e `qualified-v2/exports/{explorer,calls}.json`, daily/operations/decisions/dividends/calls.csv. Reparos pré-pagos de identidade dos componentes JCP e de escala numérica da Mínima Variância documentados no inventário, sem reescrever evidências diagnósticas.

Próxima etapa: explorar os resultados na interface e usar o relato descritivo no TCC; qualquer nova campanha ou ajuste estratégico requer escopo próprio.


Auditoria do orçamento PASS: 4703 chamadas lógicas, 6 retries, máximo 2 tentativas por chamada, no máximo uma resposta consumida por voto. Pico reconstruído antes de HTTP: US$ 8.26302975. 40 vetos determinísticos dispensaram a chamada de risco; não foram lacunas de análise.

Tokens conhecidos: 4904993 de entrada + 887456 de saída + 116730 de thinking = 5909179. Versão devolvida: gemini-3.8-flash; esse texto não certifica checkpoint imutável.

A inferência continuou durante a interrupção do Codex e terminou em 13/11/2026 às 22:28 (São Paulo), sem segunda instância nem reset. Reprodutibilidade da análise usa os envelopes/votos persistidos; novas chamadas ao alias estocástico não garantem respostas iguais.
