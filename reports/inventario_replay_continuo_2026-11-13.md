# Inventário da campanha contínua de abril a novembro

Estado final: seis carteiras concluídas, 153/153 dias sem lacunas e 918 estados
reconciliados PASS. Inferência real em 13/11, das 17:41 às 22:28 (São Paulo),
no mesmo orçamento agregado e sem reinício durante a interrupção do Codex.
Explorador local entregue e verificado em desktop/celular, sem deploy.
[Resultados finais](replay_continuo_2026-04_2026-11.md) ·
[Explorador e cópia de entrega](../docs/REPLAY_MULTIATIVOS.md#explorador-local-e-entrega-final).

Escopo: DP-35 / REPLAY-01, acrescido das referências solicitadas por Lucas em
13/11. Período fixo 06/04–12/11/2026, 153 pregões, cinco ativos. Outubro oficial,
pilotos anteriores e Railway preservados. Primeiro concluir referências; depois
executar Multiagentes; frontend somente depois dos dados/resultados.

| Carteira | Implementação encontrada | Convenções existentes |
|---|---|---|
| Buy & Hold | Livro manual atual, DP-11/20/30 | Cesta inicial próxima de 20% por ativo, unidades inteiras; não rebalanceia; proventos em caixa no pagamento |
| SMA | `dashboard/rule_portfolios.py` do checkout da aplicação atual + `src/strategies/sma_cross.py` | Cruzamento 50/200; 201 fechamentos causais; parcelas independentes de 20%; entra somente zerado, vende tudo no sinal de saída |
| Bollinger | Mesmo módulo atual + `src/strategies/bollinger_bands.py` | 20 períodos, 2 desvios; 21 fechamentos; rompimento inferior compra, superior vende, conforme código; mesmas parcelas independentes |
| Equal Weight | `src/backtesting/portfolio.py::EqualWeightPortfolio` | Pesos iguais, 63 pregões entre rebalanceamentos; não confundir com o adaptador single-asset de `src/strategies/equal_weight.py` |
| Mínima Variância | `src/backtesting/portfolio.py::MinVariancePortfolio` | Sexta carteira confirmada por Lucas em 13/11. Janela 252 retornos, rebalanceamento 63 pregões, `allow_short=False`, SLSQP e seus defaults originais; fallback Equal se histórico insuficiente ou otimização falhar |
| Multiagentes | Radar atual + gestor de quantidades + livro/execução/proventos existentes | Cinco analistas por ativo, risco, gestor; schemas/quórum/vetos/prompts inalterados. Gemini 3.8 Flash; no máximo duas tentativas físicas por chamada lógica para falhas de transporte |

## Origem e comparabilidade

A worktree `b507` não contém o módulo de regras atual. A aplicação salva em
`C:/Users/LUCAS/Meu Canto/TCC/Hedge-Fund-Lab` contém a DP-36 e esse módulo.
Os módulos atuais de livro, proventos e regras foram copiados literalmente para
`data/cache/continuous-replay/april-november-2026-flash/engine/`; não se alterou
nenhum checkout de origem. O código SMA/Bollinger realmente importado é comparado
por SHA-256 com essa cópia antes de executar. Cada fonte usada terá hash no
manifest da campanha. Os pilotos anteriores continuam com seus próprios snapshots.

O motor legado de portfólio começa em caixa, não incorpora o livro DP-30 e pode
usar preços ajustados também no patrimônio. Executá-lo diretamente junto aos
livros atuais misturaria convenções. A adaptação prevista reutiliza somente os
pesos das estratégias multiativos, com o mesmo cadastro inicial, RAW B3,
unidades inteiras, custo 0,03%, execução na abertura seguinte e proventos fora
do caixa reinvestível. Primeira decisão no fechamento de D0; depois a cada 63
pregões. Não haverá ajuste de parâmetros/otimizador para melhorar resultados.
Essas convenções são congeladas no manifest antes da comparação. Os cinco livros
de referência são concluídos antes de qualquer inferência. Pesos, janela exata,
resultado completo relevante do otimizador (sucesso/status/mensagem/iterações/
objetivo/pesos) e eventual fallback acompanham os recibos no SQLite. O código
multiativos é idêntico por SHA-256 nos dois checkouts. Para obter quantidades e
ajustar compras ao caixa na abertura, reutiliza-se `auction_orders.plan`, também
usado na Multiagentes. Ele reduz compras proporcionalmente quando necessário;
isso é explicitamente uma convenção comum desta campanha, distinta da prioridade
alfabética de compras do executor legado de portfólio.

## Cobertura auditada

| Ativo | Início B3 salvo | Fim antes desta atualização | Barras B3 já salvas |
|---|---|---|---:|
| PETR4 | 03/01/2000 | 20/10/2026 | 6644 |
| VALE3 | 03/01/2000 | 20/10/2026 | 6638 |
| ITUB4 | 03/01/2000 | 20/10/2026 | 6644 |
| WEGE3 | 02/08/2004 | 20/10/2026 | 5506 |
| BBAS3 | 03/01/2000 | 20/10/2026 | 6641 |

A base normalizada está em JSON selado, `data/platform/market-base-v1/b3`.
Yahoo mantém CSV bruto e JSON normalizado por hash em
`data/platform/stock-history-v1/<ticker>`. A campanha copiou a base necessária,
completou somente 16 pregões B3 de 21/10–12/11 e atualizou Yahoo no intervalo
necessário ao aquecimento/replay; não recoletou vinte anos de cotações.
O bundle de trabalho cobre 07/01/2025–12/11/2026, 463 barras por ativo.
Existem 765 inputs de decisão congelados, sempre anteriores à sessão-alvo.
Os snapshots Yahoo locais anteriores cobriam 03/01/2000–20/10/2026 para
PETR4/VALE3/WEGE3/BBAS3 (6728 barras) e 21/12/2000–20/10/2026 para ITUB4
(6475 barras). São séries diferentes da B3 RAW; não se atribui ao Yahoo a
cobertura oficial nem se usa seu calendário para fills. Auditoria por fonte em
`yahoo_coverage_audit.json`.

Os ZIPs/JSON recém-baixados ficam preservados. O ZIP anual 2025 já em cache
confere com o hash do normalizado e foi copiado. O ZIP 2026 atualmente em cache
tem outro hash que o usado na redução selada de 16/10; não foi apresentado como
se fosse aquele original. A redução original e seu hash permanecem preservados.
Auditoria estruturada: `coverage_audit.json`, `data_audit.json`, `inputs/manifest.json`
na raiz da campanha.

## Persistência, limites e próxima etapa

### Servidor e cópia local

O Railway é a cópia de trabalho desde a migração de outubro; o guia de deploy
manda manter o PC como cópia anterior, sem dois escritores. Por isso a auditoria
local até 20/10 não demonstrava atraso da produção. A consulta de leitura em
13/11 confirmou o volume `hfl-data` de 20 GB montado em `/app/data`, deploy
`18fdc3c0-a955-47d8-a611-7201ca652c37`, e todos os cinco ativos até **12/11/2026**.
O histórico persiste em JSON selado no volume; Yahoo conserva CSV e snapshots
JSON, e os livros/chamadas usam SQLite. A coleta diária não requer migração SQL.

Com o Tailscale local inicialmente desligado, a primeira exportação somente de
mercado foi obtida por SSH Railway antes da orientação de restringir o acesso ao
Tailscale. Depois de Lucas ligá-lo, o GET conhecido
`/api/platform/market-base` respondeu e confirmou a atualização de 13/11 às
09:00–09:03 para o fechamento 12/11. Não se alteraram rede, configuração,
workers nem livros do servidor. Os 16 snapshots remotos necessários estão em
`remote/b3`; todos conferem em linhas e hash do ZIP bruto com os já preparados.
Não foi preciso substituir ou recoletar os inputs congelados.

Cobertura remota: PETR4/ITUB4 6660 datas; VALE3 6654; BBAS3 6657 desde 03/01/2000;
WEGE3 5522 desde 02/08/2004. Fim comum 12/11, zero conflitos. Lacunas antigas
de calendário ainda aparecem na base longa (1/1/7/4/1 conforme ativo), mas não
no intervalo exigido pelo replay, que passou pela cobertura integral. Evidências:
`remote/audit.json`, `remote/comparison.json`, `remote/tailscale-market-status.json`.

Livro e chamadas em SQLite independentes; inputs, respostas, decisões, operações,
marcas diárias e CSV para a futura tela. O orçamento agregado US$34,78 tem uma
linha durável por tentativa física; custo conhecido mais reserva integral das
tentativas incertas/em voo, sem reset ao retomar. O ajuste operacional ainda está
em qualificação; os custos simulados do ensaio não são gasto de API.

Reconstrução exploratória: fatores/snapshots adquiridos agora, sem disponibilidade
histórica comprovada. O cutoff declarado de março/2026 não garante ausência de
contaminação, e o alias da API não é imutável. Próxima etapa: fechar o conjunto e
qualificar as referências e recuperação, concluir todos os livros determinísticos,
então iniciar a campanha paga contínua sob o teto já autorizado.

## Reparo contábil identificado antes da inferência

A geração das referências parou em11/06, antes da primeira chamada paga, ao
encontrar duas parcelas JCP de BBAS3 com a mesma data-com01/06 e pagamento11/06:
R$0,05968401166 e R$0,08157785203 por ação. A chave atual do cadastro agrupa
carteira+ticker+data-com+pagamento+tipo; a primeira parcela entrou e a segunda foi
recusada por payload diferente. Há outra colisão de parcelas em01/09→11/09.
Nenhuma marca diária de11/06 foi publicada; as45marcas até10/06 foram preservadas.

O adaptador exclusivo `continuous_replay_dividends.py` identifica cada componente
pelo ticker/tipo/datas/label/taxa bruta. Reutiliza `entitlements`, arredondamento
por evento, validação/replay e append transacional do livro. Reconhece um recibo
antigo somente se seu payload exato confere; acrescenta somente o componente
faltante, sem apagar/reescrever/duplicar o já recebido. A mesma função atende
todos os seis livros e preserva taxa/fonte/identidade no recibo. Não se alterou
fonte de produção nem evidência anterior. Manifestos e ajustes pré-pagos ficam
versionados (`campaign.json`, `campaign-v2.json`, `campaign-v3.json` e respectivos
amendments); todos anteriores a qualquer HTTP Gemini.

Check focado PASS: para855ações, as duas parcelas líquidas43,38+59,29=102,67
são recebidas uma vez, inclusive partindo do recibo parcial legado. O check
diário passa a comparar o caixa recebido com a soma independente de **todos**
os componentes B3 elegíveis, além da reconstrução de posições/custos/recebíveis.
Retry/crash/cap e ensaio offline de20pregões/120estados também passaram.

## Diagnóstico e normalização numérica antes da campanha final

As cinco referências diagnósticas terminaram153pregões;765estados diários foram
reconciliados. A coincidência de Mínima Variância/Equal não era evidência de uma
solução ótima. Na mesma covariância passada de06/04,07/07 e05/10, o SLSQP
original parou em uma iteração nos pesos0,2. Gradientes diferentes nos pesos
interiores violavam a condição de ótimo; um pequeno candidato long-only factível
já reduzia a variância. Uma solução com objetivo normalizado reduziu a variância
**dentro da amostra de estimação** em6,9164%,18,1204% e18,4192%, respectivamente.
Esses números não são retorno futuro ou benefício financeiro realizado.

O reparo é somente numérico: dividir a função-objetivo pela maior variância
diagonal positiva, constante para cada matriz, preserva exatamente o minimizador,
a covariância, a janela252, o rebalanceamento63, soma1 e long-only. As tolerâncias
padrão do SLSQP foram mantidas. O adaptador faz isso antes do `minimize` existente
e registra escala, objetivo original, objetivo normalizado, pesos e status.
Nenhuma das76fontes congeladas foi editada ou teve seu hash contornado.

Checks PASS: exemplo analítico de dois ativos com pesos10/90; invariância ao
escalar retornos; matriz nula; KKT aproximado e solução de referência nas três
covariâncias passadas. O livro/153marcas anteriores permanecem como diagnóstico,
com seus hashes em `diagnostic_references_preserved.json`. A versão final usa
`qualified-v2/` e os mesmos inputs congelados. Seu orçamento continua no **mesmo
arquivo pai `budget.sqlite`**, ainda com zero tentativas antes da revisão; não há
reset de teto nem de cobrança. `active_campaign.json` identifica a fase final.
