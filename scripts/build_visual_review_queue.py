#!/usr/bin/env python3
"""Build a human visual-review queue with direct links into the review UI."""
from __future__ import annotations

import csv
import re
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parents[1]
TRIAGE = ROOT / "data" / "triage" / "property_candidate_triage.csv"
OUT_CSV = ROOT / "data" / "triage" / "visual_review_queue.csv"
OUT_MD = ROOT / "data" / "triage" / "visual_review_queue.md"
OUT_HTML = ROOT / "public" / "visual-review-queue.html"

AREA_SLUGS = {
    "Columbia Valley": "columbia-valley",
    "Cranbrook/Kimberley": "cranbrook-kimberley",
    "Fernie/Sparwood": "fernie-sparwood",
}

SOURCE_LABELS = {
    "mls_drone_or_aerial_candidate": "Strong MLS aerial/elevated",
    "arcgis_overhead_house_backyard_candidate": "Strong ArcGIS overhead",
    "bing_overhead_house_backyard_candidate": "Strong Bing overhead",
    "google_overhead_house_backyard_candidate": "Strong Google overhead",
    "mapbox_overhead_house_backyard_candidate": "Strong Mapbox overhead",
    "possible_mls_elevated_candidate_needs_verify": "Possible MLS elevated - verify",
    "possible_bing_overhead_needs_verify": "Possible Bing overhead - verify",
    "possible_google_overhead_needs_verify": "Possible Google overhead - verify",
    "possible_mapbox_overhead_needs_verify": "Possible Mapbox overhead - verify",
    "mls_ground_backyard_context_only": "Ground backyard context only",
    "no_usable_aerial_candidate_after_full_review": "Photo not found",
}

PRIORITY_BASE = {
    "mls_drone_or_aerial_candidate": 1,
    "google_overhead_house_backyard_candidate": 2,
    "bing_overhead_house_backyard_candidate": 3,
    "arcgis_overhead_house_backyard_candidate": 4,
    "mapbox_overhead_house_backyard_candidate": 5,
    "possible_mls_elevated_candidate_needs_verify": 6,
    "possible_google_overhead_needs_verify": 7,
    "possible_bing_overhead_needs_verify": 8,
    "possible_mapbox_overhead_needs_verify": 9,
    "mls_ground_backyard_context_only": 10,
    "no_usable_aerial_candidate_after_full_review": 11,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def short_notes(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def priority_group(source: str) -> str:
    if source in {
        "mls_drone_or_aerial_candidate",
        "google_overhead_house_backyard_candidate",
        "bing_overhead_house_backyard_candidate",
        "arcgis_overhead_house_backyard_candidate",
        "mapbox_overhead_house_backyard_candidate",
    }:
        return "A - strong candidate"
    if source.startswith("possible_"):
        return "B - verify possible candidate"
    if source == "mls_ground_backyard_context_only":
        return "C - fallback context only"
    return "D - no usable candidate yet"


def main() -> None:
    rows = read_csv(TRIAGE)
    queue = []
    for row in rows:
        source = row["recommended_source"]
        area_slug = AREA_SLUGS[row["source_label"]]
        app_path = f"/{area_slug}#listing-{row['listing_id']}"
        review_reason = short_notes(row.get("notes", ""))
        queue.append({
            "review_order": 0,
            "priority_group": priority_group(source),
            "triage_rank": int(row["triage_rank"]),
            "triage_score": int(row["triage_score"]),
            "listing_id": row["listing_id"],
            "address": row["address"],
            "source_label": row["source_label"],
            "recommended_source": source,
            "recommended_label": SOURCE_LABELS.get(source, source),
            "coordinate_confidence": row.get("coordinate_confidence", ""),
            "best_photo_indices": row.get("mls_best_photo_indices", ""),
            "arcgis_real_tiles": row.get("aerial_real_tiles", ""),
            "arcgis_placeholder_tiles": row.get("aerial_placeholder_tiles", ""),
            "best_overhead_candidate": row.get("best_overhead_candidate", ""),
            "aerial_contact_sheet": row.get("aerial_contact_sheet", ""),
            "mls_contact_sheet": row.get("mls_contact_sheet", ""),
            "google_best_image": row.get("google_best_image", ""),
            "google_contact_sheet": row.get("google_contact_sheet", ""),
            "bing_contact_sheet": row.get("bing_contact_sheet", ""),
            "mapbox_contact_sheet": row.get("mapbox_contact_sheet", ""),
            "app_path": app_path,
            "review_reason": review_reason,
            "rights_note": "MLS/listing photos are research-only until rights are verified.",
        })

    queue.sort(key=lambda r: (PRIORITY_BASE.get(r["recommended_source"], 99), -r["triage_score"], r["triage_rank"]))
    for i, row in enumerate(queue, 1):
        row["review_order"] = i

    fields = [
        "review_order", "priority_group", "triage_rank", "triage_score", "listing_id", "address", "source_label",
        "recommended_source", "recommended_label", "coordinate_confidence", "best_photo_indices", "arcgis_real_tiles",
        "arcgis_placeholder_tiles", "best_overhead_candidate", "aerial_contact_sheet", "mls_contact_sheet",
        "google_best_image", "google_contact_sheet", "bing_contact_sheet", "mapbox_contact_sheet", "app_path",
        "review_reason", "rights_note",
    ]
    write_csv(OUT_CSV, queue, fields)

    strong = [r for r in queue if r["priority_group"] == "A - strong candidate"]
    possible = [r for r in queue if r["priority_group"] == "B - verify possible candidate"]
    fallback = [r for r in queue if r["priority_group"].startswith("C") or r["priority_group"].startswith("D")]

    lines = [
        "# Visual review queue",
        "",
        "Purpose: fastest human pass through the best overhead/backyard candidates, with direct anchors into the review UI.",
        "",
        f"- Total properties: **{len(queue)}**",
        f"- Strong candidates: **{len(strong)}**",
        f"- Possible candidates needing verification: **{len(possible)}**",
        f"- Fallback/no-candidate rows: **{len(fallback)}**",
        "- Rights note: MLS/listing photos are research-only until rights are verified.",
        "",
        "## First 40 to review",
        "",
        "| # | Address | Area | Candidate | Score | Best photos | Review link |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for row in queue[:40]:
        lines.append(
            f"| {row['review_order']} | {row['address']} | {row['source_label']} | {row['recommended_label']} | "
            f"{row['triage_score']} | {row['best_photo_indices'] or '—'} | `{row['app_path']}` |"
        )
    lines.extend(["", "Outputs:", f"- `{OUT_CSV.relative_to(ROOT)}`", f"- `{OUT_MD.relative_to(ROOT)}`"])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    source_options = "\n".join(
        f'<option value="{html.escape(source)}">{html.escape(label)}</option>'
        for source, label in sorted(SOURCE_LABELS.items(), key=lambda item: item[1])
    )
    area_options = "\n".join(
        f'<option value="{html.escape(area)}">{html.escape(area)}</option>'
        for area in sorted(AREA_SLUGS)
    )
    group_options = "\n".join(
        f'<option value="{html.escape(group)}">{html.escape(group)}</option>'
        for group in sorted({r["priority_group"] for r in queue})
    )
    table_rows = []
    for row in queue:
        text = " ".join([row["address"], row["listing_id"], row["source_label"], row["recommended_label"], row["review_reason"]]).lower()
        table_rows.append(f"""
          <tr data-group="{html.escape(row['priority_group'])}" data-area="{html.escape(row['source_label'])}" data-source="{html.escape(row['recommended_source'])}" data-text="{html.escape(text)}">
            <td>{row['review_order']}</td>
            <td><strong>{html.escape(row['address'])}</strong><span>MLS {html.escape(row['listing_id'])}</span></td>
            <td>{html.escape(row['source_label'])}</td>
            <td>{html.escape(row['recommended_label'])}</td>
            <td>{row['triage_score']}</td>
            <td>{html.escape(row['best_photo_indices'] or '-')}</td>
            <td>{html.escape(str(row['arcgis_real_tiles']))} / {html.escape(str(row['arcgis_placeholder_tiles']))}</td>
            <td><a href="{html.escape(row['app_path'])}">Open card</a></td>
            <td>{html.escape(row['review_reason'])}</td>
          </tr>
        """)
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Visual review queue</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fb; color: #172033; }}
    body {{ margin: 0; padding: 24px; }}
    .top {{ position: sticky; top: 0; z-index: 2; background: rgba(245,247,251,.94); backdrop-filter: blur(12px); border: 1px solid #d7dfec; border-radius: 18px; padding: 18px; margin-bottom: 18px; box-shadow: 0 12px 38px rgba(15,23,42,.08); }}
    h1 {{ margin: 0 0 8px; letter-spacing: -.03em; }}
    .summary {{ color: #52627a; margin: 0 0 14px; }}
    .filters {{ display: grid; grid-template-columns: minmax(220px, 1.5fr) minmax(170px,.75fr) minmax(190px,.8fr) minmax(220px,1fr); gap: 10px; }}
    input, select {{ width: 100%; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 12px; padding: 10px 12px; background: white; color: #172033; }}
    .tableWrap {{ overflow-x: auto; border: 1px solid #d7dfec; border-radius: 18px; background: white; box-shadow: 0 8px 26px rgba(15,23,42,.06); }}
    table {{ border-collapse: collapse; width: 100%; min-width: 1180px; font-size: 13px; }}
    th {{ text-align: left; background: #f8fbff; color: #64748b; text-transform: uppercase; letter-spacing: .055em; font-size: 11px; }}
    th, td {{ border-bottom: 1px solid #e5eaf2; padding: 10px 12px; vertical-align: top; }}
    tr:last-child td {{ border-bottom: 0; }}
    td span {{ display: block; color: #64748b; font-size: 12px; margin-top: 2px; }}
    a {{ color: #1d4ed8; font-weight: 800; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .hidden {{ display: none; }}
    @media (max-width: 860px) {{ body {{ padding: 12px; }} .top {{ position: static; }} .filters {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <section class="top">
    <h1>Visual review queue</h1>
    <p class="summary"><strong id="visibleCount">{len(queue)}</strong> / {len(queue)} properties · {len(strong)} strong · {len(possible)} possible verification · {len(fallback)} fallback/no-candidate · MLS photos are research-only until rights are verified.</p>
    <div class="filters">
      <input id="q" placeholder="Search address, MLS, notes..." />
      <select id="group"><option value="">All priority groups</option>{group_options}</select>
      <select id="area"><option value="">All areas</option>{area_options}</select>
      <select id="source"><option value="">All candidate types</option>{source_options}</select>
    </div>
  </section>
  <div class="tableWrap">
    <table>
      <thead><tr><th>#</th><th>Address</th><th>Area</th><th>Candidate</th><th>Score</th><th>Best MLS photos</th><th>ArcGIS real/placeholder</th><th>Review</th><th>Notes</th></tr></thead>
      <tbody id="rows">{''.join(table_rows)}</tbody>
    </table>
  </div>
  <script>
    const q = document.getElementById('q');
    const group = document.getElementById('group');
    const area = document.getElementById('area');
    const source = document.getElementById('source');
    const rows = [...document.querySelectorAll('tbody tr')];
    const count = document.getElementById('visibleCount');
    function apply() {{
      const query = q.value.trim().toLowerCase();
      let visible = 0;
      for (const row of rows) {{
        const ok = (!query || row.dataset.text.includes(query))
          && (!group.value || row.dataset.group === group.value)
          && (!area.value || row.dataset.area === area.value)
          && (!source.value || row.dataset.source === source.value);
        row.classList.toggle('hidden', !ok);
        if (ok) visible++;
      }}
      count.textContent = visible;
    }}
    [q, group, area, source].forEach((el) => el.addEventListener('input', apply));
  </script>
</body>
</html>
"""
    OUT_HTML.write_text(html_doc, encoding="utf-8")

    print(f"Wrote {OUT_CSV.relative_to(ROOT)} ({len(queue)} rows)")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"Wrote {OUT_HTML.relative_to(ROOT)}")
    print(f"Strong={len(strong)} possible={len(possible)} fallback/no-candidate={len(fallback)}")


if __name__ == "__main__":
    main()
