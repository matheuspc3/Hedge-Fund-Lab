# Premium V3 — Mercado e cenários de abertura

Entrega local em 11/10/2026. **HEDGE-FUND-LAB PREMIUM V3 — MARKET MONITOR & ORDER SCENARIO READY**.

Painel: <http://localhost:8085/paper>. A aba Mercado consulta registros locais;
o simulador fica na Sala de Decisão. Nenhuma aprovação, rejeição, ordem, chamada
Gemini ou execução experimental foi realizada durante esta entrega. Sem push.

## Fase A — avaliação compartilhada e simulador

`opening_conditions` calcula a interseção dos limites brutos e as condições
individuais. `evaluate_opening` extrai a avaliação que já existia em `resolve`:
usa a mesma correção de concentração após custos, o mesmo `fwd.reconcile` e o
mesmo motor de liquidação congelado. O runner supervisionado chama esse helper;
a API trabalha sobre cópias, sem instalar a ordem retornada. `act`, aprovação,
cancelamento, sincronização e runner original não foram modificados.

A única correção de fronteira é numérica: comparar `54.88 / 56 - 1` com `-0.02`
podia rejeitar a igualdade por arredondamento binário. Os limites passam a ser
comparados na base bruta, com tolerância de 1e-12 para essa igualdade, preservando
a regra inclusiva. Um teste confronta simulador e reconciliação sintética.

Os campos explicam unidade, exemplo, consequência e valor aplicado. Digitar
`5` em concentração significa **5%**, aproximadamente R$ 5.000 sobre R$ 100.000.
A prévia mostra a faixa inclusiva, limites contraditórios, redundância entre
preço máximo e gap de alta e o bloqueio por queda excessiva, mesmo com compra
mais barata. A validação definitiva continua no backend.

O cenário usa a posição supervisionada atual, a direção validada e os custos
originais; COMPRA não vira VENDA para atingir o teto. Uma decisão de outra
marca temporal não produz estimativas financeiras sobre um ledger posterior.
MANTER, veto e venda sem posição não são promovidos a operações.

Limites/gap usam bruto oficial. Para estimar os valores, o preço hipotético é
convertido pelo fator ajustado/bruto do último fechamento congelado, com hash da
série conferido. A abertura e o fechamento **sintéticos em memória** são iguais:
patrimônio e concentração exibidos são na abertura, descontados os custos.
Proventos futuros podem mudar o fator; a estimativa não prevê essa mudança.
Quantidade fracionária é expressa na base ajustada do ledger.

### Caso registrado de 09/10/2026

Referência bruta R$ 56; máximo R$ 56; gaps de alta/baixa 2%; concentração 5%.
A faixa resultante é **R$ 54,88 a R$ 56,00, inclusive**.

| Abertura hipotética | Resultado | Condição |
|---|---|---|
| R$ 54,00 | Bloqueada | Gap de baixa maior que 2% |
| R$ 54,88 | Permitida | Extremo inferior inclusivo |
| R$ 55,00 | Permitida | Dentro de todos os limites |
| R$ 56,00 | Permitida | Extremo superior inclusivo |
| R$ 56,50 | Bloqueada | Preço máximo de compra |
| R$ 57,50 | Bloqueada | Gap de alta e preço máximo |

Com R$ 55 e carteira em caixa: valor da compra R$ 4.999,795008;
90,905363789 unidades ajustadas; custos R$ 4,099832; caixa R$ 94.996,105160;
patrimônio R$ 99.995,900168; concentração após custos **5%**. Os casos foram
verificados sobre os registros reais somente para leitura e no Chrome. Os testes
automatizados reproduzem a referência de R$ 56 em fixtures sintéticas, sem
depender de futuras mudanças legítimas da carteira real.

## Fase B — pesquisa e escolha de fonte

Pesquisa em 11/10/2026, exclusivamente em fontes dos fornecedores. Não foi
contratado serviço ou aceita licença. Escolha: **cache oficial histórico local +
`OfflineProvider` para intradiário indisponível**. O fallback solicitado permite
entregar o monitor sem atribuir tempo real a fontes que não o comprovam.

| Fonte considerada | PETR4, atraso e abertura | Preço, quotas e acesso | Uso e estabilidade |
|---|---|---|---|
| B3 UMDF / distribuidores licenciados | Segmento de ações; tempo real ou atraso de 15 min. Abertura exige contratação e validação do feed específico | Contrato, tarifas fixas/variáveis e cotação do distribuidor; não é uma API pública gratuita | Procedência da bolsa; obrigações de distribuição e infraestrutura próprias |
| Site de cotações B3 | Ações com atraso de 15 min; exibição começa 15 min após a abertura | Consulta web pública; nenhuma quota/SLA de API validada | Não foi usado scraping para simular um feed de abertura |
| brapi | PETR4 no sandbox sem token. Atualização publicada: grátis 30 min, Startup 15 min, Pro 5 min; não comprova o leilão em tempo real | Grátis 15 mil/mês; Startup 150 mil; Pro 500 mil. Sandbox 20/min/IP. Página exibe anual equivalente R$ 99,99 e R$ 116,66/mês, cobrados anualmente; não confundir com contratação mensal | Página declara finalidade informativa e planos pagos comerciais; link de termos retornou 404 nesta consulta. Há página de status; nenhum SLA de abertura foi validado |
| Yahoo / yfinance | PETR4.SA já é usado pelo projeto para o fator histórico; não há comprovação de abertura oficial em tempo real | Biblioteca existente; quota/preço/SLA de dados não validados | Projeto não afiliado ao Yahoo, uso educacional/pessoal segundo README; acesso à página PETR4.SA retornou HTTP 429 nesta revisão |
| Cache congelado existente | Bruto B3 COTAHIST e série ajustada já registrados, com sessão, coleta, origem e SHA256 | Sem novas requisições, credencial, custo ou polling | Escolhido para o histórico. Disponibilidade limitada ao que já foi congelado; intradiário explicitamente ausente |

Fontes consultadas:

- [B3 Market Data: acesso, atraso e contratos](https://www.b3.com.br/en_us/market-data-and-indices/data-services/market-data/distributors/faq/).
- [Cotações públicas B3 e atraso](https://b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/).
- [brapi: preços, atualização, quotas e sandbox](https://brapi.dev/pricing),
  [frequência](https://brapi.dev/faq/qual-a-frequencia),
  [status](https://status.brapi.dev/),
  [link de termos indisponível na revisão](https://brapi.dev/terms-of-use).
- [yfinance: finalidade e direitos de uso dos dados](https://github.com/ranaroussi/yfinance).
- [Grade B3, Ofício 005/2026-PRE, anexo 3](https://www.b3.com.br/data/files/E3/B2/C2/12/BC09C910F37907C9AC094EA8/OC%20005-2026%20PRE%20NOVOS%20HORARIOS%20DE%20NEGOCIACAO_PT.pdf).

### Contrato substituível

`dashboard.market_api.QuoteProvider.quote(ticker, at)` retorna preço bruto em
reais, timestamp com fuso, fonte e classificação: `realtime_verified`,
`delayed`, `official_close` ou `unknown`. Tempo real exige também metadado
`realtime_evidence` do adapter confiável; a ausência rebaixa a classificação.
Metadados inválidos, timestamp futuro, preço inválido ou falha do provider
produzem indisponibilidade. Quotes são normalizados para BRT; timestamp de
outro dia ou idade maior que 30 min sinaliza desatualização.

Um futuro adapter substitui `market_api.PROVIDER` no backend. Deve implementar
timeout, cache, limite de requisições e verificar a licença/fonte. O browser não
aceita URLs arbitrárias de provider. O adapter atual não acessa a rede, não
exige chave, não grava observações e não inicia serviço adicional.

O fechamento histórico mostra a sessão separada do **timestamp de coleta
registrado no input**, sem inventar horário do último negócio. SMA50/200,
RSI14 e MACD 12/26/9 reutilizam as funções existentes em `src.indicators`, somente
lidas; a volatilidade vem da decisão Risk registrada. A procedência informa
que a série é ajustada e identifica o hash. Não há indicador intradiário.

## Fase C — Mercado e navegação

Mercado é a quinta área operacional. Exibe fechamento, coleta, próxima sessão,
abertura prevista, estado pelo calendário/relógio, observação intradiária e
limites de aprovações ativas. Estados: dentro/fora do limite, aguardando
abertura, dados insuficientes e informação desatualizada. Cotação atrasada é
somente informativa e nunca afirma execução na abertura. Concentração executada
não pode ser deduzida apenas da cotação e aparece como dado insuficiente.

A grade de horário foi verificada para março–outubro de 2026: pré-abertura
09:45–10:00; sessão regular até 17:00, incluindo call final. Fora desse intervalo
de datas, sessão útil fica desconhecida e a próxima hora não verificada fica
indisponível. A previsão não atesta leilão, suspensão, prorrogação ou after-market.
O calendário existente reconhece o feriado de **12/10/2026**; próxima sessão
após 09/10 é **13/10 às 10:00 BRT**.

Mercado atualiza manualmente, com cancelamento da consulta anterior. A prévia
de limites aguarda 300 ms após digitação, cancela requisições anteriores e
descarta respostas de decisões antigas. Não há novo polling. Carregar a página
continua sem POST; POSTs de cenário só ocorrem após interação com o formulário.
Histórico hipotético fica apenas na tela: não entra em auditoria ou ledger.

## Arquivos e endpoints

| Arquivo | Mudança |
|---|---|
| `scripts/run_h2_v6_supervised.py` | Helpers puros compartilhados; `resolve` delega a avaliação |
| `dashboard/market_api.py` | Simulador sem escrita, adapter e monitor de Mercado |
| `dashboard/server.py` | Rotas locais, JSON estrito e CSRF no novo POST |
| `dashboard/paper.html`, `paper.js`, `paper.css` | Quinta área, formulário explicado, faixa e estimativas |
| `tests/test_h2_premium_v3.py` | 11 casos parametrizados; fixtures reaproveitadas |
| Este documento e `docs/evidence/h2_premium_v3/` | Pesquisa, resultados, hashes e capturas |

- `GET /api/forward/market`: registros históricos e observações informativas.
- `POST /api/forward/scenario`: JSON exato com `decision_session`,
  `decision_sha256`, `limits` e `hypothetical_open`. Preço nulo consulta só a
  prévia; preços de R$ 0,01 a R$ 1.000.000 calculam o cenário. Não exige uma
  confirmação de aprovação porque não realiza ação humana ou escrita.

As duas rotas herdam Host/Origin/loopback. O POST exige CSRF, content type,
limite de corpo, chaves únicas/exatas, números finitos e validação dos limites.
Hash de decisão incorreto ou auditoria inválida falha de modo fechado.
Os endpoints anteriores mantêm suas confirmações e o fluxo pago separado.

## Verificação

Regressão focada: **79 passed**, cobrindo V3, supervisão, dashboard e forward.
Após os últimos ajustes de metadados e apresentação, repetição direcionada:
**12 passed**. Ruff nos quatro arquivos Python alterados, `node --check` e
`git diff --check` passaram. Testes sem chaves Gemini, com conexões e DNS externos
bloqueados; só loopback para segurança HTTP. Nenhum teste inicializa a carteira
real. Fixtures cobrem todas as 32 combinações de campos de compra e 16 de venda,
posição preexistente, custos, direção contrária, limites contraditórios,
volatilidade ausente, bruto/ajustado, calendário, ausência de dados, quotes
atrasadas/obsoletas/inválidas, rejeição de payload e ausência de escrita.

Reprodução (pytest precisa de diretório temporário gravável):

```powershell
.venv/Scripts/python.exe -m pytest tests/test_h2_premium_v3.py tests/test_h2_v6_supervised.py tests/test_h2_forward_dashboard.py tests/test_h2_v6_forward.py -q --basetemp="$env:TEMP/hfl-v3-check-$([guid]::NewGuid())"
.venv/Scripts/python.exe -B scripts/check_h2_forward_dashboard.py
.venv/Scripts/python.exe -B scripts/run_h2_v6_supervised.py verify
```

**Integridade:** 265 arquivos científicos idênticos à baseline anterior, mais
13 arquivos dos ledgers/inputs/decisões/aprovações idênticos à baseline capturada
antes do V3. Carteira real: R$ 100.000, zero unidades, zero ações humanas;
auditoria íntegra com um evento `PROPOSED`. Sem mudança em `src/`, manifesto,
parâmetros, Validation OA-1, Final Test ou decisão original.

**Suíte geral anterior, separada:** não foi reexecutada nesta entrega. O
[registro V2](evidence/h2_premium_v2/recheck/verification.json) documenta 1499
aprovados e 10 falhas: sete dependem do PostgreSQL ausente na porta 5435, três
são expectativas históricas desatualizadas em `test_cal_b4_safety`, `test_spec`
e `test_v6_phase_routing`. Não são resultados medidos novamente no V3.

## Capturas

Chrome real, larguras 1440, 640 e 420 px; sem transbordamento horizontal e sem
erros/warnings no console. Regressão visual das outras três áreas verificou
navegação e os 32 slots do catálogo. Nenhum controle de aprovação foi acionado.

| Tela | 1440 px | 640 px | 420 px |
|---|---|---|---|
| Mercado | [captura](evidence/h2_premium_v3/market-1440.jpg) | [captura](evidence/h2_premium_v3/market-640.jpg) | [captura](evidence/h2_premium_v3/market-420.jpg) |
| Cenário permitido | [captura](evidence/h2_premium_v3/scenario-1440.jpg) | [captura](evidence/h2_premium_v3/scenario-640.jpg) | [captura](evidence/h2_premium_v3/scenario-420.jpg) |

[Cenário bloqueado em 420 px](evidence/h2_premium_v3/scenario-blocked-420.jpg).
[Medições e resultados no navegador](evidence/h2_premium_v3/browser-checks.json).
[Verificação consolidada](evidence/h2_premium_v3/verification.json).

## Limitações e Git

Não há feed intradiário habilitado: o painel mostra literalmente **Cotação
intradiária indisponível**. Só dados já congelados são lidos; consultar Mercado
não baixa o próximo fechamento. A sessão é uma previsão, e o simulador usa o
último fator conhecido. Só a reconciliação oficial existente pode registrar
execução virtual. Há apenas um fechamento prospectivo, sem série de desempenho
suficiente para inferências sobre o filtro humano.

Implementação no commit local `9208352`. Documentação e evidências em commit
local subsequente. A verificação consolidada registra o código testado; o
log local identifica o commit das evidências. Nenhum push foi executado.
