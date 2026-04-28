#!/usr/bin/env python3
"""Build per-property contact sheets/mosaics from collected aerial tiles."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "contact_sheets"
TILE_RE = re.compile(r"z(?P<z>\d+)_x(?P<x>\d+)_y(?P<y>\d+)\.jpg$")


def safe_text(value: object) -> str:
    return "" if value is None else str(value)


def load_font(size: int = 18) -> ImageFont.ImageFont:
    for name in ["arial.ttf", "calibri.ttf", "segoeui.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def parse_tile(path: str) -> tuple[int, int, int] | None:
    match = TILE_RE.search(Path(path).name)
    if not match:
        return None
    return int(match.group("z")), int(match.group("x")), int(match.group("y"))


def make_sheet(listing: dict, tile_paths: list[str], thumb_size: int, label_height: int) -> Path | None:
    parsed = []
    for rel in tile_paths:
        tile = parse_tile(rel)
        full = ROOT / rel
        if tile and full.exists():
            z, x, y = tile
            parsed.append((x, y, full, rel))
    if not parsed:
        return None

    xs = sorted({x for x, _, _, _ in parsed})
    ys = sorted({y for _, y, _, _ in parsed})
    x_index = {x: i for i, x in enumerate(xs)}
    y_index = {y: i for i, y in enumerate(ys)}
    cols, rows = len(xs), len(ys)
    header_h = 104
    sheet = Image.new("RGB", (cols * thumb_size, header_h + rows * thumb_size + label_height), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(22)
    meta_font = load_font(16)

    title = f"{safe_text(listing.get('address'))} — {safe_text(listing.get('source_label'))}"
    meta = (
        f"Listing {safe_text(listing.get('listing_id'))} | "
        f"lat/lon {safe_text(listing.get('latitude'))}, {safe_text(listing.get('longitude'))} | "
        f"sale {safe_text(listing.get('sale_price'))} {safe_text(listing.get('sale_date'))}"
    )
    draw.text((12, 10), title, fill="black", font=title_font)
    draw.text((12, 42), meta, fill="black", font=meta_font)
    draw.text((12, 70), "ArcGIS World Imagery tile mosaic/contact sheet — center tile should contain property coordinate", fill="#333333", font=meta_font)

    for x, y, full, rel in parsed:
        col = x_index[x]
        row = y_index[y]
        left = col * thumb_size
        top = header_h + row * thumb_size
        with Image.open(full) as img:
            img = img.convert("RGB").resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        sheet.paste(img, (left, top))
        outline = "red" if col == cols // 2 and row == rows // 2 else "white"
        draw.rectangle((left, top, left + thumb_size - 1, top + thumb_size - 1), outline=outline, width=4 if outline == "red" else 1)

    footer_y = header_h + rows * thumb_size + 8
    draw.text((12, footer_y), "Red outline = coordinate center tile. Use this sheet to pick best overhead/backyard crop candidate.", fill="#333333", font=meta_font)

    out_dir = OUT / listing["folder"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "aerial_contact_sheet.jpg"
    sheet.save(out_path, quality=90, optimize=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listings", default=str(DATA / "listings.json"))
    parser.add_argument("--thumb-size", type=int, default=256)
    parser.add_argument("--label-height", type=int, default=42)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    listings = json.loads(Path(args.listings).read_text(encoding="utf-8"))
    if args.limit:
        listings = listings[: args.limit]

    rows = []
    made = 0
    missing = 0
    for listing in listings:
        tile_paths = listing.get("aerial_candidates", []) or []
        out_path = make_sheet(listing, tile_paths, args.thumb_size, args.label_height)
        if out_path:
            made += 1
            rel = str(out_path.relative_to(ROOT))
        else:
            missing += 1
            rel = ""
        rows.append({
            "source_label": listing.get("source_label", ""),
            "listing_id": listing.get("listing_id", ""),
            "address": listing.get("address", ""),
            "latitude": listing.get("latitude", ""),
            "longitude": listing.get("longitude", ""),
            "aerial_tile_count": len(tile_paths),
            "contact_sheet": rel,
            "needs_geocode_fallback": "yes" if len(tile_paths) == 0 else "",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    index_path = OUT / "index.csv"
    with index_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {made} contact sheets; {missing} listings need coordinate/geocode fallback")
    print(f"Index: {index_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
