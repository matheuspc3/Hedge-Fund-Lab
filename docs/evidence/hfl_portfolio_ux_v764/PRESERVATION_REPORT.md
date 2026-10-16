# Preservação

`preservation_before.json` foi criado **antes de qualquer implementação** pelo utilitário existente. Cobre Radar/registro e ledgers H2, conforme escopo desse utilitário. Antes da regressão completa: `changes: []`, `violations: []`.

V1/V2, fixtures seladas e evidências científicas também são conferidos pelos baselines históricos e verificador V7.5: `ok: true`, nenhuma ausência, divergência de métrica/documento ou violação. Protocolo V7.6: `errors: []`. Snapshot adicional `protected_pre_regression.json` cobre Global PM/carteira demonstrativa antes da suíte; não é apresentado como anterior à implementação.

Não foram editados `src/`, runners, validadores, contratos, políticas, baselines, estados financeiros, claims, journals, autorizações ou reservas. Adaptador novo é somente leitura/apresentação; nenhum handler de escrita modificado. A primeira regressão detectou que portfolio_api.py era fixado por baseline; esse arquivo foi restaurado byte a byte e o roteamento novo foi movido para server.py, sem modificar baselines. Nenhuma inferência, chamada Gemini, ordem, execução paper, H2 Final Test, retuning ou push.

Verificação final após a suíte:

| Evidência | Resultado |
|---|---|
| preservation_since.json | changes: [], violations: [] desde o snapshot inicial |
| preservation_baselines.json | violations: []; somente duas divergências OPERATIONAL históricas de job/last_prepare, já existentes |
| protected_since.json | 227 arquivos Global PM/V5 antes e depois; changes: [], violations: [] |
| consolidation_final.json | ok: true; nenhuma divergência científica |
| protocol_final.json | errors: [] |
| git diff 888c8d7..HEAD -- dashboard/portfolio_api.py | vazio; API selada restaurada exatamente |

Os bytes de registros/claims/journals/autorizações/reservas foram preservados. Relatórios/capturas desta pasta não são evidências científicas retroativamente modificadas.
