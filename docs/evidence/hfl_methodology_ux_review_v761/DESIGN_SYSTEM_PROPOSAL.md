# Proposta de design system

Base: os tokens de `dashboard/shell.css` (o conjunto mais completo e já
compartilhado), unificando `paper.css` e `radar.css`. Sem dependências novas:
CSS com propriedades personalizadas e componentes HTML/JS simples, no padrão
atual do projeto.

## 1. Tokens

### Cor (tema escuro atual; tema claro opcional no UX-M8)

| Token | Valor | Uso | Contraste sobre `--bg` / `--surface` |
|---|---|---|---|
| `--bg` | `#0b1118` | fundo | — |
| `--surface`, `--surface-2` | `#131e29`, `#192838` | cartões, painéis | — |
| `--text` | `#edf3f8` | texto | 16,95 / 15,08 |
| `--text-2` | `#bccbd8` | texto secundário | 11,44 / 10,18 |
| `--muted` | `#9aaebf` | legenda | 8,29 / 7,37 |
| `--link` | `#a1cfff` | links | 11,63 / 10,35 |
| `--border-strong` (novo) | a definir com ≥ 3:1 | contorno de campos e controles | **obrigatório ≥ 3:1** (hoje `--line` 1,67 e `--border2` 2,34 falham o 1.4.11 como contorno único) |
| `--line` | `#2a3c4c` | divisórias decorativas apenas | — |

Tokens **semânticos de estado** (substituem as cores soltas de `paper.css`):
`--state-ok`, `--state-warn`, `--state-error`, `--state-info`,
`--state-neutral`, `--state-synthetic`, `--state-paid`. Cada um tem fundo,
texto e borda, e todas as combinações de texto precisam de ≥ 4,5:1.

### Tipografia

`--sans: system-ui, -apple-system, 'Segoe UI', sans-serif` (atual) e
`--mono` para hashes, códigos e números tabulares. Escala: 12 / 14 / 16
(corpo) / 20 / 24 / 32 px; altura de linha 1,5 no corpo. **Um único h1 por
página**; h2 para seções e h3 para cartões.

### Espaçamento e forma

Escala de 4 px: 4, 8, 12, 16, 24, 32, 48. Raio 8 px (cartões) e 6 px
(controles). Alvos de clique ≥ 24 × 24 px (WCAG 2.2, 2.5.8), 44 × 44 em móvel.

## 2. Componentes

| Componente | Função | Regras |
|---|---|---|
| Shell (único) | navegação global de 6 áreas + Ajuda + selo "Sem ordens reais" | substitui todas as navegações de página |
| Subnavegação local | abas da mesma entidade | ≤ 6 abas; `role="tablist"`; estado na URL |
| Cabeçalho de página | h1, uma frase de propósito, selos de natureza (consultivo, sintético…) | sem versões no título |
| Cartão | bloco de informação | título h2/h3, conteúdo, ação opcional |
| Selo de estado | estado de um registro | ícone + texto + cor (seção 3) |
| Selo de tratamento | `HFL-…-V2` + hash curto + link para evidência | metadado, monoespaçado |
| Botão por natureza | consulta, preparação, paga, simulação | seção 4 |
| Stepper de fluxo | Preparar → Verificar → Autorizar → Resultado | cada etapa com estado próprio |
| Diálogo de confirmação de custo | única porta para inferência paga | seção 5 |
| Tabela | dados tabulares | cabeçalho fixo, rolagem com foco, números alinhados à direita, unidade no cabeçalho |
| Gráfico | séries financeiras | Chart.js (já presente em `vendor/`); legenda textual e tabela alternativa |
| Ajuda "?" | explicação contextual | [CONTEXTUAL_HELP_GLOSSARY.md](CONTEXTUAL_HELP_GLOSSARY.md) |
| Alerta | informação, aviso, erro, bloqueio | ícone + título + ação sugerida; `role="status"` ou `role="alert"` |
| Estado vazio | "nada aqui ainda" | explica por quê e o que fazer, sem acionar nada |
| Carregando | leitura em andamento | texto "Lendo registros locais…" (não só spinner) |
| Detalhes técnicos | profundidade progressiva | `<details>` com rótulo "Detalhes técnicos" |

## 3. Semântica visual dos estados

Nunca só cor: todo estado tem ícone e texto.

| Estado | Ícone | Texto do selo | Cor | Observação |
|---|---|---|---|---|
| Preparado | ◐ | Preparado | info | criou registro; nada foi pago |
| Bloqueado | ⛔ | Bloqueado: <motivo> | warn | sempre com o motivo e o caminho de resolução |
| Em execução | ⟳ | Em execução | info | com início e o que está acontecendo |
| Concluído | ● | Concluído | neutral | ação terminou; não diz se é válido |
| Validado | ✓ | Proposta válida pelas regras | ok | **sem** destaque de "aprovado para operar" |
| Rejeitado | ✕ | Rejeitada pelo validador | error | título explícito, motivo com código e descrição |
| Expirado | ⌛ | Validade expirada | neutral | ao lado do estado selado, sem substituí-lo |
| Somente leitura | 🔒 | Somente leitura | neutral | registros históricos |
| Demonstração sintética | ⚗ | Demonstração sintética | synthetic | padrão listrado ou borda tracejada em todo o bloco |
| Inferência oficial | ◆ | Inferência real (Gemini) | info | com tratamento e data |
| Resultado consultivo | ⓘ | Consultivo: não é ordem | neutral | obrigatório junto de toda proposta |

Regras:

- Uma resposta rejeitada **nunca** usa o mesmo destaque de uma válida
  (padrão já iniciado na V7.4).
- Uma proposta válida nunca usa verde de "sucesso operacional", nem botões de
  executar ordem.
- Selos de natureza (sintético, consultivo) aparecem no **cabeçalho do bloco**,
  não só no rodapé.

## 4. Natureza das ações

| Natureza | Efeito | Botão | Confirmação |
|---|---|---|---|
| **Consulta** | lê registros; não cria contexto; não chama provedor | secundário (contorno) | nenhuma |
| **Preparação** | cria snapshot/registro; sem chamada paga | primário neutro + ícone de gravação | resumo do que será gravado |
| **Inferência paga** | consome orçamento; chama o provedor | **único** estilo "pago" (ícone de moeda + rótulo "pago") | **diálogo padrão de custo** + preflight válido |
| **Simulação** | contas hipotéticas em memória ou ledger paper autorizado | secundário com ícone de simulação | nenhuma (memória) ou autorização humana (paper) |
| **Registro histórico** | somente leitura | sem botões de ação | — |

Proibido: botão "Executar tudo"; ações pagas sem preflight; ações pagas no
Início; rótulos com negação para indicar ausência de custo ("sem Gemini"),
porque a ausência de custo é dita pelo componente.

## 5. Padrão de confirmação de custo

```text
┌ Autorizar inferência paga ────────────────────────────────────────┐
│ O que será executado   Gestor Global — 1 proposta de carteira      │
│ Tratamento             HFL-MULTIASSET-GLOBAL-PM-V2  (159fd196…)    │
│ Fotografia/contexto    v76-c1-pilot-20261009-r001  (c4879f28…)     │
│ Chamadas máximas       1 (sem nova tentativa automática)           │
│ Custo estimado         US$ 0,0197   (planejamento, não fatura)     │
│ Reserva conservadora   US$ 0,159744 (bloqueada, nunca devolvida)   │
│ Orçamento usado/teto   US$ 0,319488 / US$ 5,00                     │
│ Validade do contexto   até 13/10/2026 17:29 BRT                    │
│ Consequências          cria registro permanente; uma falha incerta │
│                        pode ser cobrada; nada é executado no       │
│                        mercado                                     │
│ [ ] Li e autorizo esta inferência paga                             │
│                         [Cancelar]   [Autorizar esta inferência]   │
└────────────────────────────────────────────────────────────────────┘
```

Regras: os dados vêm do **preflight** (token incluído); o botão só se habilita
com a caixa marcada; Esc e Cancelar não fazem nada; um diálogo por inferência
ou lote, nunca agregando tratamentos diferentes.

## 6. Mensagens

| Tipo | Modelo |
|---|---|
| Vazio | "Nenhuma proposta registrada para esta seleção. Prepare uma fotografia para começar." |
| Carregando | "Lendo registros locais… nenhum processo foi iniciado." |
| Erro | "Não foi possível ler <o quê>. <causa>. <o que fazer>." + código técnico em detalhes |
| Bloqueio | "Bloqueado: <motivo>. Resolve-se em <onde>." |
| Rejeição | "Resposta rejeitada pelo validador: <descrição> (`<código>`)." |
| Sucesso de consulta | sem toast; atualizar o conteúdo e a hora da leitura |

## 7. Acessibilidade e responsividade

- Referência: **WCAG 2.2 AA**. Verificado nesta entrega: contraste dos tokens
  de texto (≥ 6,5:1) e falha das bordas como contorno único (U14). **Não
  verificado:** renderização, ordem de foco real, zoom 200%/400%, leitores de
  tela; isso fica para o UX-M8, com ferramentas sem dependência pesada (Chrome
  DevTools, como na V7.3).
- Pontos de quebra: 420, 640, 1024 e 1440 px (os já usados nas validações da
  V7.3). Sem rolagem horizontal da página; tabelas rolam dentro da própria
  região com foco.
- `prefers-reduced-motion` respeitado (já existe em `shell.css` e `paper.css`).
