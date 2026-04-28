# Tubs progress summary - 2026-04-28

## Goal correction

Matt clarified the target: prioritize **aerial/top-down or elevated shots that show the house and backyard together**. Hot tubs/pools are not the objective and should not drive ranking. They remain only incidental notes if visible while reviewing imagery.

## Current counts

- Listings parsed: 300
- ArcGIS aerial tiles collected: 2,691
- Aerial contact sheets generated: 299/300
- Coordinate fallback repaired: 3/4 bad/missing coordinate listings
- Remaining coordinate blocker: `4827 HOLLAND Crescent`
- ArcGIS imagery availability check: 27 listings have real aerial tiles; 273 are all-placeholder/no usable ArcGIS imagery; 1 has no coordinate
- MLS thumbnails inventoried: 7,467
- MLS contact sheets generated: 299
- MLS contact sheets vision-reviewed so far: 32

## Corrected consolidated triage output

Regenerated all-listing candidate table with ranking focused on house + backyard aerial/elevated coverage:

- `data/triage/property_candidate_triage.csv`
- `data/triage/property_candidate_triage.json`

Current recommended-source split:

- MLS drone/aerial candidates: 8
- ArcGIS overhead house+backyard candidates: 10
- Possible MLS elevated candidate needing verification: 1
- MLS ground backyard context only: 1
- Still needs aerial review: 38
- Blocked by ArcGIS no imagery: 241
- Blocked no coordinate: 1

## Current best aerial/elevated candidates

Top rows in the corrected ranking:

1. `1732 20TH S Avenue` - MLS drone/aerial candidate, likely house + backyard elevated context.
2. `2510 COBBLESTONE Trail` - MLS drone/aerial candidate, likely house + backyard elevated context.
3. `2543 LEDGEROCK Ridge` - MLS drone/aerial candidate, likely house + backyard elevated context.
4. `4576 COLUMERE Road` - MLS drone/aerial candidate, likely house + backyard elevated context.
5. `4891 Glen Eagle Drive` - MLS drone/aerial candidate, likely house + backyard elevated context.
6. `4992 MOUNTAIN VIEW Drive` - MLS drone/aerial candidate, likely house + backyard elevated context.
7. `804 17TH S Street` - MLS drone/aerial candidate, likely house + backyard elevated context.
8. `960 COPPER POINT Way` - MLS drone/aerial candidate, likely house + backyard elevated context.
9. `1681 KOOCANUSA LAKE Drive` - ArcGIS overhead house+backyard candidate.
10. `1643 Koocanusa Lake Drive` - ArcGIS overhead house+backyard candidate.

## Blockers / cautions

- ArcGIS World Imagery is mostly unavailable for this property set at the collected zoom/area: most tiles are Esri placeholder images.
- MLS photos are inventoried for internal research only. Reuse rights remain unknown and must be verified before using or publishing any MLS image.
- MLS drone/aerial labels are vision-triage labels from contact sheets and should be verified at full resolution.

## Next best action

Continue MLS contact-sheet review specifically for **true aerial/drone/elevated shots that capture house + backyard together**, not amenity detection. If Matt wants broader top-down coverage, add an alternate overhead imagery source because ArcGIS coverage is sparse here.
