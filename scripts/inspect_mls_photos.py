#!/usr/bin/env python3
"""Download MLS thumbnails and seed an inventory of possible aerial/backyard photos.

This does not grant reuse rights. It only creates a research inventory so candidates
can be reviewed and licensed/cleared later.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from PIL import Image, ImageDraw, ImageFont, ImageStat

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PHOTOS = DATA / "mls_photos"
SHEETS = DATA / "mls_contact_sheets"
INVENTORY = DATA / "mls_photo_inventory"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; tubs-research/0.1)"})


def thumb_url(url: str) -> str:
    return url if "thumbnail" in url else f"{url}&thumbnail"


def photo_name(url: str, idx: int) -> str:
    qs = parse_qs(urlparse(url).query)
    name = (qs.get("name") or [f"photo_{idx:02d}"])[0]
    return f"{idx:02d}_{name.replace('.', '_')}.jpg"


def safe_text(value: object) -> str:
    return "" if value is None else str(value)


def load_font(size: int = 15) -> ImageFont.ImageFont:
    for name in ["arial.ttf", "calibri.ttf", "segoeui.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def download(url: str, path: Path, delay: float) -> bool:
    if path.exists() and path.stat().st_size > 1000:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    r = SESSION.get(thumb_url(url), timeout=30)
    if r.status_code == 200 and r.headers.get("content-type", "").startswith("image") and len(r.content) > 1000:
        path.write_bytes(r.content)
        time.sleep(delay)
        return True
    time.sleep(delay)
    return False


def image_metrics(path: Path) -> dict:
    try:
        with Image.open(path) as img:
            img = img.convert("RGB").resize((160, 120), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            total = len(pixels)
            green = sum(1 for r, g, b in pixels if g > r * 1.08 and g > b * 1.03 and g > 55) / total
            blue = sum(1 for r, g, b in pixels if b > r * 1.12 and b > g * 1.03 and b > 65) / total
            bright = ImageStat.Stat(img.convert("L")).mean[0]
            contrast = ImageStat.Stat(img.convert("L")).stddev[0]
            # Research proxy: yards/drone/outdoor photos usually contain greenery/water and decent texture.
            outdoor_score = min(100, round(green * 95 + blue * 55 + contrast * 0.8))
            return {
                "green_ratio": round(green, 3),
                "blue_ratio": round(blue, 3),
                "brightness": round(bright, 1),
                "contrast": round(contrast, 1),
                "outdoor_candidate_score": outdoor_score,
            }
    except Exception:
        return {"green_ratio": "", "blue_ratio": "", "brightness": "", "contrast": "", "outdoor_candidate_score": 0}


def make_contact_sheet(listing: dict, photos: list[dict], thumb: int = 150, cols: int = 5) -> str:
    if not photos:
        return ""
    rows = (len(photos) + cols - 1) // cols
    header_h = 82
    footer_h = 24
    sheet = Image.new("RGB", (cols * thumb, header_h + rows * (thumb + 22) + footer_h), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(18)
    meta_font = load_font(13)
    draw.text((8, 8), f"MLS thumbnails — {listing.get('address')} ({listing.get('source_label')})", fill="black", font=title_font)
    draw.text((8, 34), f"Listing {listing.get('listing_id')} | research inventory only; verify image rights before reuse", fill="#333", font=meta_font)
    draw.text((8, 55), "Green outline = outdoor/backyard/aerial candidate proxy. Numbers are MLS photo indices.", fill="#333", font=meta_font)
    for i, photo in enumerate(photos):
        row, col = divmod(i, cols)
        x = col * thumb
        y = header_h + row * (thumb + 22)
        path = ROOT / photo["local_path"]
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                img.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
                ox = x + (thumb - img.width) // 2
                oy = y + (thumb - img.height) // 2
                sheet.paste(img, (ox, oy))
        except Exception:
            pass
        candidate = int(photo.get("outdoor_candidate_score") or 0) >= 35
        draw.rectangle((x, y, x + thumb - 1, y + thumb - 1), outline="#00aa00" if candidate else "#cccccc", width=3 if candidate else 1)
        draw.text((x + 4, y + thumb + 3), f"#{photo['photo_index']} score {photo.get('outdoor_candidate_score', 0)}", fill="black", font=meta_font)
    out = SHEETS / listing["folder"] / "mls_contact_sheet.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88, optimize=True)
    return str(out.relative_to(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listings", default=str(DATA / "listings.json"))
    parser.add_argument("--max-photos-per-listing", type=int, default=30)
    parser.add_argument("--limit-listings", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.03)
    args = parser.parse_args()

    listings = json.loads(Path(args.listings).read_text(encoding="utf-8"))
    if args.limit_listings:
        listings = listings[: args.limit_listings]

    photo_rows = []
    listing_rows = []
    downloaded = 0
    for li, listing in enumerate(listings, 1):
        urls = listing.get("mls_photo_urls", []) or []
        if args.max_photos_per_listing:
            urls = urls[: args.max_photos_per_listing]
        listing_photos = []
        for idx, url in enumerate(urls, 1):
            path = PHOTOS / listing["folder"] / photo_name(url, idx)
            ok = download(url, path, args.delay)
            if not ok:
                continue
            downloaded += 1
            metrics = image_metrics(path)
            row = {
                "source_label": listing.get("source_label", ""),
                "listing_id": listing.get("listing_id", ""),
                "address": listing.get("address", ""),
                "photo_index": idx,
                "local_path": str(path.relative_to(ROOT)),
                "source_url": url,
                "candidate_type": "possible_backyard_aerial_or_outdoor" if int(metrics["outdoor_candidate_score"] or 0) >= 35 else "unclassified",
                "reuse_rights": "unknown_research_only",
                "review_status": "needs_review",
                **metrics,
            }
            photo_rows.append(row)
            listing_photos.append(row)
        sheet = make_contact_sheet(listing, listing_photos)
        candidates = sum(1 for p in listing_photos if p["candidate_type"] != "unclassified")
        listing_rows.append({
            "source_label": listing.get("source_label", ""),
            "listing_id": listing.get("listing_id", ""),
            "address": listing.get("address", ""),
            "downloaded_mls_thumbnails": len(listing_photos),
            "possible_outdoor_backyard_aerial_candidates": candidates,
            "mls_contact_sheet": sheet,
            "reuse_rights": "unknown_research_only",
            "notes": "Candidate score is a color/texture proxy; human or vision review still required.",
        })
        if li % 25 == 0:
            print(f"Processed {li}/{len(listings)} listings; thumbnails={downloaded}")

    INVENTORY.mkdir(parents=True, exist_ok=True)
    photo_csv = INVENTORY / "mls_photo_candidates.csv"
    listing_csv = INVENTORY / "mls_listing_summary.csv"
    if photo_rows:
        with photo_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(photo_rows[0].keys()))
            writer.writeheader()
            writer.writerows(photo_rows)
    if listing_rows:
        with listing_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(listing_rows[0].keys()))
            writer.writeheader()
            writer.writerows(listing_rows)
    (INVENTORY / "README.md").write_text(
        "# MLS photo research inventory\n\n"
        "Generated thumbnails/contact sheets are for internal research only. Reuse rights are unknown and must be verified before marketing use.\n\n"
        "Candidate scoring is only a rough color/texture proxy for outdoor/backyard/aerial-looking images; it is not a final classification.\n",
        encoding="utf-8",
    )
    print(f"Downloaded/verified {downloaded} MLS thumbnails")
    print(f"Photo inventory: {photo_csv.relative_to(ROOT)}")
    print(f"Listing summary: {listing_csv.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
