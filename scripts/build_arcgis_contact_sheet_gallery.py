#!/usr/bin/env python3
"""Build a static all-property ArcGIS contact-sheet gallery for fast visual review."""
from __future__ import annotations

import csv
import html
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTACT_INDEX = ROOT / "data" / "contact_sheets" / "index.csv"
TRIAGE_CSV = ROOT / "data" / "triage" / "property_candidate_triage.csv"
PUBLIC = ROOT / "public"
OUT_DIR = PUBLIC / "arcgis-contact-sheets"
OUT_HTML = PUBLIC / "arcgis-contact-sheets.html"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "item"


def rel_public(path: Path) -> str:
    return path.relative_to(PUBLIC).as_posix()


def main() -> None:
    contact_rows = read_csv(CONTACT_INDEX)
    triage_rows = read_csv(TRIAGE_CSV)
    triage_by_id = {r["listing_id"]: r for r in triage_rows}

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    missing_sources: list[str] = []
    for i, c in enumerate(contact_rows, start=1):
        listing_id = c["listing_id"]
        t = triage_by_id.get(listing_id, {})
        rank = int(t.get("triage_rank") or i)
        base = f"{rank:03d}-{slug(c['address'])}-{listing_id}-arcgis-sheet.jpg"
        src = ROOT / c["contact_sheet"].replace("\\", "/")
        dest = OUT_DIR / base
        if src.exists():
            shutil.copy2(src, dest)
            image_url = rel_public(dest)
        else:
            missing_sources.append(str(src.relative_to(ROOT)))
            image_url = ""

        real_tiles = int(t.get("aerial_real_tiles") or 0)
        placeholder_tiles = int(t.get("aerial_placeholder_tiles") or 0)
        rows.append({
            "rank": rank,
            "listing_id": listing_id,
            "address": c["address"],
            "source_label": c["source_label"],
            "recommended_source": t.get("recommended_source", ""),
            "coordinate_confidence": t.get("coordinate_confidence", ""),
            "aerial_review_status": t.get("aerial_review_status", ""),
            "backyard_visibility": t.get("aerial_backyard_visibility", ""),
            "overhead_quality": t.get("aerial_overhead_quality", ""),
            "real_tiles": real_tiles,
            "placeholder_tiles": placeholder_tiles,
            "tile_count": int(c.get("aerial_tile_count") or 0),
            "needs_geocode_fallback": c.get("needs_geocode_fallback", ""),
            "image_url": image_url,
            "notes": t.get("notes", ""),
        })

    rows.sort(key=lambda r: (r["rank"], r["address"]))
    source_counts = Counter(r["source_label"] for r in rows)
    recommended_counts = Counter(r["recommended_source"] or "unknown" for r in rows)
    real_count = sum(1 for r in rows if r["real_tiles"] > 0)
    placeholder_only = sum(1 for r in rows if r["real_tiles"] == 0 and r["placeholder_tiles"] > 0)
    fallback_needed = sum(1 for r in rows if r["needs_geocode_fallback"])

    options_source = "\n".join(
        f'<option value="{html.escape(k)}">{html.escape(k)} ({v})</option>'
        for k, v in sorted(source_counts.items())
    )
    options_recommended = "\n".join(
        f'<option value="{html.escape(k)}">{html.escape(k)} ({v})</option>'
        for k, v in sorted(recommended_counts.items())
    )

    cards = []
    for r in rows:
        classes = []
        if r["real_tiles"] > 0:
            classes.append("real")
        elif r["placeholder_tiles"] > 0:
            classes.append("placeholder")
        else:
            classes.append("unknown")
        cards.append(f"""
        <article class="card {' '.join(classes)}" data-source="{html.escape(r['source_label'])}" data-recommended="{html.escape(r['recommended_source'] or 'unknown')}" data-text="{html.escape((r['address'] + ' ' + r['listing_id'] + ' ' + r['source_label']).lower())}">
          <header>
            <div class="rank">#{r['rank']:03d}</div>
            <div>
              <h2>{html.escape(r['address'])}</h2>
              <p>{html.escape(r['source_label'])} · MLS {html.escape(r['listing_id'])}</p>
            </div>
          </header>
          <a href="{html.escape(r['image_url'])}" target="_blank" rel="noreferrer">
            {f'<img src="{html.escape(r["image_url"])}" loading="lazy" alt="ArcGIS contact sheet for {html.escape(r["address"])}" />' if r['image_url'] else '<div class="missing">missing sheet</div>'}
          </a>
          <dl>
            <div><dt>Recommended</dt><dd>{html.escape(r['recommended_source'] or 'unknown')}</dd></div>
            <div><dt>ArcGIS status</dt><dd>{html.escape(r['aerial_review_status'] or 'unknown')}</dd></div>
            <div><dt>Visibility</dt><dd>{html.escape(r['backyard_visibility'] or 'unknown')}</dd></div>
            <div><dt>Quality</dt><dd>{html.escape(r['overhead_quality'] or 'unknown')}</dd></div>
            <div><dt>Tiles</dt><dd>{r['real_tiles']} real / {r['placeholder_tiles']} placeholder / {r['tile_count']} total</dd></div>
            <div><dt>Coords</dt><dd>{html.escape(r['coordinate_confidence'] or 'unknown')}</dd></div>
          </dl>
        </article>
        """)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ArcGIS contact sheet gallery</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0b1020; color: #e5ecff; }}
    body {{ margin: 0; padding: 24px; }}
    .top {{ position: sticky; top: 0; z-index: 2; background: rgba(11,16,32,.94); backdrop-filter: blur(12px); border: 1px solid #26324d; border-radius: 18px; padding: 18px; margin-bottom: 20px; box-shadow: 0 12px 40px rgba(0,0,0,.35); }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .summary {{ color: #aebde5; margin: 0 0 14px; }}
    .filters {{ display: grid; grid-template-columns: minmax(180px, 1.5fr) minmax(160px, .8fr) minmax(220px, 1fr) minmax(160px, .8fr); gap: 10px; }}
    input, select {{ width: 100%; box-sizing: border-box; background: #121a2f; color: #e5ecff; border: 1px solid #33415f; border-radius: 12px; padding: 10px 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }}
    .card {{ border: 1px solid #26324d; border-radius: 18px; overflow: hidden; background: #11182b; box-shadow: 0 8px 24px rgba(0,0,0,.25); }}
    .card.real {{ border-color: #236f52; }}
    .card.placeholder {{ border-color: #6f5523; }}
    header {{ display: grid; grid-template-columns: auto 1fr; gap: 12px; padding: 14px; align-items: center; }}
    .rank {{ font-weight: 800; color: #88f0c2; background: #142c28; border-radius: 999px; padding: 8px 10px; }}
    h2 {{ margin: 0; font-size: 16px; }}
    p {{ margin: 3px 0 0; color: #9fb0d6; font-size: 13px; }}
    img {{ display: block; width: 100%; aspect-ratio: 1.45 / 1; object-fit: cover; border-block: 1px solid #26324d; background: #080c16; }}
    .missing {{ min-height: 240px; display: grid; place-items: center; color: #ffb4b4; background: #261515; }}
    dl {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; padding: 14px; margin: 0; }}
    dt {{ font-size: 11px; color: #7f91bd; text-transform: uppercase; letter-spacing: .04em; }}
    dd {{ margin: 2px 0 0; font-size: 13px; color: #dbe6ff; overflow-wrap: anywhere; }}
    .hidden {{ display: none; }}
    @media (max-width: 820px) {{ body {{ padding: 12px; }} .filters {{ grid-template-columns: 1fr; }} .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <section class="top">
    <h1>ArcGIS contact sheet gallery</h1>
    <p class="summary"><strong id="visibleCount">{len(rows)}</strong> / {len(rows)} properties · {real_count} with real ArcGIS tiles · {placeholder_only} placeholder-only · {fallback_needed} needing geocode fallback · generated from data/contact_sheets/index.csv</p>
    <div class="filters">
      <input id="q" placeholder="Search address, MLS, area…" />
      <select id="source"><option value="">All areas</option>{options_source}</select>
      <select id="recommended"><option value="">All recommended sources</option>{options_recommended}</select>
      <select id="tileMode"><option value="">All ArcGIS tile states</option><option value="real">Has real ArcGIS tiles</option><option value="placeholder">Placeholder-only ArcGIS</option></select>
    </div>
  </section>
  <main class="grid" id="grid">
    {''.join(cards)}
  </main>
  <script>
    const q = document.getElementById('q');
    const source = document.getElementById('source');
    const recommended = document.getElementById('recommended');
    const tileMode = document.getElementById('tileMode');
    const cards = [...document.querySelectorAll('.card')];
    const count = document.getElementById('visibleCount');
    function apply() {{
      const query = q.value.trim().toLowerCase();
      let visible = 0;
      for (const card of cards) {{
        const ok = (!query || card.dataset.text.includes(query))
          && (!source.value || card.dataset.source === source.value)
          && (!recommended.value || card.dataset.recommended === recommended.value)
          && (!tileMode.value || card.classList.contains(tileMode.value));
        card.classList.toggle('hidden', !ok);
        if (ok) visible++;
      }}
      count.textContent = visible;
    }}
    [q, source, recommended, tileMode].forEach(el => el.addEventListener('input', apply));
  </script>
</body>
</html>
"""
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUT_HTML.relative_to(ROOT)}")
    print(f"Copied {len(list(OUT_DIR.glob('*.jpg')))} ArcGIS contact sheets to {OUT_DIR.relative_to(ROOT)}")
    print(f"Real ArcGIS tiles: {real_count}; placeholder-only: {placeholder_only}; geocode fallback needed: {fallback_needed}")
    if missing_sources:
        print("Missing source sheets:")
        for item in missing_sources:
            print(f"- {item}")


if __name__ == "__main__":
    main()
