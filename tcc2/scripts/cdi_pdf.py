"""Gera tcc2/referencias/BCBCDI2026.pdf a partir da série do CDI baixada da API do Banco Central.

Uso (na raiz do repositório, com PyMuPDF instalado num ambiente à parte):
    python tcc2/scripts/cdi_pdf.py
Fonte: tcc2/evidence/09-cdi-periodo/cdi_sgs12_20260406_20261112.json (SGS, série 12).
O PDF traz a origem, a data de acesso, a taxa diária de cada pregão e o acumulado, para
que a citação "CDI acumulado de 8,33\\%" possa ser conferida e grifada.
"""
import json
from pathlib import Path

import pymupdf

TCC2 = Path(__file__).resolve().parents[1]
dados = json.loads((TCC2 / "evidence/09-cdi-periodo/cdi_sgs12_20260406_20261112.json").read_text(encoding="utf-8"))
fator = 1.0
linhas = []
for r in dados:
    fator *= 1 + float(r["valor"]) / 100
    linhas.append(f"{r['data']}   {float(r['valor']):.6f}   {(fator - 1) * 100:7.4f}")
acum = (fator - 1) * 100
assert len(dados) == 153 and round(acum, 2) == 8.33, (len(dados), acum)

cab = [
    "Banco Central do Brasil - Sistema Gerenciador de Series Temporais (SGS)",
    "Serie 12: Taxa de juros - CDI (% ao dia)",
    "Fonte: https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados",
    "Consulta: dataInicial=06/04/2026, dataFinal=12/11/2026. Acesso em 19/11/2026.",
    f"Dias uteis no periodo: {len(dados)}. CDI acumulado no periodo: {acum:.2f}%.",
    "",
    "Data         Taxa (% a.d.)   Acumulado (%)",
]
doc = pymupdf.open()
por_pag = 50
blocos = [linhas[i:i + por_pag] for i in range(0, len(linhas), por_pag)]
for n, bloco in enumerate(blocos):
    pg = doc.new_page()
    texto = (cab if n == 0 else cab[-1:]) + bloco
    pg.insert_text((50, 60), "\n".join(texto), fontname="cour", fontsize=9)
doc.save(TCC2 / "referencias" / "BCBCDI2026.pdf")
print(f"{len(dados)} dias, acumulado {acum:.4f}%, {doc.page_count} páginas")
