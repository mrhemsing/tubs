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
BING_INDEX_CSV = ROOT / "data" / "alternate_contact_sheets" / "bing" / "index.csv"
BING_REVIEW_DIR = ROOT / "data" / "alternate_contact_sheets" / "bing"
MAPBOX_INDEX_CSV = ROOT / "data" / "alternate_contact_sheets" / "mapbox" / "index.csv"
MAPBOX_REVIEW_DIR = ROOT / "data" / "alternate_contact_sheets" / "mapbox"
GOOGLE_INDEX_CSV = ROOT / "data" / "alternate_contact_sheets" / "google" / "index.csv"
GOOGLE_REVIEW_DIR = ROOT / "data" / "alternate_contact_sheets" / "google"


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


def load_bing_reviews() -> dict[str, dict[str, object]]:
    reviews: dict[str, dict[str, object]] = {}
    if not BING_INDEX_CSV.exists():
        return reviews
    index = {r["listing_id"]: r for r in read_csv(BING_INDEX_CSV)}
    for p in sorted(BING_REVIEW_DIR.glob("bing_review_batch_*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for item in data:
            lid = str(item["listing_id"])
            reviews[lid] = {
                "listing_id": lid,
                "address": item.get("address", ""),
                "has_useful_bing_overhead": item.get("has_useful_bing_overhead", "unclear"),
                "best_tile_position": item.get("best_tile_position", ""),
                "coverage_strength": item.get("coverage_strength", "unclear"),
                "notes": item.get("notes", ""),
                "bing_contact_sheet": index.get(lid, {}).get("bing_contact_sheet", ""),
                "bing_tile_count": index.get(lid, {}).get("bing_tile_count", ""),
            }
    return reviews


def load_mapbox_reviews() -> dict[str, dict[str, object]]:
    reviews: dict[str, dict[str, object]] = {}
    if not MAPBOX_INDEX_CSV.exists():
        return reviews
    index = {r["listing_id"]: r for r in read_csv(MAPBOX_INDEX_CSV)}
    for p in sorted(MAPBOX_REVIEW_DIR.glob("mapbox_review_batch_*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for item in data:
            lid = str(item["listing_id"])
            reviews[lid] = {
                "listing_id": lid,
                "address": item.get("address", ""),
                "has_useful_mapbox_overhead": item.get("has_useful_mapbox_overhead", "unclear"),
                "best_tile_position": item.get("best_tile_position", ""),
                "coverage_strength": item.get("coverage_strength", "unclear"),
                "notes": item.get("notes", ""),
                "mapbox_contact_sheet": index.get(lid, {}).get("mapbox_contact_sheet", ""),
                "mapbox_tile_count": index.get(lid, {}).get("mapbox_tile_count", ""),
            }
    return reviews


def load_google_reviews() -> dict[str, dict[str, object]]:
    reviews: dict[str, dict[str, object]] = {}
    if not GOOGLE_INDEX_CSV.exists():
        return reviews
    index = {r["listing_id"]: r for r in read_csv(GOOGLE_INDEX_CSV)}
    for p in sorted(GOOGLE_REVIEW_DIR.glob("google_review_batch_*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for item in data:
            lid = str(item["listing_id"])
            reviews[lid] = {
                "listing_id": lid,
                "address": item.get("address", ""),
                "has_useful_google_overhead": item.get("has_useful_google_overhead", "unclear"),
                "best_zoom": item.get("best_zoom", ""),
                "coverage_strength": item.get("coverage_strength", "unclear"),
                "notes": item.get("notes", ""),
                "google_contact_sheet": index.get(lid, {}).get("google_contact_sheet", ""),
                "google_image_count": index.get(lid, {}).get("google_image_count", ""),
                "google_image_z20": index.get(lid, {}).get("google_image_z20", ""),
                "google_image_z19": index.get(lid, {}).get("google_image_z19", ""),
                "google_image_z18": index.get(lid, {}).get("google_image_z18", ""),
            }
    return reviews


def score_row(row: dict[str, object]) -> int:
    """Rank for Matt's goal: aerial/elevated views showing house + backyard together."""
    score = 0
    aerial_quality = row.get("aerial_overhead_quality", "")
    backyard_visibility = row.get("aerial_backyard_visibility", "")

    # True overhead/aerial evidence is the main objective.
    if row.get("mls_drone_or_aerial") == "yes":
        score += 110
    elif row.get("mls_drone_or_aerial") == "unclear":
        score += 25

    if row.get("bing_overhead") == "yes":
        score += 62
    elif row.get("bing_overhead") == "unclear":
        score += 18

    if row.get("google_overhead") == "yes":
        score += 25
    elif row.get("google_overhead") == "unclear":
        score += 18

    if row.get("mapbox_overhead") == "yes":
        score += 20
    elif row.get("mapbox_overhead") == "unclear":
        score += 16

    if aerial_quality == "good":
        score += 45
    elif aerial_quality == "fair":
        score += 28

    if backyard_visibility == "good":
        score += 40
    elif backyard_visibility == "partial":
        score += 24

    # MLS ground-level backyard photos are useful context, but not the target.
    if row.get("mls_backyard_photos") == "yes":
        score += 8
    if row.get("mls_candidate_strength") == "high":
        score += 8
    elif row.get("mls_candidate_strength") == "medium":
        score += 4

    # Hot tub/pool is retained only as a secondary note, not a ranking driver.
    if row.get("coordinate_confidence") == "unresolved":
        score -= 25
    return score


def main() -> None:
    aerial_rows = read_csv(TRIAGE_CSV)
    mls_summary = {r["listing_id"]: r for r in read_csv(MLS_SUMMARY_CSV)}
    mls_reviews = load_mls_reviews()
    bing_reviews = load_bing_reviews()
    mapbox_reviews = load_mapbox_reviews()
    google_reviews = load_google_reviews()

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
        br = bing_reviews.get(lid, {})
        mb = mapbox_reviews.get(lid, {})
        gr = google_reviews.get(lid, {})
        hot_signal = mr.get("hot_tub_or_pool_visible") or r.get("hot_tub_visible") or "unclear"
        has_arcgis_house_backyard = r.get("overhead_quality") in {"good", "fair"} and r.get("backyard_visibility") in {"good", "partial"}
        best_source = "needs_aerial_review"
        aerial_coverage_goal = "unreviewed"
        if mr.get("has_drone_or_aerial_photos") == "yes":
            best_source = "mls_drone_or_aerial_candidate"
            aerial_coverage_goal = "likely_house_and_backyard_elevated_context"
        elif has_arcgis_house_backyard:
            best_source = "arcgis_overhead_house_backyard_candidate"
            aerial_coverage_goal = "likely_house_and_backyard_overhead"
        elif br.get("has_useful_bing_overhead") == "yes":
            best_source = "bing_overhead_house_backyard_candidate"
            aerial_coverage_goal = "likely_house_and_backyard_bing_overhead"
        elif gr.get("has_useful_google_overhead") == "yes":
            best_source = "google_overhead_house_backyard_candidate"
            aerial_coverage_goal = "likely_house_and_backyard_google_overhead"
        elif mb.get("has_useful_mapbox_overhead") == "yes":
            best_source = "mapbox_overhead_house_backyard_candidate"
            aerial_coverage_goal = "likely_house_and_backyard_mapbox_overhead"
        elif mr.get("has_drone_or_aerial_photos") == "unclear":
            best_source = "possible_mls_elevated_candidate_needs_verify"
            aerial_coverage_goal = "possible_elevated_context_needs_verify"
        elif br.get("has_useful_bing_overhead") == "unclear":
            best_source = "possible_bing_overhead_needs_verify"
            aerial_coverage_goal = "possible_bing_overhead_needs_verify"
        elif gr.get("has_useful_google_overhead") == "unclear":
            best_source = "possible_google_overhead_needs_verify"
            aerial_coverage_goal = "possible_google_overhead_needs_verify"
        elif mb.get("has_useful_mapbox_overhead") == "unclear":
            best_source = "possible_mapbox_overhead_needs_verify"
            aerial_coverage_goal = "possible_mapbox_overhead_needs_verify"
        elif r.get("coordinate_confidence") == "unresolved":
            best_source = "blocked_no_coordinate"
            aerial_coverage_goal = "no_coordinate_for_overhead_collection"
        elif (
            r.get("review_status") == "blocked_no_aerial_imagery"
            and mr.get("has_drone_or_aerial_photos") == "no"
            and br.get("has_useful_bing_overhead") == "no"
            and gr.get("has_useful_google_overhead") == "no"
        ):
            best_source = "no_usable_aerial_candidate_after_full_review"
            aerial_coverage_goal = "reviewed_no_house_backyard_overhead_found"
        elif r.get("review_status") == "blocked_no_aerial_imagery":
            best_source = "blocked_arcgis_no_imagery"
            aerial_coverage_goal = "no_arcgis_overhead_available"
        elif mr.get("has_backyard_photos") == "yes":
            best_source = "mls_ground_backyard_context_only"
            aerial_coverage_goal = "ground_context_not_aerial"

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
            "aerial_coverage_goal": aerial_coverage_goal,
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
            "bing_overhead": br.get("has_useful_bing_overhead", "unreviewed"),
            "bing_contact_sheet": br.get("bing_contact_sheet", ""),
            "bing_tile_count": br.get("bing_tile_count", ""),
            "bing_best_tile_position": br.get("best_tile_position", ""),
            "bing_coverage_strength": br.get("coverage_strength", "unreviewed"),
            "google_overhead": gr.get("has_useful_google_overhead", "unreviewed"),
            "google_contact_sheet": gr.get("google_contact_sheet", ""),
            "google_image_count": gr.get("google_image_count", ""),
            "google_best_zoom": gr.get("best_zoom", ""),
            "google_best_image": gr.get(f"google_image_z{gr.get('best_zoom', '')}", ""),
            "google_coverage_strength": gr.get("coverage_strength", "unreviewed"),
            "mapbox_overhead": mb.get("has_useful_mapbox_overhead", "unreviewed"),
            "mapbox_contact_sheet": mb.get("mapbox_contact_sheet", ""),
            "mapbox_tile_count": mb.get("mapbox_tile_count", ""),
            "mapbox_best_tile_position": mb.get("best_tile_position", ""),
            "mapbox_coverage_strength": mb.get("coverage_strength", "unreviewed"),
            "hot_tub_or_pool_signal": hot_signal,
            "source_risk": "research_only_verify_license",
            "notes": "; ".join(x for x in [r.get("notes", ""), mr.get("notes", ""), br.get("notes", ""), gr.get("notes", ""), mb.get("notes", "")] if x),
        }
        row["triage_score"] = score_row(row)
        rows.append(row)

    rows.sort(key=lambda x: (-int(x["triage_score"]), x["address"]))
    for i, row in enumerate(rows, 1):
        row["triage_rank"] = i

    fields = [
        "triage_rank", "triage_score", "listing_id", "address", "source_label", "area", "subarea",
        "coordinate_confidence", "latitude", "longitude", "recommended_source", "aerial_coverage_goal", "best_overhead_candidate",
        "aerial_contact_sheet", "aerial_review_status", "aerial_backyard_visibility", "aerial_overhead_quality",
        "aerial_real_tiles", "aerial_placeholder_tiles", "mls_contact_sheet", "mls_photo_count",
        "mls_backyard_photos", "mls_drone_or_aerial", "mls_best_photo_indices", "mls_candidate_strength",
        "bing_overhead", "bing_contact_sheet", "bing_tile_count", "bing_best_tile_position", "bing_coverage_strength",
        "google_overhead", "google_contact_sheet", "google_image_count", "google_best_zoom", "google_best_image", "google_coverage_strength",
        "mapbox_overhead", "mapbox_contact_sheet", "mapbox_tile_count", "mapbox_best_tile_position", "mapbox_coverage_strength",
        "hot_tub_or_pool_signal", "source_risk", "notes",
    ]
    write_csv(OUT_CSV, rows, fields)
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)} and {OUT_JSON.relative_to(ROOT)}")
    print(f"MLS vision-reviewed listings: {len(mls_reviews)}")
    print("Top 10:")
    for row in rows[:10]:
        print(f"#{row['triage_rank']} score={row['triage_score']} {row['address']} [{row['recommended_source']}] coverage={row['aerial_coverage_goal']} mls_aerial={row['mls_drone_or_aerial']}")


if __name__ == "__main__":
    main()
