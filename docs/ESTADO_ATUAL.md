# Estado atual do Hedge-Fund-Lab

Baseline auditada em **08/09/2026**, considerando o diretório de trabalho local,
inclusive mudanças ainda não commitadas. O objetivo deste documento é responder
até onde o projeto chega hoje e evitar que planos antigos sejam confundidos com
implementação.

## Conclusão executiva

O projeto já é um bom **protótipo técnico de laboratório quantitativo**. Ele
coleta e persiste dados, calcula indicadores, executa cinco benchmarks clássicos,
possui dashboard e contém um fluxo LLM auditável de três estágios cujo primeiro
estágio é um quorum configurável de 30 chamadas.

Ele ainda **não é a arena científica descrita como objetivo**. As estratégias
clássicas e o sistema LLM usam motores e relógios de execução diferentes; o LLM
não aparece na comparação principal; não existe orquestrador de experimento,
divisão train/validation/test ou walk-forward; e os resultados clássicos atuais
possuem vieses e custos inconsistentes. Portanto, os números exibidos no
dashboard e os JSONs de agentes são demonstrações técnicas, não evidência de que
uma abordagem venceu outra.

## O que existe hoje

| Área | Status | O que realmente faz |
|---|---|---|
| Dados | Implementado com lacunas | Baixa OHLCV diário pelo `yfinance`, mantém cache CSV por ticker, calcula indicadores e persiste em PostgreSQL ou SQLite via SQLAlchemy. |
| Persistência | Implementado | Tabelas de ativos, cotações e indicadores, com unicidade por ativo/data e atualização em conflito nos caminhos principais. |
| Indicadores | Implementado | SMA 50/200, Bollinger 20/2, RSI 14 e MACD 12/26/9. |
| Estratégias clássicas | Implementado | Buy & Hold, SMA Cross e Bollinger single-asset; Equal Weight e Mínima Variância multi-ativo. |
| Backtest clássico | Bloqueado para ciência | Executa sinais, posições, custos opcionais, métricas e curvas, mas negocia na mesma barra usada para decidir e o dashboard usa custo zero. |
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
04/01/2016 a 05/08/2026. Cada ticker tem uma barra final com algum OHLC igual a
zero; a pipeline atual não a rejeita.

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

Verificações executadas nesta auditoria:

| Verificação | Resultado |
|---|---|
| Coleta atual do Pytest (`poetry run pytest --collect-only -q`) | **312 testes coletados** em 08/09/2026 |
| Última suíte completa documentada | **308 passaram** na auditoria anterior; não reexecutada nesta reorganização documental |
| Cobertura (última medição, anterior a esta mudança) | **95%** |
| Ruff | **14 violações preexistentes fora dos arquivos desta mudança** |
| Ruff nos arquivos desta mudança | **verde** |
| Pyright no escopo configurado (última medição) | **181 erros** |
| Banco PostgreSQL local | 10 ativos; 26.390 datas únicas de cotação e indicadores |
| Duplicatas ativo/data | 0 |
| Barras com algum OHLC não positivo | 1 por ticker, na última data |

O conflito da última previsão foi resolvido no contrato e nos testes: ela é
preservada como `PREDICTED`, sem `execution_date` ou `execution_price`, e não
entra em trades ou desempenho até ser reconciliada por uma abertura futura.

A cobertura alta comprova que muito código foi exercitado, mas não valida o
desenho experimental. Alguns testes hoje reforçam o comportamento enviesado; por
exemplo, o teste chamado “sem look-ahead” espera compra pelo fechamento da própria
barra do sinal.

## Problemas que invalidam a comparação atual

### 1. Relógios diferentes

O motor LLM observa o fechamento de `t` e executa na abertura de `t+1`. O motor
single-asset clássico calcula o sinal com o fechamento de `t` e negocia pelo
mesmo fechamento. O motor de portfólio calcula pesos com dados disponíveis até o
fechamento atual e rebalanceia no próprio fechamento. Não há competição justa
enquanto todos não usarem o mesmo relógio e modelo de execução.

### 2. Custos não comparáveis

O dashboard instancia todos os motores com `CostModel()` padrão, isto é, custo
zero. No motor clássico single-asset, o custo da compra e do short é calculado
sobre o preço unitário em vez do valor financeiro total, e a quantidade comprada
não reserva caixa para custos. A monografia, ao contrário, promete resultados
líquidos e análise de turnover.

### 3. Participantes diferentes

As três estratégias single-asset são executadas separadamente nos dez ativos e
depois agregadas. Equal Weight e Mínima Variância são carteiras conjuntas. O LLM
opera apenas um ticker. Essas unidades experimentais não são equivalentes.

### 4. Métricas e agregação

- A “curva média” single-asset é construída por `DataFrame.mean`, que aceita a
  união de datas e ignora ausências, embora o comentário diga interseção. A
  composição pode mudar ao longo da série.
- A volatilidade do scatter das carteiras é estimada dividindo retorno acumulado
  por Sharpe; isso não recupera a volatilidade anualizada correta.
- O dashboard não calcula nem publica turnover, custo total, benchmark de mercado
  ou incerteza estatística.
- `periodo` dos ativos no JSON vem da configuração, não das datas efetivamente
  observadas.

### 5. Ausência de protocolo experimental

Os splits 2016–2019, 2020–2021 e 2022–2025 aparecem no plano, mas não existem no
código. Não há congelamento de prompts, parâmetros e universo; run manifest;
walk-forward; teste out-of-sample; sementes da execução; nem teste estatístico.

## Riscos técnicos relevantes

### Dados

- O cache usa apenas o ticker como chave. Ele verifica se alcança a data final,
  mas não verifica a data inicial e retorna todo o arquivo sem recortar o
  intervalo solicitado.
- A atualização de rede baixa novamente o intervalo completo; “incremental” vale
  para a carga idempotente no banco, não para a extração.
- A limpeza apenas faz forward-fill, remove linhas totalmente nulas e ordena. Não
  valida OHLC, zeros, volume, calendário, duplicatas antes da carga, moeda,
  timezone, ajuste por proventos/splits ou proveniência da fonte.
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
- A configuração completa do banco, incluindo senha, é escrita no log; esse log
  está versionado no estado atual.
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
