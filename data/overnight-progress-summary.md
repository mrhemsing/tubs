# Tubs progress summary — 2026-04-29 20:03 PDT

## Heartbeat to-do status

1. **ArcGIS contact sheets**
   - Verified per-address ArcGIS aerial contact sheets for **300/300** listings.
   - Index: `data/contact_sheets/index.csv`
   - Sheets: `data/contact_sheets/<area>/<listing-folder>/aerial_contact_sheet.jpg`

2. **Geocode fallback**
   - Coordinate fallback/recollection pass remains clean.
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

5. **SeedVR/R2 status**
   - SeedVR local assets: **857/857** present.
   - R2 upload completed: **857/857** objects uploaded to bucket `tubs` under prefix `seedvr-4x/`.
   - GitHub is clean and pushed at `df3bff1`.

## Current blocker / next best action

- Need the bucket's **public** R2 URL (`*.r2.dev`) or a custom domain.
- The provided `https://ecef92aafc34f23688fc8d77f9486db7.r2.cloudflarestorage.com` endpoint is the private S3 API endpoint and returns an auth error for browser image loading.
- Once Matt provides the public URL, set `NEXT_PUBLIC_SEEDVR_BASE_URL` to that base and verify the review UI loads SeedVR images from R2.
