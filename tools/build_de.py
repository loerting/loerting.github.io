#!/usr/bin/env python3
"""Builds the German pages under de/ from the English ones and the pairs in tools/de.py."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from de import PAIRS

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://loertinggames.com/"
PAGES = {
    "index.html": "",
    "vena/index.html": "vena/",
    "what-the-buck/index.html": "what-the-buck/",
    "fish-dont-return/index.html": "fish-dont-return/",
    "press/index.html": "press/",
    "legal/index.html": "legal/",
    "vena/PRIVACY_POLICY.html": "vena/PRIVACY_POLICY",
}
URL_ATTR = re.compile(r'\b(href|src|poster|data-src|srcset)="([^"]*)"')
SHARED = re.compile(r"^((?:\.\./)*)(assets/|favicon\.svg)")


def deeper(value: str) -> str:
    parts = []
    for part in value.split(","):
        lead = part[: len(part) - len(part.lstrip())]
        parts.append(lead + SHARED.sub(r"../\1\2", part.lstrip()))
    return ",".join(parts)


def german(html: str, path: str) -> str:
    html = html.replace('<html lang="en">', '<html lang="de">', 1)
    html = URL_ATTR.sub(lambda m: f'{m.group(1)}="{deeper(m.group(2))}"', html)
    html = html.replace(f'<link rel="canonical" href="{BASE}{path}">', f'<link rel="canonical" href="{BASE}de/{path}">')
    html = html.replace(f'<meta property="og:url" content="{BASE}{path}">', f'<meta property="og:url" content="{BASE}de/{path}">')
    html = html.replace('<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="de_AT">')
    for english, text in sorted(PAIRS, key=lambda pair: len(pair[0]), reverse=True):
        html = html.replace(english, text)
    html = re.sub(r'href="/de/([^"]*)" hreflang="de" lang="de" data-lang="de" aria-label="Deutsch">DE<',
                  r'href="/\1" hreflang="en" lang="en" data-lang="en" aria-label="English">EN<', html)
    html = re.sub(r'href="/de/([^"]*)" hreflang="de" lang="de" data-lang="de">Deutsch<',
                  r'href="/\1" hreflang="en" lang="en" data-lang="en">English<', html)
    return html


def main() -> int:
    unused = {english for english, _ in PAIRS}
    for page, path in PAGES.items():
        source = (ROOT / page).read_text(encoding="utf-8")
        unused -= {english for english in unused if english in source}
        target = ROOT / "de" / page
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(german(source, path), encoding="utf-8")
    for english in sorted(unused):
        print(f"unused pair: {english[:90]}")
    print(f"{len(PAGES)} German pages written, {len(unused)} unused pairs")
    return 1 if unused else 0


if __name__ == "__main__":
    sys.exit(main())
