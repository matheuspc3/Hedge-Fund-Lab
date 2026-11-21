"""Grifa nos PDFs das referências os trechos que sustentam cada citação do TCC.

Uso (na raiz do repositório):
    python tcc2/scripts/grifar_referencias.py tcc2/overleaf/referencias/grifos.jsonl

Requer PyMuPDF (`pip install pymupdf`), que NÃO é dependência do projeto: rode com um
ambiente à parte. Cada linha do .jsonl é um grifo:
    {"chave": "Lo2002", "pagina": 3, "trecho": "texto copiado do PDF", "nota": "Cap. 2, l. 140: ..."}
"pagina" (1-based) é opcional; sem ela, o trecho é procurado no documento inteiro.
O grifo leva a "nota" como comentário, para quem abrir o PDF saber qual frase do TCC ele
sustenta.

Os originais ficam em output/referencias-originais/ (ignorado pelo Git) e o PDF grifado
é sempre regerado a partir deles, então rodar de novo não duplica grifos. Se o original
faltar, ele é refeito a partir do PDF grifado, sem os grifos "TCC 2".
Sai com código 1 se algum trecho não for encontrado.
Com --teste, só procura os trechos e não grava nada.
"""
import json, re, sys, unicodedata
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REFS = REPO / "tcc2" / "overleaf" / "referencias"
ORIG = REPO / "output" / "referencias-originais"


def norm(palavra):
    # NFKC desfaz ligaturas tipográficas ("ﬁ" -> "fi") comuns em PDFs de editoras.
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFKC", palavra).lower())


def tokens(pg):
    """Palavras da página na ordem de leitura, juntando hífen de fim de linha."""
    out = []  # (palavra normalizada, [retângulos])
    ws = pg.get_text("words")  # x0, y0, x1, y1, palavra, bloco, linha, n
    i = 0
    while i < len(ws):
        w, rects = ws[i][4], [pymupdf.Rect(ws[i][:4])]
        while w.endswith("-") and i + 1 < len(ws) and ws[i + 1][5:7] != ws[i][5:7]:
            i += 1
            w, rects = w[:-1] + ws[i][4], rects + [pymupdf.Rect(ws[i][:4])]
        if norm(w):
            out.append((norm(w), rects))
        i += 1
    return out


def achar(toks, alvo):
    n = len(alvo)
    for i in range(len(toks) - n + 1):
        if all(toks[i + k][0] == alvo[k] for k in range(n)):
            return [r for _, rs in toks[i:i + n] for r in rs]
    return None


def grifar(doc, pagina, trecho, nota):
    # ponytail: casamento exato de palavras normalizadas, na ordem de leitura do PDF.
    # Trecho que cruza colunas ou páginas, ou PDF digitalizado sem texto, não casa;
    # nesses casos o grifo é feito à mão.
    trecho = re.sub(r"(\w)- (\w)", r"\1\2", trecho)  # hífen de fim de linha copiado do PDF
    alvo = [norm(w) for w in trecho.split() if norm(w)]
    paginas = [doc[pagina - 1]] if pagina else list(doc)
    for pg in paginas:
        rects = achar(tokens(pg), alvo)
        if rects:
            a = pg.add_highlight_annot(rects)
            a.set_info(content=nota, title="TCC 2")
            a.update()
            return "ok"
    return "NÃO ENCONTRADO"


sys.stdout.reconfigure(encoding="utf-8")  # console do Windows não é UTF-8 por padrão
teste = "--teste" in sys.argv
entradas = [json.loads(l) for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
ORIG.mkdir(parents=True, exist_ok=True)
falhas, docs = 0, {}
for e in entradas:
    chave = e["chave"]
    if chave not in docs:
        destino, original = REFS / f"{chave}.pdf", ORIG / f"{chave}.pdf"
        if not original.exists() and not teste:
            # Sem original (ex.: PDF grifado em outra máquina): refaz a partir do grifado,
            # tirando só os grifos deste script ("TCC 2"); grifos de terceiros ficam.
            # Lido da memória: no Windows, o arquivo aberto impede salvar o grifado por cima.
            limpo = pymupdf.open(stream=destino.read_bytes(), filetype="pdf")
            for pg in limpo:
                a = pg.first_annot
                while a:
                    a = pg.delete_annot(a) if a.info.get("title") == "TCC 2" else a.next
            limpo.save(original)
            limpo.close()
        docs[chave] = pymupdf.open(original if original.exists() else destino)
    status = grifar(docs[chave], e.get("pagina"), re.sub(r"\s+", " ", e["trecho"]).strip(), e["nota"])
    falhas += status == "NÃO ENCONTRADO"
    print(f"{chave:20s} p.{e.get('pagina', '-')!s:>4} {status:24s} {e['trecho'][:60]}")
for chave, doc in docs.items():
    if not teste:
        doc.save(REFS / f"{chave}.pdf", garbage=4, deflate=True)  # 4 junta objetos duplicados (fontes repetidas incham PDFs salvos pelo macOS)
print(f"{len(entradas)} grifos em {len(docs)} PDFs; {falhas} não encontrados")
sys.exit(1 if falhas else 0)
