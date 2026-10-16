# Componentes adotados

Reutilizados UX-M2/M4: shell/AREAS, tokens de design-system.css, ds-card, ds-alert, estados `HFL.state`, ajuda `ds-help`, glossário único, tabelas em regiões roláveis e Chart.js local. Nenhuma segunda paleta, navegação global, biblioteca ou central de ajuda.

`monitoring.js` fornece a mesma visualização de leitura em `/portfolio` e `/paper`: seletor, resumo, posição, composição, evolução, operações, eventos e detalhes. `monitoring.css` organiza layout e usa tokens existentes. Markup curto permanece nas duas páginas; nenhum framework/template novo foi introduzido para compartilhar esse trecho.

Novos termos: patrimônio, capital alocado, custo médio, marcação, peso atual, resultados realizado/não realizado, liquidação, execução paper, histórico reconciliado, proposta consultiva, validação financeira, custos e giro. Termos existentes de caixa, D+2, peso-alvo, exposição, drawdown e volatilidade são reutilizados.

Regras contábeis e risco permanecem em Python. JavaScript formata BRL, USD, percentuais e datas em BRT, escapa conteúdo externo, monta tabelas e gráficos. Valores históricos faltantes não são aproximados. Contadores de requisição impedem respostas antigas de substituir seleções recentes.
