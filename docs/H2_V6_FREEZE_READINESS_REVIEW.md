# H2 v6 - Revisão final de prontidão acadêmica e System Freeze

**H2_V6 FREEZE READINESS REVIEW COMPLETE — AWAITING FORMAL APPROVAL**

Branch conferida: `#1-Update`. HEAD auditado: `9d8636a4581a51229dd911d0863ef32551e7adb7`.
Data de referência: 08/10/2026, America/Sao_Paulo. Revisão de documentos, fontes,
identidades e checks offline; nenhuma execução científica real.

## Parecer

O pacote metodológico está suficientemente especificado para manifestação humana
sobre SF-B1..SF-B6, bootstrap A e a política de custos. A qualificação offline
confirma contratos computacionais; **não qualifica o caminho live**. Não é possível
realizar o System Freeze imediatamente após as assinaturas no estado auditado.
Faltam integração produtiva, persistência de chamadas reais, guards operacionais
de autorização/release e manifesto definitivo verificável. Esses itens devem ser
concluídos e qualificados offline antes de congelar a infraestrutura de avaliação.

Não há motivo técnico demonstrado para reabrir CAL-B4, repetir development,
alterar o tratamento, implementar bootstrap B ou aumentar R. A falha histórica
v5 é de expectativa entre estados do ciclo científico, não evidência de regressão
financeira da camada nova. Uma verificação adicional encontrou expectativa
histórica semelhante em um teste de roteamento v6; ela também fica registrada.

Entregas de aprovação: [resumo acadêmico](H2_V6_ACADEMIC_APPROVAL_SUMMARY.md)
e sua [versão PDF de duas páginas](H2_V6_ACADEMIC_APPROVAL_SUMMARY.pdf).
Campos de autor, coautor e orientador permanecem em branco.

## 1. Base documental e identidade

Hashes SHA256 dos bytes observados, preservados nesta revisão:

| Documento | SHA256 |
|---|---|
| [Proposta](H2_V6_EVALUATION_AMENDMENT_PROPOSAL.md), commit `00aa8ec` | `23d6f9464ffbcbbdacc44ecd0d59f39b2cdaa3d5e8b5b873faf73f0653607244` |
| [Deliberação](H2_V6_EVALUATION_AMENDMENT_DELIBERATION.md), commit `199a294` | `fe01092079e8bb9df60b97151631b5c9bff6fd36a249f18e8ea8ea55b7495dbb` |
| [Qualificação offline](H2_V6_EVALUATION_OFFLINE_QUALIFICATION.md), commit `9d8636a` | `32668ea06577146c8bd87070af6ffb80602758d798466f6a7ca60e141c283dbf` |
| [Relatório sintético](evidence/h2_v6_evaluation/qualification_offline.json) | `f8d1086f1aff74f94662e284a89325b4680a3db90281a67a0182d7e48693c16e` |
| Resumo acadêmico Markdown desta entrega | `04c01e44f7ac34dedeff7fb68bde36990ab068cc8fa0cf18309e6fbbc0d2a4ce` |
| Resumo acadêmico PDF desta entrega (duas páginas) | `797a8c5c147a058d265c66506a52896899f03a911134c856a5756d98803f779a` |

O resumo vincula proposta e deliberação por esses hashes. Em caso de divergência
entre resumo e documentos vinculados, suspender a confirmação e corrigir o
resumo; não presumir alteração do objeto assinado. Manifestação com ressalva que
mude o contrato exige resolução explícita e nova identidade antes do freeze.

Identidades preservadas: ParticipantSpec H2 v6
`7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938`;
commitment CAL-B4
`35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`;
revisão humana CAL-B4
`33db64913ace88d2b5c72bcdc2b37b608f939e4ade0e681b4a46dbbbb1474733`.
Snapshot `20261004T201258177516Z-b4cf39fc761f251d2dd18e787008345a`, identidade
`b4cf39fc761f251d2dd18e787008345aaf02bd9e19f913390c510338b84ee7d4`, CSV PETR4.SA
`7b6a0018191028ecea2ee66785c27f771a721aa4a96c4953ca87ac6d688c3ffa`.

Mantidos: tratamento=6; Technical Prompt=5; schema=2; vocabulary/validator=1;
Risk Prompt=2; checker=3; Portfolio existente; N=5; consenso=0,6;
require_all_votes=true; parâmetros 21/0,50/0,25/1,0; runtime Gemini nativo,
`gemini-3.8-flash`, LOW, temperature=1, max_output_tokens=8192,
retry_attempts=6, retry_base_delay=2, sem seed transmitida. CAL-B4 permanece
one-shot consumida, `CAL_B4_PASS — SANITY CHECK ONLY`,
`SYSTEM_CALIBRATION_COMPLETE=True`. Esses valores não são novas escolhas.

## 2. Decisões a ratificar

| Item | Manifestação de autor e coautor | Ciência/concordância do orientador |
|---|---|---|
| SF-B1 | H0₂: Δ≤0 / HA₂: Δ>0; B&H primário; um contraste no Final; inferência condicionada às trajetórias | Concordar com o alcance da conclusão e a separação da H1 multiativo |
| SF-B2 | R=3 em cada fase, chamadas próprias, sem seleção/substituição; recuperação exata ou interrupção | Reconhecer que três chamadas não equivalem a três mercados nem permitem generalização irrestrita |
| SF-B3 | Média dos Sharpes individuais; publicar os três runs e resumos, sem Sharpe de curva média | Concordar com o estimando e com a dispersão entre runs apenas descritiva |
| SF-B4 | A selecionado: basic pareado, B=5000, α=0,05, PCG64/20261008, bloco=10, rank=4751, empates/degenerações | Concordância expressa com aproximação não studentizada, pressupostos e ausência de estudo tamanho/poder/cobertura |
| SF-B5 | B&H, SMA Regime50/200 e Bollinger Estado20/2, incluindo igualdades, HOLD em bandas colapsadas e settlement | Concordar com os contratos dos controles secundários, sem confundir com adapters históricos |
| SF-B6 | Sortino MAR/rf=0 com flags; turnover de ordens/capital inicial | Concordar com convenções e com ausência de razão econômica nas degenerações |
| Custos | Baseline 5; grid 0/5/10/20; replay estrito sem rede, N/A fundamentado, sem agregação parcial | Concordar com interpretação contrafactual condicional e publicação de não estimabilidade |
| Escopo | Validation descritiva, Final separado, nenhuma seleção por resultado; release por integridade | Ciência dos limites, publicação de negativos/inconclusivos e ausência de autorização live por esta aprovação |

As três manifestações devem identificar os hashes e o objeto, com eventuais
ressalvas discriminadas. Assinatura CAL-B4 e commits anteriores não substituem
essas manifestações. Aprovar o amendment ratifica a especificação, não valida
outcomes, não certifica implementação ainda ausente e não autoriza freeze ou egress.

## 3. Auditoria técnica

### 3.1 Falha histórica v5 e evidência complementar v6

`tests/experiments/test_cal_b4_safety.py:67` espera `development S3 failure` de
`scripts/h2_v5.py:55`. O fluxo real verifica fontes/commits, carry-forward,
`require_sessions(used_sessions())` e só depois governança S3. O inventário
`scripts/select_cal_b4.py:25` agora inclui identidades da CAL-B4 consumida, que
`require_sessions` v5 rejeita com `CAL-B4 must stay sealed during v5 development`.
O teste recebe a exceção correta de bloqueio, porém antes da mensagem esperada.
A prioridade do guard é coerente com o estado posterior à CAL-B4; não há passagem
para fase proibida. O relatório offline já demonstrava isso isoladamente e com
contexto anterior à CAL-B4 somente no teste histórico.

Nesta revisão, a amostra ampliada também incluiu
`tests/experiments/test_v6_phase_routing.py:54`: o payload sintético reprovado
é corretamente marcado FAIL, mas o teste espera que `committed_phase("defect")`
não encontre PASS no repositório. O HEAD atual já tem evidência comprometida de
defect PASS. `scripts/h2_v6.py:119` lê essa evidência, não o payload local do teste.
A expectativa era anterior ao desenvolvimento; sua falha não demonstra aceitação
de um manifest comprometido FAIL. **Esse achado é adicional à única falha da
regressão anteriormente reportada**, pois esta amostra incluiu outro arquivo.
Um check adicional desta revisão, com raiz de evidência temporária e verificação
Git simuladas, confirmou que `committed_phase` rejeita manifest v6 FAIL e aceita
PASS. Nenhuma evidência de desenvolvimento real foi alterada nesse check.

Tratamento: registrar contexto, nome, esperado/observado e preservar ambos os
testes/guards byte a byte. Não introduzir skip, mudar regex, selecionar outra
evidência real ou declarar a suíte histórica verde. Para a infraestrutura nova,
um único check de avaliação v6 com entradas sintéticas deve verificar:
(a) rejeição de fonte/manifest de identidade divergente;
(b) Validation incompleta/corrompida e autorização de development/CAL-B4 não
liberam Final; (c) um registro de fase FAIL não libera fase posterior;
(d) baseline íntegro negativo/degenerado continua elegível por integridade.
Fixtures devem isolar a evidência esperada, sem depender de ausência de arquivos
de fases já encerradas. Não há necessidade de ressuscitar o comando v5.

### 3.2 Registry e menor integração segura

`src/experiments/participants.py:26` registra sete kinds históricos, mas não
`sma_regime_h2_proposed` nem `bollinger_state_h2_proposed`.
Os adapters já existem em `h2_evaluation.py:77/90`, usam `SignalParticipant`,
`sma` e `bollinger_bands` e têm specs/assinaturas adequadas. B&H já é reutilizável.
`h2_evaluation_offline.py:224` altera globalmente o registry sob lock e restaura
em finally; esse lock não protege runners externos. A ponte não serve ao live.

Menor alteração candidata: importar as duas classes existentes no registry e
adicionar somente as duas entradas explícitas. Manter os kinds e hashes das
specs propostas, sem renomeá-los por estética depois da aprovação; não alterar
`sma_cross`, `bollinger` ou B&H. `build_participant` continuará validando assinatura
e produzindo instâncias novas. Check necessário: construir as três specs pelo
registry normal, verificar instâncias distintas e as regras já qualificadas.

A injeção do cliente durável é problema separado: o runner chama
`build_participant(spec)` diretamente (`runner.py:260`) e não oferece hook.
`LLMParticipant` já admite `llm_client` (`participant.py:880`). Candidata mínima:
um hook local de construção no runner, default no builder atual, para a
orquestração v6 fornecer o cliente durável sem mutação global. Manter todos os
preflights e a identidade da spec antes da construção; não permitir import path
arbitrário em JSON, não pôr cliente/credencial na ParticipantSpec e não construir
LLM antes dos guards. Não se propõe novo motor financeiro ou arquitetura genérica.

**Registry e runner pertencem ao inventário de fontes congeladas da CAL-B4.**
O patch futuro deve ser revisão explícita de infraestrutura pós-CAL-B4, vinculado
ao novo manifesto, com diff permitido e hashes próprios; não atualizar o freeze
CAL-B4 nem seus selos para fazê-los aceitar o código novo. A verificação histórica
permanece reproduzível no commit histórico preservado. O comparador da avaliação
deve distinguir o baseline histórico do patch de infraestrutura autorizado e
continuar exigindo igualdade dos contratos do tratamento. Exigir todos os hashes
históricos sobre uma árvore com registry alterado bloquearia o próprio patch.

### 3.3 R=3, idempotência e recuperação de chamadas reais

Há garantia **offline**: `OfflineEvaluationBatch.execute` reserva slots L01..L03
e `_JournalClient.generate` reserva `(slot, sequence, request.identity)` com
commit SQLite `synchronous=FULL` antes do mock. Resposta/erro é persistido antes
de voltar ao participante; reinício de slot STARTED é replay-only, sem novo
cliente ou sufixo científico. COMPLETE é reutilizado após selos e identidade.
Publicação usa o staging do runner; recuperação de publicação sem selo compara
CSV/manifest/decisões/trace e preserva bytes. Lock abandonado falha fechado.

Isso não comprova idempotência live: o harness exige `MockLLMClient`, rejeita
snapshot reservado e impõe `no_network`; o runner produtivo não integra esse
banco. `RecordingLLMClient` mantém registros em memória até a publicação.
`run_cal_b4.RawJournal` tem padrões úteis de envelope bruto e fsync, mas é
específico de anchors/autorização CAL-B4 e não deve ser reaproveitado mediante
desbloqueio. Seu checkpoint de HTTP 200 ocorre depois do transporte; ele sozinho
não substitui reserva durável anterior ao envio no novo fluxo.

Um check adicional desta revisão simulou erro no UPDATE após a resposta mock,
antes da persistência, e reabriu o banco: a reserva sem registro permaneceu
durável, a resposta não chegou ao chamador, a recuperação falhou fechada e o
contador continuou em uma chamada mock. Isso confirma o limite offline, não
uma queda de processo ou resposta HTTP real; a integração produtiva ainda falta.

Contrato mínimo live a implementar, preservando retries congelados:

| Fronteira da queda | Estado e recuperação obrigatórios |
|---|---|
| Antes da reserva confirmada | Nenhum envio; registrar/iniciar a mesma identidade mediante guards |
| Reserva confirmada, antes/durante envio | Se não há resposta durável, estado incerto; recusar nova inferência, inclusive após timeout/reinício |
| API respondeu, envelope ainda não persistido | Mesmo estado incerto; não presumir que timeout significa ausência de resposta e não substituir run |
| Envelope bruto persistido, antes de validação/trace | Reprocessar o envelope local sob schemas congelados; nenhum reenvio |
| Resposta/erro durável, antes do participante/publicação | Replay exato; erros científicos continuam falha, nunca HOLD |
| Publicação concluída, antes do selo do slot | Conferir artifacts com replay exato e selar sem sobrescrever |
| Slot completo e selado | Reutilizar; comando repetido não cria novas chamadas |

Identidade externa ao request deve incluir manifesto/batch, fase e run. Prompts
iguais entre L01 e L02 não autorizam compartilhar uma resposta. Registrar tentativas,
response_id, requested/resolved_model, envelope e resposta validada sem segredos.
Nenhuma reserva pode voltar a fresh por limpeza automática. Uma interrupção pode
inviabilizar completar a fase: recuperação exata ou interrupção é o contrato,
não promessa de disponibilidade. Transação atômica entre API e disco local não
existe no fluxo auditado; não prometer exactly-once remoto. Retentativas transitórias
do contrato congelado não equivalem a substituir uma resposta científica recebida.

Checks específicos necessários no caminho definitivo, com transporte falso e
zero rede: quedas nas três fronteiras reserva/envio, resposta/commit e
commit/publicação; reabertura do banco; ausência de chamadas extras; erro de
fsync/commit impedindo entrega da resposta; dois processos/comando concorrente
sem duplicar slots; lock abandonado bloqueado. Basta um check pequeno que
exercite esse contrato; não se exige campanha live ou novo framework.

### 3.4 Bootstrap A e reprodução

`h2_evaluation.py:155/165/188/224` implementa A conforme a proposta: vetor
pareado, PCG64/20261008, 5000 draws, reinício=0,1, centro Δ*−Δ̂, p com +1 e ≥,
ordem 4751 (posição Python 4750), limite estrito e guards de degeneração.
Validation não calcula p; Final tem um contraste. Pareamento usa calendário
completo, sem inner join/preenchimento. Retornos vêm de `periodic_returns` e
Sharpe do helper canônico; warmup fica fora, caixa/entrada/settlement ficam dentro.

O check existente de métricas/benchmarks foi reexecutado nesta revisão: igualdade
com o protótipo, repetibilidade, rank/empates, specs e fronteiras passaram. Na
fixture sintética de 247 retornos, hashes reproduzidos:
índices `cec5427e9c8d3bbdeaaca586eea158ae6156ddd005f19e962e69a6b34ac0f470`;
erros `c53e35819778969df818c31c1ff77e235a65a090967d9a0d7801e1a01d6fd4bf`.
Esses hashes são de fixture, **não de retornos reais** nem prova de tamanho/poder.

A identidade reproduzível definitiva deve vincular ordem das colunas/sessões,
retornos de entrada e seus hashes, fontes, versões do ambiente, algoritmo/RNG,
B/α/seed/bloco/rank, número de draws degenerados e hashes dos índices/erros.
O código já usa bytes `<i8` e `<f8` para estes hashes. Preservar inputs e o
ambiente permite regenerá-los; um hash isolado não permite reprodução. Não há
necessidade de guardar uma nova matriz gigante se a regeneração íntegra for
qualificada. Lacuna é vinculação/persistência definitiva, não outra implementação
estatística. Aceitação de A e seus limites continua decisão humana.

### 3.5 Sensibilidade contrafactual de custos

Contrato e fixtures são coerentes: `cost_sensitivity` reutiliza 5 bps, executa
0/10/20 pelo motor com replay canônico, recalcula estado Risk/Portfolio, exige
completude do trace e não usa rede. Fixture inativa permitiu replay; fixture
compra/perda/venda divergiu, publicou motivo/identidade e métricas null. Qualquer
run indisponível impede resumo dos três; benchmarks são execuções próprias.
Não estimabilidade é resultado descritivo previsto, não novo blocker científico.

Duas lacunas devem ser tratadas na integração mínima: o harness captura qualquer
`Exception` LLM como replay inválido, inclusive erro operacional de publicação;
uma falha de benchmark sai do método sem disposição estruturada. Distinguir
divergência/falta/sobra esperadas de falha de código, disco ou integridade do
baseline. A primeira produz N/A fundamentado; a segunda interrompe/falha fechado,
sem mascarar o problema como resultado contrafactual normal. Persistir disposições
das combinações pré-declaradas ou registrar a fase como incompleta; não declarar
fechamento descritivo com combinações desaparecidas. Não é necessário transformar
erro operacional em métrica N/A para obter aparência de completude.

`require_release` atual confere somente baseline/benchmarks de 5 bps, não a
completude das disposições de sensibilidade. O manifesto deve explicitar o
fechamento dessas disposições e seu registro separado do gate primário. Um N/A
esperado não reprova baseline íntegro nem cria gate de desempenho para Final;
baseline corrompido bloqueia release, mesmo com cenários descritivos válidos.
Sem trades fixados, matcher relaxado ou chamadas adicionais como fallback.

### 3.6 Validation → Final e autorizações

Guards financeiros de janelas estão no runner/arena e foram qualificados offline.
As duas PhaseWindow da avaliação são explícitas: o PHASES global histórico não
as contém. A orquestração definitiva deve passá-las ao runner, preservar warmup
504 inclusivo e conferir decisão/settlement antes de construir cliente/chamar API.

`OfflineEvaluationBatch.require_release` exige Validation e chama summary para
três runs/benchmarks íntegros, calendário, selos e fontes; identidade do snapshot
é comparada. Não testa sinal de retorno, Sharpe, p ou superioridade. Está correto
como referência offline, mas `RunContext` e o runner genérico não obrigam esse
checkpoint no live. É necessário ligá-lo ao entrypoint definitivo, antes do
acesso da fase Final e novamente antes de execução, com evidência durável de
Validation, manifesto congelado e autorização específica da fase.

`docs/evidence/h2_v6/execution_authorization.json` autoriza apenas development
e exclui Validation/Final. A autorização CAL-B4 declara
`validation_final_authorized=false` e `system_freeze_authorized=false`.
O guard development `h2_v6.require_pre_live_freeze` não é guard da avaliação e
não deve ser usado para herdar autorização ou contornar seu limite de sessões.

São necessárias decisões distintas: aprovação acadêmica; autorização futura
para realizar o freeze; e autorização de egress/executar **Validation** vinculada
ao manifesto, R=3, janelas, runtime, payloads científicos, cobrança e recuperação.
Depois de Validation completa e revisão de integridade, autorização posterior
específica para **Final Test**, vinculada também ao checkpoint de release.
O guard deve rejeitar autorização ausente, de outra fase/manifesto/run ou
development/CAL-B4 antes de qualquer transporte. Não armazenar chaves em artifacts.
Nenhuma dessas autorizações foi criada nesta revisão.

## 4. Manifesto definitivo: conteúdo mínimo pendente

Não existe neste HEAD um manifesto definitivo aprovado/selado da avaliação.
O plano sintético não é seu substituto: marca OFFLINE_SYNTHETIC_ONLY, não inclui
ambiente completo e `_SOURCE_PATHS` não cobre, por exemplo, registry, calendário,
transportes e a futura integração. O manifest individual do runner registra
Python/versão do projeto, não todas as dependências necessárias à reprodução.

Produzir **após resolução das aprovações e patch**, sem tocar o freeze histórico,
um manifesto novo (caminho candidato:
`docs/evidence/h2_v6_evaluation/system_freeze_manifest.json`) com:

| Bloco | Conteúdo verificável obrigatório |
|---|---|
| Documentos e humanos | Proposta, deliberação, resumo, esta revisão, qualificação e checks novos com hashes; manifestações individualizadas e suas referências; política aprovada de custos/limites |
| Proveniência | Commit limpo final, árvore/patch permitido em relação a `9d8636a`, fontes por caminho/SHA256, scripts/checks de avaliação e inventário de artifacts; manifesto com hash externo, sem auto-hash circular |
| Fontes transitivas | Registry/runner/spec/context/phases/anchors; avaliação/adapters/orquestração/journal/guards; arena/engine/costs/metrics/calendar; snapshot/transform; base/B&H/indicadores; participant/features/prompts/schemas/evidence/checker/quorum/Risk/Portfolio; llm_client/llm_trace/telemetria/artifacts/config e entrypoint. Usar inventário histórico existente + arquivos novos/diff permitido, sem copiar milhares de hashes para esta revisão |
| Preservação | ParticipantSpec integral + SHA256; hashes/versões de contratos; vínculo CAL-B4 commitment, freeze, guards, raw batch, audit/revisão/status; igualdade do tratamento e exceções de infraestrutura explicitamente identificadas |
| Dados e calendário | Snapshot ID/identity, arquivos/hashes, ticker PETR4.SA, representação/preço/provenance, calendário oficial B3/hashes e lista esperada de sessões por fase, sem ler outcomes para preparar o freeze |
| Ambiente | Python/SO/arquitetura, versões efetivamente instaladas e lock/config com hashes; NumPy/pandas/pydantic/LangGraph e demais dependências transitivas materiais; configuração SQLite/fsync, locale/timezone e serialização do hash |
| Execução e runs | Capital=100000, cash_return=0, long-only/fractional_notional, close→open seguinte, sem venda terminal; seis identidades LLM declaradas (três por fase), instâncias/traces próprios; reservas, retries e política de recuperação/interrupção; benchmark por fase/cenário |
| Métricas e inferência | Sharpe v1/rf=0/ddof=1/252/limiar=1e-15; SF-B1..SF-B6; média/dispersion individual; Sortino MAR=0 com flags, turnover nocional/capital; métricas canônicas de retorno/CAGR/drawdown/custos; A/PCG64/B=5000/seed/bloco/α/rank/regras de degeneração, um contraste Final |
| Benchmarks/custos | Specs exatas e hashes abaixo, regras inclusive igualdade; grid 0/5/10/20, brokerage=0/tax=0,00032, baseline=5; replay sem rede, todos os motivos/disposições, null e ausência de agregação parcial |
| Release/acesso | Validation descritiva sem tuning; completude/identidade/selos/auditoria antes do Final; nenhum limiar de desempenho; fechamento descritivo documentado; aprovação do freeze separada de autorizações específicas de egress; recusa por drift/corrupção/incompletude |
| Evidência posterior | Manifestos/curvas/trades/decisões/traces/envelopes/attempts/selos por run; inputs e hashes da inferência; resultados/custos completos ou disposições N/A. Estes serão produzidos só nas fases autorizadas, não para preencher o freeze agora |

| Fase | Domínio | Decisões | Settlement | Curva/retornos | Warmup |
|---|---|---|---|---|---|
| Validation | 2024-09-02..2025-08-29 | 2024-09-02..2025-08-28 | 2025-08-29 | 248/247 | 504 inclusivo |
| Final Test | 2025-09-01..2026-08-31 | 2025-09-01..2026-08-28 | 2026-08-31 | 250/249 | 504 inclusivo |

Hashes de ParticipantSpecs (JSON canônico UTF-8), não de código:

| Kind/parâmetros além do ticker PETR4.SA | SHA256 |
|---|---|
| `buy_and_hold` | `cbdb92508d9766c5668b2500eea837cce3f5384d117f08a61765765829be0ef1` |
| `sma_regime_h2_proposed`, fast=50, slow=200 | `9fec52feb42a4dcea4ff7ca6973db348e03cf3efb92fe64252ac32e373f02bc5` |
| `bollinger_state_h2_proposed`, window=20, k=2.0 | `1ba8fddb165ec8b4bec5025f7be1ee38a8ff5e5e30d7e88c9b24958e2ec47345` |

Ambiente observado nesta revisão: Windows 11 build 22631; Python 3.13.9;
NumPy 2.5.1; pandas 3.0.3; pydantic 2.13.4; LangGraph 1.2.2; pytest 9.1.1.
Não é pin definitivo: `pyproject.toml` aceita faixas, e observar versões não
as sela no plano. Pesos/modelo remoto não são congeláveis localmente; manter
requested/resolved_model e envelope/replay auditáveis, sem trocar alias/runtime.

## 5. Matriz de bloqueios

| ID | Classe | Disposição/critério de encerramento | Efeito sobre freeze |
|---|---|---|---|
| A1 | APPROVAL_BLOCKER | Autor e coautor ratificarem SF-B1..SF-B6, A, custos/N/A, janelas e limitações, com hashes e ressalvas resolvidas | Impede |
| A2 | APPROVAL_BLOCKER | Orientador registrar ciência/concordância sobre o mesmo objeto, principalmente inferência condicional/basic e limites | Impede |
| A3 | APPROVAL_BLOCKER | Autorização específica futura para realizar System Freeze do pacote tecnicamente concluído | Impede executar o ato; esta tarefa o proíbe |
| A4 | APPROVAL_BLOCKER | Autorizações externas distintas para Validation e posteriormente Final, vinculadas à identidade e release | Impede fases live; não precisa antecipar Final para congelar |
| E1 | ENGINEERING_BLOCKER | Registro estático dos dois adapters existentes + construção local com cliente durável, sem ponte global, preflights preservados | Impede |
| E2 | ENGINEERING_BLOCKER | Orquestração produtiva R=3 e journal durável antes de egress, raw envelope/replay, slots/selos/locks e checks de queda/commit | Impede |
| E3 | ENGINEERING_BLOCKER | Entrypoint verificar manifesto, autorização de fase, PhaseWindow e checkpoint Validation íntegro antes de Final; check negativo/positivo sem gate financeiro | Impede |
| E4 | ENGINEERING_BLOCKER | Ligar custos/replay ao fluxo definitivo e tratar separadamente N/A esperado e falha operacional; fechamento de disposições ou estado incompleto | Impede qualificação definitiva dessa camada |
| E5 | ENGINEERING_BLOCKER | Novo manifesto verificável cobrindo documentos/fontes/ambiente/inputs/benchmarks/janelas/release; comparador aceitar somente patch de infraestrutura aprovado, preservando baseline CAL-B4 | Impede; mera lista textual não basta |
| D1 | DOCUMENTATION_ONLY | Registrar falha histórica v5, prioridade do guard e reprodução; não alterar teste/guard científico | Não impede após registro e checks pertinentes v6 |
| D2 | DOCUMENTATION_ONLY | Registrar expectativa histórica v6 anterior ao defect PASS comprometido; isolar evidência nos checks novos | Não impede após registro e confirmação do gate novo |
| D3 | DOCUMENTATION_ONLY | Após aprovação, alinhar redação da monografia/protocolo com amendment e bibliografia, sem mudar os originais nesta tarefa | Não exige novo tratamento ou teste; aprovação deve ter objeto inequívoco |
| L1 | NONBLOCKING_LIMITATION | R=3/mercado único, inferência condicional sem população de futuras chamadas | Reportar; não aumentar R automaticamente |
| L2 | NONBLOCKING_LIMITATION | Basic de primeira ordem, n=247/249, bloco fixo, regimes/caudas, ausência tamanho/poder/cobertura | Reportar; não implementar B/campanha estatística automaticamente |
| L3 | NONBLOCKING_LIMITATION | Sharpe/Sortino degenerados, inatividade ou resultado negativo | Publicar com flags/inconclusivo; não reprovar fase íntegra |
| L4 | NONBLOCKING_LIMITATION | Custos mudam estado e podem tornar replay exato não estimável | Publicar N/A/motivo; não autorizar novas chamadas ou trades fixados |
| L5 | NONBLOCKING_LIMITATION | API e disco não têm transação conjunta; queda incerta pode impedir completar run; pesos do modelo remoto não são congeláveis | Aceitar limite fail-closed e auditar; não prometer exactly-once/recuperação universal |

E1..E5 são responsabilidades interligadas de um patch mínimo de infraestrutura,
não cinco novos subsistemas. A ausência de implementação live é blocker; o custo
de disponibilidade de uma política fail-closed correta é limitação reconhecida.
Uma limitação torna-se questão de aprovação se um signatário não aceitar seu
alcance; não vira funcionalidade por padrão.

## 6. Evidência desta revisão e limites dos checks

A qualificação comprometida contém 15 grupos offline PASS e 394 PASS/uma falha
histórica na amostra anterior; seu relatório continua intacto. Nesta revisão,
reexecutados o check existente `metrics_and_benchmarks()` (cinco grupos PASS)
e `preservation()` (um grupo PASS): 6752 hashes históricos, dez anchors seladas,
doze gates PASS e hash da revisão humana conferidos. Nenhum outcome CAL-B4 foi
calculado. Não se reexecutou a integração completa de 320 segundos nem se
substituiu o relatório de qualificação por esta amostra.

Regressão complementar sem mudanças/fixtures de contexto:

```powershell
.venv/Scripts/python.exe -B -m pytest -q --tb=short -p no:cacheprovider --basetemp=tmp_freeze_readiness_20261008_verified tests/experiments/test_cal_b4_safety.py tests/experiments/test_v6_phase_routing.py tests/experiments/test_runner_evaluation.py tests/experiments/test_evaluation_spec.py tests/experiments/test_phases.py tests/agents/test_llm_trace.py
```

Resultado: **132 PASS, 2 FAIL, 0 ERROR**, 12,34 s. As duas falhas são as expectativas
históricas descritas em §3.1. Não declarar suíte integral PASS. Tentativas anteriores
no sandbox tiveram 22 erros de acesso a temporários; a execução com acesso local
adequado eliminou esses erros sem alteração de código/teste. Diretórios temporários
criados para esta regressão foram removidos; não foram removidas evidências.

Reprodução parcial de contratos e preservação, sem rede nem prices reais:

```powershell
@'
import sys
sys.path.insert(0, 'scripts')
from qualify_h2_v6_evaluation import metrics_and_benchmarks, preservation
metrics_and_benchmarks()
preservation()
'@ | .venv/Scripts/python.exe -B -
```

O status offline qualificado anterior é preservado, mas não significa aprovação
formal, freeze ou qualificação do transporte real. Os checks de quedas/autorização
da integração definitiva são propostos, **não declarados executados**. Além dos
seis grupos existentes reexecutados, os dois checks isolados descritos em §3.1
e §3.3 passaram; usam somente evidências geradas, mock e banco temporário.

## 7. Ordem exata dos próximos passos

1. Submeter o resumo de duas páginas e os dois documentos vinculados aos três
   responsáveis; obter manifestações do autor/coautor e ciência/concordância do
   orientador. Resolver ressalvas antes de usar o amendment como aprovado.
2. Implementar somente E1..E4, com fontes/patch próprios da avaliação: dois registros
   estáticos, injeção local, journal/orquestração R=3, autorização/release por fase e
   replay de custos. Preservar tratamento e toda evidência científica histórica.
3. Qualificar essa integração offline com transporte falso e dados gerados:
   registry normal, quedas/reserva/commit/publicação, idempotência, autorização
   ausente/de outra fase, fronteiras, release incompleto/corrompido e íntegro
   negativo/degenerado, disposições de custos. Reusar checks de A e métricas;
   registrar expectativas históricas sem modificar/ocultar os testes.
4. Fechar E5: preparar manifesto definitivo candidato com ambiente e fontes
   completos, escopo do patch e vínculos humanos; versionar o pacote e conferir
   commit limpo, hashes, preservação histórica e comparador do novo manifesto.
   Não usar `allow_dirty=True` no caminho real.
5. Obter autorização expressa para realizar o System Freeze sobre esse pacote
   concreto; só então executar o ato em tarefa futura. Assinaturas acadêmicas
   sozinhas não autorizam esta operação nesta tarefa.
6. Solicitar/registrar autorização externa específica para Validation vinculada
   ao manifesto congelado; somente depois executar os três runs reais e controles,
   sem tuning, seleções ou substituições. Esta revisão não faz essa execução.
7. Publicar Validation e disposições descritivas; revisar integridade, completude,
   calendário e identidade, gerar checkpoint de release mesmo se desempenho
   for negativo/inconclusivo. Falha de integridade interrompe progressão.
8. Obter autorização posterior específica para Final Test vinculada ao freeze e
   release; somente então executar três novos runs, benchmarks e o único
   contraste A, publicando negativos/degenerações/sensibilidade conforme aprovado.

Nenhuma assinatura, aprovação, autorização, Gemini, Validation, Final Test ou
System Freeze foi preenchido/executado. Nenhum tratamento, amendment anterior,
guard/teste histórico, artifact científico ou selo CAL-B4 foi modificado.

**H2_V6 FREEZE READINESS REVIEW COMPLETE — AWAITING FORMAL APPROVAL**
