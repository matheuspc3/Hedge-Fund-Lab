"""Confere quais trabalhos citados no Cap. 3 aparecem nos resultados da busca.

Uso: python match_cited.py references.bib cap3_keys.txt principal.tsv secundaria.tsv
Casa por identificador arXiv ou por título normalizado.
"""
import re, sys, unicodedata


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[{}\\]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


bib = open(sys.argv[1], encoding="utf-8").read()
entries = {}
for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
    key, body = m.group(1).strip(), m.group(2)
    t = re.search(r"title\s*=\s*\{(.*?)\},?\s*\n", body, re.S)
    e = re.search(r"eprint\s*=\s*\{([\d.]+)", body) or re.search(r"arXiv[.:/ ]*(\d{4}\.\d{4,5})", body)
    entries[key] = (norm(t.group(1)) if t else "", e.group(1) if e else None)

keys = [k.strip() for k in open(sys.argv[2], encoding="utf-8") if k.strip()]
results = {}
for path in sys.argv[3:]:
    rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")][1:]
    results[path] = rows

for key in keys:
    title, eid = entries.get(key, ("", None))
    hits = []
    for path, rows in results.items():
        for r in rows:
            rid = r[0].split("v")[0]
            if (eid and rid == eid) or (title and norm(r[3])[:60] == title[:60]):
                hits.append(path.rsplit("/", 1)[-1].replace(".tsv", ""))
    print(f"{key:20s} {','.join(sorted(set(hits))) or '-':22s} {title[:70]}")
