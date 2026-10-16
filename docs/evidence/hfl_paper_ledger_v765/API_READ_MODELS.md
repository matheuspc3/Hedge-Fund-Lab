# API e dashboard

Nova rota **GET /api/portfolio/ledger**, roteada em server.py sem alterar portfolio_api.py selado. Catálogo normal: wallets=[], OFFICIAL_PAPER_DISABLED, official_execution_enabled=false. O snapshot V2 e H2 continuam nos endpoints anteriores. Nenhum parâmetro seleciona caminho de arquivo ou banco.

| Consulta | Resultado |
|---|---|
| `?demo=1` | catálogo explícito da exportação sintética, se existir |
| `?demo=1&wallet=synthetic-v765` | resumo/posições atuais, curva, operações, eventos, preços, reconciliações |
| `&session=2026-04-17` | estado da sessão reconciliada, marca e posições dessa sessão |
| `&resource=events&limit=10&offset=10` | página de eventos completos, IDs e hashes |
| `&resource=sessions&from=2026-04-20&to=2026-04-22` | snapshots completos das sessões no intervalo |
| `&resource=trades/settlements/reconciliations/orders/observations` | usar um dos nomes, sem barras, para histórico correspondente |

Limite 1..100 (default 50); offset 0..1000000. Resposta paginada: items, total, offset, limit, next_offset. Filtros ISO from/to inclusivos, session exata exige sessão reconciliada. Históricos longos têm páginas, inclusive arrays da view principal e metadados `pagination` por recurso. Todos os pontos mantêm snapshot completo de posições, base/custo médio, caixa, PnL/custos/pesos, hashes e reconciliação.

O envelope verifica selo/exportação, replay e integridade de modo puro. Não executa Gemini, reconciliador persistente ou create/append; teste substitui ambos os escritores por exceções e confere bytes antes/depois. Teste HTTP reinicia o servidor e compara resumo/curva/trades. Não há POST de execução do ledger novo; a rota rejeita POST (404) e query duplicada/desconhecida/inválida (400). Erros de integridade/leitura usam o contrato existente `portfolio_integrity_or_query_failed` (400); a interface oculta estado financeiro anterior. Não há recuperação silenciosa.

## DASHBOARD_INTEGRATION

`/portfolio`: somente multiativos no seletor padrão. Link explícito muda para linha experimental H2 em `/paper`. Deep link antigo `wallet=h2:*` é redirecionado preservando carteira e abrindo acompanhamento H2; `/paper` continua com cinco alternativas independentes. Não se somam carteiras.

Checkbox "Explorar demonstração do ledger persistente · dados sintéticos" é opt-in; `demo=1` preserva seleção explícita em deep link. O catálogo sintético substitui o consultivo enquanto selecionado. Não existe fixture apresentada como carteira oficial. O modo mostra origem, identidade operacional própria, qualificação temporária, ausência de tratamento científico e execução oficial desabilitada.

Visão geral: patrimônio, caixa, exposição e número de posições. Caixa puro não gera rosca. Posições/acompanhamento: marca histórica, tabela de custódia/custo médio, pontos patrimoniais sem interpolação, tabela equivalente, seletor de sessão e liquidações futuras. Evidências: três operações da fixture, timeline com dez eventos/página, referências de hashes e reconciliações. Resultado atual e histórico selecionado são calculados pelo backend; JavaScript só formata.

Atualizar visualização faz GET; não avança sessão nem importa preços. Uma sessão não vira histórico de rentabilidade. Simulador V5/V6 mantém sua área independente e rótulos. Registros Global PM oficiais continuam consultáveis na aba de decisões. Sem fluxo financeiro novo no servidor normal.
