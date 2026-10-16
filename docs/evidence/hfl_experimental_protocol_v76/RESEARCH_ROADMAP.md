# Roadmap de pesquisa

Fases futuras em ordem de prioridade (valor científico × viabilidade). Nenhuma
foi iniciada. Cada fase paga exige decisão humana, limite, preflight e
autorização próprios.

| Fase | Entrega | Depende de | Custo (reserva) | Valor | Viabilidade |
|---|---|---|---|---|---|
| **P1** | Revisão humana do pré-registro; decisões **[DECIDIR]**; versão congelada (`FROZEN_FOR_FUTURE_EVALUATION`) | V7.6 | 0 | alto | alta |
| **P2** | C1: repetibilidade V2 em S0 (10 + 19 tentativas) | P1; autorização paga | até US$ 4,632576 | alto: primeira estimativa de conformidade com denominador | alta: runner existe, cabe no teto selado |
| **P3** | Caminho de preparo com posições (código novo fora dos arquivos selados), qualificado offline com S1–S9 | P1 | 0 | alto: destrava a dimensão D | média |
| **P4** | C2: sensibilidade ao estado (S1, S4, S5) | P3; P2 concluída; autorização | US$ 0,79872 por cenário | médio | média |
| **P5** | Conferência COTAHIST das sessões de C3; autorização de orçamento Radar | P1 | 0 | médio | alta |
| **P6** | C3: retrospectiva fora da amostra (10 sessões) | P5; autorização | US$ 34,77504 | médio: generalização, com ressalvas temporais | média (reserva alta, custo observado baixo) |
| **P7** | Ledger paper multiativo separado + qualificação offline + controles | P1 | 0 | alto para a dimensão E | baixa/média: componente novo |
| **P8** | C4: prospectiva com paper (20 sessões) e controles | P7; protocolo congelado; autorização | US$ 69,55008 | alto | baixa: exige operação diária disciplinada |

## Trabalhos laterais (sem campanha)

| Item | Motivo | Exige |
|---|---|---|
| Tratamento Radar novo com agregação de pensamento correta (`null` ≠ 0) | errata de tokens | versão nova do tratamento Radar; nunca editar o V1 |
| Tratamento Global PM novo com `ERRORS` completo | auditoria A4 | versão nova; útil só se houver outra mudança de contrato |
| Conciliação de cobrança no console do provedor (12/10/2026) | custo real desconhecido | acesso humano ao console |
| Decisão sobre as falhas legadas da suíte | triagem | aprovação metodológica (preservação, V7.3, H2, Git) |
| Revisão humana independente da V7.5 e da V7.6 | a auditoria V7.6 foi feita pelo mesmo agente | revisor(a) humano(a) |
| Pacote de arquivamento sem journals privados | auditoria externa sem `data/` | decisão sobre o que pode ser publicado |

## Dependências

```text
P1 ─┬─> P2 ──────────────┐
    ├─> P3 ──> P4 <──────┘
    ├─> P5 ──> P6
    └─> P7 ──> P8
```
