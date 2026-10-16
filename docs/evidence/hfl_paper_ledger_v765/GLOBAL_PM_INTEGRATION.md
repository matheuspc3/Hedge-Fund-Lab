# Global PM e autorização futura

Consulta local confirmou os IDs originais:

| Registro | Resultado preservado | Consequência |
|---|---|---|
| v7-5a78ea5d15214e37bcae18f167ffcee3 (V1) | REJECTED_BY_VALIDATOR | somente evidência |
| v74-76d07c0d32444cecaf07e875deacb519 (V2) | VALID_PROPOSAL, 100% caixa, zero operações, PETR4/ITUB4 em observação | manter snapshot consultivo, nenhuma ordem |

`paper_ledger_api.official_reference` usa `platform_api.public_global` para ler e verificar os registros existentes e extrai ID, identidade, hash do contexto, resultado e validação, status, número de operações e execution_enabled=false. `PROPOSAL_REFERENCED` registra esse vínculo informativo **somente em carteiras sintéticas durante os testes**. Referências não entram no mapa de propostas executáveis V5, não mudam o status selado e não podem obter autorização por VALIDATION_RECORDED. Teste comprova que referenciar V1/V2 não altera um centavo.

A execução sintética usa exclusivamente propostas estruturadas V5 e contextos de fixture com pareceres/60 retornos, validados pelo manager existente. PROPOSAL_LINKED, VALIDATION_RECORDED e AUTHORIZATION_RECORDED são etapas distintas. A autorização vincula carteira, versão/escopo, operador sintético, hashes da proposta/validação, estado, marks, operações/quantidades, limites e prazo. O motor revalida ao reservar. Uma proposta sem operações pode receber registro informativo de aprovação, mas PAPER_ORDER_CREATED é recusado — não inventa negociação.

## PAPER_AUTHORIZATION_DESIGN

Fluxo oficial futuro, ainda sem adaptador/endpoints de escrita:

```text
Decision → Proposal → Validation → READY_FOR_HUMAN_REVIEW
→ AUTHORIZED → PAPER_ORDER_PENDING → PAPER_FILLED
→ Settlement → Valuation → Reconciliation
                    ↘ PAPER_REJECTED / EXPIRED
```

Antes de habilitar: novo tratamento/protocolo revisado, identidade e caixa próprios, proposta válida, contexto prospectivo antes da abertura, autorização humana autenticada por campanha/carteira/etapa e hashes, prazo não vencido, quantidade explícita, preço RAW de abertura t+1 com proveniência validada, idempotency key persistida, conferência de risco/settlement e reconciliação. Cancelamento/rejeição/expiração deixam trilha; contexto expirado não produz nova autorização automaticamente.

Não reutilizar aprovação de inferência Gemini como autorização financeira, nem aprovações H2/V1/V2 entre tratamentos. Veto permanece NO_OPERATION_ON_VETO; permitir redução de ativo vetado exige tratamento científico novo. Ativação exige ingestão oficial e calendário prospectivo validado. O modelo sintético aqui não implementa identidade humana/autenticação oficial, slippage ou abertura causal.

V1 pago no backend continua a pendência histórica `BACKEND_V1_CLOSURE_PENDING_APPROVAL` descrita na V7.6.3. Não foi acionado nem modificado nesta entrega. Não confundir a ausência de endpoint de execução do **novo ledger** com uma mudança nos handlers legados de inferência.
