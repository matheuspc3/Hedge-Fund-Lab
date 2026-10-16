# H2 v6 — auditoria anterior ao System Freeze

**H2_V6 SYSTEM FREEZE BLOCKED — EVALUATION PROTOCOL INCOMPLETE**.

A identidade científica e o fechamento da CAL-B4 passaram na auditoria. O freeze
definitivo não foi realizado: o item 3 do pedido exige reportar definições
necessárias ausentes/ambíguas antes do freeze e proíbe preencher lacunas
silenciosamente. Não existe manifesto definitivo de System Freeze nem comando
Validation qualificado. Nenhum resultado reservado foi aberto; zero chamadas
externas. A CAL-B4 continua PASS e SYSTEM_CALIBRATION_COMPLETE=True.

Evidência estruturada e todos os hashes observados:
[system_freeze_pre_audit.json](system_freeze_pre_audit.json).
Esse arquivo é auditoria, **não um manifesto de freeze** e não autoriza execução.
Commit de referência: `9f4e1fb465225384f61bf3d509b931fda9f0e985`, branch `#1-Update`.

## 1. Auditoria pré-freeze

O comando/guard existente `run_cal_b4.verified_batch` conferiu freeze anterior,
raw batch, dez anchor seals, commitment, autorização específica e árvore limpa.
Foi verificado também AUDIT_SEAL.json, os 12 gates e a revisão humana commitada.
Não foram regenerados status, gates, respostas ou avaliações humanas.

| Verificação | Resultado |
|---|---|
| Estado canônico | CAL_B4_PASS — SANITY CHECK ONLY |
| SYSTEM_CALIBRATION_COMPLETE | True |
| Anchors / automatic gates / human fields | 10/10 / 12/12 PASS / 40/40 PASS |
| Assinatura | Lucas Pereira da Silva, 2026-10-08T23:10:22Z |
| Commits de revisão / fechamento | d71777b / 9f4e1fb |
| One-shot | CONSUMED; R=1; raw inalterado desde c5aa362 |
| Artefatos baseline | 6752 arquivos e guardas preservados |
| Validation / Final Test | NOT EXECUTED |
| Outcomes financeiros CAL-B4 | NOT COMPUTED |

ParticipantSpec final:
`7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938`.
Commitment CAL-B4:
`35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`.
Ambos conferem integralmente com os arquivos canônicos e a autorização assinada.

## 2. Tratamento aprovado, preservado

H2 treatment 6; Technical prompt 5; response schema 2; evidence vocabulary 1;
evidence validator 1; Risk prompt 2; Portfolio existente; Technical checker v3.
N=5, consensus_threshold=0.6, require_all_votes=true. Runtime Gemini native,
gemini-3.8-flash, LOW, temperature=1.0, max_output_tokens=8192, sem seed
transmitida, retry_attempts=6 e retry_base_delay=2.0.

Parâmetros: volatility_window=21; risk_max_volatility=0.50;
risk_max_drawdown=0.25; risk_max_concentration=1.0; long_target_weight=1.0.
O JSON de auditoria registra a ParticipantSpec completa, sem recompor defaults.
Nenhum tratamento, prompt, contrato, checker ou parâmetro foi alterado.

As oito features continuam: bb_lower_gap, bb_upper_gap, bb_width, macd_ratio,
macd_signal_ratio, rsi, sma200_gap, sma50_gap. Fórmulas e transformação causal
permanecem nas fontes existentes, com hashes observados de features.py,
pipeline/transform.py, participant.py e contratos associados. Nenhuma feature
real Validation/Final foi calculada.

| Contrato | SHA256 observado |
|---|---|
| Technical prompt v5 | b041c5f03e20296f06f254629227b6a55978eb2aefccd1ba5eade33aac520a5d |
| Risk prompt v2 | 990424e307e2c593afc40ebafef2c12387029ecf46a285f18a595c447e1e2151 |
| Portfolio prompt | 497b56e89f1f2fc193f999e6bc23c88cccb7a2c6da96de5c11f09417482ae68a |
| TechnicalEvidenceResponse v2 | e7c50f92fecb48508e6531cf30c4de2a857a47a76646be371e43ea7482276712 |
| RiskVerdict | 482b3eaee55f3d6dbce991e5f72bf340d5841ed6542a8aa9691ab8052e0e9c53 |
| PortfolioAction | 5fda582a11b128eb75c91758ae380f8eecfb999d277a36cd6f6b4ddda0ad9ad4 |

Snapshot existente: `20261004T201258177516Z-b4cf39fc761f251d2dd18e787008345a`;
identity `b4cf39fc761f251d2dd18e787008345aaf02bd9e19f913390c510338b84ee7d4`.
PETR4.SA CSV SHA256:
`7b6a0018191028ecea2ee66785c27f771a721aa4a96c4953ca87ac6d688c3ffa`.
Manifest e hashes dos bytes foram verificados pelo helper de snapshot existente;
nenhum OHLCV foi convertido em feature/decisão/performance reservada. Calendário
B3, políticas B3 COTAHIST/Yahoo adjustment e integridade existentes preservados.

## 3. Avaliação: aprovado versus ainda aberto

Sharpe anualizado líquido é a métrica primária; rf=0 e cash_return=0.
H2_SCIENTIFIC_SHARPE_DEFINITION_V1 já aprovado pelo Amendment 5: retornos líquidos
diários da curva, dias em caixa e settlement incluídos; mean(r-rf/252) /
std(r,ddof=1) * sqrt(252). Convenção existente: menos de dois retornos ou desvio
<1e-15 produz escore 0; NaN/inf falha fechado. Nenhuma convenção foi alterada.

Famílias aprovadas: Buy & Hold primário; SMA/Bollinger secundários.
Baseline de custos: brokerage_fixed=0, spread_bps=5, tax_rate=0.00032;
capital inicial=100000; quantity_mode=fractional_notional. Sensibilidade de custo
já pré-declarada no protocolo: spread_bps em {0,5,10,20}, brokerage/tax fixos,
somente descritiva e sem seleção. Esse desenho não foi inventado nesta tarefa.

**Resultados financeiros negativos são cientificamente válidos.** Não se exige
retorno positivo nem superioridade para aceitar uma execução íntegra; nenhuma
mudança oportunista ou exclusão de run desfavorável é autorizada.

Bloqueios que impedem o freeze definitivo:

| ID | Definição pendente | Fonte canônica |
|---|---|---|
| SF-B1 | Contraste H2 v6 e H0/H1 formais, direção e critérios de inferência. A monografia tem H1 clássico vs Equal Weight, H2 LLM vs benchmarks e H0 genérica; isso não resolve os TBD do protocolo. | EXPERIMENT_PROTOCOL §2; monografia §Síntese e Hipóteses |
| SF-B2 | Número exato de replicações Validation/Final. Proposta 2–3 para Validation é explicitamente não congelada. R=3 development e R=1 CAL-B4 não fixam evaluation R. | EXPERIMENT_PROTOCOL §15 |
| SF-B3 | Regra de agregação dos runs: primeiro, média, mediana ou outra ainda não escolhida. | EXPERIMENT_PROTOCOL §15, Repetições da Validation |
| SF-B4 | Teste estatístico, significância, intervalos, multiplicidade, dependência temporal e unidade de reamostragem. | EXPERIMENT_PROTOCOL §18 |
| SF-B5 | ParticipantSpecs exatas dos benchmarks, parâmetros e frequência. Defaults SMA50/200 e Bollinger20/2 e o indicator-family control não são aprovação das specs separadas. | EXPERIMENT_PROTOCOL §12; monografia comentário dos benchmarks |
| SF-B6 | Política científica das métricas secundárias: MAR do Sortino e turnover de ordens. Código identifica MAR como default técnico; turnover atual é mudança média de pesos observados, com drift, expressamente não congelado como turnover científico. | backtesting/metrics.py:167 e :210; EXPERIMENT_PROTOCOL §17 |

A busca nos documentos H2/amendments não encontrou decisão posterior que feche
essas lacunas. O protocolo principal identifica-se como DRAFT e instrui que TBD
não é decisão aprovada. Não foram escolhidos novos valores, testes ou thresholds.

## 4. Janelas e ausência de lookahead

Datas do pedido registradas apenas como limites autorizados para o futuro. O
calendário foi consultado sem prices, features, payloads ou resultados reservados.

| Fase | Domínio | Última decisão pela regra existente | Settlement | Sessões do domínio |
|---|---|---|---|---|
| Validation | 2024-09-02 → 2025-08-29 | 2025-08-28 | 2025-08-29 | 248 |
| Final Test | 2025-09-01 → 2026-08-31 | 2026-08-28 | 2026-08-31 | 250 |

A última sessão é settlement, não nova decisão: no_order_execution_may_cross_phase_boundary
já exige execução dentro da fase. Decidir em 2025-08-29 liquidaria em 2025-09-01,
invadindo Final; decidir em 2026-08-31 exigiria uma barra fora do domínio/snapshot.
Não foram truncadas janelas silenciosamente: a distinção domínio/decision_end é
explicitada aqui e deverá entrar nas specs futuras após resolver os bloqueios.

O motor atual decide com cópia do histórico `.loc[:session]`, executa intents
pendentes no open seguinte e não chama participante no settlement. Warmup é
histórico, não decisão/trade/performance; mínimo aprovado de 504 sessões.
O runner suporta PhaseWindow explícita, recorta o motor em phase.end e recusa
settlement fora da fase antes de criar participante. Os testes sintéticos
confirmam essas propriedades. PHASES atual só declara Sequential; os limites
Validation/Final terão de ser ligados explicitamente na infraestrutura futura.

Validation deve vir primeiro. Final Test continua proibido até conclusão formal
de Validation e conferência da identidade congelada. Não existe nesta auditoria
um gate de liberação Final improvisado ou baseado em desempenho observado.

## 5. Proteções e preparação operacional

Os guardas existentes da CAL-B4 continuam ativos. A infraestrutura genérica
verifica snapshot, provenance limpa, spec, execução fracionária, schemas e replay.
Replay identifica provider/model, prompts, opções, schema, papel, analista e
sessão; divergência/sobra/falta falha fechado. Persistência publica artifacts
atomicamente e preserva o snapshot/trace capturados no run.

Isso não equivale a um guard pós-System-Freeze completo: o ExperimentRunner
genérico aceita diferentes specs materialmente declaradas, e RunContext sozinho
não exige Validation concluída antes de Final. Sem protocolo final aprovado,
não foi criado wrapper que dê aparência de congelamento ou libere uma fase.
Modelo remoto não permite congelar pesos internos; futuro live requer auditar
resolved_model e manter o replay como reprodução exata, sem atualizar alias.

Idempotência live/resume de Validation, número de runs, agregação e checkpoint de
liberação Final deverão ser qualificados depois da definição ex ante. Não se
confunde atomicidade de persistência nem run_ids distintos com garantia de
idempotência de chamadas externas.

Desenvolvimento de UI/exportação/visualização poderá continuar se separado dos
contratos/resultados científicos; não alterar funções de tratamento/métricas
para resolver necessidades da interface.

**Comando Validation live: NÃO PREPARADO/LIBERADO**, porque a configuração de
avaliação necessária ainda não está integralmente definida. Nenhum runner foi
editado para ignorar guards. Nenhuma chamada Gemini foi executada.

## 6. Testes offline

**381 PASS, 0 FAIL, 48.07 s**, usando apenas mocks e fixtures sintéticas.
Comando integral reproduzível em system_freeze_pre_audit.json.

Cobertura: guards de snapshot/spec/provenance, janela e warmup causal,
settlement/phase boundary, v6 strict evidence, traces, replay de decisões/trades/
equity/métricas e mismatch fail-closed, persistência atômica/manifest, execução
fracionária, custos e funções canônicas/Scientific Sharpe.
Os testes passaram com temporários restritos ao workspace. Não executaram
Validation/Final reais nem produziram outcomes CAL-B4. Passar testes genéricos
não qualifica o futuro protocolo estatístico ou o comando específico de fase.

## 7. Entrega, estado e próximo passo

Criados somente esta auditoria, seu JSON e uma nota de estado; nenhum arquivo
de tratamento ou artefato científico anterior foi alterado. A revisão assinada,
status CAL-B4 PASS, raw evidence, gates e hashes são preservados.

System Freeze definitivo: NOT EXECUTED; Validation/Final: NOT EXECUTED;
Gemini/external calls: 0; CAL-B4 outcomes: NOT COMPUTED.
Estado permitido: **READY FOR SYSTEM FREEZE DESIGN**, com bloqueios SF-B1..SF-B6.
Não registrar H2_V6 SYSTEM FREEZE COMPLETE — READY FOR VALIDATION.

Próximo passo: decisão explícita dos autores em um amendment de avaliação que
resolva SF-B1..SF-B6; depois retomar o freeze e a qualificação dos guards/CLI.
Não é necessário reabrir a CAL-B4 nem repetir development para declarar essas
escolhas antes de qualquer resultado reservado. Não inventá-las nesta auditoria.

O commit que introduz esta auditoria registra a entrega bloqueada; HEAD de
referência acima permite auditar o diff. O Git ficará limpo após esse commit.
