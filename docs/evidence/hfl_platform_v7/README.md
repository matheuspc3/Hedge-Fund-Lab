# HFL PREMIUM V7 — UNIFIED PLATFORM & OPERATIONAL READINESS

Entrega local qualificada em 11/10/2026, sobre o commit V6 `e54883d`, sem push.
Servidor da entrega: **http://localhost:8090/**. Todos os módulos usam esse
mesmo processo/origem; o comando para reiniciar está no runbook.

## Mapa da entrega

| Item solicitado | Implementação / evidência |
| --- | --- |
| Auditoria antes do código | [Inventário e matriz de consolidação](../../HFL_PLATFORM_AUDIT_V7.md) |
| Arquitetura de informação | [Arquitetura, rotas, runners, fontes e identidades](../../HFL_PLATFORM_ARCHITECTURE.md) |
| Plataforma e padrões compartilhados | Shell com quatro grupos, breadcrumbs, fonte identificada, navegação móvel, foco e tabelas acessíveis |
| Landing operacional | Cinco carteiras independentes, última decisão, supervisão, calendário, alertas e jobs |
| Radar → Global PM | Seleção/fonte/sessão transferidas; preparo hipotético explícito, Risk, preflight e autorização global própria |
| Prontidão de 13/10 | [Diagnóstico read-only](readiness.json), [auditoria supervisionada](supervision.json) |
| Runbook | [Rotina operacional e recuperação](../../HFL_OPERATIONS_RUNBOOK.md) |
| Testes | [Regressão final](regression-release.txt), [Ruff](ruff.txt), [sintaxe JS](javascript.json) |
| Navegador real | [Métricas Chrome e teclado](browser-checks.json), capturas abaixo |
| Preservação | [Baseline prévio](preservation_baseline.json), [verificação final](integrity.json) |
| Fluxo sintético | [Prova pública do registro criado](synthetic-flow.json) |
| Arquivos e commits | [Arquivos alterados](changed-files.txt), [identidade e Git após o commit de implementação](repository-check.json) |

## Resultado da qualificação

- **229 testes e 31 subtestes aprovados**, offline, em 239,98 segundos.
- Ruff aprovado e nove arquivos JavaScript com sintaxe válida.
- **11.094 arquivos protegidos sem alteração**, incluindo 66 arquivos de `src/`,
  fontes congeladas, decisões, claims, ledgers, implementações e evidências V4–V6.
- Decisão de 09/10 preservada:
  `27e51c949aebac155b1d890c6fff74d1a242852d7f5c8d3a30cdc602a6a09ddc`.
- Chrome a 1440, 640 e 420 px: navegação, menus, tabelas e gráficos; sem overflow
  horizontal persistente e sem erros de console. Menu abre com Enter e fecha
  com Escape, devolvendo o foco. Tabelas dinâmicas são focáveis.
- Seis abas H2 mantidas; URLs anteriores, catálogo de 30 Technical slots
  (5 ativos e 25 livres), Risk e Portfolio preservados.
- Testados Host/Origin/CSRF, headers/chaves duplicados, tamanho, JSON exato,
  orçamento, fonte/sessão, token obsoleto, consentimento, duplicidade, jobs,
  recuperação sem nova inferência, consultas sem escrita e proteção Final Test.
- Nenhuma chamada Gemini, execução Validation/Final Test, aprovação humana,
  reconciliação ou operação financeira foi feita nesta entrega.

O percurso real no navegador foi Radar sintético V4 → seleção de cinco
pareceres de 09/10 → snapshot hipotético → preflight → confirmação **fake**
separada → proposta válida E, 100% caixa, **US$ 0 e zero operações**. O registro
novo e seus claims/journal permanecem locais. Nenhum exemplo A–F ou registro
anterior foi sobrescrito. A demonstração não representa inferência Gemini.

Os relatórios `regression.txt`, `regression-final.txt` e `platform-recheck.txt`
registram etapas anteriores; `regression-release.txt` é a rodada definitiva.

## Capturas

| Área | Desktop 1440 | Tablet 640 | Mobile 420 |
| --- | --- | --- | --- |
| Visão Geral | [Abrir](landing-1440.jpg) | [Abrir](landing-640.jpg) | [Abrir](landing-420.jpg) |
| Cinco carteiras | [Abrir](landing-wallets-1440.jpg) | — | [Abrir](landing-wallets-420.jpg) |
| Sala de decisão | [Abrir](decision-1440.jpg) | [Abrir](decision-640.jpg) | [Abrir](decision-420.jpg) |
| Radar | [Abrir](radar-1440.jpg) | [Abrir](radar-640.jpg) | [Abrir](radar-420.jpg) |
| Gestor Global | [Abrir](global-workflow-1440.jpg) | [Abrir](global-workflow-640.jpg) | [Abrir](global-workflow-420.jpg) |
| Resultado global | [Abrir](global-result-1440.jpg) | [Abrir](global-result-640.jpg) | [Abrir](global-result-420.jpg) |
| Pesquisa H2 | [Abrir](h2-1440.jpg) | [Abrir](h2-640.jpg) | [Abrir](h2-420.jpg) |
| Legado | [Abrir](legacy-1440.jpg) | [Abrir](legacy-640.jpg) | [Gráficos](legacy-analysis-420.jpg) |
| Logs | [Abrir](logs-1440.jpg) | [Abrir](logs-640.jpg) | [Abrir](logs-420.jpg) |

Detalhes: [consentimento fake inicialmente desmarcado](global-confirmation-1440.jpg),
[bloqueio oficial por pareceres ausentes](global-official-420.jpg),
[supervisão](supervision-420.jpg), [catálogo](agents-420.jpg),
[H2 governança](h2-audit-420.jpg), [H2 multiagente](h2-agents-420.jpg).

## Reproduzir as verificações

Na raiz do projeto, PowerShell, com o ambiente já instalado:

```powershell
.venv/Scripts/python.exe -B scripts/check_platform.py
.venv/Scripts/python.exe -B scripts/run_h2_v6_supervised.py verify
.venv/Scripts/python.exe -m ruff check dashboard/server.py dashboard/platform_api.py scripts/check_platform.py tests/test_platform_v7.py tests/test_platform_ui.py tests/test_h2_dashboard_async.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_platform_v7.py tests/test_platform_ui.py tests/test_global_pm.py tests/test_multiasset_portfolio.py tests/test_multiasset_radar.py tests/test_h2_v6_forward.py tests/test_h2_v6_supervised.py tests/test_h2_premium_v3.py tests/test_h2_forward_dashboard.py tests/test_h2_dashboard_async.py tests/test_h2_dashboard_analysis.py tests/agents/test_gemini_client.py tests/pipeline/test_b3_official.py --basetemp=data/platform/regression-v7-release
Get-ChildItem dashboard/*.js | ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE) { throw 'JavaScript inválido' } }
```

Conferência de todos os hashes V7, somente leitura:

```powershell
@'
import hashlib, json
from pathlib import Path
root = Path.cwd()
baseline = json.loads((root / 'docs/evidence/hfl_platform_v7/preservation_baseline.json').read_text(encoding='utf-8'))
changed = [name for name, sha in baseline.items() if not (root / name).is_file() or hashlib.sha256((root / name).read_bytes()).hexdigest() != sha]
assert not changed, changed
print(f'{len(baseline)} arquivos protegidos: OK')
'@ | .venv/Scripts/python.exe -B -
```

## Pendências reais

Os cinco pareceres oficiais estão ausentes/incompletos. ITUB4 mantém bloqueio
de consistência entre fontes (fator/split). Resolver inputs e autorizar o lote
Radar precede qualquer proposta oficial; a autorização Global PM é outra.
O contexto global dura 24 horas e não se renova automaticamente.

A supervisionada aguarda decisão humana até **13/10 às 10h BRT**; nenhuma
aprovação foi criada. H2, Buy & Hold e SMA têm intenções para essa abertura,
sem execução observada. Calendário não confirma leilão; não há preço
intradiário no diagnóstico. As cinco carteiras têm R$ 100 mil cada e não
devem ser somadas como uma carteira compartilhada.

A governança científica permanece provisória/não ratificada, com Final Test
bloqueado conforme a autoridade original. Limites multiativos são didáticos,
o gestor é consultivo, o servidor é local e não há scheduler, migração de
stack, novos agentes ou execução financeira multiativos habilitada.
