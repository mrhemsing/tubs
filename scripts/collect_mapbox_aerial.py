#!/usr/bin/env python3
"""Collect Mapbox Satellite tiles as an alternate overhead source.

Requires a Mapbox access token in MAPBOX_TOKEN / MAPBOX_ACCESS_TOKEN or --token.
Research output only; verify imagery licensing/attribution before reuse outside this workflow.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import re
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TRIAGE = DATA / "triage" / "property_candidate_triage.csv"
TILE_ROOT = DATA / "alternate_aerial" / "mapbox"
SHEET_ROOT = DATA / "alternate_contact_sheets" / "mapbox"
INDEX = SHEET_ROOT / "index.csv"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; tubs-research/0.1)"})
TARGET_STATUSES = {
    "blocked_arcgis_no_imagery",
    "needs_aerial_review",
    "mls_ground_backyard_context_only",
    "possible_bing_overhead_needs_verify",
}


def latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


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


def tile_url(x: int, y: int, z: int, token: str, retina: bool) -> str:
    suffix = "@2x.jpg90" if retina else ".jpg90"
    return f"https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}{suffix}?access_token={token}"


def fetch_tiles(row: dict[str, str], zoom: int, radius: int, delay: float, token: str, retina: bool) -> list[Path]:
    lat = float(row["latitude"])
    lon = float(row["longitude"])
    x0, y0 = latlon_to_tile(lat, lon, zoom)
    folder = f"{slug(row['source_label'])}/{slug(row['address'])}-{row['listing_id']}/mapbox_satellite_z{zoom}"
    out_dir = TILE_ROOT / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            x, y = x0 + dx, y0 + dy
            path = out_dir / f"z{zoom}_x{x}_y{y}.jpg"
            if not path.exists():
                resp = SESSION.get(tile_url(x, y, zoom, token, retina), timeout=30)
                if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                    path.write_bytes(resp.content)
                else:
                    body = resp.text[:200] if resp.text else ""
                    raise RuntimeError(f"Mapbox tile request failed status={resp.status_code} type={resp.headers.get('content-type')} body={body}")
                time.sleep(delay)
            paths.append(path)
    return paths


def parse_tile(path: Path) -> tuple[int, int] | None:
    match = re.search(r"_x(?P<x>\d+)_y(?P<y>\d+)\.jpg$", path.name)
    if not match:
        return None
    return int(match.group("x")), int(match.group("y"))


def make_sheet(row: dict[str, str], tiles: list[Path], zoom: int, thumb_size: int = 256) -> Path | None:
    parsed = []
    for p in tiles:
        xy = parse_tile(p)
        if xy:
            parsed.append((*xy, p))
    if not parsed:
        return None
    xs = sorted({x for x, _, _ in parsed})
    ys = sorted({y for _, y, _ in parsed})
    x_index = {x: i for i, x in enumerate(xs)}
    y_index = {y: i for i, y in enumerate(ys)}
    header_h = 120
    footer_h = 48
    sheet = Image.new("RGB", (len(xs) * thumb_size, header_h + len(ys) * thumb_size + footer_h), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(22)
    meta_font = load_font(15)
    draw.text((12, 10), f"{row['address']} — {row['source_label']}", fill="black", font=title_font)
    draw.text((12, 44), f"Listing {row['listing_id']} | Mapbox Satellite z{zoom} | lat/lon {row['latitude']}, {row['longitude']}", fill="#333", font=meta_font)
    draw.text((12, 74), "Red outline = property coordinate center tile. Research only; verify imagery rights/attribution before reuse.", fill="#333", font=meta_font)
    for x, y, p in parsed:
        col = x_index[x]
        row_i = y_index[y]
        left = col * thumb_size
        top = header_h + row_i * thumb_size
        with Image.open(p) as img:
            img = img.convert("RGB").resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        sheet.paste(img, (left, top))
        center = col == len(xs) // 2 and row_i == len(ys) // 2
        draw.rectangle((left, top, left + thumb_size - 1, top + thumb_size - 1), outline="red" if center else "white", width=4 if center else 1)
    draw.text((12, header_h + len(ys) * thumb_size + 12), "Use this sheet to visually pick best house + backyard/lot overhead candidate.", fill="#333", font=meta_font)
    out_dir = SHEET_ROOT / slug(row["source_label"]) / f"{slug(row['address'])}-{row['listing_id']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "mapbox_satellite_contact_sheet.jpg"
    sheet.save(out, quality=90, optimize=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--zoom", type=int, default=19)
    parser.add_argument("--tile-radius", type=int, default=1)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--token", default=os.environ.get("MAPBOX_TOKEN") or os.environ.get("MAPBOX_ACCESS_TOKEN") or "")
    parser.add_argument("--no-retina", action="store_true", help="Use 256px tiles instead of @2x tiles")
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("Missing Mapbox token. Set MAPBOX_TOKEN / MAPBOX_ACCESS_TOKEN or pass --token.")

    rows = target_rows(read_triage(), args.limit)
    SHEET_ROOT.mkdir(parents=True, exist_ok=True)
    index_rows = []
    for i, row in enumerate(rows, 1):
        tiles = fetch_tiles(row, args.zoom, args.tile_radius, args.delay, args.token, not args.no_retina)
        sheet = make_sheet(row, tiles, args.zoom)
        index_rows.append({
            "source_label": row["source_label"],
            "listing_id": row["listing_id"],
            "address": row["address"],
            "recommended_source": row["recommended_source"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "mapbox_tile_count": len(tiles),
            "mapbox_contact_sheet": str(sheet.relative_to(ROOT)) if sheet else "",
        })
        print(f"[{i}/{len(rows)}] {row['address']}: {len(tiles)} Mapbox tiles")
    if index_rows:
        with INDEX.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(index_rows[0].keys()))
            writer.writeheader()
            writer.writerows(index_rows)
    print(f"Wrote {INDEX.relative_to(ROOT)} with {len(index_rows)} rows")


if __name__ == "__main__":
    main()
