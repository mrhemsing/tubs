# Tubs progress summary - 2026-04-28

## Current counts

- Listings parsed: 300
- ArcGIS aerial tiles collected: 2,691
- Aerial contact sheets generated: 299/300
- Coordinate fallback repaired: 3/4 bad/missing coordinate listings
- Remaining coordinate blocker: `4827 HOLLAND Crescent`
- ArcGIS imagery availability check: 27 listings have real aerial tiles; 273 are all-placeholder/no usable ArcGIS imagery; 1 has no coordinate
- MLS thumbnails inventoried: 7,467
- MLS contact sheets generated: 299
- MLS contact sheets vision-reviewed so far: 22

## Consolidated triage output

Generated all-listing candidate table:

- `data/triage/property_candidate_triage.csv`
- `data/triage/property_candidate_triage.json`

Current recommended-source split:

- ArcGIS overhead candidates: 10
- MLS drone/aerial candidates: 4
- MLS backyard candidates: 16
- Blocked by ArcGIS no imagery: 229
- Still needs review: 40
- Blocked no coordinate: 1

## Best current candidates

Top ranked rows in `property_candidate_triage.csv`:

1. `75 103RD Avenue` - MLS backyard candidate; possible covered hot tub visible in photo 29; needs human verification.
2. `814 307TH Avenue` - MLS backyard candidate; hot tub clearly visible in photo 28 per vision pass; needs human verification.
3. `1265 VALLEY VIEW Place` - ArcGIS overhead candidate plus strong MLS backyard photos; no visible tub/pool.
4. `1681 KOOCANUSA LAKE Drive` - best ArcGIS overhead/backyard candidate from aerial pass.
5. `9382 MOYIE SHORES ESTATE Road` - ArcGIS overhead candidate plus strong waterfront MLS candidates; no visible tub/pool.

Current MLS drone/aerial candidates:

- `2543 LEDGEROCK Ridge`
- `4891 Glen Eagle Drive`
- `4992 MOUNTAIN VIEW Drive`
- `960 COPPER POINT Way`

## Blockers / cautions

- ArcGIS World Imagery is mostly unavailable for this property set at the collected zoom/area: most tiles are Esri placeholder images.
- MLS photos are inventoried for internal research only. Reuse rights remain unknown and must be verified before using or publishing any MLS image.
- Vision flags are triage, not final labels. Hot tub/pool positives should be human-verified at full resolution.

## Next best action

Continue MLS contact-sheet review for the remaining high-candidate / needs-review properties, then optionally add an alternate overhead imagery source if Matt wants more true top-down backyard coverage beyond the limited ArcGIS availability.
