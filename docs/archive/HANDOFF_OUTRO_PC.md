# Hedge-fund-lab — Handoff para continuar em outro computador

> **HISTÓRICO — NÃO USAR COMO ESTADO ATUAL.** Este handoff registra uma etapa
> intermediária e pode conter instruções e afirmações desatualizadas. Consulte
> [`../ESTADO_ATUAL.md`](../ESTADO_ATUAL.md) e
> [`../ROADMAP.md`](../ROADMAP.md).

Este documento contém o contexto necessário para outro Codex continuar o projeto.

> **Importante:** o trabalho descrito abaixo está local e pode ainda não ter sido
> commitado/pushado. Antes de trocar de computador, envie as alterações para uma
> branch remota ou copie a pasta inteira do projeto.

## 1. Como transportar o trabalho

No computador atual, entre na pasta:

```text
C:\Users\81000286\Meu Canto\TCC\Hedge-Fund-Lab
```

Recomendação via Git:

```powershell
git switch -c feature/multiagent-quorum
git add .
git commit -m "Implement multi-agent quorum and agent backtesting"
git push -u origin feature/multiagent-quorum
```

No outro computador:

```bash
git clone <URL-DO-REPOSITORIO>
cd Hedge-Fund-Lab
git switch feature/multiagent-quorum
```

Se não quiser usar Git, compacte a pasta inteira, excluindo `.venv`, e copie-a
para o outro computador.

## 2. Prompt para colar no Codex do outro computador

Copie e envie o texto abaixo ao Codex:

```text
Analise este repositório e continue a implementação do Hedge-fund-lab.

Leia primeiro AGENTS.md, README.md, PLAN_HEDGEFUND.md, main.tex e o código em
src/agents e src/backtesting/agent_engine.py.

Contexto do trabalho já realizado:

- O projeto é um laboratório quantitativo de backtesting para TCC.
- Já existiam ETL, indicadores, cinco estratégias clássicas, motores de
  backtesting e dashboard.
- Foi implementada a Fase 4 do sistema multiagente com LangGraph.
- O fluxo é: quorum de analistas técnicos -> gestor de risco -> gestor de
  portfólio.
- O quorum possui 30 analistas técnicos executados concorrentemente.
- Cada voto possui analyst_id, sinal, confiança, temperatura e seed.
- O requisito atual é uma supermaioria de 25/30.
- Todos os 30 votos precisam ser válidos por padrão.
- Sem 25 votos no mesmo sinal, o resultado coletivo é MANTER.
- Os analistas devem usar o mesmo modelo, com variação controlada de temperatura
  e seed.
- O usuário pretende usar uma chave do OmniRouter/Agent Router.
- Provavelmente serão testados modelos GPT e Claude, uma família/modelo por leva.
- O orçamento será definido depois dos primeiros testes.
- Calibração de risco e Kelly ainda não foi decidida.
- Não invente valores calibrados.

Implementações existentes:

- src/agents/state.py:
  modelos Pydantic para TechnicalSignal, TechnicalVote, TechnicalConsensus,
  RiskVerdict, FinalDecision e AgentState.
- src/agents/llm_client.py:
  LLMClient abstrato, MockLLMClient, RetryingLLMClient e CachedLLMClient.
- src/agents/technical_analyst.py:
  analista individual e ensemble paralelo.
- src/agents/risk_manager.py:
  regras duras de volatilidade, drawdown e concentração.
- src/agents/portfolio_manager.py:
  fractional Kelly e limites de posição.
- src/agents/graph.py:
  grafo LangGraph.
- src/backtesting/agent_engine.py:
  decisão no fechamento de t e execução na abertura de t+1, com custos, caixa,
  posições e auditoria.
- scripts/run_agent_backtest.py:
  runner demonstrativo com mock.
- scripts/repair_sqlite_database.py:
  reparador de duplicatas que cria backup antes de alterar o banco.
- O pipeline foi alterado para usar upsert de cotações e indicadores.
- Foram adicionadas constraints únicas (ativo_id, data).
- O resultado do backtest pode exportar auditoria JSON completa.
- Prefect foi atualizado para 3.x para suportar Python 3.13.
- LangGraph 1.x, SciPy e Ruff foram adicionados ao pyproject.toml.

Estado de validação anterior:

- Antes da última alteração de 25/30, 296 testes passavam.
- A cobertura global era 97%.
- Ensemble e AgentBacktestEngine estavam com 100%.
- O lint dos arquivos alterados passava.

IMPORTANTE: a última alteração foi interrompida depois de:

- mudar consensus_threshold padrão para 5/6;
- adicionar temperature_min=0.2;
- adicionar temperature_max=0.8;
- adicionar seed_base=10000;
- adicionar options à interface LLMClient;
- fazer cache e retry encaminharem options;
- registrar temperature e seed em TechnicalVote;
- adicionar configurações LLM em src/config.py e .env.example;
- atualizar testes de 20/30 para 25/30.

Essa última alteração ainda NÃO foi testada.

Primeiras tarefas obrigatórias:

1. Inspecionar git status e git diff.
2. Corrigir README.md, que ainda pode mencionar 20/30 e 2/3.
3. Rodar os testes direcionados.
4. Rodar a suíte completa com cobertura mínima de 95%.
5. Rodar Ruff apenas nos arquivos tocados.
6. Corrigir qualquer incompatibilidade causada pelo novo parâmetro options.
7. Não executar o reparador no hedgefundlab.db sem confirmar o backup.
8. Não usar o resultado mock como resultado científico.

Depois:

- localizar a documentação oficial do OmniRouter/Agent Router;
- confirmar endpoint, autenticação, nomes dos modelos e suporte a JSON Schema;
- implementar um cliente real isolado, provavelmente OpenAI-compatible somente
  se a documentação confirmar;
- nunca hardcodar a chave;
- ler LLM_API_KEY, LLM_BASE_URL e LLM_MODEL do ambiente;
- registrar modelo, custo/tokens e latência na auditoria;
- criar um modo dry-run para estimar chamadas antes de gastar créditos;
- manter cache e retry envolvendo o cliente real;
- testar o cliente sem chamadas pagas usando transporte HTTP mockado.

Siga AGENTS.md: código mínimo, sem dependências desnecessárias, regras financeiras
determinísticas fora do LLM e testes para toda lógica não trivial.
```

## 3. Preparação do ambiente no novo computador

Python 3.13 funcionou com Prefect 3.8.1. Python 3.11 ou 3.12 também deve ser
adequado.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Verificação inicial

```bash
python -m pytest tests/agents tests/backtesting/test_agent_engine.py -q
python -m pytest --cov=src --cov-report=term --cov-fail-under=95 -q
python -m ruff check src/agents src/backtesting/agent_engine.py tests/agents tests/backtesting/test_agent_engine.py
```

## 4. Estado exato da última alteração

A configuração desejada agora é:

```python
AnalystEnsembleConfig(
    analyst_count=30,
    consensus_threshold=5 / 6,  # 25 de 30
    require_all_votes=True,
    temperature_min=0.2,
    temperature_max=0.8,
    seed_base=10_000,
)
```

A variação foi desenhada assim:

- Analista 1: temperatura 0.2, seed 10001.
- Analistas intermediários: temperaturas distribuídas linearmente.
- Analista 30: temperatura 0.8, seed 10030.
- Mesmo prompt base e mesmo modelo dentro de uma leva.
- `analyst_id`, temperatura e seed entram na auditoria.
- As opções também entram na chave do cache.

O teste com apenas três analistas usa `2/3` intencionalmente para manter o teste
pequeno. Isso não é o default experimental.

## 5. Configuração prevista para o OmniRouter

O `.env.example` recebeu placeholders:

```dotenv
LLM_PROVIDER=omnirouter
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

O cliente real ainda não foi implementado porque o acesso à documentação do
OmniRouter falhou. Não se deve adivinhar o endpoint.

No outro computador:

1. Localize a documentação oficial.
2. Preencha `LLM_BASE_URL` e `LLM_MODEL`.
3. Crie `.env`, que já é ignorado pelo Git.
4. Nunca coloque a chave no README, código, teste ou commit.

Exemplo:

```dotenv
LLM_PROVIDER=omnirouter
LLM_BASE_URL=<ENDPOINT-OFICIAL>
LLM_API_KEY=<SUA-CHAVE>
LLM_MODEL=<NOME-EXATO-DO-MODELO>
```

## 6. Banco de dados

O SQLite versionado possui duplicatas antigas. Foram observadas:

- WEGE3: 22.419 registros, mas 2.491 datas únicas.
- 19.928 duplicatas de WEGE3.
- Diversos ativos com duas cópias por data.
- PETR4 com apenas 251 datas únicas de 2024 e múltiplas cópias.

O código novo impede duplicatas em bancos novos, mas `create_all()` não adiciona
constraints a tabelas já existentes.

Reparo disponível:

```bash
python scripts/repair_sqlite_database.py hedgefundlab.db
```

Esse comando:

- cria `hedgefundlab.db.bak`;
- mantém o registro mais recente por ativo/data;
- remove duplicatas;
- cria índices únicos.

Ele ainda não foi executado no banco principal.

## 7. Runner demonstrativo

Depois dos testes:

```bash
python scripts/run_agent_backtest.py \
  --ticker WEGE3.SA \
  --days 60 \
  --analysts 30 \
  --threshold 0.8333333333333334 \
  --decision-frequency 5
```

No Windows:

```powershell
python scripts\run_agent_backtest.py --ticker WEGE3.SA --days 60 --analysts 30 --threshold 0.8333333333333334 --decision-frequency 5
```

Saída:

```text
data/agent_runs/WEGE3.SA_mock.json
```

Uma execução anterior com mock produziu:

- R$ 100.000 -> R$ 107.721,56.
- 4 trades.
- 12 rodadas de decisão.
- 30 votos por rodada.

Isso é apenas demonstração técnica, não resultado científico.

## 8. Próximas implementações recomendadas

Ordem mais segura:

1. Finalizar e validar 25/30.
2. Atualizar README.
3. Implementar `OmniRouterLLMClient`.
4. Mockar completamente o transporte HTTP.
5. Adicionar medição de:
   - prompt tokens;
   - completion tokens;
   - custo estimado;
   - latência;
   - modelo efetivamente usado;
   - erros e retries.
6. Implementar `--dry-run` com:
   - número de pregões;
   - frequência das decisões;
   - chamadas por rodada;
   - chamadas totais;
   - estimativa de tokens;
   - nenhuma chamada externa.
7. Executar uma leva pequena:
   - um ticker;
   - 20 a 60 pregões;
   - poucas datas de decisão;
   - cache ativado.
8. Avaliar divergência dos 30 votos.
9. Só depois definir orçamento, risco e Kelly.
10. Congelar parâmetros antes do teste out-of-sample.

## 9. Ponto crítico

Sem commit/push, o outro computador verá apenas a versão antiga do repositório.
Transporte primeiro as mudanças locais e, no novo computador, comece por
`git status`, `git diff` e pela suíte de testes.
