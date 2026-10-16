# Hedge-Fund-Lab — Premium V2: supervisão humana em paper trading

Carteira **H2 v6 Supervisionada** (`h2_v6_supervised`): o operador aprova ou
rejeita a recomendação já gravada pelos agentes, define limites e acompanha a
ordem virtual até a reconciliação com a abertura oficial. O contrato técnico
completo está em [H2_V6_HUMAN_SUPERVISION_SPEC.md](H2_V6_HUMAN_SUPERVISION_SPEC.md)
(revisão 2). Nada aqui envia ordens reais, chama o Gemini ou altera a H2 v6 original.

## Entrega por fases

| Fase | Commit | Conteúdo |
|---|---|---|
| A — contrato e ledger | `a8d964e` | especificação revisada; `scripts/run_h2_v6_supervised.py`; 30 testes offline |
| B — integração operacional | `787e968` | `GET /api/forward/supervision`, `POST …/approve·reject·cancel·sync`; teste HTTP |
| C — interface Premium | `b42799a`, `d33b096` | painel Supervisão Humana, quinta carteira, histórico e linha do tempo |

Cada fase só avançou com testes verdes e `check_h2_forward_dashboard.py` íntegro.

## Datas de início efetivas

Todas começam no fechamento de **09/10/2026**, em caixa, com R$ 100.000, mesmos
custos (spread 5 bps + 0,032%), execução fracionária e manifesto.

| Carteira | Inicialização registrada | Primeira ordem possível |
|---|---|---|
| IA H2 v6 original | decisão gravada em 10/10/2026 15:17 | abertura de 13/10/2026 |
| Buy & Hold | sombra do ledger original | abertura de 13/10/2026 |
| SMA Regime 50/200 | 10/10/2026 16:42 | abertura de 13/10/2026 |
| Bollinger Estado 20/2 | 10/10/2026 16:42 | sem ordem (alvo 0) |
| **H2 v6 Supervisionada** | **10/10/2026 21:02** (`sync` real, antes do prazo) | abertura de 13/10/2026, **se aprovada** |

A inicialização ainda era legítima: o ledger original tinha só o fechamento de
início e a abertura-alvo (13/10 10:00) estava no futuro. A proposta de 09/10
(COMPRA, alvo 100%, `ACTION_BUY`, decisão `27e51c94…`) está
**AGUARDANDO_APROVACAO** até 13/10/2026 10:00. Nenhuma aprovação foi feita em
nome do operador. Sem decisão até o prazo, ela vira `EXPIRADA` e a carteira
supervisionada continua em caixa.

## Operação diária

```text
fechamento S   prepare → preflight → run (H2 original, pago, confirmado)
               → Sincronizar SMA e Bollinger → Sincronizar carteira supervisionada
até 10:00 T    Sala de Decisão → Supervisão Humana: aprovar (com limites) ou rejeitar
fechamento T   prepare (congela a barra bruta oficial de T) → run → Sincronizar supervisionada
               ⇒ a ordem de S é reconciliada na abertura oficial de T
```

A sincronização supervisionada é gratuita e determinística, como a dos
benchmarks; usa o mesmo lock de operações e, como eles, exige Git limpo para a
identidade do manifesto. Se a sessão T não for preparada, a abertura bruta vem
do COTAHIST em cache somente quando o SHA256 dele coincide com o registrado no
`input.json` mais recente; senão a ordem fica `BLOQUEADA_BASE_PRECOS`.

## Endpoints

| Método | Endpoint | Efeito |
|---|---|---|
| GET | `/api/forward/supervision[?session=S]` | propostas, estado derivado no backend, ações, resultados, linha do tempo, auditoria |
| POST | `/api/forward/supervision/approve` | `{confirm, decision_session, decision_sha256, limits}` → 201 |
| POST | `/api/forward/supervision/reject` | `{confirm, decision_session, decision_sha256}` → 201 |
| POST | `/api/forward/supervision/cancel` | idem; só antes do prazo e após aprovação |
| POST | `/api/forward/supervision/sync` | `{}` → job 202 |

Mesmas proteções dos POST existentes: loopback, Host exato, Origin igual, CSRF,
JSON ≤ 4096 bytes sem duplicatas nem não finitos e campos exatos por comando.
Conflitos de estado retornam 409 com código (`deadline_passed`,
`decision_hash_mismatch`, `duplicate_action`, `invalid_transition:…`); limites
inválidos retornam 400 com o campo (`invalid_limit:max_buy_price`). A aprovação
não autoriza inferência: o teste HTTP substitui os caminhos do modelo por
falhas e nenhum é alcançado.

## Interface

- **Sala de Decisão:** painel Supervisão Humana logo após o fluxo dos agentes,
  com recomendação original, decisão do operador, limites, condições
  pendentes, status da ordem e resultado da reconciliação (abertura bruta,
  ajustada, origem e gap). Formulário de limites com prévia informativa que não
  supõe preço futuro. Confirmação própria, separada da autorização paga do
  Gemini. Cancelamento só enquanto a aprovação for cancelável.
- **Visão Geral:** quinta ficha com patrimônio, retorno, caixa, PETR4,
  exposição, custos e última operação; o selo "Aguardando aprovação" distingue
  proposta de ordem.
- **Carteiras:** comparação das cinco; para a supervisionada, contagem de
  aprovadas, rejeitadas e não executadas, tabela de decisões e linha do tempo
  intervenção × patrimônio. A diferença em relação à original é descritiva, sem
  afirmação causal.
- **Agentes:** inalterado (32 posições, parâmetros congelados).

## Limitações declaradas

- Risk Manager e `BUY_AT_TARGET_NOOP` avaliaram a carteira original; com
  posições divergentes, a supervisionada não reinterpreta vetos.
- O servidor é local e não autentica pessoas; o registro não identifica o operador.
- `state.json` supervisionado reaproveita `fwd.new_state`, que inclui um livro
  B&H sombra sem uso aqui; a carteira B&H exibida continua vindo do ledger original.
- Aprovar exige que a proposta tenha sido sincronizada antes do prazo; sessões
  sem sincronização viram `SEM_DECISAO` e nunca são oferecidas retroativamente.

## Verificação

```powershell
.venv/Scripts/python.exe -B -m pytest tests/test_h2_v6_supervised.py tests/test_h2_forward_dashboard.py tests/test_h2_dashboard_async.py tests/test_h2_dashboard_analysis.py tests/test_h2_v6_forward.py tests/test_generate_dashboard_data.py -q -p no:cacheprovider --basetemp=$env:TEMP/hfl_focus
.venv/Scripts/python.exe -B scripts/run_h2_v6_supervised.py verify
.venv/Scripts/python.exe -B scripts/check_h2_forward_dashboard.py
```

### Resultados

- `tests/test_h2_v6_supervised.py`: **31 passed** (ledger offline + HTTP), cobrindo
  aprovação válida, rejeição, expiração, aprovação após a abertura, hash adulterado,
  aprovação duplicada, cancelamento, concentração 80%, volatilidade, compra acima
  do limite, venda abaixo do limite, gap de alta e de baixa, bases bruto/ajustado
  divergentes, limite aplicado ao bruto e não ao ajustado, posições divergentes,
  COMPRA/VENDA/MANTER, veto, `BUY_AT_TARGET_NOOP`, FAILED/MISSED/LATE, sem ordem
  necessária, sincronização pulada, quedas entre registro, journal, liquidação e
  ledger, cauda de journal truncada, execução única, adulteração da cadeia,
  isolamento do Forward Test original e segurança dos endpoints.
- Harness Node do `paper.js` real: o diálogo de supervisão não envia nada sem
  checkbox, dois cliques geram um único POST, e nunca para `/run`.
- Regressão focada: **77 passed** (`test_h2_v6_supervised`, `test_h2_forward_dashboard`,
  `test_h2_dashboard_async`, `test_h2_dashboard_analysis`, `test_h2_v6_forward`,
  `test_generate_dashboard_data`). Ruff e `node --check` aprovados.
- Suíte completa, árvore limpa em `d33b096`, rede externa bloqueada, chaves Gemini
  ausentes: **1494 passed / 10 failed**. As 10 são exatamente as falhas conhecidas
  e classificadas em [H2_V6_PREMIUM_UI.md](H2_V6_PREMIUM_UI.md): 7 por PostgreSQL
  ausente em 5435 e 3 por expectativa histórica desatualizada. **Nenhuma regressão nova.**
  Nenhum teste existente foi alterado para passar; o harness Node ganhou asserções.
- Integridade: `check_h2_forward_dashboard.py` → **265 hashes protegidos
  inalterados** antes e depois de cada fase e da inicialização real. Os
  arquivos de `data/forward/h2_v6_paper` e `h2_v6_benchmarks` foram comparados
  byte a byte antes/depois do `sync` real: idênticos.
- `run_h2_v6_supervised.py verify` no ledger real: cadeia íntegra (1 evento, `PROPOSED`).

### Navegador

Chrome headless via DevTools Protocol, 1440/640/420 px, sem dependências novas.

- **Dados reais** (somente GET; nenhuma ação executada):
  [visão geral](evidence/h2_premium_v2/real-overview-1440.jpg) ·
  [640](evidence/h2_premium_v2/real-overview-640.jpg) ·
  [420](evidence/h2_premium_v2/real-overview-420.jpg),
  [Sala](evidence/h2_premium_v2/real-room-1440.jpg),
  painel de supervisão [1440](evidence/h2_premium_v2/real-supervision-1440.jpg) ·
  [640](evidence/h2_premium_v2/real-supervision-640.jpg) ·
  [420](evidence/h2_premium_v2/real-supervision-420.jpg),
  carteira supervisionada [1440](evidence/h2_premium_v2/real-wallets-supervised-1440.jpg) ·
  [420](evidence/h2_premium_v2/real-wallets-supervised-420.jpg),
  [Agentes](evidence/h2_premium_v2/real-agents-1440.jpg).
  Zero erros de console, zero requisições não-GET, nenhum overflow horizontal
  (`real-browser-checks.json`).
- **Mundo sintético** (fixture de teste em pasta temporária, decisões modeladas
  sobre o registro de 09/10, nunca em `data/`), para estados que o ledger real
  ainda não tem: [execução com concentração 80%](evidence/h2_premium_v2/synthetic-supervision-1440.jpg),
  [venda não executada por limite](evidence/h2_premium_v2/synthetic-supervision-not-executed-1440.jpg),
  [diálogo de aprovação](evidence/h2_premium_v2/synthetic-approval-dialog-1440.jpg),
  [após aprovar](evidence/h2_premium_v2/synthetic-supervision-approved-1440.jpg),
  [linha do tempo e divergência](evidence/h2_premium_v2/synthetic-wallets-supervised-1440.jpg),
  [cinco carteiras com curva](evidence/h2_premium_v2/synthetic-overview-1440.jpg),
  [painel em 420 px](evidence/h2_premium_v2/synthetic-supervision-420.jpg).
  O fluxo ponta a ponta no navegador abriu o diálogo com envio desabilitado,
  fez zero POST antes da confirmação, exatamente um POST para
  `/supervision/approve` depois dela, e terminou em `APROVADA`
  (`synthetic-browser-checks.json`). Textos de agentes nessas capturas são
  cópias do registro real e não correspondem às decisões sintéticas.
