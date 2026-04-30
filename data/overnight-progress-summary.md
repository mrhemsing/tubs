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

## Current blocker / next best action

- No blockers remain for the current to-do list.
- Next best action: Matt should visually spot-check a few live cards and open **Edit tub layer** to choose photos in the new editor picker; browser automation click verification is unavailable in this gateway build because Playwright act support is missing.
