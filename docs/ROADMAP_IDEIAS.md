# 🗺️ Roadmap de Ideias & Backlog do Projeto (Hedge-Fund-Lab)

Este documento registra o planejamento das próximas fases, novas ideias de funcionalidades e a visão arquitetural do projeto para a defesa do TCC.

---

## 📌 1. Próximas Fases Prioritárias

### 🤖 Fase A: Comitê de Agentes de IA (LangGraph + LLM)
- [ ] **Módulo de Decisão Multiagente**:
  - **Agente Analista Técnico**: Analisa tendências, RSI, Bollinger Bands e SMA.
  - **Agente Gerenciador de Risco**: Avalia volatilidade, correlação entre ativos e limite de Max Drawdown.
  - **Agente Gestor de Portfólio (Master)**: Recebe os pareceres dos subagentes e toma a decisão final de alocação de carteira.
- [ ] **Interface Abstrata de LLM**: Suporte configurável para modelos (OpenAI, Anthropic, Ollama local) via `pydantic-settings`.

---

### 📊 Fase B: Arena de Carteiras em Tempo Real & MetaTrader 5 (MT5)
- [ ] **Integração MetaTrader 5 (Python `MetaTrader5`)**:
  - Conexão com Conta Demo (Simulado Gratuito) em corretora brasileira (XP/BTG/Clear).
  - Leitura oficial de dados de fechamento às 17:05 BRT.
  - Envio e registro de ordens simuladas de compra/venda ao final do pregão.
- [ ] **Torneio/Arena Comparativa no Dashboard**:
  - Comparação diária entre 4 carteiras operando em paralelo:
    1. 🤖 **Carteira IA**: Liderada pelo Comitê Multiagente LLM.
    2. 📈 **Carteira Quant X**: Mínima Variância (Markowitz).
    3. ⚖️ **Carteira Quant Y**: Equal Weight (Pesos Iguais).
    4. 🏆 **Benchmark**: Buy & Hold (IBOV / Carteira Passiva).
- [ ] **Prevenção Rígida de Lookahead Bias**:
  - Tomada de decisão executada estritamente entre 18:00 e 22:00 BRT com dados disponíveis até às 17:05 BRT para agir no dia seguinte.

---

### ⚡ Fase C: Extrator Secundário para Cotações Pós-Fechamento (BRAPI / MT5)
- [ ] **Módulo BRAPI (`brapi.dev`)**:
  - Adicionar extrator alternativo ao `yfinance` para capturar a cotação oficial das ações da B3 imediatamente às 17:05 BRT (sem precisar aguardar a consolidação de madrugada do Yahoo Finance).
- [ ] **Seletor Dinâmico de Fonte de Dados**:
  - Alternar automaticamente: `yfinance` para séries históricas longas (2016–2025) e `BRAPI` / `MT5` para o pregão do dia atual.

---

## 💡 2. Ideias de Expansão Futura (Diferenciais para a Banca)

- [ ] **Análise de Sentimento de Notícias**:
  - Agente LLM especializado em ler manchetes financeiras e notícias corporativas do dia para ajustar o peso dos ativos no portfólio.
- [ ] **Mapeamento Realista de Custos de Transação**:
  - Incorporar taxas de B3 (emolumentos + taxa de liquidação) e modelo de slippage no envio de ordens.
- [ ] **Exportador de Relatórios para a Monografia**:
  - Script para gerar tabelas comparativas e gráficos formatados em PDF/LaTeX prontos para inserir no relatório do TCC.

---

## 📝 3. Histórico de Melhorias Já Concluídas ✅

- [x] **Arquitetura Padrão Ouro**: Migração para Poetry, Justfile, Ruff e Pyright.
- [x] **PostgreSQL 16 no Docker**: Persistência isolada na porta `5435` com restrição de unicidade `(ativo_id, data)`.
- [x] **ETL Incremental com Upsert**: Inserção sem duplicação de dados históricos (`ON CONFLICT DO NOTHING`).
- [x] **Suíte de Testes 100% Aprovada**: 245 testes automatizados (pytest).
- [x] **Comando Único `just run`**: ETL incremental + Recálculo dos Backtests + Dashboard Web.
