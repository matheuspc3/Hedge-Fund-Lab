# Dashboard operacional H2 v6

## Análise técnica inicial

O servidor existente é `http.server` com threads, loopback e Chart.js local.
As seis abas históricas usam `h2.js` e `h2_api.py`; esses arquivos não precisam
de alteração. Um link acima do menu leva ao novo espaço `/paper`, com Sala de
Decisão e Carteiras, evitando ampliar o menu histórico.

O runner `scripts/run_h2_v6_forward.py` já oferece prepare/preflight/run,
entrada causal congelada, prazo de abertura, lock do ledger, confirmação pelo
hash e journal durável com recuperação exclusivamente por replay. Ele será o
único caminho de inferência. O preflight exige Git limpo: alterações em
desenvolvimento bloqueiam a operação até o commit.

A sessão real 09/10/2026 foi decidida em 10/10 para a abertura de 13/10.
São cinco votos de COMPRA, risco aprovado e alvo 100%; a posição financeira
observada ainda é caixa de R$ 100.000, com zero trades/custos executados.
O texto de explicação contém um problema de codificação já presente no trace;
a consulta preserva o texto gravado, sem corrigir os arquivos científicos.

## Fase A — consulta

Implementados `/api/forward/history`, `/api/forward/decision?session=YYYY-MM-DD`
e `/api/forward/portfolios`, além de `/paper`. A API projeta explicitamente os
campos de decisão e de trace; não oferece download dos arquivos forward.
Analistas ausentes permanecem ausentes, sem votos sintéticos. Evidências são
agrupadas por código/papel, mantendo os registros individuais acessíveis.
IA e B&H vêm exclusivamente do ledger forward existente, sem curvas Validation.

O servidor valida Host/Origin, restringe arquivos estáticos a uma lista fixa,
desabilita listagem de diretórios e mantém bind 127.0.0.1. Não há acesso HTTP a
código Python, paths arbitrários ou provider journals.

## Integridade

`docs/evidence/h2_forward_dashboard/protected_before.json` registra os hashes
anteriores à implementação: inventários do candidato, `src/`, evidências de
OA-1, artifacts de Validation, runner, Chart.js e todos os arquivos forward
existentes, inclusive a decisão de 09/10. Conferência repetível:

```powershell
.venv/Scripts/python.exe -B scripts/check_h2_forward_dashboard.py
.venv/Scripts/python.exe -B dashboard/server.py 8081
```

Abrir `http://127.0.0.1:8081/paper`. Abrir ou consultar a página nunca chama Gemini.

## Fase B — operação

`forward_jobs.py` executa exclusivamente os comandos fixos do runner original,
com `shell=False`, em uma thread por job e um subprocesso por comando. Isso
também isola o bloqueio de rede do preflight: ele não altera os sockets das
threads HTTP. Há um único lock de operações compartilhado entre processos.

| Método | Endpoint | Comportamento |
|---|---|---|
| GET | `/api/forward/history` | Sessões decididas, preparadas e MISSED |
| GET | `/api/forward/decision?session=YYYY-MM-DD` | Projeção do trace/decisão e execução observada |
| GET | `/api/forward/portfolios` | Ledgers prospectivos, composição e comparação compatível |
| GET | `/api/forward/status?job=<32 hex>` | Job persistido, progresso observado e CSRF desta instância |
| POST | `/api/forward/prepare` | `prepare` original; payload `{}` |
| POST | `/api/forward/preflight` | `preflight` original offline; payload `{}` |
| POST | `/api/forward/run` | Exige `{confirm:true, confirmation_token:"…"}` |
| POST | `/api/forward/benchmarks` | Sincroniza os dois runners determinísticos; payload `{}` |

POST exige Host exato, Origin igual ao Host, JSON limitado a 4096 bytes, token
CSRF em `X-CSRF-Token`, ausência de campos extras, chaves duplicadas e valores
não finitos. Requests cross-site/same-site são recusados; só navegação top-level
para HTML público é permitida. APIs e subrecursos não recebem essa exceção.
Respostas proíbem frames, para evitar sobreposição de cliques de confirmação.

O preflight READY emite confirmação HMAC com validade de 10 minutos, ligada ao
input completo, ledger, runner, sessão e prazo. A confirmação é revalidada
antes de reservar a tentativa; outro preflight é executado antes do `run`, que
também aplica seus próprios gates. Mudança de input, ledger, prazo ou processo
invalida a confirmação. Chaves Gemini nunca vão ao browser.

`data/forward/h2_v6_dashboard/run-<S>.json` é um claim write-once, gravado e
sincronizado em disco antes do subprocesso. Cliques duplicados, recarga, dois
navegadores ou dois servidores não criam uma segunda execução. Após falha,
o claim permanece: não há botão de retry pago nem desbloqueio automático.
Decisão existente é somente consulta, inclusive FAILED/LATE_NOT_EXECUTABLE.

Jobs e progresso sobrevivem à recarga. Contagens vêm apenas das linhas `calls`
do SQLite em modo read-only: sequência, etapa, status e presença de resposta.
O HTTP não retorna stdout/stderr, requests, raw, record, prompts ou journal.
Prepare e preflight mostram início e conclusão reais, sem percentuais inventados.
Erros de gate têm identificação; erros do runner oferecem código de saída e
orientação para diagnóstico local, sem expor envelopes.

### Recuperação

Se a instância foi encerrada durante um job, o lock persistente bloqueia novas
operações. Examine localmente o job, o PID e os registros do runner. Não apague
`decision.json`, claims ou reservas para tentar novamente. O runner científico
mantém sua recuperação por replay; o dashboard não executa recuperação paga.
Um token de preflight antigo deixa de funcionar após reiniciar o servidor.
Uma queda entre a decisão e `state.json` permanece bloqueada pelo runner;
a interface não tenta reparar nem inventa uma execução financeira.

## Benchmarks prospectivos

Dois comandos separados da inferência, usando um entrypoint comum mínimo:

```powershell
.venv/Scripts/python.exe -B scripts/run_h2_v6_forward_benchmarks.py sma_regime_h2_proposed
.venv/Scripts/python.exe -B scripts/run_h2_v6_forward_benchmarks.py bollinger_state_h2_proposed
```

Reutilizam literalmente `BENCHMARK_FACTORIES`/`BENCHMARK_SPECS`: SMA é estado
50 > 200; Bollinger é estado 20/2 com persistência do alvo, não cruzamentos do
benchmark legado. A carteira nasce em caixa; não herda posições do warm-up.
Liquidação, custos, calendário, normalização de unidades entre vintages e
capital vêm do forward original. Só o histórico truncado em S chega à estratégia.
Não há nova implementação de indicadores, sizing ou inferência.

Os novos ledgers ficam em `data/forward/h2_v6_benchmarks/<strategy>/state.json`.
Nenhum arquivo da carteira IA/B&H é escrito por esses comandos. A inicialização
comum só é aceita enquanto a primeira abertura da IA ainda está no futuro e
o primeiro fechamento continua sendo a última sessão encerrada. `initialized_at`
registra o instante real; a referência pode ser o fechamento anterior, mas a
ordem só vale para uma abertura futura. Se esse período já passou, o runner
recusa `NOT_COMPARABLE`, sem reconstruir ordens passadas. Criar um novo período
conjunto exigiria uma decisão metodológica explícita fora deste dashboard.

Em lacunas, ordens já pendentes são liquidadas nos preços observados e sessões
sem decisão são MISSED; só S recebe uma decisão nova. Repetir o mesmo comando
na mesma sessão é idempotente. Atualize dados, execute a IA com confirmação
quando elegível, e sincronize os benchmarks antes da próxima abertura.
A comparação exige início, capital, custos, execução, manifesto e todas as
datas/aberturas/fechamentos iguais. Carteira divergente é identificada e excluída
do gráfico; a composição individual continua consultável.

## Verificação

Os testes operacionais usam comandos falsos e fixtures sintéticas. Cobrem READY,
decisão existente, pendência, execução, MISSED, FAILED, prazo, alteração de
input/ledger, token adulterado/expirado, recarga, dois servidores, clique
duplicado, payloads, CSRF/Host/Origin, paths, isolamento dos dados e regras dos
benchmarks. O harness Node executa o `paper.js` real e exige checkbox e clique
final; abrir/recarregar não produz POST. Gemini não foi executado.

```powershell
.venv/Scripts/python.exe -B -m pytest tests/test_h2_forward_dashboard.py tests/test_h2_dashboard_async.py tests/test_h2_dashboard_analysis.py tests/test_h2_v6_forward.py -q -p no:cacheprovider --basetemp=./data/forward/dashboard_checks
.venv/Scripts/python.exe -B scripts/check_h2_forward_dashboard.py
```

O Windows sandbox impediu o pytest de acessar os próprios diretórios temporários;
os testes foram executados fora dele, mantendo fixtures isoladas e bloqueio de
rede externa na suíte completa. Nenhuma configuração de segurança foi alterada.

Screenshots de Chrome: [1440 px](evidence/h2_forward_dashboard/paper-1440.jpg),
[640 px](evidence/h2_forward_dashboard/paper-640.jpg),
[420 px](evidence/h2_forward_dashboard/paper-420.jpg). Todos usam a sessão real
de 09/10 e distinguem alvo 100% da posição observada em caixa.
As quatro carteiras estão na [captura de Carteiras](evidence/h2_forward_dashboard/paper-wallets-1440.jpg).
Medições DOM e navegação das seis abas: `evidence/h2_forward_dashboard/browser-checks.json`.

SMA e Bollinger foram inicializadas de fato em 10/10/2026, antes da abertura de
13/10, a partir do input congelado `8acf2b53eb36…`. Ambas começam no fechamento
de referência 09/10, em caixa, como IA/B&H. Todas têm R$ 100.000, retorno zero,
zero operações e custos zero. SMA registra alvo 100% para 13/10; Bollinger
mantém alvo zero. Essas são recomendações futuras; nenhuma execução foi inferida.
O preflight após o commit confirmou a identidade `gemini-3.8-flash`, T=1,
thinking low, e retornou DECISION_EXISTS para a IA. A reserva/journal existente
não mudou. O servidor de verificação está em `http://localhost:8082/paper`;
a porta 8081 já estava ocupada por uma instância anterior, que foi preservada.

Arquivos implementados: `dashboard/forward_api.py`, `dashboard/forward_jobs.py`,
`dashboard/paper.html`, `dashboard/paper.css`, `dashboard/paper.js`,
`scripts/run_h2_v6_forward_benchmarks.py`, `scripts/check_h2_forward_dashboard.py`,
`tests/test_h2_forward_dashboard.py`; integração em `dashboard/server.py` e
link de navegação em `dashboard/h2.html`. Documentação e evidências neste arquivo
e em `docs/evidence/h2_forward_dashboard/`.

### Resultados de regressão

Regressão focada (dashboard operacional, seis abas, forward e geração histórica):
**36 passed**, sem Gemini. Ruff e `node --check` aprovados. Chrome confirmou as
seis abas, dados OA-1 carregados e console sem erros. Layout verificado em
1440, 640 e 420 px; sem overflow horizontal após a atualização de tamanho.
Prepare real reaproveitou o input existente; preflight real retornou
DECISION_EXISTS e manteve a inferência desabilitada.

A primeira execução integral teve 1451 passed / 12 failed. Um teste do novo
harness precisava inicializar o stub de `<dialog>` e foi corrigido; outro gate
exigia a árvore Git limpa durante desenvolvimento. Os dez casos restantes
estão fora do patch: sete testes ETL exigem PostgreSQL em `127.0.0.1:5435`,
ausente, e três testes antigos esperam estados anteriores do registry e das
evidências v5/v6. Seus módulos e evidências não foram alterados. Não se mudaram
os arquivos científicos para adaptar essas expectativas.
