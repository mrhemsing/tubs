# Tubs progress summary - 2026-04-28

## Goal lock

Primary target: for each listed property, identify the **best available aerial/top-down/elevated photo(s) showing the house and backyard/lot together**.

Not the goal: hot tubs, pools, amenities, or ground-level backyard marketing photos except as secondary context.

## Current counts

- Listings parsed: 300
- ArcGIS aerial tiles collected: 2,691
- Aerial contact sheets generated: 299/300
- Coordinate fallback repaired: 3/4 bad/missing coordinate listings
- Remaining coordinate blocker: `4827 HOLLAND Crescent`
- ArcGIS imagery availability check: 27 listings have real aerial tiles; 273 are all-placeholder/no usable ArcGIS imagery; 1 has no coordinate
- MLS thumbnails inventoried: 7,467
- MLS contact sheets generated: 299
- MLS contact sheets reviewed for house+backyard aerial/elevated candidates so far: 72

## Corrected consolidated triage output

All-listing candidate table, ranked for house + backyard aerial/elevated coverage:

- `data/triage/property_candidate_triage.csv`
- `data/triage/property_candidate_triage.json`

Current recommended-source split:

- MLS drone/aerial candidates: 24
- ArcGIS overhead house+backyard candidates: 10
- Possible MLS elevated candidates needing verification: 7
- MLS ground backyard context only: 1
- Still needs aerial review: 34
- Blocked by ArcGIS no imagery: 223
- Blocked no coordinate: 1

## Current best aerial/elevated candidates

Top rows in the corrected ranking:

1. `1018 SWANSEA Road` - MLS aerial/top-down/oblique views; best photo indices `1,4,5,7,8,9,10,11`.
2. `1732 20TH S Avenue` - MLS drone/aerial candidate; best photo indices `1,2,3,4,5,6,7,9`.
3. `2510 COBBLESTONE Trail` - MLS drone/elevated candidate; best photo indices `1,2,3,4,8,9`.
4. `2543 LEDGEROCK Ridge` - MLS elevated/drone-style candidate; best photo indices `1,3,26,27,29,30`.
5. `4576 COLUMERE Road` - MLS aerial/elevated context; best photo indices `1,2,3,4,5,6,7,9,10`.
6. `4891 Glen Eagle Drive` - MLS drone/aerial candidate; best photo indices `1,4,5,23`.
7. `4992 MOUNTAIN VIEW Drive` - MLS aerial/property overview; best photo indices `1,17,18,19`.
8. `804 17TH S Street` - MLS overhead/aerial angles; best photo indices `1,2,4,5,7,8,9,15,16,19,20,21,22,24,25`.
9. `960 COPPER POINT Way` - MLS aerial/drone neighborhood/property context; best photo indices `7,6,3,5,1`.
10. `1681 KOOCANUSA LAKE Drive` - ArcGIS overhead house+backyard candidate.

New candidates from latest review batch:

- `1018 SWANSEA Road` - strong MLS aerial/top-down/oblique coverage.
- `1609 8TH S Avenue` - MLS elevated/aerial oblique, best photo indices `8,7,5`.
- `8042 MCINTOSH LOOP Road` - MLS aerial/top-down wooded lot view, best photo indices `4,5,14,16`.
- `921 11TH Avenue` - MLS elevated/aerial property/neighborhood view, best photo indices `4,24,25,26,27`.

Additional latest candidates:

- 224 Lindsay Street - clear elevated/top-down aerial; best photo index 3.
- 4824 MCKAY Street - strong vertical/top-down aerial; best photo indices 5,3,4.
- 941 5th Avenue - useful top-down aerial; best photo index 29.
- 1282 23RD S Street - elevated oblique aerial; best photo index 1.
- 1325 12 Avenue - medium elevated yard/lot coverage; best photo indices 11,12,19,20.
- 2904 Edgewood Drive - strong MLS aerial set; best photo indices 3,1,5,4.
- 1629 Staple Crescent - multiple MLS aerial/oblique views; best photo indices 5,2,3,1,4,6.
- 5221 Columbia River Road - wooded-lot aerial/elevated coverage; best photo indices 1,20,21.
- 1502 PINERIDGE MOUNTAIN Place - medium elevated/lot coverage; best photo indices 3,4,9,10,12,13.
- 815 LAKEVIEW MEADOWS GREEN - medium elevated yard/deck coverage; best photo indices 4,5,20.
- 21 MT MINTON Street - MLS elevated rear-lot views; best photo indices 29,30,28,1.
- Possible elevated/needs-verify: 862 10TH Avenue, 4942 MOUNTAIN HILL Road, 1059 SWANSEA Road.

## Blockers / cautions

- ArcGIS World Imagery is mostly unavailable for this property set at the collected zoom/area: most tiles are Esri placeholder images.
- MLS photos are inventoried for internal research only. Reuse rights remain unknown and must be verified before using or publishing any MLS image.
- MLS drone/aerial labels are vision-triage labels from contact sheets and should be verified at full resolution.

## Next best action

Continue MLS contact-sheet review specifically for true aerial/drone/elevated shots that capture house + backyard/lot together. If Matt wants broader top-down coverage for the 238 ArcGIS-blocked properties, add an alternate overhead imagery source.
