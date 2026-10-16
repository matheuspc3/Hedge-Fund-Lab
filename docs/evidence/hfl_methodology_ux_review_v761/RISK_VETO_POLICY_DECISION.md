# Política de veto de risco — análise para decisão humana

**Estado:** análise e recomendação. **Nenhuma política foi escolhida e nada foi
alterado.** O tratamento V2 selado continua com veto absoluto.

## 1. Implementação efetiva hoje

O veto nasce no Radar e é aplicado em três camadas, todas seladas:

| Camada | Onde | Regra | Código de erro |
|---|---|---|---|
| Origem do veto | `scripts/multiasset_radar.py` (regra `HARD_ASSET_VOLATILITY_RULE`) | volatilidade anualizada de 21 sessões > 50% → `VETADO`, sem chamar o Risk LLM | — |
| Política de risco V5 | `scripts/multiasset_portfolio.py`, `POLICY["veto_policy"] = "NO_OPERATION_ON_VETO; MISSING_OPINION_HOLD_ONLY"` (hash da política `5e7eac11…` selado nos contratos V1 e V2) | nenhuma operação em ativo vetado; sem parecer, só manter | — |
| Gestor V5 | `scripts/multiasset_manager.py:397-398` (SHA-256 `4caf6bf8…` selado) | qualquer operação (compra **ou venda**) em ativo `VETADO` | `individual_veto` |
| Validador Global PM V2 | `scripts/multiasset_global_pm_v2.py:454-459`, invariante I13; `VALIDATION["veto"] = "VETADO_NO_OPERATION_AND_NO_WEIGHT_INCREASE"` | qualquer operação, ou peso-alvo acima do atual | `vetoed_asset_allocation` |
| Prompt V2 | linha 34: "Risk individual VETADO: nenhuma operação e nenhum aumento de peso" | instrução ao modelo | — |

Comportamento observado na qualificação V7.6 (S5, validador V2 real):

| Caso | Resultado |
|---|---|
| comprar BBAS3 vetado, sem posição | rejeitado (`vetoed_asset_allocation`) |
| peso-alvo positivo sem operação | rejeitado |
| manter posição vetada (peso igual) | **válido** |
| aumentar posição vetada | rejeitado |
| **reduzir** posição vetada (vender 500 de 1000) | **rejeitado** |
| zerar posição vetada (vender 1000 de 1000) | **rejeitado** (verificado na V7.6.1 em memória, mesmo validador) |

## 2. Por que isso importa

O veto do Radar indica **risco individual excessivo** (volatilidade acima de
50%). Com o veto absoluto, uma carteira que já tem o ativo **não pode reduzi-lo
nem zerá-lo** justamente quando o risco ficou alto: o controle que deveria
proteger trava a exposição. Hoje isso não aparece nas inferências reais,
porque as duas partiram de 100% em caixa (S0). Passa a importar em qualquer
campanha com posições (C2, C4).

## 3. Três políticas

| | **A — Veto absoluto** (atual) | **B — Apenas redução** | **C — Redução condicionada** |
|---|---|---|---|
| Regra | nenhuma operação; peso-alvo ≤ atual | proibido comprar ou aumentar; **vender, reduzir e zerar permitidos** | como B, mas a venda só é admitida se condições adicionais forem satisfeitas |
| Vantagens | simples; já selado e testado; impede que o texto do modelo contorne o veto; nunca gera giro em ativo de risco | coerente com o sentido financeiro do veto ("não adicionar risco"); permite desalavancar quando o risco sobe; invariante simples e derivável | controla abusos (vender o vetado para financiar outra aposta, vendas parciais irrelevantes); pode exigir confirmação humana no paper |
| Desvantagens | trava exposição em ativo de risco alto; o gestor não pode reagir ao próprio sinal de risco | permite giro (venda do vetado + compra de outro ativo); exige revisar a interação com compras dependentes de liquidação | mais regras, mais códigos, mais testes; risco de parâmetros arbitrários sem evidência; mais difícil de explicar |
| Invariantes | I13 atual | I13′: em ativo `VETADO`, nenhuma compra e peso-alvo ≤ atual; vendas permitidas desde que custódia, custo e risco projetado passem (I16) | I13′ mais, por exemplo: (a) a venda reduz o peso do vetado; (b) o risco projetado global não piora; (c) `settlement_deferred` não usa recebível de venda vetada para comprar ativo com volatilidade maior; (d) motivo estruturado obrigatório |
| Riscos operacionais | exposição presa; ordens de saída impossíveis no paper futuro | vendas em ativo volátil com deslizamento; uso do veto como gatilho de giro | complexidade operacional; regras mal calibradas geram rejeições sem valor científico |
| Compatível com o contrato atual? | **sim** (é o atual) | **não**: muda I13, a regra do gestor V5 e o texto da política V5 | **não**: idem, com mais regras |
| Carteiras já posicionadas | posição congelada até o veto sair | posição pode ser reduzida ou zerada | reduzida/zerada sob condições |
| Testes afetados | nenhum | `test_global_pm_v2::test_09` permanece válido para V2; o novo tratamento precisa de casos próprios (S5 reduzir/zerar → válido; S5 comprar → rejeitado) | idem, mais um caso por condição |
| Versionamento científico | nenhum | **tratamento novo** | **tratamento novo** |

## 4. Recomendação técnica

1. **Não alterar a V2.** A campanha C1 (S0, 100% em caixa, sem posições) é
   indiferente entre A, B e C e pode seguir com a V2 como está.
2. **Para campanhas com posições (C2, C4), recomendar a política B** num
   tratamento novo, porque é a interpretação financeira usual de um veto de
   risco individual (bloquear aumento de risco, não a saída) e tem uma
   invariante simples e derivável. A política C só se justifica com
   evidência de abuso observada em B; adotá-la agora seria parametrizar sem
   dados.
3. **A decisão é humana.** Ela muda a política de risco e o contrato.

## 5. Plano de migração (se B for aprovada)

| Passo | Conteúdo | Selados intocados |
|---|---|---|
| 1 | Nova versão da política V5: `veto_policy = "NO_INCREASE_ON_VETO; REDUCTION_ALLOWED; MISSING_OPINION_HOLD_ONLY"`, com hash próprio | `multiasset_portfolio.py` V5 (baseline) |
| 2 | Novo módulo de gestor (ex.: `multiasset_manager_v2.py`) importando o V5 e trocando só a regra de veto | `multiasset_manager.py` |
| 3 | Novo tratamento `HFL-MULTIASSET-GLOBAL-PM-V3` (ou `V2-1`): prompt com a nova linha de veto; I13′; `ERRORS` completo (inclui os dois códigos sem descrição); contratos e diretório próprios | todo o V2 |
| 4 | Qualificação offline: matriz S0–S9 com expectativas do novo tratamento (S5 reduzir/zerar → válido) e mutações da guarda | — |
| 5 | Protocolo: nova versão listando o novo tratamento; V2 e V3 nunca no mesmo grupo de replicação | — |

**Custo de não decidir:** C2 e C4 ficariam com a política A, e qualquer
resultado sobre carteiras com posições vetadas herdaria a trava de exposição.
