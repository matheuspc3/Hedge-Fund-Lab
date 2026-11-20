"""Compacta tcc2/overleaf/ para subir no Overleaf e confere que o pacote compila sozinho.

Uso (na raiz do repositório):
    python tcc2/scripts/export_overleaf.py                  # com os PDFs das referências
    python tcc2/scripts/export_overleaf.py --sem-referencias  # só o necessário para compilar
Saída: output/tcc2-overleaf.zip (output/ é ignorado pelo Git).

tcc2/overleaf/ já é o projeto do Overleaf; entram todos os arquivos dela, menos os
auxiliares da compilação (main.aux, main.log, main.pdf etc.), que o Overleaf regera.
Depois o pacote é extraído numa pasta temporária, compilado (pdflatex, bibtex,
pdflatex x2) e verificado por tcc2/scripts/check_build.py.
"""
import subprocess, sys, tempfile, zipfile
from pathlib import Path

TCC2 = Path(__file__).resolve().parents[1]
PROJETO = TCC2 / "overleaf"
OUT = TCC2.parent / "output" / "tcc2-overleaf.zip"
sem_refs = "--sem-referencias" in sys.argv


def entra(p):
    rel = p.relative_to(PROJETO)
    if rel.parts[0] == "referencias" and sem_refs:
        return False
    return not (len(rel.parts) == 1 and p.stem == "main" and p.suffix != ".tex")


def compilar(pasta):
    passos = [["pdflatex", "-interaction=nonstopmode", "main.tex"], ["bibtex", "main"],
              ["pdflatex", "-interaction=nonstopmode", "main.tex"],
              ["pdflatex", "-interaction=nonstopmode", "main.tex"]]
    for cmd in passos:
        subprocess.run(cmd, cwd=pasta, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.run([sys.executable, str(TCC2 / "scripts" / "check_build.py"), str(pasta)]).returncode


lista = sorted(p for p in PROJETO.rglob("*") if p.is_file() and entra(p))
OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for p in lista:
        z.write(p, p.relative_to(PROJETO).as_posix())
print(f"{OUT} ({len(lista)} arquivos, {OUT.stat().st_size / 1e6:.1f} MB)")

with tempfile.TemporaryDirectory() as tmp:
    zipfile.ZipFile(OUT).extractall(tmp)
    sys.exit(compilar(Path(tmp)))
