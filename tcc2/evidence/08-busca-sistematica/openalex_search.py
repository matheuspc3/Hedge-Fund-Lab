"""Busca sistemática no OpenAlex (API pública) para o Cap. 3 do TCC 2.

Uso: python openalex_search.py <saida.tsv> <filtro_titulo_e_resumo> [<filtro_titulo>]
Os filtros são combinados com AND, a partir de 01/01/2023; o de título é opcional. Grava id OpenAlex,
DOI, id arXiv (quando houver), ano, tipo da fonte principal, nome da fonte, título e
resumo (reconstruído do índice invertido) de todos os resultados.
"""
import json, re, sys, time, urllib.parse, urllib.request

API = "https://api.openalex.org/works?"
FIELDS = "id,doi,display_name,publication_date,type,primary_location,locations,abstract_inverted_index"


def get(params):
    url = API + urllib.parse.urlencode(params, safe=":|,*")
    req = urllib.request.Request(url, headers={"User-Agent": "tcc-literature-search/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # rede instável: tenta de novo
            body = e.read()[:300] if hasattr(e, "read") else b""
            print("retry", attempt, e, body, file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise SystemExit("falhou")


def abstract(inv):
    if not inv:
        return ""
    pos = {i: w for w, idx in inv.items() for i in idx}
    return " ".join(pos[i] for i in sorted(pos))


def arxiv_id(work):
    for loc in work.get("locations") or []:
        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", loc.get("landing_page_url") or "")
        if m:
            return m.group(1)
    m = re.search(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", (work.get("doi") or "").lower())
    return m.group(1) if m else ""


def clean(s):
    return " ".join((s or "").replace("\t", " ").split())


out, ta = sys.argv[1], sys.argv[2]
ti = sys.argv[3] if len(sys.argv) > 3 else ""
flt = f"title_and_abstract.search:{ta}," + (f"title.search:{ti}," if ti else "") + "from_publication_date:2023-01-01"
# ponytail: paginação por número de página (sem chave de API o OpenAlex recusa
# cursor). Limite de 10.000 resultados; acima disso, usar chave e cursor.
rows, page, total = [], 1, None
while True:
    data = get({"filter": flt, "per-page": 200, "page": page, "select": FIELDS})
    total = data["meta"]["count"]
    for w in data["results"]:
        src = (w.get("primary_location") or {}).get("source") or {}
        rows.append((w["id"].rsplit("/", 1)[-1], (w.get("doi") or "").replace("https://doi.org/", ""),
                     arxiv_id(w), (w.get("publication_date") or "")[:4], src.get("type") or "",
                     clean(src.get("display_name")), clean(w.get("display_name")),
                     clean(abstract(w.get("abstract_inverted_index")))))
    if not data["results"] or len(rows) >= total:
        break
    page += 1
    time.sleep(1)
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("id\tdoi\tarxiv\tano\ttipo_fonte\tfonte\ttitulo\tresumo\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(f"totalResults={total} gravados={len(rows)}", file=sys.stderr)
