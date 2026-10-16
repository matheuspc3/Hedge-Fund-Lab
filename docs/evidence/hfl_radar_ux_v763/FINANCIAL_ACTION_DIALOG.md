# Confirmação compartilhada de custo

`HFL.confirmCost(data)` retorna `Promise<boolean>`. O componente é somente
apresentação/consentimento: não conhece endpoints, não faz fetch e não autoriza
o provedor. Modal nativo `dialog`, cancelamento/Escape, foco inicial em Cancelar,
retorno de foco ao acionador e botão desabilitado até consentimento explícito.

Campos: `operation`, `treatment`, `context`, `run`, `callsMax`, `estimatedUsd`,
`reservedUsd`, `remainingUsd` opcional, `validUntil` opcional, `ready`, `source`
e `confirmationToken`. Ausência de dados obrigatórios, custo inválido, reserva
inferior à estimativa e validade vencida impedem abertura. O prazo, quando
informado, é revalidado ao confirmar. Sem prazo fornecido, o diálogo informa
que o backend revalida o contexto, sem inventar uma validade.

Estimativa e reserva são exibidas separadamente, em USD com seis casas; nenhuma
é apresentada como fatura. Falha incerta pode gerar cobrança; execução consultiva
não envia ordens. Detalhes mostram a fonte e o token do preflight.

## Integração autorizada nesta versão

O listener do botão `#execute` do Radar continua exigindo `report.ready`,
consentimento original, isolamento de rede, orçamento e execução gravável.
Para um lote pago, abre o diálogo usando o próprio `POST /api/radar/preflight`:
estimativas/reservas e máximos de chamadas vêm de `items[].estimate`.
Orçamento remanescente deriva dos tetos e reservas operacionais existentes.
Depois do modal, compara a versão da visualização e a identidade do relatório;
mudança de seleção/preflight recusa a operação. O payload original conserva
`confirmation_token`, `authorize_paid`, `confirm`, tickers, sessão, teto e replay.
O servidor recalcula seu preflight como antes. Não há novo botão pago nem alteração
de contrato/runner; recuperação offline e demonstração seguem o fluxo existente.

## Testes e próximos pontos de integração

Fixtures locais verificam dados, detalhes, cancelamento, Escape, consentimento,
recusa de campos ausentes/expirados, payload inalterado e contexto alterado durante
o modal. Preflight/run desses testes são respondidos pelo DevTools antes do envio.
Nenhum POST pago chega ao servidor. Os custos das fixtures são explicitamente
de teste e não aparecem na aplicação em consultas reais.

Paper/H2 poderão adotar o componente no UX-M6 após mapear seu preflight específico.
Global PM V1 permanece fechado na UI; V2 permanece somente pelo CLI. Não há
integração paga nova para nenhum deles.
