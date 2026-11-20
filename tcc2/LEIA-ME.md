# tcc2/ — monografia do TCC 2

| Pasta | O que tem |
|---|---|
| `overleaf/` | O projeto LaTeX completo, exatamente como sobe para o Overleaf: `main.tex`, classe, estilo bibliográfico, `references.bib`, `ficha.pdf` (exemplo do modelo, até a biblioteca emitir a definitiva), `chapters/`, `figures/`, `images/` e `referencias/` (PDFs das obras citadas, grifados, com `INDICE.md` e `VERIFICACAO_CITACOES.md`). O `main.pdf` é versionado; os auxiliares da compilação são ignorados pelo Git. |
| `scripts/` | Geradores e verificações: tabelas e figuras do replay (`metricas_replay.py`, `bootstrap_replay.py`), checagem do build (`check_build.py`), pacote do Overleaf (`export_overleaf.py`), grifos das referências (`grifar_referencias.py`) e PDF do CDI (`cdi_pdf.py`). |
| `evidence/` | Material-fonte da escrita (cópias datadas de documentos, dados do replay, busca sistemática, CDI). Índice em `evidence/LEIA-ME.md`. |
| `agent-reports/` | Relatórios de apoio e de revisão. Não vão para o repositório oficial do TCC (`scripts/preparar_repo_professor.sh`). |
| `arquivo/` | Material do TCC 1 que não é mais usado: o modelo e o texto antigos (`tcc1/`) e a pasta de referências antiga (`referencia/`). |

## Compilar e conferir

```bash
cd tcc2/overleaf
pdflatex main && bibtex main && pdflatex main && pdflatex main
python ../scripts/check_build.py          # falha se voltar algum defeito de layout
```

## Subir para o Overleaf

Compacte a pasta `overleaf/` (ou rode `python tcc2/scripts/export_overleaf.py`, que gera
`output/tcc2-overleaf.zip` e confere que o pacote compila; `--sem-referencias` deixa os PDFs
das referências de fora) e use "New Project → Upload Project" no Overleaf.
