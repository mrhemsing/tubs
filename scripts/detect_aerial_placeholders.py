#!/usr/bin/env python3
"""Detect Esri no-imagery placeholder tiles and reprioritize aerial triage."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "triage"


def tile_metrics(rel_path: str) -> dict:
    path = ROOT / rel_path
    if not path.exists():
        return {"exists": False, "bytes": 0, "contrast": 0.0, "brightness": 0.0, "placeholder": True}
    try:
        with Image.open(path) as img:
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            brightness = float(stat.mean[0])
            contrast = float(stat.stddev[0])
        size = path.stat().st_size
        # Esri placeholder tiles observed as tiny gray JPEGs (~2.5KB, contrast ~5).
        placeholder = size < 4000 and contrast < 10 and 185 <= brightness <= 230
        return {
            "exists": True,
            "bytes": size,
            "contrast": round(contrast, 2),
            "brightness": round(brightness, 2),
            "placeholder": placeholder,
        }
    except Exception:
        return {"exists": False, "bytes": 0, "contrast": 0.0, "brightness": 0.0, "placeholder": True}


def listing_placeholder_status(listing: dict) -> dict:
    tiles = listing.get("aerial_candidates", []) or []
    metrics = [tile_metrics(p) for p in tiles]
    if not metrics:
        return {"tile_count": 0, "placeholder_count": 0, "real_tile_count": 0, "all_placeholder": True}
    placeholder_count = sum(1 for m in metrics if m["placeholder"])
    real_tile_count = len(metrics) - placeholder_count
    return {
        "tile_count": len(metrics),
        "placeholder_count": placeholder_count,
        "real_tile_count": real_tile_count,
        "all_placeholder": placeholder_count == len(metrics),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listings", default=str(DATA / "listings.json"))
    parser.add_argument("--triage", default=str(OUT / "property_aerial_triage.csv"))
    args = parser.parse_args()

    listings = json.loads(Path(args.listings).read_text(encoding="utf-8"))
    status_by_id = {l["listing_id"]: listing_placeholder_status(l) for l in listings}

    triage_path = Path(args.triage)
    rows = list(csv.DictReader(triage_path.open(encoding="utf-8")))
    for row in rows:
        status = status_by_id.get(row["listing_id"], {})
        row["aerial_placeholder_tiles"] = status.get("placeholder_count", "")
        row["aerial_real_tiles"] = status.get("real_tile_count", "")
        if status.get("all_placeholder") and row.get("review_status") == "needs_review":
            row["review_status"] = "blocked_no_aerial_imagery"
            row["backyard_visibility"] = "unclear"
            row["overhead_quality"] = "poor"
            row["hot_tub_visible"] = "unclear"
            note = "Automated placeholder detection: all aerial tiles appear to be Esri no-imagery placeholders; use MLS/contact-sheet path instead."
            row["notes"] = (row.get("notes", "") + " " if row.get("notes") else "") + note

    fieldnames = list(rows[0].keys())
    # If the new fields were not present, DictReader rows receive keys when assigned but not in fieldnames.
    for field in ["aerial_placeholder_tiles", "aerial_real_tiles"]:
        if field not in fieldnames:
            fieldnames.append(field)

    with triage_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "property_aerial_triage.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    summary_rows = []
    for listing in listings:
        s = status_by_id[listing["listing_id"]]
        summary_rows.append({
            "listing_id": listing["listing_id"],
            "address": listing.get("address", ""),
            "source_label": listing.get("source_label", ""),
            **s,
        })
    summary_path = OUT / "aerial_placeholder_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    all_placeholder = sum(1 for s in status_by_id.values() if s["all_placeholder"])
    no_tiles = sum(1 for s in status_by_id.values() if s["tile_count"] == 0)
    real = sum(1 for s in status_by_id.values() if s["real_tile_count"] > 0)
    print(f"Listings with real aerial tiles: {real}")
    print(f"Listings with all-placeholder aerial tiles: {all_placeholder}")
    print(f"Listings with no aerial tiles: {no_tiles}")
    print(f"Summary: {summary_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
