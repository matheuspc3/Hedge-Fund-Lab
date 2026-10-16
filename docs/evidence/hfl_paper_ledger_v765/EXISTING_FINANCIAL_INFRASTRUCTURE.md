# Auditoria prévia — V7.6.5

Branch inicial `#1-Update`, HEAD `b025104`. Somente `out.json` estava não rastreado; é do operador e não integra esta entrega. Fontes: ROADMAP, README/relatórios V7.6.2–V7.6.4, protocolo paper V7.6, módulos abaixo e registros locais. O relatório V7.6.4 confirma 1765 passed, 14 failed, 61 subtests e Chrome 36/36; ainda será confrontado com regressão desta entrega.

| Capacidade | Existente / implementação | Reuso | Limitação |
|---|---|---|---|
| Criar carteira | `scripts/multiasset_portfolio.py::apply(INITIALIZED)` | redutor puro | identidade V5 sintética, não ledger operacional |
| Posições | `position`, `view`, `fill` | integral | quantidades inteiras; BRL |
| Comprar / vender | `reserve`, `fill`, `apply` | integral | pré-financiado; custos didáticos |
| Caixa | `view`, `fill` | integral | compra debita na execução, custódia libera D+2 |
| Reservas | `reserve`, `CANCELLED` | integral | uma cesta pendente por carteira |
| Recebíveis | `fill(SELL)`, `SETTLED` | integral | venda só financia compra depois da confirmação |
| Liquidação D+2 | `settlement_day`, `B3Calendar` | cálculo + guarda de cobertura nova | V5 aceita regras 2026; lista oficialmente conferida termina 31/08 |
| Custos | `cost`, `POLICY` | integral | 0,1%; PRE_IR, não modelo tributário |
| Marcação | `checked_marks`, `MARKED`, `view` | adaptador versionado | motor aceita apenas RAW sintético; proveniência externa fica no envelope |
| Reconciliação | `view`, `Store.load/verify` | invariantes + replay | store V5 restrito a `data/portfolio/.../demo-*` |
| Patrimônio histórico | replay V5 e curvas H2 | novo modelo de leitura | não há série multiativos operacional por sessão |
| Persistência | Store V5, JSON atômico; H2 `state.json` | redutor, hashes; não stores selados | projeções V5 separadas da escrita de eventos |
| Recuperação | Store V5 replay/checkpoint/lock local | conceito, não escrita V5 | sem transação única entre arquivos |
| Parecer / limites / giro | `multiasset_manager.validate/risk` | integral | histórico de risco sintético, 60 retornos; veto proíbe também venda |
| APIs / dashboard | `monitoring_api.py`, `monitoring.js`, `server.py` | contrato visual existente | V2 snapshot, H2 independente; GET nunca reconcilia persistindo |

Banco existente: SQLAlchemy/PostgreSQL em `src/db/connection.py`, voltado a cotações/indicadores (`models.py`). Não há migração nem tabela de ledger a reutilizar; não se inicia PostgreSQL. Escolha: SQLite da biblioteca padrão, arquivo **exclusivamente temporário**, schema independente versionado, `BEGIN IMMEDIATE`, unicidade e eventos/checkpoint na mesma transação. Nenhuma dependência nova. A API normal não instancia escritores.

O adaptador terá identidade `HFL-MULTIASSET-PAPER-LEDGER-V1`; manterá identidade, política e arquivos do motor V5 intactos. Metadados, catálogo de eventos, cobertura do calendário e proveniência são contratos novos, explícitos. Nenhuma extensão silenciosa dos experimentos anteriores.

Preservação anterior à implementação: `preservation_before.json` (Radar/H2/registry), `protected_before.json` (11250 arquivos Global PM, V5 e evidências anteriores), `official_before.json` (consulta offline V1/V2 e cinco H2). Baselines históricos: zero violações, duas diferenças operacionais legadas. Não se acionaram runners, claims, reconciliações ou fontes externas.
