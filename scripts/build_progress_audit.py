#!/usr/bin/env python3
"""Build compact current-progress audit artifacts for the tubs overnight workflow."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "triage"

TRIAGE = OUT_DIR / "property_candidate_triage.csv"
CONTACT_INDEX = DATA / "contact_sheets" / "index.csv"
MLS_CANDIDATES = DATA / "mls_photo_inventory" / "mls_photo_candidates.csv"
MLS_SUMMARY = DATA / "mls_photo_inventory" / "mls_listing_summary.csv"
GALLERY = ROOT / "public" / "arcgis-contact-sheets.html"
GALLERY_DIR = ROOT / "public" / "arcgis-contact-sheets"

OUT_JSON = OUT_DIR / "current_progress_audit.json"
OUT_CSV = OUT_DIR / "current_progress_by_area.csv"
def progress_summary_path() -> Path:
    today = datetime.now().astimezone().date().isoformat()
    return DATA / f"progress_summary_{today}.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    triage = read_csv(TRIAGE)
    contact = read_csv(CONTACT_INDEX)
    mls_candidates = read_csv(MLS_CANDIDATES)
    mls_summary = read_csv(MLS_SUMMARY)

    by_area: dict[str, dict[str, object]] = defaultdict(lambda: {
        "properties": 0,
        "arcgis_real_tile_properties": 0,
        "arcgis_placeholder_only_properties": 0,
        "geocode_fallback_needed": 0,
        "mls_thumbnails": 0,
        "mls_proxy_candidates": 0,
        "mls_proxy_candidate_listings": 0,
        "recommended_sources": Counter(),
    })

    contact_by_id = {r["listing_id"]: r for r in contact}
    mls_summary_by_id = {r["listing_id"]: r for r in mls_summary}
    mls_candidate_listing_ids = {r["listing_id"] for r in mls_candidates if r.get("candidate_type") != "unclassified"}

    for row in triage:
        area = row["source_label"]
        item = by_area[area]
        item["properties"] += 1
        real = int(row.get("aerial_real_tiles") or 0)
        placeholders = int(row.get("aerial_placeholder_tiles") or 0)
        if real > 0:
            item["arcgis_real_tile_properties"] += 1
        elif placeholders > 0:
            item["arcgis_placeholder_only_properties"] += 1
        if contact_by_id.get(row["listing_id"], {}).get("needs_geocode_fallback"):
            item["geocode_fallback_needed"] += 1
        mls_row = mls_summary_by_id.get(row["listing_id"], {})
        item["mls_thumbnails"] += int(mls_row.get("downloaded_mls_thumbnails") or 0)
        item["mls_proxy_candidates"] += int(mls_row.get("possible_outdoor_backyard_aerial_candidates") or 0)
        if row["listing_id"] in mls_candidate_listing_ids:
            item["mls_proxy_candidate_listings"] += 1
        item["recommended_sources"][row["recommended_source"]] += 1

    area_rows = []
    for area in sorted(by_area):
        item = by_area[area]
        area_rows.append({
            "source_label": area,
            "properties": item["properties"],
            "arcgis_real_tile_properties": item["arcgis_real_tile_properties"],
            "arcgis_placeholder_only_properties": item["arcgis_placeholder_only_properties"],
            "geocode_fallback_needed": item["geocode_fallback_needed"],
            "mls_thumbnails": item["mls_thumbnails"],
            "mls_proxy_candidates": item["mls_proxy_candidates"],
            "mls_proxy_candidate_listings": item["mls_proxy_candidate_listings"],
            "recommended_sources_json": json.dumps(dict(sorted(item["recommended_sources"].items())), sort_keys=True),
        })

    total_recommended = Counter(r["recommended_source"] for r in triage)
    rights = Counter(r.get("reuse_rights", "") for r in mls_candidates)
    audit = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "properties": len(triage),
        "arcgis_contact_sheet_index_rows": len(contact),
        "public_arcgis_gallery_exists": GALLERY.exists(),
        "public_arcgis_gallery_sheets": len(list(GALLERY_DIR.glob("*.jpg"))) if GALLERY_DIR.exists() else 0,
        "geocode_fallback_needed": sum(1 for r in contact if r.get("needs_geocode_fallback")),
        "coordinate_confidence": dict(sorted(Counter(r.get("coordinate_confidence", "") for r in triage).items())),
        "recommended_sources": dict(sorted(total_recommended.items())),
        "mls_thumbnails": len(mls_candidates),
        "mls_proxy_candidates": sum(1 for r in mls_candidates if r.get("candidate_type") != "unclassified"),
        "mls_proxy_candidate_listings": len(mls_candidate_listing_ids),
        "mls_reuse_rights": dict(sorted(rights.items())),
        "areas": area_rows,
        "blockers": [],
        "next_best_action": "Visually spot-check the linked ArcGIS sheet gallery and a few live review cards, then test Edit tub layer on chosen cards.",
    }

    if audit["arcgis_contact_sheet_index_rows"] != audit["properties"]:
        audit["blockers"].append("ArcGIS contact-sheet index count does not match triage property count.")
    if audit["public_arcgis_gallery_sheets"] != audit["properties"]:
        audit["blockers"].append("Public ArcGIS gallery sheet count does not match property count.")
    if audit["geocode_fallback_needed"]:
        audit["blockers"].append("Some listings still need geocode fallback.")
    if audit["mls_reuse_rights"] != {"unknown_research_only": audit["mls_thumbnails"]}:
        audit["blockers"].append("MLS reuse-rights inventory has unexpected values; review before using photos.")

    write_csv(OUT_CSV, area_rows, [
        "source_label", "properties", "arcgis_real_tile_properties", "arcgis_placeholder_only_properties",
        "geocode_fallback_needed", "mls_thumbnails", "mls_proxy_candidates", "mls_proxy_candidate_listings",
        "recommended_sources_json",
    ])
    OUT_JSON.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    out_md = progress_summary_path()

    md_lines = [
        f"# Tubs progress summary — {audit['generated_at']}",
        "",
        f"- Properties triaged: **{audit['properties']}**",
        f"- ArcGIS contact sheets: **{audit['arcgis_contact_sheet_index_rows']}** indexed; **{audit['public_arcgis_gallery_sheets']}** in public gallery",
        f"- Geocode fallback needed: **{audit['geocode_fallback_needed']}**",
        f"- MLS thumbnails inventoried: **{audit['mls_thumbnails']}**; proxy outdoor/backyard/aerial candidates: **{audit['mls_proxy_candidates']}** across **{audit['mls_proxy_candidate_listings']}** listings",
        f"- MLS reuse rights: **unknown_research_only** for all inventoried thumbnails",
        f"- Blockers: **{'; '.join(audit['blockers']) if audit['blockers'] else 'none'}**",
        f"- Next best action: {audit['next_best_action']}",
        "",
        "## Area rollup",
        "",
        "| Area | Properties | Real ArcGIS | Placeholder-only ArcGIS | MLS thumbnails | MLS proxy candidates |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in area_rows:
        md_lines.append(
            f"| {row['source_label']} | {row['properties']} | {row['arcgis_real_tile_properties']} | "
            f"{row['arcgis_placeholder_only_properties']} | {row['mls_thumbnails']} | {row['mls_proxy_candidates']} |"
        )
    md_lines.extend(["", "Outputs:", f"- `{OUT_JSON.relative_to(ROOT)}`", f"- `{OUT_CSV.relative_to(ROOT)}`"])
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"Wrote {out_md.relative_to(ROOT)}")
    print(f"Blockers: {audit['blockers'] or 'none'}")


if __name__ == "__main__":
    main()
