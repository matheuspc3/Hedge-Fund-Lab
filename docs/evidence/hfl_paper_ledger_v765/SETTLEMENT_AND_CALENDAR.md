# Liquidação e dados de mercado

## Cobertura e D+2

Reutilizados B3Calendar v2 e settlement_day V5; uma guarda nova exige presença na lista local conferida contra COTAHIST (`docs/evidence/calendar/`). SHA-256 do arquivo bruto: `c4af99f8807975bbdcdadcdd86a4d0e1f30a45a701ed7b2ed5657ed9bb4f0508`; digest da listagem documentado na fonte: `9f23b4b24f48537f90d8353c0820bdc0b2917a0bf1bfd40fca9d4364a9496619`. A diferença vem da serialização/terminador de linha, não de sessões distintas.

O motor limita-se a 2026; a lista verificada termina em 31/08/2026. O adaptador aceita somente a interseção: sessões 2026 existentes nessa lista. D+2 usa as duas sessões seguintes da lista **e** confere concordância com o cálculo V5. Sem duas sessões cobertas, bloqueia reserva/fill/liquidação; não estende cobertura por regra presumida. 28/08 é sessão coberta, mas seu D+2 exige setembro, portanto é bloqueado. 13/10 não está coberto por este adaptador, embora o calendário de regras consiga calculá-lo. Não se alterou calendário ou liquidação de H2/experimentos.

Exemplo verificável da fixture: sexta 17/04/2026 → segunda 20/04 (D+1); terça 21/04 é feriado e está ausente na lista; quarta 22/04 (D+2). Venda de quarta 22/04 → sexta 24/04. Fim de semana/21 de abril são recusados como sessões. Confirmação de custódia tem identidade própria, fonte sintética e data não anterior ao vencimento.

## MARKET_DATA_AND_VALUATION

Observação selada: schema, ticker/preços, sessão, BRL, RAW, fonte, classificação, tipo, timestamp, data_sha256 e sha256. Preços individuais são rastreáveis pelo hash do bundle que os contém. Cada importação do mesmo hash é única; repetir chave idempotente devolve o evento anterior, mudar chave não duplica a importação.

| Classificação | Fonte suportada nesta qualificação | Uso |
|---|---|---|
| SYNTHETIC_TEST | SYNTHETIC_OFFLINE_NOT_MARKET_DATA, fixture=true, SYNTHETIC_REFERENCE | valorização e fills sintéticos na mesma sessão |
| OFFICIAL_B3_RAW | B3_COTAHIST_FIXTURE, fixture=true, OPEN/CLOSE | fixture do **contrato/formato** oficial, apenas valorização |
| ADJUSTED_RESEARCH | não suportada | rejeitada, não misturada a custódia RAW |
| UNKNOWN_SOURCE | não suportada | rejeitada |

OFFICIAL_B3_RAW não significa que estes valores foram baixados da B3: são fixtures explicitamente identificadas. Não há ingestão oficial implementada/ativada. Nenhum preço real novo foi consultado ou baixado. A ponte versionada entrega ao motor seu contrato sintético original; o envelope conserva a proveniência original. Não troca classificação de um dado real por sintético.

Quotes só podem ser usados depois de observed_at, em sua sessão, sem retroceder o relógio. Fechamento não é preço de abertura: o adaptador de execução desta versão exige SYNTHETIC_REFERENCE, e recusa CLOSE/OPEN oficiais de fixture para criar ordens. O protocolo t → abertura t+1 continua dependência da ativação futura, não está simulado como se fosse execução oficial.

Se faltar preço para uma posição, PORTFOLIO_VALUED registra a sessão indisponível e os tickers ausentes, mantém a última marca completa com sua data original e bloqueia operações. Não gera ponto patrimonial. Uma observação completa posterior resolve a ausência sem apagar o diagnóstico anterior. Não se interpola a curva nem apresenta consulta da interface como data da cotação.
