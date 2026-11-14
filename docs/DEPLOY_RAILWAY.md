# Servidor pessoal no Railway (DP-34)

O dashboard roda 24/7 no Railway e só é acessível pela tailnet de Lucas:
`https://hedge-fund-lab.<sua-tailnet>.ts.net/`. Nada escuta publicamente: o Python
continua em `127.0.0.1:8081` dentro do contêiner e o `tailscale serve` faz o HTTPS
da tailnet. Arquivos: `Dockerfile`, `.dockerignore`, `railway.json`,
`scripts/railway_entrypoint.sh`.

**[conta]** = passo que exige a conta de Lucas (Railway, Tailscale, Resend, Google).

O entrypoint exporta `HFL_PUBLIC_HOST` com o nome MagicDNS do nó; o servidor já
aceita exatamente esse host com `Origin: https://<HFL_PUBLIC_HOST>`. Use o endereço
anunciado nos logs: um nó anterior pode fazer o Tailscale acrescentar `-1` ao nome.

O build executa `scripts/restore_frozen_bytes.py`: restaura finais de linha apenas
quando o SHA-256 reproduz o selo original. As capturas HTML com finais mistos são
preservadas por `.gitattributes`; conteúdo diferente faz o build falhar. Não
recalcule hashes para contornar `original_source_changed` ou
`observed_evidence_bytes_mismatch`.

## Como o contêiner sobe

**Identidade conferida no servidor e no Railway em 23/10:** o TCC fica no
projeto **Centauro ERP**, no ambiente **`tcc`**, serviço **`impartial-comfort`**.
O nome do projeto não indica que seja o serviço de produção do ERP. Para esta
aplicação, sempre escopar ações ao ambiente/serviço abaixo:

- Projeto: `ad6797e4-d9a0-45a2-b7b8-04950c277b5b`.
- Ambiente `tcc`: `f467c798-f6c7-48eb-be9c-5a4477e2e9cc`.
- Serviço: `7987997f-61ea-4e23-ae05-3cda9dd50d97`.
- Volume `hfl-data`: `8f660448-45ed-4a61-b145-118915e7b924`, `/app/data`, 20 GB.

No SSH, usar **`/opt/venv/bin/python`**; o `python` do shell aponta para o
interpretador do sistema, sem as dependências da aplicação. O shell SSH não
herda automaticamente todas as variáveis do processo principal.

Recuperação de acesso de 23/10: checagem SSH terminou com `Authorization
successful` ao reiniciar o fluxo em `login.tailscale.com` e usar o Google da
conta da tailnet. O login GitHub anterior havia terminado em `bad
tailscale-authstate2 cookie`. A conexão Railway existente que lista Centauro
ERP acessa o ambiente `tcc`; não é necessário insistir na conexão adicional
que falha com `could not validate id_token_hint`.

**Origem usada no `tcc` (23/10):** fork `LuquinhasPS/Hedge-Fund-Lab` do
repositório `matheuspc3/Hedge-Fund-Lab`. Lucas usa o fork porque conseguiu
selecioná-lo no Railway. O serviço segue a branch
`fix/railway-daily-cycle-20261021`, fixado por `source.commitSha` no código
`2baa6c38b4483fa3a5518018a3c85704fd9317d0`. Sincronizar a `main` do fork com
o original não troca esse pin, não incorpora a branch do PR #2 à `main` e não
publica automaticamente uma versão nova. Atualizar a versão fixada é uma ação
separada de deploy; preservar o volume `/app/data`.

DP-36 publicada após autorização explícita de Lucas: deploy
`38c9ee72-2541-4ade-b28a-613f0b8dee46` em SUCCESS, servidor iniciado às 20:28
de 23/10 (Brasília). A versão anterior DP-35 era `4fefe40`, deploy
`5b2b7739-d8db-44ce-a990-514db37b54ae`, preservada no histórico do Railway.
SMA/Bollinger foram inicializadas uma vez pelo SSH com `/opt/venv/bin/python`
e custo de 0,03%; a atualização de mercado agora avança as duas sem IA.
Backup anterior: `/app/data/backups/before-rule-wallets-20261023T232120Z`.

DP-35/APP-05: o servidor inicia também o processador de ordens intradiárias,
com verificação a cada 60 s, independente de `HFL_DAILY_CYCLE`. Novas aprovações
entre os cortes usam a primeira barra Yahoo de 1 min posterior à aprovação
(atraso ~15 min); ordens OPEN/CLOSE gravadas mantêm sua regra. O recibo conserva
a fonte em `execution-prices.json` no mesmo volume. Não exige variável ou chave
nova; falhas desse processador são registradas com prefixo `DP-35` nos logs.

1. `tini` (PID 1) executa `scripts/railway_entrypoint.sh` e repassa o SIGTERM do
   Railway ao Python e ao `tailscaled` (parada limpa em menos de 1 s no teste local).
2. Sem `TS_AUTHKEY` e sem identidade salva no volume, sai com código 64 (falha
   rápida, porque o serviço ficaria inacessível). `HFL_TAILSCALE=0` pula o Tailscale
   (somente teste local).
3. `tailscaled --tun=userspace-networking` (o Railway não oferece TUN), estado em
   `/app/data/.tailscale` (no volume: o nó mantém a mesma identidade após reinícios).
4. `tailscale up --hostname=hedge-fund-lab --ssh --accept-dns=false`. A chave só é
   usada no primeiro login; depois pode expirar sem efeito.
5. `tailscale serve --bg --https=443 http://127.0.0.1:8081`.
6. `exec python dashboard/server.py 8081`.

## 1. Tailscale [conta]

1. Admin console → **DNS**: ative **MagicDNS** e **HTTPS Certificates** (sem isso o
   `serve` falha e só o SSH funciona).
2. **Access controls** (policy file): acrescente a tag e a regra de SSH. A política
   padrão (`grants` liberando tudo) já permite o acesso HTTPS; se você restringiu,
   libere `tag:hfl:443` para seus dispositivos.

   ```jsonc
   "tagOwners": { "tag:hfl": ["autogroup:admin"] },
   "ssh": [
     { "action": "accept", "src": ["autogroup:member"], "dst": ["tag:hfl"], "users": ["root"] }
   ]
   ```

3. **Settings → Keys → Generate auth key**: *Reusable* desligado, *Ephemeral*
   desligado, *Pre-approved* ligado, *Tags* = `tag:hfl`. Nós com tag não expiram.
   Copie a chave (`tskey-auth-…`) direto para o Railway; não salve em arquivo.

## 2. Resend (aviso por e-mail) [conta]

Resend → **API Keys → Create** com permissão *Sending access*. Sem domínio
verificado, o Resend só entrega para o e-mail dono da conta, o que basta aqui. O
contêiner precisa de saída para `api.resend.com` (o Railway libera saída por
padrão); não há dependência extra (HTTP da biblioteca padrão).

## 3. Projeto no Railway [conta]

1. **New Project → Deploy from GitHub repo** → este repositório, branch `main`. O
   `railway.json` escolhe o builder Dockerfile, 1 réplica, sem *sleep*, reinício
   em falha (até 10 tentativas). Não há healthcheck: nada escuta em porta pública.
2. Serviço → **Settings → Networking**: se existir domínio `*.up.railway.app`,
   **apague**; nunca use *Generate Domain* nem *TCP Proxy*. (Mesmo se criado, nada
   responde: o app escuta só em 127.0.0.1.)
3. Serviço → **Volume** (botão direito no canvas → *Volume*): **mount path
   `/app/data`**. Tamanho: veja a seção 6. Um volume por serviço; dá para aumentar
   depois sem parada, mas não diminuir.
4. **Variables** (todas como variáveis do serviço; nenhuma vai para o repositório):

   | Variável | Valor | Primeiro boot |
   |---|---|---|
   | `TS_AUTHKEY` | chave do passo 1.3 | obrigatória |
   | `GEMINI_API_KEY` | chave do Google AI Studio [conta] | pode ficar para depois |
   | `HFL_RESEND_API_KEY` | chave do passo 2 | |
   | `HFL_NOTIFY_TO` | e-mail da sua conta Resend | |
   | `HFL_NOTIFY_FROM` | opcional; padrão `Hedge Fund Lab <onboarding@resend.dev>` | |
   | `HFL_DAILY_CYCLE` | `0` no primeiro boot, `1` depois da migração | `0` |
   | `HFL_MARKET_BASE_AUTOUPDATE` | `0` no primeiro boot; remova (ou `1`) depois | `0` |
   | `TS_DEBUG_MTU` | `1280`; sozinho não impediu a recorrência do timeout Chrome | `1280` |
   | `TS_DEBUG_ALWAYS_USE_DERP` | `true`; neste ambiente, usar relay criptografado para contornar o timeout do caminho UDP direto | `true` |

   `TZ` não é necessário: as regras usam `ZoneInfo("America/Sao_Paulo")` (pacote
   `tzdata` do lock). Os horários do log saem em UTC. `HFL_PORT` (padrão 8081) e
   `TS_HOSTNAME` (padrão `hedge-fund-lab`) só se quiser mudar.
5. **Deploy**. Nos logs deve aparecer `railway_entrypoint: tailnet
   https://hedge-fund-lab.<tailnet>.ts.net/` e `Servidor iniciado`. O nó aparece em
   *Machines* no admin do Tailscale com a tag `tag:hfl`.

## 4. Migrar data/ do PC (Git Bash)

O PC precisa estar na tailnet (app Tailscale ligado). Use **Git Bash**: o pipe do
Windows PowerShell 5 corrompe binários.

1. Pare o servidor local (Ctrl+C) e não rode nada que grave em `data/` até o fim.
   No Railway, o ciclo e a base de mercado ficam parados (`0`) até o passo 4.
2. Teste o SSH: `ssh root@hedge-fund-lab "df -h /app/data"`.
3. Copie (sem compressão: os ZIP da B3 já são comprimidos):

   ```bash
   cd "/c/Users/LUCAS/Meu Canto/TCC/Hedge-Fund-Lab"
   tar -C data -cf - --exclude=./cache --exclude=./tmp --exclude=./logs \
       --exclude='./radar/tmp*' . \
     | ssh root@hedge-fund-lab "tar -C /app/data -xf - --no-same-owner && du -sh /app/data"
   ```

   Confira a contagem de arquivos e o registro do Radar nos dois lados:

   ```bash
   find data -type f -not -path 'data/cache/*' -not -path 'data/tmp/*' \
     -not -path 'data/logs/*' -not -path 'data/radar/tmp*' | wc -l
   sha256sum data/radar/registry.json
   ssh root@hedge-fund-lab "find /app/data -type f -not -path '*/.tailscale/*' | wc -l; sha256sum /app/data/radar/registry.json"
   ```

4. No Railway, mude `HFL_DAILY_CYCLE=1` e remova `HFL_MARKET_BASE_AUTOUPDATE` (ou
   `1`). A mudança de variável reinicia o serviço e o servidor lê o registro migrado.
5. A partir daqui o Railway é a cópia de trabalho. **Não** rode o servidor nem a
   rotina no PC contra o mesmo `data/` (dois escritores divergem o ledger); o
   `data/` do PC fica como cópia anterior à migração.

## 5. Verificar

- Do PC e do celular (app Tailscale ligado): abra
  `https://hedge-fund-lab.<tailnet>.ts.net/` → a Carteira carrega.
- Fora da tailnet (Wi-Fi do celular sem Tailscale): o endereço não resolve.
- Logs do Railway: nenhum `local_origin_required` nas suas navegações.

## 6. Tamanho do volume e o que migrar

Medição de `data/` em 20/10/2026 (2,5 GB no total):

| Pasta | Tamanho | Papel | Migrar? |
|---|---|---|---|
| `radar/` | 1,0 GB | execuções do Radar, registro, análises por carteira (~90 MB cada: cópia própria do COTAHIST) | sim |
| `raw/cotahist/` | 525 MB | ZIP anuais da B3 usados pela preparação do Radar | sim (baixáveis de novo, mas são a fonte selada) |
| `runs/` | 486 MB | experimentos H2/CAL (Legacy; `h2_v6_provisional` 137 MB é lido pelo `/h2`) | sim |
| `platform/` | 348 MB | `manual-v1` (carteiras e operações, 48 KB), `market-base-v1` (5 MB), `stock-history-v1` (60 MB, reconstruível pelo Yahoo); ~280 MB de pastas de regressão/QA | sim |
| `forward/` | 106 MB | paper H2 v6 (Legacy) | sim |
| `global_pm/`, `portfolio/`, `snapshots/`, `agent_runs/` | 52 MB | registros selados antigos | sim |
| `cache/`, `tmp/`, `logs/`, `radar/tmp*` | 20 MB | cache de verificações e logs | não (recriados) |

Migrar ~2,45 GB. **Crescimento:** cada análise diária copia ~90 MB do COTAHIST, então
o ciclo automático soma ~2 GB/mês. O plano Hobby tem teto de **5 GB** por volume
(cheio em ~1 mês); o Pro permite até 1 TB. Escolha: Pro com volume de 20 GB, ou
Hobby somente depois de o código deixar de copiar o COTAHIST por análise. Para
economizar espaço agora, as pastas de regressão/QA de `platform/` e os
experimentos de `runs/` (exceto `h2_v6_provisional`) podem ficar só no PC; o
Legacy correspondente deixará de abrir no servidor.

## 7. Backup (do PC, pela tailnet)

Fora dos horários do ciclo (09:00, 12:00, 16:00 de Brasília), no Git Bash:

```bash
ssh root@hedge-fund-lab "tar -C /app/data -cf - --exclude=./.tailscale ." \
  > "/c/Users/LUCAS/Backups/hfl-data-$(date +%Y%m%d).tar"
```

Exclua `.tailscale` (é a chave do nó). Semanal basta; guarde as últimas cópias.
O Railway também oferece backups do volume (cobrados como armazenamento).

## 8. Custos e limites

- Preços do Railway (out/2026): RAM US$ 10/GB-mês, vCPU US$ 20/vCPU-mês, volume
  US$ 0,15/GB-mês, saída US$ 0,05/GB. Hobby US$ 5/mês com US$ 5 de uso incluído;
  Pro US$ 20/mês com US$ 20 incluídos.
- Estimativa: 137 MB de RAM ocioso no teste local; ~0,5 GB durante análises ≈ até US$ 5; CPU quase
  ociosa ≈ US$ 1; 20 GB de volume ≈ US$ 3. O Gemini (teto de reserva US$ 4/dia da
  DP-34) é cobrado à parte pelo Google.
- Redeploy com volume tem alguns segundos de parada; se coincidir com 09:00/12:00, a
  tentativa seguinte (12:00/16:00) cobre.
- O Railway não tem região no Brasil; B3 e Yahoo podem limitar IPs de datacenter.
  Se os downloads falharem nos logs, as três tentativas registram o dia sem análise.
