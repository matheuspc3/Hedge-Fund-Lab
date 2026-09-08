# Documentação do Hedge-Fund-Lab

Este diretório separa o que o projeto **faz hoje** do que foi **planejado** ou
escrito como direção acadêmica. Os documentos antigos continuam úteis para
recuperar intenção, mas não são evidência de que uma funcionalidade existe ou de
que um resultado é metodologicamente válido.

## Por onde começar

1. [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md) — baseline auditada em 24/08/2026:
   capacidades reais, limitações, qualidade e divergências documentais.
2. [`ARQUITETURA.md`](ARQUITETURA.md) — fluxos implementados, fronteiras atuais
   e arquitetura-alvo para uma arena comparável.
3. [`PLANO_EVOLUCAO.md`](PLANO_EVOLUCAO.md) — sequência recomendada de trabalho,
   decisões pendentes e critérios objetivos de conclusão.

## Classificação dos documentos

| Documento | Papel | Autoridade sobre o estado atual |
|---|---|---|
| `README.md` da raiz | Entrada operacional e setup | Média; deve apontar para esta baseline |
| `docs/ESTADO_ATUAL.md` | Fotografia verificável da implementação | Alta |
| `docs/ARQUITETURA.md` | Arquitetura implementada e alvo aprovado | Alta |
| `docs/PLANO_EVOLUCAO.md` | Backlog priorizado | Alta para a ordem, não para fatos implementados |
| `docs/PLAN_HEDGEFUND.md` | Plano original detalhado | Histórico |
| `docs/ROADMAP_IDEIAS.md` | Ideias e direção anterior | Histórico |
| `HANDOFF_OUTRO_PC.md` | Registro de uma etapa de desenvolvimento | Histórico e potencialmente defasado |
| `docs/faculdade/monografia/` | Texto acadêmico e intenção metodológica | Acadêmica; precisa ser reconciliada com o código |

## Vocabulário de status

- **Implementado**: existe um caminho executável no estado atual do repositório.
- **Parcial**: existe, mas falta integração, robustez ou fidelidade ao objetivo.
- **Bloqueado para ciência**: executa tecnicamente, porém ainda não sustenta uma
  comparação experimental válida.
- **Planejado**: aparece apenas em documentação, backlog ou texto acadêmico.
- **Histórico**: descreve uma decisão ou estado anterior e não deve guiar o código
  sem nova validação.

## Regra de manutenção

Toda mudança que altere participante, dado, relógio de decisão, execução, custo,
métrica ou auditoria do experimento deve atualizar `ESTADO_ATUAL.md` e, se mudar
uma fronteira, `ARQUITETURA.md`. Resultados gerados nunca devem ser promovidos a
evidência científica sem cumprir a definição de pronto de `PLANO_EVOLUCAO.md`.
