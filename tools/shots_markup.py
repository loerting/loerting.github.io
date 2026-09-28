#!/usr/bin/env python3
"""Prints the screenshot grid for a game page: tools/shots_markup.py vena alts.txt"""
import sys

game, alts_file = sys.argv[1], sys.argv[2]
alts = [line.strip() for line in open(alts_file, encoding="utf-8") if line.strip()]
base = f"../assets/media/{game}/shots"
rows = []
for i, alt in enumerate(alts, 1):
    n = f"{i:02d}"
    big = i == 1
    width, height = (1920, 1080) if big else (960, 540)
    sizes = "(max-width: 720px) 100vw, 50vw" if big else "(max-width: 720px) 50vw, 25vw"
    avif = f"{base}/{n}-960.avif 960w, {base}/{n}-1920.avif 1920w" if big else f"{base}/{n}-960.avif"
    jpg = f"{base}/{n}-1920.jpg" if big else f"{base}/{n}-960.jpg"
    hidden = " hidden" if i > 5 else ""
    rows.append(
        f'        <a href="{base}/{n}-1920.jpg" data-shot{hidden}><picture>'
        f'<source type="image/avif" srcset="{avif}" sizes="{sizes}">'
        f'<img src="{jpg}" alt="{alt}" width="{width}" height="{height}" loading="lazy">'
        f"</picture></a>")
print("\n".join(rows))
