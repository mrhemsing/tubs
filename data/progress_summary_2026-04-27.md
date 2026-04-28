# Tubs overnight progress summary — 2026-04-27

## Goal

Collect the best available top-down/aerial backyard photo candidates for each property from Matt's three Xposure listing links.

## Shipped

- Parsed all three source lists into structured data.
- Built aerial tile collection from ArcGIS World Imagery.
- Generated per-address aerial contact sheets for fast review.
- Added geocode fallback for bad/missing coordinates.
- Built a property-level aerial triage table.
- Inventoried MLS/listing photos as research-only candidates.

## Current counts

- Listings parsed: **300**
- Aerial tiles collected: **2,691**
- Properties with aerial contact sheets / ready for review: **299 / 300**
- Blocked/no-coordinate property: **1** — `4827 HOLLAND Crescent`
- MLS thumbnails downloaded/verified: **7,467**
- MLS thumbnails flagged by rough outdoor/backyard/aerial proxy: **6,603**

## Key outputs

- `data/listings.csv`
- `data/triage/property_aerial_triage.csv`
- `data/contact_sheets/` *(generated locally, ignored by git)*
- `data/mls_photo_inventory/mls_listing_summary.csv`
- `data/mls_photo_inventory/top_mls_photo_candidates_by_listing.csv`
- `data/mls_contact_sheets/` *(generated locally, ignored by git)*

## Blockers / cautions

- `4827 HOLLAND Crescent` still needs manual parcel lookup or a better source. Public geocoders returned wrong/locality-only matches.
- MLS/listing photos are marked `unknown_research_only`; finding candidates is not permission to reuse them in print.
- ArcGIS/Esri imagery licensing still needs confirmation before using exported imagery in marketing.

## Next best action

Run vision/human triage on the highest-priority candidate sheets to mark:

- backyard visible
- usable top-down crop
- likely hot tub / pool / outdoor amenity
- quality good enough for print mockup
- source risk / rights follow-up needed

Recommended next milestone: review the top 50 aerial triage rows first, then use MLS contact sheets to find true drone/backyard angles where the overhead tiles are weak.
