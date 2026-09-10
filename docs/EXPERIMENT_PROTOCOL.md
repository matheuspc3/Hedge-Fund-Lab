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
