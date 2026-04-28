#!/usr/bin/env python3
"""Build an HTML review page for aerial/elevated house+backyard candidates."""
from __future__ import annotations

import csv
import html
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAGE = ROOT / "data" / "triage" / "property_candidate_triage.csv"
MLS_PHOTOS = ROOT / "data" / "mls_photo_inventory" / "mls_photo_candidates.csv"
OUT = ROOT / "data" / "review" / "index.html"

KEEP_SOURCES = {
    "mls_drone_or_aerial_candidate",
    "arcgis_overhead_house_backyard_candidate",
    "possible_mls_elevated_candidate_needs_verify",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rel(path: str) -> str:
    if not path:
        return ""
    p = path.replace("\\", "/")
    return "../" + p.removeprefix("data/")


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def parse_indices(value: str) -> list[str]:
    out: list[str] = []
    for part in (value or "").replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit() and part not in out:
            out.append(part)
    return out


def badge(source: str) -> str:
    labels = {
        "mls_drone_or_aerial_candidate": "MLS aerial/elevated",
        "arcgis_overhead_house_backyard_candidate": "ArcGIS overhead",
        "possible_mls_elevated_candidate_needs_verify": "Possible elevated",
        "mls_ground_backyard_context_only": "Ground context only",
        "needs_aerial_review": "Needs review",
        "blocked_arcgis_no_imagery": "No ArcGIS imagery",
        "blocked_no_coordinate": "No coordinate",
    }
    return f'<span class="badge {esc(source)}">{esc(labels.get(source, source))}</span>'


def image_tag(src: str, alt: str, css: str = "") -> str:
    if not src:
        return ""
    return f'<a href="{esc(src)}"><img class="{esc(css)}" loading="lazy" src="{esc(src)}" alt="{esc(alt)}"></a>'


def main() -> None:
    rows = read_csv(TRIAGE)
    photos = read_csv(MLS_PHOTOS)
    photo_map: dict[tuple[str, str], str] = {}
    for p in photos:
        photo_map[(p["listing_id"], str(int(p["photo_index"])))] = p["local_path"]

    counts = Counter(r["recommended_source"] for r in rows)
    reviewed = sum(1 for r in rows if r["mls_drone_or_aerial"] != "unreviewed")
    candidate_rows = [r for r in rows if r["recommended_source"] in KEEP_SOURCES]

    cards: list[str] = []
    for r in candidate_rows:
        indices = parse_indices(r.get("mls_best_photo_indices", ""))
        thumbs = []
        for idx in indices[:8]:
            src = photo_map.get((r["listing_id"], idx))
            if src:
                thumbs.append(
                    f'<figure><div class="idx">#{esc(idx)}</div>{image_tag(rel(src), r["address"] + " photo " + idx, "thumb")}</figure>'
                )
        if not thumbs and r.get("best_overhead_candidate"):
            thumbs.append(
                f'<figure><div class="idx">ArcGIS</div>{image_tag(rel(r["best_overhead_candidate"]), r["address"] + " ArcGIS overhead", "thumb")}</figure>'
            )

        contact_links = []
        if r.get("mls_contact_sheet"):
            contact_links.append(f'<a href="{esc(rel(r["mls_contact_sheet"]))}">MLS contact sheet</a>')
        if r.get("aerial_contact_sheet"):
            contact_links.append(f'<a href="{esc(rel(r["aerial_contact_sheet"]))}">ArcGIS contact sheet</a>')
        if r.get("best_overhead_candidate"):
            contact_links.append(f'<a href="{esc(rel(r["best_overhead_candidate"]))}">Best ArcGIS tile</a>')

        cards.append(f"""
        <article class="card {esc(r['recommended_source'])}">
          <header>
            <div class="rank">#{esc(r['triage_rank'])}</div>
            <div>
              <h2>{esc(r['address'])}</h2>
              <div class="meta">MLS/List ID {esc(r['listing_id'])} · {esc(r['source_label'])} · score {esc(r['triage_score'])}</div>
            </div>
            {badge(r['recommended_source'])}
          </header>
          <div class="details">
            <div><b>Best photo indices:</b> {esc(r.get('mls_best_photo_indices') or '—')}</div>
            <div><b>Coverage:</b> {esc(r.get('aerial_coverage_goal'))}</div>
            <div><b>Coordinate confidence:</b> {esc(r.get('coordinate_confidence'))}</div>
            <div><b>ArcGIS real/placeholder tiles:</b> {esc(r.get('aerial_real_tiles'))}/{esc(r.get('aerial_placeholder_tiles'))}</div>
          </div>
          <p class="notes">{esc(r.get('notes'))}</p>
          <nav>{' · '.join(contact_links)}</nav>
          <div class="thumbs">{''.join(thumbs)}</div>
        </article>
        """)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tubs aerial/elevated property review</title>
<style>
:root {{ color-scheme: light; --bg:#f7f8fb; --card:#fff; --ink:#15202b; --muted:#64748b; --line:#dbe3ef; --blue:#1d4ed8; }}
body {{ margin:0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; background:var(--bg); color:var(--ink); }}
.top {{ position:sticky; top:0; z-index:2; background:rgba(247,248,251,.96); border-bottom:1px solid var(--line); padding:18px 24px; backdrop-filter: blur(6px); }}
h1 {{ margin:0 0 6px; font-size:24px; }}
.summary {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
.pill {{ background:#e8eef9; border:1px solid #d5deef; padding:6px 10px; border-radius:999px; font-size:13px; }}
main {{ padding:20px 24px 48px; max-width:1400px; margin:auto; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:16px; margin:0 0 18px; box-shadow:0 2px 10px rgba(15,23,42,.04); }}
header {{ display:flex; align-items:flex-start; gap:12px; }}
h2 {{ margin:0; font-size:20px; }}
.rank {{ font-weight:800; color:var(--blue); min-width:46px; }}
.meta, .details, .notes, nav {{ color:var(--muted); font-size:13px; }}
.details {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:6px 18px; margin:12px 0; }}
.notes {{ line-height:1.45; }}
.badge {{ margin-left:auto; white-space:nowrap; border-radius:999px; padding:6px 10px; font-size:12px; font-weight:700; background:#e0f2fe; color:#075985; }}
.badge.arcgis_overhead_house_backyard_candidate {{ background:#dcfce7; color:#166534; }}
.badge.possible_mls_elevated_candidate_needs_verify {{ background:#fef3c7; color:#92400e; }}
a {{ color:var(--blue); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.thumbs {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap:10px; margin-top:14px; }}
figure {{ margin:0; position:relative; border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#f1f5f9; min-height:110px; }}
.thumb {{ width:100%; height:150px; object-fit:cover; display:block; }}
.idx {{ position:absolute; top:6px; left:6px; background:rgba(15,23,42,.82); color:white; border-radius:999px; padding:3px 7px; font-size:12px; font-weight:700; z-index:1; }}
.footer {{ color:var(--muted); font-size:12px; margin-top:28px; }}
</style>
</head>
<body>
<section class="top">
  <h1>Tubs aerial/elevated property review</h1>
  <div class="meta">Goal: best available aerial/top-down/elevated photos showing house + backyard/lot together. MLS rights are unknown/research-only.</div>
  <div class="summary">
    <span class="pill">Properties: {len(rows)}</span>
    <span class="pill">MLS reviewed: {reviewed}</span>
    <span class="pill">MLS aerial/elevated: {counts['mls_drone_or_aerial_candidate']}</span>
    <span class="pill">ArcGIS overhead: {counts['arcgis_overhead_house_backyard_candidate']}</span>
    <span class="pill">Possible elevated: {counts['possible_mls_elevated_candidate_needs_verify']}</span>
    <span class="pill">Needs review: {counts['needs_aerial_review']}</span>
    <span class="pill">ArcGIS no imagery: {counts['blocked_arcgis_no_imagery']}</span>
  </div>
</section>
<main>
  {''.join(cards)}
  <div class="footer">Generated by scripts/build_review_page.py from data/triage/property_candidate_triage.csv.</div>
</main>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(candidate_rows)} candidate cards")


if __name__ == "__main__":
    main()
