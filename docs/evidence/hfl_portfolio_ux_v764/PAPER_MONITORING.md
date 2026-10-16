# Acompanhamento paper

## Implementado

Leitura dos cinco estados H2 persistidos, seleção por carteira, atualização por GET, posições/caixa/custos/exposição, última decisão e controles registrados, histórico de operações, curva por sessões reconciliadas, marcas e fontes. A linha do tempo combina eventos publicados, sem criar um journal paralelo. PnL total líquido de custos vem da projeção H2 existente; realizado e não realizado ficam indisponíveis quando não publicados separadamente.

Atualizar relê o armazenamento. Não salva patrimônio no navegador, chama agentes, baixa preços ou reconcilia. Requisições antigas não substituem uma seleção mais recente. Erros escondem valores antigos para evitar associação à nova carteira; há consulta novamente. As cinco carteiras são alternativas independentes e seus patrimônios não se somam.

## Observação H2 de 13/10

Em `h2_observation.json`: todas as cinco carteiras têm R$ 100.000 em caixa, zero posições, zero custos, uma marca de 09/10/2026 e nenhuma compra/venda reconciliada. IA H2 v6, Buy & Hold e SMA têm intenções para 13/10; Bollinger mantém caixa. A supervisionada, sem aprovação, é **EXPIRADA** após o prazo de 13/10 às 10h BRT. A expiração é calculada pelo backend na consulta e rotulada como evento derivado, sem lançamento persistido novo. A intenção H2 original permanece pendente de reconciliação, sem confirmar execução.

A observação é datada e não substitui futuras leituras. Não se presume preenchimento pela passagem da abertura, autoriza após prazo ou reconstrói entrada retroativa.

## Bloqueios

Não existe ledger prospectivo multiativos oficial compatível com Global PM V2. Existe motor V5 com ledger sintético selado; promovê-lo implicitamente a carteira oficial seria incorreto. O adaptador apresenta somente o snapshot consultivo V2, em caixa, e identifica a ausência de acompanhamento operacional.

H2 não publica reservas, quantidades em liquidação, custo médio, recebíveis D+2 ou decomposição de PnL. Esses campos são indisponíveis, sem importar política multiativos. A série H2 só publica patrimônio histórico: caixa/valor investido históricos não são reconstruídos pelo frontend. Um fechamento é insuficiente para gráfico temporal ou drawdown.

Contrato futuro em [NEXT_STEPS.md](NEXT_STEPS.md) e no protocolo V7.6 existente. Nenhum mecanismo de escrita foi habilitado.
