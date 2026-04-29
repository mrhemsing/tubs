# Tubs aerial review progress — 2026-04-29

## Current state

- Total properties: **300 / 300 classified**
- Public candidate cards: **291**
- Per-address ArcGIS contact sheets: **300 / 300 generated** at `data/contact_sheets/`
- MLS contact sheets reviewed: **183**
- Google Static Maps satellite sheets indexed: **300 / 300**
- Google-reviewed/promoted candidates: **216 reviewed**, with Google imagery available as QA/detail links for all 300 addresses
- Tub concept mockups: **291 / 291 candidate cards**
- 4x upscaled review/editor images: **857 total** — 275 distinct primary candidate sources + 291 tub mockups + 291 editable tub design bases
- Coordinate blockers: **0**
- Needs-aerial-review rows: **0**
- Unresolved blocker rows: **0**
- Next.js build: **passing** after latest data refresh

## Final source/status split

- **174** Google overhead candidates
- **49** MLS aerial/elevated candidates
- **18** possible MLS elevated candidates needing verification
- **18** possible Google overhead candidates needing verification
- **15** Bing overhead candidates
- **10** ArcGIS overhead candidates
- **7** possible Bing overhead candidates needing verification
- **4** MLS ground-context-only
- **3** Mapbox raw-source candidates remain in triage, but Mapbox cards are intentionally suppressed where weaker than other options
- **2** photo not found after full review

## Tub + image-quality pass

- Generated tub concept mockups for all **291** public candidate cards.
- Added editable tub design layer with drag, scale, rotate, reset, local browser save, and copy-placement JSON.
- Added FAL/RealESRGAN 4x upscaling pipeline.
- Ran 4x upscale for all visible/review-edit images: **275 distinct primary candidate sources**, **291 tub mockups**, and **291 editable design bases**.
- Upscaled assets live under `public/upscaled-4x/`; index is `public/upscaled-4x.json`.
- Review UI prefers 4x assets when available and labels them with `· 4x`.
- Editable tub layer now uses 4x design-base imagery when available; the tub overlay is vector/canvas-rendered and can export an edited 4x mockup after manual placement/scale/rotation adjustments.

## ArcGIS contact-sheet pass

- Rebuilt per-address ArcGIS tile contact sheets from collected aerial tiles.
- Output index: `data/contact_sheets/index.csv`.
- Result: **300 contact sheets created**, **0 listings missing ArcGIS tile sheets**, **0 listings flagged for geocode fallback** from this pass.

## Final no-candidate rows

These are explicitly classified as `no_usable_aerial_candidate_after_full_review`, not left as unresolved blockers:

- `15 ALPINE TRAILS Crescent` — MLS has ground-level/deck/wooded-yard views only; ArcGIS is placeholder; Google and Bing are dense tree cover/no identifiable target house+lot.
- `9905 OSPREY LANDING Drive` — coordinate refined to ArcGIS point geocode; MLS has deck/wooded-lot context only; ArcGIS is placeholder; Google/Bing show road/trees/no clear house+lot.

## Latest Google fill-in pass

- Collected Google Static Maps imagery for the remaining **84** candidate-card addresses that previously had no Google imagery.
- `data/alternate_contact_sheets/google/index.csv` now covers **300 / 300** addresses.
- Every public candidate card now has a Google contact-sheet link; ArcGIS cards can display a Google image first where available so low-res ArcGIS crops are less prominent.
- Updated ranking/export support so reviewed usable Google beats ArcGIS/Bing after MLS, while unreviewed Google imagery remains available as a supporting link/photo.

## Earlier coordinate refinement + Bing fallback pass

Created `data/triage/coordinate_refinement_2026-04-29.csv`, refined 8 remaining blocker coordinates with ArcGIS point/subaddress geocoder matches, recollected ArcGIS and Bing, and wrote:

- `data/alternate_contact_sheets/bing/bing_review_batch_003.json`
- `data/alternate_contact_sheets/bing/bing_review_batch_004.json`

New promoted Bing overhead candidates:

- `150 SULLIVAN Drive` — high confidence Bing overhead.
- `4642 ROWAN Street` — medium confidence Bing overhead.
- `4958 MERLO Road` — medium confidence Bing overhead.
- `5160 RIVERSIDE Drive` — high confidence Bing overhead.
- `5401 BOOMERANG Way` — medium confidence Bing overhead.

New possible Bing candidates needing human verification:

- `37-6674 WARDNER-KIKOMUN Road`
- `18-6674 WARDNER-KIKOMUM Road`
- `15 Turner Close`

ArcGIS z19 recollection still returned Esri placeholders for refined rows, so the gains came from Bing fallback.

## Earlier MLS manifest review

Reviewed 11 remaining MLS contact sheets that were still unreviewed among blocker/needs-review rows and wrote `data/mls_photo_inventory/mls_crosscheck_batch_019.json`.

New promoted MLS aerial/elevated candidate:

- `1611 1ST S Avenue` — clear elevated/drone-style exterior images show the house with surrounding lot/landscape context. Best candidate photos: **1, 2, 21, 3**. Reuse rights remain `unknown_research_only`.

This cleared the previous **2 needs-aerial-review rows** (`1 BIGHORN SHEEP Lane`, `2527 LEDGEROCK Ridge`) by confirming they lack MLS aerial/elevated candidates.

## Decisions / notes

- Google remains the primary fallback source after MLS where already reviewed because it generally gives better resolution than ArcGIS/Bing/Mapbox.
- Visible Google cards use the single best reviewed zoom image, not the 3-panel diagnostic sheet.
- Google contact sheets are still exported as QA/detail links.
- Imagery remains research/internal; Google licensing/attribution/caching rules still need resolution before public/commercial reuse.
- Tub images are concept mockups only; the tub is digitally added and should not be represented as an existing property feature.

## Next best action

1. Matt can review the **291 candidate cards** using the 4x primary/tub images and editable tub design layer.
2. Human-verify high-value possible rows, especially possible Bing and possible Google candidates.
3. Manually verify `4827 HOLLAND Crescent` vs `4827 Holland Creek Ridge Rd` before treating that coordinate as final.
