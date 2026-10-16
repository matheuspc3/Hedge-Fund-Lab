# Wireframes (baixa fidelidade)

Texto monoespaçado, versionável e sem dependências. `[?]` = ajuda contextual;
`(◆ pago)` = botão de inferência paga; `🔒` = somente leitura; `⚗` =
demonstração sintética.

## 1. Shell (desktop e móvel)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ HEDGE-FUND-LAB        Início  Mercado  Carteira  Operação diária  Pesquisa   │
│                       Auditoria                     [?] Ajuda   ● Sem ordens │
│                                                                    reais [?] │
├──────────────────────────────────────────────────────────────────────────────┤
│ Mercado › Radar                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Móvel (≤ 640 px):  [☰ Menu]  HEDGE-FUND-LAB  [?]      ● Sem ordens reais
                   menu em lista; Esc fecha; foco volta ao botão
```

## 2. Início (jornada A)

```text
Início
O Hedge-Fund-Lab é um laboratório de pesquisa que testa agentes de IA na análise de ações da B3.
Nenhuma ordem real é enviada: as carteiras são virtuais ou hipotéticas. [?]

┌ Por onde começar ───────────────────────────────────────────────────────────┐
│ [Entender um ativo →]  [Montar uma carteira hipotética →]  [Ver a pesquisa →]│
└──────────────────────────────────────────────────────────────────────────────┘
┌ Ambientes ──────────────────────────────────────────────────────────────────┐
│ Operação diária PETR4   ● Paper prospectivo     Próximo pregão: 13/10 [?]   │
│ Radar e Gestor Global   ◆ Inferência real sob autorização  ⓘ consultivo     │
│ Pesquisa H2             🔒 Registro histórico   Final Test bloqueado [?]     │
│ Simulações              ⚗ Demonstração sintética                            │
└──────────────────────────────────────────────────────────────────────────────┘
┌ Atenção necessária (operador) ─────────── [Detalhes técnicos ▸] ────────────┐
│ ⛔ Bloqueado: orçamento agregado do Radar acima do teto local. Resolve-se em │
│    Auditoria › Execuções e custos.                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

Sem botões pagos no Início.

## 3. Ativo (jornada B)

```text
Mercado › Ativos › PETR4                          Sessão 09/10/2026 · B3 oficial [?]
[ Preço e indicadores ] [ Comitê ] [ Parecer de risco ]
┌ Preço ───────────────────────────────┐ ┌ Indicadores ─────────────────────────┐
│ (gráfico preço + Bollinger)          │ │ RSI 74,92 [?]      MACD +0,044 [?]   │
│ tabela alternativa ▸                 │ │ Vol. 21d 39,23% [?] Banda sup. −0,2% [?]│
└──────────────────────────────────────┘ └──────────────────────────────────────┘
┌ Comitê ──────────────────────────────────────────────────────────────────────┐
│ 5 votos: COMPRA ×5   Consenso [?]: COMPRA   Confiança técnica [?]: 0,744       │
│ Parecer de risco [?]: APROVADO (LLM consultivo)   Recomendação final: COMPRA  │
│ ⓘ Recomendação não é ordem. O gestor pode manter caixa.                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 4. Radar: lote de comitês (jornada C)

```text
Mercado › Radar          Execução: radar-2026-10-09-recovery-01 · Concluída ● [?]
Universo: PETR4 VALE3 ITUB4 WEGE3 BBAS3        Tratamento HFL-MULTIASSET-RADAR-V1 [?]

Fluxo   ① Preparar dados ─ ② Verificar requisitos ─ ③ Autorizar custo ─ ④ Resultado
        [Preparar dados]   [Verificar requisitos]   [Revisar custo e autorizar… (◆ pago)]

Sinais lado a lado [?]
┌ Ativo ┬ Votos C/M/V ┬ Consenso ┬ Risco         ┬ Recomendação ┬ Detalhe ┐
│ BBAS3 │ 5/0/0       │ COMPRA   │ ⛔ VETADO (regra)│ MANTER      │ [Abrir] │
└───────┴─────────────┴──────────┴───────────────┴──────────────┴─────────┘
[Comparar dois ativos]                [Levar seleção ao Gestor Global →]
```

## 5. Gestor Global: proposta (jornada D)

```text
Carteira › Gestor Global                Tratamento HFL-MULTIASSET-GLOBAL-PM-V2 [?]
ⓘ Consultivo: nenhuma proposta vira ordem.

┌ Fotografia [?] ───────────────────────────────────────────────────────────────┐
│ Caixa disponível [?] R$ 100.000,00   Reservado [?] 0   Recebível D+2 [?] 0     │
│ Pareceres: 5 (hashes verificados ✓)   Validade até 13/10 17:29                 │
└────────────────────────────────────────────────────────────────────────────────┘
Fluxo   ① Preparar ✓ ─ ② Verificar requisitos ✓ ─ ③ Autorizar custo ─ ④ Resultado
                                                   [Revisar custo e autorizar… (◆ pago)]

Resultado (válida)                               Resultado (rejeitada)
┌──────────────────────────────────────┐        ┌──────────────────────────────────────┐
│ ✓ Proposta válida pelas regras       │        │ ✕ Resposta rejeitada pelo validador   │
│   VALID_PROPOSAL [?]                 │        │   explanation_selection_inconsistent  │
│ Caixa-alvo 100% · 0 operações        │        │   "As listas de ativos não            │
│ Observação: ITUB4, PETR4 [?]         │        │    selecionados… não correspondem…"   │
│ ⓘ Não é ordem nem garantia de lucro  │        │ Intenção registrada (auditoria) ▸     │
│ Texto do modelo (não verificado) ▸   │        │ Sem gráfico de alocação               │
└──────────────────────────────────────┘        └──────────────────────────────────────┘
```

## 6. Diálogo de custo

Ver [DESIGN_SYSTEM_PROPOSAL.md](DESIGN_SYSTEM_PROPOSAL.md) §5.

## 7. Pesquisa › Evidências (jornada E)

```text
Pesquisa › Evidências                                              🔒 Somente leitura
┌ Pacote ─────────────────────┬ Estado ─────────────────┬ Hash/Commit ─┬────────┐
│ V7.5 Consolidação científica │ Verificado ✓ · 2 erratas │ b171c80      │ [Abrir] │
│ V7.6 Protocolo de robustez   │ Qualificado offline      │ 0da31e25…    │ [Abrir] │
│ V7.6.1 Revisão e UX          │ Aguardando revisão humana│ —            │ [Abrir] │
└──────────────────────────────┴──────────────────────────┴──────────────┴────────┘
Erratas: ERRATUM-HFL-2026-001 (tokens do Radar) · ERRATUM-HFL-2026-002 (restrição de compra)
Conclusões permitidas / proibidas ▸        Como reproduzir ▸
```

## 8. Auditoria (jornada F)

```text
Auditoria › Execuções e custos
Filtros: [Tudo ▾] [Rejeitadas] [Bloqueadas] [Recuperação necessária]
┌ Registro ───────────────┬ Tipo ─────┬ Estado ─────────────┬ Piso ──┬ Reserva ┬ Cobrança ─┐
│ v74-76d07…              │ Gestor V2 │ ✓ Válida · 🔒       │ 0,0263 │ 0,1597  │ desconhec.│
│ v7-5a78…                │ Gestor V1 │ ✕ Rejeitada · 🔒    │ 0,0235 │ 0,1597  │ desconhec.│
│ radar-…-recovery-01     │ Radar     │ ● Concluída · 🔒    │ 0,0431 │ 3,3178  │ desconhec.│
│ radar-…-original        │ Radar     │ ⛔ Incidente · 🔒   │ —      │ 3,3178* │ desconhec.│
└─────────────────────────┴───────────┴─────────────────────┴────────┴─────────┴───────────┘
* reserva incerta, nunca liberada [?]
[Recuperar sem nova chamada]  (aparece só em registros com recuperação possível)
```

## 9. Painel de ajuda aberto

```text
Confiança técnica [?]
┌───────────────────────────────────────────────────────────────┐
│ Confiança técnica (qualitativa)                       [×]     │
│ Número de 0 a 1 que resume quão firmes foram os votos.        │
│ ▸ Saiba mais                                                   │
│ ⚠ Não é probabilidade de lucro nem tamanho de posição.        │
│ Como o laboratório calcula ▸   Glossário completo →           │
└───────────────────────────────────────────────────────────────┘
```
