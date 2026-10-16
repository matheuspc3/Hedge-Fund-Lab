# H2 v6 — implementação e qualificação da avaliação offline

Branch `#1-Update`. Implementação técnica provisória, conforme a proposta
`00aa8ec` e a deliberação `199a294`. Nenhuma aprovação ou assinatura foi inferida.

Estado científico preservado:
`H2_V6 EVALUATION AMENDMENT PROPOSED — AWAITING AUTHOR APPROVAL`.

## Inventário e arquivos novos

| Arquivo novo | Responsabilidade |
|---|---|
| `src/experiments/h2_evaluation.py` | Specs, adapters, agregação, candidato A, métricas secundárias e limites das fases |
| `src/experiments/h2_evaluation_offline.py` | Orquestração exclusivamente sintética, banco durável, publicação/recuperação, replay de custos e release por integridade |
| `scripts/qualify_h2_v6_evaluation.py` | Self-check executável com asserts, preços gerados, mocks e bloqueio de rede |
| `docs/evidence/h2_v6_evaluation/qualification_offline.json` | Resultados sintéticos, disposições por run/custo, hashes e grupos de checks |

Reutilizados: `ExperimentRunner.run/persist` e seus writers CSV; `ExecutionEngine`,
`CostModel` e execução fracionária; snapshot canônico e integridade; `B3Calendar`;
`EvaluationSpec`, `PhaseWindow` e guards de fronteira; `ParticipantSpec`,
`RunContext` e `canonical_json`; `SignalParticipant`, `BuyAndHoldParticipant`,
`sma` e `bollinger_bands`; `LLMParticipant` com cliente injetado,
`RecordingLLMClient`, `ReplayLLMClient`, `load_trace` e `MockLLMClient`;
retornos, Sharpe científico, Sortino técnico e soma de custos canônicos;
`run_cal_b4.verify_freeze`, selos e auditoria já existentes. Nenhuma dependência
nova. Nenhum arquivo histórico foi editado.

O registry é atualizado temporariamente sob lock e restaurado em `finally`.
Essa ponte atende ao harness offline; seu limite é não coexistir com outro
runner que altere o registry no mesmo processo. Não foi introduzido um runner
financeiro alternativo nem um caminho live. `allow_dirty=True` é usado somente
para fixtures gerados, com identidade e hashes verificados; não autoriza execução
científica real com árvore suja.

## Identidade dos benchmarks

Specs serializadas via `ParticipantSpec.to_dict()` e hash SHA256 UTF-8 do JSON
canônico. Ticker comum `PETR4.SA`. Capital 100000, execução fracionária,
brokerage=0, spread primário=5 bps e tax_rate=0.00032.

| Kind | Parâmetros | SHA256 |
|---|---|---|
| `buy_and_hold` | ticker | `cbdb92508d9766c5668b2500eea837cce3f5384d117f08a61765765829be0ef1` |
| `sma_regime_h2_proposed` | ticker, fast_window=50, slow_window=200 | `9fec52feb42a4dcea4ff7ca6973db348e03cf3efb92fe64252ac32e373f02bc5` |
| `bollinger_state_h2_proposed` | ticker, window=20, k=2.0 | `1ba8fddb165ec8b4bec5025f7be1ee38a8ff5e5e30d7e88c9b24958e2ec47345` |

Os kinds continuam identificados como propostos. Os hashes das specs não
substituem hashes de código: o plano de cada batch vincula fontes, specs,
snapshot, custos, janela, capital e teste. Fontes históricas em `src/` são
conferidas contra o freeze CAL-B4 antes das execuções sintéticas.

SMA entra quando fast>slow e sai em igualdade. Bollinger usa ddof=1, fronteiras
inclusivas e HOLD em bandas colapsadas. Ambos começam em caixa, observam apenas
histórico causal e emitem intenção somente quando muda o alvo. B&H mantém seu
adapter original. Nenhuma venda terminal é criada. `sma_cross` e `bollinger`
históricos permanecem byte a byte preservados.

## Matriz de conformidade

| Decisão | Implementação e evidência offline |
|---|---|
| SF-B1 | H0 Δ≤0 / HA Δ>0; B&H primário; Validation descritiva, Final com um contraste; nenhuma inferência para controles/custos |
| SF-B2 | Slots L01/L02/L03; clientes novos e respostas validadas próprias; nenhuma seleção/substituição por desempenho; reservas SQLite antes da inferência mock |
| SF-B3 | Média dos três Sharpes individuais; publicação individual, diferenças, mínimo, máximo e desvio padrão amostral entre runs; não calcula Sharpe de retornos médios como principal |
| SF-B4 | Apenas A; stationary bootstrap pareado B=5000, PCG64/20261008, restart=0.1, rank 4751, empates ≥ e p com +1; equivalência com protótipo preservado, hashes de índices/raízes e degeneração inconclusiva |
| SF-B5 | Specs acima, regime/estado e helpers existentes; testes de primeira entrada, igualdade, bandas colapsadas, fronteiras, manutenção e settlement |
| SF-B6 | Sortino técnico canônico MAR/rf=0; economic_value=null com motivo nas degenerações; turnover nocional executado/capital inicial, quantidade de ordens e custos; entradas inválidas falham |

A inferência é condicional às três trajetórias LLM observadas. O bootstrap basic
não é teste nulo exato e depende de pressupostos de dependência temporal e
regularidade da razão Sharpe. Bloco médio 10 e B=5000 foram selecionados antes
da avaliação, não ajustados aos resultados. Degenerações originais ou em draws
não são removidas nem reamostradas: p/limite ficam null e a conclusão inconclusiva.

## Persistência, recuperação e custos

O banco SQLite usa reserva de chamada e commit FULL antes do mock; persiste
resposta/erro antes de retornar ao participante. Slots interrompidos tornam-se
replay-only: nenhum preenchimento live/mock de sufixo faltante. Lacunas incertas
falham fechadas. Publicação reutiliza o staging atômico do runner. A recuperação
de publicação sem selo compara CSVs, identidade, decisões e trace semântico,
preservando os bytes originais. Slots completos têm inventário e hashes; repetição
de comando reutiliza os resultados íntegros. Um lock abandonado exige investigação,
não recuperação automática com novas respostas.

Para cada spread em 0/5/10/20, três disposições LLM e três benchmarks são
predefinidos. 5 reutiliza baseline. Demais custos recalculam estado/quantidades
no motor com o matcher canônico completo. Caixa/posição/drawdown não são fixados
para obter correspondência. Divergência publica
`COST_SENSITIVITY_NOT_ESTIMABLE — EXACT_REPLAY_INVALID`, motivo e identidade;
métricas completas e resumo LLM ficam null. Não se agrega subconjunto válido.
Falha do cenário descritivo não invalida baseline íntegro. Benchmarks têm novas
instâncias determinísticas por cenário e resultados selados reutilizáveis.

Fixtures incluem inatividade com replay integral válido e uma perda gerada após
compra seguida de venda, que expõe alteração do payload Risk/Portfolio pelos
custos. São dados inventados para exercitar os contratos, sem relação com preços
reservados. O relatório JSON identifica separadamente essas disposições; seus
outcomes são exclusivamente sintéticos. CSVs/traces individuais são publicados e
verificados em diretório temporário, removido ao terminar; caminhos no relatório
são referências dessa execução de teste, não arquivos científicos permanentes.

## Fronteiras e release

| Fase sintética | Domínio | Última decisão | Settlement |
|---|---|---|---|
| Validation | 2024-09-02..2025-08-29 | 2025-08-28 | 2025-08-29 |
| Final | 2025-09-01..2026-08-31 | 2026-08-28 | 2026-08-31 |

Warmup inclusivo=504 (503 anteriores + primeira sessão). Nenhuma ordem passa
entre fases. O release exige três runs e benchmarks completos, selos, identidade
de fontes/tratamento/snapshot e calendário completo. Inatividade e degeneração
estatística não bloqueiam release; corrupção, tuning e incompletude bloqueiam.
O snapshot reservado real é rejeitado antes de acesso aos preços. O harness
exige attestation de geração sintética e não oferece opção live nem argumento
de arquivo de preços.

## Regressão e reprodução

Runtime observado: Python 3.13.9, NumPy 2.5.1, pandas 3.0.3, pydantic 2.13.4.
Ruff check e format --check passaram nos três arquivos novos.

Regressão direcionada a runner, fases, avaliação, métricas, custos, traces e
contratos Technical: 394 PASS e uma falha histórica de expectativa na primeira
execução (395 casos). O teste
`test_v5_development_s3_failure_blocks_further_phases` espera a mensagem v5 de S3;
no estado atual a CAL-B4 consumida ativa antes o guard `CAL-B4 must stay sealed
during v5 development`. A mesma falha foi reproduzida isoladamente sem importar
a camada nova. Não é uma falha científica nova nem foi escondida com skip.

Os 14 testes de `test_cal_b4_safety.py` passaram em sua reprodução contextual,
com `scripts.h2_v5.used_sessions` mockado para `anchors.CAL_B3_ANCHORS`
**apenas durante aquele teste histórico**. Os demais 13 mantiveram o estado
atual. O teste S3 passou também isoladamente nessa condição. Nenhum guard,
fonte, artifact ou status CAL-B4 foi alterado. Assim, 381 testes da regressão
restante passaram e os 14 de segurança passaram no contexto apropriado;
a suíte histórica sem esse fixture continua tendo a expectativa incompatível.

Reprodução da qualificação nova (asserts exigem Python sem `-O`):

```powershell
.venv/Scripts/python.exe -B scripts/qualify_h2_v6_evaluation.py
```

`--report <caminho_novo>` persiste o JSON sem sobrescrever relatórios existentes.
Rede externa é bloqueada; loopback é permitido para o self-pipe do asyncio.
Todos os clientes de inferência são mocks/replays, sem leitura de `.env` ou chave.

## Preservação e limites de autorização

O check existente verifica 6752 hashes de fontes/artifacts históricos, guards,
selos do raw batch, selos das dez anchors, auditoria automática e revisão humana.
ParticipantSpec H2 v6: `7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938`.
Commitment: `35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`.
Revisão humana: `33db64913ace88d2b5c72bcdc2b37b608f939e4ade0e681b4a46dbbbb1474733`.
Os 12 gates CAL-B4 e seu estado `CAL_B4_PASS — SANITY CHECK ONLY` são apenas
verificados; não recalculados com inferências ou outcomes.

Zero chamadas adicionais a Gemini/outro provedor. CAL-B4 permanece consumida
one-shot. Nenhum outcome financeiro reservado foi lido/calculado. Validation e
Final reais permanecem intocados; System Freeze não executado. Nenhuma assinatura
ou aprovação foi criada.

Pendências: assinaturas do autor/coautor e registro de concordância do orientador;
aprovação explícita do amendment e política de custos; vinculação definitiva de
código, ambiente e identities no futuro System Freeze; autorização específica
antes de qualquer execução real. A qualificação offline não autoriza a ponte
registry nem o escape `allow_dirty` para execução live. A correção da expectativa
do teste histórico exigiria revisão própria, pois sua fonte está congelada.

## Resultado técnico e versionamento

Os **15 grupos de checks novos passaram** em 320.18 segundos. No fixture em
caixa, os nove replays 0/10/20 bps foram íntegros; no fixture com compra/perda/venda,
os nove foram rejeitados por divergência, com motivos/identidades e sem métricas
completas. Baseline 5 foi reutilizado nos dois casos. Repetição de comandos não
criou chamadas adicionais; os contadores mock baseline/cenário ativo permaneceram
3705 e 4818 respectivamente. Final sintético degenerado manteve p/limite null.
Nenhum desses números representa execução ou desempenho real da H2.

Estado técnico, relativo à qualificação nova e aos testes de regressão no contexto
de ciclo de vida descrito acima:

`H2_V6 EVALUATION LAYER QUALIFIED OFFLINE — AWAITING FORMAL APPROVAL AND SYSTEM FREEZE`.

O resultado **não declara que a suíte histórica sem ajuste de contexto passou**;
sua falha de expectativa foi preservada e documentada. O estado de aprovação do
amendment continua pendente. Não declarar `READY FOR VALIDATION`.

Commit da implementação: `37f705c` — três arquivos novos. O relatório presente e
o JSON são versionados em commit separado de evidência offline, sem modificar
artifacts científicos anteriores. O identificador desse segundo commit é o
retornado por `git log -1 -- docs/H2_V6_EVALUATION_OFFLINE_QUALIFICATION.md`.
Após os commits, verificar `git status --short`, o escopo aditivo contra `199a294`
e o guard CAL-B4 sobre evidência comprometida. Parar: aprovações formais e futuro
System Freeze permanecem fora desta execução.
