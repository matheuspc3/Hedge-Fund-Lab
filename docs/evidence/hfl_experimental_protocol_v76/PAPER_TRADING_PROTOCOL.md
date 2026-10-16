# Protocolo de paper trading multiativo (futuro)

Especificação para campanhas futuras (C4 e, em modo descritivo, C3). **Nenhum
lançamento foi feito na V7.6.** O ledger paper multiativo não existe; sua
implementação é um requisito (`PAPER_LEDGER_NOT_IMPLEMENTED`) que precisa de
revisão própria antes de qualquer campanha.

## 1. Cinco estados que não se confundem

| Estado | Quem produz | Efeito |
|---|---|---|
| **Proposta consultiva** | Global PM (LLM) | intenção de alocação; nenhum efeito |
| **Validação** | validador V2 + motor V5 (determinísticos) | `VALID_PROPOSAL` ou rejeição; nenhum efeito |
| **Autorização humana** | operador, por campanha e etapa | permite lançar *aquela* proposta validada no ledger paper; registrada com hash da proposta |
| **Execução paper** | motor de simulação, regras abaixo | lançamento simulado no ledger paper |
| **Execução real** | — | **fora do escopo e desabilitada** (`execution_enabled: false`, `CONSULTATIVE_ONLY_V1`) |

Uma proposta rejeitada nunca é lançada. Uma proposta validada só é lançada com
autorização humana específica. Aprovações do H2 não valem aqui.

## 2. Separação de ledgers

- Raiz própria (proposta): `data/paper/hfl_multiasset_paper_v1/`, com
  identidade própria, nunca dentro de `data/forward/` (ledger H2 v6 + Buy &
  Hold) nem de `data/global_pm/`.
- Cada lançamento referencia `record_id`, `context_sha256` e `result.sha256` da
  proposta e o hash da autorização.
- O ledger H2 v6 e o ledger multiativo nunca compartilham caixa, posições,
  aprovações ou métricas.

## 3. Regras de simulação (propostas para congelamento)

| Elemento | Regra |
|---|---|
| Capital inicial | R$ 100.000,00 em caixa liquidado |
| Posições | quantidades inteiras; custo médio pela regra do motor V5 (`BASIS_AUTHORITY`) |
| Caixa liquidado | único financiador de compras sem dependência |
| Caixa reservado | reservado no lançamento da ordem (preço-limite × quantidade + custo); liberado se a ordem não for preenchida |
| Recebíveis | vendas geram recebível em D+2 pelo calendário B3 (`B3_CASH_EQUITIES_D+2_OC041_2026_CONFIRMED`); recebível não é caixa disponível até a liquidação confirmada |
| Compras dependentes | só executadas após a liquidação da venda de que dependem (`funding_source = SETTLEMENT`) |
| Custos e tarifas | política didática congelada: `fee_rate` 0,1% por execução; sem modelo de imposto (`PRE_IR_NOT_A_TAX_MODEL`) |
| Preço de referência da decisão | fechamento oficial (COTAHIST) da sessão t |
| Execução hipotética | ordem enviada para a **abertura oficial de t+1** (COTAHIST); nenhum dado de t+1 entra na decisão |
| Deslizamento | 10 pb adversos sobre a abertura (proposta; fixada no pré-registro) |
| Ordens não preenchidas | compra não preenchida se abertura × (1 + deslizamento) > preço-limite; venda, se abertura × (1 − deslizamento) < preço-limite; ativo sem negócio em t+1 → não preenchida; tudo registrado, reserva liberada |
| Corporate actions | eventos oficiais da B3 aplicados pela regra do motor V5 (proventos como renda líquida na data de pagamento; desdobramento/bonificação ajustam quantidade); evento não resolvido → sessão interrompida, sem lançamento |
| Marcação a mercado | fechamento oficial de cada sessão |
| Resultados | realizado (vendas) e não realizado (marcação), pelo motor V5 |
| Limites | os mesmos da política V5 (concentração 40%, exposição 85%, giro, custo, operações ≤ 10) checados antes do lançamento |

## 4. Fluxo por sessão (C4)

1. Após o fechamento de t: Radar (5 comitês) → Global PM V2 → validação.
2. Antes da abertura de t+1: autorização humana do lançamento (ou registro de
   "sem lançamento"); hash da proposta e da autorização em commit local.
3. Abertura de t+1: execução paper pelas regras da seção 3.
4. Fechamento de t+1: marcação; nova decisão parte do estado do ledger.

Uma sessão sem decisão válida mantém a carteira, sem operação, e registra a
falha. Nenhuma decisão é refeita depois de conhecida a abertura.

## 5. O que este protocolo não autoriza

Ordens reais, carteiras prospectivas com dinheiro real, reaproveitamento de
aprovações H2, ou qualquer lançamento antes do congelamento do protocolo e da
autorização humana da campanha.
