# Testes de interação real

`scripts/ui_check_v763.mjs` usa Chrome headless real via cliente DevTools já
existente (`ui_cdp_v762.mjs`), sem nova dependência. `tests/test_ui_v763.py`
torna a jornada executável pelo pytest e reutiliza o servidor keyless da V7.6.2.

Resultado da jornada: **53 verificações aprovadas**, zero falhas, zero escritas
inesperadas/provedor, zero exceções JavaScript. Fonte bruta:
`ui_checks_release.json`. Não são verificações estáticas de HTML.

Cobertura: entrada pelo Início, universo real, seleção de PETR4, indicadores e
unidades, Mercado → Radar, run/asset preservados, retorno de foco, cinco ativos,
filtros COMPRA/VENDA/MANTER/VETADO, remoção e combinação vazia, BBAS3 determinístico,
voto/evidências expansíveis, ajuda/Escape/foco, clipboard real, recarga com filtros,
tentativa original preservada, comparação de duas empresas, Radar → Carteira,
V1 desabilitado, modal de custo e contexto alterado, quatro viewports, mobile,
popover, ampliação, API vazia/erro interceptada, gráficos Chart.js legados e aliases.

Os selects são operados por Home/ArrowDown/Enter do Chrome; cliques e teclado
usam eventos do DevTools. Estados vazios/erro e preflight/run usam fixtures
locais identificadas. Requisições de escrita são interceptadas **antes** do
transporte; somente preflight/run explicitamente simulados são respondidos.
O teste compara integralmente o payload de execução existente. Cancelamento
e contexto invalidado não produzem nem mesmo uma execução simulada adicional.

Durante o teste inicial dos gráficos legados, todos os caminhos `/api/*` e URLs
do provedor ficam bloqueados no domínio Network. Depois é instalada a interceptação
Fetch integral para as jornadas Mercado/Radar. O export estático real é entregue byte a byte de `dashboard/data.json` pelo DevTools,
sem construir ou substituir séries; o relatório registra `LOCAL_UNALTERED_EXPORT`
e o tamanho do arquivo. A consulta HTTP direta ao mesmo servidor também foi
conferida (16.643.576 bytes). O servidor não tem chave Gemini.

As tentativas anteriores estão preservadas em `ui_checks*.json`: houve erro de
limpeza do perfil Chrome no Windows e falhas na checagem do export legado de
16 MB quando consultado no mesmo ciclo das interceptações. A checagem final
executa os gráficos primeiro e os confirmou. Não foram alterados gráficos ou
dados científicos para obter aprovação. A limpeza do perfil agora espera o
processo terminar e usa retries nativos, validando o caminho temporário. Cada
Chrome usa uma porta dinâmica identificada por `DevToolsActivePort`, evitando
conflito entre sessões. Os dois testes DOM antigos do Radar agora carregam o
componente real `market-ui.js` e fornecem as APIs mínimas de Window/DOM que ele
usa; suas asserções de cancelamento, identidade e bloqueio foram mantidas.
A reexecução dos três testes afetados passou (`ui_verified.txt`).

```powershell
node scripts/ui_check_v763.mjs http://127.0.0.1:8105 resultado.json capturas
.venv/Scripts/python.exe -m pytest -q tests/test_ui_v763.py
```

O runner anterior V7.6.2 também ganhou interceptação de APIs/provedor para que
cliques forçados do teste V1 nunca enviem um POST pago ao servidor real.
