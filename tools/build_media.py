#!/usr/bin/env python3
"""Builds assets/media and assets/press from the Steam store, the clip folders and the press kits. --force rebuilds everything."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
OUT = ROOT / "assets" / "media"
HOME = Path.home()

VENA_CLIPS = Path(os.environ.get("VENA_CLIPS", "/mnt/nvme/09_ShortClips"))
VENA_LOGOS_ZIP = Path(os.environ.get(
    "VENA_LOGOS_ZIP", HOME / "Downloads/03_Logos-20260928T135409Z-1-001.zip"))
FDR_CLIPS = Path(os.environ.get("FDR_CLIPS", HOME / "fish-dont-return-clips"))
FDR_MARKETING = Path(os.environ.get("FDR_MARKETING", HOME / "fish-dont-return/marketing"))

VENA_APP = 4165740
FDR_APP = 5270480
STEAM_CDN = "https://shared.akamai.steamstatic.com/store_item_assets/"

CARD_SIZE = (720, 1280)
CLIP_SIZE = (540, 960)
HERO_WIDTHS = (1280, 1920, 2880)
SHOT_WIDTHS = (960, 1920)
OG_SIZE = (1200, 630)
AVIF_QUALITY = 62
JPEG_QUALITY = 84


@dataclass(frozen=True)
class Clip:
    name: str
    source: Path
    start: float
    length: float
    size: tuple[int, int]
    fps: int
    crf: int


CLIPS = (
    Clip("vena/card", VENA_CLIPS / "main_menu_map.mp4", 0.0, 8.0, CARD_SIZE, 60, 30),
    Clip("vena/clip-place", VENA_CLIPS / "satisfying_placements.mp4", 0.0, 3.5, CLIP_SIZE, 30, 28),
    Clip("vena/clip-dice", VENA_CLIPS / "roll_dice_shop.mp4", 0.0, 5.0, CLIP_SIZE, 30, 28),
    Clip("vena/clip-perk", VENA_CLIPS / "perk_selection.mp4", 0.6, 2.4, CLIP_SIZE, 30, 28),
    Clip("fdr/card", FDR_CLIPS / "wreck_searchlight.mp4", 2.0, 10.0, CARD_SIZE, 60, 30),
    Clip("fdr/clip-program", FDR_CLIPS / "program_coins.mp4", 0.0, 11.0, CLIP_SIZE, 30, 28),
    Clip("fdr/clip-lionfish", FDR_CLIPS / "lionfish_ram.mp4", 0.0, 14.0, CLIP_SIZE, 30, 28),
    Clip("fdr/clip-veil", FDR_CLIPS / "veil_descent.mp4", 0.0, 11.0, CLIP_SIZE, 30, 28),
)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def fresh(target: Path, force: bool) -> bool:
    return force or not target.exists()


def fetch(url: str, target: Path) -> Path:
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "studio-site-build"})
    with urllib.request.urlopen(request) as response, open(target, "wb") as out:
        shutil.copyfileobj(response, out)
    return target


def steam_assets(app: int) -> dict:
    query = json.dumps({
        "ids": [{"appid": app}],
        "context": {"language": "english", "country_code": "AT"},
        "data_request": {"include_assets": True},
    })
    url = ("https://api.steampowered.com/IStoreBrowseService/GetItems/v1/?input_json="
           + urllib.parse.quote(query))
    path = fetch(url, CACHE / f"steam_{app}_assets.json")
    return json.loads(path.read_text())["response"]["store_items"][0]["assets"]


def steam_details(app: int) -> dict:
    url = f"https://store.steampowered.com/api/appdetails?appids={app}&l=english"
    path = fetch(url, CACHE / f"steam_{app}_details.json")
    return json.loads(path.read_text())[str(app)]["data"]


def steam_image(app: int, key: str) -> Path:
    assets = steam_assets(app)
    url = STEAM_CDN + assets["asset_url_format"].replace("${FILENAME}", assets[key])
    return fetch(url, CACHE / f"steam_{app}_{key}.jpg")


def save_avif_jpeg(image: Image.Image, stem: Path, jpeg: bool = True) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    rgb = image.convert("RGB")
    rgb.save(stem.with_suffix(".avif"), quality=AVIF_QUALITY, speed=4)
    if jpeg:
        rgb.save(stem.with_suffix(".jpg"), quality=JPEG_QUALITY, optimize=True, progressive=True)


def cover(image: Image.Image, size: tuple[int, int], focus_x: float = 0.5) -> Image.Image:
    w, h = size
    scale = max(w / image.width, h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)),
                           Image.Resampling.LANCZOS)
    left = round((resized.width - w) * focus_x)
    top = (resized.height - h) // 2
    return resized.crop((left, top, left + w, top + h))


def widths(image: Image.Image, stem: Path, sizes: tuple[int, ...]) -> None:
    for width in sizes:
        height = round(image.height * width / image.width)
        resized = image.resize((width, height), Image.Resampling.LANCZOS)
        save_avif_jpeg(resized, stem.with_name(f"{stem.name}-{width}"))


def encode_clip(clip: Clip, force: bool) -> None:
    target = OUT / f"{clip.name}.mp4"
    if not fresh(target, force):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    w, h = clip.size
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(clip.start), "-t", str(clip.length),
         "-i", str(clip.source), "-an",
         "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p", "-r", str(clip.fps),
         "-c:v", "libx264", "-preset", "slower", "-tune", "animation", "-crf", str(clip.crf),
         "-profile:v", "high", "-movflags", "+faststart", "-threads", "6", str(target)])
    frame = CACHE / f"{clip.name.replace('/', '_')}_first.png"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(target), "-frames:v", "1", str(frame)])
    save_avif_jpeg(Image.open(frame), target.with_suffix(""))


def build_trailer(force: bool) -> None:
    target = OUT / "vena" / "trailer.mp4"
    if not fresh(target, force):
        return
    movie = steam_details(VENA_APP)["movies"][0]
    master = movie["hls_h264"]
    run(["ffmpeg", "-v", "error", "-y", "-i", master, "-map", "0:v:0", "-map", "0:a:0",
         "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-crf", "27",
         "-maxrate", "2800k", "-bufsize", "5600k", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
         "-threads", "6", str(target)])
    frame = CACHE / "vena_trailer_frame.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", "6", "-i", str(target), "-frames:v", "1", str(frame)])
    save_avif_jpeg(Image.open(frame).resize((1920, 1080), Image.Resampling.LANCZOS),
                   OUT / "vena" / "trailer-poster")


def trimmed_logo(source: Path, target: Path, width: int) -> None:
    logo = Image.open(source).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    height = round(logo.height * width / logo.width)
    logo = logo.resize((width, height), Image.Resampling.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    logo.save(target.with_suffix(".avif"), quality=75, speed=4)
    logo.save(target.with_suffix(".webp"), quality=90, method=6)


def vena_logo_kit() -> Path:
    kit = CACHE / "vena_logos"
    if not kit.exists():
        with zipfile.ZipFile(VENA_LOGOS_ZIP) as archive:
            for member in archive.namelist():
                if member.endswith(".png") and "Capsule_Old" not in member:
                    archive.extract(member, kit)
    return kit / "03_Logos"


def build_images(force: bool) -> None:
    vena_hero = Image.open(steam_image(VENA_APP, "library_hero_2x"))
    fdr_hero = Image.open(steam_image(FDR_APP, "library_hero_2x"))
    if fresh(OUT / "vena" / "hero-1920.avif", force):
        widths(vena_hero, OUT / "vena" / "hero", HERO_WIDTHS)
    if fresh(OUT / "fdr" / "hero-1920.avif", force):
        widths(fdr_hero, OUT / "fdr" / "hero", HERO_WIDTHS)

    if fresh(OUT / "vena" / "logo.avif", force):
        trimmed_logo(vena_logo_kit() / "Bibliothekslogo.png", OUT / "vena" / "logo", 960)
    if fresh(OUT / "fdr" / "logo.avif", force):
        trimmed_logo(FDR_MARKETING / "steam/images/library/library_logo_1280.png",
                     OUT / "fdr" / "logo", 960)

    vena_shots = [fetch(s["path_full"], CACHE / f"vena_ss_{i:02d}.jpg")
                  for i, s in enumerate(steam_details(VENA_APP)["screenshots"], 1)]
    fdr_shots = sorted((FDR_MARKETING / "steam/images/screenshots").glob("*.jpg"))
    for game, shots in (("vena", vena_shots), ("fdr", fdr_shots)):
        for i, shot in enumerate(shots, 1):
            stem = OUT / game / "shots" / f"{i:02d}"
            if fresh(stem.with_name(f"{i:02d}-1920.avif"), force):
                widths(Image.open(shot), stem, SHOT_WIDTHS)

    for game, app in (("vena", VENA_APP), ("fdr", FDR_APP)):
        target = OUT / game / "capsule"
        if fresh(target.with_suffix(".avif"), force):
            save_avif_jpeg(Image.open(steam_image(app, "library_capsule_2x")), target)

    for game, app in (("vena", VENA_APP), ("fdr", FDR_APP)):
        target = OUT / game / "og"
        if fresh(target.with_suffix(".jpg"), force):
            capsule = Image.open(steam_image(app, "main_capsule_2x"))
            capsule.convert("RGB").resize(OG_SIZE, Image.Resampling.LANCZOS).save(
                target.with_suffix(".jpg"), quality=86, optimize=True)

    target = OUT / "site" / "og.jpg"
    if fresh(target, force):
        target.parent.mkdir(parents=True, exist_ok=True)
        half = (OG_SIZE[0] // 2, OG_SIZE[1])
        sheet = Image.new("RGB", OG_SIZE, (11, 11, 12))
        sheet.paste(cover(vena_hero, half, 0.8), (0, 0))
        sheet.paste(cover(fdr_hero, half, 0.4), (half[0], 0))
        sheet.save(target, quality=86, optimize=True)


def build_press(force: bool) -> None:
    press = ROOT / "assets" / "press"
    press.mkdir(parents=True, exist_ok=True)
    pdf = press / "fish-dont-return-press-kit.pdf"
    if fresh(pdf, force):
        shutil.copy(FDR_MARKETING / "press_kit/press_kit.pdf", pdf)

    kit = vena_logo_kit()
    bundles = {
        "vena-press-assets.zip": [
            (kit / "Bibliothekslogo.png", "logo/vena-logo.png"),
            (kit / "GameLogo1024x1024.png", "logo/vena-icon.png"),
            (steam_image(VENA_APP, "library_capsule_2x"), "art/library-capsule-600x900.jpg"),
            (steam_image(VENA_APP, "main_capsule_2x"), "art/main-capsule-1232x706.jpg"),
            (steam_image(VENA_APP, "header_2x"), "art/header-920x430.jpg"),
            (steam_image(VENA_APP, "library_hero_2x"), "art/library-hero-3840x1240.jpg"),
            *[(CACHE / f"vena_ss_{i:02d}.jpg", f"screenshots/vena-{i:02d}.jpg") for i in range(1, 11)],
        ],
        "fish-dont-return-press-assets.zip": [
            (FDR_MARKETING / "steam/images/library/library_logo_1280.png", "logo/fish-dont-return-logo.png"),
            (FDR_MARKETING / "steam/images/library/library_capsule_600x900.png", "art/library-capsule-600x900.png"),
            (FDR_MARKETING / "steam/images/store/main_capsule_1232x706.png", "art/main-capsule-1232x706.png"),
            (FDR_MARKETING / "steam/images/store/header_capsule_920x430.png", "art/header-920x430.png"),
            (FDR_MARKETING / "steam/images/library/library_hero_3840x1240.png", "art/library-hero-3840x1240.png"),
            *[(shot, f"screenshots/{shot.name}")
              for shot in sorted((FDR_MARKETING / "steam/images/screenshots").glob("*.jpg"))],
        ],
    }
    for name, files in bundles.items():
        target = press / name
        if not fresh(target, force):
            continue
        with zipfile.ZipFile(target, "w", zipfile.ZIP_STORED) as archive:
            for source, arcname in files:
                archive.write(source, arcname)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild files that already exist")
    args = parser.parse_args()
    CACHE.mkdir(exist_ok=True)
    for clip in CLIPS:
        encode_clip(clip, args.force)
    build_images(args.force)
    build_trailer(args.force)
    build_press(args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
