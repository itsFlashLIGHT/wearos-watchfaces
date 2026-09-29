"""Generate res/raw/watchface.xml (Watch Face Format v2) from the exported assets."""
import os
from xml.sax.saxutils import quoteattr

import build_assets
from pixelart import GRID, HORIZON, MOB_STRIP_H, MOB_STRIP_TOP, MOBS, OFFSET, PRECIP_H, SCALE

SIZE = GRID * SCALE  # 480


def py(design_y):
    """Design-space (150 grid) row -> screen px on the 480 canvas."""
    return (design_y + OFFSET) * SCALE

RAW = os.path.join(build_assets.RES, "raw")

LOW_BATTERY = 20
DAYS_RU = ["ВС", "ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]  # [DAY_OF_WEEK]: 1 = Sunday

AVAIL = "[WEATHER.IS_AVAILABLE] == 1"
COND = "[WEATHER.CONDITION]"
# Day/night and golden hour come from the weather service only while its data is
# fresh: the watch refreshes weather irregularly, and hours-old data still says
# "day" long after sunset. Stale or missing data falls back to the clock.
STALE_MS = 90 * 60 * 1000
AGE = "([UTC_TIMESTAMP] - [WEATHER.LAST_UPDATED])"
FRESH = f"({AVAIL} && {AGE} < {STALE_MS})"
STALE = f"([WEATHER.IS_AVAILABLE] == 0 || {AGE} >= {STALE_MS})"
IS_NIGHT = (f"(({FRESH} && [WEATHER.IS_DAY] == 0) || "
            f"({STALE} && ([HOUR_0_23] < 7 || [HOUR_0_23] >= 20)))")
# Golden hour: the forecast for the next hour flips day<->night; clock fallback 06 / 19.
NEXT_OK = "[WEATHER.HOURS.1.IS_AVAILABLE] == 1"
SUNSET = (f"(({FRESH} && {NEXT_OK} && [WEATHER.IS_DAY] == 1 && [WEATHER.HOURS.1.IS_DAY] == 0) || "
          f"({STALE} && [HOUR_0_23] == 19))")
SUNRISE = (f"(({FRESH} && {NEXT_OK} && [WEATHER.IS_DAY] == 0 && [WEATHER.HOURS.1.IS_DAY] == 1) || "
           f"({STALE} && [HOUR_0_23] == 6))")

WEATHER_CODES = {
    "storm": [9],
    "snow": [5, 7, 10, 11],
    "rain": [4, 6, 12],
    "fog": [3, 13],
    "cloudy": [2, 14, 15],
}


def is_weather(kind):
    ors = " || ".join(f"{COND} == {c}" for c in WEATHER_CODES[kind])
    return f"({AVAIL} && ({ors}))"


def background_condition(clouds):
    # Debug: FORCE_SCENE=rain_day ./build.sh install pins one background.
    forced = os.environ.get("FORCE_SCENE")
    if forced:
        return layers(f"bg_{forced}", clouds)
    # Order matters: the first matching Compare wins.
    cases = []
    for kind in ("storm", "snow", "rain", "fog"):
        cases.append((f"{kind}_night", f"{is_weather(kind)} && {IS_NIGHT}", f"bg_{kind}_night"))
        cases.append((f"{kind}_day", is_weather(kind), f"bg_{kind}_day"))
    cloudy = is_weather("cloudy")
    for phase, expr in (("sunset", SUNSET), ("sunrise", SUNRISE)):
        cases.append((f"cloudy_{phase}", f"{cloudy} && {expr}", f"bg_cloudy_{phase}"))
        # storm/snow/rain/fog already matched above, so no weather check needed
        cases.append((f"clear_{phase}", expr, f"bg_clear_{phase}"))
    cases.append(("cloudy_night", f"{cloudy} && {IS_NIGHT}", "bg_cloudy_night"))
    cases.append(("cloudy_day", cloudy, "bg_cloudy_day"))
    cases.append(("clear_night", IS_NIGHT, "bg_clear_night"))

    exprs = "\n".join(f'          <Expression name="{n}"><![CDATA[{e}]]></Expression>'
                      for n, e, _ in cases)
    compares = "\n".join(f'        <Compare expression="{n}">\n'
                         f'{layers(r, clouds)}\n'
                         f'        </Compare>' for n, _, r in cases)
    return f"""      <Condition>
        <Expressions>
{exprs}
        </Expressions>
{compares}
        <Default>
{layers("bg_clear_day", clouds)}
        </Default>
      </Condition>"""


def cloud_shift(period):
    """Scroll left one art pixel (3 px) every `period` seconds, wrapping after GRID px."""
    return f"-{SCALE} * floor(([SECONDS_IN_DAY] % {GRID * period}) / {period})"


def layers(bg, clouds):
    """Background image plus its scrolling cloud strip (if the scene has clouds)."""
    key = bg[len("bg_"):]
    out = f"          {image(bg)}"
    kind = key.split("_")[0]
    if kind in ("rain", "storm", "snow"):
        out += (f'\n          <PartAnimatedImage x="0" y="0" width="{SIZE}" height="{PRECIP_H * SCALE}">'
                f'\n            <AnimationController play="ON_VISIBLE" repeat="TRUE" resumePlayBack="TRUE"/>'
                f'\n            <AnimatedImage resource="precip_{kind}" format="WEBP"/>'
                f'\n          </PartAnimatedImage>')
    if key in clouds:
        period = 1 if key.startswith("storm") else 2  # storm clouds race by
        out += (f'\n          <PartImage x="0" y="0" width="{SIZE * 2}" height="{HORIZON * SCALE}">'
                f'\n            <Transform target="x" value="{cloud_shift(period)}"/>'
                f'\n            <Image resource="clouds_{key}"/>'
                f'\n          </PartImage>')
    return out


def image(resource):
    return (f'<PartImage x="0" y="0" width="{SIZE}" height="{SIZE}">'
            f'<Image resource="{resource}"/></PartImage>')


def bitmap_fonts(manifest):
    out = ["  <BitmapFonts>"]
    for font, chars in manifest.items():
        out.append(f'    <BitmapFont name="{font}">')
        for ch, (res, w, h) in chars.items():
            out.append(f'      <Character name={quoteattr(ch)} resource="{res}" width="{w}" height="{h}"/>')
        out.append("    </BitmapFont>")
    out.append("  </BitmapFonts>")
    return "\n".join(out)


def text(name, x, y, w, h, font, size, template, params, alpha=None, variant=None, align="CENTER"):
    ps = "\n".join(f'              <Parameter expression={quoteattr(p)}/>' for p in params)
    a = f' alpha="{alpha}"' if alpha is not None else ""
    v = f'\n        <Variant mode="AMBIENT" target="alpha" value="{variant}"/>' if variant is not None else ""
    return f"""      <PartText name="{name}" x="{x}" y="{y}" width="{w}" height="{h}"{a}>{v}
        <Text align="{align}">
          <BitmapFont family="{font}" size="{size}">
            <Template><![CDATA[{template}]]>
{ps}
            </Template>
          </BitmapFont>
        </Text>
      </PartText>"""


def ternary(pairs, default):
    """[(cond, value), ...] -> nested ?: expression returning string literals."""
    expr = f'"{default}"'
    for cond, val in reversed(pairs):
        expr = f'({cond}) ? "{val}" : {expr}'
    return expr


def day_of_week():
    return ternary([(f"[DAY_OF_WEEK] == {i + 1}", d) for i, d in enumerate(DAYS_RU[:-1])], DAYS_RU[-1])


def heart_params():
    low = f"[BATTERY_PERCENT] < {LOW_BATTERY}"
    params = []
    for i in range(10):
        lo = i * 10
        # jiggle row j: 0 steady, 1 raised, 2 lowered; only while battery is low
        j = f"(({low}) ? (([SECOND] + {i * 7}) % 3) : 0)"
        pairs = []
        for jj in range(3):
            for fill, thr in ((2, lo + 10), (1, lo + 5)):
                pairs.append((f"{j} == {jj} && [BATTERY_PERCENT] >= {thr}", str(jj * 3 + fill)))
            pairs.append((f"{j} == {jj}", str(jj * 3)))
        params.append(ternary(pairs, "0"))
    return params


MOB_EVERY_HOURS = 3   # a mob walks through the cave at 00:00, 03:00, 06:00 ...
MOB_WINDOW_MIN = 5    # ... whenever the screen turns on during the first 5 minutes


def mob_pick(selector, play, indent):
    """Condition choosing which mob animation plays, by `selector` % len(MOBS)."""
    names = list(MOBS)
    pad = " " * indent
    exprs = "\n".join(f'{pad}    <Expression name="{n}"><![CDATA[{selector} == {i}]]></Expression>'
                      for i, n in enumerate(names[:-1]))

    def anim(n):
        return (f'<PartAnimatedImage x="0" y="0" width="{SIZE}" height="{MOB_STRIP_H * SCALE}">'
                f'<AnimationController play="{play}"/>'
                f'<AnimatedImage resource="mob_{n}" format="WEBP"/></PartAnimatedImage>')
    compares = "\n".join(f'{pad}  <Compare expression="{n}">{anim(n)}</Compare>' for n in names[:-1])
    return (f"{pad}<Condition>\n{pad}  <Expressions>\n{exprs}\n{pad}  </Expressions>\n"
            f"{compares}\n{pad}  <Default>{anim(names[-1])}</Default>\n{pad}</Condition>")


def mob_block():
    """Mob crossing the cave: on schedule (and on tap), otherwise only on tap."""
    n = len(MOBS)
    scheduled = f"[HOUR_0_23] % {MOB_EVERY_HOURS} == 0 && [MINUTE] < {MOB_WINDOW_MIN}"
    return f"""    <Group name="cave_mob" x="0" y="{MOB_STRIP_TOP * SCALE}" width="{SIZE}" height="{MOB_STRIP_H * SCALE}">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Condition>
        <Expressions>
          <Expression name="mob_time"><![CDATA[{scheduled}]]></Expression>
        </Expressions>
        <Compare expression="mob_time">
{mob_pick(f"floor([HOUR_0_23] / {MOB_EVERY_HOURS}) % {n}", "ON_VISIBLE TAP", 10)}
        </Compare>
        <Default>
{mob_pick(f"[MINUTE] % {n}", "TAP", 10)}
        </Default>
      </Condition>
    </Group>"""


def hearts_block():
    params = heart_params()
    flash = f"[BATTERY_PERCENT] < {LOW_BATTERY} && ([SECOND] % 2) == 0"
    steady = text("hearts", 0, 0, 270, 30, "hearts", 30, "%s" * 10, params)
    blink = text("hearts_flash", 0, 0, 270, 30, "hearts_flash", 30, "%s" * 10, params)
    return f"""    <Group name="battery_hearts" x="{(SIZE - 270) // 2}" y="{py(99)}" width="270" height="30">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Condition>
        <Expressions>
          <Expression name="flash"><![CDATA[{flash}]]></Expression>
        </Expressions>
        <Compare expression="flash">
  {blink}
        </Compare>
        <Default>
  {steady}
        </Default>
      </Condition>
    </Group>"""


def debug_weather():
    """DEBUG_WEATHER=1: raw weather values under the date as
    "<available> <is_day> <condition> <next hour is_day> <night branch>  <minutes since update>"."""
    if not os.environ.get("DEBUG_WEATHER"):
        return ""
    flag = lambda e: f'({e}) ? "1" : "0"'
    params = [flag("[WEATHER.IS_AVAILABLE] == 1"), flag("[WEATHER.IS_DAY] == 1"),
              "[WEATHER.CONDITION]", flag("[WEATHER.HOURS.1.IS_DAY] == 1"), flag(IS_NIGHT),
                        f"floor({AGE} / 60000)"]
    return text("debug_weather", 2, py(84), SIZE, 27, "sm", 27, "%s %s %s %s %s  %s", params, variant=0)


def build(manifest, clouds):
    time_params = ["[HOUR_0_23_Z]", "[MINUTE_Z]"]
    date_params = [day_of_week(), "[DAY_Z]", "[MONTH_Z]"]
    temp_sign = '[WEATHER.TEMPERATURE] > 0 ? "+" : ""'
    boot = ternary([("[STEP_PERCENT] >= 100", "d"), ("[STEP_PERCENT] >= 66", "c"),
                    ("[STEP_PERCENT] >= 33", "b")], "a")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated by tools/gen_watchface.py - do not edit by hand. -->
<WatchFace width="{SIZE}" height="{SIZE}">
  <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
  <Metadata key="PREVIEW_TIME" value="14:37:00"/>
{bitmap_fonts(manifest)}
  <Scene backgroundColor="#ff000000">
    <Group name="scene" x="0" y="0" width="{SIZE}" height="{SIZE}">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
{background_condition(clouds)}
    </Group>

    <!-- time: the 12 px trailing gap of the last glyph is offset by x=6 -->
{text("time", 6, py(36), SIZE, 90, "big", 90, "%s:%s", time_params, variant=0)}
{text("time_ambient", 6, py(36), SIZE, 90, "biga", 90, "%s:%s", time_params, alpha=0, variant=255)}

    <Group name="date_row" x="0" y="{py(73)}" width="{SIZE}" height="27">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Condition>
        <Expressions>
          <Expression name="weather"><![CDATA[[WEATHER.IS_AVAILABLE] == 1]]></Expression>
        </Expressions>
        <Compare expression="weather">
  {text("date_temp", 2, 0, SIZE, 27, "sm", 27, "%s %s.%s  %s%s°", date_params + [temp_sign, "[WEATHER.TEMPERATURE]"])}
        </Compare>
        <Default>
  {text("date", 2, 0, SIZE, 27, "sm", 27, "%s %s.%s", date_params)}
        </Default>
      </Condition>
    </Group>
{text("date_ambient", 2, py(73), SIZE, 27, "sma", 27, "%s %s.%s", date_params, alpha=0, variant=255)}

{mob_block()}
{debug_weather()}

{hearts_block()}

{text("steps", 2, py(113), SIZE, 27, "sm", 27, "%s%s", [boot, "[STEP_COUNT]"], variant=0)}
  </Scene>
</WatchFace>
"""


def main():
    manifest, clouds = build_assets.main()
    import mockups
    preview = mockups.round_face(mockups.hud(mockups.scene("clear", True), mockups.SAMPLE))
    preview.save(os.path.join(build_assets.DRAWABLE, "preview.png"), optimize=True)
    os.makedirs(RAW, exist_ok=True)
    with open(os.path.join(RAW, "watchface.xml"), "w", encoding="utf-8") as f:
        f.write(build(manifest, clouds))
    print("watchface.xml written")


if __name__ == "__main__":
    main()
