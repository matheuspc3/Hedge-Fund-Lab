# Material de apoio para a escrita do TCC 2

Cópias dos arquivos do repositório que servem de fonte para a monografia,
reunidas em 16/11/2026 a partir do commit `e5b835e`. São 71 arquivos, idênticos
byte a byte aos originais na data da cópia.

**Os originais continuam nos lugares de origem e são a fonte válida.** Nada foi
movido. As cópias são um retrato: se um original mudar, a cópia fica para trás.
Para saber quais originais mudaram desde a cópia, rode na raiz do repositório:

```bash
sha256sum -c tcc2/evidence/ORIGENS.sha256 --quiet
```

Cada linha `FAILED` é um original alterado depois da cópia. Os hashes valem para a cópia de
trabalho em que o manifesto foi gerado; em outra máquina, diferenças de fim de
linha podem acusar `FAILED` sem que o conteúdo tenha mudado. Os documentos de
`01-direcao-e-estado/` mudam a cada sessão de trabalho, então é esperado que
apareçam. Links internos dos arquivos copiados apontam para os caminhos
originais e não funcionam a partir daqui.

## O que há em cada pasta

### `01-direcao-e-estado/` — escopo, decisões e histórico

| Arquivo | Original | Uso |
|---|---|---|
| `DIRECAO_DO_PROJETO.md` | `docs/` | Decisões DP-01 a DP-37; base para escopo, justificativas e limitações |
| `ROADMAP.md` | `docs/` | Ordem das entregas e resultados resumidos de cada campanha |
| `ESTADO_ATUAL.md` | `docs/` | Registro datado do que foi entregue e verificado |

### `02-arquitetura/` — capítulo 4

| Arquivo | Original | Uso |
|---|---|---|
| `ARQUITETURA.md` | `docs/` | Onde cada responsabilidade está implementada |
| `HFL_PLATFORM_ARCHITECTURE.md` | `docs/` | Arquitetura da plataforma local |
| `HFL_MULTIASSET_PORTFOLIO_DESIGN.md` | `docs/` | Desenho da carteira multiativos |
| `HFL_PREMIUM_V4_RADAR.md` | `docs/` | Comitê de analistas e risco por ativo (Radar) |
| `HFL_PREMIUM_V6_GLOBAL_PM.md` | `docs/` | Gestor final da carteira |
| `CICLO_USO_PLATAFORMA.md` | `docs/` | Fluxo de uso de ponta a ponta |
| `DEPLOY_RAILWAY.md` | `docs/` | Servidor e ciclo diário autônomo |
| `PILOTO_MULTIATIVOS_SPEC.md` | `docs/` | Contrato do piloto; origem da proposta R7 de risco assimétrico |

### `03-metodo-h2/` — capítulo 5 como está hoje (hipóteses H1 e H2)

| Arquivo | Original | Uso |
|---|---|---|
| `EXPERIMENT_PROTOCOL.md` | `docs/` | Protocolo experimental citado pela monografia |
| `H2_METHODOLOGICAL_FREEZE_V1.md` | `docs/` | Congelamento metodológico: configuração, gates, âncoras |
| `H2_V5_AMENDMENT_13.md`, `H2_V6_AMENDMENT_14.md` | `docs/` | Versões 5 e 6 do tratamento |
| `H2_V6_ACADEMIC_APPROVAL_SUMMARY.md` | `docs/` | Resumo para aprovação acadêmica da avaliação |
| `H2_V6_OA1_VALIDATION_SCIENTIFIC_SUMMARY.md` | `docs/` | Síntese científica da validação provisória |
| `calendar/` (2 arquivos) | `docs/evidence/calendar/` | Calendário B3 com as fontes, citado na matriz de evidências |

### `04-replay-abril-novembro/` — capítulos 5 e 6 (foco empírico atual, DP-37)

| Arquivo | Original | Uso |
|---|---|---|
| `relatorios/evolucao_replay_v1_v2_v3_tcc.md` | `reports/` | **Começar por aqui.** Documento mestre: método, v1, v2, v3, tabelas e limitações |
| `relatorios/replay_continuo_2026-04_2026-11.md` | `reports/` | Resultado original da v1 e das cinco referências |
| `relatorios/auditoria_posicoes_replay_2026-04_2026-11.md` | `reports/` | Os 5 achados da v1 e o plano da v2 |
| `relatorios/replay_continuo_v2_2026-04_2026-11.md` | `reports/` | Resultado e limites da v2 |
| `relatorios/replay_continuo_v3_2026-04_2026-11.md` | `reports/` | Resultado e os 4 pilares da v3 |
| `relatorios/inventario_replay_continuo_2026-11-13.md` | `reports/` | Origem dos dados, convenções e reparos da campanha |
| `relatorios/REPLAY_MULTIATIVOS.md` | `docs/` | Contrato do replay e como abrir o explorador |
| `dados/auditoria-v1/` (11 arquivos) | `output/auditoria-replay-20261115/` | Votos, sinais, posições e preços médios da v1; `verificacao.json` |
| `dados/auditoria-v2/` (7 arquivos) | `output/auditoria-replay-v2/` | Comparativo v1 × v2 em JSON e CSV |
| `dados/auditoria-v3/` (10 arquivos) | `output/auditoria-replay-v3/` | Comparativo v1 × v2 × v3 em JSON e CSV |
| `dados/series-v1/`, `series-v2/`, `series-v3/` | `data/replays/<versão>/exports/` | `daily.csv` (918 estados diários por versão), `dividends.csv`, `manifest.json`; base para curvas, drawdown e Sharpe |
| `telas/preview-desktop.jpg` | `data/replays/.../exports/` | Captura do explorador, candidata a figura |

### `05-replay-pilotos/` — antecedentes do replay

| Arquivo | Original | Uso |
|---|---|---|
| `replay_multiasset_2026-04.md` | `reports/` | Primeiro piloto, 06 a 17/04 |
| `replay_multiasset_2026-04-20_2026-05-05.md` | `reports/` | Segundo piloto, janela de queda |
| `janelas_queda_multiativos_2026-11-13.md` | `reports/` | Como a janela de queda foi escolhida |

### `06-operacao-diaria/` — observação operacional do capítulo 6

| Arquivo | Original | Uso |
|---|---|---|
| `Relógio de dados e preço de execução.md` | `reports/` | Regras de preço e horário de execução (DP-33) |
| `2026-10-14.md`, `2026-10-15.md` | `docs/daily/` | Registros dos primeiros dias do acompanhamento |

O arquivo `Resultados-comparados.md`, na raiz desta pasta, já existia e não foi alterado.

### `07-tcc1-versao-docs-faculdade/`

`main.tex` copiado de `docs/faculdade/monografia/`. Existem três versões do
texto do TCC 1 no repositório, com a mesma estrutura de seções e tamanhos
diferentes: esta (457 linhas), `tcc2/source/tcc1/main.tex` (407) e
`tcc2/referencia/main.tex` (360). Falta decidir qual é a versão entregue.

## Atenção: dados que vieram de fora do Git

Os 38 arquivos de `04-replay-abril-novembro/dados/` e `telas/` foram copiados
de `output/` e `data/replays/`, pastas que não são versionadas. Commitar esta
pasta publica esses arquivos no repositório, que é público. Eles trazem
resultados agregados, sem e-mails nem chaves; quatro deles (`comparacao_*.json`
e dois `manifest.json`) contêm o caminho local da máquina onde foram gerados.

## O que ficou de fora de propósito

| Material | Onde consultar | Motivo |
|---|---|---|
| Código (`scripts/continuous_replay*.py`, auditorias, `src/`, `dashboard/`) | no lugar | Citar pelo caminho; copiar fonte selado criaria duplicata sujeita a divergência |
| Chamadas ao modelo e explorador (`calls.json`, `calls.csv`, `explorer.json`, `index.html`, `operations.csv`, `decisions.csv`) | `data/replays/<versão>/exports/` | Mais de 100 MB por versão, fora do Git |
| Pacotes de evidência selados (`cal_a`, `sequential_dev`, `stress`, `h2_v*` e outros) | `docs/evidence/` | Centenas de MB, selados por hash |
| Demais documentos `H2_*` (operação, interface, runbooks) | `docs/` | Não são citados pela monografia |
| `AVALIACAO_COLETA_DADOS_2026-10-14.md`, `PESQUISA_MUNICAO_AGENTES.md`, `PLANO_IMPLEMENTACAO_MULTIAGENTES.md`, `HFL_PREMIUM_V5_PORTFOLIO.md`, `HFL_PLATFORM_AUDIT_V7.md`, `HFL_OPERATIONS_RUNBOOK.md` | `docs/` | Apoio secundário; copiar se algum capítulo passar a usá-los |
| Relatórios de integração com o Railway e revisão de endpoints | `reports/` | Operacionais |
| PDFs e normas do TCC 1 | `tcc2/source/tcc1/` e `tcc2/referencia/` | Já estavam na pasta |
