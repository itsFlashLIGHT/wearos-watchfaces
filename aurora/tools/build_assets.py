"""Export all Aurora drawables (backgrounds, icons, precip loops, bitmap fonts)."""
import os

import art
from art import (BAR_CELL_H, BAR_CELL_W, BIG_H, ICON_KINDS, PRECIP_MS, PALETTE,
                 SMALL_H)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "watchface", "src", "main", "res")
DRAWABLE = os.path.join(RES, "drawable-nodpi")

WHITE = art.hx("#f5f8fc") + (255,)
SMALL_WHITE = art.hx("#eef3f9") + (255,)
AMB_BIG = art.hx("#b7c0ca") + (255,)
AMB_SMALL = art.hx("#8d97a2") + (255,)
SHADOW_BIG = ((0, 4), 4, (8, 12, 24, 110))
SHADOW_SMALL = ((0, 2), 2, (8, 12, 24, 100))

CHAR_IDS = {str(d): str(d) for d in range(10)}
CHAR_IDS.update({":": "colon", ".": "dot", "+": "plus", "-": "minus", "°": "deg",
                 " ": "space", "П": "cy_pe", "Н": "cy_en", "В": "cy_ve", "Т": "cy_te",
                 "С": "cy_es", "Р": "cy_er", "Ч": "cy_che", "Б": "cy_be"})

BIG_CHARS = "0123456789: "
SMALL_CHARS = "0123456789.+-° ПНВТСРЧБ"


def save(img, name):
    img.save(os.path.join(DRAWABLE, name + ".png"), optimize=True)


def export_font(manifest, family, chars, font, color, shadow=None):
    manifest[family] = {}
    for ch, img in art.mono_digits(chars, font, color, shadow).items():
        name = f"{family}_{CHAR_IDS[ch]}"
        save(img, name)
        manifest[family][ch] = (name, img.width, img.height)


def main():
    os.makedirs(DRAWABLE, exist_ok=True)
    for f in os.listdir(DRAWABLE):
        os.remove(os.path.join(DRAWABLE, f))

    for weather, phase in PALETTE:
        save(art.background(weather, phase), f"bg_{weather}_{phase}")

    for kind in ICON_KINDS:
        save(art.weather_icon(kind), f"icon_{kind}")

    for kind in ("rain", "snow"):
        frames = art.precip_frames(kind)
        frames[0].save(os.path.join(DRAWABLE, f"precip_{kind}.webp"), save_all=True,
                       append_images=frames[1:], duration=PRECIP_MS[kind], loop=0,
                       lossless=True, method=6)

    manifest = {}
    export_font(manifest, "big", BIG_CHARS, art._font(300, BIG_H), WHITE, SHADOW_BIG)
    export_font(manifest, "biga", BIG_CHARS, art._font(300, BIG_H), AMB_BIG)
    export_font(manifest, "sm", SMALL_CHARS, art._font(400, SMALL_H), SMALL_WHITE,
                SHADOW_SMALL)
    export_font(manifest, "sma", SMALL_CHARS, art._font(400, SMALL_H), AMB_SMALL)

    # footsteps icon as character 'a' of the small font
    img = art.steps_icon()
    save(img, "sm_steps")
    manifest["sm"]["a"] = ("sm_steps", img.width, img.height)

    # steps progress bar: '0' empty segment, '1' filled
    manifest["bar"] = {}
    for ch, filled in (("0", False), ("1", True)):
        img = art.bar_segment(filled)
        name = f"bar_{'fill' if filled else 'empty'}"
        save(img, name)
        manifest["bar"][ch] = (name, img.width, img.height)
    return manifest


if __name__ == "__main__":
    m = main()
    print({k: len(v) for k, v in m.items()})
