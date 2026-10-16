# Preservação V7.6.5

Antes de implementar: `preservation_before.json` cobre Radar/H2/registro; `protected_before.json` fixa 11250 arquivos Global PM/V5 e evidências anteriores. `preservation_baselines_before.json`: violations=[], duas divergências OPERATIONAL já existentes. `official_before.json` fixa consulta V1 rejeitada, V2 validada e sem operações, e cinco carteiras H2 sem trades.

Não foram editados motor V5/V6, manager/validadores, calendário, runners H2/Radar/Global PM, contratos, src/, portfolio_api.py, claims, journals, autorizações oficiais, custos, políticas científicas, Final Test ou evidências anteriores. Novo código fica em módulos de envelope/qualificação/API; UI e roteamento somente leitura têm alterações explícitas. Nenhuma inferência, atualização externa, reconciliação retroativa, aprovação retroativa, ordem real, ordem paper oficial ou push foi executado.

As escritas de qualificação SQLite ocorrem em TEMP externo com prefixo hfl-paper-. Os testes legados da suíte têm armazenamento sintético isolado próprio; os snapshots antes/depois verificam que registros científicos reais não mudaram. H2 original continua pending, supervisionada expirada, ambos sem operações. V1/V2 continuam com resultados originais; nenhuma referência consultiva produz ordem.

Verificação final, após a regressão:

| Evidência | Resultado |
|---|---|
| preservation_final.json | changes=[], violations=[] desde o snapshot anterior à implementação |
| preservation_baselines_final.json | violations=[]; apenas as duas diferenças OPERATIONAL já presentes |
| protected_final.json | 11250 arquivos antes e depois, changes=[], violations=[]; inclui detecção de remoção/arquivos inesperados nas áreas protegidas |
| consolidation_final.json | ok=true, nenhuma ausência/divergência científica/documental |
| protocol_final.json | errors=[] |
| official_final.json | V1 REJECTED_BY_VALIDATOR; V2 VALID_PROPOSAL, zero operações; cinco H2 sem trades |
| diff contra b025104 em src/, motores/manager e portfolio_api.py | vazio |

Zero arquivos de evidência anteriores foram modificados. Diferenças operacionais históricas continuam declaradas, sem editar baselines. Regressão geral: mesmas 14 falhas do baseline, nenhuma nova. O servidor de captura sem chave foi encerrado depois da coleta; nenhum serviço oficial foi ativado.
