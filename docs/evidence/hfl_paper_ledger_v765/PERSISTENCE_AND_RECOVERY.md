# Persistência, concorrência e recuperação

SQLite stdlib; schema independente (`PRAGMA user_version=1`), tabelas `events` e `checkpoints`. Não modifica banco existente nem precisa de serviço. `BEGIN IMMEDIATE` serializa escritores; timeout 10 s, synchronous FULL, rollback journal SQLite. Evento e checkpoint são confirmados juntos. Primary key (carteira, sequência), unicidade (carteira, chave) e event_id global. Triggers recusam UPDATE/DELETE de eventos. Checkpoint atualizado somente depois de validar o estado anterior por replay.

Escritores só abrem `ledger.sqlite3` em subdiretório `hfl-paper-*` do TEMP do sistema, resolvido e externo ao repositório. Raízes H2/data/experimentos são recusadas. A criação usa `xb`: arquivo preexistente, mesmo vazio após interrupção durante criação, exige inspeção explícita; nunca é truncado automaticamente. Nenhum escritor é chamado pela API. Toda qualificação usa TemporaryDirectory e encerra conexões antes de remover o diretório.

Leitores SQLite usam URI mode=ro e transação de leitura para snapshot consistente. Verificam schema, integrity_check, índices versus corpo, hash, cadeia, sequência, identidades, relógios, fingerprints do motor/calendário e equivalência exata do checkpoint com replay. A exportação tem selo adicional; o GET verifica esse selo e repete replay em memória. Não produz checkpoints, claims, journals, arquivos de lock nem correções.

| Interrupção | Recuperação |
|---|---|
| antes do commit, inclusive entre evento e checkpoint | rollback; evento não existe após reinício |
| morte real do processo com transação aberta | rollback journal SQLite recupera o estado anterior |
| depois do commit, confirmação perdida | consultar/repetir **mesmo** comando e chave; devolve original sem novo efeito |
| corrupção, hash inválido ou checkpoint divergente | RECONCILIATION_FAILED; rejeita novas escritas dependentes; não tenta reparar |
| lock ocupado por outro escritor | espera limitada; erro não é presumido como sucesso |
| banco vazio/incerto na criação | não sobrescrever; inspeção explícita |

Qualificação cobre rollback em dois pontos, confirmação perdida, morte de subprocesso (`os._exit`), seis threads concorrentes, reinício em processo independente, triggers, arquivo ilegível, checkpoint adulterado, eventos re-selados inválidos e cauda removida. Reinício do servidor HTTP lê a mesma exportação/curva sem efeitos.

`ponytail`: replay completo O(n) por comando/leitura, contextos de proposta e preços embutidos para reprodução. Custo cresce com o histórico; checkpoint verificado + segmentos imutáveis é a evolução. SQLite local não é coordenação multi-host. Hashes detectam corrupção e alterações sem selo correspondente; não são assinatura digital contra administrador capaz de reescrever **toda** a cadeia/checkpoint. Ativação oficial exige cabeça externamente ancorada, controle de acesso e backup/restauração testados. Não se declara tolerância a perda física do disco.

A exportação inicial foi arquivada como `synthetic_ledger_initial.json` quando o envelope ganhou referências consultivas explícitas; o dashboard usa exclusivamente `synthetic_ledger.json`, gerado depois da definição final. Nenhum registro anterior à V7.6.5 foi reescrito.
