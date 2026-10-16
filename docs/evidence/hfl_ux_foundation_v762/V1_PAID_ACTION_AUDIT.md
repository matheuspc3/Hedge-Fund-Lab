# Ação paga obsoleta do Global PM V1: auditoria e correção na interface

## 1. Contexto

O tratamento `HFL-MULTIASSET-GLOBAL-PM-V1` tem resultado oficial
`REJECTED_BY_VALIDATOR` (registro `v7-5a78ea5d15214e37bcae18f167ffcee3`) e foi
encerrado para novas inferências pelo protocolo V7.6. A auditoria V7.6.1 (U10)
mostrou que `/portfolio` ainda oferecia o fluxo pago desse tratamento.

## 2. Gatilhos localizados

| Elemento (`portfolio.html`) | Ação JS (`global-workflow.js`) | Requisição | Efeito |
|---|---|---|---|
| `#workflow-prepare` "2. Preparar snapshot e Risk · sem Gemini" | listener de clique → `post('prepare')` | `POST /api/platform/global-prepare` | grava contexto V1 novo |
| `#workflow-preflight` "3. Preflight global" | `api('global-preflight?…')` | `GET` | gera token de confirmação |
| `#workflow-run` "4. Solicitar proposta · confirmar custo" | abre `#workflow-confirm` | — | etapa de consentimento |
| `#workflow-authorize` "Confirmar somente esta inferência" | `post('run', {authorize_paid})` | `POST /api/platform/global-run` | **inferência paga V1** (modo oficial) |
| `#workflow-replay` "Recuperar somente offline" | `post('replay')` | `POST /api/platform/global-replay` | recuperação sem nova chamada |

Outros caminhos pela interface: nenhum. Só `global-workflow.js` monta
`'global-'+command` (verificado por teste). A seção "Proposta da IA"
(demonstrações A–F) usa apenas respostas roteirizadas, sem custo.

## 3. Correção (apresentação apenas)

- Os botões de preparar, verificar requisitos e solicitar ficam **ocultos e
  desabilitados**, junto com os consentimentos e o orçamento, num grupo
  `data-closed-v1`.
- `global-workflow.js` ganhou `const V1_CLOSED=true`:
  - os ouvintes de preparar, verificar, solicitar e autorizar retornam sem efeito;
  - `controls()` mantém os três desabilitados;
  - `post()` recusa qualquer comando que não seja `replay`, com a mensagem
    abaixo, mesmo que alguém reexiba os botões pelo DevTools (teste
    "v1:forced_clicks_do_nothing").
- Aviso visível no topo do Gestor Global, com selo "Tratamento encerrado":
  "Este tratamento (`HFL-MULTIASSET-GLOBAL-PM-V1`) foi encerrado para novas
  inferências. Os resultados anteriores permanecem disponíveis para consulta e
  auditoria." O aviso informa ainda que a V2 roda só pelo CLI, com verificação e
  autorização humana separadas, e que o painel não oferece atalho pago para ela.
- Estados que sugeriam continuar o fluxo ("aguardando preflight", "pronto para
  solicitar inferência") passaram a "novas inferências pelo painel desativadas".

## 4. Preservado

- Consulta de registros (lista e detalhe), inclusive o V1 rejeitado: o detalhe
  mostra `REJECTED_BY_VALIDATOR` com selo próprio e a identidade V1 (teste
  "v1:history_still_consultable_and_rejected").
- Recuperação sem nova chamada (`global-replay`) para registros existentes.
- Registros, contextos, claims, journals, resultado selado e evidências: nenhum
  arquivo de dados foi tocado.
- A V2 continua `VALID_PROPOSAL` e **não** ganhou caminho pago na interface (o
  botão de solicitar segue desabilitado também para registros V2).

## 5. Risco operacional residual (backend)

**A desativação é da interface, não um bloqueio de segurança completo.** O
servidor continua aceitando `POST /api/platform/global-prepare` e
`/global-run` (`dashboard/server.py`, `_handle_platform` →
`platform_api.GLOBAL_JOBS.start` → `run_global_pm`, runner V1). Uma requisição
forjada por um processo local ainda precisaria de origem local, token CSRF,
preflight válido com token de confirmação, `authorize_paid`, origem Radar
`VERIFIED`, orçamento disponível e `GEMINI_API_KEY` no ambiente do servidor. A
chave é carregada do `.env` desde o commit `946813d`. Os controles reduzem o
risco, mas a rota existe.

**Recomendação (exige aprovação, não aplicada):** recusar no servidor
`global-prepare`/`global-run` para a identidade V1 com um erro
`treatment_closed_for_new_inferences`, mantendo `global-replay`. Isso altera
o comportamento do backend e os testes de rota de `test_platform_v7`; por isso
fica como decisão humana separada.

## 6. Verificação

| Verificação | Resultado |
|---|---|
| Botões V1 desabilitados e ocultos (navegador) | aprovado |
| Cliques forçados após reexibir os botões: nenhum diálogo, nenhuma requisição | aprovado |
| Aviso de encerramento visível | aprovado |
| Histórico V1 consultável e rejeitado | aprovado |
| V2 validada e sem atalho pago | aprovado |
| `test_platform_ui` (Node, DOM simulado): preflight, solicitar, autorizar e preparar não enviam nada; replay ainda envia | aprovado |
| Mutação `V1_CLOSED=false` | derruba `test_platform_ui` e `test_ui_v762::test_closed_v1_triggers_and_no_new_paid_path` |
