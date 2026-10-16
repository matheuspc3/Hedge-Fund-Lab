# V7 — auditoria inicial da plataforma

Levantamento em 11/10/2026, antes de modificar código. Base local `e54883d`,
branch `#1-Update`, árvore limpa. Não houve execução de modelos, download,
aprovação, reconciliação ou acesso a resultados do Final Test.

## Matriz de páginas e fluxos existentes

| Página / função | Endereço anterior | Dados / autoridade | Endpoints | Ações | Estados efetivos | Duplicações, nomes e limitações | Destino V7 |
|---|---|---|---|---|---|---|---|
| Dashboard genérico legado | `/`, `/index.html` | `dashboard/data.json`, export de backtests | `/data.json` | filtros, gráficos de ativos/estratégias | loading, erro, dados locais | “Portfólio Multi-Ativo” pode ser confundido com V5; tema e navegação próprios; export estático não prospectivo | preservar `/index.html`, alias `/legacy`; raiz passa a visão operacional |
| Histórico H2 v6 | `/h2` | Validation provisória/oficial allowlisted, manifesto e governança | `/api/h2/status`, `validation`, `analysis` | trocar fonte e seis abas | não iniciada, execução, interrompida, selada, demo | outra “Visão geral”; seis abas necessárias; fonte demo nunca se mistura; avisos científicos indispensáveis | Pesquisa e Auditoria, seis abas preservadas |
| Histórico — decisões/multiagente | `/h2#provisional/decisions`, `/agents` no fragmento | decisões e traces normalizados de Validation | `/api/h2/decision`, `analysis` | consultar sessão, run, evidências | disponível, carregando, ausente | votos históricos distintos dos agentes prospectivos; não é catálogo ativo | manter no histórico |
| Histórico — auditoria | `/h2#provisional/audit` | manifests, checkpoints, métricas e arquivos públicos allowlisted | `/api/h2/run`, `trace`, `artifact` | consultar/baixar artefatos públicos | ausente, disponível, bloqueado | journals/envelopes privados excluídos; Final Test bloqueado | manter fonte de autoridade científica |
| Paper — resumo | `/paper#visao` | forward original + B&H sombra + SMA/Bollinger + supervisionada | `/api/forward/portfolios`, `decision`, `history` | seleção de curvas e consulta | sem carteira, observação única, comparável/não comparável | “Visão Geral” local duplicada; patrimônios alternativos não somáveis | preservar resumo local, landing agrega separadamente |
| Sala de Decisão | `/paper#sala` | input, votos, Risk, PM, intenção e reconciliação gravados | `/api/forward/decision`, `history` | consultar decisão; preparar, preflight, confirmar inferência | AGUARDANDO, DECIDED, FAILED, MISSED, LATE_NOT_EXECUTABLE | blocos extensos de analistas antes da decisão financeira; decisão existente não admite nova chamada | Operação; priorizar síntese, manter detalhes expansíveis |
| Supervisão humana | painel dentro de `/paper#sala` | ledger `h2_v6_supervised`, proposals/approvals/audit | GET `supervision`; POST `supervision/sync`, `approve`, `reject`, `cancel` | ação humana explícita, limites, cancelamento antes do prazo | AGUARDANDO_APROVACAO, APROVADA, REJEITADA, EXPIRADA, PENDENTE_ABERTURA, EXECUTADA, bloqueios | não tinha acesso direto de navegação; recomendação ≠ aprovação ≠ execução | link contextual para o mesmo painel, sem segundo fluxo de aprovação |
| Carteiras prospectivas | `/paper#carteiras` | cinco estratégias existentes, ledgers separados | `/api/forward/portfolios` | selecionar carteira, trades/composição | disponível, indisponível, divergente | mesmo capital de referência; proventos não lançados separadamente; ajustes já preservam valor | Operação; jamais somar ou preencher carteiras ausentes |
| Mercado/simulador | `/paper#mercado`, formulário da Sala | cache oficial congelado; provider intradiário offline | GET `market`; POST `scenario` | consulta manual e cenário em memória | fechado/pré-abertura/negociação/encerrado/desconhecido; limite/dado insuficiente/desatualizado | sem cotação intradiária; simulação não confirma abertura; grade tem horizonte documentado | Operação; reutilizar calendário e simulador |
| Catálogo de agentes | `/paper#agentes` | configuração H2 congelada + catálogo exploratório | `/api/forward/agents` | perfil, simulador local de quórum | cinco ativos; 25 slots disponíveis; Risk e PM | catálogo de 32 slots já existe; slots não equivalem a votos efetivos | Laboratório, link para catálogo existente |
| Radar Multiativos V4 | `/radar` | `data/radar/hfl_multiasset_v1` ou raiz explícita de demonstração | GET `status`, `search`, `detail`; POST `universe`, `prepare`, `preflight`, `run` | até cinco ativos, preparo, autorização paga, replay, detalhe/comparação | PREPARED, COMPLETED, INTEGRITY_ERROR, FAILED_REPLAY_ONLY, RUNNING, recuperação | header/tema próprios; universo persistido ≠ pareceres selecionados; só link genérico para Global PM | manter runner/API selados; transferir seleção, sessão e fonte explicitamente |
| Contabilidade multiativos V5 | parte inferior de `/portfolio` | `demo-qualified-v5`, cadeia de 22 eventos | GET `/api/portfolio/status`, `case`, `scenario` | consulta e simulação em memória | demo ausente, íntegra, plano válido/rejeitado | “Gestor de Carteira” reúne demo contábil e proposta; não é carteira prospectiva | área sintética explicitamente separada; nenhum executor novo |
| Proposta Global V6 | parte superior de `/portfolio` | índice A–F, snapshots/contextos novos, CallBank privado | GET `/api/global-pm/status`, `case`, `simulate`, `selection`, `prepared`, `preflight` | consulta A–F, simulação, prévia de seleção; prepare/run somente CLI | NO_PROPOSAL, AWAITING_PREFLIGHT, VALID_PROPOSAL, REJECTED_BY_VALIDATOR, PROVIDER_FAILED, RECOVERY_REQUIRED, PROPOSAL_EXPIRED | falta passagem funcional Radar→contexto; UI não prepara ou solicita inferência; fake não é Gemini; validade 24 h | nova fronteira HTTP controlada delega ao runner V6 inalterado |
| Jobs H2 | `/api/forward/status` + painel da Sala | `data/forward/h2_v6_dashboard`, claims e locks | POSTs operacionais existentes | prepare/preflight/run/sync | RUNNING, COMPLETE, FAILED; READY/DECISION_EXISTS/RECOVERY_REQUIRED nos gates | observabilidade dispersa; resultado de preflight pode estar obsoleto; subprocessos são comandos fixos, sem shell | agregação pública somente leitura, preservando estados originais |
| Logs técnicos legados | `/logs`, `/logs.html` | arquivo de log local | `/api/logs` SSE | filtros de linhas e pausa | conectado, aguardando, desconectado | não é autoridade científica nem ledger; diagnóstico separado dos journals privados | preservar compatibilidade; auditoria central usa projeções allowlisted |

## Estado local observado

- Cinco carteiras prospectivas realmente existem. Cada uma marca R$ 100.000,
  caixa R$ 100.000, zero posição; última marca 09/10/2026. São alternativas.
- Decisão original de 09/10: `DECIDED`, gerada em 10/10 às 15:17 BRT; intenção
  para 13/10. SHA-256 `27e51c949aebac155b1d890c6fff74d1a242852d7f5c8d3a30cdc602a6a09ddc`.
- Supervisionada: `AGUARDANDO_APROVACAO`, prazo 13/10/2026 10:00 BRT,
  auditoria íntegra com um evento; nenhuma aprovação registrada.
- SMA e Bollinger existem e são comparáveis. B&H é a sombra do ledger original.
- Radar oficial: quatro inputs preparados para 09/10, sem parecer completo;
  os cinco pareceres necessários ao Global PM oficial estão ausentes.
- V5/V6 são demonstrações sintéticas seladas e independentes. V6 A–E válidos,
  F rejeitado. Não são patrimônio prospectivo nem inferência real do Gemini.
- Próxima sessão segundo calendário existente: 13/10, abertura prevista 10:00
  BRT. Previsão não comprova leilão/negociação efetivos; intradiário indisponível.

## Decisões de consolidação

1. Um servidor, uma raiz operacional, quatro grupos: Visão Geral, Operação,
   Laboratório, Pesquisa e Auditoria. Shell e tokens visuais compartilhados.
2. Preservar páginas/rotas/endpoints e JS especializados. Links contextuais usam
   os painéis existentes; não criar segundo catálogo, carteira ou aprovação.
3. API de plataforma agrega projeções verificáveis. Não copia ledgers e não
   declara integridade apenas porque conseguiu ler um JSON.
4. Integração Global PM aceita somente IDs locais restritos, contextos novos,
   seleção da mesma fonte/sessão, consentimento de snapshot hipotético e limites
   didáticos. Preflight e autorização de custo próprios, sem disparar Radar.
5. POSTs novos exigem loopback/Host/Origin/CSRF, JSON estrito, orçamento,
   idempotência e testes de falha/recuperação. Nenhum comando shell é criado
   com dados do browser. Nenhuma execução financeira multiativos é oferecida.
6. Diagnóstico somente leitura e runbook orientam 13/10. Não inferem, baixam,
   reconciliam, aprovam, removem claims ou inicializam carteiras ao consultar.

## Inventário de dependências e preservação

Inspecionados os arquivos HTML/CSS/JS, APIs, jobs, servidor e assets em
`dashboard/` (o export de dados é tratado como legado, sem carregar dados
científicos desnecessários); runners Forward, Supervised, Benchmarks, Radar,
financeiro V5 e Global PM V6; guias Premium V1–V6 e testes relevantes.
Chart.js é local, com licença no repositório. Python stdlib + dependências
existentes cobrem a consolidação. Não é necessário novo framework/banco.

Baseline anterior ao código: `docs/evidence/hfl_platform_v7/preservation_baseline.json`,
estendendo o inventário V6 com decisões/ledgers e demonstrações posteriores.
Fontes seladas, `src/`, manifesto, Validation, Final Test e evidências anteriores
permanecem protegidos. Nenhum diretório científico será reorganizado.
