# Regressão V7.6.5

Baseline local confirmado nos artefatos V7.6.4: 1765 passed, 14 failed, 61 subtests; Chrome 36/36. Nenhum baseline foi modificado. Lista de falhas conhecida: sete PostgreSQL indisponível, três expectativas H2/registro, duas preservações legadas operacionais e duas expectativas Radar. O teste de snapshot dependente de Git usa TEMP externo como na V7.6.4.

Qualificação direcionada e lint concluídos antes da regressão geral. Roteiros Chrome V7.6.4 adaptados à mudança autorizada de H2 para /paper (assertions de identidade/saldo/execução mantidas). Arquivos congelados durante a execução geral; saída em `.pytest_cache/` ignorada por Git, copiada para evidência depois. `out.json` do operador excluído apenas da consulta Git do processo de teste por configuração temporária; não editado, removido ou commitado.

Execução geral no commit `d91e5c5`: **1801 passed, 14 failed, 129 subtests passed em 1003,26 s (16 min 43 s)**. Saída integral `regression_final.txt`; comparação `regression_comparison.json`: `new_failures: []`, `baseline_not_repeated: []`. São precisamente as mesmas 14 falhas V7.6.4. Nenhum baseline/teste científico foi ajustado. A suíte geral permanece vermelha; a qualificação nova passa.

36 testes novos aprovados: 34 de ledger/leitura/mutações e dois HTTP/Chrome. 1801 = 1765 + 36; 129 subchecks = 61 + 68. Rodada direcionada final: **49 passed, 68 subtests passed em 125,49 s** (`targeted_final.txt`), incluindo monitoramento e Chrome V7.6.4. Coleta real final: **30/30**, blocked=[] e exceptions=[] (`ui_final.json`). Ruff check/format nos módulos novos, Ruff check nos arquivos Python alterados e node --check nos scripts JavaScript: aprovados.

Não houve edição durante a suíte. Depois dela, apenas documentação/resultados/roadmap e um comentário `ponytail` sobre o custo O(n) do replay; nenhuma lógica de runtime mudou. O comentário e os relatórios finais não exigem repetição da suíte completa; o lint final confere o estado entregue.
