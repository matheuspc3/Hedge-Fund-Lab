# Premium V6 — evidências da qualificação offline

**HFL PREMIUM V6 — AI GLOBAL PORTFOLIO MANAGER QUALIFIED OFFLINE**

Identidade `HFL-MULTIASSET-GLOBAL-PM-V1`. Qualificação em 11/10/2026,
exclusivamente com `FakeGlobalPortfolioManager`, sem chamada real Gemini,
sem operação prospectiva e sem escrita em carteira. Não houve push.

Arquitetura, adapter, fronteira matemática com V5, política, limitações e
comandos futuros: [guia V6](../../HFL_PREMIUM_V6_GLOBAL_PM.md).

## Resultado

- **206 testes + 2 subtests passaram** em 364,17 s; 39 testes novos.
- Ruff e formatação: cinco arquivos Python aprovados. Sintaxe dos dois JS
  aprovada. `git diff --check` aprovado.
- **11.027 arquivos protegidos** conferidos por SHA-256: nenhuma alteração.
  Manifesto original e 73 fontes congeladas preservados. O gate com Git limpo
  passou após o commit local `ad64764` de implementação. Um segundo commit
  local registra essa verificação; nenhum código foi alterado nessa etapa.
- V5 preservada: 22 eventos, cadeia íntegra. A–E V6 válidos; F rejeitado por
  pesos somando 120%. Todas as propostas têm `portfolio_changed=false`.
- Chrome: cenários A–F, venda/recebíveis, rotação condicionada, não operação,
  rejeição e seleção de fonte inspecionados; console sem warnings/errors.
  Sem overflow horizontal da página em 1440, 640 e 420 px. Tabelas têm rolagem própria.
- Cinco pareceres oficiais ausentes permanecem ausentes; cinco sintéticos
  elegíveis somente na seleção sintética explícita. Prévia não chama agentes.

## Artefatos

| Artefato | Conteúdo |
|---|---|
| [verification_final.json](verification_final.json) | Hashes, resultados, integridade, Git e limitações |
| [contracts.json](contracts.json) | Prompt integral versionado, JSON Schema, configuração, políticas e selos |
| [demo-qualified-v6.zip](demo-qualified-v6.zip) | Índice A–F, seis contextos/snapshots/resultados, autorizações, reservas e journals falsos privados |
| [preservation_baseline.json](preservation_baseline.json) | Inventário anterior à implementação, 11.027 hashes |
| [regression_final.txt](regression_final.txt) | Regressão final completa, 206 testes |
| [recovery_checks.txt](recovery_checks.txt) | Checks adicionais de recuperação, orçamento, adulteração e falha incerta |
| [offline_tests_initial.txt](offline_tests_initial.txt) | Primeira execução, 35 testes; antecede as quatro extensões finais |
| [demo_generation.txt](demo_generation.txt) | Geração qualificada A–F, sem inferência real |
| [static_checks.txt](static_checks.txt) | Comandos e resultados das verificações estáticas |
| [browser_checks.json](browser_checks.json) | Observações da UI, medidas responsivas e prévias de custo |

O ZIP contém **somente dados sintéticos novos V6**. Journals não são servidos
pela API. Guardar o pacote localmente; não há exportação de chaves nem envio
a serviço externo. Selos dependem dos bytes das fontes locais: mudanças futuras
exigem novos contextos, sem atualizar estes exemplos retrospectivamente.

## Capturas

| Largura | Capturas Chrome |
|---|---|
| 1440 | [Resumo](chrome_1440.jpg), [alocações e tabela](chrome_1440_allocations.jpg) |
| 640 | [Resumo responsivo](chrome_640.jpg) |
| 420 | [Resumo mobile](chrome_420.jpg), [alocações](chrome_420_allocations.jpg) |
| Rejeição F | [Estado bloqueado](chrome_rejected_F.jpg) |

## Reprodução offline

Na raiz do projeto, com as dependências existentes:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_global_pm.py tests/test_multiasset_portfolio.py tests/test_multiasset_radar.py tests/test_h2_v6_forward.py tests/test_h2_v6_supervised.py tests/test_h2_premium_v3.py tests/test_h2_forward_dashboard.py tests/agents/test_gemini_client.py tests/pipeline/test_b3_official.py --basetemp=data/global_pm/regression-recheck-<novo-id>
.venv/Scripts/python.exe -m ruff check scripts/multiasset_global_pm.py scripts/run_global_pm.py dashboard/global_pm_api.py dashboard/server.py tests/test_global_pm.py
.venv/Scripts/python.exe -m ruff format --check scripts/multiasset_global_pm.py scripts/run_global_pm.py dashboard/global_pm_api.py dashboard/server.py tests/test_global_pm.py
node --check dashboard/global-pm.js
node --check dashboard/portfolio.js
git diff --check
.venv/Scripts/python.exe scripts/run_global_pm.py status --root data/global_pm/hfl_global_pm_v1/demo-qualified-v6-a
.venv/Scripts/python.exe scripts/run_global_pm.py replay --root data/global_pm/hfl_global_pm_v1/demo-qualified-v6-a
.venv/Scripts/python.exe dashboard/server.py 8089
```

Painel: `http://localhost:8089/portfolio`. Para regenerar fixtures, usar **outro**
ID com `demo --root data/global_pm/hfl_global_pm_v1/demo-<novo-id>`.
Não sobrescrever exemplos selados. Os testes usam raízes temporárias próprias,
proíbem rede externa e permitem somente o servidor HTTP de loopback no check local.

## Limites da conclusão

Contratos, finanças determinísticas, replay e consulta foram qualificados;
inferência real e qualidade preditiva não foram avaliadas. Limites V5 continuam
didáticos; custos/impostos/slippage, calendário vigente, custódia/autenticação,
política de alocação, revisão factual da prosa e qualquer piloto prospectivo
precisam de fases próprias. Nenhuma proposta ou autorização de custo habilita
execução financeira.
