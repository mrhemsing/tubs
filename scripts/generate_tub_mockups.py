#!/usr/bin/env python3
"""Generate concept hot-tub mockups from exported review card images.

This creates clearly synthetic concept overlays for internal visual review. It does
not imply a tub exists on the property and should be labeled as a mockup wherever
shown.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
ASSETS = PUBLIC / "review-assets"
MOCKUPS = PUBLIC / "tub-mockups"
OUT_INDEX = PUBLIC / "tub-mockups.json"

SKIP_MOCKUP_SOURCES = {
    "no_usable_aerial_candidate_after_full_review",
    "mls_ground_backyard_context_only",
}


def slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:90] or "item"


def asset_path(url: str) -> Path:
    return PUBLIC / url.lstrip("/").replace("/", "\\")


def useful_thumb(card: dict) -> str:
    # Prefer true overhead sources. MLS photos can be oblique/ground-level, so use
    # Google support imagery if present for non-overhead MLS cards.
    source = card.get("recommendedSource", "")
    if source.startswith("google") and card.get("googleBestImage"):
        return card["googleBestImage"]
    if card.get("links", {}).get("googleBestImage") and not source.startswith("mls"):
        return card["links"]["googleBestImage"]
    thumbs = card.get("thumbs") or []
    for preferred in ["Google", "Bing", "ArcGIS", "Mapbox"]:
        for thumb in thumbs:
            if thumb.get("label") == preferred:
                return thumb.get("url", "")
    if thumbs and not source.startswith("mls"):
        return thumbs[0].get("url", "")
    return card.get("links", {}).get("googleBestImage", "")


def make_tub_asset(size: int) -> Image.Image:
    """Draw a top-down white acrylic spa with blue water and subtle details."""
    scale = 4
    w = h = size * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(w * 0.08)
    # shadow handled separately; draw shell
    d.rounded_rectangle((pad, pad, w - pad, h - pad), radius=int(w * 0.16), fill=(246, 248, 247, 255), outline=(205, 210, 210, 255), width=max(4, int(w * 0.018)))
    inner = int(w * 0.17)
    d.rounded_rectangle((inner, inner, w - inner, h - inner), radius=int(w * 0.12), fill=(171, 226, 236, 230), outline=(235, 247, 248, 255), width=max(4, int(w * 0.014)))
    # water highlights
    for i, alpha in enumerate([55, 42, 32]):
        inset = inner + int(w * (0.045 + i * 0.04))
        d.ellipse((inset, inset, w - inset, h - inset), outline=(245, 255, 255, alpha), width=max(3, int(w * 0.01)))
    # headrests / controls
    rests = [
        (int(w*.19), int(h*.20), int(w*.33), int(h*.28)),
        (int(w*.67), int(h*.72), int(w*.81), int(h*.80)),
        (int(w*.20), int(h*.67), int(w*.29), int(h*.82)),
        (int(w*.72), int(h*.18), int(w*.80), int(h*.33)),
    ]
    for box in rests:
        d.rounded_rectangle(box, radius=int(w*.035), fill=(38, 48, 55, 210))
    d.rounded_rectangle((int(w*.42), int(h*.10), int(w*.58), int(h*.17)), radius=int(w*.02), fill=(55, 65, 72, 230))
    # jets
    jet_color = (40, 66, 76, 105)
    for cx, cy in [(0.30,0.38),(0.40,0.30),(0.60,0.31),(0.70,0.40),(0.35,0.70),(0.50,0.76),(0.66,0.66),(0.28,0.55),(0.74,0.55)]:
        r = int(w * 0.018)
        x = int(w * cx); y = int(h * cy)
        d.ellipse((x-r, y-r, x+r, y+r), fill=jet_color)
    # mild blur/downsample for photoreal-ish integration
    return img.resize((size, size), Image.Resampling.LANCZOS)


def green_score_crop(img: Image.Image, x: int, y: int, s: int) -> float:
    crop = img.crop((x, y, x + s, y + s)).resize((24, 24), Image.Resampling.BILINEAR).convert("RGB")
    pix = list(crop.getdata())
    score = 0.0
    for r, g, b in pix:
        green = max(0, g - max(r, b))
        brightness = (r + g + b) / 3
        if g > 55 and green > 8 and 35 < brightness < 220:
            score += green + min(g, 160) * 0.15
        # penalize water/sky/roof/black shadows
        if b > g + 20 or brightness < 35 or brightness > 235:
            score -= 8
    return score / len(pix)


def choose_position(img: Image.Image, tub_size: int) -> tuple[int, int]:
    w, h = img.size
    margin = max(12, tub_size // 3)
    step = max(14, tub_size // 4)
    best = None
    # Bias slightly toward lower half / backyard-ish visual area while still
    # selecting green open pixels.
    for y in range(margin, max(margin + 1, h - tub_size - margin), step):
        for x in range(margin, max(margin + 1, w - tub_size - margin), step):
            score = green_score_crop(img, x, y, tub_size)
            score += (y / h) * 2.5
            score -= abs((x + tub_size / 2) - w * 0.52) / w * 1.2
            if best is None or score > best[0]:
                best = (score, x, y)
    if best and best[0] > 1.0:
        return best[1], best[2]
    return int(w * 0.58 - tub_size / 2), int(h * 0.62 - tub_size / 2)


def apply_tub(base: Image.Image, tub_size: int, rotation: float) -> tuple[Image.Image, dict[str, float]]:
    base = base.convert("RGBA")
    w, h = base.size
    tub = make_tub_asset(tub_size).rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
    tw, th = tub.size
    x, y = choose_position(base.convert("RGB"), max(tw, th))
    x = max(0, min(w - tw, x))
    y = max(0, min(h - th, y))

    shadow = Image.new("RGBA", tub.size, (0, 0, 0, 0))
    alpha = tub.getchannel("A").filter(ImageFilter.GaussianBlur(max(3, tub_size // 18)))
    shadow.putalpha(alpha.point(lambda a: int(a * 0.28)))
    out = base.copy()
    out.alpha_composite(shadow, (x + max(2, tub_size // 24), y + max(3, tub_size // 20)))
    out.alpha_composite(tub, (x, y))
    placement = {
        "xPct": round(((x + tw / 2) / w) * 100, 2),
        "yPct": round(((y + th / 2) / h) * 100, 2),
        "sizePct": round((max(tw, th) / min(w, h)) * 100, 2),
        "rotation": round(rotation, 2),
    }
    return out.convert("RGB"), placement


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-data", default=str(PUBLIC / "review-data.json"))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    data = json.loads(Path(args.review_data).read_text(encoding="utf-8"))
    cards = [c for c in data.get("cards", []) if c.get("recommendedSource") not in SKIP_MOCKUP_SOURCES]
    if args.limit:
        cards = cards[: args.limit]

    MOCKUPS.mkdir(parents=True, exist_ok=True)
    rows = []
    made = 0
    for card in cards:
        src_url = useful_thumb(card)
        if not src_url:
            continue
        src = asset_path(src_url)
        if not src.exists():
            continue
        with Image.open(src) as im:
            im = im.convert("RGB")
            max_dim = 960
            if max(im.size) > max_dim:
                im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            tub_size = max(54, min(130, int(min(im.size) * 0.17)))
            rotation = ((int(card.get("rank", 0)) * 17) % 30) - 15
            out, placement = apply_tub(im, tub_size, rotation)
        name = f"{str(card['rank']).zfill(3)}-{slug(card['address'])}-{card['listingId']}-tub-mockup.jpg"
        dest = MOCKUPS / name
        out.save(dest, quality=90, optimize=True)
        rel = "/tub-mockups/" + name
        rows.append({
            "listingId": card["listingId"],
            "address": card["address"],
            "rank": card["rank"],
            "sourceImage": src_url,
            "mockup": rel,
            "placement": placement,
            "label": "Tub concept mockup",
            "notice": "Concept mockup only — hot tub digitally added.",
        })
        made += 1
    OUT_INDEX.write_text(json.dumps({"count": len(rows), "mockups": rows}, indent=2), encoding="utf-8")
    print(f"Generated {made} tub mockups -> {MOCKUPS.relative_to(ROOT)}")
    print(f"Index: {OUT_INDEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
