# Histórico oficial do Gestor Global

Dados conferidos por `platform_api.public_global` contra contexto, resultado, claims e autorização existentes. `official_decisions.json` é uma observação para auditoria desta entrega; não alimenta a interface nem substitui artefatos primários.

| Campo | V1 | V2 |
|---|---|---|
| Identidade | HFL-MULTIASSET-GLOBAL-PM-V1 | HFL-MULTIASSET-GLOBAL-PM-V2 |
| Registro | v7-5a78ea5d15214e37bcae18f167ffcee3 | v74-76d07c0d32444cecaf07e875deacb519 |
| Status selado | REJECTED_BY_VALIDATOR | VALID_PROPOSAL |
| Sessão de mercado | 09/10/2026 | 09/10/2026 |
| Resposta concluída (BRT) | 12/10/2026 15:27:04 | 12/10/2026 18:08:01 |
| Caixa-alvo | 100% | 100% |
| Patrimônio hipotético | R$ 100.000 | R$ 100.000 |
| Operações propostas / executadas | 0 / 0 | 0 / 0 |
| Financeiro V5 isolado | válido | válido |
| Validação global | rejeitada | aprovada |
| Custo observado mínimo USD | 0,02354175 | 0,02626725 |
| Reserva USD | 0,159744 | 0,159744 |
| Cobrança confirmada | não | não |

V1 falha em `explanation_selection_inconsistent`: a intenção econômica de caixa não corrige a inconsistência das listas do contrato. Continua rejeitada, com evidências acessíveis e nenhum botão de nova inferência.

V2: PETR4, ITUB4, VALE3, WEGE3 e BBAS3 com peso-alvo zero. PETR4 e ITUB4 estão na watchlist por sinal favorável com RSI elevado. VALE3 tem VENDA, mas não há custódia para vender; BBAS3 é vetada por risco; WEGE3 é MANTER. Motivos completos e métricas citadas vêm da resposta real. Validação não produz autorização financeira ou posição.

A tela separa data da sessão, conclusão da inferência (`result.completed_at`) e consulta da interface. O preparo do contexto (`created_at`) aparece na lista e nas evidências, sem ser chamado de data da deliberação. Expiração do contexto é apresentada separadamente do status selado.

O backend V1 continua com `BACKEND_V1_CLOSURE_PENDING_APPROVAL`. Nenhum bloqueio científico de servidor foi implementado; a página nova remove os gatilhos de escrita e não carrega o script operacional legado. V2 somente consulta, sem botão pago.
