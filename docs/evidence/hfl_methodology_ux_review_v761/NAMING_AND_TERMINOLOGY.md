# Nomenclatura e terminologia

## 1. Convenções

1. **Português brasileiro, orientado à ação** nos títulos de botão: verbo no
   infinitivo + objeto ("Verificar requisitos", "Autorizar custo").
2. **Um conceito, um nome** em toda a aplicação. O termo técnico aparece como
   subtítulo ou na ajuda "?", nunca como única informação.
3. **Nenhuma versão no nome de página.** Versões e identidades científicas
   (`HFL-MULTIASSET-GLOBAL-PM-V2`, "H2 v6", hashes) aparecem como selos de
   metadado.
4. **Rótulos de ação incluem a natureza da ação** por componente (selo/ícone),
   não por negação textual ("sem Gemini", "sem executar").
5. **Datas não entram em rótulos de navegação** ("Prontidão para 13/10" →
   "Próximo pregão", com a data dentro da página).
6. **Não se renomeiam** identificadores científicos, chaves de API, rotas
   persistidas, campos de contrato ou status selados
   (`VALID_PROPOSAL`, `REJECTED_BY_VALIDATOR`). A tela mostra um rótulo amigável
   ao lado do código original.

## 2. Distinções obrigatórias

| Conceito | Nome visível | Nunca chamar de |
|---|---|---|
| leitura de dados e indicadores | **Análise de mercado** | "operação" |
| voto/parecer de um agente | **Parecer do agente** (analista, Risk) | "recomendação de investimento" |
| resultado agregado de um comitê | **Parecer do comitê** | "ordem", "sinal de compra executável" |
| alocação proposta pelo gestor | **Proposta de carteira** | "ordem", "decisão executada" |
| verificação determinística | **Validação** (válida / rejeitada) | "aprovação para operar" |
| contas hipotéticas em memória | **Simulação** | "execução" |
| lançamento em carteira virtual prospectiva | **Execução virtual (paper)** | "operação real" |
| resultados selados | **Registro histórico** | "resultado ao vivo" |
| envio de ordem a corretora | **Operação real, desabilitada** | — (nunca oferecida) |

## 3. Dicionário: nome atual → nome proposto

| Atual | Onde | Proposto | Termo técnico preservado (subtítulo/ajuda) |
|---|---|---|---|
| Visão Geral (grupo do menu, `/`) | shell | **Início** | — |
| Visão Geral (vista do `/paper`) | `paper.html` | **Resumo das carteiras** | — |
| Visão geral (aba do `/h2`) | `h2.html` | **Resumo do experimento** | — |
| Operação (grupo) / Operação Paper / Operação Paper Trading / Operação PETR4 | shell, cabeçalhos | **Operação diária PETR4** | paper trading prospectivo |
| Paper Trading (link para `#visao`) | shell | **Carteiras prospectivas** | — |
| Sala de Decisão (`/paper#sala`) | `paper.html`, shell | **Decisão do dia** | deliberação dos agentes H2 |
| Supervisão Humana (alias de `#sala`) | shell | removido do menu; seção "Aprovação humana" dentro de Decisão do dia | — |
| Sala de Decisão (`/radar#room`) | `radar.html` | **Detalhe do comitê** | — |
| Mercado e Abertura / Mercado | shell / `paper.html` | **Mercado e abertura (PETR4)** | — |
| Laboratório (grupo) | shell | dividido entre **Mercado** e **Carteira multiativos** | — |
| Radar Multiativos / Radar de Ativos / Continuar no Radar | shell, cabeçalhos | **Radar** (área Mercado) | `HFL-MULTIASSET-RADAR-V1` |
| Gestor Global / Gestor de Carteira | shell, cabeçalhos | **Gestor Global** | Global PM; tratamento como selo |
| Proposta da IA | `portfolio.html` | **Propostas de carteira** | — |
| Propostas e Simulações | shell | **Simulações e demonstrações** | — |
| Agentes | shell (`/paper#agentes`) | **Catálogo de agentes H2** (em Pesquisa) | — |
| Pesquisa e Auditoria (grupo) | shell | **Pesquisa** e **Auditoria** (duas áreas) | — |
| Histórico H2 v6 | shell | **Experimento H2** (Pesquisa) | H2 v6 |
| Auditoria Operacional / Processos e Auditoria | shell | **Auditoria › Registros** | — |
| Logs Técnicos / 📋 Hedge-fund-lab Logs | shell, `logs.html` | **Logs técnicos** | — |
| Backtests Legados | shell | **Backtests legados** (Pesquisa) | — |
| Prontidão para 13/10 | shell | **Próximo pregão** | — |
| Carteiras Prospectivas | shell | **Carteiras prospectivas** | — |
| 1. Atualizar dados / 1. Preparar dados / 2. Preparar snapshot e Risk · sem Gemini | botões | **Preparar dados** | snapshot / contexto |
| 2. Preflight / 2. Verificar preflight / 3. Preflight global | botões | **Verificar requisitos** | preflight |
| 3. Confirmar e executar agentes / 3. Confirmar e executar este lote / 4. Solicitar proposta · confirmar custo | botões | **Revisar custo e autorizar…** (abre a confirmação padrão) | inferência paga |
| Autorizar e executar Gemini / Confirmar somente esta inferência | diálogos | **Autorizar esta inferência paga** | — |
| Recuperar somente offline | botões | **Recuperar sem nova chamada** | replay offline |
| Consultar registros / Consultar resultados | botões | **Atualizar a lista** | — |
| Simular proposta sem executar / Simular cenário offline | botões | **Simular (sem custo, sem registro)** | — |
| Contexto / Snapshot (quando o usuário vê) | textos | **Fotografia da carteira e dos pareceres** | snapshot / contexto congelado |
| Claim | textos | **Registro de tentativa** | claim |
| Journal | textos | **Diário de chamadas** | journal |
| Risk / Risco consultivo | colunas | **Parecer de risco** (+ selo "regra" ou "LLM") | Risk individual |
| VALID_PROPOSAL | selos | **Proposta válida pelas regras** (código ao lado) | `VALID_PROPOSAL` |
| REJECTED_BY_VALIDATOR | selos | **Resposta rejeitada pelo validador** | `REJECTED_BY_VALIDATOR` |
| PREMIUM V4 / V6 / V7, NOVO EXPERIMENTO V6 | cabeçalhos | removidos; versão em "Sobre" e nos selos de tratamento | — |

## 4. O que não muda

Rotas (com aliases), endpoints `/api/*`, campos JSON, identidades
`HFL-*`, `record_id`, status selados, nomes de arquivo de evidência e CLIs. A
mudança é de **apresentação**, via uma camada de rótulos (dicionário único
consumido pelas páginas).
