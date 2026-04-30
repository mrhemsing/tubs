# Tubs progress summary — 2026-04-29 21:33 PDT

## Heartbeat to-do status

1. **ArcGIS contact sheets**
   - Verified per-address ArcGIS aerial contact sheets for **300/300** listings.
   - Index: `data/contact_sheets/index.csv`
   - Sheets: `data/contact_sheets/<area>/<listing-folder>/aerial_contact_sheet.jpg`

2. **Geocode fallback**
   - Coordinate fallback/recollection remains clean.
   - Repaired: **0**
   - Unresolved: **0**
   - Contact-sheet index reports **0** listings needing geocode fallback.

3. **Per-property triage/ranking table**
   - Consolidated triage covers **300/300** listings.
   - Outputs:
     - `data/triage/property_candidate_triage.csv`
     - `data/triage/property_candidate_triage.json`
   - Recommended source counts:
     - MLS aerial/elevated: **49**
     - Google overhead: **174**
     - Bing overhead: **15**
     - ArcGIS overhead: **10**
     - Mapbox overhead: **3**
     - Possible MLS elevated: **18**
     - Possible Bing overhead: **7**
     - Possible Google overhead: **18**
     - Ground context only: **4**
     - Photo not found: **2**
   - Coordinate unresolved: **0**

4. **MLS photo manifest/inventory**
   - MLS thumbnails inventoried for **300/300** listings.
   - MLS thumbnails: **7,467**
   - Research-only outdoor/backyard/aerial proxy candidates: **6,603** photos across **299** listings.
   - Outputs:
     - `data/mls_photo_inventory/mls_photo_candidates.csv`
     - `data/mls_photo_inventory/mls_listing_summary.csv`
     - `data/mls_photo_inventory/README.md`
   - Reuse rights remain **unknown_research_only**.

5. **Live site / SeedVR R2 verification**
   - GitHub is clean and pushed.
   - Live `https://tubs.b-average.com/` returns **200**.
   - Live `https://tubs.b-average.com/columbia-valley` returns **200** and contains the public R2 SeedVR URL.
   - Browser snapshot confirms visible review cards label active **SeedVR 4x** assets and show **215 SeedVR 4x images active** for Columbia Valley.
   - Public R2 sample image fetch still returns **200 image/jpeg**.
   - `npm run build` passed locally with `.env.local` active.

6. **ArcGIS contact-sheet gallery**
   - Added a fast visual review gallery for all **300/300** per-address ArcGIS sheets.
   - Output: `public/arcgis-contact-sheets.html`
   - Copied public sheet assets: `public/arcgis-contact-sheets/*.jpg`
   - Filterable by area, recommended source, text search, and ArcGIS tile state.
   - Current ArcGIS tile-state counts: **27** listings with real ArcGIS tiles; **273** placeholder-only; **0** needing geocode fallback.
   - Build check: `npm run build` passed.
   - Later heartbeat linked the gallery from the sticky area navigation as **ArcGIS sheet gallery** for one-click access from the live review UI.

7. **Current progress audit artifacts**
   - Added repeatable audit script: `scripts/build_progress_audit.py`
   - Outputs:
     - `data/progress_summary_2026-04-30.md`
     - `data/triage/current_progress_audit.json`
     - `data/triage/current_progress_by_area.csv`
   - Latest audit confirms **300** properties triaged, **300** ArcGIS sheets indexed, **300** public gallery sheets, **0** geocode fallback needed, **7,467** MLS thumbnails, **6,603** proxy outdoor/backyard/aerial candidates across **299** listings, and **no blockers**.
   - Area rollup: Columbia Valley **0/100** real ArcGIS tile properties, Cranbrook/Kimberley **4/100**, Fernie/Sparwood **23/100**.
   - Build check: `npm run build` passed after audit generation.

8. **Visual review queue**
   - Added direct card anchors in the review UI (`/[area]#listing-<MLS id>`) so checklist rows can jump straight to candidate cards.
   - Added repeatable queue script: `scripts/build_visual_review_queue.py`
   - Outputs:
     - `data/triage/visual_review_queue.csv`
     - `data/triage/visual_review_queue.md`
   - Queue covers **300** properties: **251** strong candidates, **43** possible candidates needing verification, and **6** fallback/no-candidate rows.
   - The markdown queue lists the first **40** fastest human review targets with area, candidate label, score, best MLS photo indices, and direct review anchor.
   - Build check: `npm run build` passed after adding anchors and regenerating artifacts.
   - Later heartbeat added a public filterable queue page: `public/visual-review-queue.html`, linked from the review UI sticky nav as **Visual review queue**.
   - The queue page supports text search plus priority group, area, and candidate-type filters; rows open directly to `/<area>#listing-<MLS id>` cards.
   - Build check: `npm run build` passed after adding the public queue page/link.

## Current blocker / next best action

- No blockers remain for the current to-do list.
- Next best action: Matt should visually spot-check the linked **ArcGIS sheet gallery** plus a few live review cards, then open **Edit tub layer** to choose photos in the new editor picker; browser automation click verification is unavailable in this gateway build because Playwright act support is missing.
