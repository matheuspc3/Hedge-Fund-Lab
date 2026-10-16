# Plano de migração e critérios de aceite (HFL-UX-001)

Consolida os entregáveis `UX_MIGRATION_PLAN` e `UX_ACCEPTANCE_CRITERIA`.
**Nada foi implementado:** a reescrita só começa depois da aprovação do UX-M1.

## 1. Princípios

1. **Nenhuma mudança de comportamento científico ou financeiro.** Validadores,
   runners, contratos, rotas `/api/*`, preflights, confirmações e efeitos de cada
   botão continuam idênticos, salvo decisão humana explícita registrada.
2. **Migração incremental por página**, com paridade de funções verificada antes
   de remover a versão antiga; rotas antigas viram aliases.
3. **Uma camada de apresentação:** dicionário de rótulos, glossário e tokens
   compartilhados; nada de texto duplicado por página.
4. **Sem dependências pesadas:** HTML/CSS/JS atuais, Chart.js já presente,
   testes DOM em Node (padrão do teste 20 da V7.4) e capturas via Chrome
   DevTools (padrão da V7.3).
5. **Nenhum novo caminho de inferência paga.** Toda ação paga continua
   passando pelo preflight e pela confirmação existentes.

## 2. Marcos

| Marco | Escopo | Depende de | Esforço relativo | Riscos | Critérios de aceite |
|---|---|---|---|---|---|
| **UX-M1** Auditoria e AI | esta entrega: inventário, sitemaps, jornadas, nomenclatura, glossário, design system, wireframes | — | M (feito) | proposta não validada com usuários | **aprovação humana** do sitemap, do dicionário de nomes e do design system |
| **UX-M2** Design system e componentes | tokens únicos (`--border-strong` ≥ 3:1, estados semânticos), selos, botões por natureza, stepper, diálogo de custo, ajuda "?", alertas, vazio/carregando; dicionário de rótulos e glossário como dados | M1 | L | regressão visual nas páginas antigas | componentes documentados; testes DOM do "?" (clique, teclado, Esc) e do diálogo de custo (botão desabilitado sem consentimento); contraste verificado por script |
| **UX-M3** Navegação e Início | shell de 6 áreas + Ajuda; remoção das navegações de página; aliases de rota; novo Início (jornada A) | M2 | M | links externos e favoritos antigos | todas as 18 rotas atuais respondem; zero navegação duplicada; Início sem ação paga; inventário V7.6.1 reexecutado sem destinos órfãos |
| **UX-M4** Mercado: Radar e análises | página do ativo (indicadores + comitê + Risk), Radar com stepper e confirmação padrão, "Detalhe do comitê" (renomeado), comparação | M3 | L | quebrar o fluxo pago do Radar | paridade: preparo, preflight, lote pago, replay e consulta funcionam igual (mesmas chamadas `/api/radar/*` e `/api/platform/radar-*`); testes existentes do Radar verdes |
| **UX-M5** Carteira, Gestor Global e simulações | separar Carteira hipotética, Gestor Global e Simulações (fim das 3 gerações na mesma página); selos de tratamento; **decisão U10** | M3 + decisão humana U10 | XL | U10 é mudança de comportamento | decisão U10 registrada; nenhuma demonstração sem selo sintético; rejeitada × válida distintas; nenhum caminho pago novo |
| **UX-M6** Operação diária, pesquisa e evidências | "Decisão do dia" (sem item duplicado de supervisão), carteiras prospectivas; Experimento H2 (títulos e selos); páginas novas e somente leitura de Evidências e Metodologia (leem `docs/evidence`) | M3 | L | ler documentos sem expor dados privados | nenhum journal privado exibido; Final Test exibido como bloqueado; estados H2 inalterados |
| **UX-M7** Auditoria, logs, configurações e ajuda | Auditoria (execuções, custos, registros, diagnóstico, recuperação), logs com identidade da plataforma, Ajuda (como funciona, glossário, FAQ) | M2, M3 | M | duplicar dados já mostrados em outras áreas | custos sempre como piso / reserva / cobrança desconhecida; recuperação rotulada "sem nova chamada" |
| **UX-M8** Acessibilidade, responsividade e testes finais | WCAG 2.2 AA em todas as páginas; 420/640/1024/1440 px; foco, zoom, leitor de tela; regressão completa | M4–M7 | M | descobrir problemas estruturais tarde | relatório de conformidade com limitações declaradas; capturas por ponto de quebra; suíte sem novas falhas |

Esforço relativo: S < M < L < XL (sem estimativa em horas antes do UX-M1
aprovado).

## 3. Decisão crítica antes do UX-M5 (U10)

A UI oferece um caminho pago para o **Global PM V1**, tratamento fechado pelo
protocolo V7.6, e só mostra a V2 em leitura. Opções:

| Opção | Efeito | Observação |
|---|---|---|
| a) desabilitar o caminho pago V1 na UI (V1 fica só para leitura) | interface coerente com o protocolo | mudança de comportamento; reversível |
| b) manter, rotulando "Tratamento V1 — histórico, fechado; nova inferência não entra no protocolo" | nenhum comportamento muda | risco de gasto fora do protocolo |
| c) expor a V2 com o mesmo fluxo | UI usa o tratamento vigente | **novo caminho de inferência paga na UI**: exige autorização própria e testes; a V7.4 deixou a V2 só no CLI de propósito |

**Recomendação:** (a) já no UX-M3, como mudança mínima e reversível, e (c) só
com decisão humana separada. Não implementado nesta entrega.

## 4. Critérios de aceite globais

### Funcionais

- Todas as funções inventariadas em [ux_inventory.json](ux_inventory.json)
  continuam acessíveis (checklist de paridade por botão).
- As mesmas chamadas de API por ação (comparação de rede antes e depois).
- Ações pagas: mesma sequência preflight → token → confirmação → claim; nenhum
  botão pago novo; nenhum "executar tudo".
- Registros históricos somente leitura em toda a interface.

### Visuais e de linguagem

- Um h1 por página; nenhuma versão no título; nomes conforme o dicionário.
- Todos os estados da tabela de semântica com ícone + texto + cor.
- Rejeitada ≠ válida; válida ≠ ordem autorizada.
- Todo termo do glossário com "?" no primeiro uso visível de cada página.

### Acessibilidade

- WCAG 2.2 AA: contraste ≥ 4,5:1 (texto) e ≥ 3:1 (componentes); foco visível;
  alvo ≥ 24 px; ajuda operável por teclado e toque; nada só por hover; nada só
  por cor.

### Integridade científica

- `check_preservation.py --since`: `violations: []`.
- Verificadores V7.5 e V7.6 sem divergência; suíte sem novas falhas.
- Nenhum arquivo selado, contrato, runner ou validador alterado.

## 5. Testes por marco

| Tipo | Ferramenta | Desde |
|---|---|---|
| Inventário e destinos | `scripts/review_v761.py ux` | M3 |
| DOM de componentes | Node + DOM simulado (padrão `test_global_pm_v2::test_20`) | M2 |
| Capturas por ponto de quebra | Chrome DevTools headless (padrão V7.3) | M3 |
| Contraste | script sobre os tokens | M2 |
| Regressão funcional | `pytest` completo + testes de API existentes | todos |
