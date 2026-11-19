"""Busca sistemática no arXiv (API pública) para o Cap. 3 do TCC 2.

Uso: python arxiv_search.py <nome> <query> <saida.tsv>
Grava id, data, categorias, título e resumo de todos os resultados.
"""
import sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
API = "https://export.arxiv.org/api/query?"
PAGE = 500


def fetch(query, start):
    url = API + urllib.parse.urlencode(
        {"search_query": query, "start": start, "max_results": PAGE,
         "sortBy": "submittedDate", "sortOrder": "ascending"})
    req = urllib.request.Request(url, headers={"User-Agent": "tcc-literature-search/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return ET.fromstring(r.read())
        except Exception as e:  # rede instável: tenta de novo
            print("retry", attempt, e, file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise SystemExit("falhou")


def clean(s):
    return " ".join((s or "").split())


name, query, out = sys.argv[1], sys.argv[2], sys.argv[3]
root = fetch(query, 0)
total = int(root.find("os:totalResults", NS).text)
print(f"{name}: totalResults={total}", file=sys.stderr)
rows, start = [], 0
while True:
    for e in root.findall("a:entry", NS):
        aid = e.find("a:id", NS).text.rsplit("/abs/", 1)[-1]
        cats = ",".join(c.get("term") for c in e.findall("a:category", NS))
        rows.append((aid, e.find("a:published", NS).text[:10], cats,
                     clean(e.find("a:title", NS).text), clean(e.find("a:summary", NS).text)))
    start += PAGE
    if start >= total:
        break
    time.sleep(3.5)  # limite de uso da API do arXiv
    root = fetch(query, start)
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("id\tdate\tcats\ttitle\tabstract\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(f"{name}: gravados {len(rows)} de {total}", file=sys.stderr)
