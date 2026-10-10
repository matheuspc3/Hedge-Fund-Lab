# Hedge-Fund-Lab — Premium UI v1 (`/paper`)

Evolução visual e de organização do dashboard operacional prospectivo. Nenhuma
funcionalidade operacional foi reimplementada: prepare/preflight/run, claims,
CSRF, confirmação HMAC e benchmarks continuam exatamente como em
[H2_V6_FORWARD_DASHBOARD.md](H2_V6_FORWARD_DASHBOARD.md).

## Áreas

| Área | Hash | Conteúdo |
|---|---|---|
| Visão Geral | `#visao` (padrão) | Uma ficha por carteira, gráfico comparativo, resumo da última deliberação |
| Sala de Decisão | `#sala` | Fluxo da decisão, comitê, quórum, síntese das evidências, Risk/Portfolio, histórico, operação |
| Carteiras | `#carteiras` | Tabela comparativa, composição, intenção pendente, curva, operações, proventos |
| Agentes | `#agentes` | Configuração congelada, simulador de quórum, catálogo de 32 posições, ficha individual |

Os hashes antigos `#room` e `#wallets` continuam abrindo Sala e Carteiras. A
navegação usa links nativos com `aria-current` (teclado e leitores de tela
funcionam sem JavaScript adicional); em ≤520 px vira grade 2×2, sem abas ocultas.
`/h2` (Validation OA-1) não foi alterado.

## Regras de apresentação

- **Patrimônios não são somados.** As quatro carteiras são simulações paralelas
  com o mesmo capital inicial.
- **Intenção ≠ posição.** A composição é sempre a do último fechamento
  reconciliado; a intenção pendente aparece em barra tracejada separada. Caixa
  100% aparece como segmento de caixa, nunca como barra de PETR4 cheia.
- **Gráfico por número de observações:** 0 → estado vazio; 1 → bloco compacto
  com o ponto inicial; 2+ → linhas com seleção de estratégias, tooltip e tabela.
  Carteira não comparável sai do gráfico com nota; carteira com marcação mais
  antiga que as demais é sinalizada como "sem novos dados".
- **Drawdown** só com 2+ fechamentos; antes disso `N/D`.
- **Ausências explícitas:** `N/D`, "Sem observações", "Sem resposta gravada".
  Analistas ausentes não recebem voto; respostas inválidas aparecem como tal.
- **Síntese "por que decidiram"** agrupa as evidências estruturadas gravadas por
  posição em relação ao sinal agregado (favorável, cautela, contrária, neutra),
  com frequência e analistas que a citaram. Sem sinal direcional (MANTER ou sem
  consenso), mantém o papel literal (suporte à COMPRA/VENDA). Rótulos com valor
  (ex.: `RSI atual = 74.915165`) vêm do texto renderizado já gravado no trace.
  Não há nova chamada ao modelo.
- **Confiança coletiva** é explicada como gravada pelo agregador
  (`src/agents/technical_analyst.py`): média das confianças dos votos vencedores
  × fração do comitê no sinal vencedor; não é probabilidade de acerto.
- **Fluxo da decisão** marca "Não alterou" quando Risk aprova ou Portfolio
  confirma o sinal agregado. Estados de ordem: Pendente, Executada, Reconciliada
  sem operação, Sem ordem necessária, Não executável (LATE), Sem ordem (FAILED),
  Sem decisão (MISSED/aguardando).
- **Agentes:** 30 slots Technical + Risk + Portfolio. Apenas os 5 declarados no
  manifesto congelado (`analyst_count`) são ativos; os 25 restantes são "slot
  livre · sem histórico" e não são clicáveis. A ficha mostra modelo, versão do
  prompt, parâmetros do manifesto, seed observada, chamadas, distribuição,
  confiança média, concordância com o consenso (só Technical), erros, retries,
  tokens e custo estimado (preço de tabela registrado no runner OA-1). Risk e
  Portfolio não têm tokens gravados pelo provedor: `N/D`. A versão do prompt do
  Portfolio não está declarada no manifesto: `N/D`.
- **Comitês futuros:** a configuração H2 v6 é exibida como congelada e não
  editável. O simulador local aplica a regra de agregação (inclusive desempate
  MANTER → COMPRA → VENDA e quórum completo) a votos hipotéticos de 5–30
  analistas, sem rede.

## API

Somente leitura, sem parâmetros extras, mesmas proteções de Host/Origin:

| Endpoint | Mudança |
|---|---|
| `GET /api/forward/history` | + `vote_counts`, `technical_outcome`, `target_weight`, `final_decision` por sessão |
| `GET /api/forward/decision` | + rótulos/posição/analistas por evidência, `divergences`, `committee`, `flow`, `order`, `intent_weight`, `retry_count`/`error_type` por analista |
| `GET /api/forward/portfolios` | + `cash`, `pnl`, `observations`, `max_drawdown`, `dividends`; operações com `decision_session`, `asset`, `equity_after` |
| `GET /api/forward/agents` | **novo**: catálogo de 32 posições e observabilidade a partir de `llm_trace.jsonl` e `decision.json` |

Nenhum endpoint POST foi adicionado ou alterado. O catálogo lê apenas campos
selecionados do trace (status, retries, tentativas, duração, tokens, seed,
saída validada); prompts, respostas cruas, `provider.sqlite` e
`provider_journal.jsonl` nunca são lidos nem enviados.

## Dividendos e proventos — metodologia antes de contabilizar

Hoje o ledger usa preços ajustados (COTAHIST × fator yfinance). Quando uma nova
vintage incorpora um provento, o runner reescala as unidades
(`units *= close_antigo / close_novo`), preservando o valor marcado. O provento
já está, portanto, embutido no retorno total. A interface mostra
"Proventos ainda não contabilizados" e não exibe valores.

Contabilização individual exigiria, antes de qualquer código:

1. Fonte oficial de eventos (B3: tipo, data-com/ex, data de pagamento, valor por
   ação), com hash e data de obtenção.
2. Escolher **um** método para todas as carteiras: preços ajustados sem crédito
   em caixa (atual) **ou** preços brutos com crédito em caixa na data de
   pagamento (provisão na data-ex). Nunca os dois — isso duplicaria o provento.
3. Tributação: JCP com retenção na fonte; dividendos isentos sob a regra vigente.
4. Nova identidade de ledger e início comum para as quatro carteiras; nada é
   recalculado retroativamente nos ledgers atuais.

## Supervisão humana

Especificação futura em [H2_V6_HUMAN_SUPERVISION_SPEC.md](H2_V6_HUMAN_SUPERVISION_SPEC.md).
Nenhuma aprovação foi implementada; o runner não foi alterado.

## Verificação

```powershell
.venv/Scripts/python.exe -B -m pytest tests/test_h2_forward_dashboard.py tests/test_h2_dashboard_async.py tests/test_h2_dashboard_analysis.py tests/test_h2_v6_forward.py tests/test_generate_dashboard_data.py -q -p no:cacheprovider
.venv/Scripts/python.exe -B scripts/check_h2_forward_dashboard.py
.venv/Scripts/python.exe -B dashboard/server.py 8083   # abrir http://127.0.0.1:8083/paper
```

Novos testes em `tests/test_h2_forward_dashboard.py`: fluxo/consenso/estados de
ordem (pendente, executada, LATE, FAILED), analistas ausentes e inválidos sem
consenso, métricas de carteira com 1 e 3 fechamentos (intenção 100% com
exposição 0%), catálogo de 32 posições, leitura sem rede (socket bloqueado),
`/api/forward/agents` somente GET, e o harness Node do `paper.js` real agora
também verifica a regra do simulador de quórum sem requisições.

Navegador real: Chrome headless via DevTools Protocol (script local, sem
dependências novas) em 1440, 640 e 420 px, nas quatro áreas, com ficha de
carteira (SMA) e de agentes (RM, TA-03). Resultado em
`evidence/h2_premium_ui/browser-checks.json`: zero erros de console, zero
requisições não-GET, nenhum overflow horizontal.

## Classificação das 12 falhas da regressão anterior

Reexecução em árvore Git limpa (commit `3656374`), rede externa bloqueada por
plugin local de socket, chaves Gemini ausentes do ambiente, `--basetemp` fora
do repositório: **1463 passed / 10 failed** em 9 min 13 s. Nenhuma falha envolve
o dashboard; nenhum teste, evidência ou módulo inventariado foi alterado.

| # | Teste | Classe | Evidência |
|---|---|---|---|
| 1–7 | `tests/pipeline/test_flows.py::TestPipelineFlow::*` (7) | Dependência de ambiente | `psycopg2.OperationalError`: PostgreSQL ausente em `127.0.0.1:5435` |
| 8 | `test_spec.py::test_registry_cobre_os_cinco_classicos_e_o_participante_llm` | Expectativa histórica desatualizada | O registry ganhou `sma_regime_h2_proposed` e `bollinger_state_h2_proposed` (commits `37f705c`/`286f160`, 08–09/10); o teste é de 04/10 |
| 9 | `test_v6_phase_routing.py::test_structural_failure_prevents_phase_selection_and_progression` | Expectativa histórica desatualizada | Espera ausência de PASS de `defect`; `docs/evidence/h2_v6/defect_hardening_20261008T015051Z/manifest.json` foi commitado em 08/10, depois do teste (07/10) |
| 10 | `test_cal_b4_safety.py::test_v5_development_s3_failure_blocks_further_phases` | Expectativa histórica desatualizada | A fase continua recusada com `ValueError`, mas por um gate anterior (`require_sessions`: "CAL-B4 must stay sealed during v5 development") antes da mensagem esperada de S3. A propriedade de segurança se mantém; só a mensagem difere |
| 11 | `test_h2_v6_provisional.py::test_oa1_validation_seal_and_dashboard` | Fixture/ambiente (basetemp) | Passa com basetemp fora do repositório. Com `--basetemp=./data/...` falha em `h2_evaluation_offline.py:100`: "offline artifacts may not use reserved data/evidence roots" — o guard funciona como projetado |
| 12 | `test_snapshot.py::test_manifest_adulterado_e_rejeitado[code]` | Fixture incorreta | Passa fora do repositório. Com basetemp dentro da worktree limpa, a mutação grava `git_dirty=false`, valor que já vigorava, e o manifesto não muda ("a mutação precisa alterar o manifest"). A mutação deveria inverter o valor observado |

Regressão real introduzida pelo dashboard: **nenhuma**. Casos inconclusivos:
nenhum. As falhas 8–12 pertencem a módulos científicos/inventariados e ficam
documentadas, sem reparo nesta entrega.

Reprodução:

```powershell
# suíte completa; basetemp fora do repositório
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --basetemp=$env:TEMP/hfl_full -rf
# as duas sensíveis ao basetemp: passam acima, falham com basetemp em data/
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --basetemp=./data/forward/premium_ui_repro "tests/experiments/test_h2_v6_provisional.py::test_oa1_validation_seal_and_dashboard" "tests/pipeline/test_snapshot.py::test_manifest_adulterado_e_rejeitado"
```

Observação: o comando de regressão focada da entrega anterior usava
`--basetemp=./data/forward/dashboard_checks`; isso basta para provocar 11 e 12
quando os testes científicos entram na mesma execução. Os comandos acima usam
um diretório temporário externo.

## Integridade

`scripts/check_h2_forward_dashboard.py`: **265 hashes protegidos inalterados**,
incluindo `decision.json`, trace, journal, `provider.sqlite` e `state.json` da
sessão de 09/10/2026. Nenhum arquivo do inventário mudou, logo não houve
reconciliação de inventário. Arquivos alterados: `dashboard/forward_api.py`,
`dashboard/server.py` (uma rota GET), `dashboard/paper.{html,css,js}`,
`tests/test_h2_forward_dashboard.py` e documentação. Nenhuma chamada ao Gemini,
nenhuma execução de Validation/Final Test, nenhum POST durante a verificação.

## Capturas (Chrome headless, dados reais de 09/10/2026)

| Área | 1440 px | 640 px | 420 px |
|---|---|---|---|
| Visão Geral | [overview-1440](evidence/h2_premium_ui/paper-overview-1440.jpg) | [overview-640](evidence/h2_premium_ui/paper-overview-640.jpg) | [overview-420](evidence/h2_premium_ui/paper-overview-420.jpg) |
| Sala de Decisão | [room-1440](evidence/h2_premium_ui/paper-room-1440.jpg) | [room-640](evidence/h2_premium_ui/paper-room-640.jpg) | [room-420](evidence/h2_premium_ui/paper-room-420.jpg) |
| Carteiras | [wallets-1440](evidence/h2_premium_ui/paper-wallets-1440.jpg) | [wallets-640](evidence/h2_premium_ui/paper-wallets-640.jpg) | [wallets-420](evidence/h2_premium_ui/paper-wallets-420.jpg) |
| Agentes | [agents-1440](evidence/h2_premium_ui/paper-agents-1440.jpg) | [agents-640](evidence/h2_premium_ui/paper-agents-640.jpg) | [agents-420](evidence/h2_premium_ui/paper-agents-420.jpg) |

Detalhes: [carteira SMA](evidence/h2_premium_ui/paper-wallet-detail-sma-1440.jpg),
[ficha do Risk Manager](evidence/h2_premium_ui/paper-agent-detail-rm-1440.jpg),
[ficha do TA-03 em 420 px](evidence/h2_premium_ui/paper-agent-detail-ta3-420.jpg),
recortes em 420 px do [comitê](evidence/h2_premium_ui/crop-committee-420.jpg),
da [composição](evidence/h2_premium_ui/crop-composition-420.jpg) e do
[perfil](evidence/h2_premium_ui/crop-profile-420.jpg).
