#!/usr/bin/env python3
"""Repair bad/missing listing coordinates using ArcGIS geocoding, then recollect aerial tiles."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import requests

import collect

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GEOCODE_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "tubs-research/0.1"})


def valid_bc_coord(lat: object, lon: object) -> bool:
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return False
    return 48 <= lat_f <= 52 and -118 <= lon_f <= -114


def query_variants(listing: dict) -> list[str]:
    address = listing.get("address", "")
    subarea = listing.get("subarea", "")
    variants = [
        f"{address} {subarea} British Columbia Canada",
        f"{address} Windermere British Columbia Canada",
        f"{address} Invermere British Columbia Canada",
        f"{address} Cranbrook British Columbia Canada",
        f"{address} Kimberley British Columbia Canada",
        f"{address} Jaffray British Columbia Canada",
        f"{address} British Columbia Canada",
    ]
    seen = set()
    result = []
    for q in variants:
        q = " ".join(q.split())
        if q not in seen:
            seen.add(q)
            result.append(q)
    return result


def geocode_listing(listing: dict, min_score: float) -> dict | None:
    for q in query_variants(listing):
        r = SESSION.get(
            GEOCODE_URL,
            params={
                "SingleLine": q,
                "f": "json",
                "maxLocations": 3,
                "outFields": "Match_addr,Addr_type,Score",
                "sourceCountry": "CAN",
            },
            timeout=30,
        )
        r.raise_for_status()
        for candidate in r.json().get("candidates", []):
            attrs = candidate.get("attributes", {})
            loc = candidate.get("location", {})
            score = float(attrs.get("Score", candidate.get("score", 0)) or 0)
            addr_type = attrs.get("Addr_type", "")
            lat, lon = loc.get("y"), loc.get("x")
            if score >= min_score and addr_type in {"PointAddress", "StreetAddress"} and valid_bc_coord(lat, lon):
                return {
                    "latitude": f"{lat:.8f}",
                    "longitude": f"{lon:.8f}",
                    "geocode_source": "arcgis_world_geocoder",
                    "geocode_query": q,
                    "geocode_match_addr": attrs.get("Match_addr", ""),
                    "geocode_addr_type": addr_type,
                    "geocode_score": score,
                    "coordinate_confidence": "point" if addr_type == "PointAddress" else "street",
                }
        time.sleep(0.2)
    return None


def write_outputs(listings: list[dict]) -> None:
    (DATA / "listings.json").write_text(json.dumps(listings, indent=2), encoding="utf-8")
    fields = [
        "source_label", "listing_id", "address", "area", "subarea", "latitude", "longitude",
        "coordinate_confidence", "geocode_source", "geocode_match_addr", "geocode_score",
        "list_price", "sale_price", "sale_date", "beds", "baths", "year_built", "lot_size",
        "fin_area", "pid", "photo_count", "folder",
    ]
    with (DATA / "listings.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for listing in listings:
            writer.writerow({field: listing.get(field, "") for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listings", default=str(DATA / "listings.json"))
    parser.add_argument("--min-score", type=float, default=85.0)
    parser.add_argument("--aerial", action="store_true")
    parser.add_argument("--zoom", type=int, default=19)
    parser.add_argument("--tile-radius", type=int, default=1)
    args = parser.parse_args()

    listings = json.loads(Path(args.listings).read_text(encoding="utf-8"))
    repaired = []
    unresolved = []
    for listing in listings:
        if valid_bc_coord(listing.get("latitude"), listing.get("longitude")):
            listing.setdefault("coordinate_confidence", "listing")
            continue
        fix = geocode_listing(listing, args.min_score)
        if fix:
            listing.update(fix)
            if args.aerial:
                listing["aerial_candidates"] = collect.download_aerial_tiles(listing, args.zoom, args.tile_radius)
            repaired.append(listing)
        else:
            listing["coordinate_confidence"] = "unresolved"
            unresolved.append(listing)

    write_outputs(listings)
    print(f"Repaired {len(repaired)} listings; unresolved {len(unresolved)}")
    for listing in repaired:
        print(f"FIXED {listing['listing_id']} {listing['address']} -> {listing['latitude']},{listing['longitude']} ({listing.get('geocode_match_addr')}) tiles={len(listing.get('aerial_candidates', []))}")
    for listing in unresolved:
        print(f"UNRESOLVED {listing['listing_id']} {listing['address']}")


if __name__ == "__main__":
    main()
