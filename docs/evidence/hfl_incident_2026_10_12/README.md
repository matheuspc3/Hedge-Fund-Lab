# Incidente Radar 12/10/2026 02:59 BRT — guard offline em inferência real

Lote oficial `d3877668…` (PETR4, VALE3, ITUB4, WEGE3, BBAS3; sessão 09/10):
25 chamadas reservadas, 25 `TRANSPORT_ERROR` `RuntimeError: offline qualification
forbids network`, zero envelopes, zero pareceres. Registro forense somente
leitura com hashes: [forensics.json](forensics.json). Testes:
`tests/test_radar_network_isolation.py`. Regressão: [regression.txt](regression.txt).

## 1. Causa-raiz comprovada

`src/experiments/h2_evaluation_offline.py`, função `no_network()`, linhas 123–129:
`patch.object` substitui `socket.socket.connect`, `socket.socket.connect_ex` e
`socket.create_connection` **no processo inteiro**, não na thread que a chamou.
No servidor (`ThreadingMixIn`), qualquer requisição que entre nesse guard afeta
todas as threads.

Gatilho introduzido na V7.2: `dashboard/platform_api.py`, `radar_readiness()`,
chama `radar.preflight()` (`scripts/multiasset_radar.py:436`, dentro de
`no_network()`) para responder `GET /api/platform/radar-readiness`. A página
`/radar` faz esse GET logo após `POST /api/radar/run` (`refresh()` → `inputs()`)
e a cada 2 s enquanto o job está RUNNING. O worker pago (thread de
`radar_api.post` → `radar.run`) usa `urllib` → `http.client` →
`socket.create_connection`, que naquele momento era o `MagicMock` do guard.

Dois mecanismos, ambos reproduzidos sem rede externa:

| Mecanismo | Teste | Resultado |
|---|---|---|
| Interferência: enquanto um GET está no guard, outra thread não conecta | `test_sealed_guard_blocks_other_threads` | `RuntimeError` na thread worker; servidor local recebe 0 requisições |
| Vazamento: dois guards sobrepostos em threads diferentes; cada `patch.object` restaura o que viu ao entrar e o guard **fica instalado** | `test_sealed_guard_leaks_when_checks_interleave` | após ambos saírem, `create_connection` continua bloqueado no processo |
| Incidente com o código real (readiness GET + `radar.run` + transporte HTTP real em loopback) | `test_incident_reproduced_with_real_radar_code` | mesma assinatura do journal de 02:59: 5 chamadas, `RuntimeError`, `http_status null`, `raw` nulo, `FAILED_REPLAY_ONLY` |

Não há log de requisições do servidor para dizer qual dos dois ocorreu às 02:59;
a uniformidade das 25 falhas em 1,5 s é compatível com ambos. A falha não é do
Gemini: a mensagem só existe nas linhas 118 e 128 desse guard.

**Por que os cinco ativos:** o guard é global ao processo e o lote é sequencial
em uma única thread; com `create_connection` bloqueado durante (ou desde antes
de) todo o lote, cada uma das 5 chamadas de cada ticker falhou na primeira
conexão. Os 25 registros são todos `technical_analyst`: sem votos, o Risk
nunca foi chamado.

## 2. Correção

`scripts/network_scope.py` (fora do código selado): `install()` coloca **um**
dispatcher permanente nos três atributos. Ele recusa exatamente o que o guard
selado recusa, com a mesma mensagem, mas só quando o **contexto atual** está
dentro de `network_scope.no_network()` (`ContextVar`). Em seguida religa todo
nome `no_network` carregado (inclusive o do módulo selado) para essa versão.
`server.main()` chama `install()`; importar o servidor não muda nada, então os
testes offline continuam com o guard original.

- GETs continuam offline no próprio contexto (inclusive em `asyncio.to_thread`).
- O worker pago, que é outra thread, não é afetado; não há patch/restore por
  chamada, logo não existe vazamento.
- Nada desabilita a proteção globalmente; `src/` e o Radar selado não mudaram.
- `radar-view` informa `network_isolation`; a UI desabilita a execução paga se o
  servidor estiver sem isolamento (processo antigo).

Limite (`ponytail:`): uma referência ao guard selado capturada fora de um nome
de módulo continuaria global; não existe hoje e o teste confirma que nenhum
módulo carregado ficou com o guard selado.

## 3. Testes

`test_radar_network_isolation.py` (9): causa (interferência, vazamento,
incidente real), correção (worker conclui 6 chamadas no mesmo cenário com o GET
ainda offline), equivalência de bloqueio, `server.main()` instala e religa,
replay sem requisições e sem alterar claim/journal, novo lote no mesmo claim
recusado, estados de job/comitê, parcial e incerto. Mutações (sem religar; sem
dispatcher) derrubam a suíte. Cada teste restaura o socket do processo.

Regressão relevante: **259 passed, 2 failed**. As duas falhas são os testes de
preservação selados V5/V6 (`test_31_original_ledgers_preserved`,
`test_original_scientific_radar_and_ledger_preservation`), que comparam hash
exato de `data/radar/hfl_multiasset_v1/job.json` e `last_prepare.json`. Esses
arquivos mudaram com as ações do operador em 12/10 (preparo do ITUB4 às 02:41 e
o lote das 02:59), não com esta correção. A política V7.2 os classifica como
OPERATIONAL, sem violação ([preservation.json](preservation.json)). Baselines e
testes não foram editados para passar. Ruff e sintaxe JS limpos.

## 4. Forense das 25 chamadas

| Fato | Evidência |
|---|---|
| Reserva antes do transporte | CallBank `reservations` L01 = 5 por ticker (5 analistas; Risk não chamado) |
| Falha local antes de qualquer socket | `attempts`: `TRANSPORT_ERROR`, `RuntimeError`, mensagem do guard, `http_status null`; `http.client` chama `socket.create_connection`, substituído pelo guard que lança antes de DNS ou TCP |
| Nada recebido | `raw` nulo nas 25; sem `token_usage`; 32–93 ms por chamada (incompatível com TLS + geração) |
| Reprodução | o servidor local recebeu 0 requisições com a mesma assinatura |
| Um único attempt por chamada | sem retry (`max_http_attempts_per_call = 1`) |

Conclusão técnica: **nenhuma requisição saiu do processo**. Isso se apoia no
ponto exato da exceção e na reprodução, não no `http_status null`. A
classificação exposta é `NO_SEND_EVIDENCE` ("bloqueio local antes da conexão;
cobrança a confirmar no provedor"): conferir o uso da chave no console do
Google AI Studio para 05:59 UTC é a confirmação do lado do provedor.

Destino do lote: **incidente imutável**. Claims, journals, `failure.json`,
eventos e a reserva permanecem. Replay não reconstrói (não há envelopes) e não
faz requisições. Um novo lote pago para esses claims é recusado
(`inference_already_reserved_replay_only`). A UI agora mostra "Infraestrutura
concluída · 0/5 comitês concluídos" e, por ticker, "Falha sem envelope
recuperável".

## 5. Reservas

A reserva `d3877668….json` registra US$ 3,31776 (teto conservador; estimativa
US$ 0,14625). É uma reserva do orçamento local, não um gasto observado, e não é
liberada automaticamente. Na raiz `hfl_multiasset_v1` restam US$ 1,68224 do teto
de US$ 5,00, insuficiente para um novo lote de cinco (US$ 3,31776).

## 6. Procedimento seguro para uma futura execução oficial (não executado)

1. Reiniciar o servidor com o código corrigido. Um processo antigo pode manter o
   guard vazado e bloquear tudo que ele mesmo baixa (preparo do Radar pela UI);
   os jobs H2 rodam em subprocesso e não são afetados. Em `/radar`, confirmar
   que não aparece o aviso de isolamento.
2. Preferir o CLI para o lote pago: processo próprio, sem GETs concorrentes.
3. Usar **identidade operacional separada**: outra raiz Radar (por exemplo
   `data/radar/hfl_multiasset_v1_r2`), com reservas e orçamento próprios; nada é
   copiado da raiz do incidente.

```powershell
$env:GEMINI_API_KEY = '<chave somente neste terminal>'
$R = 'data/radar/hfl_multiasset_v1_r2'; $S = '2026-10-13'
.venv/Scripts/python.exe -B scripts/radar_corporate_events.py prepare --root $R --session $S   # GRAVA, sem Gemini
.venv/Scripts/python.exe -B scripts/run_multiasset_radar.py preflight --root $R --session $S   # CONSULTA
.venv/Scripts/python.exe -B scripts/run_multiasset_radar.py run --root $R --session $S --confirm <token> --authorize-paid   # PAGA
```

4. O Gestor Global da UI lê só a raiz oficial; pareceres de outra raiz seguem
   pelo CLI `run_global_pm.py --radar-root $R`, com autorização própria.
