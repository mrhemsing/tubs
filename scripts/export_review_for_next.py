#!/usr/bin/env python3
"""Export triage review data and selected images for the Next.js app."""
from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAGE = ROOT / "data" / "triage" / "property_candidate_triage.csv"
MLS_PHOTOS = ROOT / "data" / "mls_photo_inventory" / "mls_photo_candidates.csv"
PUBLIC = ROOT / "public"
ASSETS = PUBLIC / "review-assets"
OUT_JSON = PUBLIC / "review-data.json"

KEEP_SOURCES = {
    "mls_drone_or_aerial_candidate",
    "arcgis_overhead_house_backyard_candidate",
    "bing_overhead_house_backyard_candidate",
    "google_overhead_house_backyard_candidate",
    "possible_mls_elevated_candidate_needs_verify",
    "possible_bing_overhead_needs_verify",
    "possible_google_overhead_needs_verify",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_indices(value: str) -> list[str]:
    out: list[str] = []
    for part in (value or "").replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit() and part not in out:
            out.append(part)
    return out


def slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "item"


def copy_asset(src_rel: str, prefix: str) -> str:
    if not src_rel:
        return ""
    src = ROOT / src_rel.replace("\\", "/")
    if not src.exists():
        return ""
    ext = src.suffix.lower() or ".jpg"
    dest = ASSETS / f"{prefix}{ext}"
    i = 2
    while dest.exists() and dest.read_bytes() != src.read_bytes():
        dest = ASSETS / f"{prefix}-{i}{ext}"
        i += 1
    if not dest.exists():
        shutil.copy2(src, dest)
    return "/review-assets/" + dest.name


def main() -> None:
    if ASSETS.exists():
        shutil.rmtree(ASSETS)
    ASSETS.mkdir(parents=True, exist_ok=True)

    rows = read_csv(TRIAGE)
    photos = read_csv(MLS_PHOTOS)
    photo_map: dict[tuple[str, str], str] = {}
    for p in photos:
        try:
            idx = str(int(p["photo_index"]))
        except ValueError:
            idx = p["photo_index"]
        photo_map[(p["listing_id"], idx)] = p["local_path"]

    cards = []
    for r in rows:
        if r["recommended_source"] not in KEEP_SOURCES:
            continue
        base = f"{str(r['triage_rank']).zfill(3)}-{slug(r['address'])}-{r['listing_id']}"
        thumbs = []
        if r["recommended_source"].startswith("bing") and r.get("bing_contact_sheet"):
            url = copy_asset(r["bing_contact_sheet"], f"{base}-bing-sheet-primary")
            if url:
                thumbs.append({"label": "Bing", "url": url})
        if r["recommended_source"].startswith("google") and r.get("google_contact_sheet"):
            url = copy_asset(r.get("google_best_image", ""), f"{base}-google-best")
            if not url:
                url = copy_asset(r["google_contact_sheet"], f"{base}-google-sheet-primary")
            if url:
                thumbs.append({"label": "Google", "url": url})
        if r["recommended_source"].startswith("mapbox") and r.get("mapbox_contact_sheet"):
            url = copy_asset(r["mapbox_contact_sheet"], f"{base}-mapbox-sheet-primary")
            if url:
                thumbs.append({"label": "Mapbox", "url": url})
        for idx in parse_indices(r.get("mls_best_photo_indices", ""))[:8]:
            src = photo_map.get((r["listing_id"], idx))
            url = copy_asset(src, f"{base}-mls-{idx}") if src else ""
            if url:
                thumbs.append({"label": f"#{idx}", "url": url})
        if r.get("google_best_image") and not r["recommended_source"].startswith("google"):
            url = copy_asset(r.get("google_best_image", ""), f"{base}-google-best")
            if url:
                thumbs.append({"label": "Google", "url": url})
        if not thumbs and r.get("best_overhead_candidate"):
            url = copy_asset(r["best_overhead_candidate"], f"{base}-arcgis-best")
            if url:
                thumbs.append({"label": "ArcGIS", "url": url})
        if not thumbs and r.get("bing_contact_sheet"):
            url = copy_asset(r["bing_contact_sheet"], f"{base}-bing-sheet-primary")
            if url:
                thumbs.append({"label": "Bing", "url": url})

        mls_sheet = copy_asset(r.get("mls_contact_sheet", ""), f"{base}-mls-sheet")
        aerial_sheet = copy_asset(r.get("aerial_contact_sheet", ""), f"{base}-arcgis-sheet")
        best_arcgis = copy_asset(r.get("best_overhead_candidate", ""), f"{base}-arcgis-tile")
        bing_sheet = copy_asset(r.get("bing_contact_sheet", ""), f"{base}-bing-sheet")
        google_best = copy_asset(r.get("google_best_image", ""), f"{base}-google-image")
        google_sheet = copy_asset(r.get("google_contact_sheet", ""), f"{base}-google-sheet")
        mapbox_sheet = copy_asset(r.get("mapbox_contact_sheet", ""), f"{base}-mapbox-sheet")

        cards.append({
            "rank": int(r["triage_rank"]),
            "score": int(r["triage_score"]),
            "listingId": r["listing_id"],
            "address": r["address"],
            "sourceLabel": r["source_label"],
            "recommendedSource": r["recommended_source"],
            "coverageGoal": r.get("aerial_coverage_goal", ""),
            "bestPhotoIndices": r.get("mls_best_photo_indices", ""),
            "coordinateConfidence": r.get("coordinate_confidence", ""),
            "arcgisRealTiles": r.get("aerial_real_tiles", ""),
            "arcgisPlaceholderTiles": r.get("aerial_placeholder_tiles", ""),
            "bingOverhead": r.get("bing_overhead", ""),
            "bingTileCount": r.get("bing_tile_count", ""),
            "bingBestTilePosition": r.get("bing_best_tile_position", ""),
            "bingCoverageStrength": r.get("bing_coverage_strength", ""),
            "googleOverhead": r.get("google_overhead", ""),
            "googleImageCount": r.get("google_image_count", ""),
            "googleBestZoom": r.get("google_best_zoom", ""),
            "googleBestImage": google_best,
            "googleCoverageStrength": r.get("google_coverage_strength", ""),
            "mapboxOverhead": r.get("mapbox_overhead", ""),
            "mapboxTileCount": r.get("mapbox_tile_count", ""),
            "mapboxBestTilePosition": r.get("mapbox_best_tile_position", ""),
            "mapboxCoverageStrength": r.get("mapbox_coverage_strength", ""),
            "notes": r.get("notes", ""),
            "thumbs": thumbs,
            "links": {
                "mlsContactSheet": mls_sheet,
                "arcgisContactSheet": aerial_sheet,
                "bestArcgisTile": best_arcgis,
                "bingContactSheet": bing_sheet,
                "googleBestImage": google_best,
                "googleContactSheet": google_sheet,
                "mapboxContactSheet": mapbox_sheet,
            },
        })

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["recommended_source"]] = counts.get(r["recommended_source"], 0) + 1
    reviewed = sum(1 for r in rows if r.get("mls_drone_or_aerial") != "unreviewed")

    all_addresses = [
        {
            "rank": int(r["triage_rank"]),
            "listingId": r["listing_id"],
            "address": r["address"],
            "sourceLabel": r["source_label"],
            "recommendedSource": r["recommended_source"],
            "bestPhotoIndices": r.get("mls_best_photo_indices", ""),
            "coordinateConfidence": r.get("coordinate_confidence", ""),
            "mlsReviewed": r.get("mls_drone_or_aerial") != "unreviewed",
            "mlsAerial": r.get("mls_drone_or_aerial", ""),
            "bingOverhead": r.get("bing_overhead", ""),
            "googleOverhead": r.get("google_overhead", ""),
            "mapboxOverhead": r.get("mapbox_overhead", ""),
            "arcgisRealTiles": r.get("aerial_real_tiles", ""),
            "arcgisPlaceholderTiles": r.get("aerial_placeholder_tiles", ""),
        }
        for r in rows
    ]

    payload = {
        "generatedAt": "2026-04-28",
        "goal": "Best available aerial/top-down/elevated photos showing each house and backyard/lot together.",
        "rightsNotice": "MLS/listing photos are inventoried for internal research only. Reuse rights are unknown and must be verified before publishing or reusing.",
        "summary": {
            "properties": len(rows),
            "mlsReviewed": reviewed,
            "counts": counts,
            "candidateCards": len(cards),
        },
        "cards": cards,
        "allAddresses": all_addresses,
    }
    PUBLIC.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    total_bytes = sum(p.stat().st_size for p in ASSETS.glob("*"))
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Copied {len(list(ASSETS.glob('*')))} assets ({total_bytes / 1024 / 1024:.1f} MB)")
    print(f"Cards: {len(cards)}")


if __name__ == "__main__":
    main()
