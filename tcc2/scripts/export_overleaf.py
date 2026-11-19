"""Gera o pacote do Overleaf a partir de tcc2/ e confere que ele compila sozinho.

Uso (na raiz do repositório): python tcc2/scripts/export_overleaf.py
Saída: output/tcc2-overleaf.zip (output/ é ignorado pelo Git).

Entram só os arquivos de que a compilação precisa: main.tex, classe, estilo
bibliográfico, references.bib, ficha.pdf (exemplo do modelo, até a biblioteca
emitir a definitiva), chapters/, figures/*.tex, as imagens citadas por
\\includegraphics e, se existir, a pasta referencias/ (PDFs das obras citadas).
Depois o pacote é extraído numa pasta temporária, compilado (pdflatex, bibtex,
makeglossaries, pdflatex x2) e verificado por scripts/check_build.py.
"""
import re, subprocess, sys, tempfile, zipfile
from pathlib import Path

TCC2 = Path(__file__).resolve().parents[1]
REPO = TCC2.parent
OUT = REPO / "output" / "tcc2-overleaf.zip"
FICHA = REPO / "docs" / "faculdade" / "monografia" / "ficha.pdf"


def arquivos():
    fixos = ["main.tex", "eic-bcc-tcc.cls", "apalike.bst", "references.bib"]
    lista = [TCC2 / f for f in fixos]
    lista += sorted((TCC2 / "chapters").rglob("*.tex"))
    lista += sorted((TCC2 / "figures").glob("*.tex"))
    tex = "\n".join(p.read_text(encoding="utf-8") for p in lista if p.suffix == ".tex")
    for img in sorted(set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex))):
        lista.append(TCC2 / img)
    if (TCC2 / "referencias").is_dir():
        lista += sorted(p for p in (TCC2 / "referencias").rglob("*") if p.is_file())
    faltando = [str(p) for p in lista if not p.exists()]
    if faltando:
        sys.exit("arquivos ausentes: " + ", ".join(faltando))
    return lista


def compilar(pasta):
    passos = [["pdflatex", "-interaction=nonstopmode", "main.tex"], ["bibtex", "main"],
              ["pdflatex", "-interaction=nonstopmode", "main.tex"],
              ["pdflatex", "-interaction=nonstopmode", "main.tex"]]
    for cmd in passos:
        subprocess.run(cmd, cwd=pasta, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.run([sys.executable, str(TCC2 / "scripts" / "check_build.py"), str(pasta)]).returncode


lista = arquivos()
OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for p in lista:
        z.write(p, p.relative_to(TCC2).as_posix())
    z.write(FICHA, "ficha.pdf")
print(f"{OUT} ({len(lista) + 1} arquivos, {OUT.stat().st_size / 1e6:.1f} MB)")

with tempfile.TemporaryDirectory() as tmp:
    zipfile.ZipFile(OUT).extractall(tmp)
    sys.exit(compilar(Path(tmp)))
