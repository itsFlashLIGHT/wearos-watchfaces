"""All Aurora artwork: gradient sky backgrounds, weather icons, precip frames, glyphs.

Everything is drawn with Pillow; icons are rendered at 4x and downscaled for
smooth edges. PNGs and watchface.xml are generated, never edited by hand.

Font: Jost (SIL Open Font License), variable weight - thin 300 for the clock,
regular 400 for the small line. Downloaded into tools/fonts/Jost.ttf.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 480
SS = 4  # supersampling for icons
ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(ROOT, "fonts", "Jost.ttf")

BIG_H = 104      # clock glyph height, px on the 480 canvas
SMALL_H = 26     # date/steps glyph height
BAR_H = 10       # steps progress segment height


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- backgrounds

# (weather, phase) -> (top, bottom, glow color)
PALETTE = {
    ("clear", "day"):     ("#2b6cb8", "#9fc9ee", "#fff3c4"),
    ("clear", "night"):   ("#070b1d", "#1d2a52", "#cdd8ff"),
    ("clear", "sunrise"): ("#26356b", "#f2a35e", "#ffd9a0"),
    ("clear", "sunset"):  ("#33245c", "#e06a4f", "#ffc78f"),
    ("cloudy", "day"):     ("#57697e", "#a3b1bf", "#e8eef4"),
    ("cloudy", "night"):   ("#121826", "#2c3648", "#93a3bd"),
    ("cloudy", "sunrise"): ("#4a4a72", "#c98d6b", "#ffd0a0"),
    ("cloudy", "sunset"):  ("#43355f", "#b66a58", "#ffb98c"),
    ("rain", "day"):   ("#3c4d60", "#71808f", "#b9c6d2"),
    ("rain", "night"): ("#0d1420", "#232f3e", "#7f8ea0"),
    ("storm", "day"):   ("#2a3140", "#4b5568", "#b9a8d8"),
    ("storm", "night"): ("#090d16", "#1b2431", "#8f7fb8"),
    ("snow", "day"):   ("#7d93a9", "#c9d7e3", "#eef4fa"),
    ("snow", "night"): ("#16202e", "#3a4a5e", "#c6d4e6"),
    ("fog", "day"):   ("#6d7a85", "#aab4bc", "#dfe5e9"),
    ("fog", "night"): ("#151b23", "#333d47", "#8c99a5"),
}

GLOW_ALPHA = {"clear": 195, "cloudy": 100, "rain": 70, "storm": 90, "snow": 80, "fog": 70}

# glow center as a fraction of the canvas
GLOW_POS = {"day": (0.72, 0.20), "night": (0.28, 0.18),
            "sunrise": (0.50, 0.30), "sunset": (0.50, 0.30)}


def background(weather, phase):
    top, bottom, glow = (hx(c) for c in PALETTE[(weather, phase)])
    col = Image.new("RGB", (1, SIZE))
    for y in range(SIZE):
        col.putpixel((0, y), mix(top, bottom, y / (SIZE - 1)))
    img = col.resize((SIZE, SIZE)).convert("RGBA")

    # soft sun / moon glow
    ov = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    gx, gy = GLOW_POS[phase]
    r = 170
    d.ellipse([gx * SIZE - r, gy * SIZE - r, gx * SIZE + r, gy * SIZE + r],
              fill=glow + (GLOW_ALPHA[weather],))
    img = Image.alpha_composite(img, ov.filter(ImageFilter.GaussianBlur(70)))

    if phase == "night":
        ov = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        rng = random.Random(42)
        for _ in range(80):
            x, y = rng.uniform(0, SIZE), rng.uniform(0, SIZE * 0.62)
            rad = rng.uniform(0.7, 1.9)
            a = rng.randint(70, 190)
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(255, 255, 255, a))
        img = Image.alpha_composite(img, ov)

    if weather == "fog":
        ov = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        tint = (255, 255, 255) if phase != "night" else (180, 195, 210)
        for i, y in enumerate((140, 220, 300, 380)):
            d.rounded_rectangle([-40, y, SIZE + 40, y + 34], 17,
                                fill=tint + (26 if i % 2 else 40,))
        img = Image.alpha_composite(img, ov.filter(ImageFilter.GaussianBlur(14)))

    # vignette for depth
    vig = Image.new("L", (SIZE, SIZE), 0)
    d = ImageDraw.Draw(vig)
    d.ellipse([-70, -70, SIZE + 70, SIZE + 70], fill=110)
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    dark = Image.new("RGBA", (SIZE, SIZE), (5, 8, 16, 255))
    return Image.composite(img.convert("RGB"), dark.convert("RGB"), vig)


# --------------------------------------------------------------------- icons

ICON_KINDS = ["sun", "moon", "cloud_day", "cloud_night", "rain", "snow", "storm", "fog"]

SUN = hx("#ffd23f")
SUN_EDGE = hx("#ffb02e")
MOON = hx("#e9edf7")
CLOUD_L = hx("#f4f7fb")
CLOUD_D = hx("#aab6c8")
RAIN = hx("#6db3f2")
BOLT = hx("#ffd94d")
SNOWC = hx("#ffffff")
FOG = hx("#cfd6dd")


def _circle(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def _cloud(d, cx, cy, s, color):
    """Puffy cloud: three domes on a rounded base. s ~ half-width unit."""
    d.rounded_rectangle([cx - 2.0 * s, cy - 0.35 * s, cx + 2.0 * s, cy + 0.95 * s],
                        0.6 * s, fill=color)
    _circle(d, cx - 1.05 * s, cy - 0.35 * s, 0.95 * s, color)
    _circle(d, cx, cy - 0.75 * s, 1.15 * s, color)
    _circle(d, cx + 1.1 * s, cy - 0.3 * s, 0.85 * s, color)


def _sun(d, cx, cy, r):
    for k in range(8):
        a = math.radians(k * 45)
        x0, y0 = cx + (r + 7) * math.cos(a), cy + (r + 7) * math.sin(a)
        x1, y1 = cx + (r + 20) * math.cos(a), cy + (r + 20) * math.sin(a)
        d.line([x0, y0, x1, y1], fill=SUN_EDGE, width=9)
    _circle(d, cx, cy, r, SUN)


def _moon_layer(size, cx, cy, r):
    """Crescent as its own RGBA layer (punched with a transparent circle)."""
    lay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    md.ellipse([cx - r * 0.35, cy - r * 1.05, cx + r * 1.35, cy + r * 0.65], fill=0)
    lay.paste(MOON + (255,), (0, 0), mask)
    return lay


def weather_icon(kind, out=96):
    s = out * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx = cy = s / 2
    if kind == "sun":
        d = ImageDraw.Draw(img)
        _sun(d, cx, cy, s * 0.21)
    elif kind == "moon":
        img = _moon_layer(s, cx, cy, s * 0.24)
    else:
        d = ImageDraw.Draw(img)
        # small sun/moon peeking from behind the cloud
        if kind == "cloud_day":
            _sun(d, cx + s * 0.27, cy - s * 0.26, s * 0.14)
        elif kind == "cloud_night":
            img = Image.alpha_composite(img, _moon_layer(s, cx + s * 0.27, cy - s * 0.26, s * 0.14))
            d = ImageDraw.Draw(img)
        color = CLOUD_L if kind in ("cloud_day", "rain", "snow") else \
                CLOUD_D if kind == "cloud_night" else hx("#8d99ac") if kind == "storm" else FOG
        _cloud(d, cx, cy - s * 0.04, s * 0.185, color)
        base = cy + s * 0.20
        if kind == "rain":
            for i, dx in enumerate((-0.16, 0.0, 0.16)):
                x = cx + dx * s
                d.line([x, base, x - s * 0.05, base + s * 0.16], fill=RAIN, width=int(s * 0.045))
        elif kind == "snow":
            for dx in (-0.17, 0.0, 0.17):
                _circle(d, cx + dx * s, base + s * 0.07, s * 0.038, SNOWC)
        elif kind == "storm":
            x = cx + s * 0.02
            d.polygon([(x, base - s * 0.03), (x - s * 0.11, base + s * 0.11),
                       (x - s * 0.01, base + s * 0.11), (x - s * 0.09, base + s * 0.24),
                       (x + s * 0.09, base + s * 0.05), (x + s * 0.0, base + s * 0.05)],
                      fill=BOLT)
        elif kind == "fog":
            for i in range(3):
                y = base + s * 0.02 + i * s * 0.075
                w = s * (0.30 - i * 0.045)
                d.rounded_rectangle([cx - w, y, cx + w, y + s * 0.04], s * 0.02, fill=FOG)
    return img.resize((out, out), Image.LANCZOS)


def steps_icon(out_h=SMALL_H):
    """Two shoe prints, used as character 'a' of the small bitmap font."""
    s = out_h * SS
    img = Image.new("RGBA", (s * 2, s), (0, 0, 0, 0))  # extra width = gap before digits
    col = hx("#eef3f9") + (255,)
    w, h = s * 0.44, s * 0.70
    for (x, y, ang) in ((s * 0.02, s * 0.26, -22), (s * 0.52, -s * 0.04, -22)):
        foot = Image.new("RGBA", (int(w * 2), int(h * 2)), (0, 0, 0, 0))
        fd = ImageDraw.Draw(foot)
        fd.rounded_rectangle([w * 0.4, 0, w * 1.6, h * 1.15], w * 0.58, fill=col)   # sole
        fd.rounded_rectangle([w * 0.6, h * 1.28, w * 1.45, h * 1.85], w * 0.32, fill=col)  # heel
        foot = foot.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(foot, (int(x), int(y)))
    return img.resize((out_h * 2, out_h), Image.LANCZOS)


def bar_segment(filled):
    """Steps progress segment: characters '1' (filled) / '0' (empty) of the bar font."""
    s = BAR_H * SS
    cell_w, cell_h = int(s * 1.6), s  # width includes the gap to the next segment
    img = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = hx("#ffc857") + (255,) if filled else (255, 255, 255, 64)
    d.rounded_rectangle([0, 0, cell_w - s * 0.4, cell_h], cell_h / 2, fill=col)
    return img.resize((cell_w // SS, cell_h // SS), Image.LANCZOS)


BAR_CELL_W = bar_segment(True).width  # 16
BAR_CELL_H = BAR_H


# ------------------------------------------------------------------- precip

def precip_frames(kind, n_frames=12):
    """Looping rain / snow overlay, full canvas. Frame shift is seamless."""
    frames = []
    rng = random.Random(7 if kind == "rain" else 11)
    n = 90 if kind == "rain" else 70
    drops = []
    for _ in range(n):
        if kind == "rain":
            drops.append((rng.uniform(0, SIZE), rng.uniform(-SIZE, SIZE),
                          rng.uniform(28, 44), rng.uniform(18, 30), rng.randint(60, 110)))
        else:
            drops.append((rng.uniform(0, SIZE), rng.uniform(-SIZE, SIZE),
                          rng.uniform(9, 16), rng.uniform(1.4, 3.0),
                          rng.randint(90, 200), rng.uniform(0, math.tau)))
    for f in range(n_frames):
        t = f / n_frames
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for drop in drops:
            x0, y0, speed = drop[0], drop[1], drop[2]
            y = (y0 + speed * SIZE * t / 10) % (SIZE + 60) - 30
            if kind == "rain":
                _, _, _, ln, a = drop
                d.line([x0, y, x0 - ln * 0.12, y + ln], fill=(158, 195, 235, a), width=2)
            else:
                _, _, _, r, a, ph = drop
                x = x0 + math.sin(y / 46 + ph) * 7
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
        frames.append(img)
    return frames


PRECIP_MS = {"rain": 70, "snow": 110}


# ------------------------------------------------------------------- glyphs

def _font(weight, cap_h):
    """Jost at the pixel size that gives digits the requested cap height."""
    probe = ImageFont.truetype(FONT_PATH, 100)
    probe.set_variation_by_axes([weight])
    h0 = probe.getbbox("0")[3] - probe.getbbox("0")[1]
    f = ImageFont.truetype(FONT_PATH, round(100 * cap_h / h0))
    f.set_variation_by_axes([weight])
    return f


def glyph(ch, font, color, shadow=None):
    """Render one character, cropped to its ink box (shadow included)."""
    pad = 12
    tmp = Image.new("RGBA", (10, 10))
    x0, y0, x1, y1 = ImageDraw.Draw(tmp).textbbox((0, 0), ch, font=font)
    w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        off, blur, scol = shadow
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - x0 + off[0], pad - y0 + off[1]), ch, font=font, fill=scol)
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text((pad - x0, pad - y0), ch, font=font, fill=color)
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def mono_digits(chars, font, color, shadow=None):
    """char -> image, all digits padded to one advance width (stable clock)."""
    imgs = {ch: glyph(ch, font, color, shadow) for ch in chars}
    digits = [c for c in chars if c.isdigit()]
    if digits:
        w = max(imgs[c].width for c in digits)
        for c in digits:
            im = imgs[c]
            if im.width < w:
                wide = Image.new("RGBA", (w, im.height), (0, 0, 0, 0))
                wide.alpha_composite(im, ((w - im.width) // 2, 0))
                imgs[c] = wide
    return imgs
