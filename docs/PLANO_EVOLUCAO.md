# Plano de evolução do Hedge-Fund-Lab

O objetivo é chegar a uma arena reproduzível em que as cinco estratégias
clássicas e a estratégia LLM de três estágios concorram sob o mesmo protocolo.
O plano prioriza validade experimental antes de otimização, UI ou operação em
tempo real.

## Decisões recomendadas

| Tema | Recomendação inicial | Motivo |
|---|---|---|
| Unidade experimental | Carteira multi-ativo comum aos seis participantes | É coerente com “hedge fund” e permite ao gestor LLM realmente gerir portfólio. |
| Universo inicial | Os 10 ativos já carregados, com análise secundária PETR4/WEGE3 | Evita comparar média de single-assets com carteira e preserva o recorte acadêmico. |
| Relógio | Features no fechamento de `t`; execução na abertura de `t+1` | Comparável e sem execução impossível no mesmo fechamento observado. |
| Quorum | Manter 30 e 25/30, nomeando-o ensemble controlado | Preserva a hipótese atual sem fingir diversidade de especialistas. |
| Risco | Limites determinísticos obrigatórios; LLM apenas complementa | Segurança e reprodutibilidade. |
| Position sizing | Não usar confiança LLM como probabilidade de Kelly até calibrar | Confiança textual não é probabilidade observada. |
| Custos | Uma especificação versionada e aplicada a todos | Sem isso Sharpe líquido e turnover não são comparáveis. |
| Resultado | Um `RunResult` canônico por participante e spec | Remove agregações e métricas ad hoc. |
| Tempo real | Fora do caminho crítico até a arena histórica estar válida | MT5/BRAPI adicionariam risco sem validar a hipótese principal. |

Essas recomendações precisam ser aprovadas pela dupla e refletidas na monografia
antes do experimento final.

## Fase 0 — Congelar a baseline

Objetivo: tornar explícito o ponto de partida sem alterar arquitetura.

- [x] Inventariar código, dados, testes e documentos.
- [x] Separar estado atual, arquitetura e plano.
- [x] Preservar a decisão acionável do último pregão como `PREDICTED`, sem
  execução nem impacto nas métricas; registrar sessão-alvo, execução e rejeição
  nas decisões históricas.
- [ ] Fazer a suíte completa, Ruff e o subconjunto obrigatório de tipos ficarem
  verdes.
- [ ] Parar de versionar logs e remover credenciais de URLs logadas.
- [ ] Registrar decisões metodológicas em uma seção curta de ADRs ou neste plano.

Critério de saída: zero teste funcional falhando; comandos de qualidade com
resultado conhecido e documentação sem afirmar mais do que o código entrega.

## Fase 1 — Núcleo científico comum

Objetivo: corrigir dados, tempo, execução, custo e métricas antes de criar arena.

### Dados

- [ ] Validar intervalo solicitado no cache e recortar exatamente `[start, end]`.
- [ ] Adicionar gate de qualidade para unicidade, OHLC positivo e consistente,
  volume, ordenação e datas.
- [ ] Remover/rejeitar as dez barras finais inválidas encontradas na baseline.
- [ ] Registrar fonte, horário de download, parâmetros de ajuste, hash e cobertura
  em um manifest de snapshot.
- [ ] Fazer cargas parciais falharem de modo observável ou emitirem status parcial
  consumível por automação.
- [ ] Adotar migrations antes de mudar schema.

### Execução

- [ ] Definir ordem normalizada: ticker, direção, quantidade/peso alvo, instante de
  decisão e primeira data elegível de execução.
- [ ] Fazer todos os sinais de fechamento executarem apenas em `t+1`.
- [ ] Corrigir custo de compra/short para usar valor total da ordem.
- [ ] Reservar custo no cálculo de quantidade e proibir caixa negativo.
- [ ] Definir venda a descoberto: suportar completamente ou rejeitar configuração.
- [ ] Aplicar a mesma política de lote, slippage, spread, corretagem e emolumentos.

### Métricas

- [ ] Ter uma única implementação de Sharpe, Sortino, drawdown, retorno,
  volatilidade, turnover, custos e exposição.
- [ ] Corrigir agregação temporal e volatilidade do scatter.
- [ ] Distinguir retorno total, retorno anualizado e valores percentuais nas APIs.
- [ ] Testar as invariantes com exemplos pequenos que falham no código atual.

Critério de saída: os cinco clássicos rodam pelo mesmo motor, com curvas líquidas,
sem same-bar execution e com manifests reproduzíveis.

## Fase 2 — Arena de participantes

Objetivo: eliminar scripts de comparação específicos por estratégia.

- [ ] Definir um contrato mínimo de participante que recebe estado observável e
  devolve ordens/pesos alvo.
- [ ] Adaptar Buy & Hold, SMA Cross, Bollinger, Equal Weight e Mínima Variância.
- [ ] Adaptar o grafo LLM sem permitir que ele altere caixa/posição diretamente.
- [ ] Criar `ExperimentSpec`: snapshot, universo, split, capital, frequência,
  custos, benchmark, seeds e participante.
- [ ] Criar `RunResult` e manifest comuns.
- [ ] Executar todos no mesmo calendário e intervalo.
- [ ] Persistir resultados por `run_id`, sem usar nome de arquivo como identidade.
- [ ] Permitir que o mesmo runner opere em dois modos: replay histórico completo
  e avanço diário de exatamente um pregão.
- [ ] Persistir previsão pendente com `as_of`, próximo pregão elegível, validade,
  ordens e status; reconciliá-la antes de gerar a previsão seguinte.
  O backtest LLM já persiste o subconjunto `as_of`, `target_session`, status e
  execução; ainda faltam validade, ordem canônica, armazenamento entre processos
  e reconciliação do runner diário.
- [ ] Resolver calendário da B3 para que “amanhã” signifique próxima sessão, não
  simplesmente data atual + 1 dia.
- [ ] Remover as classes single-asset vestigiais de Equal Weight/Min Variance só
  depois que nenhum caller depender delas.

Critério de saída: uma única chamada da arena produz seis resultados comparáveis
e auditáveis, e o dashboard apenas os consome.

## Fase 3 — Endurecer o participante LLM

Objetivo: tornar o quorum reprodutível, mensurável e resistente a concorrência.

- [ ] Separar nome do provedor, protocolo HTTP e modelo; confirmar contrato do
  endpoint usado em documentação oficial antes de fixá-lo.
- [ ] Enviar apenas opções suportadas e confirmar se seed é efetivamente aceita.
- [ ] Usar structured output nativo quando disponível, com fallback explícito.
- [ ] Tornar cache concorrente seguro e incluir provedor, modelo, prompt version,
  schema, opções e snapshot na chave.
- [ ] Tornar retry e telemetria locais à chamada, nunca estado global mutável.
- [ ] Registrar sucesso/falha, latência, tokens, custo real/estimado, cache hit,
  retries, agente, data e hash do prompt por evento.
- [ ] Corrigir dry-run para emitir intervalo mínimo/máximo e separar chamadas
  lógicas de chamadas externas pagas.
- [ ] Garantir fail-closed em quorum, risco e portfólio para erros de rede, parse e
  persistência.
- [ ] Calibrar confiança ou substituir Kelly por sizing determinístico no primeiro
  experimento.
- [ ] Evoluir o estado para carteira multi-ativo: posições, caixa, pesos,
  correlações, limites globais e ordens por ticker.

### Desenho do quorum

O quorum de 30 deve ser tratado como variável experimental, não como garantia de
qualidade. Registrar e comparar pelo menos:

1. um analista determinístico;
2. 30 amostras do mesmo modelo com diversidade controlada;
3. opcionalmente, modelos heterogêneos, se orçamento e hipótese justificarem;
4. ablações de limiar e exigência de todos os votos.

Critério de saída: uma execução pequena pode ser repetida a partir do manifest,
tem custo conhecido e não perde votos por corrida local.

## Fase 4 — Protocolo experimental

Objetivo: produzir evidência defendível, não apenas curvas bonitas.

- [ ] Aprovar universo e splits cronológicos sem sobreposição.
- [ ] Usar treino somente onde há estimação; validação para parâmetros/prompts; e
  teste final congelado executado uma vez.
- [ ] Implementar walk-forward como análise de robustez.
- [ ] Fixar parâmetros dos cinco benchmarks antes do teste.
- [ ] Definir taxa livre de risco e benchmark de mercado.
- [ ] Executar sensibilidade a custos, frequência e quorum.
- [ ] Reportar dispersão por subperíodo, ativo e seed, não apenas uma média.
- [ ] Aplicar teste estatístico adequado às séries dependentes e declarar suas
  premissas; não escolher teste somente depois de ver o ranking.
- [ ] Versionar tabela final, curvas, drawdowns, turnover e custos com `run_id`.

Critério de saída: qualquer número da monografia aponta para um run reproduzível,
e qualquer participante foi avaliado sob a mesma `ExperimentSpec`.

## Fase 5 — Produto e visualização

Objetivo: transformar resultados confiáveis em ferramenta de exploração.

- [ ] Dashboard consultar catálogo de runs em vez de um JSON único de 16 MB.
- [ ] Exibir LLM junto dos clássicos apenas quando a spec for idêntica.
- [ ] Mostrar badges claros para mock, validação, teste e experimento final.
- [ ] Adicionar custos, turnover, intervalo, universo, modelo e prompt version.
- [ ] Criar job id, status, cancelamento e isolamento de logs.
- [ ] Fazer mock ser o padrão da UI; exigir confirmação explícita para chamada paga.
- [ ] Escapar conteúdo de logs e restringir bind/autenticação se sair de localhost.

Critério de saída: a UI não inicia gasto por acidente, não mistura runs e consegue
explicar de onde veio cada gráfico.

## Fase 6 — Monografia e entrega

- [ ] Remover resumos, abstracts, introduções e subseções duplicadas.
- [ ] Resolver todos os blocos `verify`/`remarks`.
- [ ] Trocar futuro por passado somente para itens realmente implementados.
- [ ] Corrigir “grafo cíclico” se a arquitetura continuar linear.
- [ ] Alinhar dois ativos versus dez ativos e justificar análise principal e
  secundária.
- [ ] Descrever quorum como ensemble quando essa for a implementação.
- [ ] Gerar tabelas e figuras a partir dos manifests finais, sem copiar valores à
  mão.

Critério de saída: texto, código, configuração e artefatos finais descrevem o mesmo
experimento.

## Backlog priorizado

| Prioridade | Item | Impacto se adiado |
|---|---|---|
| P0 | Motor comum com execução `t+1` | Toda comparação permanece inválida |
| P0 | Custos e caixa corretos | Resultados líquidos incorretos |
| P0 | Gate de qualidade e snapshot | Experimento pode usar barras inválidas/mutáveis |
| P0 | Unidade experimental comum | LLM e clássicos continuam incomparáveis |
| P0 | Run spec/result canônicos | Não há reprodutibilidade |
| P1 | Cache/retry concorrentes seguros | Votos e telemetria podem se perder |
| P1 | Contrato real do provedor/seed/schema | Quorum não corresponde à configuração declarada |
| P1 | Splits e congelamento | Risco de data snooping e ajuste no teste |
| P1 | Métricas e agregação únicas | Rankings e gráficos podem ser enganosos |
| P1 | CI, teste, lint e tipos verdes | Regressões ficam fáceis de introduzir |
| P2 | Dashboard por run e job control | Operação local frágil e pouco explicável |
| P2 | Reorganização física dos módulos | Código segue duplicado, mas sem invalidar ciência |
| P3 | MT5, BRAPI, notícias e tempo real | Aumenta escopo antes de provar o núcleo |

## Definição de pronto do primeiro experimento sério

Um resultado só pode entrar na comparação principal quando:

- usa snapshot validado e imutável;
- tem universo, período e calendário idênticos aos demais;
- decide com informação até `t` e executa em `t+1`;
- usa o mesmo capital, custo, lote e slippage;
- possui manifest com versões, parâmetros, seeds, modelo e prompts;
- deriva métricas do módulo canônico sobre curva líquida;
- registra falhas e não mistura mock/cache com chamadas reais sem identificação;
- foi produzido após congelamento de parâmetros e antes de examinar o teste final;
- pode ser reexecutado por outra máquina a partir do repositório e do snapshot.

Para o ciclo diário, também deve ser possível provar que cada ordem executada na
abertura veio de uma previsão imutável gerada após o fechamento anterior, e que a
última previsão ainda não executada está identificada como pendente e excluída
das métricas realizadas.

Até essa definição ser cumprida, a saída deve carregar o rótulo
**DEMONSTRAÇÃO TÉCNICA — NÃO CIENTÍFICA**.
