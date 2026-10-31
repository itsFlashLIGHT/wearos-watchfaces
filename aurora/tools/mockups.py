"""Render README mockups: compose the face with Pillow exactly where the WFF
layout puts every element, then clip to the round watch screen."""
import os

from PIL import Image, ImageDraw

import art
from art import BAR_CELL_H, BAR_CELL_W, BIG_H, ICON_KINDS, SIZE, SMALL_H

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mockups")

TIME_Y = 84
DATE_Y = 226
ICON_Y, ICON_SIZE = 262, 88
STEPS_Y = 372
BAR_Y = 410

WHITE = art.hx("#f5f8fc") + (255,)
SMALL_WHITE = art.hx("#eef3f9") + (255,)
AMB_BIG = art.hx("#b7c0ca") + (255,)
AMB_SMALL = art.hx("#8d97a2") + (255,)

ICON_FOR = {"storm": "storm", "snow": "snow", "rain": "rain", "fog": "fog"}

SAMPLE = dict(date="ПТ 31.10", temp="+12", steps="6842", percent=68)


def _text(img, s, font, color, y, shadow=None):
    if shadow:
        off, blur, scol = shadow
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        d.text(((SIZE - d.textlength(s, font=font)) / 2 + off[0], y + off[1]), s,
               font=font, fill=scol)
        from PIL import ImageFilter
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    d = ImageDraw.Draw(img)
    d.text(((SIZE - d.textlength(s, font=font)) / 2, y), s, font=font, fill=color)


def mockup(weather, phase, sample=SAMPLE):
    img = art.background(weather, phase).convert("RGBA")
    if weather in ("rain", "storm", "snow"):
        img.alpha_composite(art.precip_frames("rain" if weather == "storm" else "snow")[6])

    is_night = phase == "night"
    time_s = "23:47" if is_night else "14:37"
    big = art._font(300, BIG_H)
    small = art._font(400, SMALL_H)
    _text(img, time_s, big, WHITE, TIME_Y, shadow=((0, 4), 4, (8, 12, 24, 110)))
    _text(img, f"{sample['date']}  {sample['temp']}°", small, SMALL_WHITE, DATE_Y,
          shadow=((0, 2), 2, (8, 12, 24, 100)))

    kind = ICON_FOR.get(weather)
    if kind is None:  # clear / cloudy pick the day or night variant
        kind = "sun" if weather == "clear" and not is_night else \
               "moon" if weather == "clear" else \
               f"cloud_{'night' if is_night else 'day'}"
    img.alpha_composite(art.weather_icon(kind, ICON_SIZE),
                        ((SIZE - ICON_SIZE) // 2, ICON_Y))

    # steps: icon + count, centered as one row
    icon = art.steps_icon()
    d = ImageDraw.Draw(img)
    tw = d.textlength(sample["steps"], font=small)
    row_w = icon.width + 8 + tw
    x0 = (SIZE - row_w) / 2
    img.alpha_composite(icon, (int(x0), STEPS_Y))
    d.text((x0 + icon.width + 8, STEPS_Y), sample["steps"], font=small, fill=SMALL_WHITE)

    filled = round(sample["percent"] / 10)
    bx = (SIZE - BAR_CELL_W * 10) / 2
    for i in range(10):
        img.alpha_composite(art.bar_segment(i < filled),
                            (int(bx + i * BAR_CELL_W), BAR_Y))
    return img


def ambient(sample=SAMPLE):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    _text(img, "14:37", art._font(300, BIG_H), AMB_BIG, TIME_Y)
    _text(img, sample["date"], art._font(400, SMALL_H), AMB_SMALL, DATE_Y)
    return img


def round_face(img):
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, SIZE, SIZE], fill=255)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    scenes = [("clear", "day"), ("clear", "night"), ("clear", "sunset"),
              ("cloudy", "day"), ("rain", "day"), ("storm", "night"),
              ("snow", "day"), ("fog", "day")]
    thumbs = []
    for weather, phase in scenes:
        face = round_face(mockup(weather, phase))
        face.save(os.path.join(OUT, f"{weather}_{phase}.png"), optimize=True)
        thumbs.append(face.resize((240, 240), Image.LANCZOS))
    round_face(ambient()).save(os.path.join(OUT, "ambient.png"), optimize=True)

    grid = Image.new("RGBA", (240 * 4, 240 * 2), (24, 28, 36, 255))
    for i, t in enumerate(thumbs):
        grid.alpha_composite(t, (240 * (i % 4), 240 * (i // 4)))
    grid.save(os.path.join(OUT, "overview.png"), optimize=True)
    print("mockups:", ", ".join(os.listdir(OUT)))


if __name__ == "__main__":
    main()
