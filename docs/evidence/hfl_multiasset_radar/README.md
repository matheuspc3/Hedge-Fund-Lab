# HFL PREMIUM V4 — MULTIASSET RADAR READY

Qualificado em 11/10/2026, sem Gemini real e sem ordens multiativos.
Implementação local: `e5e44fc`.

- **138 testes passaram** na regressão final, incluindo os 16 checks do radar.
  [Saída da regressão](regression_tests.txt) e [checks offline](offline_tests.txt).
- Chrome em **1440, 640 e 420 px**, sem transbordamento da página. A tabela
  usa rolagem horizontal própria. Cadastro, remoção, ticker inválido, seleção
  zero/um/cinco, preparação, preflight, confirmação sintética, resultado,
  Sala de Decisão e bloqueio entre sessões diferentes foram exercitados.
  [Registro](chrome_checks.json), [1440](radar-1440.png), [640](radar-640.png),
  [420](radar-420.png), [sala](decision-420.png),
  [comparação bloqueada](comparison-blocked-420.png).
- **10.766 arquivos protegidos conferidos**, zero alterações no baseline,
  manifesto H2 original verificado com suas **73 fontes**. Logs HTTP voláteis
  e locks ficam fora do baseline; nenhum ledger foi excluído.
  [Baseline](preservation_baseline.json) e [verificação](verification.json).
- Exemplo: cinco empresas na sessão 09/10/2026, mais um histórico de VALE3
  em 08/10 para testar a comparação. **Seis comitês completos, 36 chamadas
  ao transporte falso, custo US$ 0**. Dados sintéticos, sem recomendação.
  [Resultados](synthetic_results.json) e [arquivo completo](synthetic_example.zip).
- Estimativa declarada para cinco ativos oficiais: **US$ 0,14625**, com
  **US$ 3,31776** de reserva conservadora e limite cumulativo de US$ 5 por
  raiz. Tarifas e hipóteses no [guia](../../HFL_PREMIUM_V4_RADAR.md).

O ZIP contém entradas congeladas, CSVs, claims, journals SQLite e exportados,
eventos, resultados selados e configuração. Para consultar uma cópia:

```powershell
Expand-Archive docs/evidence/hfl_multiasset_radar/synthetic_example.zip data/radar/demo-restored
$env:HFL_RADAR_ROOT = 'data/radar/demo-restored'
.venv/Scripts/python.exe dashboard/server.py 8087
```

Abrir `http://localhost:8087/radar` não chama agentes. O ZIP pode ser verificado
pelo SHA256 registrado em `verification.json`. Não reexecutar inferência sobre
esses claims; consultas e replay são offline.

Arquivos da implementação: `.gitignore`, `README.md`, `dashboard/server.py`,
`dashboard/paper.html`, `dashboard/radar_api.py`, `dashboard/radar.html`,
`dashboard/radar.css`, `dashboard/radar.js`, `scripts/multiasset_radar.py`,
`scripts/run_multiasset_radar.py`, `tests/test_multiasset_radar.py`,
`docs/HFL_PREMIUM_V4_RADAR.md` e `docs/HFL_MULTIASSET_PORTFOLIO_DESIGN.md`.
Esta pasta reúne as evidências adicionais. Nenhuma dependência nova; nenhum
arquivo de `src` ou inventário científico alterado; nenhum push.

O Risk do radar é consultivo e específico do ativo. Risco dependente da
carteira permanece não avaliado. A execução real e a validação de fontes
externas não foram exercitadas; preparação oficial reutiliza os guards B3
existentes, testados offline. O gestor global está somente especificado.

```powershell
git log -2 --oneline
git status --short
```
