# Calendário B3 e proteção do holdout H2

## 1. Problema

O calendário do projeto (`src/backtesting/b3_calendar.py`) é auditado contra o
COTAHIST oficial só até 31/08/2026. As 10 sessões da campanha retrospectiva C3
(set.–out./2026) vinham apenas da regra de calendário
(bloqueio `COTAHIST_SESSION_VERIFICATION` na V7.6).

## 2. Procedimento definido e executado (diagnóstico)

`python -B scripts/review_v761.py calendar` (somente leitura, sem rede):

1. Abre o COTAHIST 2026 já em cache da execução recovery-01 e confere seu
   SHA-256 contra o registrado pelos inputs selados do Radar.
2. Percorre os registros e **descarta pelo prefixo de data** tudo antes de
   01/09/2026. Registros da janela do Final Test H2 (01/09/2025–31/08/2026)
   nunca são interpretados além dos 8 bytes de data.
3. Dos registros de 01/09 a 08/10/2026, lê só data, `CODBDI` (02), `TPMERC`
   (010) e código de negociação. **Nenhum preço é lido**, nem da janela
   fora da amostra.
4. Compara as sessões presentes para os 5 ativos com a regra de calendário e
   com as 10 sessões selecionadas pela semente 7606.

Resultado ([calendar_check.json](calendar_check.json)):

| Verificação | Resultado |
|---|---|
| SHA-256 do arquivo = registrado pelos inputs do Radar | sim (`d55b48e4…fc11`) |
| Última data encontrada a partir de 01/09 | 09/10/2026 |
| Sessões da regra no período | 27 |
| Sessões no COTAHIST com os 5 ativos | 27 |
| Regra × COTAHIST | idênticos (nenhuma falta, nenhuma sobra) |
| 10 sessões selecionadas presentes | 10/10 |

A seleção **não foi alterada**: só conferida.

## 3. Critérios de validação para o uso futuro

1. Na preparação de C3, baixar de novo o COTAHIST oficial (o cache é
   OPERATIONAL e pode mudar), registrar o SHA-256 e repetir a conferência
   por data. Divergência → sessão substituída pela próxima da ordem
   pré-registrada, com registro do motivo.
2. Os inputs Radar de cada sessão C3 registram o SHA do COTAHIST usado
   (comportamento atual do preparo normalizado).
3. Não usar sessões fora de 01/09–08/10/2026 em C3 sem versão nova do
   protocolo.
4. Não chamar C3 de prospectiva: os preços das sessões já eram conhecidos
   quando o protocolo foi escrito.

## 4. Holdout H2: o que está protegido e o que não está

| Ação | Situação |
|---|---|
| Executar agentes em sessões da janela FINAL_TEST H2 | **proibido** pelo validador do protocolo (`session_in_h2_window`) |
| Avaliar retornos dentro da janela H2 | não ocorre em nenhuma campanha |
| Selecionar sessões olhando preços ou retornos | não ocorre: regra de calendário + semente |
| Conferência de calendário V7.6.1 | só datas a partir de 01/09/2026 |
| **Histórico de indicadores das sessões C3** | **contém barras da janela H2**: SMA200, MACD e volatilidade de uma sessão de setembro/2026 usam cerca de 10 meses anteriores, inclusive PETR4 |

O último item já vale para o Radar de 09/10/2026 (311 sessões desde
16/07/2025). É uso dos preços públicos como **entrada** de indicadores, e não
execução do H2 nem avaliação no holdout. Mesmo assim, deve ser declarado.
**Decisão humana:** aceitar essa sobreposição de entrada (recomendado, porque
é inevitável para indicadores de longo prazo e não revela resultado do H2) ou
adiar C3 até o Final Test H2 ser executado ou liberado.

## 5. Efeito no protocolo

O bloqueio `COTAHIST_SESSION_VERIFICATION` pode ser removido **numa versão
nova do protocolo** (1.1.0), citando este diagnóstico, sob a condição do
critério 1 (reconferir na preparação). A versão 1.0.0 não é alterada.
