# Tubs progress summary — 2026-04-29 20:48 PDT

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

5. **SeedVR/R2/deploy readiness**
   - SeedVR local assets: **857/857** present.
   - R2 upload completed: **857/857** objects uploaded to bucket `tubs` under prefix `seedvr-4x/`.
   - Public R2 image fetch verified: **200 image/jpeg** from `https://pub-f76325cc62ad4a85bd9b7eb123482f9c.r2.dev/seedvr-4x/...`.
   - `npm run build` passed with the public R2 SeedVR URL active.
   - GitHub is clean and pushed at `61ca293`.

## Current blocker / next best action

- No data/workflow blockers remain for the current to-do list.
- Next best action: verify the live deployed `tubs.b-average.com` build after deployment finishes, then spot-check a few review cards for R2-loaded SeedVR images and the new photo picker in editing mode.
