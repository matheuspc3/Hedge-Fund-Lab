# Arquitetura da carteira

Antes, `portfolio.html` empilhava fluxo Global PM, propostas A–F e livro contábil V5. O mesmo renderizador de exemplos também recebia eventos de decisões oficiais. Isso favorecia associação visual indevida entre uma inferência e posições sintéticas.

Agora há cinco áreas por finalidade, com a navegação global existente. As abas da página substituem visualmente os links secundários duplicados do shell. `monitoring.js` apresenta a consulta; `portfolio.js` e `global-pm.js` permanecem confinados ao simulador. O evento que encaminhava inferências oficiais ao renderizador demonstrativo foi removido. `global-workflow.js` legado permanece para compatibilidade técnica/teste de fechamento, mas não é carregado pela página; nenhuma ação de replay ou escrita está exposta no histórico novo.

```text
registros oficiais → platform_api.public_global → decisões do gestor
contexto V2 → monitoring_api.global_snapshot → fotografia hipotética
ledgers H2 → forward_api.portfolios/decision/supervision → monitoring_api.h2_wallet
fixtures V5/V6 → portfolio_api/global_pm_api existentes → simulador
monitoring.js → renderização, tabelas e gráficos (sem regras financeiras)
```

## Contrato novo

`GET /api/portfolio/monitoring` retorna catálogo, registros consultivos oficiais, `read_only: true` e hora da consulta.

`GET /api/portfolio/monitoring?wallet=h2:ai` ou `wallet=global:<v74-id>` retorna identidade, classificação, resumo, posições, marcas, curva, operações, eventos, decisão e limitações. IDs H2 são allowlisted; IDs Global usam a expressão já existente da plataforma. Campos extras e parâmetros repetidos são rejeitados. Nenhuma rota POST foi adicionada. O dispatcher existente mantém origem local, erros sanitizados e `Cache-Control: no-store`.

V1 pode ser consultada como decisão, mas não selecionada como carteira V2. Fixtures não entram no catálogo. Ausência de fonte retorna indisponibilidade; corrupção rejeita a consulta. Integridade H2 original reutiliza `forward_integrity`; supervisão reutiliza a auditoria existente. Carteiras incompatíveis com a identidade/preços comuns ficam indisponíveis neste adaptador, sem aproveitar valores de outra carteira.

A fotografia V2 não recebe uma curva artificial nem operações derivadas de pesos. `persistent_execution: false` explicita a falta de ledger oficial multiativos. H2 usa `persistent_execution: true` por possuir registros existentes; isso não significa atualização automática.

Sem dependências, banco, motor contábil, modelo de risco ou mecanismo de escrita novos. Somente um adaptador de apresentação e roteamento GET em `server.py` (`portfolio_api.py` permanece byte a byte no baseline); APIs financeiras de escrita intactas.
