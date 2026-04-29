#!/usr/bin/env python3
"""Apply vetted coordinate fixes for remaining aerial blocker rows and refresh ArcGIS tiles."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import collect
import build_triage

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

FIXES = {
    # Exact ArcGIS PointAddress for likely full road-name correction of bad out-of-region row.
    "10604265": {
        "latitude": "50.49725211",
        "longitude": "-116.00174982",
        "coordinate_confidence": "point_geocode",
        "geocode_source": "arcgis_world_geocoder_manual_variant",
        "geocode_match_addr": "4827 Holland Creek Ridge Rd, Invermere, British Columbia, V0A 1K3",
        "geocode_score": "100",
        "geocode_note": "Listing address says 4827 HOLLAND Crescent, but ArcGIS resolves exact PointAddress for 4827 Holland Creek Ridge Rd; needs human address-label verification.",
    },
    # Nominatim/OSM local East Kootenay corrections for rows where listing coordinates repeated a bad forest coordinate.
    "10672111": {"latitude": "50.47914710", "longitude": "-116.04140250", "coordinate_confidence": "house_geocode", "geocode_source": "nominatim", "geocode_match_addr": "2577 Sandstone Circle, Invermere, BC"},
    "10607338": {"latitude": "50.49162910", "longitude": "-115.99699200", "coordinate_confidence": "street_geocode", "geocode_source": "nominatim", "geocode_match_addr": "Timber Ridge Road, Area F, East Kootenay, BC"},
    "10629099": {"latitude": "50.49706570", "longitude": "-116.00270150", "coordinate_confidence": "street_geocode", "geocode_source": "nominatim", "geocode_match_addr": "Holland Creek Ridge Road, Area F, East Kootenay, BC"},
    "10587559": {"latitude": "50.49916860", "longitude": "-115.99691450", "coordinate_confidence": "street_geocode", "geocode_source": "nominatim", "geocode_match_addr": "Lakeview Meadows Close, Area F, East Kootenay, BC"},
    "10588693": {"latitude": "50.49996270", "longitude": "-115.99623070", "coordinate_confidence": "street_geocode", "geocode_source": "nominatim", "geocode_match_addr": "Copperview Close, Area F, East Kootenay, BC"},
    "10613313": {"latitude": "50.49839430", "longitude": "-115.99778400", "coordinate_confidence": "street_geocode", "geocode_source": "nominatim", "geocode_match_addr": "Lakeview Meadows Glen, Area F, East Kootenay, BC"},
}

CSV_FIELDS = [
    "source_label", "listing_id", "address", "area", "subarea", "latitude", "longitude",
    "coordinate_confidence", "geocode_source", "geocode_match_addr", "geocode_score",
    "list_price", "sale_price", "sale_date", "beds", "baths", "year_built", "lot_size",
    "fin_area", "pid", "photo_count", "folder",
]


def write_listings_csv(listings: list[dict]) -> None:
    with (DATA / "listings.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for listing in listings:
            w.writerow({field: listing.get(field, "") for field in CSV_FIELDS})


def update_triage(listings_by_id: dict[str, dict]) -> None:
    path = DATA / "triage" / "property_aerial_triage.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    for row in rows:
        lid = row["listing_id"]
        if lid not in FIXES:
            continue
        listing = listings_by_id[lid]
        tiles = listing.get("aerial_candidates", []) or []
        best = build_triage.center_tile(tiles)
        stats = build_triage.image_stats(best)
        row.update({
            "latitude": listing.get("latitude", ""),
            "longitude": listing.get("longitude", ""),
            "coordinate_confidence": listing.get("coordinate_confidence", ""),
            "best_overhead_candidate": best,
            "contact_sheet": build_triage.contact_sheet_path(listing),
            "aerial_tile_count": str(len(tiles)),
            "image_quality_score_auto": str(stats["quality_score"]),
            "center_tile_bytes": str(stats["bytes"]),
            "center_tile_brightness": str(stats["brightness"]),
            "center_tile_contrast": str(stats["contrast"]),
        })
        if best:
            row["review_status"] = "needs_review"
            row["backyard_visibility"] = "unreviewed"
            row["overhead_quality"] = "unreviewed"
        note = f"Coordinate fallback applied: {listing.get('geocode_match_addr','')} ({listing.get('geocode_source','')}); recollected ArcGIS z19 tiles."
        if listing.get("geocode_note"):
            note += " " + listing["geocode_note"]
        row["notes"] = (row.get("notes", "") + "; " if row.get("notes") else "") + note
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    (DATA / "triage" / "property_aerial_triage.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


def main() -> None:
    listings = json.loads((DATA / "listings.json").read_text(encoding="utf-8"))
    fixed = []
    for listing in listings:
        lid = str(listing.get("listing_id"))
        if lid not in FIXES:
            continue
        listing.update(FIXES[lid])
        listing["aerial_candidates"] = collect.download_aerial_tiles(listing, zoom=19, radius=1)
        fixed.append((lid, listing.get("address"), len(listing.get("aerial_candidates", []))))
    (DATA / "listings.json").write_text(json.dumps(listings, indent=2), encoding="utf-8")
    write_listings_csv(listings)
    listings_by_id = {str(l["listing_id"]): l for l in listings}
    update_triage(listings_by_id)
    print(f"Applied {len(fixed)} coordinate fixes")
    for lid, address, tile_count in fixed:
        print(f"{lid} {address}: {tile_count} ArcGIS tiles")


if __name__ == "__main__":
    main()
