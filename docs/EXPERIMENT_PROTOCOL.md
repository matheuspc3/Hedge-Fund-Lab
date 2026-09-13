# Protocolo experimental do Hedge-Fund-Lab

> **STATUS: DRAFT — NÃO CONGELADO**
>
> Este documento é o contrato científico do experimento, não um roadmap. Valores
> e políticas marcados como `TBD` ou `PENDENTE DE CONGELAMENTO` não foram
> aprovados pela dupla/orientador e não podem ser tratados como decisão final.

## 1. Research question

Sob os mesmos dados, informação disponível, relógio, capital, custos e modelo de
execução, qual é o efeito da utilização de um sistema multiagente baseado em LLM
sobre o desempenho líquido ajustado ao risco em comparação com abordagens
quantitativas clássicas?

**STATUS: PENDENTE DE CONGELAMENTO.** A redação final e a definição operacional
de desempenho líquido ajustado ao risco devem ser aprovadas antes do TEST.

## 2. Hypotheses

- Hipótese principal: `TBD`.
- Hipóteses nulas e alternativas formais: `TBD`.
- Critérios de aceitação/rejeição: `TBD`.
- Hierarquia entre hipótese principal e análises exploratórias: `TBD`.

Nenhuma hipótese será reformulada após observar o conjunto TEST sem ser marcada
como análise pós-hoc.

## 3. Universe

- Universo principal candidato: os 10 ativos já usados pelo projeto.
- Análises secundárias candidatas: PETR4 e WEGE3.
- Critérios de inclusão, exclusão, liquidez e sobrevivência: `TBD`.
- Tratamento de entradas, saídas e mudanças de ticker: `TBD`.

**STATUS: proposta / pendente de congelamento.** O universo principal deve ser
comum a todos os participantes.

## 4. Dataset/snapshot

Cada execução científica deve referenciar um snapshot imutável contendo, no
mínimo:

- fonte e parâmetros de download;
- cobertura solicitada e efetivamente observada por ativo;
- política de ajuste por proventos e splits;
- timezone, moeda e calendário;
- regras e relatório do gate de qualidade OHLCV;
- horário de obtenção, versão e hash dos arquivos;
- versão do pipeline de features.

Fonte definitiva, formato, localização, política de ajustes e schema do manifest:
`TBD`.

Implementação técnica atual, ainda sem congelar essas decisões: o
`DatasetSnapshot` materializa CSVs em diretório próprio, calcula SHA-256 por
arquivo e registra proveniência e cobertura por sessões do `B3Calendar` local.
O `ExperimentRunner` consome apenas esse artefato — nunca `yfinance` nem o cache
mutável —, recusa snapshot com `scientific_ready=false` e reconfere tamanho e
hash de cada arquivo antes de executar.

Capacidade técnica adicional, também sem congelar decisão científica alguma: o
manifest do snapshot possui identidade verificável. O `snapshot_id` é
`timestamp + digest` do JSON canônico do manifest menos o próprio ID, cobrindo
`quality`, `coverage`, `files`, `tickers`, intervalos, fonte, calendário e
pipeline; o carregamento reconfere o digest e o nome do diretório. Adulterar o
manifest — inclusive `scientific_ready` — é detectado, sem que isso substitua a
conferência dos SHA-256 dos CSVs. É tamper-evidence do artefato, não assinatura
criptográfica.
Lacunas, datas inesperadas ou intervalo sem sessões resultam em
`scientific_ready=false`; não há preenchimento de barras. O calendário é
explicitamente identificado como aproximação local com exceções configuráveis e
ainda requer validação contra fonte oficial/versionada.

## 5. Train / Validation / Test

- TRAIN: datas definitivas `TBD`.
- VALIDATION: datas definitivas `TBD`.
- TEST: datas definitivas `TBD`.

Os intervalos serão cronológicos, sem sobreposição. TRAIN será usado apenas onde
houver estimação; VALIDATION poderá orientar parâmetros e prompts; TEST será
aberto somente após congelamento. **STATUS: PENDENTE DE CONGELAMENTO.**

## 6. Walk-Forward

- Tipo de janela: `TBD`.
- Tamanho da janela de treino: `TBD`.
- Tamanho da janela de avaliação: `TBD`.
- Passo entre janelas: `TBD`.
- Política de reestimação: `TBD`.

O Walk-Forward será uma análise de robustez sem vazamento de informação futura.

## 7. Information available at t

Direção proposta: cada participante recebe somente dados confirmados e features
calculáveis até o fechamento da sessão `t`. A lista definitiva de campos, regras
de warm-up, defasagens de publicação e tratamento de ausências é `TBD`.

Nenhuma feature poderá incorporar a abertura ou qualquer dado de `t+1`.

## 8. Execution at t+1

Direção proposta: ordens decididas após o fechamento de `t` tornam-se elegíveis
na abertura da próxima sessão válida `t+1`.

- Tipo de ordem canônica: `TBD`.
- Formação do preço de execução: `TBD`.
- Lotes, arredondamento e liquidez: `TBD`.
- Slippage e spread: `TBD`.
- Falta de barra, suspensão e execução parcial: `TBD`.
- Política de short: `TBD`.

As mesmas regras serão aplicadas a todos os participantes.

Implementação técnica preliminar, sem congelar as escolhas acima:
`OrderIntent` registra ticker, peso alvo long-only e instante da decisão —
direção não é declarada pelo participante. Nem a direção nem a elegibilidade de
execução pertencem a ele: o `ExecutionEngine` é quem determina se existe próxima
abertura observada, deriva compra ou venda do delta entre posição e quantidade
alvo naquela abertura, e executa com quantidade inteira e o `CostModel`
existente. Os cinco
benchmarks clássicos já usam esse caminho, single e multi-ativo.

Para carteiras, a implementação atual usa a interseção dos calendários como
calendário comum, executa vendas antes de compras e, quando o caixa não cobre
todos os alvos, escalona as compras pelo mesmo fator antes de truncar para
quantidade inteira. Isso é um mecanismo técnico determinístico, escolhido para
remover dependência da ordem dos tickers — não uma política científica de
rateio. Lote B3, slippage, spread científico, liquidez, execução parcial,
margem, política de suspensão/falta de barra, destino do caixa residual e
política definitiva de short continuam `TBD`.

## 9. Capital

- Capital inicial: `TBD`.
- Moeda-base: `TBD`.
- Aportes e retiradas: `TBD`.
- Remuneração de caixa: `TBD`.
- Alavancagem e limites de exposição: `TBD`.

Caixa negativo será proibido, salvo decisão explícita e congelada em sentido
contrário.

## 10. Transaction costs

- Corretagem: `TBD`.
- Emolumentos e taxas: `TBD`.
- Spread: `TBD`.
- Slippage: `TBD`.
- Tributos: `TBD`.
- Fonte e data de vigência dos valores: `TBD`.

**STATUS: PENDENTE DE CONGELAMENTO.** Custos serão calculados sobre o valor
financeiro total e aplicados igualmente a todos os participantes.

## 11. Position sizing

- Universo entregue ao participante: derivado tecnicamente da spec —
  single-asset recebe o `ticker` declarado, carteira recebe todos os tickers do
  snapshot, e o universo efetivo é registrado no manifest. Critério científico
  de composição do universo permanece `TBD` (seção 3).
- Limite por ativo: `TBD`.
- Limite de exposição total: `TBD`.
- Rebalanceamento e frequência: `TBD`.
- Política de caixa residual e lote: `TBD`.
- Política definitiva de Kelly: `TBD`.
- Thresholds determinísticos de risco: `TBD`.

Confiança textual do LLM não será tratada como `P(win)` sem calibração empírica
prévia. Caso essa calibração não exista no primeiro experimento, será adotado
sizing determinístico ainda a definir.

## 12. Benchmarks

Candidatos atuais:

- Buy and Hold;
- SMA Cross;
- Bollinger Bands;
- Equal Weight;
- Mínima Variância;
- benchmark de mercado: `TBD`.

Parâmetros e frequência de cada benchmark: `TBD`. Todos serão congelados antes
do TEST e executados pelo contrato comum.

## 13. Multi-agent variants

Pendência arquitetural registrada aqui para não ser esquecida na migração: um
participante LLM multi-ativo precisará de semântica explícita para tickers
omitidos numa decisão. Hoje o `ExecutionEngine` trata ticker sem intenção como
"manter posição", o que é correto para os cinco clássicos. A preferência
arquitetural futura é exigir do participante um target portfolio completo. Essa
mudança não foi feita e não altera os benchmarks atuais.

Variantes candidatas:

- agente técnico único;
- ensemble técnico;
- ensemble + risk manager;
- sistema completo;
- comparação local vs cloud;
- opcionalmente, roteamento híbrido local/cloud.

Número de analistas, quorum, regra para votos inválidos, papéis e thresholds:
`TBD`. A configuração atual de 30 analistas e 25/30 é baseline técnica, não
parâmetro científico automaticamente congelado.

## 14. Models/providers

- Modelo local: `TBD`.
- Modelo cloud: `TBD`.
- Provedor(es): `TBD`.
- Versão/data de acesso e endpoint: `TBD`.
- Parâmetros de geração suportados: `TBD`.
- Structured output: `TBD`.

Compatibilidade será declarada apenas após validação documental e técnica. Cache
hits e respostas mock serão identificados e não serão confundidos com chamadas
reais.

## 15. Seeds and stochasticity

- Seeds por variante e execução: `TBD`.
- Número de repetições: `TBD`.
- Política quando o provedor não aceitar seed: `TBD`.
- Tratamento de não determinismo residual: `TBD`.

Seed só será enviada a um provedor após confirmação de suporte. Toda seed
configurada, enviada ou apenas auditada deverá ser distinguida no manifest.

## 16. Prompt versioning

Cada prompt científico terá identificador de versão, conteúdo ou hash, papel do
agente, schema esperado e parâmetros de geração. O procedimento de revisão e a
versão final são `TBD`.

Prompts serão congelados antes do TEST. Alterações posteriores criam nova versão
e não sobrescrevem resultados existentes.

## 17. Metrics

Métricas candidatas:

- retorno total e anualizado;
- volatilidade anualizada;
- Sharpe líquido;
- Sortino;
- Max Drawdown;
- Turnover;
- custos totais;
- exposição e caixa;
- medidas adicionais: `TBD`.

Taxa livre de risco, convenções de anualização, tratamento de dias sem posição e
fórmulas definitivas: `TBD`.

## 18. Statistical analysis

- Teste(s) estatístico(s): `TBD`.
- Nível de significância e intervalos de confiança: `TBD`.
- Correção para comparações múltiplas: `TBD`.
- Tratamento de dependência temporal: `TBD`.
- Unidade de reamostragem/bootstrap: `TBD`.
- Análises por subperíodo e seed: `TBD`.

Os testes e suas premissas serão escolhidos antes de observar o ranking em TEST.

## 19. Ablations

Plano candidato:

```text
A — quantitativos clássicos
B — agente técnico único
C — ensemble técnico
D — ensemble + risk manager
E — sistema completo
F — local vs cloud
G — roteamento híbrido local/cloud (opcional posterior)
```

O objetivo é estimar qual componente acrescenta valor. Contrastes, seeds,
orçamento e critérios estatísticos: `TBD`.

## 20. Reproducibility manifest

Cada `run_id` deverá registrar, no mínimo:

- versão do código e ambiente;
- `ExperimentSpec` completa;
- snapshot e hashes;
- universo, calendário e split;
- participante e parâmetros;
- capital, custos e regras de execução;
- modelo, provedor e parâmetros efetivamente enviados;
- prompts e schemas versionados;
- seeds configuradas e efetivamente suportadas;
- eventos de telemetria, cache, retry e falha;
- artefatos e versão do cálculo de métricas.

Formato e schema versionado do manifest: `TBD`.

Implementação técnica atual, que não congela nenhum item acima: cada execução
por `ExperimentRunner` publica `data/runs/<run_id>/manifest.json` com
`schema_version`, `run_id`, `spec_hash`, `created_at`, a `ExperimentSpec`
canônica, o participante, identidade/metadados/hashes do snapshot consumido, universo
efetivo, configuração de custo, configuração de métrica, capital, patrimônio
final, métricas, contagem de trades, custo total executado, commit Git e estado
dirty. `spec_hash` é o SHA-256 do JSON canônico da spec e identifica a
configuração; `run_id` identifica a execução. A coerência
`spec_hash == SHA-256(canonical_json(experiment_spec))` é verificável no próprio
artefato. O bloco `snapshot` registra `schema_version` e `identity_digest` do
snapshot, o que permite responder "qual snapshot verificável foi usado neste
run?" sem reler o diretório — a proveniência é capturada no `run()` e `persist()`
não a redescobre. Splits, seeds, prompts, modelos e benchmark ainda não fazem
parte da spec porque dependem de decisões `TBD`.

Runs reproduzíveis exigem proveniência Git verificável e working tree limpa. O
`ExperimentRunner` já impõe isso por padrão, de forma fail-closed estrita:
alterações não commitadas, commit indeterminado e proveniência não verificável
abortam a execução antes de qualquer trabalho. Existe um escape explícito de desenvolvimento
(`allow_dirty=True`) que cobre os dois casos, libera a execução e marca
`reproducibility.clean_source=false` no manifest; ele não altera o `spec_hash`.
Nenhum diff do working tree é persistido — a reprodução depende do commit, não
de um patch anexado.

## 21. Freeze procedure

Antes de abrir TEST, dupla e orientador deverão aprovar e registrar:

1. pergunta e hipóteses;
2. universo e snapshot;
3. splits e Walk-Forward;
4. participantes, parâmetros e benchmarks;
5. modelos, prompts e seeds;
6. capital, custos, execução e risco;
7. métricas, análise estatística e ablations;
8. versão do código e do manifest.

Forma de aprovação, responsáveis e registro imutável: `TBD`. Até essa aprovação,
o status deste documento permanece **DRAFT — NÃO CONGELADO**.

## 22. Rules after opening TEST

- Não ajustar participante, prompt, modelo, parâmetro ou custo após observar TEST.
- Não substituir snapshot ou universo silenciosamente.
- Não descartar falhas ou seeds desfavoráveis sem critério pré-registrado.
- Não promover análise pós-hoc a hipótese confirmatória.
- Toda correção indispensável deverá gerar nova versão do protocolo, novo
  `run_id` e justificativa explícita; a execução anterior será preservada.
- Resultados mock, VALIDATION e TEST terão rótulos distintos.
- Exceções a estas regras: `TBD` e dependem de aprovação antes do congelamento.
