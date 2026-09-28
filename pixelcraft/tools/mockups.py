"""Render full-face mockups into mockups/."""
import os
import random
from PIL import Image, ImageDraw, ImageFont

from pixelart import (GRID, OFFSET, BOOT, BOOT_TIERS, boot_tier, draw_heart, draw_text,
                      scene, sprite, text_width, upscale, hexc)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mockups")
LABEL_FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"

STEP_GOAL = 10000
SAMPLE = dict(time="14:37", date="ПН 28.09", temp="+18°", steps=8432, battery=73)
LOW_BATTERY = 20


def hud(img, d, ambient=False, flash=False, jiggle=None):
    tw = text_width(d["time"], 4)
    draw_text(img, (GRID - tw) // 2, 36 + OFFSET, d["time"], scale=4,
              color=hexc("#ffffff") if not ambient else hexc("#d0d0d0"),
              shadow=None if ambient else hexc("#3f3f3f"), shadow_off=2)
    if ambient:
        tw = text_width(d["date"])
        draw_text(img, (GRID - tw) // 2, 74 + OFFSET, d["date"], color=hexc("#9a9a9a"), shadow=None)
        return img
    row = d["date"] + "  " + d["temp"]
    draw_text(img, (GRID - text_width(row)) // 2, 74 + OFFSET, row, color=hexc("#ffffff"))

    hearts = d["battery"] / 5  # 20 half-hearts
    low = d["battery"] < LOW_BATTERY
    x0 = (GRID - (10 * 8 + 1)) // 2
    for i in range(10):
        v = hearts - i * 2
        dy = jiggle[i] if (low and jiggle) else 0
        draw_heart(img, x0 + i * 8, 100 + OFFSET + dy, 2 if v >= 2 else (1 if v >= 1 else 0),
                   flash=low and flash)

    steps = str(d["steps"])
    sw = 9 + 3 + text_width(steps)
    sx = (GRID - sw) // 2
    sprite(img, sx, 113 + OFFSET, BOOT, BOOT_TIERS[boot_tier(d["steps"] * 100 / STEP_GOAL)])
    draw_text(img, sx + 12, 114 + OFFSET, steps, color=hexc("#ffffff"))
    return img


def round_face(img):
    big = upscale(img)
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big.width - 1, big.height - 1), fill=255)
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    out.paste(big, (0, 0), mask)
    return out


def contact_sheet(faces, cols, path, bg="#1e1f22"):
    pad, lab = 40, 50
    size = faces[0][0].width
    rows = (len(faces) + cols - 1) // cols
    w = cols * size + (cols + 1) * pad
    h = rows * (size + lab) + (rows + 1) * pad
    sheet = Image.new("RGBA", (w, h), hexc(bg))
    dr = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(LABEL_FONT, 30)
    for i, (face, label) in enumerate(faces):
        cx = pad + (i % cols) * (size + pad)
        cy = pad + (i // cols) * (size + lab + pad)
        dr.ellipse((cx - 8, cy - 8, cx + size + 8, cy + size + 8), fill=hexc("#0c0c0d"),
                   outline=hexc("#4a4c52"), width=4)
        sheet.alpha_composite(face, (cx, cy))
        tw = dr.textlength(label, font=font)
        dr.text((cx + size / 2 - tw / 2, cy + size + 15), label, font=font, fill=hexc("#d8d8d8"))
    sheet.save(path)
    return sheet


def weather_sheet():
    variants = [
        ("clear", True, None, "Ясно, день", "+18°"),
        ("clear", True, "sunrise", "Рассвет", "+9°"),
        ("clear", True, "sunset", "Закат", "+14°"),
        ("clear", False, None, "Ясно, ночь", "+11°"),
        ("cloudy", True, "sunset", "Закат, облачно", "+13°"),
        ("cloudy", True, None, "Облачно", "+15°"),
        ("rain", True, None, "Дождь", "+12°"),
        ("storm", True, None, "Гроза", "+16°"),
        ("snow", True, None, "Снег", "-4°"),
        ("fog", True, None, "Туман", "+7°"),
    ]
    faces = []
    for weather, day, phase, label, temp in variants:
        img = hud(scene(weather, day, phase=phase), dict(SAMPLE, temp=temp))
        face = round_face(img)
        name = phase or ("day" if day else "night")
        face.save(os.path.join(OUT, f"{weather}_{name}.png"))
        faces.append((face, label))
    amb = Image.new("RGBA", (GRID, GRID), (0, 0, 0, 255))
    face = round_face(hud(amb, SAMPLE, ambient=True))
    face.save(os.path.join(OUT, "ambient.png"))
    faces.append((face, "Always-On"))
    contact_sheet(faces, 4, os.path.join(OUT, "overview.png"))


def boots_sheet():
    tiers = [(2150, 94, "Кожа · < 33%"), (4870, 58, "Железо · 33–65%"),
             (7920, 36, "Золото · 66–99%"), (10450, 12, "Алмаз · 100%+")]
    faces = []
    for steps, batt, label in tiers:
        img = hud(scene("clear", True), dict(SAMPLE, steps=steps, battery=batt))
        faces.append((round_face(img), label))
    contact_sheet(faces, 4, os.path.join(OUT, "boots.png"))


def low_battery_gif():
    """Minecraft low-health effect: hearts jiggle every frame, outline flashes white."""
    rng = random.Random(3)
    base = scene("clear", True)
    d = dict(SAMPLE, battery=15)
    frames = []
    for f in range(12):
        jig = [rng.choice([-1, 0, 0, 1]) for _ in range(10)]
        img = hud(base.copy(), d, flash=(f // 2) % 2 == 0, jiggle=jig)
        big = round_face(img)
        frame = Image.new("RGBA", big.size, hexc("#1e1f22"))
        frame.alpha_composite(big)
        frames.append(frame.convert("RGB").quantize(256))
    frames[0].save(os.path.join(OUT, "low_battery.gif"), save_all=True,
                   append_images=frames[1:], duration=250, loop=0)


def precip_gif(kind, weather):
    """Preview of the animated rain / snow layer over its background."""
    from pixelart import PRECIP, precip_frames
    base = scene(weather, True, precip=False)
    frames = []
    for layer in precip_frames(kind):
        img = base.copy()
        img.alpha_composite(layer)
        big = round_face(hud(img, SAMPLE))
        frame = Image.new("RGBA", big.size, hexc("#1e1f22"))
        frame.alpha_composite(big)
        frames.append(frame.convert("RGB").quantize(256))
    frames[0].save(os.path.join(OUT, f"{kind}.gif"), save_all=True,
                   append_images=frames[1:], duration=PRECIP[kind]["ms"], loop=0)


def mobs_gif():
    """All three mobs walking through the cave one after another (cropped to the cave)."""
    from pixelart import MOBS, MOB_MS, MOB_STRIP_TOP, mob_frames
    base = hud(scene("clear", True), SAMPLE)
    frames = []
    for name in MOBS:
        for layer in mob_frames(name)[::2]:
            img = base.copy()
            img.alpha_composite(layer, (0, MOB_STRIP_TOP))
            face = round_face(img).crop((0, 280, 480, 480))
            frame = Image.new("RGBA", face.size, hexc("#1e1f22"))
            frame.alpha_composite(face)
            frames.append(frame.convert("RGB").quantize(256))
    frames[0].save(os.path.join(OUT, "mobs.gif"), save_all=True,
                   append_images=frames[1:], duration=MOB_MS * 2, loop=0)


def main():
    os.makedirs(OUT, exist_ok=True)
    mobs_gif()
    precip_gif("rain", "rain")
    precip_gif("snow", "snow")
    weather_sheet()
    boots_sheet()
    low_battery_gif()
    print("ok")


if __name__ == "__main__":
    main()
