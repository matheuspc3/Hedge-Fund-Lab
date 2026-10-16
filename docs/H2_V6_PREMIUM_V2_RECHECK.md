# Premium V2 — revalidação e correções de integridade

Entrega em 10/10/2026, exclusivamente em paper trading.

O Premium V1 e as fases A/B/C do V2 já existiam na árvore limpa em `22c5d84`.
Esta revisão verificou a entrega existente e corrigiu dois problemas na fase A,
sem reimplementar inferência, estratégia, endpoints ou componentes visuais.
O relatório original continua em [H2_V6_PREMIUM_V2.md](H2_V6_PREMIUM_V2.md).

## Correções

1. **Integridade obrigatória antes de operar** (`4a78788`): anteriormente o
   verificador detectava alterações, mas `act`/`sync` não exigiam auditoria
   válida. Agora os dois verificam a cadeia, os registros e os hashes da decisão
   e do input antes de recuperar eventos ausentes ou continuar. Divergências
   retornam `supervision_integrity_failed`, sem alterar o ledger. Uma cauda
   incompleta ainda é recuperável; eventos completos adulterados não são.
2. **Concentração após custos** (`3cff317`): alvo de 80% sobre patrimônio anterior
   aos custos podia resultar em aproximadamente 80,0525% imediatamente após
   comprar. A supervisionada agora dimensiona a compra com os custos congelados
   e sua própria posição na abertura, atingindo o máximo aprovado sobre o
   patrimônio após liquidação. O motor original permanece intacto. O fechamento
   seguinte pode alterar o peso pela variação de preço; não há rebalanceamento
   automático para compensar essa deriva.

A [especificação](H2_V6_HUMAN_SUPERVISION_SPEC.md) está na revisão 3.
Os cinco casos novos falharam antes das respectivas correções e passaram depois.
Nenhum teste existente foi relaxado para passar.

## Arquivos

Alterações desta revisão: `scripts/run_h2_v6_supervised.py`,
`tests/test_h2_v6_supervised.py`, `docs/H2_V6_HUMAN_SUPERVISION_SPEC.md`, este
relatório e evidências em `docs/evidence/h2_premium_v2/recheck/`.

A implementação V2 existente integra `dashboard/forward_api.py`,
`dashboard/forward_jobs.py`, `dashboard/server.py`, `dashboard/paper.html`,
`dashboard/paper.css` e `dashboard/paper.js`. Esses arquivos não precisaram de
mudança nesta revisão. O catálogo de 32 slots continua preservado.

## API e fluxo operacional

| Método | Endpoint | Uso |
|---|---|---|
| GET | `/api/forward/supervision[?session=YYYY-MM-DD]` | Consulta de posição, propostas, intervenções, resultados e auditoria |
| POST | `/api/forward/supervision/approve` | Aprovação explícita, imutável, com limites validados |
| POST | `/api/forward/supervision/reject` | Rejeição explícita, sem nova operação |
| POST | `/api/forward/supervision/cancel` | Novo evento de cancelamento antes do prazo |
| POST | `/api/forward/supervision/sync` | Sincronização determinística e gratuita |

Nenhum endpoint de supervisão chama Gemini. Host/Origin, loopback, CSRF,
JSON estrito, confirmação, locks e idempotência continuam vigentes.

Na Sala de Decisão, consultar a recomendação registrada → preencher limites
opcionais → aprovar ou rejeitar → confirmar no diálogo. Uma aprovação válida
continua cancelável até o prazo; depois fica `PENDENTE_ABERTURA`. A sincronização
posterior verifica a abertura bruta oficial contra preço/gap e liquida na base
ajustada usada pelo Forward Test. Só então aparece execução virtual confirmada,
ou o motivo da não execução. MANTER não vira compra para igualar carteiras.

## Carteira real

`h2_v6_supervised` foi inicializada em **10/10/2026 21:02 BRT**, antes da abertura
de 13/10. A referência inicial comum é o fechamento de **09/10/2026**, com
R$ 100.000 em caixa. A recomendação COMPRA de 09/10 continua
`AGUARDANDO_APROVACAO`, com prazo em **13/10/2026 às 10:00 BRT**.

Nenhuma aprovação, rejeição, cancelamento ou execução foi registrada em nome do
operador. A auditoria real tem um evento `PROPOSED`. A consulta e a verificação
visual usaram somente GET. A instância atualizada está em
`http://localhost:8084/paper`; instâncias anteriores foram preservadas.

## Verificação

Resultados finais e classificação das falhas: ver evidência
[`verification.json`](evidence/h2_premium_v2/recheck/verification.json).

- Supervisão: **36 passed**, incluindo segurança HTTP, recuperação, execução
  única, decisões/posições divergentes, preços brutos/ajustados e limites.
- Regressão focada completa: **82 passed**.
- Suíte completa no commit `3cff317`: **1499 passed / 10 failed** em 516,61 s.
  São as sete falhas de ambiente PostgreSQL em 5435 e as três expectativas
  históricas já documentadas; **nenhuma regressão nova**.
- Ruff (lint e formatação) e `node --check dashboard/paper.js`: aprovados.
- `scripts/check_h2_forward_dashboard.py`: **265 hashes protegidos inalterados**.
- `scripts/run_h2_v6_supervised.py verify`: **ok**, um evento, zero erros.
- Chrome: quatro áreas em **1440/640/420 px**, zero erros exibidos, zero
  erros/avisos de console e nenhum overflow horizontal; detalhes de agente e
  carteira também conferidos. O backend foi reiniciado após as correções.

Os testes usaram fixtures temporárias externas ao repositório, sem chaves
Gemini reais. Hooks de auditoria Python bloquearam conexões e DNS externos;
loopback foi permitido para testes HTTP e a dependência PostgreSQL existente.
As integrações científicas executadas pela suíte são sintéticas, com transporte
falso; nenhum experimento Validation/Final Test real foi reexecutado.

Uma execução intermediária encontrou a fixture OA-1 com árvore suja durante a
segunda correção (1497 passed / 11 failed). O gate de Git limpo funcionou; essa
execução foi substituída pela suíte final no commit `3cff317`, sem editar a
árvore durante os testes. As falhas anteriores estão classificadas em
[H2_V6_PREMIUM_UI.md](H2_V6_PREMIUM_UI.md#classificação-das-12-falhas-da-regressão-anterior).

Reprodução dos verificadores, somente leitura:

```powershell
.venv/Scripts/python.exe -B scripts/check_h2_forward_dashboard.py
.venv/Scripts/python.exe -B scripts/run_h2_v6_supervised.py verify
```

## Capturas renovadas

| Área | 1440 px | 640 px | 420 px |
|---|---|---|---|
| Visão Geral | [captura](evidence/h2_premium_v2/recheck/overview-1440.jpg) | [captura](evidence/h2_premium_v2/recheck/overview-640.jpg) | [captura](evidence/h2_premium_v2/recheck/overview-420.jpg) |
| Sala de Decisão | [captura](evidence/h2_premium_v2/recheck/room-1440.jpg) | [captura](evidence/h2_premium_v2/recheck/room-640.jpg) | [captura](evidence/h2_premium_v2/recheck/room-420.jpg) |
| Carteiras | [captura](evidence/h2_premium_v2/recheck/wallets-1440.jpg) | [captura](evidence/h2_premium_v2/recheck/wallets-640.jpg) | [captura](evidence/h2_premium_v2/recheck/wallets-420.jpg) |
| Agentes | [captura](evidence/h2_premium_v2/recheck/agents-1440.jpg) | [captura](evidence/h2_premium_v2/recheck/agents-640.jpg) | [captura](evidence/h2_premium_v2/recheck/agents-420.jpg) |

Detalhes: [Supervisão Humana](evidence/h2_premium_v2/recheck/supervision-1440.jpg),
[carteira supervisionada](evidence/h2_premium_v2/recheck/wallet-supervised-1440.jpg),
[TA-01](evidence/h2_premium_v2/recheck/agent-detail-1440.jpg).
Medições: [browser-checks.json](evidence/h2_premium_v2/recheck/browser-checks.json).

## Limitações

- COTAHIST diário confirma a simulação posteriormente; não comprova execução
  intradiária em tempo real e não envia ordens reais.
- Risk e `BUY_AT_TARGET_NOOP` avaliam a posição original; seus vetos não são
  reinterpretados para outra posição supervisionada.
- O servidor local não identifica operadores. Locks remanescentes após término
  forçado exigem diagnóstico local; aprovações e reservas não devem ser apagadas.
- Há somente um fechamento reconciliado: sem curva de desempenho suficiente ou
  inferência causal sobre o filtro humano.
- Não houve nova inicialização, backfill, alteração de ledger original, mudança
  em `src/`, retuning ou push.
