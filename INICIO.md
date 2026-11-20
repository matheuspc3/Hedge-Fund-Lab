# Hedge-Fund-Lab — início

Vault do TCC e ponto de entrada do projeto. Atualizado em **19/11/2026**.

O Hedge-fund-lab acompanha e compara carteiras simuladas de ações da B3: uma carteira
decidida por agentes baseados em LLM (comitê de analistas, analista de risco e gestor) e
carteiras de referência determinísticas. Decisões, operações, caixa e patrimônio ficam
registrados e podem ser auditados.

## Onde estamos

- **Acompanhamento diário:** o ciclo autônomo da carteira Multiagentes (DP-34) roda todo
  pregão no servidor do Railway, acessível pela rede Tailscale, ao lado das carteiras de
  referência. A Multiagentes diária usa a arquitetura da v1.
- **Replay Contínuo Abril–Novembro de 2026 (DP-37):** 153 pregões com três versões da
  carteira Multiagentes (v1, v2 e v3) contra cinco referências. Consulta em
  `/laboratory/replay/` (v1), `/laboratory/replay/v2/` e `/laboratory/replay/v3/`.
- **Monografia do TCC 2:** em `tcc2/overleaf/`, pronta para o Overleaf. Revisão geral
  aplicada; falta o polimento final e 20 PDFs de referências pagas ou de livros.

O detalhe de cada entrega, com datas e verificações, está no
[estado atual](docs/ESTADO_ATUAL.md).

## Abrir primeiro

| Quero… | Abrir |
|---|---|
| Lembrar onde queremos chegar e o que decidimos | [Direção do projeto](docs/DIRECAO_DO_PROJETO.md), antes de começar qualquer trabalho |
| Saber o próximo passo | [Roadmap](docs/ROADMAP.md) |
| Ver o que já foi feito e verificado | [Estado atual](docs/ESTADO_ATUAL.md) |
| Encontrar documentos e evidências | [Índice da documentação](docs/README.md) |
| Instalar e rodar o projeto | [README técnico](README.md) |
| Usar a plataforma | [Ciclo de uso](docs/CICLO_USO_PLATAFORMA.md) |
| Mexer no servidor e no ciclo diário | [Deploy no Railway](docs/DEPLOY_RAILWAY.md) |
| Consultar o replay e seus resultados | [Replay multiativos](docs/REPLAY_MULTIATIVOS.md) e [evolução v1/v2/v3](reports/evolucao_replay_v1_v2_v3_tcc.md) |
| Trabalhar na monografia | [Monografia do TCC 2](tcc2/LEIA-ME.md) |
| Consultar planos antigos | [Arquivo histórico](docs/archive/README.md) |

## Pastas

| Pasta | O que tem |
|---|---|
| `dashboard/` | Servidor, interface web, ciclo diário e APIs das carteiras |
| `src/` | Núcleo: dados da B3, indicadores, agentes, *backtesting* e experimentos |
| `scripts/` | Executores das campanhas, auditorias e utilitários. Quase todos são citados em evidências seladas: não renomear nem mover |
| `tests/` | Testes e verificações |
| `docs/` | Direção, roadmap, estado, especificações e evidências seladas (`docs/evidence/`) |
| `reports/` | Relatórios das campanhas do replay e revisões |
| `tcc2/` | Monografia do TCC 2 e o material de apoio; ver [tcc2/LEIA-ME.md](tcc2/LEIA-ME.md) |
| `data/`, `output/` | Dados e resultados locais, fora do Git |

## Regra de navegação

Este repositório já é o vault: `.obsidian` fica na raiz e os documentos continuam em
`docs`. Não criar uma segunda cópia das evidências para o Obsidian. Links Markdown
relativos funcionam como navegação entre as notas e mantêm o material legível fora do
aplicativo.

O documento de direção fixa o objetivo e as decisões; o roadmap contém o plano ativo; as
evidências preservam o que aconteceu em cada versão. Dúvidas e propostas continuam
identificadas como tais até decisão registrada. Não editar documento selado para
fazê-lo parecer atualizado.
