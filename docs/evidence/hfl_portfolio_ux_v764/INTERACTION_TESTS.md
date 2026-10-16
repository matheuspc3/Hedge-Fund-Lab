# Testes de interação

`tests/test_portfolio_monitoring.py`: 11 casos parametrizados/funcionais. Registros oficiais V1/V2; nenhuma execução implícita; catálogo sem fixtures; fronteira de IDs; estado em arquivo temporário; nova operação persistida em fixture e relida; preços, quantidades, custos, lacuna de sessão, histórico insuficiente, fonte ausente/corrompida, expiração derivada e integridade. O verificador H2 é stubado somente nos testes de apresentação de estados artificiais; os testes existentes verificam contratos científicos reais. Nenhuma fixture escreve no ledger científico.

`tests/test_ui_v764.py`: contrato HTTP GET, parâmetros repetidos/caminhos inválidos, estáticos e jornada Chrome. Servidor `serve_dashboard_keyless.py` existente. Browser intercepta todos os writes e acessos externos antes de transporte.

`scripts/ui_check_v764.mjs`: **36 verificações**, V2 real em caixa; lista V1/V2; detalhe rejeitado/válido; três datas; pesos snapshot/alvo/projetado; voltar com foco; reload/deep links; simuladores V5/V6; isolamento H2; supervisão; timeline; refresh; paper H2 com cinco fontes; ajuda/Escape; quatro viewports; reflow equivalente a 200%; teclado; erro/retentativa; posições/operações/liquidação em fixture explícita; curva com pontos sem interpolação; zero writes e erros de runtime.

Fixtures do browser ficam na memória do teste e são rotuladas. Capturas precedem essas fixtures financeiras; mostram registros reais locais. Os testes antigos V7.6.2/V7.6.3 agora exigem ausência dos gatilhos V1 removidos da página, preservando rejeição, validade e ausência de requisição paga. Nenhuma expectativa científica/baseline alterada.

Saídas brutas: `targeted_initial.txt` (**55 passed, 23 subtests passed**); `adapter_final.txt` (**12 passed**); `ui_final.json`/`browser_final.txt` (**36/36**). `ui_initial.json` registra foco incorreto ao voltar; `ui_retry.json` registra espera de reload prematura no teste; `ui_pre_visual_review.json` passou antes do ajuste de densidade/tabela. Tentativas anteriores preservadas.

A regressão completa detectou um mock antigo em test_global_pm_v2: agora os mesmos casos A/F entram pelo GET mockado do componente sintético, com todas as assertions mantidas. Correções e jornada final: **15 passed** em corrections.txt.

Regressão completa final: **1765 passed, 14 falhas preexistentes, 61 subtests passed**; todas as jornadas de navegador passaram. Nenhuma chamada paga, ordem ou criação de registro científico detectada na preservação.
