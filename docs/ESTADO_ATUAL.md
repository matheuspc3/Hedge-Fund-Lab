# Estado atual do Hedge-Fund-Lab

Baseline auditada em **08/09/2026** sobre o estado versionado da branch
`#1-Update`. O objetivo deste documento é responder até onde o projeto chega hoje
e evitar que planos antigos sejam confundidos com implementação. Capacidades e
limitações descritas como parte do sistema são evidência do repositório;
contagens de banco, execuções e medições identificadas como locais são evidência
observada no ambiente da auditoria e não conteúdo versionado no Git.

## Conclusão executiva

O projeto já é um bom **protótipo técnico de laboratório quantitativo**. Ele
coleta e persiste dados, calcula indicadores, executa cinco benchmarks clássicos,
possui dashboard e contém um fluxo LLM auditável de três estágios cujo primeiro
estágio é um quorum configurável de 30 chamadas.

Ele ainda **não é a arena científica descrita como objetivo**. As estratégias
clássicas e o sistema LLM continuam em motores diferentes, embora agora adotem o
mesmo relógio fechamento de `t` -> abertura de `t+1`; o LLM não aparece na
comparação principal; e não existe orquestrador de experimento, divisão
train/validation/test ou walk-forward. Portanto, os números exibidos no
dashboard e os JSONs de agentes são demonstrações técnicas, não evidência de que
uma abordagem venceu outra.

## O que existe hoje

| Área | Status | O que realmente faz |
|---|---|---|
| Dados | Implementado com lacunas | Baixa OHLCV diário pelo `yfinance`, mantém cache CSV por ticker, valida estrutura, finitude e consistência OHLCV, calcula indicadores e persiste em PostgreSQL ou SQLite via SQLAlchemy. |
| Persistência | Implementado | Tabelas de ativos, cotações e indicadores, com unicidade por ativo/data e atualização em conflito nos caminhos principais. |
| Indicadores | Implementado | SMA 50/200, Bollinger 20/2, RSI 14 e MACD 12/26/9. |
| Estratégias clássicas | Implementado | Buy & Hold, SMA Cross e Bollinger single-asset; Equal Weight e Mínima Variância multi-ativo. |
| Backtest clássico | Bloqueado para ciência | Single e multi-asset decidem com dados até o fechamento de `t`, executam na abertura observada de `t+1`, calculam custos sobre o notional e preservam caixa não negativo. Retorno, risco, drawdown e custo total agora vêm do módulo canônico, mas o dashboard ainda usa custo zero e não há motor comum. |
| Sistema de agentes | Parcial | Quorum técnico -> risco -> portfólio em LangGraph, com contratos Pydantic e regras duras. Opera um ticker por execução. |
| Quorum de 30 | Implementado com ressalvas | Faz 30 chamadas concorrentes do mesmo papel e cliente, variando prompt, temperatura e seed registrado. Exige 25/30 por padrão e todos os votos válidos. |
| Cliente LLM real | Parcial | Cliente HTTP OpenAI-compatible, retry, cache e telemetria básica. A integração específica chamada de OmniRouter/Agent Router não está isolada nem comprovada no repositório. |
| Backtest LLM | Implementado com lacunas | Decide no fechamento de `t`, executa na próxima abertura observada e registra ciclo, votos, trades e curva em JSON. A última previsão fica pendente. |
| Runner diário | Parcial | `DailyAgentRunner` persiste estado, reconcilia a previsão pendente na abertura esperada e avança uma sessão por execução. Ainda não integra a arena nem um manifest canônico. |
| Calendário B3 | Parcial | `B3Calendar` resolve fins de semana, feriados recorrentes e exceções explícitas sem dependência externa; ainda precisa de validação/versionamento contra calendário oficial. |
| Arena clássicos x LLM | Planejado | Não existe participante comum, motor comum nem resultado consolidado. |
| Dashboard | Parcial | Compara as cinco estratégias clássicas e exibe indicadores. Uma tela separada dispara backtest LLM, mas não incorpora o resultado à arena. |
| Avaliação científica | Planejado | Não existem `src/evaluation`, splits temporais, walk-forward, testes de hipótese, análise de sensibilidade ou exportação científica. |
| Operação em tempo real/MT5/BRAPI | Planejado | O runner diário é simulação persistente; integrações de mercado e execução automática não existem. |

## Fluxos executáveis

### Pipeline e dashboard clássico

`just run` encadeia:

1. `src.pipeline.flows.pipeline_etl`;
2. extração ou leitura do cache;
3. limpeza e indicadores;
4. carga no banco;
5. `scripts/generate_dashboard_data.py`;
6. três backtests single-asset agregados e dois multi-ativo;
7. geração de `dashboard/data.json`;
8. servidor HTTP local em `http://localhost:8081`.

No estado auditado, o PostgreSQL local contém 10 ativos, 26.390 cotações e
26.390 registros de indicadores, sem duplicatas de ativo/data, cobrindo
04/01/2016 a 05/08/2026. Cada ticker tinha uma barra final com algum OHLC igual
a zero. O gate atual rejeita essas barras em novas execuções, mas não repara
automaticamente dados inválidos já persistidos antes desta validação.

### Backtest multiagente

`scripts/run_agent_backtest.py` lê um ticker do banco, seleciona os últimos `N`
pregões, constrói um grafo e executa:

1. **Comitê técnico**: 30 pareceres concorrentes por padrão.
2. **Agregação**: compra, venda ou manter exige 25/30; falha obrigatória força
   `MANTER`.
3. **Risco**: vendas/manutenção passam sem aumentar exposição; compras passam por
   volatilidade, drawdown e concentração antes da análise LLM.
4. **Portfólio**: limita compras por fractional Kelly, tamanho máximo e espaço de
   concentração; depois pede decisão ao LLM sem permitir inversão do sinal.
5. **Execução**: uma decisão de `t` vira ordem para a abertura de `t+1`.
6. **Auditoria**: salva curva, trades, decisões, votos e telemetria em JSON. Cada
   decisão inclui `as_of`, `target_session`, `status`, `execution_date`,
   `execution_price` e justificativa de status.

No replay histórico, `target_session` é a próxima data realmente observada no
índice, portanto sexta-feira aponta para a barra de segunda-feira quando ela
existe. A última decisão acionável permanece `PREDICTED`, sem trade nem impacto
nas métricas. Uma decisão executada vira `EXECUTED`; `MANTER` vira `NO_ACTION`;
veto ou ordem impossível vira `REJECTED`. Como o replay não deve inventar dados,
a última previsão ainda fica com `target_session=null`.

### Runner diário

`scripts/run_agent_daily.py` usa `DailyAgentRunner` para avançar exatamente uma
sessão por execução. O runner persiste caixa, posição, custos, curva, trades,
decisões e última sessão em JSON; mantém no máximo uma previsão `PREDICTED`;
reconcilia essa previsão na abertura da sessão-alvo; e só então gera a previsão
seguinte. O estado é gravado por substituição atômica e protegido por lock local
contra dois processos no mesmo host.

`B3Calendar` já resolve a próxima sessão por fins de semana, feriados recorrentes
e conjuntos explícitos de fechamentos/aberturas excepcionais. É uma aproximação
local, não um feed oficial: exceções futuras ainda precisam ser conferidas e
versionadas para uso científico. O runner também continua single-asset e separado
da arena clássica.

O chamado “gestor de portfólio” ainda dimensiona uma posição de **um único
ativo**. Ele não recebe o universo de ativos, correlações, pesos correntes da
carteira ou restrições globais. O quorum é um ensemble estocástico de um papel,
não 30 especialistas ou 30 modelos independentes.

## Evidência de validação

As verificações abaixo foram observadas no ambiente local durante a auditoria;
seus resultados não são, por si só, conteúdo versionado no Git:

| Verificação | Resultado |
|---|---|
| Suíte de pipeline com SQLite em memória (`poetry run pytest tests/pipeline -q`) | **94 passaram** em 08/09/2026 |
| Suíte completa com SQLite em memória (`poetry run pytest -q`) | **341 passaram** em 08/09/2026 |
| Cobertura (última medição, anterior a esta mudança) | **95%** |
| Ruff | **14 violações preexistentes fora dos arquivos desta mudança** |
| Ruff nos arquivos desta mudança | **verde** |
| Pyright nos arquivos desta mudança | **verde** |
| Pyright no escopo configurado (última medição) | **181 erros** |
| Banco PostgreSQL local | 10 ativos; 26.390 datas únicas de cotação e indicadores |
| Duplicatas ativo/data | 0 |
| Barras com algum OHLC não positivo | 1 por ticker, na última data |

O conflito da última previsão foi resolvido no contrato e nos testes: ela é
preservada como `PREDICTED`, sem `execution_date` ou `execution_price`, e não
entra em trades ou desempenho até ser reconciliada por uma abertura futura.

A cobertura alta comprova que muito código foi exercitado, mas não valida o
desenho experimental. O antigo teste “sem look-ahead”, que esperava compra pelo
fechamento da própria barra do sinal, foi substituído por casos explícitos que
distinguem `close(t)` de `open(t+1)` e rejeitam trade na última decisão.

## Problemas que invalidam a comparação atual

### 1. Motores separados

Os motores LLM, clássico single-asset e clássico multi-asset agora compartilham
a semântica observação até o fechamento de `t` e execução na abertura de `t+1`.
Eles ainda são implementações separadas, sem ordem canônica, arena ou modelo de
execução único; portanto, o relógio equivalente ainda não basta para produzir
uma competição científica comum.

### 2. Custos não comparáveis

O dashboard instancia todos os motores com `CostModel()` padrão, isto é, custo
zero. Os motores agora calculam custos percentuais sobre
`abs(quantity * execution_price)`, reservam esses custos antes da compra e não
deixam o caixa negativo. Os valores científicos de corretagem, spread, slippage,
taxas e lotes continuam `TBD`; logo, os resultados do dashboard ainda não são uma
comparação líquida congelada.

O `allow_short=True` legado do single-asset agora é rejeitado explicitamente, e o
motor multi-asset rejeita pesos negativos. Isso evita ampliar um suporte que era
incompleto; política de margem, fechamento da posição e demais regras de short
continuam pendentes de decisão metodológica.

### 3. Participantes diferentes

As três estratégias single-asset são executadas separadamente nos dez ativos e
depois agregadas. Equal Weight e Mínima Variância são carteiras conjuntas. O LLM
opera apenas um ticker. Essas unidades experimentais não são equivalentes.

### 4. Métricas e agregação

- `src/backtesting/metrics.py` valida que a equity curve seja temporal, ordenada,
  única e finita, e concentra retornos, retorno total, CAGR técnico,
  volatilidade, Sharpe, Sortino, drawdown e duração de drawdown.
- A curva média single-asset usa explicitamente apenas a interseção das datas
  observadas por todos os tickers; sua composição não varia silenciosamente.
- O scatter consome retorno, volatilidade anualizada e Sharpe calculados
  diretamente da mesma equity curve; não reconstrói volatilidade por divisão.
- O período publicado vem do primeiro e último ponto efetivamente observado, e
  o custo total é a soma de `trade.cost` dos trades executados.
- O dashboard ainda não publica turnover, exposição, benchmark de mercado ou
  incerteza estatística. A definição legada de mudança média de pesos inclui
  drift e não foi promovida a turnover científico.
- `252` sessões/ano, taxa livre de risco zero e MAR zero são defaults técnicos
  configuráveis, não parâmetros experimentais congelados.

### 5. Protocolo experimental ainda não congelado nem implementado

Existe um protocolo documental em `docs/EXPERIMENT_PROTOCOL.md`, marcado como
**DRAFT — NÃO CONGELADO**. Ainda não existem splits, prompts, parâmetros ou
universo congelados; `ExperimentSpec`; run manifest; walk-forward; teste
out-of-sample; nem análise estatística implementada.

## Riscos técnicos relevantes

### Dados

- O cache continua usando apenas o ticker como chave. Um hit exige cobertura dos
  limites inicial e final inclusivos, e o retorno é recortado para o intervalo
  pedido. O `end` enviado ao `yfinance` permanece exclusivo e recebe um dia a
  mais que o limite público inclusivo.
- Quando a cobertura é insuficiente, a extração baixa novamente o intervalo
  completo solicitado, combina-o com o cache validado, mantém a resposta nova no
  overlap, deduplica, ordena e persiste o CSV atualizado.
- O gate fail-fast rejeita índice não temporal, `NaT`, duplicatas, desordem,
  colunas ausentes ou não numéricas, `NaN`, infinitos, OHLC não positivo ou
  inconsistente e volume negativo. Volume zero é aceito; `NaN` em volume é
  rejeitado. O forward-fill ficou restrito a colunas auxiliares após a primeira
  validação OHLCV.
- Ainda não há validação de calendário ou de lacunas internas entre os limites,
  moeda, timezone, ajuste por proventos/splits ou proveniência da fonte.
- O flow captura falha por ticker e termina sem relançar uma falha global; uma
  automação pode interpretar uma carga parcial como sucesso.
- `create_all()` não migra bancos existentes. Não há sistema de migrations.

### Agentes e LLM

- A opção `seed` é registrada no voto e na chave do cache, mas o cliente HTTP
  envia apenas `temperature`, `top_p` e `max_tokens`. A seed não chega ao modelo.
- O schema Pydantic é anexado ao prompt, porém não é enviado como structured
  output nativo (`response_format`/JSON Schema do provedor).
- Retry e telemetria compartilham um contador mutável entre chamadas concorrentes;
  o número de retries pode ser atribuído à chamada errada.
- O cache grava todas as chamadas concorrentes no mesmo arquivo temporário, sem
  lock. Isso cria risco de corrida, perda de entradas e votos inválidos.
- Falhas de conexão são agregadas com segurança no comitê técnico, mas risco e
  portfólio só capturam respostas inválidas; uma falha de rede após o quorum pode
  abortar o grafo.
- A confiança textual do LLM é usada como probabilidade de vitória na fórmula de
  Kelly, sem calibração empírica. Esse número ainda não pode ser tratado como
  probabilidade financeira.
- A telemetria registra tokens, latência, retry e modelo, mas custo permanece
  sempre zero e os eventos não têm vínculo explícito com run, data, agente ou
  hash de prompt.
- O dry-run subestima rodadas quando existe previsão no último dia e trata
  `analistas + 2` como número fixo, embora veto e `MANTER` evitem chamadas e cache
  evite chamadas externas. Hoje ele não é uma estimativa confiável de gasto.

### Dashboard e operação

- A arena principal não contém a estratégia LLM.
- `/lab` dispara processos sem fila, identificador, cancelamento ou endpoint de
  status; a conclusão é inferida por texto no log.
- A tela seleciona o provedor real por padrão e o servidor escuta em todas as
  interfaces. Não deve ser exposto fora de ambiente local.
- O endpoint trunca o log compartilhado antes de cada execução; duas execuções
  podem interferir uma na outra.
- Linhas de log, inclusive texto produzido pelo LLM, são inseridas no HTML sem
  escape na tela do laboratório.
- A aplicação ainda pode escrever informações sensíveis de configuração,
  incluindo senha do banco, no log. O diretório `data/logs/` não é mais
  versionado, mas a exposição local continua sendo um risco e o conteúdo logado
  deve ser sanitizado.
- `dashboard/data.json` gerado tem cerca de 16 MB e é carregado integralmente pelo
  navegador.

## Execuções LLM encontradas

Existem auditorias reais locais para PETR4 e WEGE3. Cada uma contém apenas duas
datas de decisão, terminou sem trades e não constitui experimento. Em WEGE3, uma
compra consensual foi vetada porque ainda não havia observações suficientes para
volatilidade. Outras rodadas tiveram quorum incompleto. Isso demonstra integração
com um modelo real e comportamento fail-safe em alguns caminhos, não desempenho.

## Documentação defasada ou contraditória

- `archive/PLAN_HEDGEFUND.md` descreve a intenção original e as fases 5–7, que
  não foram implementadas. A tabela de resultados é exemplo, não resultado
  observado.
- `archive/ROADMAP_IDEIAS.md` marca todo o sistema multiagente como pendente,
  embora uma primeira versão exista; esse roadmap foi substituído.
- `archive/HANDOFF_OUTRO_PC.md` diz que Prefect foi atualizado para 3.x; o
  `pyproject.toml` e o lock atuais usam Prefect 2.20.25.
- A monografia descreve um grafo cíclico capaz de pedir reavaliação; o grafo atual
  é linear e não possui retorno do risco ao analista.
- A monografia alterna escopo de dois ativos e universo de dez ativos, promete
  custo/turnover líquido ainda ausente e contém blocos duplicados de resumo,
  abstract, introdução, planejamento e considerações parciais.
- Marcadores `verify` e `remarks` permanecem no texto acadêmico e indicam trechos
  ainda não aprovados.

## Baseline honesta

O projeto pode ser apresentado hoje como:

> Protótipo de laboratório de dados e backtesting para ativos da B3, com cinco
> benchmarks clássicos, dashboard exploratório e uma primeira estratégia LLM
> single-asset organizada em quorum técnico, filtro de risco e dimensionamento de
> posição, com auditoria por decisão.

Ainda não deve ser apresentado como:

> Hedge fund autônomo, arena comparativa válida, sistema de negociação em tempo
> real, portfólio LLM multi-ativo ou evidência de superioridade de agentes.
