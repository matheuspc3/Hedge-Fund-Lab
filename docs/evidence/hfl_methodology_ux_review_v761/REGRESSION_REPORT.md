# Regressão e triagem das 15 falhas

Consolida os entregáveis `REGRESSION_TRIAGE` e `REGRESSION_REPORT`. A
triagem detalhada, com a reprodução de cada falha, está em
[TEST_FAILURE_TRIAGE.md](../hfl_experimental_protocol_v76/TEST_FAILURE_TRIAGE.md)
(V7.6). Aqui se decide o que é seguro corrigir e o que depende de revisão.

## 1. Classificação

| Grupo | Testes | Causa (V7.6) | Correção segura possível? | Tipo de aprovação |
|---|---|---|---|---|
| PostgreSQL indisponível | 7 em `tests/pipeline/test_flows.py` | `init_db()` usa o `DATABASE_URL` do `.env` | **sim:** fixture que force SQLite temporário só nesses testes (comprovado: com `DATABASE_URL` de SQLite, 10/10 passam). Não toca dados nem regras científicas | operacional (altera `conftest` antigo) |
| Testes V7.3 com estado antigo | 2 em `tests/test_radar_runs.py` | afirmam 0 claims e plano 30/29 antes do lote pago | **sim, por versionamento:** testes novos que conferem o estado pré-lote pela evidência V7.3 e o pós-lote pelos claims; os antigos ficam marcados como históricos | metodológica leve (muda expectativa de teste de outra entrega) |
| Baselines operacionais de preservação | `test_global_pm.py::test_31`, `test_multiasset_portfolio.py::…preservation` | `job.json` e `last_prepare.json` (OPERATIONAL) mudaram por ação do operador | **só com mudança de critério:** exigir hash exato apenas do que `classify` marca como VIOLATION (proposta V7.3) | **metodológica** (critério de preservação histórica) |
| Divergências H2 | `test_cal_b4_safety`, `test_spec`, `test_v6_phase_routing` | mensagem de gate mudou; 2 estratégias `*_h2_proposed` no registro; gate de fase não levanta | **não nesta trilha** | **metodológica H2** (protocolo H2 v6) |
| Sensível ao estado do Git | `test_snapshot[code]` × `test_h2_v6_provisional` | par complementar (árvore limpa × suja) | **sim:** declarar a dependência e pular com motivo quando o estado do Git não for o exigido | operacional + H2 (um dos testes é H2) |

Nenhuma correção foi aplicada: todas mexem em testes antigos e precisam de
autorização. A suíte não fica verde artificialmente.

## 2. Revisão independente

A implementação e a auditoria da V7.5, da V7.6 e desta revisão foram feitas
pelo mesmo agente. Para as falhas classificadas como "metodológicas", e para o
congelamento do protocolo, a revisão humana independente é **requisito**, não
recomendação ([V76_READINESS_REVIEW.md](V76_READINESS_REVIEW.md) §4).

## 3. Execução desta entrega

Suíte completa com a árvore limpa: **1741 aprovados, 15 falhas** ([regression.txt](regression.txt)), as mesmas 15 da V7.6 (comparação nome a nome). 1741 = 1738 + 3 testes de `tests/test_review_v761.py`. Nenhuma falha nova; nenhuma envolve código da V7.6.1.
