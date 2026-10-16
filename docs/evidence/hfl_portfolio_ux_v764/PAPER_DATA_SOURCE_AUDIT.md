# Inventário de fontes e mecanismos

Inspecionados `forward_api.py`, `platform_api.py`, `portfolio_api.py`, `global_pm_api.py`, runners H2/supervisão/benchmarks, motor multiativos e protocolo V7.6. **GET** significa consulta; os mecanismos de escrita listados já existiam e não foram acionados.

| Recurso | Implementado / persistente | Oficial ou sintético | Consulta / modifica estado | Compatibilidade |
|---|---|---|---|---|
| Ledger H2 + B&H | sim / state.json | paper exploratório prospectivo, não confirmatório | GET; runner escreve explicitamente | H2 |
| Ledgers SMA/Bollinger | sim / state.json por estratégia | paper prospectivo independente | GET; sync escreve explicitamente | H2 |
| Ledger supervisionado | sim / state.json + cadeia de auditoria | paper prospectivo independente | GET; sync/ações humanas escrevem | H2 |
| Posições H2 | sim / unidades e caixa nos estados | paper, conforme eventos reconciliados | portfolios GET; reconciliação modifica | H2 |
| Operações executadas H2 | sim / sessions[].trades | paper observado, atualmente nenhuma | GET; runner escreve | H2 |
| Intenções pendentes H2 | sim / pending e decisões | não são fills | GET; runner escreve | H2 |
| Aprovações humanas | sim / approvals/*.json supervisionadas | vinculadas ao hash/prazo | supervision GET; act escreve | H2 supervisionada |
| Marcação e curva H2 | sim / mark e sessões reconciliadas | preços ajustados locais observados | GET; prepare/reconcile escreve | H2 |
| Custos H2 | sim / trades e política congelada | paper | GET; execução contabiliza | H2 |
| Recebíveis/D+2 oficiais multiativos | mecanismo didático existente; ledger oficial ausente | somente sintético V5 | GET demo; motor escreve na raiz sintética | multiativos demonstrativo |
| Reservas / custódia / custo médio / PnL separado | sim no motor V5/snapshots; H2 não publica | sintético/hipotético identificado | GET; motor didático escreve na sua raiz | multiativos demonstrativo |
| Ledger V5 | sim / state, events e demo selados | DEMONSTRAÇÃO SINTÉTICA | GET e cenários puros; CLI demo escreve | multiativos demonstrativo |
| Inferências Global PM V1/V2 | sim / context, result, claim, authorization, journal | Gemini oficial consultivo + snapshot hipotético | GET verificado; runners pagos escrevem | multiativos consultivo |
| Execução Global PM oficial | não / não | não existe | bloqueada por falta de mecanismo/contrato aprovado | multiativos oficial |
| Jobs de atualização H2 | sim / jobs operacionais | mecanismo operacional | GET status; start/prepare/sync modifica | H2 |
| Atualização automática diária | nenhum agendamento suficiente encontrado | não aplicável | nenhuma automação habilitada | ambas |
| API de monitoramento nova | sim / lê persistência existente | mantém classificação por fonte | somente GET, sem estado financeiro próprio | H2 + snapshot Global PM |

Raízes: `data/forward/h2_v6_paper`, `h2_v6_supervised`, `h2_v6_benchmarks/<estratégia>`; demonstração `data/portfolio/.../demo-qualified-v5`; contextos `data/global_pm/hfl_global_pm_v1/v7-*` e `hfl_global_pm_v2/v74-*`. Nomes completos são resolvidos pelos módulos existentes, sem aceitar caminhos enviados pelo cliente.

Preços: inputs locais congelados, CSVs e cache COTAHIST existente; fatores ajustados yfinance já preparados. Esta entrega não faz requisições externas. Proventos H2 não são lançados novamente em caixa: o ledger usa série ajustada, conforme documentação existente. Não aplicar D+2 do motor V5 à H2.
