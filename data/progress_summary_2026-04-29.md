# Tubs aerial review progress — 2026-04-29

## Current state

- Total properties: **300**
- Public candidate cards: **275**
- MLS contact sheets reviewed: **172**
- Google Static Maps satellite sheets indexed/reviewed: **216 / 216**
- Next.js build: passing after latest data refresh

## Candidate source split

- **174** Google overhead candidates
- **48** MLS aerial/elevated candidates
- **18** possible MLS elevated candidates needing verification
- **18** possible Google overhead candidates needing verification
- **10** ArcGIS overhead candidates
- **7** Bing overhead candidates
- **3** Mapbox raw-source candidates remain in triage, but Mapbox cards are intentionally suppressed because quality was judged weak
- **2** MLS ground-context-only

## Remaining blockers / gaps

- **17** properties still have ArcGIS overhead unavailable and no promoted Google/Bing/MLS overhead candidate.
- **2** properties still need aerial review:
  - `1 BIGHORN SHEEP Lane`
  - `2527 LEDGEROCK Ridge`
- **1** coordinate blocker remains:
  - `4827 HOLLAND Crescent` — currently has bad/out-of-region coordinates and needs parcel/manual/geocode correction.
- Several no-candidate rows appear to have bad or ambiguous listing coordinates, repeated coordinates, dense canopy, vacant/roadside geocodes, or no visible house at the supplied point.

## Decisions / notes

- Google is now the primary fallback source after MLS/ArcGIS/Bing because it generally gives better resolution than Mapbox.
- Visible Google cards use the single best reviewed zoom image, not the 3-panel diagnostic sheet.
- Google contact sheets are still exported as QA/detail links.
- Imagery remains research/internal; Google licensing/attribution/caching rules still need resolution before public/commercial reuse.

## Next best action

1. Fix bad/ambiguous coordinates for the 20 remaining blocker/gap rows, starting with `4827 HOLLAND Crescent` and rows where Google crosshair landed on road/forest/vacant land.
2. Re-run Google/ArcGIS/Bing collection for corrected coordinates.
3. Rebuild triage/site and verify the remaining blocked count drops.
