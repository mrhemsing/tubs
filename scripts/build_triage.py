#!/usr/bin/env python3
"""Seed a per-property triage/ranking table for aerial backyard review."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "triage"
TILE_RE = re.compile(r"z(?P<z>\d+)_x(?P<x>\d+)_y(?P<y>\d+)\.jpg$")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path else ""


def parse_tile(path: str) -> tuple[int, int, int] | None:
    match = TILE_RE.search(Path(path).name)
    if not match:
        return None
    return int(match.group("z")), int(match.group("x")), int(match.group("y"))


def center_tile(tile_paths: list[str]) -> str:
    parsed = []
    for p in tile_paths:
        parsed_tile = parse_tile(p)
        if parsed_tile:
            z, x, y = parsed_tile
            parsed.append((x, y, p))
    if not parsed:
        return ""
    xs = sorted({x for x, _, _ in parsed})
    ys = sorted({y for _, y, _ in parsed})
    cx = xs[len(xs) // 2]
    cy = ys[len(ys) // 2]
    for x, y, p in parsed:
        if x == cx and y == cy:
            return p
    return parsed[len(parsed) // 2][2]


def image_stats(path: str) -> dict:
    if not path:
        return {"bytes": 0, "brightness": "", "contrast": "", "quality_score": 0}
    full = ROOT / path
    if not full.exists():
        return {"bytes": 0, "brightness": "", "contrast": "", "quality_score": 0}
    try:
        with Image.open(full) as img:
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            brightness = float(stat.mean[0])
            contrast = float(stat.stddev[0])
        size = full.stat().st_size
        # Lightweight proxy only: avoids blank/low-detail tiles; final review still visual/AI.
        quality = min(100, round((size / 4000) + (contrast * 1.2)))
        return {
            "bytes": size,
            "brightness": round(brightness, 1),
            "contrast": round(contrast, 1),
            "quality_score": quality,
        }
    except Exception:
        return {"bytes": 0, "brightness": "", "contrast": "", "quality_score": 0}


def contact_sheet_path(listing: dict) -> str:
    p = DATA / "contact_sheets" / listing["folder"] / "aerial_contact_sheet.jpg"
    return rel(p) if p.exists() else ""


def confidence(listing: dict) -> str:
    c = listing.get("coordinate_confidence") or "listing"
    if c == "listing":
        try:
            lat = float(listing.get("latitude", ""))
            lon = float(listing.get("longitude", ""))
            if not (48 <= lat <= 52 and -118 <= lon <= -114):
                return "unresolved"
        except ValueError:
            return "unresolved"
    return c


def make_rows(listings: list[dict]) -> list[dict]:
    rows = []
    for listing in listings:
        tiles = listing.get("aerial_candidates", []) or []
        best = center_tile(tiles)
        stats = image_stats(best)
        conf = confidence(listing)
        rows.append({
            "priority_rank": "",
            "review_status": "needs_review" if best else "blocked_no_coordinate",
            "source_label": listing.get("source_label", ""),
            "listing_id": listing.get("listing_id", ""),
            "address": listing.get("address", ""),
            "area": listing.get("area", ""),
            "subarea": listing.get("subarea", ""),
            "latitude": listing.get("latitude", ""),
            "longitude": listing.get("longitude", ""),
            "coordinate_confidence": conf,
            "best_overhead_candidate": best,
            "contact_sheet": contact_sheet_path(listing),
            "aerial_tile_count": len(tiles),
            "image_quality_score_auto": stats["quality_score"],
            "center_tile_bytes": stats["bytes"],
            "center_tile_brightness": stats["brightness"],
            "center_tile_contrast": stats["contrast"],
            "backyard_visibility": "unreviewed",
            "overhead_quality": "unreviewed",
            "hot_tub_visible": "unreviewed",
            "mls_photo_count": listing.get("photo_count", 0),
            "source_risk": "research_only_verify_license",
            "notes": "" if best else "No usable coordinate yet; needs parcel/manual lookup.",
        })
    rows.sort(key=lambda r: (r["review_status"] != "needs_review", -(int(r["image_quality_score_auto"] or 0)), r["source_label"], r["address"]))
    for idx, row in enumerate([r for r in rows if r["review_status"] == "needs_review"], 1):
        row["priority_rank"] = idx
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listings", default=str(DATA / "listings.json"))
    args = parser.parse_args()
    listings = json.loads(Path(args.listings).read_text(encoding="utf-8"))
    rows = make_rows(listings)
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "property_aerial_triage.csv"
    json_path = OUT / "property_aerial_triage.json"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    usable = sum(1 for r in rows if r["review_status"] == "needs_review")
    blocked = len(rows) - usable
    print(f"Wrote {len(rows)} triage rows: {usable} ready for review, {blocked} blocked")
    print(f"CSV: {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
