# Qualificação offline — Premium V5

`HFL PREMIUM V5 — MULTIASSET PORTFOLIO ENGINE QUALIFIED OFFLINE`

[Arquitetura, contratos, política, limites e comandos](../../HFL_PREMIUM_V5_PORTFOLIO.md).
Sem execução prospectiva, ordem real ou chamada real ao Gemini.

Implementação registrada no commit local `f76eaa3`. Após esse commit, a checagem
original `run_h2_v6_forward.identity(clean=True)` passou com árvore Git limpa,
manifesto científico intacto e cadeia sintética de 22 eventos verificada.
O commit seguinte registra essa qualificação; nenhum push foi realizado.

| Evidência | Conteúdo |
|---|---|
| `verification.json` | Preservação dos 10.922 arquivos, manifesto original, carteira final, cadeia e SHA do arquivo ZIP |
| `preservation_baseline.json` | Inventário anterior ao novo motor: H2, Forward, supervisão, benchmarks, Radar e evidências V4 |
| `offline_tests.txt` | 29 checks unittest, todos offline, 42,952 s |
| `regression_final.txt` | 167 testes passaram em 133,82 s; regressões H2, supervisão, Radar, HTTP, Gemini mock e B3 |
| `regression_tests.txt` | Tentativa inicial no sandbox Windows: WinError 5 no diretório temporário pytest; a execução final foi autorizada fora do sandbox |
| `demo_generation.txt` | Geração explícita: cadeia de 22 eventos íntegra |
| `synthetic_demo.zip` | Todos os eventos, snapshot, propostas, validações, aprovações e demo A–E da carteira sintética |
| `chrome_checks.json` | Fluxo visual no Chrome, seis cenários aprovados, caso E bloqueado, sem console errors/warnings e sem overflow da página |
| `portfolio-1440.jpg` | Captura final: patrimônio, caixa, alocação e risco, 1440×1000 |
| `portfolio-preview.jpg` | Captura final na janela padrão, 1536×674 |
| `portfolio-420.jpg`, `portfolio-640.jpg` | Capturas responsivas, página com largura igual ao viewport útil |
| `invalid-proposal-420.jpg` | Pesos somando 120% rejeitados com explicação em português |
| `rotation-desktop.jpg` | Venda, recebível e compra explicitamente aguardando liquidação |
| `sale-receivable-desktop.jpg` | Cenário B: venda parcial e caixa disponível preservado |
| `portfolio-desktop.jpg` | Captura integral inicial para contexto, anterior ao refinamento dos textos de validação |

História verificada: navegador → GET local → replay/selos → resposta → gráficos,
pesos e operações. GETs de casos e simulações não modificam arquivos. Os testes
comparam hashes antes/depois e tornam qualquer chamada ao Gemini um erro.
Uma conexão loopback do teste HTTP é permitida; rede externa fica bloqueada.

Regressão final:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_multiasset_portfolio.py tests/test_multiasset_radar.py tests/test_h2_v6_forward.py tests/test_h2_v6_supervised.py tests/test_h2_premium_v3.py tests/test_h2_forward_dashboard.py tests/agents/test_gemini_client.py tests/pipeline/test_b3_official.py --basetemp=data/portfolio/regression-final-v5
```

O ZIP é uma evidência sintética para inspeção. Preserva `demo-qualified-v5/` como
identidade; sua execução/reconstrução requer os mesmos bytes dos três módulos
registrados em INITIALIZED. Gerar outro exemplo usa outra pasta `demo-*`, sem
sobrescrever eventos, ordens ou autorizações existentes. Dados reais do Radar
e carteiras prospectivas não estão nesse ZIP.

Limitações prospectivas e escolhas financeiras pendentes estão documentadas no
guia. Taxa e limites numéricos são fixtures; replay à mesma marca não é modelo
de preenchimento real nem evidência de capacidade preditiva da IA.
