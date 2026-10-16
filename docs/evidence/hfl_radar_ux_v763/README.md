# HFL Premium V7.6.3 — Mercado e Radar

Entrega de apresentação de `HFL-UX-001`, em 13/10/2026. Base: branch
`#1-Update`, commit `a5c07fb`. No início, somente `out.json` estava não
rastreado; esse arquivo pertence ao operador e não entra nos commits.

## Implementação

- `/market`: exploração do universo registrado, seleção de execução/ativo,
  indicadores e pareceres. O cartão do Início e a área Mercado abrem essa página.
- `/radar`: Universo → Comitês → Consenso → Risk → Resultado; comparação,
  filtros locais, detalhe progressivo, histórico e operações separados.
- Resumo/detalhe reutilizados nas duas páginas (`HFLMarket`).
- Confirmação de custo compartilhada (`HFL.confirmCost`), integrada ao botão
  existente do Radar com os mesmos campos de autorização e token de preflight.
- Glossário único ampliado com SMA50, SMA200, sessão e parecer oficial.
- Auditoria do V1, sem implementar sua alteração operacional no servidor.

Os resultados vêm das APIs existentes, que verificam os arquivos primários.
`official_results.json` registra a conferência da recovery-01; não alimenta o
frontend nem serve de fallback. Não houve nova inferência, chamada Gemini,
operação financeira, paper trading, Final Test ou push.

As 18 rotas legadas permanecem; os três aliases HTML de Mercado elevam o
inventário de entradas a 21. APIs de leitura e seus contratos são reutilizados.

## Arquivos de apresentação

Novos: `dashboard/market.html`, `market.js`, `market-ui.js`, `market.css`.
Modificados: `radar.html`, `radar.js`, `platform.html`, `shell.js`, `glossary.js`,
`ui.js`, `design-system.css` e os mapas de páginas/estáticos de `server.py`.
Nenhum handler `/api/*` ou módulo científico foi alterado.

## Evidências

| Assunto | Documento |
|---|---|
| Exploração e fontes | [MARKET_EXPLORER.md](MARKET_EXPLORER.md) |
| Hierarquia do Radar | [RADAR_UX_ARCHITECTURE.md](RADAR_UX_ARCHITECTURE.md) |
| Componentes e adoção | [COMPONENT_CATALOG.md](COMPONENT_CATALOG.md) |
| Indicadores e educação | [INDICATORS_AND_HELP.md](INDICATORS_AND_HELP.md) |
| Custo e autorização | [FINANCIAL_ACTION_DIALOG.md](FINANCIAL_ACTION_DIALOG.md) |
| Encerramento V1 | [V1_BACKEND_CLOSURE_PROPOSAL.md](V1_BACKEND_CLOSURE_PROPOSAL.md) |
| Acessibilidade | [ACCESSIBILITY_REPORT.md](ACCESSIBILITY_REPORT.md) |
| Interações reais | [INTERACTION_TESTS.md](INTERACTION_TESTS.md) |
| Capturas | [VISUAL_REGRESSION.md](VISUAL_REGRESSION.md) |
| Regressão e preservação | [REGRESSION_REPORT.md](REGRESSION_REPORT.md), [PRESERVATION_REPORT.md](PRESERVATION_REPORT.md) |
| Pendências | [NEXT_STEPS.md](NEXT_STEPS.md) |

## Resultado da validação

53/53 interações Chrome; regressão completa final com 1752 aprovados e 14 falhas
preexistentes, sem nova divergência frente ao baseline. Preservação final:
`changes: []`, `violations: []`; V7.5 íntegra e V7.6 com `errors: []`.
Os relatórios registram a primeira tentativa e as correções dos testes de UI.

## Verificação local

```powershell
.venv/Scripts/python.exe -B scripts/serve_dashboard_keyless.py 8105
```

Abrir `http://127.0.0.1:8105/market` e
`http://127.0.0.1:8105/radar?run=radar-2026-10-09-recovery-01`.
O servidor de verificação não carrega a chave Gemini do `.env`. As operações
existentes permanecem protegidas pelo backend; não são necessárias para consultar.

UX-M2 e UX-M4 avançaram; a migração integral dos controles operacionais e das
demais páginas permanece pendente. UX-M5–M8 não foram iniciados nesta entrega.
