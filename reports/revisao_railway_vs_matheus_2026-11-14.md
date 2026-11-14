# Diferenças entre a produção Railway e a main do Matheus

Comparação em 14/11/2026, somente leitura. Lucas pediu o commit do replay no
repositório do Matheus e a apresentação das diferenças da produção para revisão,
antes de decidir incorporá-las. Nenhuma diferença abaixo foi aplicada nesta entrega.
A publicação e a sincronização da fork ficam para a etapa seguinte.

## Fontes conferidas

- Original: `matheuspc3/Hedge-Fund-Lab`, main `5092fdfbf724656ed7a2f60f16218b55a65df492`.
- Fork usada pelo Railway: `LuquinhasPS/Hedge-Fund-Lab`, main `c63caae291f3107dc2e56f0b06f5d57668cb3122`.
- A API Railway confirma essa fork/main como fonte; último deploy SUCCESS em
  04/11/2026, com o mesmo commit da fork. Sem mudanças pendentes no serviço.
- A main do Matheus é ancestral da versão implantada. A diferença é de 28 arquivos,
  1764 linhas acrescentadas e 87 removidas, incluindo código, testes e documentos.
- Patch completo preservado junto ao pacote privado de entrega, SHA-256
  `2a0f27b7a385e915d804ef4cf80b947d9ecfd14e7088154e5a22b81cbbb07c56`. Gerado diretamente pelo Git, sem editar fontes.

[Comparação no GitHub](https://github.com/matheuspc3/Hedge-Fund-Lab/compare/5092fdfbf724656ed7a2f60f16218b55a65df492...LuquinhasPS:c63caae291f3107dc2e56f0b06f5d57668cb3122).

## O que mudou e por que merece revisão

| Conjunto | Comportamento na fork/produção | Avaliação para incorporação no original |
|---|---|---|
| Universo fixo dos agentes | `radar_analysis_api.default_tickers` conserva PETR4, VALE3, ITUB4, WEGE3 e BBAS3 mesmo depois de vender uma posição. Rotina diária e formulário usam esse universo; o backend recusa Multiagentes com seleção incompleta. | Correção coerente com DP-07/24/34: vender tudo não pode impedir uma futura recompra. Recomendo levar junto dos respectivos testes. |
| Carteiras SMA/Bollinger | Novo `rule_portfolios.py`: SMA 50/200 e Bollinger 20/2; cesta inicial comum, parcelas independentes por ativo, decisões com dados passados e execução na abertura B3 seguinte. Atualização de mercado avança os livros. | Implementa a DP-36 já registrada na fork. Recomendo preservar o conjunto se as referências diárias devem continuar no produto; não é dependência obrigatória para consultar o replay exportado. |
| Separação entre regras e agentes | Registro aceita as duas estratégias; bloqueia lançamento manual/rebalanceamento pelo gestor nelas, exclui-as da seleção de agentes e impede que a rotina confunda uma referência com a Multiagentes. Proventos são contabilizados depois de atualizar o histórico das regras. | Guardas necessárias à introdução das regras. Não copiar só o módulo novo: seus callers e essas validações fazem parte da mesma entrega. |
| Execução intradiária simulada | Novas aprovações durante o pregão passam a aguardar a primeira barra Yahoo de um minuto iniciada estritamente após a aprovação, com volume/preço coerentes e barra completa. Fonte dos ativos da cesta é congelada antes do lançamento. Faltando preço, espera/expira; não usa fechamento como substituto. Ordens OPEN/CLOSE antigas conservam sua política. | Mudança funcional de preço/fonte e relógio, não simples correção técnica. Foi registrada como autorização DP-35 de 22/10 na fork. Revisar essa decisão explicitamente antes de levá-la ao original. O replay de abril–novembro continua usando OPEN RAW B3, sem mudar resultados. |
| Processamento e prévia intradiários | Servidor inicia a consulta periódica de pendências; ciclo diário reconhece ordem intradiária pendente. A prévia fica vinculada ao mesmo slot de execução aprovado. Livro/histórico e tela mostram origem, preço, horários e estado intradiários; tela atualiza enquanto aguarda. | São partes do conjunto intradiário. Incorporar apenas com a política correspondente e seus testes; não ativar isoladamente o processador. |
| Interface e testes | Labels/origens de regras, ocultação das ações incompatíveis, universo completo no formulário, correções de texto/acentuação. Novos testes de ordens intradiárias e carteiras por regra, e ajustes dos demais testes de agentes/gestor/ciclo. | Acompanham os comportamentos acima. A comparação de fontes não equivale a uma nova execução dessa suíte. |
| Documentação | Guias e estado registram as implantações e decisões de outubro e a origem na fork. | Consolidar preservando o histórico e corrigindo as divergências de identificação descritas abaixo. |

## Divergência de identificação das decisões

A fork usa **DP-35 para execução intradiária**, autorizada em 22/10. A documentação
do replay nesta worktree usa **DP-35 para a extensão retrospectiva**, autorizada em
12/11. É uma colisão documental entre ramos, não uma autorização para misturar os
experimentos. Antes de unir os documentos, decidir uma referência inequívoca para
cada decisão, preservando os IDs originais nas evidências seladas e registrando a
correspondência. Não renomear manifests, ordens ou recibos para esconder a colisão.
A DP-36 identifica SMA/Bollinger na fork e foi referenciada como fonte do replay.

## Arquivos exatos da diferença

- `dashboard/auction_orders.py`
- `dashboard/daily_cycle.py`
- `dashboard/dividends_api.py`
- `dashboard/manual-portfolio.js`
- `dashboard/manual_portfolio_api.py`
- `dashboard/market_base_api.py`
- `dashboard/personal-charts.js`
- `dashboard/portfolio_history_api.py`
- `dashboard/product.js`
- `dashboard/radar-analysis.js`
- `dashboard/radar.html`
- `dashboard/radar_analysis_api.py`
- `dashboard/rule_portfolios.py`
- `dashboard/server.py`
- `dashboard/wallet-manager.js`
- `dashboard/wallet_manager_api.py`
- `docs/DEPLOY_RAILWAY.md`
- `docs/DIRECAO_DO_PROJETO.md`
- `docs/ESTADO_ATUAL.md`
- `docs/ROADMAP.md`
- `tests/agent_cycle_check.js`
- `tests/test_agents_ui.py`
- `tests/test_daily_cycle.py`
- `tests/test_intraday_orders.py`
- `tests/test_legacy_web.py`
- `tests/test_radar_analysis.py`
- `tests/test_rule_portfolios.py`
- `tests/test_wallet_manager.py`

## Próximo passo proposto

1. Revisar universo fixo + conjunto SMA/Bollinger e seus guardas/testes como uma
   integração própria, preservando a versão que já opera na produção.
2. Confirmar a manutenção da política intradiária de outubro antes de incorporá-la
   no original; não reescrever o preço dos replays nem das ordens antigas.
3. Consolidar os documentos com a correspondência das decisões e rodar os checks
   dos caminhos afetados na versão integrada.
4. Depois sincronizar a fork usada pelo Railway, evitando que uma sincronização
   cega do original remova funcionalidades já implantadas.

## Acesso e transferência dos resultados

O site respondeu pela rede Tailscale. A transferência SSH ao mesmo servidor
exigiu uma autenticação adicional do Tailscale. A tentativa foi encerrada quando
Lucas restringiu esta etapa ao commit e à revisão; nenhum arquivo foi enviado,
nenhum deploy/configuração foi alterado e nenhuma chamada Gemini foi feita.
Quando retomarmos essa etapa, Lucas pode concluir a autenticação ou fazer a cópia
por sua própria sessão. O pacote privado verificado já está preservado fora da
worktree e não deve ser colocado em repositório público: contém fontes B3 para uso
pessoal e respostas/contextos completos. Código e relatos podem seguir pelo Git;
os dados completos vão para uma pasta própria no volume persistente do servidor.
