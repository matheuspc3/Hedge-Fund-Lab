# Hedge-Fund-Lab — início

Vault do TCC e ponto de entrada do projeto. Atualizado em **15/10/2026**.

## Onde estamos

**V7.6.5: ledger multiativos qualificado offline com dados sintéticos.**
A execução paper oficial multiativos continua desabilitada. A plataforma ativa é
multiativos, com Radar/Mercado/Gestor Global. O experimento independente PETR4/H2
e os backtests antigos ficam em Legacy somente consulta (DP-16); PETR4 permanece
no universo multiativos. Validação de proposta não é operação
nem evidência de rentabilidade.

**APP-01/02 disponíveis:** na página inicial do dashboard, abra **Criar carteira**,
informe nome, natureza, caixa inicial e data. Selecione a carteira e preencha
**Registrar operação → Ver prévia → Confirmar registro**. Compras/vendas antigas
são permitidas desde o início informado; **Corrigir** preserva o original e permite
substituição ou anulação com motivo. Os registros permanecem após reiniciar.
Não há envio de ordens. **APP-03 parcial:** a home mostra patrimônio estimado,
evolução e preços diários abaixo das posições, usando fechamentos RAW locais
verificados. Datas sem cotação ficam pendentes; não há preço ao vivo. Coleta
contínua e proventos ainda faltam.

**Histórico das ações (DP-25):** abaixo das posições, selecionar ações e período
ou arrastar para medir variação em R$/%. Histórico diário Yahoo máximo guardado
localmente, desde 2000; **Atualizar histórico Yahoo** renova as cópias, sem mudar
o patrimônio B3 ou as operações. Fonte/ajustes identificados; sem intradiário.

**Análises por carteira (DP-22):** no Início, use **Abrir quórum para esta carteira**,
ou no Radar abra **Nova análise para uma carteira**. Carteira, dia-alvo editável
e sessão dos dados ficam preservados em execução própria. Criação não dispara
inferência; o comitê por ativo ainda não recebe posições/dia-alvo nos prompts.
**Gestor da carteira (DP-24/APP-05):** em **Agentes → Resultados**, informar custos,
preparar o plano e autorizar separadamente a chamada do gestor. Revisar quantidades
parciais/totais, referência RAW, custos e caixa; **Ver prévia → aprovar e registrar**
confirma a cesta simulada inteira. Usa fechamento identificado, sem cotação ao vivo
ou OPEN futuro. Buy & Hold permanece consultiva e sem rebalanceamento automático;
use uma análise vinculada à Multiagentes para suas movimentações.

## Abrir primeiro

**Frontend DP-23:** Carteira, Operações, Agentes, Comparação e Dados no menu
principal. O seletor do topo acompanha a navegação. Para cadastrar, use **Criar
carteira**; a operação fica em **Operações → Ver prévia → Confirmar registro**.
Em Agentes, configure a análise e prossiga em **Dados e custo**; executar a IA
continua exigindo consentimento próprio. Histórico e Legacy permanecem disponíveis.

| Quero… | Abrir |
|---|---|
| Lembrar onde queremos chegar e o que decidimos | [Direção do projeto](docs/DIRECAO_DO_PROJETO.md) — ler antes de iniciar trabalho |
| Saber o próximo passo | [Roadmap](docs/ROADMAP.md) — começar por PAPER-01 |
| Entender o que existe hoje | [Estado atual](docs/ESTADO_ATUAL.md) |
| Usar a plataforma e entender o que ainda falta | [Ciclo completo de uso](docs/CICLO_USO_PLATAFORMA.md) |
| Encontrar documentos, evidências e orientações do Obsidian | [Índice único da documentação](docs/README.md) |
| Entender o código e iniciar o projeto | [README técnico](README.md) |
| Trabalhar no texto do TCC | [Monografia](docs/faculdade/monografia/main.tex) |
| Consultar planos antigos | [Arquivo histórico](docs/archive/README.md) |

## Regra de navegação

Este repositório já é o vault: `.obsidian` fica na raiz e os documentos
continuam em `docs`. Não criar uma segunda cópia das evidências para o Obsidian.
Links Markdown relativos funcionam como navegação entre as notas e mantêm
o material legível fora do aplicativo.

O documento de direção fixa o objetivo e as decisões; o roadmap contém o plano
ativo; evidências preservam o que aconteceu em cada
versão. Dúvidas e propostas continuam identificadas como tais até decisão
registrada. Não editar documento selado para fazê-lo parecer atualizado.
