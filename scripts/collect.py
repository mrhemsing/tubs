#!/usr/bin/env python3
"""Collect listing metadata and top-down aerial image candidates."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
AERIAL = DATA / "aerial"
PHOTO_SERVER = "https://images.realtyserver.com/photo_server.php"
ESRI_TILE = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; tubs-research/0.1)"})


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    value = clean_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:90] or "unknown"


def find(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.I | re.S)
    return clean_text(match.group(1)) if match else default


def label_value(label: str, text: str) -> str:
    pattern = rf"<td class=['\"]listing-label['\"]>{re.escape(label)}</td>\s*<td[^>]*>(.*?)</td>"
    return find(pattern, text)


def photo_url(uid: str, index: int, thumbnail: bool = False) -> str:
    params = {
        "btnSubmit": "GetPhoto",
        "board": "air",
        "name": f"{uid}.L{index:02d}",
        "failover": "portal_Blank.gif",
    }
    url = f"{PHOTO_SERVER}?{urlencode(params)}"
    return f"{url}&thumbnail" if thumbnail else url


def fetch_source(source: dict, refresh: bool = False) -> str:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{source['name']}.html"
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")
    r = SESSION.get(source["url"], timeout=60)
    r.raise_for_status()
    path.write_text(r.text, encoding="utf-8")
    return r.text


def parse_listings(source: dict, text: str) -> list[dict]:
    blocks = re.split(r'<div class="listing-container[^>]*>', text)[1:]
    listings: list[dict] = []
    for block in blocks:
        listing_id = find(r'name="checkedId"\s+value="([^"]+)"', block)
        uid = find(r'data-uid="([^"]+)"', block)
        photo_count = find(r'data-photocount="(\d+)"', block, "0")
        address = find(r'<span class="listing-address">(.*?)</span>', block)
        if not listing_id or not address:
            continue
        record = {
            "source": source["name"],
            "source_label": source["label"],
            "listing_id": listing_id,
            "uid": uid,
            "photo_count": int(photo_count or 0),
            "address": address,
            "area": find(r'<span class="listing-area">(.*?)</span>', block),
            "subarea": find(r'<span class="listing-subarea">(.*?)</span>', block),
            "latitude": find(r'data-latitude="([^"]+)"', block),
            "longitude": find(r'data-longitude="([^"]+)"', block),
            "list_price": find(r'<a class="listing-price"[^>]*>(.*?)</a>', block),
            "beds": label_value("Bed", block),
            "baths": label_value("Bath", block),
            "mls": label_value("MLS&reg;", block) or label_value("MLS®", block),
            "year_built": label_value("Year Built", block),
            "lot_size": label_value("Lot Size", block),
            "fin_area": label_value("Fin Area", block),
            "pid": label_value("PID", block),
            "sale_date": label_value("Sale Date", block),
            "sale_price": label_value("Sale Price", block),
            "features": label_value("Features", block),
        }
        record["mls_photo_urls"] = [photo_url(uid, i) for i in range(1, record["photo_count"] + 1)] if uid else []
        record["folder"] = f"{record['source']}/{slugify(address)}-{listing_id}"
        listings.append(record)
    return listings


def latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def download_aerial_tiles(listing: dict, zoom: int, radius: int, delay: float = 0.05) -> list[str]:
    try:
        lat = float(listing["latitude"])
        lon = float(listing["longitude"])
    except (TypeError, ValueError):
        return []
    # Skip obviously bad coordinates for this BC project.
    if not (48 <= lat <= 52 and -118 <= lon <= -114):
        return []

    x0, y0 = latlon_to_tile(lat, lon, zoom)
    out_dir = AERIAL / listing["folder"] / f"esri_world_imagery_z{zoom}"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            x, y = x0 + dx, y0 + dy
            path = out_dir / f"z{zoom}_x{x}_y{y}.jpg"
            if not path.exists():
                url = ESRI_TILE.format(z=zoom, x=x, y=y)
                r = SESSION.get(url, timeout=30)
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                    path.write_bytes(r.content)
                time.sleep(delay)
            if path.exists():
                saved.append(str(path.relative_to(ROOT)))
    return saved


def write_outputs(listings: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "listings.json").write_text(json.dumps(listings, indent=2), encoding="utf-8")

    fields = [
        "source_label", "listing_id", "address", "area", "subarea", "latitude", "longitude",
        "list_price", "sale_price", "sale_date", "beds", "baths", "year_built", "lot_size",
        "fin_area", "pid", "photo_count", "folder",
    ]
    with (DATA / "listings.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for listing in listings:
            writer.writerow({field: listing.get(field, "") for field in fields})

    for listing in listings:
        manifest_dir = DATA / "photo_manifests" / listing["folder"]
        manifest_dir.mkdir(parents=True, exist_ok=True)
        (manifest_dir / "mls_photo_urls.txt").write_text("\n".join(listing.get("mls_photo_urls", [])), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default=str(DATA / "sources.json"))
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Limit per source for test runs; 0 means all.")
    parser.add_argument("--aerial", action="store_true", help="Download ArcGIS World Imagery tile candidates.")
    parser.add_argument("--zoom", type=int, default=19)
    parser.add_argument("--tile-radius", type=int, default=1, help="0=center tile, 1=3x3, 2=5x5.")
    args = parser.parse_args()

    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    all_listings: list[dict] = []
    for source in sources:
        text = fetch_source(source, refresh=args.refresh)
        listings = parse_listings(source, text)
        if args.limit:
            listings = listings[: args.limit]
        print(f"{source['label']}: {len(listings)} listings")
        all_listings.extend(listings)

    if args.aerial:
        for idx, listing in enumerate(all_listings, 1):
            saved = download_aerial_tiles(listing, args.zoom, args.tile_radius)
            listing["aerial_candidates"] = saved
            print(f"[{idx}/{len(all_listings)}] {listing['address']}: {len(saved)} aerial tiles")

    write_outputs(all_listings)
    print(f"Wrote {len(all_listings)} listings to data/listings.json and data/listings.csv")


if __name__ == "__main__":
    main()
