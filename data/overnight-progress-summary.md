# Tubs progress summary — 2026-04-29 18:08 PDT

## Completed heartbeat to-do pass

1. **ArcGIS contact sheets**
   - Generated/verified per-address ArcGIS aerial contact sheets for **300/300** listings.
   - Index: `data/contact_sheets/index.csv`
   - Sheets: `data/contact_sheets/<area>/<listing-folder>/aerial_contact_sheet.jpg`

2. **Geocode fallback**
   - Ran coordinate fallback/recollection pass.
   - Repaired: **0**
   - Unresolved: **0**
   - Current contact-sheet index reports **0** listings needing geocode fallback.

3. **Per-property triage/ranking table**
   - Rebuilt consolidated triage for **300/300** listings.
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
   - Downloaded/verified MLS thumbnails for **300/300** listings.
   - MLS thumbnails inventoried: **7,467**
   - Research-only outdoor/backyard/aerial proxy candidates: **6,603** photos across **299** listings.
   - Outputs:
     - `data/mls_photo_inventory/mls_photo_candidates.csv`
     - `data/mls_photo_inventory/mls_listing_summary.csv`
     - `data/mls_photo_inventory/README.md`
   - Reuse rights remain **unknown_research_only**.

## Current blocker

- Local commit `6f7ac96 Add full SeedVR 4x image batch` is still ahead of origin by 1.
- Normal `git push` failed twice with remote HTTP 500 while uploading the large SeedVR image batch (~3.4GB).
- Best next action: move SeedVR assets to Git LFS or external/static asset storage, then push code + indexes normally.
