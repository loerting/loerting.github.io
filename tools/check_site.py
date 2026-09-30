#!/usr/bin/env python3
"""Checks links, anchors, images and copy before publishing. --external also requests outside links."""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from de import KEEP
SKIP_DIRS = {".git", ".cache", ".playwright", ".playwright-cli", "tools"}
URL_ATTRS = {"href", "src", "poster", "data-src"}
BANNED_TEXT = {"—": "em-dash", "–": "en-dash", "...": "three dots (use …)"}
EMAIL = re.compile(r"mailto:|[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)
# A download's label next to its link, as "PDF, 6.9 MB" or "ZIP, 10,4 MB".
DOWNLOAD = re.compile(r'<a href="([^"]+\.(?:pdf|zip))">[^<]*<span>(?:PDF|ZIP), ([\d.,]+) MB</span>')
BANNED_CSS = {"transition: all": "transition: all", "outline: none": "outline: none"}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []
        self.ids: set[str] = set()
        self.images: list[dict[str, str | None]] = []
        self.text: list[str] = []
        self.strings: set[str] = set()
        self.has_title = False
        self.lang = ""
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "html":
            self.lang = a.get("lang") or ""
        for name in ("alt", "aria-label", "title"):
            if a.get(name):
                self.strings.add(" ".join(a[name].split()))
        if tag == "meta" and a.get("content") and (a.get("name") == "description" or a.get("property") in ("og:title", "og:description")):
            self.strings.add(a["content"])
        if tag == "title":
            self.has_title = True
        if "id" in a and a["id"]:
            self.ids.add(a["id"])
        for name in URL_ATTRS:
            if a.get(name):
                self.urls.append(a[name])
        if a.get("srcset"):
            self.urls += [part.strip().split(" ")[0] for part in a["srcset"].split(",")]
        if tag == "img":
            self.images.append(a)
        if tag == "use" and a.get("href"):
            self.urls.append(a["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.text.append(data)
            clean = " ".join(data.split())
            if re.search(r"[A-Za-z]", clean):
                self.strings.add(clean)


def pages() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.html") if not SKIP_DIRS & set(p.relative_to(ROOT).parts))


def parse(path: Path) -> Page:
    page = Page()
    page.feed(path.read_text(encoding="utf-8"))
    return page


def resolve(page_path: Path, url: str) -> Path:
    path = urlparse(url).path
    base = ROOT if path.startswith("/") else page_path.parent
    target = (base / path.lstrip("/")).resolve()
    return target / "index.html" if url.endswith("/") or target.is_dir() else target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--external", action="store_true")
    args = parser.parse_args()

    problems: list[str] = []
    parsed = {path: parse(path) for path in pages()}
    external: set[str] = set()

    for path, page in parsed.items():
        name = path.relative_to(ROOT)
        if not page.lang:
            problems.append(f"{name}: <html> has no lang")
        if not page.has_title:
            problems.append(f"{name}: no <title>")
        for url in page.urls:
            if url.startswith(("mailto:", "data:")) or url == "":
                continue
            if url.startswith(("http://", "https://")):
                external.add(url)
                continue
            clean, fragment = urldefrag(url)
            target = path if clean == "" else resolve(path, clean)
            if not target.exists():
                problems.append(f"{name}: missing {url}")
                continue
            if fragment and target.suffix == ".html":
                ids = parsed[target].ids if target in parsed else parse(target).ids
                if fragment not in ids:
                    problems.append(f"{name}: no #{fragment} in {target.relative_to(ROOT)}")
        for img in page.images:
            label = img.get("src") or "?"
            if img.get("alt") is None:
                problems.append(f"{name}: img without alt {label}")
            if not (img.get("width") and img.get("height")):
                problems.append(f"{name}: img without width/height {label}")
        for url, label in DOWNLOAD.findall(path.read_text(encoding="utf-8")):
            target = resolve(path, url)
            if target.exists() and float(label.replace(",", ".")) != round(target.stat().st_size / 1e6, 1):
                problems.append(f"{name}: {url} is {target.stat().st_size / 1e6:.1f} MB, labelled {label} MB")
        if EMAIL.search(path.read_text(encoding="utf-8")):
            problems.append(f"{name}: plain email address or mailto in the HTML")
        text = "".join(page.text)
        for char, label in BANNED_TEXT.items():
            if char in text:
                problems.append(f"{name}: {label} in visible text")

    for path, page in parsed.items():
        name = path.relative_to(ROOT)
        if name.parts[0] != "de":
            continue
        english = ROOT.joinpath(*name.parts[1:])
        if page.lang != "de":
            problems.append(f"{name}: lang is not de")
        if english not in parsed:
            problems.append(f"{name}: no English page at {english.relative_to(ROOT)}")
            continue
        for text in sorted((page.strings & parsed[english].strings) - KEEP):
            problems.append(f"{name}: not translated: {text[:80]}")

    for css in (ROOT / "assets").rglob("*.css"):
        source = css.read_text(encoding="utf-8")
        for line_no, line in enumerate(source.splitlines(), 1):
            for pattern, label in BANNED_CSS.items():
                if pattern in line:
                    problems.append(f"{css.relative_to(ROOT)}:{line_no}: {label}")

    if args.external:
        for url in sorted(external):
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 studio-site-check"})
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    if response.status >= 400:
                        problems.append(f"external {response.status}: {url}")
            except (urllib.error.URLError, TimeoutError) as error:
                problems.append(f"external failed: {url} ({error})")

    for problem in problems:
        print(problem)
    checked = sum(len(p.urls) for p in parsed.values())
    print(f"{len(parsed)} pages, {checked} references, {len(external)} external, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
