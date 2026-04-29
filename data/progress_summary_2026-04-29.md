# Tubs aerial review progress — 2026-04-29

## Current state

- Total properties: **300 / 300 classified**
- Public candidate cards: **291**
- Per-address ArcGIS contact sheets: **300 / 300 generated** at `data/contact_sheets/`
- MLS contact sheets reviewed: **183**
- Google Static Maps satellite sheets indexed: **300 / 300**
- Google-reviewed/promoted candidates: **216 reviewed**, with Google imagery available as QA/detail links for all 300 addresses
- Tub concept mockups: **291 / 291 candidate cards**
- Non-AI print-ready exports: **582 total** — 291 primary candidates + 291 tub mockups
- AI/FAL upscaled assets are retained in `public/upscaled-4x/` but disabled by default because they made aerial imagery look synthetic.
- Coordinate blockers: **0**
- Needs-aerial-review rows: **0**
- Unresolved blocker rows: **0**
- Next.js build: **passing** after latest data refresh
- Manual verification shortlist: **49 rows** — 36 high priority, 7 medium, 6 low

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
- Tested FAL/RealESRGAN 4x upscaling, but disabled it by default because AI super-resolution invented texture/detail and made aerials look fake.
- Review UI now uses real/non-AI source images by default again. AI-upscaled files remain available only behind `NEXT_PUBLIC_USE_AI_UPSCALED=1` for comparison/debugging.
- Added conservative non-AI print exports: Lanczos resize + light sharpening, no generated detail.
- Print-ready assets live under `public/print-ready/`; index is `public/print-ready.json`.
- Editable tub overlay remains vector/canvas-rendered for crisp placement/export without altering the real base imagery.

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

## Manual verification shortlist

Created focused QA outputs for the remaining judgment calls:

- `data/triage/manual_verification_shortlist.csv`
- `data/triage/manual_verification_shortlist.md`

Counts:

- **36** high-priority rows: possible MLS elevated + possible Google overhead candidates.
- **7** medium-priority rows: possible Bing overhead candidates.
- **6** low-priority rows: MLS ground-context-only and final no-candidate rows.

## Next best action

1. Matt can review `data/triage/manual_verification_shortlist.md` first, then open the corresponding candidate/tub cards.
2. Tune tub placement in the editable tub layer and use the non-AI print-ready exports for selected keepers.
3. Manually verify `4827 HOLLAND Crescent` vs `4827 Holland Creek Ridge Rd` before treating that coordinate as final.
