# Premium V6 — AI Global Portfolio Manager

Identidade nova: `HFL-MULTIASSET-GLOBAL-PM-V1`. Propostas consultivas,
exploratórias, sem executor financeiro. Não altera H2 v6, Validation OA-1,
Final Test, Forward PETR4, supervisão, Radar V4 ou os exemplos contábeis V5.
Uma proposta, inclusive válida, **não constitui operação**.

## Arquitetura e inspeção

Foram examinados o projeto multiativos V4, os guias V4/V5, os três módulos V5,
Radar e CLI, APIs, servidor, HTML/CSS/JS, CallBank, DurableGeminiClient,
Recording/ReplayLLMClient, os agentes Technical/Risk/Portfolio e os commits
locais `f76eaa3` / `9ce9024`. A árvore estava limpa; o remoto não foi usado
como fonte da implementação V5.

| Etapa | Autoridade e fronteira |
|---|---|
| Technical individual | Cinco votos originais e evidências por empresa; não dimensiona capital |
| Risk individual | Parecer consultivo do ativo; não conhece a carteira global |
| Risk global | V5: retornos alinhados, covariância, exposição, drawdown e política didática |
| Portfolio Manager Global | Uma resposta coordenada para o capital compartilhado; pode descartar compras e manter caixa |
| Validador financeiro | Decimal, quantidades inteiras, custos, caixa, reservas, liquidação, hashes e risco; pode rejeitar o modelo |
| Aprovação humana | Na V6 autoriza exclusivamente uma inferência e seu orçamento, com token exato |
| Execução virtual | Ausente na V6. Nenhum registro V6 é entregue a Store/execute_demo; reserve/fill somente na cópia em memória do simulador |

Fluxo: seleção de pareceres selados → snapshot hipotético explícito → contexto
imutável e Risk → preflight offline → autorização de inferência separada →
claim/CallBank → resposta bruta privada → schema global → validação V5 em
memória → proposta consultiva e projeções. GET/replay não inferem.

| Arquivo | Responsabilidade |
|---|---|
| `scripts/multiasset_global_pm.py` | Identidade, contratos, prompt, schema Pydantic, adapter V4, snapshot, Risk e validação global |
| `scripts/run_global_pm.py` | Preparo explícito, orçamento, claims, Gemini durável, fake nativo, replay e exemplos A–F |
| `dashboard/global_pm_api.py` | Seleção, prévias separadas de custo, leitura íntegra e simulação consultiva |
| `dashboard/global-pm.js`, `.css` | Proposta da IA, alocações, explicações, custos, estados e projeção sem execução |
| `dashboard/portfolio.html` | Nova seção V6 visualmente separada da contabilidade V5 preservada |
| `dashboard/radar.html` | Navegação Radar → pareceres → Gestor Global |
| `dashboard/server.py` | GETs V6 e assets allowlisted; proteções Host/Origin herdadas, nenhum POST V6 |
| `tests/test_global_pm.py` | 39 checks offline de contratos, finanças, auditoria, HTTP e preservação |
| `.gitignore`, `README.md`, este guia | Raiz de dados isolada e documentação |

Nenhuma dependência nova, framework, migração, Docker ou arquivo em `src/`.
Reutiliza pandas/numpy/Pydantic/Chart.js local, JSON canônico, fsync + rename,
lock exclusivo e CallBank SQLite FULL já instalados.

## Contratos próprios

`contracts()` sela hashes separados de configuração `GLOBAL_PM_CONFIG_V1`,
prompt `GLOBAL_PM_PT_V1`, JSON Schema `GlobalProposal`, Risk V5, validação
`EXPLORATORY_ALLOCATION_V1`, execução `CONSULTATIVE_ONLY_V1` e fontes Python.
Os módulos V5 permanecem byte a byte iguais. Mudanças no código/configuração
de inferência invalidam contextos V6 anteriores: não atualizar seus selos.

O prompt integral está em `multiasset_global_pm.PROMPT`; o JSON Schema e os
contratos de qualificação são exportados nas evidências. Modelo novo neste
tratamento: `gemini-3.8-flash`, T=1, thinking low, até 8192 tokens de saída,
uma chamada e uma tentativa HTTP. Não reutiliza `PortfolioAction` single-asset
nem transforma confiança em Kelly, probabilidade ou peso.

`GlobalProposal` exige identidade/versionamento, ID, sessão, criação/validade,
snapshot/context hashes, resumo, pesos atuais, pesos-alvo de todo o universo,
peso de caixa, operações, razões por empresa e globais, não selecionadas,
oportunidades adiadas, riscos e referências exatas aos pareceres.

Cada operação exige ID, ticker, BUY/SELL, quantidade string inteira ou null,
preço-limite, custo máximo, fonte de financiamento, prioridade, dependências
e razão. null solicita cálculo determinístico por peso: floor do valor-alvo
à marca conhecida, com buffer da taxa didática na compra. Não redimensionar
uma quantidade explícita, alterar pesos do modelo nem corrigir custos máximos.
Uma proposta impossível é `REJECTED_BY_VALIDATOR`, sem inferência substituta.

Cada justificativa por ativo contém ação, texto, hash do parecer e códigos de
evidência existentes nos votos recebidos. Validação confere referências,
seleções, adiamentos e coerência da ação com as operações. Textos são escapados
no navegador. Pareceres são dados, nunca instruções. Sem ferramenta de notícias,
fundamentos, pesquisa externa, retornos esperados ou prompts de outros agentes.
A prosa livre continua exigindo revisão humana: referência válida não prova
automaticamente toda afirmação natural produzida pelo modelo.

## Fontes e relógios

O adapter estende a leitura V4 existente, verificando result/input/bars/journal,
manifesto e fontes reutilizadas. Entrega cinco votos completos, consenso,
confiança qualitativa, evidências favoráveis/contrárias, alertas, Risk individual,
features, origem e hashes. Não modifica votos, claims ou journals V4.
Parecer ausente é estado explícito, sem voto presumido ou análise automática.
Seleção simultânea exige mesma sessão, modo e família/versão de fonte.

`SYNTHETIC_DEMO`: fixtures de resposta, opiniões V4 sintéticas identificadas,
preços hipotéticos explícitos e custo real zero. Não é inferência Gemini.
`CONSULTATIVE_SANDBOX`: snapshot hipotético fornecido/inicializado pela pessoa,
pareceres oficiais completos e marcas brutas correspondentes. Nunca substitui
oficiais ausentes pelo demo. Não existe modo prospectivo executável.

Snapshot tem posição econômica, base de custo, unidades reservadas/em liquidação,
caixa liquidado, reservas, recebíveis, compromissos, custos, patrimônio, marcas,
observação e hash financeiro. A inicialização CLI padrão é R$ 100.000 em caixa.
`--snapshot` aceita um contrato V6 previamente preparado, com o estado hipotético
completo, inclusive reservas/recebíveis, sem autorizações V5/H2 anteriores.
Abrir a página não inicializa carteira ou contexto.

Os pareceres V4 de 09/10 foram realmente gerados em 11/10. A V6 registra essa
observação posterior; não lhes atribui um timestamp histórico falso. Históricos
terminam na sessão das marcas; contexto precisa observar todos os inputs antes
de ser congelado. Novas respostas têm validade de 24 h desde o preparo.
Validação usa o instante durável de conclusão da resposta; replay preserva esse
instante. Consulta posterior distingue expiração de validade histórica.

## Ponte matemática com a V5

A V5 recusa qualquer modo diferente de sintético e valida relógio de execução
na própria sessão. Seus módulos estão selados e não foram alterados. Por isso
a V6 constrói uma **cópia matemática hipotética identificada**, apenas em memória:
marcas brutas/saldos iguais ao snapshot, pareceres normalizados com referência
ao selo original, e relógio lógico da sessão para calcular o plano.
Isso não converte uma análise oficial em análise sintética publicada, não
reescreve o selo original e não constitui fill histórico/prospectivo.

O contexto V6 preserva separadamente modo/origem/observação originais, hashes,
marcas e contratos. O modelo recebe essa classificação. `risk_current` e o
relatório financeiro interno V5 identificam a cópia matemática; a resposta V6
vincula o contexto original. Essa fronteira é explícita, sem monkeypatch de
políticas ou relaxamento de gates no motor V5.

Risk usa 60 retornos ajustados alinhados, 252/ano e covariância ddof=1. Conferir
cobertura de todo o universo antes de inferir, mesmo com carteira 100% em caixa.
Zero exposição nesse estado é uma identidade financeira, não imputação de dados.
Falta, duplicidade, lacunas ou futuro bloqueiam; não preencher dados por zero.
Risco atual e projetado são separados. Excesso de concentração atual é mostrado
mesmo quando uma redução torna a projeção válida.

Concentração 40%, exposição 85%, volatilidade 35%, drawdown 20%, custos 0,1%,
turnover/custo diário e calendário/liquidação 2026 são **fixtures V5 didáticas**.
Preparo exige `--ack-fixture-policy`; não aprova esses limites para operação.
V6 não aceita política indefinida nem troca limites para aprovar o Gemini.

Validação V5 recalcula caixa, unidades, patrimônio pós-custo, concentração,
exposição, volatilidade, drawdown, turnover, preços, teto de custo, reservas,
veto individual e dependências. V6 acrescenta schema/identidade, universo,
estado/contratos/referências/validade, coerência de explicações e correspondência
entre alvo e quantidade. Tolerância declarada: uma unidade bruta mais os custos
totais do plano; arredondamento e peso efetivo são mostrados separadamente.

Venda cria recebível; não aumenta imediatamente caixa disponível. A projeção
imediata contém somente operações elegíveis. Rotação futura tem projeção
condicional separada, com preços constantes **hipotéticos**, confirmação de
liquidação e nova validação/autorização exigidas antes de qualquer fase futura.
Simulação e validação nunca publicam alterações em carteira.

## Custos, autorização e recuperação

[Tarifas oficiais Google](https://ai.google.dev/gemini-api/docs/pricing), verificadas
em 11/10/2026: Gemini 3.8 Flash Standard US$ 0,75/1M entrada e US$ 3,75/1M saída
incluindo pensamento até 31/12/2026; US$ 1,50/7,50 a partir de 2027.
Contrato nativo de [saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output).
Qualificação desta entrega usa somente transporte falso; smoke real/modelo e
tarifas vigentes precisam de confirmação separada antes de uso pago futuro.

Preflight é offline. Estimativa usa tamanho do contexto / 4 bytes por token e
2500 tokens de saída: hipótese de planejamento, não telemetria. Reserva máxima
por proposta: US$ 0,159744, considerando limite de 65536 bytes de entrada,
8192 tokens de saída e tarifas maiores anunciadas. Transporte verifica tamanho
do corpo mais margem; sem grounding, tools ou retries. Limite cumulativo da
identidade V6: US$ 5. Reservas incertas nunca são liberadas automaticamente.
Contrato de preço expira em 31/12/2027; mudanças exigem nova identidade/contexto.

Token vincula snapshot, todos os pareceres, contexto, contratos, orçamento,
reservas globais e validade. `--authorize-paid` e chave local são condições
adicionais; não reutiliza aprovação de carteira ou autorizações anteriores.
Nenhuma chave vai ao prompt, API, URL ou evidência. Resposta que ecoa chave é
recusada pelo transporte durável existente.

Armazenamento isolado:

```text
data/global_pm/hfl_global_pm_v1/
  reservations/<token>.json       # custo comprometido, selo e autorização
  operation.lock                 # serializa identidade/orçamento neste host
  <analysis-id>/
    context.json                 # snapshot, pareceres, históricos, Risk e contratos
    authorization.json           # AUTHORIZE_INFERENCE_ONLY, sem aprovação de ordem
    claim.json                   # único, imutável, vinculado ao contexto
    inference.lock               # PID do processo, não expira automaticamente
    private/calls.sqlite         # CallBank FULL: reserva antes do HTTP, envelope antes do parse
    private/provider_journal.jsonl # export completo, nunca servido no HTTP
    result.json                  # saída, validação, tokens, estimativa de custo e hashes
    failure.json                 # tipo/estado, sem mensagens privadas do provedor
  demo-qualified-v6/demo.json     # índice selado A–F, casos em raízes separadas
```

Um ID preparado não é sobrescrito. Duplo clique/refresh não inicia chamadas;
HTTP não oferece run. Dois processos competem pelos mesmos locks/claim e
orçamento. CallBank tem identidade V6 própria; um schema global novo usa
Recording/ReplayLLMClient e o transporte durável existente, sem modificar o
gate single-asset H2. Persistir envelope bruto privado precede validação.

Crash depois do claim e antes do banco: diagnóstico, sem inferência substituta.
Requisição reservada sem envelope: recuperação necessária, nunca repetir HTTP.
Envelope durável sem resultado: replay offline valida e publica o resultado.
Resultado já selado: consulta/replay preserva seus bytes. Resposta inválida
ou rejeição financeira não inicia outro Gemini. Telemetria ausente resulta em
custo null/indisponível, nunca custo pago zero; reserva continua comprometida.

Locks mortos exigem conferir PID antes de remover **somente o lock**. Não apagar
claim, reserva, journal ou resultado para repetir inferência. PID reutilizado
permanece conservadoramente bloqueado. Hash local não é assinatura externa;
custódia, identidade/autenticação do operador e execução distribuída são futuras.

## Comandos

Somente consultas e demonstração, sem custo real:

```powershell
.venv/Scripts/python.exe scripts/run_global_pm.py demo
.venv/Scripts/python.exe scripts/run_global_pm.py status --root data/global_pm/hfl_global_pm_v1/demo-qualified-v6-a
.venv/Scripts/python.exe scripts/run_global_pm.py replay --root data/global_pm/hfl_global_pm_v1/demo-qualified-v6-a
.venv/Scripts/python.exe dashboard/server.py 8089
# http://localhost:8089/portfolio
```

Outro demo usa outro `--root data/global_pm/hfl_global_pm_v1/demo-<novo-id>`;
nunca regenerar sobre os exemplos selados. A interface padrão lê o índice
qualificado; `HFL_GLOBAL_PM_ROOT` pode selecionar contexto consultivo preparado.

Futuro preparo **offline** de carteira hipotética com pareceres oficiais já
disponíveis, sem downloads nem Gemini:

```powershell
.venv/Scripts/python.exe scripts/run_global_pm.py prepare --root data/global_pm/hfl_global_pm_v1/consultative-001 --session 2026-10-09 --tickers PETR4 VALE3 ITUB4 WEGE3 BBAS3 --capital 100000.00 --mode CONSULTATIVE_SANDBOX --confirm-hypothetical --ack-fixture-policy
.venv/Scripts/python.exe scripts/run_global_pm.py preflight --root data/global_pm/hfl_global_pm_v1/consultative-001 --max-usd 0.25
```

Se faltarem dados oficiais, esse preparo bloqueia. Gerar comitês do Radar exige
fluxo/autorização próprios V4 e não é parte do comando V6.

**Somente após nova autorização humana explícita do custo e do token mostrado**:

```powershell
# NÃO executado nesta entrega. Chave somente no ambiente local.
.venv/Scripts/python.exe scripts/run_global_pm.py run --root data/global_pm/hfl_global_pm_v1/consultative-001 --max-usd 0.25 --confirm <token_exato_do_preflight> --authorize-paid
```

Esse comando gera apenas uma proposta. Nenhum flag/comando habilita operações.
Replay usa o mesmo root com `replay`, exclusivamente offline.

API GET: `/api/global-pm/status`, `/case?case=A…F`, `/simulate?case=A…F`,
`/selection?mode=…&session=…&tickers=PETR4,…`, `/prepared`,
`/preflight?max_usd=0.25`. Sem parâmetros de diretório, sem POST, sem provider
envelopes, sem inicialização automática. Host/Origin, query única e allowlist
impedem acesso externo, path traversal e leitura dos journals privados.

## Exemplos e qualificação

Todos usam cinco pareceres V4 sintéticos completos, resposta fake no schema
Gemini nativo e carteiras hipotéticas novas. Preços de cenário explícitos:
PETR4 40, VALE3 60, ITUB4 30, WEGE3 50, BBAS3 25 reais. Não são preços oficiais
ou as marcas originais da série sintética do Radar.

| Caso | Estado e proposta |
|---|---|
| A | R$ 100.000 em caixa; 400 PETR4 + 300 VALE3 + 400 ITUB4; WEGE3/BBAS3 fora; caixa remanescente R$ 53.954 |
| B | PETR4 inicialmente 50%; vender 300 unidades para reduzir abaixo de 40% mesmo com sinal favorável |
| C | Vender 100 PETR4; R$ 3.996 a receber; caixa disponível R$ 80.000 preservado; nenhuma compra |
| D | R$ 9.000 disponíveis; vender 500 PETR4; compra de 250 WEGE3 aguarda liquidação; projeções imediata/condicional separadas |
| E | 500 PETR4 + caixa; `operations: []`; posições/caixa preservados |
| F | Fake propõe pesos somando 120%; rejeitado, sem novo modelo ou efeito financeiro |

FakeGlobalPortfolioManager é resposta roteirizada de contrato, não inferência
real nem o DEMO_RULE_BASED V5. Resultados são simulações contábeis, sem avaliação
de retorno/poder preditivo. A V5 selada continua inalterada e separada no painel.

Checks: `python tests/test_global_pm.py -v`; Ruff nos dois scripts, API, servidor
e teste; `node --check dashboard/global-pm.js`. Regressão focada inclui V5,
Radar, Forward, supervisão, Premium V3, dashboard, Gemini mocks e B3 oficial.
Testes bloqueiam rede externa; somente loopback HTTP é liberado no teste local.
Inventário anterior à V6 cobre **11.027 arquivos protegidos**, incluindo os
exemplos/evidências V5 e fontes seladas. O gate original do manifesto é validado
novamente com Git limpo após os commits locais.

Logs, checks, contratos, arquivo de demonstração, capturas 1440/640/420 e
verificação final: [evidências V6](evidence/hfl_global_pm/README.md).

Pendências: política de alocação/objetivo e limites operacionais aprovados;
custos reais, impostos e slippage; frações/eventos corporativos; calendário
vigente; fonte bruta/timestamps/custódia/caixa; janela e relógio prospectivos;
autenticação, assinatura/custódia de auditoria; qualificação real do modelo e
revisão factual da prosa. Nenhuma delas é aprovada pelo demo ou pela flag de
inferência. Execução futura exige fase e autorização independentes.
