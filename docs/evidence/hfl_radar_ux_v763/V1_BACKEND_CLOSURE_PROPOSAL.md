# Auditoria de encerramento do Global PM V1

**BACKEND_V1_CLOSURE_PENDING_APPROVAL** — proposta não aplicada. O pedido autoriza
auditoria e apresentação, não a mudança dos contratos operacionais/científicos.

## Caminhos encontrados

| Entrada | Encadeamento | Efeito / proteção atual |
|---|---|---|
| UI Carteira | `global-workflow.js::post` | `V1_CLOSED=true`; preparar/preflight/solicitar/autorizar não enviam; replay permanece |
| `POST /api/platform/global-prepare` | `Handler.do_POST` → `_handle_platform` → `GLOBAL_JOBS.start('prepare')` → `_work` → `cli.prepare` | Cria contexto V1; origem local, CSRF, payload estrito, consentimentos hipotético/fixture, elegibilidade dos pareceres e não sobrescrita |
| `POST /api/platform/global-run` | mesmos handlers → `start('run')` → `_work` → `scripts/run_global_pm.py::run` | Pode chamar Gemini; preflight, token, autorização paga, chave, origem Radar VERIFIED, validade, locks, reserva e claim |
| `POST /api/platform/global-replay` | `start('replay')` → `cli.run(replay=True)` | Exige contexto/claim/journal existentes; `fresh=False` e `no_network`; sem envelope recuperável, falha sem substituição |
| Chamada Python direta | `GlobalJobs.start`, `GlobalJobs._work`, `cli.prepare`, `cli.run` | `start` é o ponto compartilhado dos handlers; invocação direta do runner não passa pelo handler/CSRF/origem Radar da plataforma |
| CLI V1 | `run_global_pm.py prepare/preflight/run/replay/status/demo` | `run --confirm … --authorize-paid` ainda pode pagar se os gates forem satisfeitos; prepare congela contexto; demo é sintético |
| Cliente de baixo nível | `GlobalGeminiClient.propose` / `_transport` | Camada durável CallBank/Recording/Replay; não é uma política de encerramento V1; a V2 herda a classe |

`global_pm_api.py` importa `run_global_pm as cli`; `platform_api.py` reutiliza esse
alias. `global_pm_api.get` oferece seleção/status/case/simulate/prepared/preflight,
somente leitura ou projeção em memória. Não há POST `/api/global-pm/*` de inferência.
GETs da plataforma (`global`, `jobs`, `overview`, `global-preflight`) também não
executam o runner. A V2 utiliza seu próprio CLI e mantém identidade própria.

Busca realizada nos callers de `cli.prepare`, `cli.run`, `run_global_pm` e
`GlobalGeminiClient`, incluindo dashboard, scripts e testes. Não foram acionados
POSTs reais nem a CLI paga para comprovar a exposição.

## Proposta pronta para uma aprovação posterior

1. **Encerrar o servidor no ponto compartilhado não selado:** no início de
   `platform_api.GlobalJobs.start`, recusar `prepare` e `run`, antes de resolver
   caminhos, criar jobs, locks, reservas ou threads. Essa classe é exclusivamente
   V1; `replay` permanece. Código estável: `treatment_closed_for_new_inferences`.
   O handler atual traduz `ValueError` para HTTP 400; se desejado, mapear esse
   código especificamente para 410, sem mudar os demais erros.

   ```python
   # Proposta apenas; não aplicada nesta entrega.
   if command in {"prepare", "run"}:
       raise ValueError("treatment_closed_for_new_inferences")
   ```

2. Manter GETs históricos/status/detalhe e a identidade V1, os resultados
   rejeitados e a recuperação offline. Não redirecionar V1 para V2. Tokens de
   preflight antigos também deverão ser recusados pelo gate de `start`.
3. Para fechar também execuções diretas fora do servidor, retirar chave/egress
   do ambiente arquivado V1 e oferecer recuperação em processo offline separado;
   a V2 deve receber credenciais apenas em seu próprio ambiente autorizado.
   Um gate HTTP não revoga a capacidade de código local que possua a chave.
4. Não inserir a regra na classe `GlobalGeminiClient`: a V2 herda essa classe.
   Uma eventual mudança da CLI/runner V1 exige um plano específico para preservar
   o ambiente científico arquivado e seus hashes, além da aprovação humana.

### Por que não editar diretamente o runner selado

`multiasset_global_pm.contracts()` inclui hashes de `run_global_pm.py` e de
outros sources. `checked_context()` compara contratos armazenados com os atuais;
`run_global_pm.context_for()` é usado inclusive por `detail` e replay. Alterar
esse arquivo faria contextos históricos falharem na verificação. A identidade
V2 também registra sources V1. Não resolver isso regravando selos ou relaxando o
comparador: preservar o ambiente arquivado é parte da aprovação futura.

## Plano de verificação da futura correção

- POST prepare/run com requisições previamente válidas → erro de encerramento;
  jobs, snapshots, contextos, locks, claims, reservas e journals inalterados.
- Chamada direta de `GlobalJobs.start` com os mesmos comandos → mesmo erro.
- GETs de histórico, V1 `REJECTED_BY_VALIDATOR`, V2 `VALID_PROPOSAL`, status e
  auditoria → resultados idênticos.
- Replay de envelope existente → sem transporte; replay de chamada incerta →
  erro e nenhuma substituição. Reproduções de incidentes apenas em temporários,
  com transports falsos/offline e identificados como diagnóstico.
- CLI oficial em ambiente V1 arquivado → sem chave e sem egress; V2 isolada.
- Preservação V7.5/V7.6 e hashes de todos os selos sem divergência.

Testes existentes relevantes: `tests/test_platform_v7.py` (payload, origem Radar,
worker, conflito, recuperação); `tests/test_platform_ui.py` e `test_ui_v762.py`
(UI encerrada); `test_global_pm.py` 24–30, 34–39 (validade, autorização, orçamento,
crashes, replay e adulteração); `test_global_pm_v2.py` (contratos/herança V2).
Esses testes não devem ser modificados para aceitar alteração de evidência selada.
