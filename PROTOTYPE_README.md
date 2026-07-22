# Hedge-fund-lab · Protótipo de Validação

Pipeline ETL + Indicadores Técnicos + Dashboard Web (HTML/CSS/JS)

## Estrutura

```
hedge-fund-lab/
├── src/
│   └── prototype/
│       └── fetch_data.py      # Pipeline: yfinance → indicadores → JSON
├── dashboard/
│   ├── index.html             # Dashboard (Chart.js, dark theme)
│   ├── style.css              # Design system CSS
│   ├── app.js                 # Lógica do dashboard
│   ├── server.py              # Servidor HTTP local
│   └── data.json              # Gerado por fetch_data.py
├── tests/
│   ├── conftest.py
│   └── __init__.py            # Testes dos indicadores (13+ testes)
├── PLAN_HEDGEFUND.md          # Plano completo do projeto
└── PROTOTYPE_README.md        # Este arquivo
```

## Como Executar

### 1. Instalar dependências

```bash
pip install yfinance pandas numpy hypothesis pytest pytest-cov
```

### 2. Gerar os dados + indicadores técnicos

```bash
cd hedge-fund-lab
python -m src.prototype.fetch_data
```

Isso baixa 10 anos de PETR4.SA e WEGE3.SA, calcula SMA 50/200, Bollinger Bands (k=2), RSI (14), MACD (12,26,9), e salva em `dashboard/data.json`.

### 3. Iniciar o dashboard

```bash
python dashboard/server.py
```

Abrir http://localhost:8080 no navegador.

### 4. Rodar os testes

```bash
pytest tests/ -v
```

Com cobertura:
```bash
pytest tests/ -v --cov=src.prototype
```

## Funcionalidades do Dashboard

- **Dropdown**: Alterna entre PETR4 e WEGE3
- **Resumo**: Último fechamento, SMA50, SMA200, tendência (ALTA/BAIXA), RSI, MACD
- **Estatísticas**: Sharpe Ratio, Volatilidade Anualizada, Max Drawdown
- **Gráfico 1**: Preço + SMA 50/200 + Bollinger Bands
- **Gráfico 2**: RSI com bandas de sobrecompra (70) e sobrevenda (30)
- **Gráfico 3**: MACD + Sinal + Histograma
- **Tabela**: Últimos 20 pregões
- **Filosofia**: Seção explicativa do projeto Hedge-fund-lab
- **Responsivo**: Adapta para mobile e desktop

## Critérios de Aceitação

| # | Critério | Verificação |
|---|---|---|
| 1 | Dados de 10 anos carregados | > 2500 registros por ativo |
| 2 | SMA 50/200 corretos | Testes unitários passam |
| 3 | Bollinger Bands (k=2) | Testes unitários passam |
| 4 | RSI entre 0 e 100 | Testes + dashboard |
| 5 | MACD + Sinal + Histograma | Dashboard mostra |
| 6 | Alternar PETR4/WEGE3 | Dropdown troca gráficos |
| 7 | Testes passam | `pytest tests/ -v --cov` ≥ 95% |

## Próximas Etapas (Plano Completo)

Ver `PLAN_HEDGEFUND.md` para o plano detalhado de 7 fases:

1. **Pipeline ETL** (Prefect + PostgreSQL)
2. **Indicadores + Benchmarks** (5 estratégias clássicas)
3. **Backtesting Engine** (loop, métricas, custos)
4. **Sistema Multiagente** (LangGraph + 3 agentes LLM)
5. **Experimento** (treino/validação/teste, walk-forward)
6. **Análise** (gráficos, tabelas, hipóteses)
7. **Escrita + Defesa** (TCC finalizado)
