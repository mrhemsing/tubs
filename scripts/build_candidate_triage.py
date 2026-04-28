#!/usr/bin/env python3
"""Build consolidated property candidate triage from aerial + MLS review outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAGE_CSV = ROOT / "data" / "triage" / "property_aerial_triage.csv"
MLS_SUMMARY_CSV = ROOT / "data" / "mls_photo_inventory" / "mls_listing_summary.csv"
MLS_CROSSCHECK_DIR = ROOT / "data" / "mls_photo_inventory"
OUT_CSV = ROOT / "data" / "triage" / "property_candidate_triage.csv"
OUT_JSON = ROOT / "data" / "triage" / "property_candidate_triage.json"
CROSSCHECK_SUMMARY_CSV = ROOT / "data" / "mls_photo_inventory" / "mls_crosscheck_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def load_mls_reviews() -> dict[str, dict[str, object]]:
    reviews: dict[str, dict[str, object]] = {}
    for p in sorted(MLS_CROSSCHECK_DIR.glob("mls_crosscheck_batch_*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for item in data:
            lid = str(item["listing_id"])
            reviews[lid] = {
                "listing_id": lid,
                "address": item.get("address", ""),
                "reason": item.get("reason", "MLS contact sheet vision review."),
                "has_backyard_photos": item.get("has_backyard_photos", "unclear"),
                "has_drone_or_aerial_photos": item.get("has_drone_or_aerial_photos", "unclear"),
                "hot_tub_or_pool_visible": item.get("hot_tub_or_pool_visible", "unclear"),
                "best_photo_indices": ",".join(map(str, item.get("best_photo_indices", []))) if isinstance(item.get("best_photo_indices"), list) else item.get("best_photo_indices", ""),
                "marketing_candidate_strength": item.get("marketing_candidate_strength", "unclear"),
                "reuse_rights": item.get("reuse_rights", "unknown_research_only"),
                "notes": item.get("notes", ""),
            }
    return reviews


def score_row(row: dict[str, object]) -> int:
    score = 0
    aerial_quality = row.get("aerial_overhead_quality", "")
    if aerial_quality == "good":
        score += 40
    elif aerial_quality == "fair":
        score += 20
    if row.get("aerial_backyard_visibility") == "good":
        score += 35
    elif row.get("aerial_backyard_visibility") == "partial":
        score += 20
    if row.get("mls_drone_or_aerial") == "yes":
        score += 30
    if row.get("mls_backyard_photos") == "yes":
        score += 20
    if row.get("hot_tub_or_pool_signal") == "yes":
        score += 50
    elif row.get("hot_tub_or_pool_signal") == "unclear":
        score += 10
    if row.get("mls_candidate_strength") == "high":
        score += 15
    elif row.get("mls_candidate_strength") == "medium":
        score += 8
    if row.get("coordinate_confidence") == "unresolved":
        score -= 25
    return score


def main() -> None:
    aerial_rows = read_csv(TRIAGE_CSV)
    mls_summary = {r["listing_id"]: r for r in read_csv(MLS_SUMMARY_CSV)}
    mls_reviews = load_mls_reviews()

    cross_fields = [
        "listing_id", "address", "reason", "has_backyard_photos", "has_drone_or_aerial_photos",
        "hot_tub_or_pool_visible", "best_photo_indices", "marketing_candidate_strength", "reuse_rights", "notes",
    ]
    write_csv(CROSSCHECK_SUMMARY_CSV, list(mls_reviews.values()), cross_fields)

    rows: list[dict[str, object]] = []
    for r in aerial_rows:
        lid = r["listing_id"]
        ms = mls_summary.get(lid, {})
        mr = mls_reviews.get(lid, {})
        hot_signal = mr.get("hot_tub_or_pool_visible") or r.get("hot_tub_visible") or "unclear"
        best_source = "needs_review"
        if mr.get("has_drone_or_aerial_photos") == "yes":
            best_source = "mls_drone_or_aerial_candidate"
        elif r.get("overhead_quality") in {"good", "fair"} and r.get("backyard_visibility") in {"good", "partial"}:
            best_source = "arcgis_overhead_candidate"
        elif mr.get("has_backyard_photos") == "yes":
            best_source = "mls_backyard_candidate"
        elif r.get("review_status") == "blocked_no_aerial_imagery":
            best_source = "blocked_arcgis_no_imagery"
        elif r.get("coordinate_confidence") == "unresolved":
            best_source = "blocked_no_coordinate"

        row = {
            "listing_id": lid,
            "address": r["address"],
            "source_label": r["source_label"],
            "area": r.get("area", ""),
            "subarea": r.get("subarea", ""),
            "coordinate_confidence": r.get("coordinate_confidence", ""),
            "latitude": r.get("latitude", ""),
            "longitude": r.get("longitude", ""),
            "recommended_source": best_source,
            "best_overhead_candidate": r.get("best_overhead_candidate", ""),
            "aerial_contact_sheet": r.get("contact_sheet", ""),
            "aerial_review_status": r.get("review_status", ""),
            "aerial_backyard_visibility": r.get("backyard_visibility", ""),
            "aerial_overhead_quality": r.get("overhead_quality", ""),
            "aerial_real_tiles": r.get("aerial_real_tiles", ""),
            "aerial_placeholder_tiles": r.get("aerial_placeholder_tiles", ""),
            "mls_contact_sheet": ms.get("mls_contact_sheet", ""),
            "mls_photo_count": ms.get("downloaded_mls_thumbnails", r.get("mls_photo_count", "")),
            "mls_backyard_photos": mr.get("has_backyard_photos", "unreviewed"),
            "mls_drone_or_aerial": mr.get("has_drone_or_aerial_photos", "unreviewed"),
            "mls_best_photo_indices": mr.get("best_photo_indices", ""),
            "mls_candidate_strength": mr.get("marketing_candidate_strength", "unreviewed"),
            "hot_tub_or_pool_signal": hot_signal,
            "source_risk": "research_only_verify_license",
            "notes": "; ".join(x for x in [r.get("notes", ""), mr.get("notes", "")] if x),
        }
        row["triage_score"] = score_row(row)
        rows.append(row)

    rows.sort(key=lambda x: (-int(x["triage_score"]), x["address"]))
    for i, row in enumerate(rows, 1):
        row["triage_rank"] = i

    fields = [
        "triage_rank", "triage_score", "listing_id", "address", "source_label", "area", "subarea",
        "coordinate_confidence", "latitude", "longitude", "recommended_source", "best_overhead_candidate",
        "aerial_contact_sheet", "aerial_review_status", "aerial_backyard_visibility", "aerial_overhead_quality",
        "aerial_real_tiles", "aerial_placeholder_tiles", "mls_contact_sheet", "mls_photo_count",
        "mls_backyard_photos", "mls_drone_or_aerial", "mls_best_photo_indices", "mls_candidate_strength",
        "hot_tub_or_pool_signal", "source_risk", "notes",
    ]
    write_csv(OUT_CSV, rows, fields)
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)} and {OUT_JSON.relative_to(ROOT)}")
    print(f"MLS vision-reviewed listings: {len(mls_reviews)}")
    print("Top 10:")
    for row in rows[:10]:
        print(f"#{row['triage_rank']} score={row['triage_score']} {row['address']} [{row['recommended_source']}] hot_tub={row['hot_tub_or_pool_signal']} mls_aerial={row['mls_drone_or_aerial']}")


if __name__ == "__main__":
    main()
