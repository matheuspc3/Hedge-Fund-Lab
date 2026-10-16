# Próximas etapas propostas, não iniciadas

## HFL-PAPER-001

Consulta persistente disponível implementada. Monitoramento automático multiativos completo depende de mecanismo operacional aprovado. Reutilizar motor V5, sem promover ledger sintético; estabelecer raiz/identidade oficial própria sob o contrato já proposto no protocolo V7.6 (`PAPER_LEDGER_NOT_IMPLEMENTED`). Nenhuma escrita financeira ativada nesta versão.

Contrato mínimo por evento futuro: `event_id`, identidade/carteira, sessão de decisão, sessão-alvo, instante de disponibilidade do dado, tipo/estado, `record_id`, `context_sha256`, `result_sha256`, hash da autorização financeira específica, referências de preço bruto/fator ajustado/fonte, quantidades, preço, custos, liquidação e hash anterior. Motor existente produz contabilidade/risco e aplica idempotência, integridade, validação e reconciliação; frontend só lê. Aprovação de inferência não substitui aprovação financeira. Nunca backfill de compra ou autorização posterior ao prazo.

Antes da abertura: proposta validada + autorização específica vigente, vinculadas por hash; abertura observada t+1 só chega ao executor; fechamento observado gera marcação/reconciliação. Sem dado íntegro/autorização, manter estado e publicar motivo. Definir política oficial de custos, calendário, corporate actions e D+2 em revisão própria.

## Atualização de preços futura

| Tema | Proposta para revisão |
|---|---|
| Fonte | ingestão B3 COTAHIST existente para bruto; fator ajustado separado para indicadores |
| Frequência/disponibilidade | diária após publicação/validação; sem alegar tempo real |
| Cache | cache anual existente, inputs congelados por sessão e hash |
| Licença | revisar termos/redistribuição B3/yfinance antes de automatizar/publicar; não verificados nesta entrega |
| Integridade | hashes, esquema, cobertura, cronologia, corporate actions e proveniência causal |
| Falhas | manter última marca com data, sinalizar atraso, bloquear sessão incompleta; não substituir dados |
| Reconciliação | runner autorizado aplica eventos/marcações atomicamente em carteira própria e idempotente |

Nenhuma API paga nova. Jobs atuais são explicitamente acionados; GET não os dispara. Novas decisões seladas entram no catálogo ao atualizar visualização; execuções somente após registro válido pelo mecanismo autorizado.

## UX pendente

UX-M6: migrar integralmente operação diária, pesquisa e controles H2 preservando confirmações. UX-M7: auditoria dedicada, logs/evidências transversais. UX-M8: zoom nativo 200%, leitor de tela, alvos/contraste integral e comparação visual. Servidor V1 continua `BACKEND_V1_CLOSURE_PENDING_APPROVAL`; proposta existente não aplicada. Não iniciar automaticamente outra versão, campanha ou inferência.
