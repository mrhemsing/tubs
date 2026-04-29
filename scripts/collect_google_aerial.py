#!/usr/bin/env python3
"""Collect Google Static Maps satellite previews as an alternate overhead source.

Requires GOOGLE_MAPS_API_KEY or --key. Uses the official Google Maps Static API,
not scraped Google tiles. Research output only; verify Google Maps Platform terms,
attribution, caching, and reuse rights before publishing/reusing imagery.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TRIAGE = DATA / "triage" / "property_candidate_triage.csv"
IMAGE_ROOT = DATA / "alternate_aerial" / "google"
SHEET_ROOT = DATA / "alternate_contact_sheets" / "google"
INDEX = SHEET_ROOT / "index.csv"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; tubs-research/0.1)"})
TARGET_STATUSES = {
    "blocked_arcgis_no_imagery",
    "needs_aerial_review",
    "mls_ground_backyard_context_only",
    "possible_bing_overhead_needs_verify",
    "possible_mapbox_overhead_needs_verify",
    "mapbox_overhead_house_backyard_candidate",
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:90]


def load_font(size: int):
    for name in ["arial.ttf", "calibri.ttf", "segoeui.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def read_triage() -> list[dict[str, str]]:
    with TRIAGE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def target_rows(rows: list[dict[str, str]], limit: int = 0) -> list[dict[str, str]]:
    targets = []
    for r in rows:
        if r.get("recommended_source") not in TARGET_STATUSES:
            continue
        if r.get("coordinate_confidence") == "unresolved":
            continue
        try:
            lat = float(r.get("latitude") or "")
            lon = float(r.get("longitude") or "")
        except ValueError:
            continue
        if 48 <= lat <= 52 and -118 <= lon <= -114:
            targets.append(r)
    targets.sort(key=lambda r: int(r.get("triage_rank") or 999999))
    return targets[:limit] if limit else targets


def static_url(lat: str, lon: str, zoom: int, key: str, size: str, scale: int) -> str:
    params = {
        "center": f"{lat},{lon}",
        "zoom": str(zoom),
        "size": size,
        "scale": str(scale),
        "maptype": "satellite",
        "format": "jpg",
        "key": key,
    }
    return "https://maps.googleapis.com/maps/api/staticmap?" + urlencode(params)


def fetch_images(row: dict[str, str], zooms: list[int], key: str, size: str, scale: int, delay: float) -> list[Path]:
    lat = row["latitude"]
    lon = row["longitude"]
    folder = f"{slug(row['source_label'])}/{slug(row['address'])}-{row['listing_id']}"
    out_dir = IMAGE_ROOT / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for zoom in zooms:
        path = out_dir / f"google_satellite_z{zoom}.jpg"
        if not path.exists():
            resp = SESSION.get(static_url(lat, lon, zoom, key, size, scale), timeout=45)
            ctype = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ctype.startswith("image"):
                path.write_bytes(resp.content)
            else:
                body = resp.text[:300] if resp.text else ""
                raise RuntimeError(f"Google Static Maps failed status={resp.status_code} type={ctype} body={body}")
            time.sleep(delay)
        paths.append(path)
    return paths


def make_sheet(row: dict[str, str], images: list[Path], zooms: list[int], thumb_size: int = 320) -> Path | None:
    if not images:
        return None
    header_h = 128
    footer_h = 48
    sheet = Image.new("RGB", (len(images) * thumb_size, header_h + thumb_size + footer_h), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(22)
    meta_font = load_font(15)
    draw.text((12, 10), f"{row['address']} — {row['source_label']}", fill="black", font=title_font)
    draw.text((12, 44), f"Listing {row['listing_id']} | Google Static Maps satellite | lat/lon {row['latitude']}, {row['longitude']}", fill="#333", font=meta_font)
    draw.text((12, 74), "Research preview via official API. Verify Google licensing/attribution/caching before publishing or reuse.", fill="#333", font=meta_font)
    for i, (path, zoom) in enumerate(zip(images, zooms)):
        left = i * thumb_size
        top = header_h
        with Image.open(path) as img:
            img = img.convert("RGB").resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        sheet.paste(img, (left, top))
        draw.rectangle((left, top, left + thumb_size - 1, top + thumb_size - 1), outline="white", width=1)
        draw.text((left + 10, top + 10), f"z{zoom}", fill="white", font=meta_font, stroke_width=2, stroke_fill="black")
        cx = left + thumb_size // 2
        cy = top + thumb_size // 2
        draw.line((cx - 12, cy, cx + 12, cy), fill="red", width=3)
        draw.line((cx, cy - 12, cx, cy + 12), fill="red", width=3)
    draw.text((12, header_h + thumb_size + 12), "Red crosshair marks requested coordinate center; no Google marker added over imagery.", fill="#333", font=meta_font)
    out_dir = SHEET_ROOT / slug(row["source_label"]) / f"{slug(row['address'])}-{row['listing_id']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "google_satellite_contact_sheet.jpg"
    sheet.save(out, quality=90, optimize=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--zooms", default="20,19,18", help="Comma-separated Static Maps zooms to collect")
    parser.add_argument("--size", default="640x640")
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--key", default=os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("GOOGLE_STATIC_MAPS_KEY") or "")
    args = parser.parse_args()

    if not args.key:
        raise SystemExit("Missing Google Maps API key. Set GOOGLE_MAPS_API_KEY / GOOGLE_STATIC_MAPS_KEY or pass --key.")

    zooms = [int(z.strip()) for z in args.zooms.split(",") if z.strip()]
    rows = target_rows(read_triage(), args.limit)
    SHEET_ROOT.mkdir(parents=True, exist_ok=True)
    index_rows = []
    for i, row in enumerate(rows, 1):
        images = fetch_images(row, zooms, args.key, args.size, args.scale, args.delay)
        sheet = make_sheet(row, images, zooms)
        index_rows.append({
            "source_label": row["source_label"],
            "listing_id": row["listing_id"],
            "address": row["address"],
            "recommended_source": row["recommended_source"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "google_image_count": len(images),
            "google_image_z20": str(images[0].relative_to(ROOT)) if len(images) > 0 else "",
            "google_image_z19": str(images[1].relative_to(ROOT)) if len(images) > 1 else "",
            "google_image_z18": str(images[2].relative_to(ROOT)) if len(images) > 2 else "",
            "google_contact_sheet": str(sheet.relative_to(ROOT)) if sheet else "",
        })
        print(f"[{i}/{len(rows)}] {row['address']}: {len(images)} Google Static Maps images")

    existing: dict[str, dict[str, str]] = {}
    if INDEX.exists():
        with INDEX.open(newline="", encoding="utf-8") as f:
            for existing_row in csv.DictReader(f):
                existing[existing_row["listing_id"]] = existing_row
    for index_row in index_rows:
        existing[index_row["listing_id"]] = index_row
    if existing:
        with INDEX.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(next(iter(existing.values())).keys()))
            writer.writeheader()
            writer.writerows(existing.values())
    print(f"Wrote {INDEX.relative_to(ROOT)} with {len(existing)} total rows ({len(index_rows)} touched this run)")


if __name__ == "__main__":
    main()
