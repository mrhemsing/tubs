# tubs

Collect candidate property/backyard imagery for hot-tub print marketing research.

Initial goal: for each sold property list, collect the best available **top-down aerial / backyard** candidate images and keep source/licensing notes separate from technical availability.

## Current pipeline

```powershell
python scripts/collect.py --limit 5 --aerial --zoom 19 --tile-radius 1
```

Outputs:

- `data/listings.json` / `data/listings.csv` — parsed property metadata
- `data/aerial/<area>/<property>/` — ArcGIS World Imagery tile candidates around the coordinates
- MLS photo URL manifests for each property, for later backyard/drone-photo scoring

## Notes

- Google imagery is useful for research, but not preferred for print marketing reuse.
- ArcGIS/Esri World Imagery tiles are collected as candidate research imagery; licensing must be verified before print use.
- MLS/listing photos may include better backyard/drone shots, but rights must be confirmed before reuse.
