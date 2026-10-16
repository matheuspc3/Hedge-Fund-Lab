# Hedge-Fund-Lab

Laboratório Quantitativo de Backtesting baseado em Sistemas Multiagentes.
O produto evolui para acompanhar e comparar **carteiras simuladas diariamente**,
com decisões, operações, caixa, posições e patrimônio rastreáveis.

Comece pelo [INICIO](INICIO.md). O repositório é também o vault Obsidian;
os documentos permanecem em `docs`, sem cópias paralelas.

## Direção e estado

- [Direção e decisões aceitas](docs/DIRECAO_DO_PROJETO.md): carteira como tela
  inicial, seletor, evolução diária, D0 em 13/10 e referência inicial 20% por ativo.
- [Roadmap](docs/ROADMAP.md): sequência de implementação e critérios de saída.
- [Estado atual](docs/ESTADO_ATUAL.md): o que existe e suas limitações.
- [Documentação](docs/README.md): referências técnicas, evidências e histórico.
- [Arquitetura](docs/ARQUITETURA.md): componentes e fronteiras atuais.

**V7.6.5, fotografia documental de 13/10/2026:** ledger multiativos qualificado
offline em SQLite temporário e dados sintéticos. O dashboard lê exportação
verificada; a execução paper oficial multiativos está desabilitada.
H2/PETR4 e Radar/Global PM são linhas independentes. A V1 do PM foi rejeitada;
a V2 foi validada com 100% caixa e zero operações. Validação não prova retorno.

## Abrir o dashboard local

Com o ambiente já instalado, a partir da raiz, em PowerShell:

```powershell
# Consultar e registrar carteiras pessoais sem credencial Gemini no processo.
& .\.venv\Scripts\python.exe -B scripts/serve_dashboard_keyless.py 8116
```

Abrir [dashboard local](http://127.0.0.1:8116/). O servidor keyless serve para
consulta e registro manual pessoal; não torna os endpoints de escrita read-only.
Na home: **Criar carteira → selecionar → Registrar operação → Ver prévia →
Confirmar registro**. Para corrigir/anular, use **Corrigir**, informe o motivo e
confirme a prévia. Cadastro e operações ficam no SQLite pessoal e sobrevivem ao
reinício. Histórico anterior a D0 é permitido desde o início da carteira.
Sem cotações integradas, patrimônio com posições e retornos ficam indisponíveis;
preços/proventos/ciclo dos agentes seguem pendentes, conforme o roadmap.

| Área | Caminho | Natureza |
|---|---|---|
| Carteiras e operações | `/` | Cadastro persistente, simulação manual/real externa, posições, histórico e correções |
| Demonstração sintética | `/?demo=1` | Ensaio separado, somente consulta |
| Mercado/Radar | `/market`, `/radar` | Análise consultiva |
| Gestor e demonstrações | `/portfolio` | Snapshot PM, histórico e demonstração opt-in |
| Legacy | `/legacy` | Hub histórico somente consulta: etapa anterior e documentação do TCC |
| Piloto PETR4 histórico | `/legacy/paper` (alias `/paper`) | Carteiras H2, decisões e pendências preservadas; ações web bloqueadas |
| Pesquisa H2 histórica | `/legacy/h2` (alias `/h2`) | Avaliação, metodologia e evidências; Final Test bloqueado |
| Backtests históricos | `/legacy/backtests` (alias `/index.html`) | Export de backtests históricos |

Para operação, conferir contrato, estado e consentimentos da ação específica.
O [runbook V7.3/V7.4](docs/HFL_OPERATIONS_RUNBOOK.md) é referência versionada;
não repetir seus comandos datados como se fossem autorização atual.

## Ambiente e desenvolvimento

Python **3.11 a 3.13**, conforme [pyproject.toml](pyproject.toml).
Poetry gerencia dependências; o [justfile](justfile) reúne os comandos existentes.
PostgreSQL/Docker é usado pelo pipeline de mercado; sua disponibilidade não é
pré-requisito para simplesmente consultar os artefatos locais pelo dashboard.
Configurações vêm de `.env`; não incluir credenciais no Git ou no vault público.

```powershell
poetry install
& .\.venv\Scripts\python.exe -B scripts/check_docs.py
& .\.venv\Scripts\python.exe -B scripts/check_preservation.py
```

O primeiro comando instala dependências. Os dois seguintes são checks de leitura
de documentação e preservação. `just test` executa a suíte; `just lint` verifica
o código. `just run` executa pipeline, gera backtests e inicia o servidor; não é
um comando de simples consulta. Não executar campanhas/inferências por navegação.

## Código e verificação

`src` contém dados, indicadores, agentes, backtesting e arena experimental;
`scripts` contém runners/contratos e verificadores; `dashboard` contém APIs e
interface; `tests` contém os checks automatizados. Consulte a
[arquitetura](docs/ARQUITETURA.md) para os caminhos por subsistema.

A qualificação V7.6.5 registra 49 testes direcionados, Chrome 30/30 e regressão
1801 passed / 14 falhas preexistentes. São resultados daquela entrega;
a suíte completa permanece vermelha e não foi reexecutada nesta revisão documental.
[Relatório de regressão](docs/evidence/hfl_paper_ledger_v765/REGRESSION_REPORT.md).

O [README técnico anterior](docs/archive/README_TECNICO_ATE_V765.md) preserva
exemplos de código, configuração e screenshots antigos. Eles não descrevem
automaticamente o comportamento dos tratamentos atuais.
