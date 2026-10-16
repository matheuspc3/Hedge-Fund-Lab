# H2 v6 — Integração produtiva mínima da avaliação (E1–E5)

**H2_V6 EVALUATION PRODUCTION PATH QUALIFIED OFFLINE — AWAITING FORMAL APPROVAL AND SYSTEM FREEZE**

Branch: `#1-Update`. Referência: 09/10/2026, America/Sao_Paulo.
Commit de código qualificado: `e91f38b0d2f6344ac4c6307108778f757810f613`.
Engenharia provisória offline, conforme [revisão de prontidão](H2_V6_FREEZE_READINESS_REVIEW.md).
A proposta e a deliberação permanecem sem aprovação acadêmica formal.

## 1. Parecer e matriz E1–E5

| Item | Resultado da engenharia offline | Evidência e limite |
|---|---|---|
| E1 | PASS | Dois registros estáticos, ParticipantSpecs preservadas, hook local opcional depois dos guards/preflights; builder anterior permanece padrão. |
| E2 | PASS | Três slots isolados por fase; journal SQLite FULL, reserva antes do transporte, envelope/registro duráveis, recuperação conservadora e exclusão entre comandos. |
| E3 | PASS | Manifesto/hash/fontes/ambiente/árvore limpa, consentimento específico da fase, calendário/snapshot, janela e checkpoint de Validation íntegro antes de Final. Candidato bloqueia execução real. |
| E4 | PASS | Baseline reutilizado; 0/10/20 apenas por replay exato; N/A somente por divergência tipada; erro operacional interrompe; 24 disposições e fechamento independente. |
| E5 | PASS como candidato; BLOCKED como manifesto definitivo | Inventário verificável e SHA externo presentes. Aprovações, ato de System Freeze e autorizações reais não existem nesta entrega. |

Não resta bloqueio de implementação demonstrado pelos checks desta entrega.
Assinaturas permitem iniciar a conferência final para selagem, desde que não haja
drift ou ressalva metodológica. **Assinar não executa System Freeze nem autoriza
Validation/Final.** O ato de freeze e os consentimentos externos continuam pendentes.

## 2. Arquivos e hashes

SHA256 dos bytes da árvore qualificada; o [candidato](evidence/h2_v6_evaluation/system_freeze_candidate.json)
contém os inventários completos. Seu SHA externo é
`dc118ce9841df612d030f40e5993858eacc6d06e41eff173706fc3a72d3acb98`.
O SHA do próprio relatório fica no arquivo externo
[production_integration_report.sha256](evidence/h2_v6_evaluation/production_integration_report.sha256),
evitando auto-hash circular.

| Arquivo | SHA256 |
|---|---|
| [src/experiments/participants.py](../src/experiments/participants.py) | `0b0b249e15bd28f9332cf4d151c9cfe390600d82f152215f6d0aeffdea52c587` |
| [src/experiments/runner.py](../src/experiments/runner.py) | `428f70cac15c79f1949bb66b22dccee0af0a9c6052ccbfa94edfa8a2645b4bea` |
| [src/experiments/h2_evaluation_offline.py](../src/experiments/h2_evaluation_offline.py) | `1d11cd0249aaf787b3a5d86377b6022f51a69cf5f1e685a636effb591b8c0384` |
| [src/experiments/h2_evaluation_manifest.py](../src/experiments/h2_evaluation_manifest.py) | `95db4b191ea8c6ac8bc0e64e490d3873ab90d45517c8edf3813fb00dbe9ecb28` |
| [src/experiments/h2_evaluation_production.py](../src/experiments/h2_evaluation_production.py) | `e482336ce1907e5b183abd96b574422b829191dfb9811e2f61d60759abdcf74c` |
| [scripts/run_h2_v6_evaluation.py](../scripts/run_h2_v6_evaluation.py) | `f027a188ba9805243bf63a3b3e3b9aabe6c97e936cb57702bff652ebbd4f8989` |
| [scripts/qualify_h2_v6_production.py](../scripts/qualify_h2_v6_production.py) | `72d5e939ecb6cff0de8ec4223baf81e1b28d61b4d176775383cafc79c5a1358e` |
| [docs/evidence/h2_v6_evaluation/post_cal_b4_infrastructure.diff](evidence/h2_v6_evaluation/post_cal_b4_infrastructure.diff) | `bd7dbf531c80c1188ccc5b77cb4c205e0f4bcdb056e01ed394f861b030756f3e` |
| [docs/evidence/h2_v6_evaluation/system_freeze_candidate.json](evidence/h2_v6_evaluation/system_freeze_candidate.json) | `dc118ce9841df612d030f40e5993858eacc6d06e41eff173706fc3a72d3acb98` |
| [docs/evidence/h2_v6_evaluation/system_freeze_candidate.sha256](evidence/h2_v6_evaluation/system_freeze_candidate.sha256) | `4b19dadce0f329a8b1ed272a12f2064388034430c6badd6e455bceb1f970108a` |
| [docs/evidence/h2_v6_evaluation/qualification_production_offline.json](evidence/h2_v6_evaluation/qualification_production_offline.json) | `a7ede3303e46c5021b4fdff121f3555e08a30f9f3eb53eb240adc88dca8fc3f3` |
| [docs/evidence/h2_v6_evaluation/production_historical_regression.txt](evidence/h2_v6_evaluation/production_historical_regression.txt) | `241d11e050d6b0d6cb68599b7feadc0138ab3219b8d31d8a95a094b5324f5f43` |

`h2_evaluation.py`, motores financeiros, métricas canônicas, prompts, contratos
dos agentes, ParticipantSpec e dependências não foram modificados.
Em `h2_evaluation_offline.py`, foram removidos a ponte temporária de registry e
seu lock global; publicação, métricas e replay foram reutilizados por hooks locais,
com atribuição tipada de divergência e persistência verificável das disposições.
Nenhuma dependência foi acrescentada.

## 3. Patch de infraestrutura pós-CAL-B4

O [diff permitido](evidence/h2_v6_evaluation/post_cal_b4_infrastructure.diff), contra
`812f90821969028ca43c240dc841a39b35b5a5b6`, cobre somente:

- `participants.py`: um import e dois registros estáticos, mantendo os nomes
  `sma_regime_h2_proposed` e `bollinger_state_h2_proposed`.
- `runner.py`: tipos/imports, parâmetro opcional `participant_factory`, builder
  padrão e chamada pelo hook, na posição anterior de construção do participante.

SHA256 do diff: `bd7dbf531c80c1188ccc5b77cb4c205e0f4bcdb056e01ed394f861b030756f3e`.
São as únicas duas fontes alteradas dentro do inventário histórico CAL-B4:
registro explícito de infraestrutura autorizada para esta engenharia provisória,
sem ratificação acadêmica implícita. O comparador exige seus hashes posteriores
exatos e rejeita qualquer outra mudança.

| Fonte | SHA histórico | SHA posterior |
|---|---|---|
| `src/experiments/participants.py` | `02aa8bb058611fcf635b8e084ecc0077a35832c5c0bceb50fe073650b908ae04` | `0b0b249e15bd28f9332cf4d151c9cfe390600d82f152215f6d0aeffdea52c587` |
| `src/experiments/runner.py` | `a969d9fe0b3d813394de22f5fb1736849cb48092d21d8eb39dd4a2263f6f6d6b` | `428f70cac15c79f1949bb66b22dccee0af0a9c6052ccbfa94edfa8a2645b4bea` |

A preservação conferiu **6.752 identidades históricas: 6.750 bytes idênticos e
duas exceções de infraestrutura documentadas**. Os bytes anteriores são
reproduzíveis no commit `9d8636a4581a51229dd911d0863ef32551e7adb7`.
O runner histórico tinha bytes CRLF no selo e blob Git LF; a reconstrução aceita
essa representação somente quando reproduz o SHA256 histórico exato.
Não existe normalização genérica ou relaxamento do selo.

O verificador antigo de freeze continua estrito e recusaria o patch na árvore
atual; não foi alterado nem usado para declarar uma falsa aprovação do novo
código. Seu inventário original permanece intacto. A nova verificação distingue
o baseline histórico do patch posterior, com hashes e diff próprios.

## 4. Journal, idempotência e recuperação

O banco `provider.sqlite` é vinculado ao manifesto e à fase. Cada chamada usa
slot, sequência e identidade canônica completa: sessão, stage/analista, provedor,
modelo solicitado, prompts, schema, opções e hashes. Os registros incluem modelo
resolvido, response ID, telemetria, tentativas, envelope nativo recebido e registro
validado/erro. Cabeçalhos e credenciais não são persistidos; mensagens de erro são
sanitizadas e eco de chave no envelope impede sua gravação.

A reserva e o contador do slot compartilham transação FULL antes do transporte.
As tentativas são reservadas antes do envio; bytes de resposta são duráveis antes
da validação; resposta/erro canônico é durável antes de retornar ao participante.
Todos os acessos concorrentes à conexão do call bank usam o mesmo lock.

| Estado comprovado | Comportamento |
|---|---|
| Nenhuma reserva, ledger/inventário íntegros | Guards normais; o slot predeclarado pode iniciar. |
| Reserva sem resposta, envio/retorno incerto | FAIL CLOSED; nenhuma chamada substituta. |
| Envelope durável e validável | Reprocessamento local; nenhum transporte novo. |
| Envelope ainda inválido como transporte | FAIL CLOSED; retry incerto não é retomado após queda. |
| Registro durável | Replay com identidade exata, inclusive erro registrado. |
| Publicação existente sem selo | Reexecução local por replay; conferir curva, trades, decisões, trace e journal antes de selar; conservar os bytes publicados. |
| COMPLETE com selo íntegro | Reutilizar; não criar nova realização nem inferência. |
| Banco/schema/ledger perdido ou corrompido | FAIL CLOSED; não reconstruir um banco vazio para inferir novamente. |
| Lock de execução abandonado | FAIL CLOSED; exige investigação, sem remoção automática. |

A política de retries já congelada (seis tentativas, base 2, taxonomia nativa)
continua durante a execução original. Um HTTP malformado recuperável pode
receber a próxima tentativa original; todos os envelopes recebidos ficam
registrados. Recuperação após queda é replay-only. Slots não compartilham
respostas, clientes ou realização científica.

Não há promessa de exactly-once remoto: API e disco não compartilham transação.
FULL/fsync depende das garantias do sistema operacional e do armazenamento; os
checks usam falhas injetadas e reabertura real de SQLite, sem ensaio destrutivo
de hardware. Isso não cria permissão para substituir votos/runs.

## 5. Autorização, janelas e release

`scripts/run_h2_v6_evaluation.py` oferece preparação do candidato, preflight e
o entrypoint futuro guardado. O candidato não consegue alcançar o carregamento
do snapshot reservado pelo comando de execução. A qualificação usa outro tipo
de autorização, atestação de fixture gerada e `SyntheticTransport`; esses
registros são temporários e não autorizam egress real.

O caminho futuro exige manifesto definitivo com referências humanas íntegras,
freeze formal e consentimento externo próprio da fase, vinculados a hash,
ParticipantSpec, R=3, seis identidades predeclaradas, janela, endpoint nativo,
payloads científicos, cobrança normal e diretório único de saída.
Development/CAL-B4 nunca liberam as fases seguintes. Consentimento e hash do
manifesto são reconferidos antes de cada transporte; fontes, ambiente, árvore
limpa e snapshot são conferidos nos limites de comando/slot e antes do selo.

| Fase | Domínio | Última decisão | Settlement | Equity/retornos |
|---|---|---|---|---|
| Validation | 2024-09-02..2025-08-29 | 2025-08-28 | 2025-08-29 | 248/247 |
| Final | 2025-09-01..2026-08-31 | 2026-08-28 | 2026-08-31 | 250/249 |

Warmup: 504 sessões inclusivas (503 anteriores + primeiro bar).
O motor e os guards históricos continuam responsáveis por causalidade,
settlement e ausência de crossing; não foi criado outro motor financeiro.

O checkpoint `validation_release.json`, com SHA externo, vincula plano,
manifesto, snapshot, três runs, três benchmarks e todos os artifacts/selos.
Final exige autorização própria vinculada ao hash desse checkpoint e verifica
novamente os artifacts, estados COMPLETE e o bank de Validation antes de criar
clientes. Não há condição financeira de release. Foram exercitados contraste
inferior a B&H, retorno negativo e inferência degenerada.

O verificador confere coerência e hashes dos registros de manifestação; não
substitui o ato humano nem autentica sozinho a autoria de uma assinatura.
Nenhum desses registros humanos ou consentimentos reais foi criado.

## 6. Custos e fechamento das disposições

Baseline 5 bps é reutilizado. 0/10/20 usam somente o trace selado e o matcher
exato, recalculando estado e quantidades pelo motor. Não se fixam trades, não se
relaxa prompt/schema/identidade e não se solicita nova resposta.

Divergência esperada recebe
`COST_SENSITIVITY_NOT_ESTIMABLE — EXACT_REPLAY_INVALID`, motivo, identidade
afetada, consumo do trace e vetores `metrics=null`/`secondary=null`.
O resumo do cenário LLM é null se qualquer um dos três replays não for válido;
não se agrega um subconjunto. Benchmarks determinísticos continuam disponíveis.

O participante histórico encapsula falhas de chamada em `LLMDecisionError`.
O cliente local de replay conserva os objetos de exceção: somente falhas
exclusivamente `ReplayMismatchError` permitem atribuir esse wrapper a divergência
esperada. A classificação não procura texto de erro. Wrapper sem causa de
matcher, falhas mistas, disco, corrupção e erros de código propagam e interrompem.

Cada fase tem 24 disposições (4 spreads × [3 LLM + 3 benchmarks]), predeclaradas
no banco e atualizadas com hashes. `cost_closure.json` fecha essas disposições
separadamente do checkpoint primário. PENDING ou erro operacional não equivale a
N/A. Os checks produziram cenários válidos, nove disposições N/A esperadas no
caso ativo, corrupção detectada e interrupção por falha operacional.

## 7. Qualificação e regressão

Evidência: [qualificação integrada](evidence/h2_v6_evaluation/qualification_production_offline.json).
Resultado: **17 grupos novos PASS**, mais cinco grupos reutilizados
da qualificação estatística/benchmarks, todos com asserts habilitados.
Tempo registrado: 1303.57 segundos. Rede bloqueada no harness;
`provider_calls=0`; preços gerados; autorizações e envelopes falsos.
Artifacts individuais temporários são removidos ao concluir os checks.

Cobertura: registry normal sem mutação; três slots independentes; reserva
observável por outra conexão antes do transporte; falhas antes de reserva,
entre resposta/raw commit e raw/registro; commit/rollback falhos; reabertura;
30 chamadas concorrentes; concorrência entre comandos; publicação sem selo;
reutilização COMPLETE; autorização/manifesto/árvore limpa; ausência de checkpoint;
Validation corrompida/incompleta; release negativo; A degenerado; custos
válidos/divergentes/operacionais; disposições corrompidas; lock abandonado;
preservação de CAL-B4 e do tratamento.

Bootstrap A foi reutilizado sem alteração e comparado ao protótipo e à evidência
anterior. Mesmos B=5.000, PCG64, seed=20261008, bloco médio 10, rank 4751,
empates >=, correção +1 e decisão conjunta p/limite basic centrado.
No fixture estatístico idêntico:
índices `cec5427e9c8d3bbdeaaca586eea158ae6156ddd005f19e962e69a6b34ac0f470`;
roots `c53e35819778969df818c31c1ff77e235a65a090967d9a0d7801e1a01d6fd4bf`.
São identidades de teste sintético, sem conclusão sobre holdouts.

A [regressão histórica](evidence/h2_v6_evaluation/production_historical_regression.txt)
foi executada integralmente no escopo de 17 arquivos/402 casos:
**400 PASS, 2 FAIL, exit code 1**, sem alterações ou skips nos testes.
Os dois FAIL são os mesmos descritos na revisão inicial:

1. `test_v5_development_s3_failure_blocks_further_phases`: espera
   “development S3 failure”; o guard anterior encontra CAL-B4 já consumido e
   selado e emite “CAL-B4 must stay sealed during v5 development”.
2. `test_structural_failure_prevents_phase_selection_and_progression`: o
   fixture local FAIL não altera o defect PASS já commitado que
   `committed_phase("defect")` consulta no repositório.

Classificação: DOCUMENTATION_ONLY, incompatibilidades de expectativa entre
estados congelados, preservadas e visíveis. A suíte histórica não é declarada
verde. O gate novo de Validation → Final foi qualificado com checkpoints
sintéticos completos, incompletos e corrompidos, sem relaxar guards antigos.

Duas tentativas intermediárias de integração detectaram problemas reais:
leitura concorrente fora do lock e encapsulamento do matcher pelo participante.
Foram corrigidos nos commits abaixo e a qualificação completa foi repetida.
Os resultados intermediários não foram promovidos a PASS.

Comandos de reprodução offline, em árvore limpa (sem sobrescrever a evidência):

```powershell
.venv\Scripts\python.exe -B scripts/qualify_h2_v6_production.py
.venv\Scripts\python.exe -B -m pytest tests/experiments/test_runner.py tests/experiments/test_runner_evaluation.py tests/experiments/test_llm_runner.py tests/experiments/test_llm_run_artifacts.py tests/experiments/test_phases.py tests/experiments/test_evaluation_spec.py tests/experiments/test_execution_mode.py tests/backtesting/test_arena_evaluation_window.py tests/backtesting/test_costs.py tests/backtesting/test_fractional_execution.py tests/backtesting/test_metrics.py tests/backtesting/test_scientific_sharpe.py tests/agents/test_llm_trace.py tests/agents/test_causal_contract.py tests/agents/test_technical_evidence.py tests/experiments/test_cal_b4_safety.py tests/experiments/test_v6_phase_routing.py -q --tb=short -p no:cacheprovider --basetemp .pytest_temp/h2_v6_production_regression_reproduction
```

O segundo comando conserva exit code 1 enquanto as duas expectativas históricas
permanecerem incompatíveis com o estado commitado; isso está registrado, não
ignorado.

## 8. Preservação, candidato e lacunas

ParticipantSpec H2 v6:
`7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938`.
Commitment CAL-B4:
`35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`.
Revisão humana CAL-B4:
`33db64913ace88d2b5c72bcdc2b37b608f939e4ade0e681b4a46dbbbb1474733`.
Status preservado: `CAL_B4_PASS — SANITY CHECK ONLY`.
Selos brutos, anchors, AUDIT_SEAL, guards e os 12 gates automáticos foram conferidos.

O candidato cobre sete documentos/evidências normativas, 73 fontes/inputs
transitivos, 104 bindings históricos, ambiente com 145 distribuições instaladas,
snapshot/calendário, adapters, custos, métricas, A, runs/janelas, journal,
recuperação, release e patch permitido. Hashes dependem dos bytes exatos, inclusive
line endings. Divergência de fonte, dependência, documento ou ambiente exige
reconferência; não se recalculam selos CAL-B4 para acomodá-la.

Estado literal: `CANDIDATE / NOT APPROVED / NOT FROZEN`.
`live_authorized=false`; autor/coautor/orientador, freeze record e autorizações
reais das duas fases = null. O candidato não contém seu próprio hash: sidecar
externo, parâmetro explícito no entrypoint e vínculo na evidência de qualificação.
Esta evidência e este relatório serão vinculados separadamente no pacote de
selagem futuro, sem inserir um auto-hash no candidato.

O snapshot reservado é apenas identificado no manifesto. Não foi usado como
fonte de preços dos testes. Nenhuma Validation/Final real, Gemini, outro
provedor ou System Freeze foi executado. Tratamento, parâmetros, modelos,
prompts, hipóteses e todos os artifacts científicos anteriores permanecem intactos.

## 9. Bloqueios remanescentes e próximos passos

| Código | Classificação | Pendência exata |
|---|---|---|
| A1 | APPROVAL_BLOCKER | Autor e coautor manifestarem aprovação de SF-B1..SF-B6, bootstrap A, H0₂/HA₂, R=3/agregação, benchmarks/métricas, custos/N/A, janelas e limitações; vincular proposta/deliberação por SHA e resolver ressalvas. |
| A2 | APPROVAL_BLOCKER | Orientador registrar ciência/concordância sobre o mesmo objeto, incluindo caráter condicional da inferência e limites do basic bootstrap. |
| A3 | APPROVAL_BLOCKER | Autorização humana específica para o ato de System Freeze; produzir registro formal e manifesto definitivo com referências reais e selagem externa. |
| A4 | APPROVAL_BLOCKER para fases live | Consentimento externo próprio de Validation; posteriormente consentimento de Final vinculado ao checkpoint íntegro. Consentimento de Final não precisa ser antecipado para congelar. |
| E1–E4 | ENGINEERING_BLOCKER — superados offline | Não há implementação adicional exigida pelo resultado desta qualificação. |
| E5 definitivo | DOCUMENTATION_ONLY após A1–A3 | Incorporar manifestações/registro reais, manter identidade técnica qualificada, vincular as evidências e conferir árvore limpa/hashes antes do ato autorizado. |
| D1/D2 | DOCUMENTATION_ONLY | Registrar as duas expectativas históricas incompatíveis; conservar testes e guards. |
| L1–L4 | NONBLOCKING_LIMITATION | R=3 pequeno; inferência condicional às trajetórias; estacionariedade/bloco fixo/basic sem prova geral de cobertura; degeneração inconclusiva e custos eventualmente não estimáveis. Reportar, sem novas funcionalidades automáticas. |

Ordem exata:

1. Encaminhar o [resumo de aprovação](H2_V6_ACADEMIC_APPROVAL_SUMMARY.md) e
   [PDF de duas páginas](H2_V6_ACADEMIC_APPROVAL_SUMMARY.pdf), proposta e deliberação
   aos três responsáveis, com seus hashes originais. Campos continuam vazios.
2. Registrar manifestações individuais reais e resolver ressalvas. Se mudarem o
   contrato técnico/metodológico, atualizar identidade e repetir a qualificação
   afetada antes de prosseguir.
3. Conferir código/ambiente/bytes, diff permitido e evidências desta entrega.
   Preparar o manifesto definitivo e referências humanas sem circularidade.
4. Obter autorização específica do ato e realizar System Freeze em tarefa
   posterior; emitir registro/selagem definitiva. Nenhum ato é realizado aqui.
5. Somente então obter consentimento externo específico de Validation.
6. Executar Validation uma vez sob esse consentimento; verificar três runs,
   benchmarks, selos, disposições de custos e checkpoint de integridade, sem
   selecionar pelo resultado financeiro.
7. Obter consentimento externo próprio de Final, vinculado ao checkpoint;
   executar Final uma vez e reportar A/custos/limitações conforme aprovado.

## 10. Commits e estado de entrega

- `812f90821969028ca43c240dc841a39b35b5a5b6`: revisão de prontidão e pacote
  acadêmico prévio, preservados como baseline documental desta engenharia.
- `286f160b472104f6d21ee69b3332ad2873fef883`: integração e primeiro candidato.
- `0756d2e3ef5d6e771789af5e988d20e9cab4a1f7`: serialização de todas as leituras
  concorrentes do journal e check ampliado.
- `e91f38b0d2f6344ac4c6307108778f757810f613`: atribuição tipada de divergência de custos, null completo,
  fechamento explícito das conexões e falha de rollback sem retry de provedor.
- `3bb61b600f8b45b0ffae7ebbf6d71d8fd052804e`: evidência de qualificação e transcript histórico final.

O commit deste relatório e seu SHA externo são informados na entrega e
consultáveis por `git log -1 -- docs/H2_V6_EVALUATION_PRODUCTION_INTEGRATION.md`.
`git status --porcelain` final: vazio; árvore limpa após o commit documental.
Nenhum selo científico anterior foi refeito e nenhuma aprovação humana foi
preenchida.
