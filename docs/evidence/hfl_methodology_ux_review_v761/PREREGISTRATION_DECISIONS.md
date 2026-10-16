# Decisões pendentes do pré-registro

Organiza todos os itens **[DECIDIR]** do
[PREREGISTRATION_DRAFT.md](../hfl_experimental_protocol_v76/PREREGISTRATION_DRAFT.md),
mais as decisões implícitas que a revisão encontrou. **Nenhuma escolha foi
preenchida, e o protocolo continua `QUALIFIED_OFFLINE`.** Cada decisão aprovada
entra numa versão nova do protocolo (1.1.0) antes do congelamento.

## Achado transversal: as 29 vagas da V2 são compartilhadas

O teto de US$ 5,00 está no `CONFIG` selado da V2 e vale para **todas** as
chamadas V1 + V2. Já há US$ 0,319488 reservados, e restam **29 chamadas no
total**, não 29 por campanha. Se C1 usar as 29, a campanha fora da amostra (C3)
não poderá usar o mesmo tratamento V2, e o teste mais importante contra a
ameaça de seleção posterior (V2 desenhada depois da falha da V1) ficaria sem
tratamento comparável. As decisões D1, D6 e D7 precisam ser tomadas juntas.

| n de C1 | Meia-largura 95% (p = 0,5) | Limite superior de rejeição se 0 em n | Reserva (US$) | Vagas V2 restantes para C3 |
|---|---|---|---|---|
| 10 | ±0,31 | 25,9% | 1,59744 | 19 |
| 19 | ±0,225 | 14,6% | 3,035136 | 10 (exatamente C3) |
| 29 | ±0,18 | 9,8% | 4,632576 | 0 |

---

## D1 — Tamanho da primeira campanha (C1)

| Opções | Fundamentação | Consequências |
|---|---|---|
| a) Piloto 10 e parar | barato; mede viabilidade operacional | precisão muito baixa; deixa 19 vagas |
| b) 19 em dois estágios (10 + 9) | precisão intermediária e preserva exatamente 10 vagas V2 para C3 | C1 e C3 com o mesmo tratamento; C1 menos preciso que 29 |
| c) 29 em dois estágios (10 + 19) | máxima precisão sob o teto | consome todas as vagas; C3 exigiria tratamento novo (novo teto) |
| d) 100 | precisão ±0,10 | exige tratamento novo (o teto é contratual) |

**Recomendação:** (b), 19 = 10 + 9, junto com C3 = 10 na V2. Prioriza ter
um teste fora da amostra com o **mesmo** tratamento, ao custo de precisão em C1.
**Efeito no pré-registro:** §10 e §11. **Aprovação humana:** sim.

## D2 — Replicações por grupo

| Opções | Consequências |
|---|---|
| a) um grupo (S0, contexto econômico de 09/10) | simples; mede só variabilidade do modelo |
| b) dois grupos (S0 em 09/10 e em outra sessão) | mistura variabilidade do modelo com a dos dados; consome vagas |

**Recomendação:** (a). A variabilidade entre sessões é o objeto de C3.
**Efeito:** §6, §10. **Aprovação:** sim.

## D3 — Regras do desenho em dois estágios

**Recomendação (para aprovar ou rejeitar):**
1. Tamanho de cada estágio fixado antes (10 e 9).
2. Entre estágios, só se revisa uma **lista de segurança**: integridade
   (`run_global_pm_v2.py status` sem exceção), ausência de `RECOVERY_REQUIRED`,
   `modelVersion` igual, preflight aprovado, orçamento.
3. As métricas de conformidade e variabilidade **não são calculadas nem
   olhadas** entre os estágios. Isso evita parada opcional pelo resultado.
4. O estágio 2 acontece se, e somente se, a lista de segurança passar.

**Alternativa:** estágio único de 19 (mais simples; perde a chance de
interromper por problema de infraestrutura com menos gasto). **Efeito:** §10, §12.
**Aprovação:** sim.

## D4 — Critérios de parada

Recomendação: só critérios de segurança, nunca de resultado. Integridade
falhou; `RECOVERY_REQUIRED`; mudança observada de `modelVersion` (encerra o
grupo); preflight recusado; contrato atual ≠ selado; orçamento autorizado
esgotado; incidente de infraestrutura com diagnóstico pendente. **Efeito:** §12.
**Aprovação:** sim.

## D5 — Tratamento de inferências inválidas

| Situação | Opção recomendada | Alternativa |
|---|---|---|
| `REJECTED_BY_VALIDATOR` (contrato, risco, schema) | conta no denominador de `global_validation_rate`; entra em `rejection_code_frequency`; fora das métricas de decisão | — (excluir seria viés) |
| Falha do provedor (`PROVIDER_FAILED`) | fora do denominador de conformidade; reportada em `provider_failure_rate`; **sem reposição** | repor uma vez por falha, dentro do teto (reduz vagas de C3) |
| Falha de infraestrutura / incerta | idem; recuperação só por replay; sem reposição | idem |
| Resposta válida com texto livre sem suporte | continua `VALID_PROPOSAL`; auditoria textual separada, por rubrica | — |

**Efeito:** §9, §13. **Aprovação:** sim.

## D6 — Limites de orçamento

**Recomendação:** limite humano por campanha igual à reserva planejada (C1 =
US$ 3,035136 com 19; C3-GPM = US$ 1,59744), mais autorização de orçamento
Radar para C3 (comitês: US$ 33,1776 de reserva; exposição agregada do Radar já
acima do teto local). Nenhuma reserva antiga é liberada. **Efeito:** §11.
**Aprovação:** sim, obrigatória.

## D7 — Alocação das vagas V2 entre campanhas

Decorre de D1: (b) → C1 19 + C3 10 + 0 de folga. (c) → C1 29, e C3 com
tratamento novo. **Recomendação:** (b). **Aprovação:** sim.

## D8 — Taxa livre de risco (métricas futuras da dimensão E)

| Opções | Fundamentação | Consequências |
|---|---|---|
| a) CDI diário (série oficial do Banco Central) | custo de oportunidade realista no Brasil; essencial quando a decisão predominante é ficar em caixa | exige obter a série no futuro (rede) e fixar o hash; o ledger paper rende zero, então a comparação explicita esse custo |
| b) zero | simples, sem fonte externa | subestima o custo de oportunidade do caixa; Sharpe incomparável com a literatura brasileira |

**Recomendação:** (a), com a fonte e o hash da série registrados antes do uso,
e (b) como análise de sensibilidade. **Efeito:** §8. **Aprovação:** sim.

## D9 — Métrica primária da avaliação prospectiva (Q4)

| Opções | Consequências |
|---|---|
| a) diferença de retorno acumulado contra `SIGNAL_RULE_DETERMINISTIC` (mesma informação) | isola o efeito "gestor LLM × regra simples" |
| b) contra `ALWAYS_CASH` | mede só "investir × não investir" |
| c) Sharpe | instável com 20 sessões; indefinido para caixa |

**Recomendação:** (a), descritiva, com intervalo por bootstrap pareado em
blocos rotulado exploratório; nenhuma afirmação confirmatória com 20 sessões.
**Efeito:** §8, §13. **Aprovação:** sim.

## D10 — Controle `FIXED_WEIGHTS`

| Opções | Consequências |
|---|---|
| a) mix constante 17% × 5 + 15% caixa, rebalanceado na frequência das decisões | difere do buy and hold só pelo rebalanceamento; isola o efeito de "tempo" × alocação estática |
| b) remover o controle | menos comparações múltiplas; perde essa leitura |
| c) pesos arbitrários (ex.: 40/30/…) | arbitrário sem justificativa |

**Recomendação:** (a). **Efeito:** §4. **Aprovação:** sim.

## D11 — Política de veto para campanhas com posições

Ver [RISK_VETO_POLICY_DECISION.md](RISK_VETO_POLICY_DECISION.md). Não afeta C1
nem C3 (S0). **Recomendação:** política B num tratamento novo, antes de C2/C4.
**Aprovação:** sim.

## D12 — Mudança de versão do modelo no provedor

**Recomendação:** se o `modelVersion` do envelope mudar, o grupo de replicação
fecha; as tentativas seguintes formam um grupo novo, relatado separadamente.
**Efeito:** §12. **Aprovação:** sim.

---

## Condições para congelar (`FROZEN_FOR_FUTURE_EVALUATION`)

1. Decisões D1–D12 registradas por humano.
2. Protocolo 1.1.0 gerado com as decisões (o 1.0.0 não é sobrescrito).
3. Erratas `ERRATUM-HFL-2026-001/002` ratificadas ou rejeitadas.
4. Revisão humana independente do pacote V7.6/V7.6.1 registrada no manifesto
   (`human_review`).
5. Validador do protocolo sem erros; testes do protocolo aprovados.
