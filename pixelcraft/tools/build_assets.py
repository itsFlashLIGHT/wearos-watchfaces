"""Export all watch face drawables (backgrounds, bitmap-font glyphs, hearts, boots).

Glyph images are exported at their exact on-screen pixel size so the WFF
renderer never has to scale (and blur) the pixel art.
"""
import os
from PIL import Image

from pixelart import (FONT, HEART, HEART_PAL_FULL, HEART_PAL_EMPTY, HEART_FLASH,
                      BOOT, BOOT_TIERS, SCALE, PRECIP, MOBS, MOB_MS, cloud_layer, mob_frames,
                      precip_frames,
                      scene, upscale, hexc)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "watchface", "src", "main", "res")
DRAWABLE = os.path.join(RES, "drawable-nodpi")

WHITE, SHADOW = hexc("#ffffff"), hexc("#3f3f3f")
AMB_BIG, AMB_SMALL = hexc("#d0d0d0"), hexc("#9a9a9a")

# resource-name suffix for every font character
CHAR_IDS = {str(d): str(d) for d in range(10)}
CHAR_IDS.update({":": "colon", ".": "dot", "+": "plus", "-": "minus", "°": "deg",
                 " ": "space", "П": "cy_pe", "Н": "cy_en", "В": "cy_ve", "Т": "cy_te",
                 "С": "cy_es", "Р": "cy_er", "Ч": "cy_che", "Б": "cy_be"})

BACKGROUNDS = [(w, p) for w in ("clear", "cloudy", "rain", "storm", "snow", "fog")
               for p in ("day", "night")] + \
              [(w, p) for w in ("clear", "cloudy") for p in ("sunrise", "sunset")]

# Big font: 1 glyph pixel = 12 screen px, shadow offset 6 px.
BIG = dict(px=12, shadow=6, top=0, rows=7)
# Small font: 1 glyph pixel = 3 screen px, shadow 3 px, 1 empty row on top so
# glyphs line up with the 9-row boot icons sharing the same font.
SMALL = dict(px=3, shadow=3, top=1, rows=9)


def save(img, name):
    img.save(os.path.join(DRAWABLE, name + ".png"), optimize=True)


def glyph_image(rows, spec, color, shadow):
    w = len(rows[0])
    px = spec["px"]
    img = Image.new("RGBA", ((w + 1) * px, spec["rows"] * px + (spec["shadow"] if spec is BIG else 0)),
                    (0, 0, 0, 0))
    layers = ([(spec["shadow"], shadow)] if shadow else []) + [(0, color)]
    for off, col in layers:
        for gy, row in enumerate(rows):
            for gx, ch in enumerate(row):
                if ch == "#":
                    x0 = gx * px + off
                    y0 = (gy + spec["top"]) * px + off
                    for yy in range(y0, y0 + px):
                        for xx in range(x0, x0 + px):
                            if xx < img.width and yy < img.height:
                                img.putpixel((xx, yy), col)
    return img


def sprite_image(rows, palette, cell_w, cell_h, dy=0):
    img = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    for sy, row in enumerate(rows):
        for sx, ch in enumerate(row):
            if ch in palette:
                img.putpixel((sx, sy + dy), palette[ch])
    return img.resize((cell_w * SCALE, cell_h * SCALE), Image.NEAREST)


def heart_rows_palette(fill, flash):
    """Return a per-pixel palette dict keyed by (x, y) for one heart state."""
    pix = {}
    for sy, row in enumerate(HEART):
        for sx, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "K":
                pix[(sx, sy)] = HEART_FLASH if flash else HEART_PAL_FULL["K"]
                continue
            full = fill == 2 or (fill == 1 and sx <= 4)
            pix[(sx, sy)] = (HEART_PAL_FULL if full else HEART_PAL_EMPTY)[ch]
    return pix


def heart_image(fill, flash, dy):
    # 9x10 logical cell: heart is 8 rows tall, dy in {0,1,2} gives the jiggle
    img = Image.new("RGBA", (9, 10), (0, 0, 0, 0))
    for (x, y), c in heart_rows_palette(fill, flash).items():
        img.putpixel((x, y + dy), c)
    return img.resize((9 * SCALE, 10 * SCALE), Image.NEAREST)


def main():
    os.makedirs(DRAWABLE, exist_ok=True)
    for f in os.listdir(DRAWABLE):
        os.remove(os.path.join(DRAWABLE, f))

    # backgrounds without clouds + a separate scrolling cloud strip per scene
    manifest = {"clouds": set()}
    for weather, phase in BACKGROUNDS:
        is_day = phase != "night"
        golden = phase if phase in ("sunrise", "sunset") else None
        img = scene(weather, is_day, phase=golden, clouds=False, precip=False)
        save(upscale(img).convert("RGB"), f"bg_{weather}_{phase}")
        layer = cloud_layer(weather, is_day, golden)
        if layer:
            save(upscale(layer), f"clouds_{weather}_{phase}")
            manifest["clouds"].add(f"{weather}_{phase}")
    clouds = manifest.pop("clouds")

    # mobs crossing the cave: played once per trigger (loop=1)
    for name in MOBS:
        frames = [upscale(f) for f in mob_frames(name)]
        frames[0].save(os.path.join(DRAWABLE, f"mob_{name}.webp"), save_all=True,
                       append_images=frames[1:], duration=MOB_MS, loop=1,
                       lossless=True, method=6)

    # falling rain / snow as looping animated WebP overlays
    for kind, p in PRECIP.items():
        frames = [upscale(f) for f in precip_frames(kind)]
        frames[0].save(os.path.join(DRAWABLE, f"precip_{kind}.webp"), save_all=True,
                       append_images=frames[1:], duration=p["ms"], loop=0,
                       lossless=True, method=6)

    manifest.update({"big": {}, "biga": {}, "sm": {}, "sma": {}})
    for ch, rows in FONT.items():
        cid = CHAR_IDS[ch]
        if ch in "0123456789:":
            for font, col, sh in (("big", WHITE, SHADOW), ("biga", AMB_BIG, None)):
                img = glyph_image(rows, BIG, col, sh)
                save(img, f"{font}_{cid}")
                manifest[font][ch] = (f"{font}_{cid}", img.width, img.height)
        for font, col, sh in (("sm", WHITE, SHADOW), ("sma", AMB_SMALL, None)):
            img = glyph_image(rows, SMALL, col, sh)
            save(img, f"{font}_{cid}")
            manifest[font][ch] = (f"{font}_{cid}", img.width, img.height)

    # boots live in the small font as characters a..d (leather..diamond);
    # the cell is 12 px wider than the sprite to leave a gap before the digits
    for ch, tier in zip("abcd", ("leather", "iron", "gold", "diamond")):
        img = sprite_image(BOOT, BOOT_TIERS[tier], 12, 9)
        save(img, f"sm_boot_{tier}")
        manifest["sm"][ch] = (f"sm_boot_{tier}", img.width, img.height)

    # hearts: chars 0-2 steady, 3-5 raised, 6-8 lowered (fill = char % 3)
    manifest["hearts"], manifest["hearts_flash"] = {}, {}
    for font, flash in (("hearts", False), ("hearts_flash", True)):
        for j, dy in enumerate((1, 0, 2)):
            for fill in range(3):
                img = heart_image(fill, flash, dy)
                name = f"{'hf' if flash else 'h'}_{fill}_{j}"
                save(img, name)
                manifest[font][str(j * 3 + fill)] = (name, img.width, img.height)
    return manifest, clouds


if __name__ == "__main__":
    m, c = main()
    print({k: len(v) for k, v in m.items()}, "cloud layers:", len(c))
