# Replay exploratório da carteira multiativos em abril de 2026

12/11/2026 · **DP-37 / REPLAY-01**, extensão pontual da DP-31 autorizada por voz
por Lucas. Resultado concreto: executar a estrutura atual em dez pregões
históricos e rastrear decisões, operações e patrimônio versus Buy & Hold.
H2 permanece histórico; não houve deploy, push, chamada Railway nem operação
na carteira iniciada em outubro. Não se trata de avaliação prospectiva.


## Consulta no servidor pessoal

**16/11 — v2:** pacote `explorador_replay_v2_2026-04_2026-11.zip` instalado
no mesmo volume, em `data/replays/april-november-2026-flash-v2/`, sem substituir
a v1. SHA-256 `62998e60b09d24a49668a56cbbdcd9076db1d65ef34bb8af7a2e8d4652da5749`;
12 membros regulares, todos conferidos com o manifesto selado. A cópia usou
o SSH autenticado do Railway, porque o SSH Tailscale pediu reautenticação.
Importação atômica, idempotência e preservação integral da v1 PASS.
O importador local aceita `--version v2` nos comandos abaixo para selecionar
esse pacote/destino; sem a opção mantém a v1. A rota `/laboratory/replay/v2/`
e os atalhos entre versões estão implementados e testados localmente,
**pendentes de publicação do código**. O deploy `b29aecf` ainda serve somente
a v1. Subir dados e publicar código são etapas independentes.

DP-37 / REPLAY-01, disponibilização autorizada por Lucas em 14/11. O menu
Laboratório aponta para `/laboratory/replay/`, uma consulta dos resultados já
arquivados. A página não executa agentes ou ordens. O navegador recebe apenas
os dez exports permitidos: HTML, carregador de chamadas, JSON e CSV; os livros,
scripts de instalação e arquivos internos não são publicados por essa rota.
Mantém a proteção de Host/Origin e a rede Tailscale existente, sem acesso público.
Arquivos grandes são comprimidos por gzip em streaming quando o cliente aceita,
sem mudar seus bytes arquivados. GET/HEAD anunciam a mesma codificação; clientes
que recusam gzip recebem a representação original. A compressão não exige
bufferizar os exports de 40 MB por cliente.

O pacote privado `explorador_replay_2026-04_2026-11.zip` é instalado em
`data/replays/april-november-2026-flash/` no volume permanente; `exports/` alimenta
a consulta, `package.zip` conserva o pacote verificado e `import_receipt.json`
registra os hashes. Essa pasta não é o livro das carteiras diárias nem a raiz da
campanha paga. Os dados e recibos continuam fora do Git.

Do PC com acesso Tailscale autorizado, usando o ZIP preservado na entrega:

```powershell
python scripts/publish_replay.py "caminho/do/explorador_replay_2026-04_2026-11.zip" --check-only
python scripts/publish_replay.py "caminho/do/explorador_replay_2026-04_2026-11.zip"
```

O primeiro comando só verifica localmente. O segundo usa o SSH já existente no
mesmo servidor Tailscale, com validação estrita da chave, e transmite bytes sem
pipe textual do PowerShell. A autenticação adicional é concluída por Lucas;
não se mudam credenciais, rede, agendador ou regras para facilitar a cópia.

O importador aceita somente o SHA-256 do pacote original e seus 14 membros
regulares conhecidos. Extrai em staging, confere os arquivos, conserva o ZIP e
promove a pasta com um rename no mesmo volume. Destino existente só é aceito se
seus arquivos/recibo já conferirem; dados diferentes nunca são sobrescritos.
Falha preserva o staging para inspeção. Não exige banco ou dependência nova.

Checks locais, sem rede ou inferências:

```powershell
python tests/check_publish_replay.py
python tests/check_replay_server.py
```

Em 14/11, importação e releitura dos 14 arquivos no servidor passaram, sem mudar
o hash do livro diário. A regressão teve 133 aprovados e um skip opcional. A
criação de symlink real não foi permitida no Windows de teste; a rota resolve o
caminho e recusa destino fora da raiz. O aceite de publicação verifica GET/HEAD,
seis valores finais, filtros, decisões, operações, proventos, chamadas arquivadas,
downloads e persistência no volume depois do deploy. Não há nova execução Gemini.

## Correspondência e revisão histórica

Desde a consolidação de 14/11, **DP-37** identifica este replay e suas extensões.
O rótulo histórico **DP-35 / REPLAY-01** permanece nos scripts, relatórios,
manifests e recibos originais. A DP-35 da aplicação identifica a política
intradiária de 22/10; a DP-36 identifica as regras SMA/Bollinger usadas como fonte.
[Correspondência completa](DIRECAO_DO_PROJETO.md#correspondência-dos-identificadores-históricos).
Nenhuma evidência é regravada para renomear essas decisões.

A revisão de preservação das fontes do runner histórico é
**`d1ada710df797f63ae708bb55bde32ba6d68b358`**. Esse commit foi criado depois da
execução e inclui relatos e interface produzidos posteriormente; não existia no
início pago. A fonte autoritativa da execução é o conjunto
**`runtime_attestation.json`, snapshots `runtime-final/` e manifests da campanha**,
com os hashes e as versões efetivamente utilizados. A worktree histórica
`C:/Users/LUCAS/.codex/worktrees/b507/Hedge-Fund-Lab` mantém esse bundle privado. A integração atual muda
fontes da aplicação; tentar usá-la contra a campanha antiga deve bloquear com
**`campaign_identity_changed`**. Esse bloqueio protege a associação entre os
resultados e o código que efetivamente os produziu.

Para verificar ou reconstruir exportações históricas, usar a worktree/revisão
original com o bundle correspondente, preservando o orçamento e os recibos.
Os atributos Git `-text` das fontes do replay preservam seus bytes exatos;
a restauração das demais fontes seladas só é válida quando reproduz o hash
original. **Não ajustar selos, manifests, hashes ou a verificação de identidade
para fazer o runtime integrado aceitar a campanha antiga.** O pacote HTML/CSV/JSON
já exportado continua consultável sem rodar inferência ou reabrir a campanha.

## Estado e período

Runner: `scripts/replay_multiasset.py`. Dados preparados; inferência real
**concluída com lacunas** após Lucas responder "autorizo, pode fazer" ao teto
agregado US$ 34,78: dez pregões marcados, sete análises completas, três sem
parecer final por conexão interrompida e uma compra de 1 VALE3. Check real PASS.
[Resultado compacto](../reports/replay_multiasset_2026-04.md).
Autorização selada em `april-2026-flash/authorization.json`, vinculada ao manifest
e ao token do preflight. Não se repete a pergunta por sessão.
Credencial Gemini presente no ambiente; valor e origem não foram exibidos.
Saldo/elegibilidade dos cerca de R$ 300 mencionados não foram verificados.

Escolha anterior à medição de retorno: **06/04/2026–17/04/2026**, sessões
06, 07, 08, 09, 10, 13, 14, 15, 16 e 17. A primeira referência é 02/04
(03/04 é Sexta-Feira Santa). Calendário B3 v2 e cobertura RAW real dos cinco
ativos conferidos; nenhuma sessão faltante no aquecimento de 450 dias corridos.
Cada input termina na referência anterior ao pregão-alvo e usa sua própria
janela de 450 dias, como o Radar atual. Aquecimento não cria patrimônio anterior.

O [model card oficial](https://deepmind.google/models/model-cards/gemini-3-8-flash/)
declara corte em março de 2026 e publicação em 02/09/2026, consultado em 12/11.
Isso não garante ausência de conhecimento posterior ou imutabilidade da API.
O replay é produzido agora; não certifica ausência de contaminação nem permite
atribuir eventuais acertos ou divergências ao cutoff.

## Reuso e adaptações

| Etapa | Componente efetivamente reutilizado | Adaptação / limite |
|---|---|---|
| Dados e indicadores | `market_base_api.series`, `multiasset_radar.technical_input`, `DataTransformer` | Snapshot local B3 RAW + fatores Yahoo, recortado por sessão; disponibilidade histórica não certificada |
| Comitê | `multiasset_radar.run/committee` | Mesmos cinco analistas por ativo, prompt v5, consenso 0,6, todos os votos, temperatura 1, thinking low, saída 8192 |
| Risco individual | `multiasset_radar.committee` | Mesmo veto determinístico acima de 50% anualizados ou chamada de risco; sem qualificação de risco global |
| Gestor da carteira | `wallet_manager_api.WalletClient`, `PROMPT`, `Proposal`, `prompt_input` | Carteira, caixa e posições propagados; não usa o contrato consultivo V1/V2 como substituto |
| Validação | `wallet_manager_api.compile_proposal` | Quantidades, universo completo, sinais, vetos e caixa; falha interrompe, sem transformar resposta inválida em HOLD |
| Execução | `auction_orders.first_auction/plan` | Aprovação hipotética às 09h → OPEN B3; ajuste proporcional de compras se necessário; preço ausente não inventa fill |
| Livro | `manual_portfolio_api.post/batch/replay`, internamente `multiasset_portfolio.fill` | SQLite isolado, transação atômica e hash chain; caixa econômico atual, sem D+2 de corretora |
| Proventos | `dividends_api.entitlements/book_received/on` | Direito na data-com, JCP líquido de 15%, pagamento vira caixa; snapshots históricos reconstituídos |
| Transporte/auditoria | Radar/WalletClient e `CallBank` existentes | Bancos novos por ativo/sessão/gestor; sem cache de respostas anteriores ou memórias; um HTTP por chamada, sem retry automático |

PETR4, VALE3, ITUB4, WEGE3, BBAS3. Capital hipotético **R$ 100.000** por
carteira, mesmos lotes inteiros aproximados de 20% e mesmo caixa residual.
Saldo inicial modelado como o cadastro DP-20: quantidades e bases calculadas
pelo fechamento anterior, registradas no início do bloco, **sem alegar fill
de mercado**, custos iniciais zero. Não se copiam posições atuais de outubro.
Operações posteriores custam **0,03%**, escolha do gestor observada no contexto
de 20/10/2026. Buy & Hold mantém unidades e proventos em caixa, sem rebalancear.

O horário econômico é simulado; `recorded_at`, coleta e journal mantêm o relógio
real. Não se reconstituem cotação intradiária, prévia, alertas de tese velha,
aprovação humana nem tentativas das 12h/16h. A DP-34 não foi reproduzida
integralmente. PREABE é proxy diário para abertura, sem spread, impacto,
book ou prova de execução no leilão. Não existe ordem para corretora.

## Dados e isolamento

Fonte local lida: `C:/Users/LUCAS/Meu Canto/TCC/Hedge-Fund-Lab/data/platform/`.
Somente `market-base-v1` e `stock-history-v1`, em leitura, sem abrir o banco
de carteiras de produção. Os snapshots Yahoo foram coletados em 20/10/2026;
fatores posteriores podem reescrever o passado. Datas de aquisição, hashes dos
arquivos B3 e fontes de ajustes ficam no bundle. O bloco não contém splits
nem eventos de caixa novos nos snapshots B3/Yahoo inspecionados; splits ou
dividendos Yahoo sem correspondência B3 bloqueiam o preparo.

Raízes absolutas neste checkout:

- Real preparado: `C:/Users/LUCAS/.codex/worktrees/b507/Hedge-Fund-Lab/data/cache/historical-replay/april-2026-flash/`.
- Teste: `C:/Users/LUCAS/.codex/worktrees/b507/Hedge-Fund-Lab/data/cache/historical-replay/april-2026-flash-offline/`.

Cada raiz contém `manifest.json`, `market.json`, proventos selados em `market/`,
50 inputs/CSVs em `sessions/<alvo>/radar/analyses/`, `preflight.json` e,
depois da execução, `book/manual.sqlite3`, bancos de chamadas, contextos,
propostas, `day.json` e `report.json`. `execution_mode.json` impede misturar
respostas de teste com inferência real. Uma sessão reclamada sem conclusão exige
revisão; reexecutar não paga novamente. Falhas preservam bancos/envelopes;
nesta primeira versão não há CLI automática para recuperá-las. Não apagar claims.

## Orçamento e único bloqueio

Até **310 chamadas**: 10 × (5 ativos × até 6 + 1 gestor), sem retries.
Preços [oficiais Standard](https://aistudio.google.com/docs/pricing#gemini-3.8-flash),
reverificados em 12/11/2026: US$ 0,75/1M de entrada e US$ 3,75/1M de saída,
incluindo thinking. Reservas existentes usam os tetos US$ 1,50 / US$ 7,50.

| Medida | USD |
|---|---:|
| Reserva conservadora por sessão | 3,477504 |
| Reserva conservadora do bloco | **34,775040** |
| Máximo com os limites de tokens/bytes e tarifas atuais | **17,387520** |
| Estimativa de planejamento dos analistas (não uso observado) | 1,46250 |
| Gestor | Depende do contexto; incluído integralmente na reserva |

O teto conservador arredondado para autorizar é **US$ 34,78**. Não é custo
esperado nem promessa de cobertura por créditos. O teto diário US$ 4 da DP-34
é da rotina diária, não uma autorização de campanha histórica.
Lucas aceitou o teto agregado, inclusive se os créditos não forem elegíveis.
Um preflight com teto explícito valida todo o bloco antes de emitir seu token.

## Verificação e execução

**Ocorrência real e revisão:** em 07/04, uma chamada técnica de ITUB4 teve
`ProviderTransportError` / WinError 10054 (conexão encerrada pelo host remoto),
sem envelope ou usage recuperável. Sem quórum completo, não houve chamada do
gestor nem operações. Revisão técnica selada em `sessions/2026-04-07/review.json`
registrou `NO_ANALYSIS`, manteve posições/caixa e permitiu seguir em 08/04 sem
repetir a requisição incerta. Esse dia entra na trajetória patrimonial, mas não
na contagem de análises completas; não se inventa voto ou decisão HOLD.
Em 10/04, um voto de BBAS3 teve o mesmo WinError 10054 e recebeu o mesmo
tratamento, registrado no `review.json` daquele dia; retomada em 13/04.
Em 14/04, o mesmo erro ocorreu na chamada de risco de BBAS3, após os votos
técnicos: o parecer final ficou incompleto, sem gestor/operação; os votos
recebidos foram preservados. Revisão registrada e retomada em 15/04, propagando
a posição de VALE3 comprada em 13/04 e o caixa remanescente.

O leitor de relatório do runner congelado também revelou uma incompatibilidade:
espera selo em `failure.json`, mas as falhas do Radar são JSON sem selo. Para
preservar o manifest/código que efetivamente geraram as chamadas, o adaptador
`scripts/report_multiasset_replay.py` lê os bancos diretamente, confere hashes
dos envelopes/records e substitui somente o escritor de relatório com o helper
`bind` existente. Não muda prompts, inferência, validação, execução ou livro.
O custo da resposta ausente é desconhecido, limitado separadamente; ausência
de `thoughts_tokens` só vira zero quando total = entrada + saída o comprova.
O relatório corrente deve ser gerado com esse adaptador:

```powershell
& $py scripts/report_multiasset_replay.py report --id april-2026-flash
```

Sem rede, primeiro uma sessão, depois dez, usando o parser nativo e respostas
de teste identificadas: **310 chamadas simuladas e 13 operações conferidas**.
Resultado final do check: `april-2026-flash-offline/checks.json`, `status=PASS`.
Check persistente: `tests/check_multiasset_replay.py`:
isolamento, mesma base inicial, propagação financeira, taxas, OPEN oficial,
Buy & Hold constante, ausência de orçamento implícito, reexecução idempotente
com sockets bloqueados e separação offline/live. Barras futuras adulteradas
produzem inputs/CSVs idênticos aos originais. Números do teste não são resultado
de investimento Gemini.

Regressão dos componentes: **63 passed, 1 skipped, 9 subtests passed** em
`test_wallet_manager.py` e `test_manual_portfolio.py`; skip de navegador.
Radar: **15 passed, 1 failed**; o teste de preservação histórica encontra
CRLF de checkout Windows em evidências com SHA esperado LF. Não foram alteradas
expectativas nem evidências para esconder a falha. As 52 fontes requeridas pelo
gate de Radar foram repostas com bytes LF já presentes no Git; nenhum diff
de lógica no legado. Ruff dos dois arquivos novos passou. Sem teste de navegador:
nenhuma interface nova.

PowerShell, a partir da raiz deste checkout (o ambiente Python existente foi
reutilizado, sem dependência nova):

```powershell
$py = 'C:/Users/LUCAS/Meu Canto/TCC/Hedge-Fund-Lab/.venv/Scripts/python.exe'
& $py tests/check_multiasset_replay.py --id april-2026-flash-offline
& $py scripts/replay_multiasset.py preflight --id april-2026-flash
# Somente após a escolha do teto por Lucas:
$check = (& $py scripts/replay_multiasset.py preflight --id april-2026-flash --max-usd 34.78) | ConvertFrom-Json
if (-not $check.ready) { throw 'Preflight bloqueado; consultar errors' }
& $py scripts/replay_multiasset.py live --id april-2026-flash --max-usd 34.78 --confirm $check.confirmation_token
& $py scripts/report_multiasset_replay.py report --id april-2026-flash
```

O [relatório real](../reports/replay_multiasset_2026-04.md) registra patrimônio
final R$ 102.503,49 versus R$ 102.498,88, diferença de R$ 4,61 (0,00461 p.p.).
Foram 305 tentativas HTTP, 302 respostas com uso conhecido, três erros sem
resposta recuperável; 373.010 tokens conhecidos, sem afirmar total integral.
Custo conhecido estimado US$ 0,4650735, até US$ 0,6309615 incluindo o limite
das respostas incertas. Latências somadas 1.187,1 s; tempo corrido 25,24 min.
Nenhuma tentativa HTTP foi repetida. Fontes executadas preservadas em `runtime/`.
Próximo passo: incorporar a evidência exploratória ao TCC com as lacunas e
premissas declaradas, sem ampliar automaticamente o ensaio.

O preflight real foi refeito com o teto autorizado US$ 34,78 antes da chamada;
a autorização agregada está selada em `authorization.json`. Manifest real:
`95538e340b18c4aeb5f14c30b55e71e21c36b3b73b7e60df0c3c31c6408720f9`.
O livro isolado é `book/manual.sqlite3`; `checks.json` registra a reconciliação
real, e `report.json` distingue as sete análises completas das três lacunas.

```powershell
& $py tests/check_multiasset_replay.py --id april-2026-flash --real
```

## Segunda janela autorizada em 13/11 — 20/04 a 05/05

Lucas escolheu o bloco A após a triagem de queda e autorizou teto agregado próprio
de US$ 34,78. `replay_multiasset_window.py` adapta somente datas via `bind` e usa
o leitor/recuperação já qualificado, preservando o runner e os registros do
primeiro ensaio. Manifest/identidade, autorização, bancos e carteiras próprios
em `data/cache/historical-replay/april-may-2026-flash/`; fontes em `runtime/`.

Execução concluída: dez marcações, oito análises completas e duas falhas de
transporte (ITUB4 em 23/04, WEGE3 em 30/04), sem repetição das respostas incertas.
Nove operações, com redução e encerramento de BBAS3, redução de WEGE3 e VALE3,
compras de ITUB4, VALE3 e PETR4. Nos quarenta pareceres de dias completos:
10 COMPRA, 23 MANTER, 7 VENDA. Não foram alterados prompts/gates para gerar vendas.

Resultado líquido: agentes R$ 92.668,80 / −7,3312%, B&H R$ 92.800,14 / −7,19986%;
diferença −R$ 131,34. Caixa final R$ 14.246,87 / R$ 146,11 e direitos a receber
R$ 252,54 / R$ 252,49. Quantidade ao fim da data-com, JCP líquido, centavos por
evento e ausência de caixa antes do pagamento reconciliados. Aumento posterior
de PETR4 não gerou direitos adicionais; aumento anterior de ITUB4 gerou R$ 0,05.

306 tentativas na campanha inteira, incluindo retomadas; 375.498 tokens conhecidos.
Custo estimado conhecido US$ 0,4645395; limite adicional incerto US$ 0,110592;
total com esse limite US$ 0,5751315, sem fatura/saldo de créditos confirmado.
Os checks reais e de proventos passaram; 528 arquivos do primeiro ensaio foram
conferidos byte a byte. [Relatório novo](../reports/replay_multiasset_2026-04-20_2026-05-05.md).

```powershell
& $py scripts/replay_multiasset_window.py report --id april-may-2026-flash
& $py tests/check_multiasset_replay.py --id april-may-2026-flash --real --receivables
```

## Campanha contínua de seis carteiras — 13/11

Autorização própria para06/04–12/11/2026,153pregões, teto agregado únicoUS$34,78.
Buy & Hold, SMA50/200, Bollinger20/2, Equal Weight63 e Mínima Variância252/63
foram concluídas antes da API. Entrada DP-20 comum; referências não reinvestem
proventos. Multiagentes mantém o gestor e todo o caixa disponível do livro;
recebíveis somente entram no caixa no pagamento. Não junta os pilotos anteriores.

Raiz dos dados/orçamento:
`data/cache/continuous-replay/april-november-2026-flash/`.
`active_campaign.json` aponta a fase final **`qualified-v2/`**; o orçamento
continua no mesmo `budget.sqlite` pai. Livro, checkpoints, sessões e exports
finais ficam no subdiretório. Os livros/153marcas diagnósticas anteriores foram
preservados, não são a referência final da Mínima Variância.

Reparos anteriores à inferência: identidade por componente B3 para JCPs com as
mesmas datas/tipo; e normalização positiva da escala da função-objetivo SLSQP.
Mantém covariância, janela, frequência e restrições, sem usar retorno futuro.
Conferência de765estados finais PASS, incluindo todos os componentes de
proventos, fills/custos e KKT das três decisões de Mínima. Exemplo analítico10/90,
invariância de escala, matriz nula, retry/cap/crash/retomada também PASS.
Nenhuma fonte selada alterada. [Inventário e diagnóstico](../reports/inventario_replay_continuo_2026-11-13.md).

Comandos de referência da execução histórica, somente na worktree/revisão e
ambiente Python já qualificados. A campanha está concluída: consultar o pacote
exportado não exige `--live`, retomada ou novas inferências:

```powershell
# Se já houver processo vivo no PID de qualified-v2/status.json, acompanhar esse processo.
# Depois de uma interrupção, este mesmo comando retoma os mesmos livros e orçamento.
& $py scripts/continuous_replay.py --live
& $py tests/check_continuous_replay.py data/cache/continuous-replay/april-november-2026-flash/qualified-v2
& $py scripts/export_continuous_replay.py
```

Não recriar raiz, trocar datas/fontes ou zerar/copiar o orçamento para retomar.
O código/verificação de identidade bloqueia fontes diferentes; `runtime-final/`
e `runtime_attestation.json` preservam fontes e versões utilizadas. O lock do
processo impede dois executores. Cada tentativa HTTP tem reserva durável antes
da saída, no máximo duas por chamada lógica; resposta recebida/durável é sempre
reutilizada, inclusive após interrupção antes do registro interpretado. Resposta
inválida não é substituída. Tentativa incerta permanece com reserva integral.
Falha de integridade/teto interrompe; quorum/schema/vetos não são relaxados.

`status.json`, logs e checkpoints estão em `qualified-v2/`; o SQLite pai agrega
custo conhecido + incerteza + chamadas em voo de toda a campanha. CSV/JSON de
sessões, operações, decisões, proventos e chamadas em `qualified-v2/exports/`.
Os artefatos são locais e ignorados no Git. A inferência ocorreu em 13/11,
das 17:41 às 22:28 (São Paulo), após a qualificação, e concluiu 153/153 dias.
O frontend foi construído depois dos resultados; não há campanha em execução.


## Explorador local e entrega final

Entrega DP-37 / REPLAY-01 concluída (regras SMA/Bollinger da DP-36): `checks.json`, `budget_audit.json`,
`preservation_check.json` e `ui_checks.json` em `qualified-v2/` registram PASS.
São 918 estados diários, sem lacunas; os pilotos e as evidências diagnósticas
permanecem separados. [Relatório final](../reports/replay_continuo_2026-04_2026-11.md).

Com Python instalado, extraia o pacote `explorador_replay_2026-04_2026-11.zip`
e execute na pasta extraída:

```powershell
python abrir_explorador.py
```

O inicializador usa apenas a biblioteca padrão, serve a pasta em 127.0.0.1,
abre o navegador e encerra com Ctrl+C. Mantenha os arquivos juntos. Consulta local
sem novas inferências ou alteração do livro. Na worktree, o mesmo inicializador
fica em `data/cache/continuous-replay/april-november-2026-flash/qualified-v2/exports/`.
Para reconstruir o HTML a partir das exportações reconciliadas:

```powershell
& $py scripts/build_replay_explorer.py
```

O explorador compara as seis curvas e mostra a carteira/dia selecionados,
posições, votos e risco, decisões quantitativas, operações, recebidos e recebíveis,
chamadas reais carregadas sob demanda e CSV/JSON. Textos dos modelos são evidências
preservadas e podem conter erros; não são fatos certificados. Alterar o recorte
não reinicia o retorno acumulado desde D0. Recibos de fontes e auditoria ficam
acessíveis. Navegação por teclado nas abas e rótulos dos filtros presentes.

Verificação HTTP local em 1280 e 390 px: valores finais das seis carteiras,
rebalanceamento Mínima, fill de duas WEGE3, dois componentes JCP BBAS3 na mesma
data, retry preservado, filtros e exportações, sem erros no console ou overflow
horizontal. A política de URLs do navegador de teste permite apenas HTTP/HTTPS
e bloqueou a abertura direta file://; esse modo não foi verificado e não houve
contorno da restrição. O servidor temporário de QA é encerrado na entrega.

Cópia de entrega privada fora da worktree:
`C:/Users/LUCAS/Meu Canto/TCC/Hedge-Fund-Lab/output/replay-continuo-20261113/`.
Contém o pacote de exploração, relatório, capturas e arquivo completo de evidências
com manifesto SHA-256. Não substitui os originais nem altera aplicação/produção.
Próximo passo: explorar os resultados e incorporar a análise descritiva no TCC.
