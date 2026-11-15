# Sumário Proposto — TCC 2

> Proposta de estrutura para os capítulos (arquivos `tcc2/chapters/0N-*.tex`),
> alinhada à ordem de produção de `WRITING_RULES.md`. Não escrever resultados
> antes de existirem. Os capítulos 1–3 e 5 podem ser redigidos já; 6–7 dependem
> das pendências experimentais.

## Estrutura e dependências

| # | Capítulo | Arquivo | Depende de |
|---|---|---|---|
| 1 | Introdução | `01-introducao.tex` | objetivo/hipóteses (congelados) |
| 2 | Fundamentação Teórica | `02-fundamentacao.tex` | literatura (verificar bib) |
| 3 | Trabalhos Relacionados | `03-relacionados.tex` | bibliografia (Xia2026, FinCoT, etc.) |
| 4 | Arquitetura e Implementação | `04-arquitetura.tex` | `INVENTARIO_TECNICO.md` |
| 5 | Metodologia Experimental | `05-metodologia.tex` | `EXPERIMENT_PROTOCOL.md`, freeze |
| 6 | Resultados e Discussão | `06-resultados.tex` | **resultados reais** (pendente) |
| 7 | Conclusão | `07-conclusao.tex` | cap. 6 |

## Conteúdo por capítulo

- **Introdução** — problema, objetivo geral/específicos, hipóteses H1/H2/H0
  (idênticas ao TCC 1), contribuição ("laboratório quantitativo reproduzível,
  auditável e extensível" — freeze §15), organização do trabalho.
- **Fundamentação** — eficiência de mercado (Fama 1970), momentum (Jegadeesh &
  Titman 1993), teoria de carteiras (Markowitz 1952), métricas de risco
  (Sharpe 1966/1994, Sortino 1994, MaxDD, turnover), overfitting de backtest
  (Bailey et al.), 1/N (DeMiguel 2009), caminhos LLM/agentes.
- **Relacionados** — agentic trading (Xia 2026), FinCoT, demais trabalhos LLM
  em finanças; lacuna que o laboratório preenche.
- **Arquitetura** — stack real (stdlib/SQLite/SQLAlchemy/LangGraph/B3),
  módulos, pipeline, arena, proveniência. **Não** repetir Prefect/PostgreSQL.
- **Metodologia** — desenho experimental (Hardening → CAL-A → SEQUENTIAL →
  STRESS → CAL-B → FREEZE → VALIDATION → FINAL TEST), pseudo-live causal,
  gates, âncoras, Bootstrap A, calibração ≠ treinamento, ameaças à validade.
- **Resultados** — tabela de métricas principais, curva de patrimônio, drawdown
  (formato já antecipado no TCC 1). Somente com dados reais; `TODO` para o que
  faltar.
- **Conclusão** — síntese, limitações, trabalhos futuros.

## Observações

- Capítulos 1–3 e 5 são redigíveis agora a partir do que já está congelado.
- Capítulo 4 usa o `INVENTARIO_TECNICO.md` como fonte.
- Capítulos 6–7 ficam bloqueados até `PENDENCIAS_EXPERIMENTAIS.md` §2 ser
  resolvido (resultados reais de H1/H2 e inferência).
- Antes de redigir, executar o `revisor-cientifico` sobre os textos; aprovação
  final é dos autores e do orientador.
