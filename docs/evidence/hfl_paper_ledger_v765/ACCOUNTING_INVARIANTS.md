# Contabilidade e reconciliação

Autoridade: `multiasset_portfolio.apply/view/reserve/fill` selado. Dinheiro em Decimal, centavos HALF_EVEN, custo médio calculado a partir da base contábil; arredondamento de venda parcial preserva a base residual. Preços não finitos, floats, bools, quantidades fracionárias/negativas e montantes fora de centavos são recusados pelo motor. Numpy/float existente é usado só na estatística de risco, não para contabilização.

- Caixa disponível = liquidado − reservado; recebível nunca financia compra antes da confirmação.
- Quantidade disponível = total − reservada − em liquidação; nenhuma venda a descoberto.
- Patrimônio = caixa liquidado + recebíveis + valor marcado das posições; reserva não é descontada duas vezes.
- Patrimônio = capital inicial + realizado líquido + renda líquida + não realizado.
- Base das compras inclui custos; venda reconhece receita líquida menos base proporcional. Custos não são debitados novamente na liquidação.
- Exposição/pesos derivam do valor marcado dividido pelo patrimônio, com resíduo dos pesos no caixa, conforme V5.
- Compra é pré-financiada na execução; D+2 libera custódia. Venda gera recebível líquido D+2. Não é um novo modelo de clearing.
- Veto impede **qualquer** operação, inclusive redução. Validador V5 verifica custódia, concentração, exposição, custos, giro diário, histórico de risco, pareceres e dependências.

Qualificação final (fixture): compras de 100 PETR4 × 40 e 100 VALE3 × 60 em 17/04; custos 4 + 6. Custódia liberada em 22/04. Venda de 40 PETR4 × 43 em 22/04: custo 1,72, base 1601,60, realizado 116,68, recebível 1718,28, confirmado em 24/04. Marcas finais PETR4=41 e VALE3=60: caixa 91708,28, posições 8460,00, patrimônio 100168,28, custos 11,72, não realizado 51,60. São valores sintéticos, sem observação científica de retorno.

## RECONCILIATION

Primeira barreira: replay integral reaplica cada validação/redutor e compara o checkpoint persistido. Segunda: view confere identidades financeiras e saldos. Terceira: reconciliador do envelope confere totais de custos/realizado versus fills, IDs de ordens/fills e datas D+2 contra calendário verificado. Pode receber `expected` externo (campos da view); divergência é registrada com motivo exato, sem mudar saldo.

`PORTFOLIO_RECONCILED` publica snapshot completo por sessão só em sucesso; um ponto não é histórico de desempenho. Sessão publicada não pode receber nova ordem ou nova valorização, e não é sobrescrita. Falha registrada ou marca incompleta bloqueia ordens dependentes. Falhas de leitura/replay retornam `RECONCILIATION_FAILED` sem evento de reparo. A leitura GET é pura; não persiste reconciliação.

Testes: divergência explícita de patrimônio, adulteração de saldo no checkpoint, mutação de custo/preço via hashes, índice/cadeia/cronologia inválidos, eventos duplicados, importação repetida, arquivo corrompido e remoção de cauda. Cinco mutantes em memória removem as guardas de RAW, checkpoint, escopo de autorização, autoridade de fill e cobertura de calendário: os mesmos checks falham em cada mutante. Nenhum arquivo selado é editado para testar mutações.

Drawdown reutiliza peak_equity do V5 por evento; não é uma nova métrica científica calculada apenas por fechamentos. Volatilidade no read model permanece indisponível quando não há estatística publicada. A curva exporta custos, realizado, não realizado, exposição, drawdown, posições, pesos e hashes de marca/reconciliação por sessão.
