"""Confere a compilação da monografia contra os defeitos corrigidos no Lote 0.

Uso (depois de compilar em tcc2/): python scripts/check_build.py [diretorio_do_build]
Falha (código 1) se o log ou os auxiliares mostrarem: hifenização sem padrões do
português, caixa estourando a margem, níveis de marcador pulados (\\paragraph
numerado), referência ou citação indefinida, lista de acrônimos vazia ou entrada
"x.y.0.z" no sumário.
"""
import re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # console do Windows não é UTF-8 por padrão
build = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
log = (build / "main.log").read_text(encoding="utf-8", errors="replace")
toc = (build / "main.toc").read_text(encoding="utf-8", errors="replace")
acr = build / "main.acr"

checks = {
    "hifenização sem padrões do português": "No hyphenation patterns were preloaded" in log,
    "caixa estourando a margem (Overfull \\hbox)": "Overfull \\hbox" in log,
    "nível de marcador pulado (hyperref)": "between bookmark levels is greater" in log,
    "referência ou citação indefinida": bool(re.search(r"undefined on input|There were undefined", log)),
    "lista de acrônimos vazia": not acr.exists() or "glossentry" not in acr.read_text(encoding="utf-8", errors="replace"),
    "entrada x.y.0.z no sumário": bool(re.search(r"\\numberline \{\d+\.\d+\.0", toc)),
}
falhas = [nome for nome, falhou in checks.items() if falhou]
for nome, falhou in checks.items():
    print(("FALHA " if falhou else "ok    ") + nome)
for linha in re.findall(r"Overfull \\hbox \([^)]*\) in paragraph at lines [\d-]+", log):
    print("      ", linha)
sys.exit(1 if falhas else 0)
