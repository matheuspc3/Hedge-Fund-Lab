"""Separa os resultados do OpenAlex que entram na triagem.

Uso: python dedup_openalex.py <openalex.tsv> <arxiv.tsv> <saida_para_triagem.tsv>
Entram os trabalhos com fonte principal revisada (periódico, anais de congresso ou
série de livros) que não estão nos resultados do arXiv, comparando id arXiv e título
normalizado. Imprime a contagem de cada etapa.
"""
import re, sys, unicodedata

REVISADA = {"journal", "conference", "book series"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def read(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    head = lines[0].split("\t")
    return head, [dict(zip(head, l.split("\t"))) for l in lines[1:]]


_, oa = read(sys.argv[1])
_, ax = read(sys.argv[2])
ax_ids = {r["id"].split("v")[0] for r in ax}
ax_titles = {norm(r["title"]) for r in ax}

revisada = [r for r in oa if r["tipo_fonte"] in REVISADA]
novos, vistos = [], set()
for r in revisada:
    t = norm(r["titulo"])
    if r["arxiv"] in ax_ids or t in ax_titles or t in vistos:
        continue
    vistos.add(t)
    novos.append(r)

print(f"OpenAlex: {len(oa)}; fonte revisada: {len(revisada)}; "
      f"já no arXiv ou duplicados: {len(revisada) - len(novos)}; para triagem: {len(novos)}")
cols = ["id", "doi", "ano", "fonte", "titulo", "resumo"]
with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as f:
    f.write("\t".join(cols) + "\n")
    for r in novos:
        f.write("\t".join(r[c] for c in cols) + "\n")
