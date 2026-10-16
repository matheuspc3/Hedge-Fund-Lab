# Navegação (UX-M3) e página inicial

Consolida os entregáveis `NAVIGATION_MAPPING` e `HOMEPAGE_IMPLEMENTATION`.

## 1. Antes × depois

| | Antes (V7.6.1, reconfirmado no código) | Depois (V7.6.2) |
|---|---|---|
| Menus | shell com 4 grupos e 17 links, **mais** cabeçalhos próprios ocultos por CSS em `/radar`, `/portfolio`, `/paper`, `/h2`, `/logs` | **um** shell, renderizado pelo servidor a partir de `AREAS`; cabeçalhos de página removidos do HTML |
| Organização | por origem técnica: Visão Geral · Operação · Laboratório · Pesquisa e Auditoria | por objetivo: **Início · Mercado · Carteira multiativos · Operação diária PETR4 · Pesquisa · Auditoria**, mais **Ajuda** global |
| Subnavegação | grupos com 4–5 links, alguns duplicados (Supervisão = Sala) | 0 a 4 seções por área; barra de seções oculta quando há uma só |
| Página atual | `aria-current` no grupo, sem breadcrumb útil | área (`aria-current="true"`), seção (`aria-current="page"`), breadcrumb "Hedge-Fund-Lab › Área › Seção" e faixa de ambiente por área |
| Versões em títulos | "Premium V4", "Premium V6", "PREMIUM V7" | nenhuma (`<title>` = "Página · Área · Hedge-Fund-Lab") |
| Celular | botão "Menu da plataforma", aviso "sem ordens reais" escondido | botão "Menu" com Esc; aviso de segurança sempre visível; alvos de 44 px |

## 2. Mapa de links

| Link antigo (grupo) | Destino | Agora |
|---|---|---|
| Carteiras Prospectivas (Visão Geral) | `/#wallets` | painel no Início; também Operação diária › Carteiras prospectivas |
| Prontidão para 13/10 (Visão Geral) | `/#readiness` | painel "Operação diária PETR4 · atenção necessária" no Início (sem data no menu) |
| Processos e Auditoria (Visão Geral) / Auditoria Operacional (Pesquisa e Auditoria) | `/#audit` | **Auditoria › Registros e processos** |
| Continuar no Radar (Visão Geral) / Radar Multiativos (Laboratório) | `/radar` | **Mercado › Radar de comitês** |
| Sala de Decisão (Operação) | `/paper#sala` | **Operação diária PETR4 › Decisão do dia** |
| Paper Trading (Operação) | `/paper#visao` | Operação diária PETR4 › Resumo das carteiras |
| Carteiras (Operação) | `/paper#carteiras` | Operação diária PETR4 › Carteiras prospectivas |
| Supervisão Humana (Operação) | `/paper#supervisao` (alias de `#sala`) | removido do menu (era o mesmo destino); o link antigo continua funcionando e marca "Decisão do dia" |
| Mercado e Abertura (Operação) | `/paper#mercado` | Operação diária PETR4 › Mercado e abertura |
| Gestor Global (Laboratório) | `/portfolio#global-workflow` | **Carteira multiativos › Gestor Global: registros** |
| Propostas e Simulações (Laboratório) | `/portfolio#ai-proposal` | Carteira multiativos › Propostas e simulações |
| — | `/portfolio#carteira-contabil` (âncora nova) | Carteira multiativos › Carteira contábil (demonstração) |
| Agentes (Laboratório) | `/paper#agentes` | **Pesquisa › Catálogo de agentes H2** |
| Histórico H2 v6 (Pesquisa e Auditoria) | `/h2` | **Pesquisa › Experimento H2** |
| Logs Técnicos | `/logs` | **Auditoria › Logs técnicos** |
| Backtests Legados | `/legacy` | Pesquisa › Backtests legados |

Menus de página removidos: "Operação Paper | Radar de Ativos | Gestor Global | Histórico
H2 v6" (Radar), "Operação Paper | Radar de Ativos | Gestor de Carteira |
Histórico H2 v6" (Carteira), "Visão Geral | Sala de Decisão | … | Radar de Ativos |
Gestor de Carteira" (Operação diária), "Análise Histórica → Operação Paper Trading"
(H2), "Dashboard | Logs" (Logs). As abas do H2 (`role="tablist"`) continuam:
são subnavegação local real, não menu global.

## 3. Rotas e deep links preservados

- As **18 rotas** continuam servidas (GET e HEAD), com os mesmos arquivos e APIs.
- Deep links testados no navegador: `/radar?run=radar-2026-10-09-recovery-01`
  (seletor de execução mantém o valor; recarregar mantém a URL);
  `/portfolio?run=…` (modo travado pela execução); `/portfolio?analysis=<id>`;
  `/paper#agentes`, `#supervisao`, `#sala`; `/#audit`, `/#wallets`;
  `/h2#provisional/audit`; `/portfolio#ai-proposal`.
- **`?run=`** é levado pelos links de Mercado e Carteira enquanto estiver na URL;
  os demais parâmetros (`analysis`, `tickers`, `session`, `mode`) continuam sob
  controle de cada página, sem interferência do shell.
- Histórico do navegador: trocar de seção por hash e voltar atualiza a área e a
  seção destacadas (teste "history:hash_navigation_and_back").
- Nenhum endpoint `/api/*`, identificador científico ou campo de registro mudou.

## 4. Divergências em relação ao blueprint V7.6.1 (e por quê)

| Blueprint | Implementado | Motivo |
|---|---|---|
| Mercado › Ativos e indicadores | Mercado tem só o Radar; o cartão "Explorar o mercado" abre os **Backtests legados** (indicadores por ativo, 2016–2025), listados em Pesquisa | a única tela com gráficos de indicadores por ativo é a legada; uma página de ativo nova é escopo do UX-M4 |
| Auditoria como página própria | a área aponta para `/#audit` (seção do Início) e para `/logs` | página dedicada é escopo do UX-M7; o link de área já existe e não muda quando ela for criada |
| Catálogo de agentes em Pesquisa | listado em Pesquisa, mas fisicamente em `/paper#agentes` | mover a vista exigiria mexer na estrutura do `/paper` (UX-M6) |
| Selo "Ajuda" como área | botão "Ajuda" persistente no shell + "?" em cada termo | conforme o pedido: acesso global sem sétima seção |
| Pesquisa › Evidências e Metodologia | não criadas | páginas novas que leem `docs/evidence` são escopo do UX-M6 |

## 5. Página inicial reformulada

Estrutura (`dashboard/platform.html`, `platform.js`, `platform.css`):

| Bloco | Conteúdo | Fonte |
|---|---|---|
| Apresentação | nome, descrição pedida, "Laboratório de pesquisa · sistemas multiagentes"; três garantias: **nenhuma ordem real**, **custos sob controle (¤ + confirmação)**, **resultados auditáveis**; cada uma com "?" | texto fixo |
| Explorar o laboratório | seis tarefas com destino real: Explorar o mercado (`/legacy`), Consultar o Radar (`/radar?run=`), Analisar uma carteira (`/portfolio?run=#global-workflow`), Acompanhar a operação paper (`/paper#visao`), Consultar pesquisas (`/h2`), Auditar resultados (`/#audit`); cada uma com o selo da natureza (somente leitura, consultivo, paper prospectivo) | links reais; `?run=` vindo da API |
| Estado do laboratório | Radar oficial (execução, estado, sessão, pareceres oficiais); Gestor Global (inferências reais por estado selado: V2 validada, V1 rejeitada e encerrada; demonstrações sintéticas contadas à parte); Operação diária (decisão registrada, sessão e abertura-alvo, número de carteiras); Integridade (hashes conferem) | `GET /api/platform/overview` (somente leitura); campo ausente → selo "Indisponível" |
| Como funciona | fluxo Dados → Analistas → Consenso → Risk → Gestor Global → **Validação** → Proposta consultiva, com "?"; alerta "decisões dos agentes não viram operações"; diferença Radar × Gestor Global × Operação paper | texto fixo, coerente com as erratas V7.6.1 |
| Painéis operacionais (mantidos) | atenção do próximo pregão, cinco carteiras virtuais, registros/integridade/processos | mesmos ids e mesma lógica (`#readiness`, `#wallets`, `#audit`) |

Garantias da implementação:

- Nenhum botão pago no Início; o único botão é "Atualizar" (consulta).
- Não há status inventado: o estado vem da API; a existência de arquivo não é
  tratada como execução ativa; "experimentos em andamento" não é exibido porque
  não há fonte de verdade para isso.
- "Tratamento encerrado" (V1) e "V2 somente pelo CLI" são fatos do protocolo
  V7.6, ditos como tais no texto da métrica.
- Nada bloqueia a navegação: não há tutorial obrigatório.
