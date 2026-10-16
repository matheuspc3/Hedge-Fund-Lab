# Desenho de repetibilidade do Global PM V2 (campanha C1)

Objetivo: medir a variabilidade do tratamento `HFL-MULTIASSET-GLOBAL-PM-V2` sob
condições controladas, sem alterar o tratamento selado. Nada aqui foi
executado.

## 1. Tratamento fixo

- Identidade, prompt (`GLOBAL_PM_PT_V2`), schema, `CONFIG` (modelo, opções,
  teto), política de validação e código: os mesmos do registro
  `v74-76d07c0d32444cecaf07e875deacb519` (contratos `159fd196…6590e2`).
- O validador do protocolo exige `contracts()["sha256"]` atual = selado. Se
  algo mudar, a campanha para e vira proposta de tratamento novo.
- O runner V2 (`scripts/run_global_pm_v2.py`) é usado como está: `prepare` →
  `preflight` → `run`, uma chamada, sem retry.

## 2. Controle experimental

| Fator | Como é preservado ou registrado | Garantia |
|---|---|---|
| Modelo | `requested_model` e `resolved_model` (journal); `modelVersion` e `responseId` no envelope bruto | registrado; o provedor **não** garante fixação de versão |
| Prompt | `PROMPT` no código selado; `system_prompt_sha256` e `user_prompt_sha256` por chamada | sistema: fixo; usuário: muda só em `record_id`, horários e hashes |
| Schema | `response_schema_sha256` = `974be1e2…` | fixo |
| Configuração | `config_sha256` = `3a3b0ca0…` | fixo |
| Temperatura | 1,0 (`CONFIG.options`) | fixa; amostragem estocástica por desenho |
| Thinking level | `low` | fixo; tokens de pensamento podem não ser informados |
| Semente | **não suportada** pelo runner V2 | limitação; variabilidade não controlável por semente |
| Contexto financeiro | carteira hipotética R$ 100.000 em caixa (S0); preços = `raw_close` dos pareceres | igual por construção; `economic_fingerprint` confere |
| Pareceres Radar | os 5 `result.json` de `radar-2026-10-09-recovery-01` (hashes no `opinion_refs`) | imutáveis; origem `VERIFIED` exigida pelo preflight |
| Preços | constantes hipotéticos | fixos |
| Sessão dos dados | 09/10/2026 | fixa |
| Políticas de risco e alocação | `risk_policy_sha256` `5e7eac11…`, `allocation_policy_sha256` `1a542d6a…` | fixas, no contrato |
| Orçamento | reserva US$ 0,159744 por tentativa; teto selado US$ 5,00 (V1 + V2) | verificado pelo preflight |
| Timestamps | `created_at`, `expires_at` (24 h), `claim.created_at`, `started_at` | registrados; diferem por tentativa |
| Bibliotecas | `poetry.lock` e `pyproject.toml` com hash selado nas fontes do contrato | fixas; a versão do Python deve ir para o registro da campanha |
| Contratos e hashes | `contracts.sources_sha256` (código, lock, calendário) | fixos |

## 3. Replicações independentes

**Cada tentativa é um registro novo do runner V2**, com:

- identidade própria: `--id v76-<campanha>-20261009-r<k>`, por exemplo
  `v76-c1-pilot-20261009-r001` (determinística; o
  `prepare` recusa raiz já usada);
- contexto próprio (24 h de validade), preflight e token próprios;
- autorização, claim, journal e reserva individuais;
- resultado imutável (`result.json`) ou falha selada (`failure.json`);
- nenhuma reutilização de claims: o preflight recusa um registro já
  reivindicado (`already_claimed_replay_only`);
- nenhum retry pago automático (`http_attempts_max = 1`); recuperação só por
  replay do journal, sem nova chamada;
- associação ao mesmo tratamento (identidade e contratos) e ao mesmo cenário
  (`replication_group`, `economic_fingerprint`).

**Identidade de contexto × identidade de tentativa × input econômico.**
`context_sha256` muda a cada tentativa, porque o contexto sela `record_id` e
horários. O input econômico é comparável pelo `economic_fingerprint`. A
qualificação offline congelou dois contextos com registros e horários
diferentes: os hashes diferem e as impressões coincidem
(`READINESS_REPORT.json → qualification.replication_identity`). O protocolo
**não** afirma que as chamadas recebem bytes idênticos: o prompt de usuário
contém o `record_id`, os horários e os hashes.

**Limites do runner atual.** O contexto expira em 24 h, então cada tentativa
precisa de `prepare` próprio, o que já é o desejado. O `prepare` oficial só
aceita carteira em caixa (`--capital`), sem posições: os cenários S1–S9 em
campanha real exigem um caminho de preparo novo (fora dos arquivos selados),
revisado antes de C2. Execuções devem ser sequenciais: há trava de processo
por identidade.

## 4. Tamanho amostral

O alvo é **precisão** da proporção de respostas conformes (`global_validation_rate`),
não poder estatístico para um efeito, porque não há comparação de tratamentos
em C1.

| n | Meia-largura 95% (aprox. normal, p = 0,5) | Wilson 95% se n/n válidas | Limite superior 95% da taxa de rejeição com 0 rejeições | Reserva (US$) | Piso de ref. (US$) | Situação |
|---|---|---|---|---|---|---|
| 10 (piloto) | ±0,31 | [0,72; 1,00] | 25,9% | 1,59744 | 0,25 | cabe no teto |
| 29 (intermediária) | ±0,18 | [0,88; 1,00] | 9,8% | 4,632576 | 0,72 | **máximo** sob o teto selado |
| 100 (ampliada) | ±0,10 | [0,96; 1,00] | 3,0% | 15,9744 | 2,49 | **bloqueada**: excede o teto selado |

Leitura: com 10 tentativas, mesmo sem nenhuma rejeição, uma taxa de rejeição de
até ~26% é compatível com os dados. Com 29, até ~10%. O tamanho que cabe sem
novo tratamento (29) dá precisão modesta; isso é declarado, não escondido.

**Recomendação para o pré-registro:** n = 29 em dois estágios fixados antes de
começar, 10 + 19. Entre os estágios só se avalia segurança (integridade,
infraestrutura, orçamento), nunca o resultado. Não há parada opcional pelo
resultado. O total não ultrapassa o teto selado. A campanha ampliada só com
tratamento novo (por exemplo, V2 com outro teto, identidade própria) ou com
decisão metodológica registrada.

**Orçamento planejado × cobrança efetiva.** A reserva é o teto conservador
(entrada máxima de 65.536 bytes a 1 token/byte e 8.192 tokens de saída, a
preços altos); o piso de referência é a média dos pisos observados (US$ 0,0249
por chamada). A cobrança efetiva só é conhecida pela fatura do provedor.
Nenhuma campanha paga é executada na V7.6.

## 5. Regras de interrupção (segurança, não resultado)

1. Integridade falhou num registro (`run_global_pm_v2.py status` levanta
   exceção) → parar e investigar.
2. `RECOVERY_REQUIRED` ou falha de infraestrutura → parar; recuperar só por
   replay.
3. Mudança observada de `modelVersion` → encerrar o grupo de replicação;
   tentativas posteriores formam outro grupo.
4. Preflight recusado (orçamento, origem Radar, validade) → parar.
5. Contrato atual ≠ selado → parar.

## 6. Métricas de C1

`global_validation_rate`, `structural_validity_rate`, `rejection_code_frequency`,
`no_operation_rate`, `target_weight_l1_dispersion`, `cash_weight_dispersion`,
`action_agreement`, `watchlist_stability`, `structured_justification_variation`,
`raw_intent_agreement` (à parte), `provider_failure_rate`,
`infrastructure_failure_rate`, `usd_observed_lower_bound`. As definições estão
em [METRIC_CATALOG.json](METRIC_CATALOG.json).
