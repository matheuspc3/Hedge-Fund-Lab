# H2 de 13/10 — investigação somente leitura

Observação em 13/10/2026 após 10:00 BRT. Fontes primárias: `data/forward/h2_v6_paper/state.json`, `sessions/2026-10-09/decision.json` e `reconciliation.json`; propostas/estado/auditoria da supervisionada; oito jobs existentes; `forward_api.order_state`, `run_h2_v6_forward.run/reconcile/target_open`, `run_h2_v6_supervised.order_state/resolve`, `forward_jobs`. Evidência consultada em `official_before.json` e inventário sanitizado `h2_jobs_observed.json`. Nenhum runner, prepare, sync, act ou reconcile foi executado.

| Item | Original | Supervisionada |
|---|---|---|
| Tratamento | H2-V6-FORWARD-PAPER | estratégia independente h2_v6_supervised |
| Sessão de decisão | 09/10/2026 | mesma decisão original referenciada |
| Decisão produzida | 10/10/2026 15:17:04.881596 BRT | referência à mesma decisão |
| Proposta supervisionada | não aplicável | 10/10/2026 21:02:07.690651 BRT |
| Abertura alvo / deadline | 13/10/2026 10:00 BRT | 13/10/2026 10:00 BRT |
| Persistida antes da abertura | true | created_after_deadline=false |
| Autorização | contrato original: confirmação do runner pelo hash do input; sem aprovação humana separada por ordem | aprovação humana específica antes do deadline |
| Aprovação/cancelamento | não integra contrato original | nenhum registro |
| Estado consultado | PENDENTE | EXPIRADA, derivada na consulta |
| Última marca | 09/10, close ajustado 56 | mesma sessão |
| Caixa / unidades | 100000 / 0 | 100000 / 0 |
| Execução/reconciliação de 13/10 | nenhuma | outcome=null; nenhuma |

Hash da decisão original: `27e51c949aebac155b1d890c6fff74d1a242852d7f5c8d3a30cdc602a6a09ddc`. Pending original contém decision_session=09/10, target_session=13/10, target_weight=1.0; a referência corresponde à decisão persistida. Portanto não é órfã nem cache desatualizado da interface: a API lê o estado corrente, e os arquivos ainda terminam em 09/10.

**Conclusão:** é uma intenção persistente válida segundo o contrato original, aguardando processamento com preços observados e reconciliação. O deadline original impede **gerar decisão** depois de conhecida a abertura; não é TTL de uma aprovação humana que o contrato original não exige. A reconciliação original procura a barra da target_session, registra a simulação na abertura observada e só então limpa pending. `forward_api.order_state` apresenta PENDENTE enquanto esse registro não existe. A supervisionada tem contrato diferente: sem aprovação até o deadline, `order_state` deriva EXPIRADA mesmo sem escrever no ledger.

Jobs: oito registros locais concluídos em 10/10, comandos prepare/preflight/benchmarks, nenhum job de reconciliação de 13/10 identificado. O inventário não prova ausência de um scheduler externo ao repositório; nenhum agendamento diário suficiente foi encontrado no código auditado. Nenhum saldo ou execução indica que a intenção já foi processada.

Não se constatou bug de expiração por falta de aprovação na original. Há uma limitação operacional/UX: PENDENTE isoladamente não mostra a idade da marca e pode sugerir fila ativa sem job. Correção proposta para tratamento/revisão futura: acrescentar estado de leitura "aguardando dados/reconciliação da sessão-alvo", data da última marca e ausência de job, sem expirar/alterar a intenção original. Testes necessários: decisão pré-abertura persistida, relógio pós-abertura sem barra, barra disponível sem job, reconciliação registrada, intenção com referência inexistente, e ausência de escrita em GET.

Nesta V7.6.5 nenhuma aprovação retroativa, inferência, operação ou reconciliação histórica foi registrada. Não é recomendação para executar a intenção hoje: qualquer ação continua dependente do protocolo e autorização do operador. O novo ledger não aplica D+2 ou regras de expiração à H2.
