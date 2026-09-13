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

Consequência da semântica de peso alvo, registrada explicitamente: no agente,
`COMPRA` passa a significar **desejar exposição long no peso alvo configurado**,
e não que o trade físico em `open(t+1)` será `BUY`.

```text
target = 25%

close(t): exposição = 20%   -> provavelmente BUY
gap overnight leva a 30%    -> ExecutionEngine pode SELL para voltar a 25%
```

Isso é correto e é a consequência pretendida: a direção financeira concreta
continua sendo responsabilidade da arena, e o participante não declara `side`.

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
- Valor definitivo de `long_target_weight`: `TBD`.

### Decisão metodológica APROVADA

Duas decisões desta seção deixaram de ser proposta e passaram a ser decisão
aprovada da estratégia LLM. Elas não congelam nenhum valor numérico.

```text
1. confiança textual do LLM NÃO é probabilidade financeira
   -> não será usada como P(win) em fórmula de sizing sem calibração empírica

2. o sizing principal do experimento v1 será DETERMINÍSTICO
   -> o LLM decide direção; a exposição é definida por política externa a ele
```

Consequência operacional adotada para o `llm_agent` da arena:

```text
Technical Analyst   -> COMPRA / VENDA / MANTER
Risk Manager        -> APROVADO / VETADO
Portfolio Manager   -> decisão QUALITATIVA (schema sem campo de tamanho)
Sizing determinístico:
    COMPRA aprovada -> target_weight = long_target_weight
    VENDA  aprovada -> target_weight = 0.0
    MANTER / VETO   -> nenhuma intenção
```

O gestor de portfólio não tem autoridade para escolher a quantidade financeira:
o schema `PortfolioAction` não possui campo de tamanho, de modo que não existe
número a ignorar depois. `confidence` continua sendo produzida, registrada no
trace e enviada aos agentes seguintes como contexto qualitativo — se ela deve
ou não influenciar *qualitativamente* a decisão é uma ablation futura, não
objeto desta decisão.

### O que continua NÃO congelado

```text
long_target_weight  = TBD
```

O default técnico em código é `0.25`, herdado do antigo teto
`max_position_size` apenas para manter API e testes convenientes. **Isso não é
aprovação metodológica.** O valor científico será escolhido junto com os demais
itens do congelamento (seção 21).

Também continuam `TBD`: calibração empírica de `confidence`, adoção de
long/short (o participante atual é long-only por construção) e qualquer
política alternativa de sizing (`volatility_target`, `calibrated_kelly`).

### Kelly não foi removido do projeto

`calculate_kelly_size` continua implementada e continua ativa no modo
`legacy_confidence_kelly`, que serve os caminhos operacionais legados
(`AgentBacktestEngine`, `DailyAgentRunner`) e permanece o default de
`PortfolioConfig` para que esses runners não troquem de política em silêncio.
Ela segue disponível para ablation, comparação metodológica e uma versão
calibrada futura.

```text
legacy / experimental alternative   != main scientific sizing v1
```

O `LLMParticipant` força `sizing_mode="qualitative"` e não expõe parâmetro
algum de Kelly. Os parâmetros que deixaram de ser materiais no caminho
científico — `kelly_fraction`, `max_position_size`,
`portfolio_max_concentration`, `payoff_ratio` — foram retirados da
`ParticipantSpec` do `llm_agent`, para que duas configurações de comportamento
idêntico não produzam `spec_hash` diferente por causa de um parâmetro morto.

### Registro, não congelamento

`long_target_weight` é configuração material: é validado
(`0 < w <= 1` e `w <= risk_max_concentration`, porque um alvo acima do limite
duro mandaria construir exatamente a exposição que o gestor de risco existe
para vetar), entra no `spec_hash` e aparece no manifest. Registrar não é
congelar.

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

Pendência arquitetural anterior, agora resolvida no nível do contrato: um
participante LLM multi-ativo precisa de semântica explícita para tickers
omitidos numa decisão. A regra adotada é **target portfolio completo**.

```text
uma decisão de carteira declara um peso para CADA ativo do universo observado

ticker omitido   -> DECISÃO INVÁLIDA
ticker extra     -> DECISÃO INVÁLIDA
ticker duplicado -> DECISÃO INVÁLIDA
peso NaN/Inf     -> DECISÃO INVÁLIDA
peso < 0 ou > 1  -> DECISÃO INVÁLIDA
soma > 1 + tol   -> DECISÃO INVÁLIDA

cash_weight = 1 - Σ target_weights
```

Ticker omitido não significa manter posição, não significa peso zero e não
autoriza o executor a inferir nada. Isso vale para uma *decisão de carteira*;
não confundir com a ausência de decisão do participante single-asset migrado,
cujo `MANTER` devolve nenhuma intenção — que é como o motor legado não emitia
ordem — e não uma carteira parcial. Peso zero é decisão explícita e precisa ser
escrita. Nada é normalizado silenciosamente. A regra está implementada e
testada em `target_portfolio_to_intents`
(`src/agents/participant.py`).

Isso não altera os cinco clássicos: o `ExecutionEngine` continua tratando
ticker sem intenção como "manter posição", que é a semântica correta para eles.
A ausência de qualquer intenção também continua significando "nenhuma decisão
nova" — coisa distinta de uma decisão de carteira parcial, que é inválida.

**Capacidade técnica atual (não é congelamento).** O participante LLM já
executa pelo mesmo `ExperimentSpec` -> `ExperimentRunner` -> `ExecutionEngine`
-> `RunResult` -> manifest dos clássicos, sob o `kind` `llm_agent`, na versão
**single-asset**. A stack de agentes é single-asset por construção e não possui
etapa de alocação entre ativos; o participante recusa universo com mais de um
ativo em vez de fabricar um laço por ticker. A variante multi-ativo continua
`TBD`.

Variantes candidatas:

- agente técnico único;
- ensemble técnico;
- ensemble + risk manager;
- sistema completo;
- comparação local vs cloud;
- opcionalmente, roteamento híbrido local/cloud.

Número de analistas, quorum, regra para votos inválidos, papéis e thresholds:
`TBD`. A configuração atual de 30 analistas e 25/30 é baseline técnica, não
parâmetro científico automaticamente congelado. Ela é configurável na
`ParticipantSpec` (`analyst_count`, `consensus_threshold`,
`require_all_votes`, `temperature_min`, `temperature_max`, `seed_base`) e entra
no `spec_hash` e no manifest — registrar não é congelar.

Frequência de decisão: `TBD`. `decision_frequency` é configuração material do
participante e entra no `spec_hash` e no manifest, mas registrar não é
congelar. Os dois defaults herdados do código legado são diferentes e ficam
declarados:

```text
AgentBacktestEngine (classe/API) default = 1   <- adotado pelo LLMParticipant
scripts/run_agent_backtest.py       default = 5   <- escolha operacional de demo
```

Nenhum dos dois foi aprovado como parâmetro científico. A frequência definitiva
do experimento deve ser decidida junto com splits e orçamento de chamadas,
antes do TEST.

Descrição correta do primeiro estágio: **ensemble/quorum de múltiplas amostras
do mesmo papel, do mesmo prompt e do mesmo modelo**, variando temperatura e
seed registrado. Não são 30 especialistas independentes; papéis e modelos
distintos não estão implementados.

Distinção adotada entre falha e decisão, no caminho da arena:

```text
timeout / erro de provedor / JSON inválido /
schema inválido / quorum incompletado por falha
        -> LLMDecisionError -> run falha

quorum sem supermaioria, com todos os votos válidos
        -> MANTER (regra de agregação da metodologia atual)
```

Falha de infraestrutura não vira decisão de investimento. O retry legitimamente
configurado hoje (`RetryingLLMClient`) continua valendo: só falha **não
recuperada** derruba o run.

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

**Proveniência registrável hoje, sem congelar escolha.** A `ParticipantSpec` do
`llm_agent` grava `provider` e `model` no `spec_hash` e no manifest, e o
provedor real exige `model` explícito — sem modelo declarado o run não começa.
`provider="mock"` também é registrado, de modo que um run mock nunca se confunde
com um run científico.

O que isso identifica é **o que foi tecnicamente solicitado**:

```text
requested_model = "<id enviado ao provedor>"      -> registrado
exact_model_weights / versão interna do modelo    -> NÃO identificável
```

O provedor não expõe versionamento de pesos, então o manifest não afirma
identificá-lo. `base_url`, timeout e credencial continuam sendo ambiente de
execução: a credencial nunca é serializada; o endpoint ainda não entra na spec,
e isso é uma lacuna conhecida de proveniência.

## 15. Seeds and stochasticity

- Seeds por variante e execução: `TBD`.
- Número de repetições: `TBD`.
- Política quando o provedor não aceitar seed: `TBD`.
- Tratamento de não determinismo residual: `TBD`.

Seed só será enviada a um provedor após confirmação de suporte. Toda seed
configurada, enviada ou apenas auditada deverá ser distinguida no manifest.

**Estado técnico verificado.** O `AgentRouterLLMClient` transmite apenas
`temperature`, `top_p` e `max_tokens`. `seed` é gerada pelo ensemble, entra no
`TechnicalVote` e aparece no trace como opção **solicitada**, mas **nunca é
enviada ao endpoint**. Essa distinção passou a ser publicada por chamada:

```text
requested_options  -> {"temperature": ..., "seed": ..., "analyst_id": ...}
transport_options  -> {"temperature": ...}       # seed ausente
```

Portanto: não existe, hoje, determinismo por seed neste provedor, e nada no
projeto deve ser descrito como tal. A decisão sobre enviar `seed` quando houver
suporte documentado continua `TBD`.

### Inferência ao vivo versus inferência por replay

Esta distinção é parte do protocolo, não detalhe de implementação.

```text
inferência ao vivo
  mesma ExperimentSpec + mesmo snapshot + provedor externo
  -> NÃO garante resposta idêntica
  -> fonte primária de evidência: o trace gravado daquela execução

inferência por replay
  trace gravado -> ReplayLLMClient -> sem rede
  -> mesmas respostas, mesmas decisões, mesmos trades, mesmas métricas
  -> é o mecanismo de reprodução exata do experimento
```

Um resultado científico publicado por este projeto é, portanto, um par:
o **run ao vivo** (com seu trace e seu commit) e a **capacidade de replay**
daquele trace. Reexecutar a mesma spec contra o provedor produz *outra*
execução, legítima como nova amostra, jamais como reprodução da primeira.

O replay recusa divergência em vez de acomodá-la: prompt, modelo, provedor,
opções solicitadas, schema, papel, analista, sessão ou ordem diferentes
levantam `ReplayMismatchError`, e sobra ou falta de registro também. Relógio e
duração não entram nessa identidade.

**Nada aqui congela modelo, prompt, quorum ou seed.** O mecanismo de evidência
existe; as escolhas científicas continuam `TBD`.

## 16. Prompt versioning

Cada prompt científico terá identificador de versão, conteúdo ou hash, papel do
agente, schema esperado e parâmetros de geração. O procedimento de revisão e a
versão final são `TBD`.

Prompts serão congelados antes do TEST. Alterações posteriores criam nova versão
e não sobrescrevem resultados existentes.

**Onde os prompts vivem hoje, e o que isso garante.** Eles continuam sendo
constantes de módulo em `src/agents/technical_analyst.py`,
`src/agents/risk_manager.py` e `src/agents/portfolio_manager.py`. **Não existe
prompt registry nem campo de versão de prompt**, e nenhum `prompt_version` é
inventado enquanto não existir mecanismo que o sustente.

O que passou a existir é proveniência do texto concreto de cada chamada:

```text
git_commit                     -> proveniência do CÓDIGO que gerou o prompt
system_prompt / user_prompt    -> o prompt LÓGICO completo, na íntegra
system_prompt_sha256
user_prompt_sha256             -> proveniência desse texto lógico
response_schema_sha256         -> estrutura do schema pedido
transport_system_prompt_sha256 -> hash do texto final enviado, quando o
                                  cliente concreto o reporta
```

Os hashes são SHA-256 do texto exato em UTF-8, **sem normalizar espaço em
branco**: dois prompts que diferem em espaço em branco são prompts diferentes.
O texto completo é gravado, e não só o hash, porque auditoria e replay precisam
reconstruir a chamada — e nenhum prompt do projeto carrega segredo. Credencial
e cabeçalho HTTP continuam fora do artefato por construção.

**Prompt lógico ≠ prompt de transporte.** O `AgentRouterLLMClient` acrescenta o
`model_json_schema()` serializado ao system prompt antes de montar o corpo
HTTP. Portanto o `system_prompt` publicado no trace **não é**, para esse
provedor, o texto literal enviado — e o protocolo não pode descrevê-lo assim.

O que torna a requisição enviada inequívoca é a combinação: prompt lógico na
íntegra + `response_schema_sha256` + o molde, que é código coberto pelo
`git_commit`. Por isso o digest do schema entra na **identidade** usada pelo
replay: dois schemas de mesmo nome e estrutura diferente perguntam coisas
diferentes ao provedor e não podem ser tratados como a mesma chamada.

O vínculo com o código permanece: o `ExperimentRunner` recusa working tree suja
e o manifest grava o commit. Registry e versionamento formal de prompt seguem
`TBD` e hardening futuro.

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

Para o `llm_agent`, o bloco `participant` do manifest carrega a configuração
material do LLM: provedor, modelo requisitado, política de retry, quorum,
limites de risco e de portfólio, janela de volatilidade e payoff. Credencial
não entra em spec, manifest, log nem artefato de auditoria.

A partir do schema 3, o manifest também publica `participant_artifacts`, e um
run `llm_agent` acompanha o arquivo `llm_calls.jsonl`:

```json
"participant_artifacts": {
  "llm_calls": {
    "path": "llm_calls.jsonl",
    "schema_version": 2,
    "call_count": 123,
    "error_count": 0,
    "bytes": 456789,
    "sha256": "..."
  }
}
```

O `sha256` é dos bytes efetivamente publicados, o que torna detectável o estado
"manifest íntegro, trace adulterado". O contrato é genérico
(`RunArtifactProvider`), e participantes clássicos publicam
`participant_artifacts` vazio. A `ExperimentSpec` **não** ganhou nada disso:
`call_id`, timestamps, latência, tokens observados, resposta bruta e caminho do
trace são o que *aconteceu*, não configuração pedida antes do run.

Com isso, "eventos de telemetria, cache, retry e falha" da lista acima passa a
ter cobertura por chamada — `attempt_count`, `retry_count`, `status`,
`error_type`, `duration_ms` e `token_usage` quando o provedor o devolve. Seguem
**não** registrados: custo monetário (sempre zero), versionamento de prompt
(inexistente por decisão) e fingerprint de modelo devolvido pelo provedor (não
é entregue no contrato atual — o manifest registra o modelo *solicitado* e o
endpoint sanitizado).

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
