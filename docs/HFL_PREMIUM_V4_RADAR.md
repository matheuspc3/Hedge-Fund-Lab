# Premium V4 — Radar multiativos

Identidade: `HFL-MULTIASSET-RADAR-V1`. Consultivo, exploratório, separado de
Validation OA-1, Final Test e Forward PETR4. Nenhuma ordem ou carteira global
é produzida. Projeto da próxima versão:
[HFL_MULTIASSET_PORTFOLIO_DESIGN.md](HFL_MULTIASSET_PORTFOLIO_DESIGN.md).

## Auditoria e reutilização

| Componente examinado | Reutilização / limite identificado |
| --- | --- |
| `src/agents/participant.py` e H2 v6 | Participante completo recusa universo multiativo; estado tem posição escalar, cash, equity e pico de patrimônio. Não instanciar esse participante como gestor global. |
| Cinco Technical Analysts | Reutilizados pelo nó existente: prompt v5, schema estruturado v2, features adimensionais, T=1, thinking low, 8192 tokens, sementes 10001–10005, quorum 3/5 e todos os votos válidos. Nenhum prompt H2 alterado. |
| Indicadores e evidências | `DataTransformer`, `dimensionless_features`, validação e vocabulário existente. Explicações são evidências dos agentes, sem ranking por confiança. |
| Risk original | Requer concentração e drawdown da carteira. Não fabricar carteira vazia ou emprestar o estado PETR4. Novo Risk consultivo recebe apenas features, consenso e volatilidade do ativo. Regra dura de volatilidade >50% veta antes da sexta chamada. Concentração, drawdown da carteira e adequação ao capital ficam `NOT_EVALUATED`. |
| Portfolio Manager | Mesmo no modo qualitativo, integra a decisão e sizing do participante single-asset. Não invocado pelo radar. Parecer final é o consenso aprovado pelo Risk, ou MANTER no veto. Não emite quantidade, peso ou ordem. |
| Forward PETR4 e supervisão | Leitura do desenho de preparação, identidade, reconciliação e aprovação. Nenhuma importação do estado ou escrita nessas carteiras. A decisão de 09/10 e ledgers originais permanecem intactos. |
| Premium V3 | Mantidos servidor stdlib, proteção Host/Origin/CSRF e Sala de Decisão. Acrescentados rota `/radar`, API isolada e link na navegação Paper. |
| B3 e ajustes | Extrator existente mantém COTAHIST oficial × fator yfinance, veto a desdobramentos incompatíveis e herança de fatores somente quando vizinhos concordam. Cache científico de anos fechados é somente leitura; novos downloads vão ao radar. Preço bruto e ajustado registrados separadamente. |
| Journals e locks | `CallBank` e `DurableGeminiClient` existentes, com identidade nova e banco por ticker/sessão. Reserva e envelope fsync/FULL antes de transporte/validação. Override da sessão pertence ao radar, sem editar os gates da avaliação. Lock existente protege lote entre processos; sem retries automáticos. |
| Manifesto e integridade | Original enumera dinamicamente `src/**/*.py`. Código novo fica em `scripts`, preservando a lista de 73 fontes. Cada input registra manifesto e hashes das fontes reutilizadas e novas. Nenhum inventário original ou hash é atualizado. |

Mudanças metodológicas declaradas: histórico mínimo de 200 sessões reais
(SMA200 disponível), cobertura solicitada de 450 dias, inicialização MACD sobre
esse histórico, risco do ativo separado da carteira, máximo seis chamadas e
uma tentativa por chamada. Isso não reproduz a H2 v6 completa nem sua série
desde 2016. Empresas com IPO recente podem ser analisadas ao completar o
histórico mínimo; lacunas e sessões sem negócio bloqueiam, sem preenchimento.
Calendário local B3 é verificado originalmente até 31/08/2026; fora disso,
a presença das barras oficiais e a igualdade da grade são gates adicionais.

## Usar sem chamadas pagas

```powershell
# Exemplo completo: cinco comitês, fake Gemini nativo, rede bloqueada, custo zero.
.venv/Scripts/python.exe scripts/run_multiasset_radar.py demo --root data/radar/demo-v4 --session 2026-10-09

# Servidor para consultar o exemplo; nenhuma inferência ao abrir a página.
$env:HFL_RADAR_ROOT = 'data/radar/demo-v4'
.venv/Scripts/python.exe dashboard/server.py 8086
# Abra http://localhost:8086/radar
```

O comando demo é explícito e não autoriza o Gemini real. Uma segunda execução
na mesma identidade/ticker/sessão é recusada. Consulte `status`, a interface,
ou use `replay`. Não exclua claims para contornar a proteção. Mantenha o demo
em raiz separada do radar oficial, pois os dois modos não sobrescrevem inputs.

## Preparar e executar dados oficiais, quando autorizado pelo usuário

```powershell
Remove-Item Env:HFL_RADAR_ROOT -ErrorAction SilentlyContinue
.venv/Scripts/python.exe scripts/run_multiasset_radar.py universe --tickers PETR4 VALE3 ITUB4 WEGE3 BBAS3
.venv/Scripts/python.exe scripts/run_multiasset_radar.py prepare --tickers PETR4 VALE3 --session 2026-10-09
.venv/Scripts/python.exe scripts/run_multiasset_radar.py preflight --tickers PETR4 VALE3 --session 2026-10-09 --max-usd 2
# Somente após autorização explícita: chave GEMINI_API_KEY no ambiente local.
.venv/Scripts/python.exe scripts/run_multiasset_radar.py run --tickers PETR4 VALE3 --session 2026-10-09 --max-usd 2 --confirm <confirmation_token_do_preflight> --authorize-paid
```

`prepare` acessa B3/yfinance, nunca LLM. `preflight` é offline e não grava.
O token vincula seleção, sessão, input hashes, modo, orçamento e reservas
globais. Mudanças exigem novo preflight. A interface exige aceite explícito
de cobrança para lotes oficiais. É possível selecionar somente um ativo.
Um lote não pronto não executa; após a execução começar, cada ativo tem
commit independente e falhas não apagam os demais.

## Custos

Consulta e testes: **US$ 0**. Planejamento por ativo: até seis chamadas,
2.500 tokens de entrada e 800 de saída por chamada (hipótese declarada, não
média observada). Gemini 3.8 Flash Standard: US$ 0,75/1M entrada e US$ 3,75/1M
saída, incluindo pensamento, até 31/12/2026; US$ 1,50/7,50 a partir de 2027.
Fonte consultada em 11/10/2026:
[tabela oficial Google](https://ai.google.dev/gemini-api/docs/pricing).

| Ativos | Estimativa USD | Reserva conservadora USD |
| --- | ---: | ---: |
| 1 | 0,02925 | 0,663552 |
| 5 | 0,14625 | 3,317760 |

A reserva considera 32.768 tokens de entrada e 8.192 de saída por chamada,
seis chamadas, uma tentativa e as tarifas maiores anunciadas para 2027.
O transporte recusa corpos acima do limite de bytes correspondente.
Limite global cumulativo desta raiz: US$ 5; reservas incertas não são liberadas
automaticamente. Isso é deliberadamente conservador. Falha e uso sem
telemetria não podem ser contabilizados como custo zero. `cost_usd` de análise
completa deriva dos tokens informados pelo provedor, incluindo pensamento,
e é estimativa de faturamento, não fatura. Nenhuma chamada paga foi necessária
para a qualificação.

## Persistência e recuperação

Raiz padrão `data/radar/hfl_multiasset_v1/`, independente dos ledgers:

```text
universe.json                     # configuração até cinco tickers
last_prepare.json                 # último lote de preparação e falhas por ativo
job.json                          # comando assíncrono da interface
reservations/<batch-token>.json   # teto global reservado antes de inferir
analyses/<ticker>/<session>/
  input.json, bars.csv            # input imutável, manifesto, origem, hashes
  claim.json                     # identidade/ticker/sessão reservados uma vez
  calls.sqlite                   # CallBank durável existente (journal local)
  provider_journal.jsonl          # export completo e hash, jamais servido como envelope
  result.json, result.sha256      # cinco votos, consenso, Risk, parecer, tokens e custo
  failure.json                   # estado de falha; sem mensagens de provedor/segredos
  events/<id>.json                # histórico imutável com hash por evento
```

São contratos JSON versionados, sem dependência de ORM ou backend web. A
SQLite reutilizada é exclusivamente o journal local já existente, não uma
migração da arquitetura de arquivos. Não adicionar PostgreSQL nesta fase.

```powershell
.venv/Scripts/python.exe scripts/run_multiasset_radar.py status --root data/radar/demo-v4
.venv/Scripts/python.exe scripts/run_multiasset_radar.py replay --root data/radar/demo-v4 --tickers PETR4 --session 2026-10-09
```

Replay reconstrói somente respostas reservadas e duráveis. Resposta incerta,
ausente, corrompida ou chamada não reservada falha fechado; nunca substitui
inferência. Se o processo morrer antes de publicar o resultado, envelopes
completos permitem terminar a publicação offline. Resultados já selados são
consultados diretamente. Votos parciais válidos e eventos ficam disponíveis
na Sala de Decisão mesmo sem parecer final.

Locks contêm PID e não expiram automaticamente. Após crash, verifique o PID
gravado em `operation.lock` com `Get-Process -Id <pid>` e confirme que nenhum
runner está ativo antes de remover **somente esse lock**. Não remover claims,
reservas ou journal. Depois, execute `replay`. PID ainda ativo/reutilizado
permanece bloqueado e exige diagnóstico. Uma falha antes de reservar um ticker
permite preparar um novo lote apenas com tickers ainda sem claim; uma reserva
global de lote interrompido permanece conservadoramente comprometida.

## API local

| Método / rota | Payload ou parâmetros |
| --- | --- |
| GET `/api/radar/status` | universo, resultados, datas, reservas, job e CSRF; sem inferência |
| GET `/api/radar/search?q=PETR` | catálogo histórico local COTAHIST; validação de negociação na preparação |
| GET `/api/radar/detail?ticker=PETR4&session=2026-10-09` | resultado/votos parciais e histórico, sem envelope de provedor |
| POST `/api/radar/universe` | `tickers` |
| POST `/api/radar/prepare` | `tickers`, `session`, `mode` (`live` ou `synthetic`) |
| POST `/api/radar/preflight` | `tickers`, `session`, `max_usd`, `replay` |
| POST `/api/radar/run` | campos do preflight mais `confirmation_token`, `authorize_paid`, `confirm` |

POST exige Origin local, Host validado, JSON limitado e X-CSRF-Token da sessão.
Preparação/execução usam thread e lock local; status persiste para diagnosticar
interrupções. Comparação lado a lado exige empresas distintas, mesma sessão e
fonte; horários de geração individuais continuam explícitos. Sessões e fontes
diferentes nunca são mostradas como uma observação simultânea.

## Verificação

```powershell
.venv/Scripts/python.exe tests/test_multiasset_radar.py -v
.venv/Scripts/python.exe -m ruff check scripts/multiasset_radar.py scripts/run_multiasset_radar.py dashboard/radar_api.py dashboard/server.py tests/test_multiasset_radar.py
node --check dashboard/radar.js
```

Evidências em [evidence/hfl_multiasset_radar](evidence/hfl_multiasset_radar).
O baseline inclui fontes inventariadas, evidências científicas e arquivos
locais do Forward existentes antes da mudança. Exclui apenas logs HTTP
voláteis e locks, que não são ledgers. O teste confere hashes e executa o
verificador original do manifesto sem alterar seus arquivos. `clean=False`
nesse **teste de leitura** permite verificar durante desenvolvimento; os
gates originais de execução continuam exigindo Git limpo, sem exceção nova.
