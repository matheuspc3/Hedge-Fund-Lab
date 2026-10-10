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
