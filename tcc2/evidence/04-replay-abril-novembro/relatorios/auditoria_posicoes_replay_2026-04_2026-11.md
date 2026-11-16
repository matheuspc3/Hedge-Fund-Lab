# Posições, saídas e cobertura dos agentes no replay de abril a novembro

15/11/2026 · DP-01/DP-07/DP-24/DP-37 · REPLAY-01.

Escopo: investigar a trajetória já executada de 06/04 a 12/11/2026, coletar
os dados existentes e procurar ativos abandonados, omissões e inconsistências.
Não houve nova inferência, alteração de parâmetros, operações ou publicação.

**Resultado: VALE3 foi zerada em 01/07 e não voltou até 12/11. Entretanto,
nenhum dos cinco ativos deixou de ser analisado ou enviado ao gestor.**
O caso de VALE3 é uma sequência de decisões de não comprar, e não a reprodução
do antigo problema de excluir do universo os ativos com posição zero.

## Quantas vezes houve posicionamento

Uma compra pode aumentar uma posição existente; não é necessariamente uma
reentrada. Aqui, “período posicionado” começa na entrada inicial comum ou na
passagem de zero para quantidade positiva. “Saída” significa zerar toda a posição.
Compras e vendas abaixo são operações executadas após a inicialização, não votos
dos analistas nem ações HOLD do gestor. A cesta inicial foi imposta ao experimento,
não escolhida pelos agentes.

| Ativo | Compras posteriores | Vendas | Períodos posicionado, incluindo inicial | Saídas completas | Reentradas | Pregões com posição no fechamento / 153 | Quantidade final |
|---|---:|---:|---:|---:|---:|---:|---:|
| BBAS3 | 4 | 6 | 3 | 2 | 2 | 76 | 13 |
| ITUB4 | 10 | 6 | 3 | 2 | 2 | 74 | 380 |
| PETR4 | 10 | 6 | 2 | 1 | 1 | 133 | 920 |
| VALE3 | 8 | 7 | 1 | 1 | 0 | 59 | 0 |
| WEGE3 | 18 | 11 | 4 | 3 | 3 | 109 | 430 |

Total: **50 compras e 36 vendas posteriores**, mais cinco compras iniciais.
Não há short. Ações BUY/SELL do gestor coincidem com as 86 operações posteriores,
inclusive quantidades; nenhuma diferença de execução foi encontrada nesse cruzamento.

| Ativo | Saída completa | Reentrada | Pregões zerado |
|---|---|---|---:|
| BBAS3 | 28/04 | 22/07 | 59 |
| BBAS3 | 13/08 | 09/09 | 18 |
| ITUB4 | 07/05 | 26/06 | 35 |
| ITUB4 | 14/08 | 19/10 | 44 |
| PETR4 | 23/06 | 21/07 | 20 |
| VALE3 | 01/07 | Não retornou até 12/11 | 94 |
| WEGE3 | 06/05 | 19/06 | 31 |
| WEGE3 | 21/07 | 27/07 | 4 |
| WEGE3 | 22/10 | 05/11 | 9 |

Contagem inclui o fechamento do dia da saída e exclui o dia da reentrada.
“Não voltou” se limita ao fim desta campanha, não afirma comportamento futuro.

## VALE3 continuou sendo considerada

Em 01/07 o gestor pediu a venda das 79 ações restantes, por enfraquecimento
técnico. A referência da proposta era R$ 77,88; o registro executado usa a
abertura RAW de R$ 77,09. São instantes distintos, não uma divergência contábil.

Nos 93 pregões seguintes à saída, VALE3 teve 52 recomendações de VENDA,
27 de MANTER e **14 de COMPRA**. Todas as 14 compras foram aprovadas pelo risco;
o gestor respondeu HOLD em todas. VALE3 não teve nenhum veto de risco no período inteiro.

As oportunidades de recompra ocorreram de **25/08 a 14/09**:

- Nos primeiros 12 pregões dessa sequência, havia caixa para uma ação aos preços
  de referência, incluindo a taxa de 0,03%, antes de outras operações da cesta.
  Caixa: R$ 144,46, depois R$ 155,12, chegando a R$ 87,78 em 10/09.
- Em 11/09 e 14/09, os R$ 21,76 disponíveis não compravam uma ação.
- O gestor justificou evitar posições pequenas, preservar liquidez e não vender
  os demais ativos sem sinal de VENDA. O prompt efetivamente exige parecer VENDA
  para vender e COMPRA para comprar; não permite liberar caixa arbitrariamente.

Há uma **inconsistência de justificativa a investigar**: o gestor fala em
“custo transacional desproporcional”, “ineficiência” e “lote” ao recusar uma ação
de VALE3. O contrato aceita ações inteiras e cobra uma taxa proporcional de 0,03%,
sem custo fixo nem lote mínimo de 100 ações informado. Uma ação de aproximadamente
R$ 79 teria custo aproximado de R$ 0,02. Preservar caixa e evitar posição irrelevante
é uma escolha permitida; alegar uma barreira de custo/lote não estabelecida não
é uma restrição do motor.

O contraste aparece em **09/09 e 10/09**: o gestor comprou três ações de BBAS3
em cada dia, com desembolsos de referência de aproximadamente R$ 67,80 e R$ 66,54,
enquanto recusava uma ação de VALE3, de aproximadamente R$ 79. Isso não prova
que a recompra seria melhor; mostra que a preferência por tamanho/caixa não foi
aplicada com uma regra quantitativa uniforme explícita.

Fontes detalhadas: `sinais_e_decisoes.csv`, `compra_sem_reentrada.csv` e os
`user_prompt`/`raw_response` das chamadas `global_portfolio_manager` dessas datas.

## Os 5 achados empíricos que explicam o desempenho do replay v1

A consolidação dos CSVs e JSONs revela cinco mecanismos estruturais e comportamentais que explicam por que a carteira `MULTIAGENT` terminou com `-17,82%` (R\$ 82.178,71) contra `-11,21%` do Buy & Hold (R\$ 88.791,11) e `+4,89%` de Bollinger 20/2 (R\$ 104.887,05):

### Achado 1 — Trava de caixa e impossibilidade de rebalancear ativos em `MANTER` (`VALE3` 94 pregões fora; `ITUB4` 27 sinais de compra ignorados)
Em `dashboard/wallet_manager_api.py::compile_proposal`, a validação exige `recommendation == "VENDA"` para autorizar qualquer redução (`SELL`), e `recommendation == "COMPRA"` para qualquer compra (`BUY`).
- Depois de sair de `VALE3` (`01/07`), `BBAS3` (`13/08`) e `ITUB4` (`14/08`), o gestor concentrou quase todo o capital em `PETR4` e `WEGE3`, deixando o caixa livre abaixo de R\$ 200 em **69 dos 153 pregões**.
- Como `PETR4` e `WEGE3` permaneciam em `MANTER` ou `COMPRA`, o gestor ficou proibido pela regra de validação de vender parcialmente uma posição sobrealocada (como `PETR4` com >60% da carteira) para financiar novas entradas:
  - **`VALE3` zerada (`01/07` a `12/11` — 94 pregões):** recebeu **14 sinais aprovados de `COMPRA`** (`25/08` a `14/09`), todos respondidos com `HOLD` por falta de caixa relevante, e nunca mais retornou à carteira.
  - **`ITUB4` zerada (`14/08` a `16/10` — 44 pregões):** recebeu **27 sinais aprovados seguidos de `COMPRA`** (`03/09` a `16/10`) respondidos com `HOLD` (caixa entre R\$ 15,26 e R\$ 155,12), só conseguindo reentrar no 28º sinal (`19/10`) quando `WEGE3` finalmente teve parecer `VENDA` e liberou caixa.

### Achado 2 — Compra no topo e venda no fundo sistemática ("whipsaw" pró-cíclico atrasado)
Em **quatro dos cinco ativos** (`WEGE3`, `ITUB4`, `VALE3`, `PETR4`), o preço médio de compra da `MULTIAGENT` pós-D0 foi **superior** ao preço médio de venda — comportamento oposto ao da estratégia `BOLLINGER_20_2` (`precos_medios_compra_venda.csv`):

| Ativo | Qtd comprada (`MULTIAGENT`) | Preço médio COMPRA (`MULTIAGENT`) | Qtd vendida (`MULTIAGENT`) | Preço médio VENDA (`MULTIAGENT`) | Preço médio COMPRA (`BOLLINGER_20_2`) | Preço médio VENDA (`BOLLINGER_20_2`) | Resultado `MULTIAGENT` R$ | Resultado `BUY_HOLD` R$ | Resultado `BOLLINGER_20_2` R$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **WEGE3** | 2.383 | **R$ 47,41** | 2.350 | **R$ 44,79** | R$ 45,85 | R$ 49,08 | **-5.443,38** | +603,40 | **+5.454,99** |
| **ITUB4** | 1.070 | **R$ 44,07** | 1.151 | **R$ 40,61** | R$ 41,04 | R$ 43,04 | **-4.527,86** | -555,18 | **+2.433,76** |
| **VALE3** | 710 | **R$ 83,46** | 949 | **R$ 78,85** | R$ 70,28 | R$ 81,12 | **-4.433,08** | -4.255,30 | **+592,99** |
| **PETR4** | 1.620 | **R$ 44,77** | 1.115 | **R$ 42,81** | R$ 47,90 | R$ 41,20 | **-1.783,77** | -443,38 | **-3.553,45** |
| **BBAS3** | 713 | **R$ 20,99** | 1.555 | **R$ 21,31** | R$ 19,59 | R$ 22,50 | **-1.633,20** | -6.558,43 | **-41,24** |
| **Total** | — | — | — | — | — | — | **-17.821,29** | **-11.208,89** | **+4.887,05** |

As features médias nos 765 pareceres (`verificacao.json`) mostram a causa:
- **`COMPRA` (`273` casos):** emitida após o ativo já ter esticado, com **RSI médio de `63,17`**, `sma50_gap = +7,82%`, `sma200_gap = +13,72%` e preço próximo à banda superior de Bollinger (`bb_upper_gap = -2,51%`).
- **`MANTER` (`269` casos):** **RSI médio de `47,81`**, `sma50_gap = -1,13%`.
- **`VENDA` (`223` casos):** emitida após quedas acentuadas, com **RSI médio de `35,07`**, `sma50_gap = -8,64%`, `sma200_gap = -5,93%` e preço próximo à banda inferior de Bollinger (`bb_lower_gap = +3,38%`).
- O caso mais severo foi **`WEGE3`**: o papel subiu no período (`R$ 50,31 → R$ 51,65`, rendendo `+R$ 603,40` no Buy & Hold e `+R$ 5.454,99` no Bollinger), mas a `MULTIAGENT` perdeu `-R$ 5.443,38` comprando topos e vendendo correções em três ciclos seguidos.

### Achado 3 — Veto de risco (`HARD_ASSET_VOLATILITY_RULE`) bloqueando saídas (`VENDA`)
O prompt determina `"Ativo VETADO: HOLD obrigatório"` e `multiasset_radar.py::committee` converte qualquer parecer vetado em `"MANTER"`. Dos 41 vetos (25 `BBAS3`, 12 `ITUB4` e 4 `PETR4`; 40 determinísticos por volatilidade anualizada de 21 dias > 50% e 1 do modelo LLM em `PETR4` em `06/10`), **25 pares ativo/pregão** tinham consenso técnico de **`VENDA` com posição aberta**, mas foram forçados a `MANTER`/`HOLD`:

| Ativo | Sinais de VENDA bloqueados com posição aberta | Datas | Quantidade preservada nesses dias |
|---|---:|---|---:|
| BBAS3 | 12 | 27/10–12/11 | 13 |
| ITUB4 | 12 | 27/10–12/11 | 380 |
| PETR4 | 1 | 05/11 | 1.220 |

Ou seja, quando a volatilidade explodiu acima de 50% e os analistas votaram `VENDA` (5/5 em `ITUB4` e `BBAS3`, 3/5 em `PETR4`), o filtro de risco impediu a redução de exposição (a proposta `R7` de `PILOTO_MULTIATIVOS_SPEC.md` ainda não estava ativa).

### Achado 4 — Concentração extrema (até 77,49% em um ativo) e compras residuais ("poeira")
Sem limite máximo de peso por ativo nem piso mínimo por ordem na carteira pessoal (`DP-24`):
- Em **101 dos 153 pregões (`66,01%` da campanha)**, a carteira detinha **apenas 2 ativos com participação relevante** ($\ge 2\%$ do patrimônio), mantendo 5 ativos em apenas 15 pregões, 4 ativos em 8 pregões e 3 ativos em 29 pregões.
- Pesos máximos atingidos no fechamento: **`VALE3` chegou a `77,49%`** em `03/06` (849 ações = R\$ 69.439,71 de R\$ 89.608,05, logo antes de cair e zerar), **`PETR4` atingiu `71,40%`** em `30/10` (1.220 ações) e **`WEGE3` atingiu `66,05%`** em `06/07` (1.250 ações).
- No extremo oposto, o gestor utilizou sobras de proventos para compras residuais sem efeito econômico: `3`, `3` e `7` ações de `BBAS3` em setembro (`13` ações = R\$ 201,24 finais, `0,25%` da carteira) e `11` ações de `WEGE3` em `27/07`.

### Achado 5 — Falta de diversidade real no comitê técnico (`83,01%` de unanimidade `5x0`)
Dos 765 pareceres ativo/pregão (`votos_individuais.csv` e `verificacao.json`):
- **635 (`83,01%`) foram unânimes `5 a 0`** (`237` vezes `5 COMPRA`, `203` vezes `5 MANTER` e `195` vezes `5 VENDA`), e em **0 dos 765 casos** houve ausência de consenso ou voto cruzado entre `COMPRA` e `VENDA` no mesmo pregão.
- Isso decorre de os 5 analistas usarem o mesmo modelo (`gemini-3.8-flash`), o mesmo `TECHNICAL_SYSTEM_PROMPT_V5` e os mesmos 7 `allowed_evidence_codes` binários, diferenciando-se apenas pela `seed` (`10001` a `10005`) em `temperature=1.0`. Sem diversidade de ótica (tendência vs reversão à média), os 5 analistas atuam como um único classificador de tendência atrasado.

## Votos, recomendações e cobertura

Cada ativo teve cinco votos técnicos por pregão: 765 votos por ativo, 3.825 no total.
Os votos individuais e suas confianças estão em `votos_individuais.csv`.
Consenso técnico antes do risco e recomendação encaminhada depois do risco
são campos distintos em `sinais_e_decisoes.csv`.

| Ativo | Consenso técnico COMPRA / MANTER / VENDA | Após risco COMPRA / MANTER / VENDA |
|---|---|---|
| BBAS3 | 38 / 46 / 69 | 29 / 67 / 57 |
| ITUB4 | 59 / 48 / 46 | 59 / 60 / 34 |
| PETR4 | 70 / 74 / 9 | 69 / 76 / 8 |
| VALE3 | 35 / 59 / 59 | 35 / 59 / 59 |
| WEGE3 | 71 / 42 / 40 | 71 / 42 / 40 |

Verificados: **765 análises ativo/pregão**, os cinco ativos em todos os 153
prompts e respostas do gestor, inclusive posições zeradas; 3.825 chamadas
técnicas, 725 de risco e 153 do gestor = 4.703 chamadas lógicas.
As 40 chamadas de risco dispensadas correspondem aos vetos determinísticos,
não a ativos esquecidos. O relatório histórico registra 4.709 tentativas físicas,
com seis retries; esta auditoria não refez a auditoria do transporte/orçamento.

## Dados coletados, reprodução e limites

Pasta de trabalho: [output/auditoria-replay-20261115](../output/auditoria-replay-20261115/).
`originais/` contém cópias byte a byte dos cinco CSVs da interface:
estados diários (918 linhas), operações (175), decisões de regras (608),
proventos pagos (97) e chamadas (4.703), além de `explorer.json`, `calls.json`
e `manifest.json`. Os CSVs originais abrangem as seis carteiras.
`decisions.csv` contém decisões das regras determinísticas, não todos os
pareceres da IA; os novos CSVs de sinais/votos cobrem essa distinção.
Recebíveis ainda não pagos estão no JSON e na atribuição, não no CSV de pagamentos.

Derivados: `posicoes_por_ativo.csv`, `saidas_e_retornos.csv`,
`operacoes_classificadas.csv` (seis carteiras), `cobertura_diaria.csv`,
`sinais_e_decisoes.csv`, `votos_individuais.csv`, `compra_sem_reentrada.csv`,
`atribuicao_contabil.csv` (seis carteiras), `posicoes_diarias.csv`,
`precos_medios_compra_venda.csv` e `verificacao.json`. Os demais derivados focam Multiagentes.

Reproduzir na raiz do repositório:

```powershell
.venv/Scripts/python.exe scripts/audit_replay_positions.py
```

**Verificação PASS:** hash do pacote portátil confere com o backup registrado;
hashes dos prompts conferem; respostas brutas do gestor conferem com as propostas;
as operações posteriores conferem com as ações propostas. Reconstrução independente
de quantidades, caixa, custos e identidade patrimonial dos **918 estados diários**;
atribuição final dos seis livros reconciliada; CSVs de estados/operações/chamadas
cruzados com o JSON. Nenhum saldo negativo ou posição negativa encontrado.
O script usa somente biblioteca padrão, lê o arquivo preservado e escreve apenas
na pasta de derivados. Os asserts são o check reproduzível desta análise.

Não foram revalidados contra fornecedores externos os preços, fatores e eventos,
nem recalculados do zero todos os direitos a proventos ou a auditoria do orçamento.
Recebíveis usados na reconciliação vêm da exportação existente. O resultado
exploratório mantém os limites originais: reconstrução retrospectiva, ausência
de arquivo point-in-time, possível contaminação do modelo e execução simulada.
Os JSONs de chamadas são completos como exportados pela interface; envelopes
HTTP/tentativas físicas e bancos originais permanecem no arquivo de evidências.

---

## Plano de melhoria para o Replay Abril–Novembro v2 (`REPLAY-02`)

Objetivo solicitado por Lucas em 15/11/2026: **preservar integralmente o Replay Abril–Novembro v1 (`REPLAY-01`) como linha de base (`baseline`)** e construir uma **versão v2 (`REPLAY-02`)** sobre os mesmos 153 pregões (`06/04/2026` a `12/11/2026`), os mesmos preços B3 RAW / proventos e as mesmas cinco referências determinísticas (`BUY_HOLD`, `SMA_50_200`, `BOLLINGER_20_2`, `EQUAL_WEIGHT_63`, `MIN_VARIANCE_252_63`), permitindo comparar diretamente **Multiagentes v1 vs Multiagentes v2** no TCC e na interface `/laboratory/replay/`.

### Preservação e isolamento arquitetural (`v1` vs `v2`)
- **Imutabilidade do v1:** `data/replays/april-november-2026-flash/`, `output/replay-continuo-20261113/` e os 76 arquivos verificados por `frozen_sources()` permanecem intocados.
- **Identidade e raízes próprias do v2:** `IDENTITY = "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2"`, armazenamento isolado em `data/cache/continuous-replay/april-november-2026-flash-v2/` e pacote publicado em `data/replays/april-november-2026-flash-v2/` (ou curva comparativa `MULTIAGENT_V2` ao lado de `MULTIAGENT` no explorador).
- **Reuso determinístico:** os 765 snapshots de entrada (`inputs/`) e os livros das cinco referências determinísticas já qualificados no `v1` são reutilizados por hash, sem recalibrar estratégias de referência.

### Intervenções nos 4 gargalos identificados no v1

| Gargalo diagnosticado no v1 | Regra / contrato no v1 (causa raiz) | Mudança projetada para o v2 (`REPLAY-02`) | Efeito concreto esperado |
|---|---|---|---|
| **1. Trava de caixa e impossibilidade de rebalancear ativos em `MANTER`** (`VALE3` 94 dias fora; `ITUB4` 27 `COMPRA` ignoradas) | `compile_proposal` exige `recommendation == "VENDA"` para qualquer `SELL`. Sem sinal de `VENDA` nos ativos em carteira, o gestor fica sem caixa para comprar novos sinais `COMPRA`. | **Regra `Trim-to-Fund` (redução parcial de rebalanceamento):** permitir `SELL` parcial em ativo com recomendação `MANTER` (ou `COMPRA`) **somente** quando: (a) o ativo estiver acima do peso neutro (`> 25%` do patrimônio) e (b) o caixa gerado na mesma cesta for usado para financiar `BUY` de ativo aprovado com recomendação `COMPRA` (ou para reenquadrar excesso acima do teto), preservando piso mínimo de `15%–20%` no ativo reduzido. | Destrava a reentrada em ativos zerados com sinal `COMPRA` (como `VALE3` em ago/set e `ITUB4` em set/out) sem exigir que o restante da carteira entre em `VENDA`. |
| **2. Concentração extrema (até 77,49%) e compras de "poeira" (`3` ações)** | Sem teto de peso por ativo nem lote financeiro mínimo por ordem em `compile_proposal`. | **Limites determinísticos de carteira no Gestor v2:** (a) **Teto por ativo (`MAX_ASSET_WEIGHT = 30%` do patrimônio):** nenhuma compra (`BUY`) pode elevar o peso projetado (`weight_after`) de um ativo acima de `30%`; (b) **Mínimo econômico por operação (`MIN_TRADE_BRL = R$ 2.000,00` ou `2%` do patrimônio):** proibir compras residuais ("poeira"), exceto na liquidação integral (`SELL` total) de saldo remanescente. | Impede que a carteira fique concentrada em apenas 2 papéis (66% dos pregões no v1) e elimina compras de 3 ou 11 ações sem efeito econômico. |
| **3. Veto de volatilidade (`HARD_ASSET_VOLATILITY_RULE`) bloqueando `VENDA`** (25 casos com posição aberta) | `multiasset_radar.py::committee` converte `VETADO` em `MANTER` e `compile_proposal` exige `risk_verdict == "APROVADO"` inclusive para `SELL`. | **Implementação da Assimetria de Risco (`Proposta R7`):** quando `risk.verdict == "VETADO"` (volatilidade 21d > 50% ou veto LLM), bloquear **exclusivamente novas compras (`BUY`)**. Se o consenso técnico for `VENDA` e houver posição aberta (`quantity_before > 0`), preservar a elegibilidade de redução/saída (`SELL`). | Libera a defesa de patrimônio em quedas voláteis (como os 12 pregões de `5/5 VENDA` em `ITUB4` e `BBAS3` e o pregão `05/11` em `PETR4`). |
| **4. Homogeneidade do comitê (`83%` `5x0`) e compra de topo / venda de fundo (`RSI 63,2` vs `35,1`)** | Cinco analistas idênticos (`prompt_version=5`, mesma lista de códigos binários, variando só `seed`), agindo como seguidor de tendência atrasado em mercado lateralizado. | **Comitê v2 com diversidade de ótica e guarda de extremos (Tendência + Reversão à Média):** manter 5 votos estruturados e supermaioria `3/5` (`0.6`), mas dividir o quórum no adaptador v2 em lentes explícitas sobre as mesmas 8 features causais: **2 analistas de Tendência/Momentum** (`SMA50/200`, `MACD`, com cautela em sobrecompra), **2 analistas de Reversão à Média / Bandas de Bollinger & RSI** (penalizando compras com `RSI > 65` / `bb_upper_gap > -0.02` e evitando vendas no fundo com `RSI < 35` / `bb_lower_gap < 0.03`) e **1 analista de Regime/Equilíbrio** (`bb_width` + confluência). | Reduz a unanimidade artificial `5x0` e impede que o comitê compre sistematicamente topos esticados (`WEGE3` a R\$ 47,41) e venda fundos de correção (a R\$ 44,79). |

### Sequência de execução proposta para o v2
1. **Passo 1 — Especificação e adaptador isolado (`scripts/continuous_replay_v2.py`):** implementar os 4 ajustes em módulo adaptador próprio (via `bind`, sem tocar nos 76 arquivos selados do v1) e validar com teste offline determinístico (`--offline`, zero custo de API) cobrindo os 4 gargalos (`check_continuous_replay_v2.py`).
2. **Passo 2 — Ensaio curto de validação ou preflight completo:** verificar o comportamento dos 4 ajustes nas janelas críticas (ex.: junho/julho em `VALE3`/`WEGE3`, setembro em `VALE3`/`ITUB4` e outubro/novembro nos vetos de `ITUB4`/`PETR4`) e calcular o preflight de orçamento da campanha v2.
3. **Passo 3 — Execução autorizada da campanha `abril–novembro v2`:** após autorização explícita do teto de API por Lucas, rodar os 153 pregões na raiz `april-november-2026-flash-v2/`, exportar os mesmos 7 artefatos (`daily.csv`, `operations.csv`, `decisions.csv`, `dividends.csv`, `calls.csv`, `explorer.json`, `calls.json`) e disponibilizar a comparação lado a lado (`v1` vs `v2`) em `/laboratory/replay/`.
