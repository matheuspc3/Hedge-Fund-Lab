"""Check active documentation links and catalog coverage, offline and read-only.

Run from any directory: python -B scripts/check_docs.py
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
HUBS = (
    "INICIO.md",
    "README.md",
    "docs/README.md",
    "docs/ARQUITETURA.md",
    "docs/DIRECAO_DO_PROJETO.md",
    "docs/PILOTO_MULTIATIVOS_SPEC.md",
    "docs/ROADMAP.md",
    "docs/ESTADO_ATUAL.md",
    "docs/archive/README.md",
)


def main():
    errors, catalogs, count = [], {}, 0
    # ponytail: check inline Markdown file links in hubs, not anchors/reference links;
    # adopt a Markdown parser only if the navigation starts using those forms.
    for name in HUBS:
        path = ROOT / name
        catalogs[name] = {path.resolve()}
        if not path.is_file():
            errors.append(f"missing hub: {name}")
            continue
        text = re.sub(
            r"(?ms)^```.*?^```[^\n]*(?:\n|$)", "", path.read_text(encoding="utf-8")
        )
        for match in re.finditer(r"\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)\)", text):
            href = match[1].strip("<>")
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
                continue
            target = (path.parent / unquote(url.path)).resolve()
            count += 1
            catalogs[name].add(target)
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f"{name}: invalid destination {href}")

    for path in sorted((ROOT / "docs").glob("*.md")):
        if path.resolve() not in catalogs["docs/README.md"]:
            errors.append(f"uncataloged document: {path.name}")
    for path in sorted((ROOT / "docs/evidence").iterdir()):
        if path.is_dir() and not any(
            target == path.resolve() or target.is_relative_to(path.resolve())
            for target in catalogs["docs/README.md"]
        ):
            errors.append(f"uncataloged evidence package: {path.name}")

    if errors:
        print("\n".join(errors))
        return 1
    print(
        f"OK: {len(HUBS)} hubs, {count} local links; docs and evidence packages cataloged."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
