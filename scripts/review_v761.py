"""V7.6.1 offline review tools: UX inventory of the dashboard and a date-only check of
the out-of-sample sessions against the cached official COTAHIST.

Read-only. No provider, no network, no server start, nothing written under data/.
The calendar check reads only the date, market and ticker fields of records dated
inside the out-of-sample window; earlier records (H2 holdout included) are skipped on
the date prefix and never parsed for prices.

Usage (project root):
  python -B scripts/review_v761.py ux          # CONSULTA: dashboard inventory (JSON)
  python -B scripts/review_v761.py calendar    # CONSULTA: sessions vs COTAHIST dates
  python -B scripts/review_v761.py build       # GRAVA ux_inventory.json e calendar_check.json
"""

import argparse
import ast
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
OUT = ROOT / "docs/evidence/hfl_methodology_ux_review_v761"
V76 = ROOT / "docs/evidence/hfl_experimental_protocol_v76"
RECOVERY = ROOT / "data/radar/hfl_multiasset_v1_recovery_01"
TICKERS = ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3")
#: Terms the naming audit tracks (lower-case match on visible text and JS strings).
TERMS = (
    "paper",
    "portfolio",
    "gestor global",
    "radar",
    "risk",
    "proposta da ia",
    "contexto",
    "preflight",
    "snapshot",
    "replay",
    "claim",
    "journal",
    "consultar",
    "recuperar",
    "histórico h2",
    "simular",
    "executar",
    "proposta validada",
    "sala de decisão",
    "visão geral",
    "laboratório",
    "operação",
    "supervisão",
    "carteira",
    "gemini",
    "inferência",
)
#: Button intent from its visible label; anything unmatched is UNCLASSIFIED.
INTENTS = (
    (
        "PAID_INFERENCE",
        re.compile(
            r"execut|autorizar e|confirmar somente|solicitar proposta|gemini", re.I
        ),
    ),
    (
        "WRITE_OR_PREPARE",
        re.compile(r"prepar|sincroniz|atualizar dados|confirmar ação|adicionar", re.I),
    ),
    (
        "READ_ONLY",
        re.compile(
            r"consult|verific|atualizar visão|comparar|simular|recuperar|fechar|voltar|cancelar|limpar|preflight|vis[aã]o|decis|compara|multiagente|experimentos|auditoria|oficial|demonstra|provis|portf|análise",
            re.I,
        ),
    ),
)


class Page(HTMLParser):
    """Collects the structure a user meets on one HTML page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items, self.open, self.counts, self.scripts = [], None, Counter(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"].split("?")[0])
        if "title" in a:
            self.counts["title_attributes"] += 1
        for key in ("aria-describedby", "aria-label", "aria-live"):
            if key in a:
                self.counts[key] += 1
        if tag in (
            "details",
            "dialog",
            "input",
            "select",
            "textarea",
            "label",
            "table",
            "canvas",
            "abbr",
        ):
            self.counts[tag] += 1
        if a.get("role") == "dialog":
            self.counts["dialog"] += 1
        if a.get("role") == "tab":
            self.counts["tab"] += 1
        if re.search(r"\bhelp\b|\binfo-?tip\b", a.get("class", "")):
            self.counts["help_affordance"] += 1
        if tag == "section" and a.get("id"):
            self.items.append({"kind": "section", "id": a["id"], "text": ""})
        if tag in ("h1", "h2", "h3", "button", "summary", "a"):
            self.open = {
                "kind": tag,
                "id": a.get("id") or a.get("href") or "",
                "text": "",
            }

    def handle_data(self, data):
        if self.open:
            self.open["text"] += data

    def handle_endtag(self, tag):
        if self.open and tag == self.open["kind"]:
            self.open["text"] = " ".join(self.open["text"].split())
            self.items.append(self.open)
            self.open = None


def routes():
    """Pages served by dashboard/server.py, read from its source (never imported)."""
    source = (DASH / "server.py").read_text(encoding="utf-8")
    found = {}
    for paths, page in re.findall(
        r'if path (?:==|in) (\([^)]*\)|"[^"]*"):\s*\n\s*return self\._serve_static\("([^"]+)"\)',
        source,
    ):
        for p in re.findall(r'"([^"]+)"', paths):
            found[p] = page
    tree = ast.parse(source)
    assigned = {
        t.id: ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        for t in n.targets
        if getattr(t, "id", "") in ("SHELL_LINKS", "AREAS")
    }
    if "AREAS" in assigned:  # V7.6.2: (id, label, href, environment, sections)
        shell = {
            area: [(href, label), *sections]
            for area, label, href, _, sections in assigned["AREAS"]
        }
    else:  # V7.6.1 and earlier
        shell = assigned["SHELL_LINKS"]
    return found, shell


def intent(label):
    # "sem executar" / "sem Gemini" negate the paid words they contain.
    label = re.sub(r"\bsem (?:gemini|executar)\b", "", label, flags=re.I)
    return next((name for name, rx in INTENTS if rx.search(label)), "UNCLASSIFIED")


def ux_inventory():
    served, shell = routes()
    pages = {}
    for page in sorted(set(served.values())):
        parser = Page()
        html = (DASH / page).read_text(encoding="utf-8")
        parser.feed(html)
        js = "".join(
            (DASH / s.lstrip("/")).read_text(encoding="utf-8")
            for s in parser.scripts
            if (DASH / s.lstrip("/")).exists() and "vendor" not in s
        )
        text = (
            re.sub(r"<[^>]+>", " ", html)
            + " "
            + " ".join(
                re.findall(r"'([^']*)'|`([^`]*)`", js)
                and [x for t in re.findall(r"'([^']*)'|`([^`]*)`", js) for x in t]
            )
        ).lower()
        buttons = [i for i in parser.items if i["kind"] == "button"]
        pages[page] = {
            "routes": sorted(r for r, p in served.items() if p == page),
            "scripts": parser.scripts,
            "h1": [i["text"] for i in parser.items if i["kind"] == "h1"],
            "h2": [i["text"] for i in parser.items if i["kind"] == "h2"],
            "sections": [i["id"] for i in parser.items if i["kind"] == "section"],
            "buttons": [
                {"id": b["id"], "label": b["text"], "intent": intent(b["text"])}
                for b in buttons
            ],
            "dynamic_buttons_in_js": len(re.findall(r"<button", js)),
            "api_endpoints_in_js": sorted(
                set(re.findall(r"/api/[a-z0-9_-]+(?:/[a-z0-9_-]+)?", js))
            ),
            "counts": dict(sorted(parser.counts.items())),
            "help_in_js": len(
                re.findall(r'title=|aria-describedby|class="[^"]*help', js)
            ),
            "terms": {t: text.count(t) for t in TERMS if text.count(t)},
        }
    headings = Counter(h for p in pages.values() for h in set(p["h1"] + p["h2"]))
    links = [
        (group, href, label) for group, items in shell.items() for href, label in items
    ]
    labels = Counter(label for _, _, label in links)
    return {
        "identity": "HFL-V761-UX-INVENTORY",
        "pages": pages,
        "routes": dict(sorted(served.items())),
        "shell_groups": {
            g: [{"href": h, "label": lab} for h, lab in items]
            for g, items in shell.items()
        },
        "shell_links_total": len(links),
        "shell_targets_unserved": sorted(
            {h.split("#")[0] or "/" for _, h, _ in links} - set(served)
        ),
        "repeated_headings_across_pages": sorted(h for h, n in headings.items() if n > 1),
        "repeated_shell_labels": sorted(lab for lab, n in labels.items() if n > 1),
        "same_target_different_labels": sorted(
            {
                h: sorted({lab for _, hh, lab in links if hh == h})
                for _, h, _ in links
                if len({lab for _, hh, lab in links if hh == h}) > 1
            }.items()
        ),
        "help_affordances_total": sum(
            p["counts"].get("help_affordance", 0) + p["counts"].get("title_attributes", 0)
            for p in pages.values()
        ),
        "paid_buttons": sorted(
            f"{page}#{b['id']}: {b['label']}"
            for page, p in pages.items()
            for b in p["buttons"]
            if b["intent"] == "PAID_INFERENCE"
        ),
    }


def calendar_check():
    """Selected out-of-sample sessions against official COTAHIST dates (date-only read)."""
    sys.path[:0] = [str(ROOT)]
    from src.backtesting.b3_calendar import B3Calendar

    manifest = json.loads((V76 / "EXPERIMENT_MANIFEST.json").read_text(encoding="utf-8"))
    selected = json.loads((V76 / "BUDGET_PLAN.json").read_text(encoding="utf-8"))[
        "out_of_sample_sessions"
    ]
    start, end = (
        date.fromisoformat(d)
        for d in manifest["session_selection"]["retrospective_window"]
    )
    lo, hi = start.strftime("%Y%m%d").encode(), end.strftime("%Y%m%d").encode()
    archive_path = RECOVERY / "cotahist/COTAHIST_A2026.ZIP"
    recorded = json.loads(
        (RECOVERY / "analyses/PETR4/2026-10-09/result.json").read_text(encoding="utf-8")
    )["source"]["cotahist_sha256"]["COTAHIST_A2026.ZIP"]
    dates, last = {t: set() for t in TICKERS}, b""
    with zipfile.ZipFile(archive_path) as archive, archive.open(
        archive.namelist()[0]
    ) as raw:
        for line in raw:
            if line[:2] != b"01" or line[2:10] < lo:
                continue  # header/trailer or before the window: never parsed further
            last = max(last, line[2:10])
            ticker = line[12:24].strip().decode("latin-1")
            if (
                line[2:10] <= hi
                and line[10:12] == b"02"
                and line[24:27] == b"010"
                and ticker in dates
            ):
                dates[ticker].add(
                    date(int(line[2:6]), int(line[6:8]), int(line[8:10])).isoformat()
                )
    rule = [d.isoformat() for d in B3Calendar().sessions_between(start, end)]
    complete = sorted(set.intersection(*dates.values()))
    return {
        "identity": "HFL-V761-OOS-CALENDAR-CHECK",
        "source": archive_path.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "source_sha256_recorded_by_radar_inputs": recorded,
        "read_scope": f"records dated {start}..{end} (date, CODBDI 02, TPMERC 010, ticker); earlier records skipped by date prefix",
        "latest_date_found_from_window_start": f"{last[:4].decode()}-{last[4:6].decode()}-{last[6:8].decode()}"
        if last
        else None,
        "rule_calendar_sessions": len(rule),
        "cotahist_sessions_all_five": len(complete),
        "rule_sessions_missing_in_cotahist": sorted(set(rule) - set(complete)),
        "cotahist_sessions_not_in_rule": sorted(set(complete) - set(rule)),
        "selected_sessions": selected,
        "selected_missing_in_cotahist": sorted(set(selected) - set(complete)),
        "per_ticker_sessions": {t: len(v) for t, v in dates.items()},
    }


def write(name, data):
    (OUT / name).write_bytes(
        (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode()
    )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=("ux", "calendar", "build"))
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.command == "build":
        write("ux_inventory.json", ux_inventory())
        write("calendar_check.json", calendar_check())
        result = {"written": ["ux_inventory.json", "calendar_check.json"]}
    else:
        result = ux_inventory() if args.command == "ux" else calendar_check()
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
