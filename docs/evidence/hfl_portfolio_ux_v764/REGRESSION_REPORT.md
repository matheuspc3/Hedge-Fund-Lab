# Regressão

## Validações anteriores à suíte completa

- `targeted_initial.txt`: **55 passed, 23 subtests passed**, 346,97 s. Inclui Chrome V7.6.2/V7.6.3/V7.6.4, proteção V1, APIs e contratos H2.
- `adapter_final.txt`: **12 passed**, versão final do adaptador e HTTP.
- `ui_final.json`: **36/36**, zero requisições bloqueadas/tentativas de escrita e zero exceções.
- Ruff e `node --check`: aprovados. Primeiras tentativas pytest/Chrome no sandbox falharam por permissão Windows para temporários/spawn; execuções com permissão de processo passaram.

## Por que 15 falhas viraram 14 na V7.6.3

Conferidos `hfl_radar_ux_v763/regression_final.txt`, `regression_comparison.json`, `ui_checks_release.json` e relatórios V7.6.2. V7.6.3 registra 1752 passed, 14 failed, 61 subtests passed; Chrome 53/53. As 61 são subtestes pytest, não 61 interações Chrome adicionais.

A falha não repetida foi `tests/pipeline/test_snapshot.py::test_manifest_adulterado_e_rejeitado[code]`. Não houve correção desse teste ou do código científico. A mutação fixa `git_dirty=False` precisa mudar o manifest. `_build` usa `repository_dir=tmp_path`; `_git_metadata` executa Git nesse diretório. Temporário **dentro** do repositório herda os metadados da árvore; se limpa, já é False e a mutação não altera nada. Temporário **fora** retorna `git_commit=None, git_dirty=None`, então a mutação altera o valor. V7.6.2 usou `.pytest_cache/tmp`; V7.6.3 usou temporário externo exclusivo. Portanto a redução é compatível com mudança ambiental, não correção definitiva. Consulta direta nesta entrega confirmou workspace com Git e TEMP externo sem Git.

A reprodução controlada confirmou: **1 failed dentro da árvore limpa** (`code_inside_repository.txt`) e **1 passed fora** (`code_outside_repository.txt`), mesma versão e sem alterar código/teste científico. Trata-se de dependência ambiental do teste, não correção definitiva nem teste omitido. Nenhum teste científico foi modificado.

## Suíte completa

Primeira execução completa, commit `50094aa`: **1763 passed, 16 failed, 61 subtests passed**, 1034,94 s (17 min 14 s). Saída bruta intacta: `regression_initial.txt`.

14 falhas coincidem com o baseline V7.6.3. As duas novas eram:

1. `test_24_no_preservation_violation`: `dashboard/portfolio_api.py` é fixado por um baseline histórico. O adaptador não alterava comportamento financeiro, mas seus quatro novos comandos de roteamento mudavam o hash. Arquivo **restaurado byte a byte**, sem editar baseline; roteamento GET movido para `server.py`.
2. `test_20_ui_distinguishes_rejected_from_validated`: mock Node tentava usar o evento removido que ligava resultados oficiais ao renderizador demonstrativo. O mock agora entrega os mesmos casos sintéticos pela leitura GET preparada, mantendo todas as assertions de rejeição/validação, erros, gráfico e botão desabilitado. A separação da interface não foi desfeita.

Reexecução direcionada: **15 passed**, 82,69 s (`corrections.txt`), incluindo as duas falhas, adaptador, HTTP e Chrome V7.6.4. Baselines históricos voltaram a `violations: []`.

Segunda execução completa no commit `09f06b2`: **1765 passed, 14 failed, 61 subtests passed**, 1009,69 s (16 min 49 s). Saída bruta intacta: `regression_final.txt`. Comparação automatizada em `regression_comparison.json`: `new_vs_v763: []`, `baseline_not_repeated: []`. As duas falhas adicionais foram resolvidas e todos os 13 testes novos passaram. A suíte permanece vermelha pelas 14 falhas conhecidas.

Grupos remanescentes: sete testes PostgreSQL local indisponível; três expectativas H2/registro; dois testes de hashes operacionais legados anteriores à recovery; dois de expectativas antigas do Radar. Nenhum baseline ou comportamento científico foi ajustado para esconder essas falhas.

As duas execuções completas ocorreram sem edição concorrente. Após a segunda, somente relatórios foram anexados; código de dashboard/scripts/tests corresponde ao commit testado. Árvore estável, saída bruta em diretório ignorado e temporário fora do repositório, como V7.6.3. `out.json` do operador será excluído somente da consulta Git do processo de teste via configuração temporária, sem editar/deletar/commitar o arquivo. Nenhum arquivo será editado durante a suíte.
