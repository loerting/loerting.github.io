#!/usr/bin/env python3
"""Builds assets/media and assets/press from the Steam store, the clip folders and the press kits. --force rebuilds everything."""
from __future__ import annotations

import argparse
import filecmp
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
WTB_KIT_ZIP = Path(os.environ.get(
    "WTB_KIT_ZIP", HOME / "Downloads/Press Kit-20260928T155139Z-1-001.zip"))
WTB_KIT = CACHE / "wtb_kit" / "Press Kit"
WTB_TRAILER = WTB_KIT / "Trailers" / "Gameplay Trailer.mp4"

VENA_APP = 4165740
FDR_APP = 5270480
WTB_APP = 4832970
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
    crop_x: int | None = None


CLIPS = (
    Clip("vena/card", VENA_CLIPS / "main_menu_map.mp4", 0.0, 8.0, CARD_SIZE, 60, 30),
    Clip("vena/clip-place", VENA_CLIPS / "satisfying_placements.mp4", 0.0, 3.5, CLIP_SIZE, 30, 28),
    Clip("vena/clip-dice", VENA_CLIPS / "roll_dice_shop.mp4", 0.0, 5.0, CLIP_SIZE, 30, 28),
    Clip("vena/clip-perk", VENA_CLIPS / "perk_selection.mp4", 0.6, 2.4, CLIP_SIZE, 30, 28),
    Clip("fdr/card", FDR_CLIPS / "wreck_searchlight.mp4", 2.0, 10.0, CARD_SIZE, 60, 30),
    Clip("fdr/clip-program", FDR_CLIPS / "program_coins.mp4", 0.0, 11.0, CLIP_SIZE, 30, 28),
    Clip("fdr/clip-lionfish", FDR_CLIPS / "lionfish_ram.mp4", 0.0, 14.0, CLIP_SIZE, 30, 28),
    Clip("fdr/clip-veil", FDR_CLIPS / "veil_descent.mp4", 0.0, 11.0, CLIP_SIZE, 30, 28),
    Clip("wtb/card", WTB_TRAILER, 86.5, 8.0, CARD_SIZE, 60, 30, 875),
    Clip("wtb/clip-upgrades", WTB_TRAILER, 37.8, 5.5, CLIP_SIZE, 30, 28, 480),
    Clip("wtb/clip-smash", WTB_TRAILER, 62.0, 6.0, CLIP_SIZE, 30, 28, 875),
    Clip("wtb/clip-prestige", WTB_TRAILER, 26.8, 7.0, CLIP_SIZE, 30, 28, 680),
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
    crop = "" if clip.crop_x is None else f"crop=ih*9/16:ih:{clip.crop_x}:0,"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(clip.start), "-t", str(clip.length),
         "-i", str(clip.source), "-an",
         "-vf", f"{crop}scale={w}:{h}:flags=lanczos,format=yuv420p", "-r", str(clip.fps),
         "-c:v", "libx264", "-preset", "slower", "-tune", "animation", "-crf", str(clip.crf),
         "-profile:v", "high", "-movflags", "+faststart", "-threads", "6", str(target)])
    frame = CACHE / f"{clip.name.replace('/', '_')}_first.png"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(target), "-frames:v", "1", str(frame)])
    save_avif_jpeg(Image.open(frame), target.with_suffix(""))


def encode_trailer(source: str, target: Path, poster_at: float) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", source, "-map", "0:v:0", "-map", "0:a:0",
         "-vf", "scale=1920:1080:flags=lanczos", "-r", "30",
         "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-crf", "27",
         "-maxrate", "2800k", "-bufsize", "5600k", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
         "-threads", "6", str(target)])
    frame = CACHE / f"{target.parent.name}_trailer_frame.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(poster_at), "-i", str(target), "-frames:v", "1", str(frame)])
    save_avif_jpeg(Image.open(frame), target.with_name("trailer-poster"))


def build_trailers(force: bool) -> None:
    if fresh(OUT / "vena" / "trailer.mp4", force):
        encode_trailer(steam_details(VENA_APP)["movies"][0]["hls_h264"], OUT / "vena" / "trailer.mp4", 6)
    if fresh(OUT / "wtb" / "trailer.mp4", force):
        encode_trailer(str(WTB_KIT / "Trailers" / "Demo Trailer.mp4"), OUT / "wtb" / "trailer.mp4", 4)


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


def wtb_kit() -> Path:
    if not WTB_KIT.exists():
        with zipfile.ZipFile(WTB_KIT_ZIP) as archive:
            for member in archive.namelist():
                if "Ingame assets" not in member and not member.endswith(".psd"):
                    archive.extract(member, WTB_KIT.parent)
    return WTB_KIT


def build_images(force: bool) -> None:
    kit = wtb_kit()
    heroes = {
        "vena": Image.open(steam_image(VENA_APP, "library_hero_2x")),
        "fdr": Image.open(steam_image(FDR_APP, "library_hero_2x")),
        "wtb": Image.open(kit / "Capsule Art" / "HeldenkapselBibliothek.png"),
    }
    logos = {
        "vena": vena_logo_kit() / "Bibliothekslogo.png",
        "fdr": FDR_MARKETING / "steam/images/library/library_logo_1280.png",
        "wtb": kit / "Capsule Art" / "Bibliothekslogo.png",
    }
    shots = {
        "vena": [fetch(s["path_full"], CACHE / f"vena_ss_{i:02d}.jpg")
                 for i, s in enumerate(steam_details(VENA_APP)["screenshots"], 1)],
        "fdr": sorted((FDR_MARKETING / "steam/images/screenshots").glob("*.jpg")),
        "wtb": sorted((kit / "Screenshots").glob("*.jpg")),
    }
    capsules = {
        "vena": steam_image(VENA_APP, "library_capsule_2x"),
        "fdr": FDR_MARKETING / "steam/images/library/library_capsule_600x900.png",
        "wtb": kit / "Capsule Art" / "Bibliothekkapsel.png",
    }
    main_capsules = {
        "vena": steam_image(VENA_APP, "main_capsule_2x"),
        "fdr": FDR_MARKETING / "steam/images/store/main_capsule_1232x706.png",
        "wtb": kit / "Capsule Art" / "Hauptkapsel.png",
    }

    for game in heroes:
        if fresh(OUT / game / "hero-1920.avif", force):
            widths(heroes[game], OUT / game / "hero", HERO_WIDTHS)
        if fresh(OUT / game / "logo.avif", force):
            trimmed_logo(logos[game], OUT / game / "logo", 960)
        for i, shot in enumerate(shots[game], 1):
            stem = OUT / game / "shots" / f"{i:02d}"
            if fresh(stem.with_name(f"{i:02d}-1920.avif"), force):
                widths(Image.open(shot), stem, SHOT_WIDTHS)
        if fresh(OUT / game / "capsule.avif", force):
            save_avif_jpeg(Image.open(capsules[game]), OUT / game / "capsule")
        if fresh(OUT / game / "og.jpg", force):
            Image.open(main_capsules[game]).convert("RGB").resize(OG_SIZE, Image.Resampling.LANCZOS).save(
                OUT / game / "og.jpg", quality=86, optimize=True)

    target = OUT / "site" / "og.jpg"
    if fresh(target, force):
        target.parent.mkdir(parents=True, exist_ok=True)
        third = (OG_SIZE[0] // 3, OG_SIZE[1])
        sheet = Image.new("RGB", OG_SIZE, (11, 10, 12))
        for i, (game, focus) in enumerate((("vena", 0.8), ("wtb", 0.5), ("fdr", 0.4))):
            sheet.paste(cover(heroes[game], third, focus), (i * third[0], 0))
        sheet.save(target, quality=86, optimize=True)


def build_press(force: bool) -> None:
    press = ROOT / "assets" / "press"
    press.mkdir(parents=True, exist_ok=True)
    # Fish Don't Return's kit in English and German, copied again whenever it was rebuilt.
    for name, source in (("fish-dont-return-press-kit.pdf", "press_kit.pdf"),
                         ("fish-dont-return-press-kit-de.pdf", "press_kit_de.pdf")):
        pdf, kit = press / name, FDR_MARKETING / "press_kit" / source
        if fresh(pdf, force) or not filecmp.cmp(kit, pdf, shallow=False):
            shutil.copy(kit, pdf)

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
        "what-the-buck-press-assets.zip": [
            (WTB_KIT / "Capsule Art" / "Bibliothekslogo.png", "logo/what-the-buck-logo.png"),
            (WTB_KIT / "Capsule Art" / "SquareProfilePicture.png", "logo/what-the-buck-square.png"),
            (WTB_KIT / "Capsule Art" / "Bibliothekkapsel.png", "art/library-capsule-600x900.png"),
            (WTB_KIT / "Capsule Art" / "VertikaleKapsel.png", "art/vertical-capsule-748x896.png"),
            (WTB_KIT / "Capsule Art" / "Hauptkapsel.png", "art/main-capsule-1232x706.png"),
            (WTB_KIT / "Capsule Art" / "Titelbereichskapsel.png", "art/header-920x430.png"),
            (WTB_KIT / "Capsule Art" / "HeldenkapselBibliothek.png", "art/library-hero-3840x1240.png"),
            *[(shot, f"screenshots/what-the-buck-{i:02d}.jpg")
              for i, shot in enumerate(sorted((WTB_KIT / "Screenshots").glob("*.jpg")), 1)],
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
    wtb_kit()
    for clip in CLIPS:
        encode_clip(clip, args.force)
    build_images(args.force)
    build_trailers(args.force)
    build_press(args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
