"""Pixel-art primitives for the Minecraft-style watch face.

Everything is drawn on a logical 160x160 grid and upscaled x3 to 480x480
(the Galaxy Watch 8 44mm panel, so every art pixel is exactly 3x3 screen px).
The layout was designed on 150x150; OFFSET re-centres it on the bigger grid.
"""
import random
from PIL import Image

GRID = 160
OFFSET = (160 - 150) // 2
SCALE = 3
HORIZON = 92 + OFFSET

# ---------------------------------------------------------------- font 5x7
FONT = {
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "2": [".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"],
    "3": [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    "4": ["...##", "..#.#", ".#..#", "#...#", "#####", "....#", "....#"],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "#...#", "....#", "...#.", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    ":": [".", "#", ".", ".", ".", "#", "."],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "°": [".#.", "#.#", ".#.", "...", "...", "...", "..."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
    "П": ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],
    "Н": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "В": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "Т": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "С": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "Р": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Ч": ["#...#", "#...#", "#...#", ".####", "....#", "....#", "....#"],
    "Б": ["#####", "#....", "#....", "####.", "#...#", "#...#", "####."],
}


def text_width(text, scale=1):
    return sum((len(FONT[c][0]) + 1) * scale for c in text) - scale


def draw_text(img, x, y, text, scale=1, color=(255, 255, 255, 255),
              shadow=(63, 63, 63, 255), shadow_off=None):
    """Minecraft-style text: glyph + solid drop shadow offset by one glyph pixel."""
    if shadow_off is None:
        shadow_off = scale
    passes = []
    if shadow:
        passes.append((shadow_off, shadow))
    passes.append((0, color))
    for off, col in passes:
        cx = x
        for ch in text:
            g = FONT[ch]
            for gy, row in enumerate(g):
                for gx, px in enumerate(row):
                    if px == "#":
                        rect(img, cx + gx * scale + off, y + gy * scale + off,
                             scale, scale, col)
            cx += (len(g[0]) + 1) * scale


def rect(img, x, y, w, h, color):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            put(img, xx, yy, color)


def put(img, x, y, color):
    if 0 <= x < img.width and 0 <= y < img.height:
        if len(color) == 4 and color[3] < 255:
            r, g, b, a = img.getpixel((x, y))
            if a == 0:
                img.putpixel((x, y), tuple(color))
                return
            t = color[3] / 255
            img.putpixel((x, y), (round(r + (color[0] - r) * t),
                                  round(g + (color[1] - g) * t),
                                  round(b + (color[2] - b) * t), 255))
        else:
            img.putpixel((x, y), tuple(color[:3]) + (255,))


def sprite(img, x, y, rows, palette):
    for sy, row in enumerate(rows):
        for sx, ch in enumerate(row):
            if ch in palette:
                put(img, x + sx, y + sy, palette[ch])


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ---------------------------------------------------------------- sprites
HEART = [
    ".KK...KK.",
    "KWRK.KRRK",
    "KWRRKRRRK",
    "KRRRRRRRK",
    ".KRRRRRDK",
    "..KRRRDK.",
    "...KRDK..",
    "....KK...",
]
HEART_PAL_FULL = {"K": hexc("#1b0b0b"), "W": hexc("#ffd0d0"),
                  "R": hexc("#e8262b"), "D": hexc("#9c1016")}
HEART_PAL_EMPTY = {"K": hexc("#1b0b0b"), "W": hexc("#4a3535"),
                   "R": hexc("#2e2222"), "D": hexc("#2e2222")}


HEART_FLASH = hexc("#ffffff")


def draw_heart(img, x, y, fill, flash=False):
    """fill: 0 empty, 1 half, 2 full. flash: white outline (low-health blink frame)."""
    for sy, row in enumerate(HEART):
        for sx, ch in enumerate(row):
            if ch == ".":
                continue
            full = fill == 2 or (fill == 1 and sx <= 4)
            pal = HEART_PAL_FULL if full else HEART_PAL_EMPTY
            if ch == "K":
                put(img, x + sx, y + sy, HEART_FLASH if flash else HEART_PAL_FULL["K"])
                continue
            put(img, x + sx, y + sy, pal[ch])


BOOT = [
    ".KKKK....",
    ".KLLK....",
    ".KLLK....",
    ".KLLK....",
    ".KLLHKK..",
    ".KLLLLLK.",
    "KLLLLLLLK",
    "KDDDDDDDK",
    ".KKKKKKK.",
]
BOOT_TIERS = {
    "leather": {"K": hexc("#24160c"), "L": hexc("#a0663b"),
                "H": hexc("#c98a55"), "D": hexc("#5c3a1e")},
    "iron":    {"K": hexc("#262626"), "L": hexc("#c6c6c6"),
                "H": hexc("#ffffff"), "D": hexc("#7a7a7a")},
    "gold":    {"K": hexc("#3a2804"), "L": hexc("#f2cf3a"),
                "H": hexc("#fff7a8"), "D": hexc("#b07a12")},
    "diamond": {"K": hexc("#0b2e2c"), "L": hexc("#4fe0d6"),
                "H": hexc("#d2fffc"), "D": hexc("#1f8f89")},
}
BOOT_PAL = BOOT_TIERS["leather"]


def boot_tier(percent):
    """Step-goal progress -> armour material."""
    if percent >= 100:
        return "diamond"
    if percent >= 66:
        return "gold"
    if percent >= 33:
        return "iron"
    return "leather"


# ---------------------------------------------------------------- scenes
SKIES = {
    ("clear", True): ("#4f86f7", "#9cc3ff"),
    ("clear", False): ("#05081c", "#1b2452"),
    ("cloudy", True): ("#6f8bb5", "#b3c3d9"),
    ("cloudy", False): ("#0c1022", "#262c45"),
    ("rain", True): ("#4a5566", "#7d8a9c"),
    ("rain", False): ("#0a0d16", "#1f2533"),
    ("storm", True): ("#1e222b", "#3c4452"),
    ("storm", False): ("#07080c", "#1a1d26"),
    ("snow", True): ("#6f7f99", "#aab6c8"),
    ("snow", False): ("#141a2c", "#34405c"),
    ("fog", True): ("#7b848f", "#a9b0b8"),
    ("fog", False): ("#1c1f26", "#3a3f48"),
}


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def gradient(stops, t):
    stops = [hexc(c) for c in stops]
    seg = min(int(t * (len(stops) - 1)), len(stops) - 2)
    local = t * (len(stops) - 1) - seg
    return lerp(stops[seg], stops[seg + 1], local)


def draw_sky(img, *stops, bands=6):
    band_h = HORIZON / bands
    for y in range(HORIZON):
        b = min(int(y / band_h), bands - 1)
        col = gradient(stops, b / (bands - 1))
        prev = gradient(stops, max(b - 1, 0) / (bands - 1))
        first_row = y == int(b * band_h) and b > 0
        for x in range(GRID):
            c = prev if first_row and (x % 2 == 0) else col
            img.putpixel((x, y), c)


def draw_sun(img, x, y):
    x, y = x + OFFSET, y + OFFSET
    rect(img, x - 2, y - 2, 18, 18, hexc("#fff3a0", 90))
    rect(img, x, y, 14, 14, hexc("#fff38a"))
    rect(img, x + 2, y + 2, 10, 10, hexc("#fffbd6"))


def draw_moon(img, x, y):
    x, y = x + OFFSET, y + OFFSET
    rect(img, x - 2, y - 2, 16, 16, hexc("#c8d4ff", 40))
    rect(img, x, y, 12, 12, hexc("#e4e8f0"))
    for cx, cy, s in [(2, 2, 3), (7, 5, 3), (3, 8, 2), (8, 1, 2)]:
        rect(img, x + cx, y + cy, s, s, hexc("#b8bfcc"))


def draw_stars(img, rng, n=40):
    for _ in range(n):
        x, y = rng.randrange(GRID), rng.randrange(HORIZON - 10)
        c = rng.choice(["#ffffff", "#cfd8ff", "#fff4c8"])
        put(img, x, y, hexc(c, rng.choice([140, 200, 255])))


def draw_cloud(img, x, y, blocks, color, shade):
    """blocks: list of (dx, dy, w, h) in 4px cells -> blocky Minecraft cloud."""
    x, y = x + OFFSET, y + OFFSET
    for dx, dy, w, h in blocks:
        rect(img, x + dx * 4, y + dy * 4, w * 4, h * 4, color)
    for dx, dy, w, h in blocks:
        rect(img, x + dx * 4, y + (dy + h) * 4 - 1, w * 4, 1, shade)


CLOUD_A = [(0, 1, 7, 2), (2, 0, 3, 1)]
CLOUD_B = [(0, 0, 4, 2), (4, 1, 3, 1)]
CLOUD_C = [(0, 1, 9, 2), (1, 0, 4, 1), (6, 0, 2, 1)]


GRASS = ["#5d9e34", "#6fb23d", "#4f8a2b", "#67a83a"]
DIRT = ["#866043", "#79553a", "#96704f", "#6c4a31", "#8b6446"]
SNOW = ["#f4f8ff", "#e3ebf6", "#ffffff", "#d6e0ee"]


def draw_ground(img, rng, snowy=False):
    top = SNOW if snowy else GRASS
    for x in range(GRID):
        depth = 3 + (1 if rng.random() < 0.35 else 0) + (1 if rng.random() < 0.12 else 0)
        for y in range(HORIZON, GRID):
            if y - HORIZON < depth:
                c = rng.choice(top)
            else:
                c = rng.choice(DIRT)
                if rng.random() < 0.02:
                    c = "#7d7d7d"
            img.putpixel((x, y), hexc(c))
    # little bumps of grass / flowers standing on the horizon
    if not snowy:
        for x in range(0, GRID, 1):
            r = rng.random()
            if r < 0.10:
                put(img, x, HORIZON - 1, hexc(rng.choice(GRASS)))
                if rng.random() < 0.4:
                    put(img, x, HORIZON - 2, hexc(rng.choice(GRASS)))
            elif r < 0.12:
                put(img, x, HORIZON - 1, hexc("#4f8a2b"))
                put(img, x, HORIZON - 2, hexc(rng.choice(["#e03c3c", "#f2d43a"])))


# ------------------------------------------------------------ underground
# Same in every scene (fixed seed); never tinted by night / golden hour.
UNDERGROUND = HORIZON + 9          # average dirt -> stone boundary
CAVE_TOP, CAVE_FLOOR = 131, 147    # tunnel the mobs walk through (floor = feet row)
STONE = ["#747474", "#6a6a6a", "#7e7e7e", "#636363", "#707070"]
DEEPSLATE = ["#4d4d52", "#45454a", "#56565b", "#3f3f44"]
CAVE_WALL = ["#2c2825", "#332e2a", "#26221f", "#2f2a27"]
ORES = {  # speckle colours on top of stone
    "coal": ["#1c1c1c", "#2e2e2e"],
    "iron": ["#d8af93", "#c49a7c"],
    "gold": ["#fcee4b", "#e6c23a"],
    "redstone": ["#e01010", "#a00808"],
    "lapis": ["#2a52c9", "#1d3a96"],
    "diamond": ["#5decf5", "#3fc6cf"],
}
# (ore, x, y) cluster centres in grid space, kept clear of the step counter
ORE_SPOTS = [("coal", 22, 113), ("iron", 128, 110), ("coal", 140, 124),
             ("gold", 36, 126), ("redstone", 118, 124), ("lapis", 14, 140),
             ("diamond", 74, 154), ("iron", 50, 110), ("coal", 100, 110),
             ("gold", 146, 140), ("redstone", 46, 152), ("coal", 110, 153),
             ("coal", 8, 124), ("iron", 150, 116), ("lapis", 132, 150)]
TORCH_X = 56


def cave_bounds(x):
    """Ceiling / floor rows of the tunnel at column x (floor is flat for walking)."""
    import math
    ceil = CAVE_TOP + round(1.5 * math.sin(x / 7.0) + math.sin(x / 3.1))
    floor = CAVE_FLOOR + (1 if (x // 9) % 3 == 0 else 0)
    return ceil, floor


def draw_underground(img, seed=5):
    rng = random.Random(seed)
    boundary = []
    b = UNDERGROUND
    for x in range(GRID):
        b = max(UNDERGROUND - 2, min(UNDERGROUND + 2, b + rng.choice([-1, 0, 0, 1])))
        boundary.append(b)
    for x in range(GRID):
        for y in range(boundary[x], GRID):
            pal = DEEPSLATE if y > CAVE_FLOOR + 4 + (x * 7 % 3) else STONE
            img.putpixel((x, y), hexc(rng.choice(pal)))
    for ore, cx, cy in ORE_SPOTS:
        cy += OFFSET // 2
        # Minecraft ore look: a 5x4 block of stone with ~11 coloured specks
        for _ in range(11):
            x, y = cx + rng.randint(-2, 2), cy + rng.randint(-2, 1)
            if y >= boundary[max(0, min(GRID - 1, x))] + 1:
                rect(img, x, y, rng.choice([1, 1, 2]), 1, hexc(rng.choice(ORES[ore])))
    # the tunnel
    for x in range(GRID):
        ceil, floor = cave_bounds(x)
        for y in range(ceil, floor + 1):
            img.putpixel((x, y), hexc(rng.choice(CAVE_WALL)))
        put(img, x, ceil - 1, hexc("#4a4a4a"))           # shadowed rim
        rect(img, x, floor + 1, 1, 1, hexc(rng.choice(["#5a5a5a", "#6e6a66"])))  # gravel
    # torch with warm light on the back wall
    tx, ty = TORCH_X, CAVE_TOP + 4
    for y in range(CAVE_TOP - 1, CAVE_FLOOR + 1):
        for x in range(tx - 12, tx + 13):
            d = ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
            ceil, floor = cave_bounds(x)
            if d < 12 and ceil <= y <= floor:
                put(img, x, y, hexc("#ff9a3a", int(70 * (1 - d / 12))))
    rect(img, tx, ty, 1, 4, hexc("#7a5a32"))
    put(img, tx, ty - 1, hexc("#ffb02e"))
    put(img, tx, ty - 2, hexc("#fff08a"))


# ------------------------------------------------------------ mobs
# Walking sprites, facing right. Two frames each (legs), '.' = transparent.
MOBS = {
    "creeper": dict(
        pal={"G": hexc("#5fbf3b"), "g": hexc("#3f8f2b"), "K": hexc("#0f1a0f")},
        body=["GGGGGGGG", "GgGGGgGG", "GKKGGKKG", "GKKGGKKG", "GGGKKGGG",
              "GGKKKKGG", "GGKGGKGG", "GgGGGGgG", "..GgGG..", "..GGgG..",
              "..GGGG..", "..gGGG..", "..GGgG..", "..GGGG.."],
        legs=[[".GG..GG.", ".GG..GG."], ["GG....GG", "GG....GG"]]),
    "zombie": dict(
        pal={"H": hexc("#3b6b44"), "S": hexc("#5f9e6a"), "K": hexc("#10200f"),
             "C": hexc("#2fa3a7"), "L": hexc("#3b3f9e")},
        body=["..HHHHH...", "..HSSSS...", "..HSSKS...", "..SSSSS...", "..SSSSS...",
              "...CCC....", "...CCSSSSS", "...CCSSSSS", "...CCC....", "...CCC....",
              "...CCC....", "...LLL...."],
        legs=[["..LL.LL...", "..LL..LL..", ".LL...LL..", ".LL....LL."],
              ["...LLL....", "...LLL....", "...LLL....", "...LLL...."]]),
    "pig": dict(
        pal={"P": hexc("#f0a0a0"), "D": hexc("#d98080"), "K": hexc("#2a1a1a"),
             "N": hexc("#e0707e")},
        body=[".......PPPP.", ".PPPPPPPPKPP", "PPPPPPPPPPNN", "PPPPPPPPPPNN",
              "PPPPPPPPPPP.", ".PPPPPPPPP.."],
        legs=[[".DD.....DD..", ".DD.....DD..", ".DD.....DD.."],
              ["..DD.....DD.", "..DD.....DD.", "..DD.....DD."]]),
}

MOB_STRIP_TOP = CAVE_TOP - 4        # rows covered by the mob animation strip
MOB_STRIP_H = CAVE_FLOOR - MOB_STRIP_TOP + 2
MOB_STEP, MOB_MS = 2, 100           # px per frame, ms per frame


def mob_frames(name):
    """Frames of `name` walking left->right through the tunnel (strip-sized)."""
    m = MOBS[name]
    w = len(m["body"][0])
    frames = []
    # start and end fully off-screen so the first / last frame is empty
    for i, x in enumerate(range(-w - 2, GRID + 2, MOB_STEP)):
        img = Image.new("RGBA", (GRID, MOB_STRIP_H), (0, 0, 0, 0))
        rows = m["body"] + m["legs"][(i // 2) % 2]
        top = CAVE_FLOOR - len(rows) + 1 - MOB_STRIP_TOP
        for sy, row in enumerate(rows):
            for sx, ch in enumerate(row):
                if ch in m["pal"]:
                    put(img, x + sx, top + sy, m["pal"][ch])
        frames.append(img)
    frames.append(Image.new("RGBA", (GRID, MOB_STRIP_H), (0, 0, 0, 0)))
    return frames


def draw_tree(img, rng, x, snowy=False):
    x += OFFSET
    base = HORIZON
    rect(img, x + 5, base - 12, 2, 12, hexc("#6b4f2a"))
    put(img, x + 5, base - 7, hexc("#4d3a1f"))
    leaves = ["#3f7a24", "#4b8c2c", "#356a1e", "#58a032"]
    for yy in range(base - 22, base - 11):
        w = 12 if yy > base - 20 else 8
        x0 = x + (6 - w // 2)
        for xx in range(x0, x0 + w):
            c = rng.choice(leaves)
            if snowy and yy < base - 19:
                c = rng.choice(SNOW)
            put(img, xx, yy, hexc(c))


RAIN, STORM_RAIN = "#6c8fe0", "#8095c8"


def draw_rain(img, rng, n, color=RAIN):
    for _ in range(n):
        x, y = rng.randrange(GRID), rng.randrange(-4, HORIZON)
        for i in range(4):
            if y + i < HORIZON + 1:
                put(img, x, y + i, hexc(color, 150))


def draw_snowflakes(img, rng, n):
    for _ in range(n):
        x, y = rng.randrange(GRID), rng.randrange(HORIZON)
        put(img, x, y, hexc("#ffffff", 230))
        if rng.random() < 0.3:
            put(img, x + 1, y, hexc("#ffffff", 160))


def draw_lightning(img, x, y):
    x, y = x + OFFSET, y + OFFSET
    pts = [(0, 0), (-3, 8), (2, 10), (-4, 22), (1, 24), (-6, 40)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        steps = max(abs(x2 - x1), abs(y2 - y1))
        for s in range(steps + 1):
            px = x + round(x1 + (x2 - x1) * s / steps)
            py = y + round(y1 + (y2 - y1) * s / steps)
            put(img, px - 1, py, hexc("#9aa6ff", 120))
            put(img, px + 1, py, hexc("#9aa6ff", 120))
            put(img, px, py, hexc("#f4f4ff"))


GOLDEN = {
    "sunrise": dict(sky=("#34488f", "#6f5fa6", "#c97a9e", "#ffc27a"), sun_x=18,
                    cloud=("#ffd6c4", "#e8a09a"), tint=(0.95, 0.80, 0.78)),
    "sunset":  dict(sky=("#231f5c", "#5e2c72", "#b8456f", "#ff8f3f"), sun_x=98,
                    cloud=("#ffb08a", "#c9607a"), tint=(0.86, 0.68, 0.62)),
}


def draw_low_sun(img, x):
    """Big sun sitting on the horizon (drawn before the ground covers its bottom)."""
    x, y = x + OFFSET, HORIZON - 9
    rect(img, x - 3, y - 3, 26, 26, hexc("#ffcf6a", 70))
    rect(img, x, y, 20, 20, hexc("#ffb347"))
    rect(img, x + 3, y + 3, 14, 14, hexc("#ffe08a"))


def tint(layer, k):
    for y in range(layer.height):
        for x in range(layer.width):
            r, g, b, a = layer.getpixel((x, y))
            if a:
                layer.putpixel((x, y), (int(r * k[0]), int(g * k[1]), int(b * k[2]), a))


def night_tint(layer):
    for y in range(layer.height):
        for x in range(layer.width):
            r, g, b, a = layer.getpixel((x, y))
            if a:
                layer.putpixel((x, y), (int(r * 0.35), int(g * 0.38), int(b * 0.55), a))


def cloud_specs(weather, is_day, phase=None):
    """Clouds of a scene as draw_cloud() argument tuples (x, y, blocks, color, shade)."""
    if phase and weather in ("clear", "cloudy"):
        g = GOLDEN[phase]
        c0, c1 = hexc(g["cloud"][0], 230), hexc(g["cloud"][1])
        if weather == "cloudy":
            return [(8, 18, CLOUD_C, c0, c1), (70, 12, CLOUD_A, c0, c1),
                    (g["sun_x"] - 6, 56, CLOUD_B, c0, c1)]
        return [(22 if phase == "sunset" else 100, 22, CLOUD_B, c0, c1)]
    if weather == "clear":
        if not is_day:
            return []
        w = (hexc("#ffffff", 220), hexc("#dfe7f5"))
        return [(16, 26, CLOUD_B, *w), (104, 18, CLOUD_A, *w)]
    if weather == "cloudy":
        c = ("#ffffff", "#d7deea") if is_day else ("#3a415c", "#2b3148")
        w = (hexc(c[0], 235), hexc(c[1]))
        return [(8, 20, CLOUD_C, *w), (76, 14, CLOUD_A, *w), (100, 28, CLOUD_B, *w)]
    c = {"rain": ("#8c95a3", "#6f7886"), "storm": ("#3a3f4a", "#2a2e37"),
         "snow": ("#d9dfe8", "#b9c3d1"), "fog": ("#b9bfc6", "#9ea5ad")}[weather]
    if not is_day:
        c = ("#2c3140", "#20242f")
    return [(cx, cy, blk, hexc(c[0]), hexc(c[1]))
            for cx, cy, blk in [(-4, 6, CLOUD_C), (40, 2, CLOUD_C), (92, 8, CLOUD_C),
                                (20, 18, CLOUD_A), (78, 22, CLOUD_A)]]


def cloud_layer(weather, is_day, phase=None):
    """Seamless 2*GRID-wide strip of the scene's clouds, for horizontal scrolling.

    Sliding it left by 0..GRID pixels and wrapping gives an endless loop.
    Returns None when the scene has no clouds.
    """
    specs = cloud_specs(weather, is_day, phase)
    if not specs:
        return None
    img = Image.new("RGBA", (GRID * 2, HORIZON), (0, 0, 0, 0))
    for x, y, blocks, c0, c1 in specs:
        for dx in (-GRID, 0, GRID, 2 * GRID):
            draw_cloud(img, x + dx, y, blocks, c0, c1)
    return img


def scene(weather, is_day, seed=7, phase=None, clouds=True, precip=True):
    """phase: None, "sunrise" or "sunset" (golden hour; clear/cloudy only).
    clouds=False / precip=False leave clouds / rain+snow out so the watch face
    can animate them as separate layers."""
    if phase and weather in ("clear", "cloudy"):
        return golden_scene(weather, phase, seed, clouds)
    rng = random.Random(seed)
    img = Image.new("RGBA", (GRID, GRID), (0, 0, 0, 255))
    draw_sky(img, *SKIES[(weather, is_day)])
    if not is_day and weather in ("clear", "cloudy"):
        draw_stars(img, rng, 45 if weather == "clear" else 15)
    if weather in ("clear", "cloudy"):
        (draw_sun if is_day else draw_moon)(img, 68, 10)
    if clouds:
        for spec in cloud_specs(weather, is_day):
            draw_cloud(img, *spec)
    if weather == "storm":
        draw_lightning(img, 112, -8)
    snowy = weather == "snow"
    land = Image.new("RGBA", (GRID, GRID), (0, 0, 0, 0))
    draw_ground(land, rng, snowy=snowy)
    draw_tree(land, rng, 127, snowy=snowy)
    if not is_day:
        night_tint(land)
    img.alpha_composite(land)
    draw_underground(img)
    if precip and weather == "rain":
        draw_rain(img, rng, 110)
    if precip and weather == "storm":
        draw_rain(img, rng, 170, STORM_RAIN)
    if precip and weather == "snow":
        draw_snowflakes(img, rng, 90)
    if weather == "fog":
        for y in range(40 + OFFSET, UNDERGROUND):
            a = min(120, 30 + (y - 40 - OFFSET) * 2)
            for x in range(GRID):
                put(img, x, y, hexc("#c9ced3" if is_day else "#3a3f48", a))
    return img


def golden_scene(weather, phase, seed=7, clouds=True):
    g = GOLDEN[phase]
    rng = random.Random(seed)
    img = Image.new("RGBA", (GRID, GRID), (0, 0, 0, 255))
    draw_sky(img, *g["sky"], bands=8)
    if phase == "sunrise":
        for _ in range(12):  # last stars fading out at the top
            put(img, rng.randrange(GRID), rng.randrange(20), hexc("#ffffff", 150))
    draw_low_sun(img, g["sun_x"])
    if clouds:
        for spec in cloud_specs(weather, True, phase):
            draw_cloud(img, *spec)
    land = Image.new("RGBA", (GRID, GRID), (0, 0, 0, 0))
    draw_ground(land, rng)
    draw_tree(land, rng, 127)
    tint(land, g["tint"])
    img.alpha_composite(land)
    draw_underground(img)
    return img


# ------------------------------------------------------------ precipitation
# Seamless loops: particles live on a tile TILE px tall that repeats down the
# screen; after the last frame every particle has moved exactly one tile.
PRECIP = {
    #         tile  frames  px/frame  ms/frame  drops per tile
    "rain":  dict(tile=80, frames=16, speed=5, ms=80, count=60, color=RAIN),
    "storm": dict(tile=80, frames=10, speed=8, ms=70, count=95, color=STORM_RAIN),
    "snow":  dict(tile=40, frames=40, speed=1, ms=150, count=45),
}


PRECIP_H = HORIZON + 1  # precipitation ends on the grass


def precip_frames(kind, seed=11):
    """Frames (GRID x PRECIP_H, transparent) of falling rain / snow."""
    import math
    p = PRECIP[kind]
    rng = random.Random(seed)
    tile, n = p["tile"], p["frames"]
    if kind == "snow":
        # near flakes fall 2 px/frame and are bigger; all sway sideways
        flakes = [(rng.randrange(GRID), rng.randrange(tile), rng.choice([1, 1, 2]),
                   rng.random() * 2 * math.pi, rng.choice([0, 1, 1, 2]))
                  for _ in range(p["count"])]
    else:
        drops = [(rng.randrange(GRID), rng.randrange(tile)) for _ in range(p["count"])]
    frames = []
    for f in range(n):
        img = Image.new("RGBA", (GRID, PRECIP_H), (0, 0, 0, 0))
        if kind == "snow":
            for x0, y0, speed, phase, amp in flakes:
                y = (y0 + f * speed) % tile
                x = (x0 + round(amp * math.sin(2 * math.pi * f / n + phase))) % GRID
                for k in range(PRECIP_H // tile + 1):
                    put(img, x, y + k * tile, hexc("#ffffff", 230 if speed == 2 else 170))
                    if speed == 2:
                        put(img, x + 1, y + k * tile, hexc("#ffffff", 200))
                        put(img, x, y + k * tile + 1, hexc("#e8eef8", 200))
        else:
            for x, y0 in drops:
                y = (y0 + f * p["speed"]) % tile
                for k in range(-1, PRECIP_H // tile + 1):
                    for i in range(4):
                        put(img, x, y + k * tile + i, hexc(p["color"], 150))
        frames.append(img)
    return frames


def upscale(img):
    return img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
