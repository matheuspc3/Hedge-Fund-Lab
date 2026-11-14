# Integração do replay com a base implantada no Railway

14/11/2026 · DP-35/36/37 / REPLAY-01. Lucas autorizou preservar as melhorias do
Matheus e os comportamentos aceitos na fork, integrar o replay e verificar os
fluxos antes da publicação. A integração acontece em worktree própria; o checkout
histórico da campanha paga continua intacto.

## Resultado concreto

Merge das revisões `d1ada710df797f63ae708bb55bde32ba6d68b358` (código e relatos do
replay) e `c63caae291f3107dc2e56f0b06f5d57668cb3122` (fork implantada). A main do
original `5092fdfbf724656ed7a2f60f16218b55a65df492` é ancestral das duas revisões.
Preserva-se o histórico Git, inclusive as correções de logs/votos/navegação do
Matheus; nenhuma escolha entre apagar um ramo e substituir pelo outro.

Os 69 arquivos já existentes em `dashboard/` são logicamente idênticos à fork
implantada (comparação normaliza apenas CRLF/LF). A única adição nessa pasta é o
HTML do explorador. Mantidos: universo dos cinco ativos mesmo após zerar posição,
SMA/Bollinger com seus guardas e proventos, execução intradiária simulada e seu
processador. Não houve nova mudança nos sinais, custos ou política financeira.

A consolidação documental mantém DP-35 para execução intradiária, DP-36 para
SMA/Bollinger e DP-37 para replay. Documenta a correspondência dos rótulos
históricos, sem renomear manifests, scripts, relatórios ou evidências seladas.
Históricos e entregas de ambos os ramos foram mantidos. O guia do replay entrou
no índice de documentação existente.

## Verificação

- **133 testes passaram, 1 skip**, na base implantada (34,67 s) e novamente na
  worktree integrada (32,01 s): `test_agents_ui`, `test_daily_cycle`,
  `test_intraday_orders`, `test_rule_portfolios`, `test_wallet_manager`,
  `test_radar_analysis` e `test_legacy_web`. O skip é o navegador real opcional;
  o check Node de expansão dos votos passou.
- Preparação de ambiente: o pytest usa um diretório temporário cujo pai não
  existia no checkout novo. Criar a pasta ignorada `.pytest_cache` resolveu os
  erros de setup; nenhum teste ou expectativa foi alterado para fazê-los passar.
- `restore_frozen_bytes.py` reproduziu hashes originais antes dos testes, sem
  atualizar selos. Os testes usaram dados e clientes simulados, com a rotina real
  e a atualização automática desativadas; nenhuma chamada Gemini nova.
- Build do explorador na integração: **153 sessões / 918 estados**. HTML,
  carregador das chamadas e inicializador são idênticos byte a byte aos artefatos
  já verificados no navegador em 1280 e 390 px. Foram usadas cópias das exportações
  existentes, sem executar novamente o replay ou recalcular suas decisões.
- Documentação: **9 hubs / 376 links locais**, catálogo e evidências PASS.
- Preservação na worktree histórica: **1069 arquivos anteriores**, **157 arquivos
  diagnósticos** e **88 fontes de runtime** conferem com os hashes registrados.
  Livro final e orçamento agregado também conferem com o backup durável verificado.

## Limites e continuidade

A campanha histórica segue exploratória, retrospectiva e sem arquivo point-in-time;
a integração não transforma seus resultados em evidência prospectiva. As fontes
integradas diferem da revisão financeira original: não contornar
`campaign_identity_changed` nem trocar hashes para reabrir a campanha. A fonte
exata da execução está no attestation e nos snapshots originais. A revisão Git do
replay foi registrada depois da execução para preservação, não é prova de que o
commit já existia no início pago. As exportações prontas continuam consultáveis.

Esta entrega integra código e documentação; os dados completos permanecem privados
e fora do Git. Não foram enviados ao servidor nem incorporados à imagem. Nenhuma
configuração Railway, carteira ativa ou fonte de produção foi alterada; nenhum
deploy foi disparado. A autenticação adicional do Tailscale para transferência
fica com Lucas quando essa etapa for retomada.

Próximo passo: revisar a integração no original, depois sincronizar a fork de
produção e transferir os resultados para uma pasta própria no volume persistente,
com conferência de integridade, antes de disponibilizar a consulta no deploy.
