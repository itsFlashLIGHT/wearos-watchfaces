"""Generate res/raw/watchface.xml (Watch Face Format v2) from the exported assets."""
import os
from xml.sax.saxutils import quoteattr

import build_assets
from art import BAR_CELL_H, BAR_CELL_W, BIG_H, SIZE, SMALL_H

RAW = os.path.join(build_assets.RES, "raw")

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

# Layout on the 480 canvas
TIME_Y = 84
DATE_Y = 226
ICON_Y, ICON_SIZE = 262, 88
STEPS_Y = 372
BAR_Y = 410
BAR_W = BAR_CELL_W * 10


def is_weather(kind):
    ors = " || ".join(f"{COND} == {c}" for c in WEATHER_CODES[kind])
    return f"({AVAIL} && ({ors}))"


def image(resource, size=SIZE):
    return (f'<PartImage x="0" y="0" width="{size}" height="{size}">'
            f'<Image resource="{resource}"/></PartImage>')


def layers(bg):
    """Background image plus the animated precip overlay (rain/storm/snow)."""
    key = bg[len("bg_"):]
    kind = key.split("_")[0]
    out = f"          {image(bg)}"
    if kind in ("rain", "storm", "snow"):
        res = "precip_rain" if kind == "storm" else f"precip_{kind}"
        out += (f'\n          <PartAnimatedImage x="0" y="0" width="{SIZE}" height="{SIZE}">'
                f'\n            <AnimationController play="ON_VISIBLE" repeat="TRUE" resumePlayBack="TRUE"/>'
                f'\n            <AnimatedImage resource="{res}" format="WEBP"/>'
                f'\n          </PartAnimatedImage>')
    return out


def background_condition():
    # Debug: FORCE_SCENE=rain_day ./build.sh install pins one background.
    forced = os.environ.get("FORCE_SCENE")
    if forced:
        return layers(f"bg_{forced}")
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
                         f'{layers(r)}\n'
                         f'        </Compare>' for n, _, r in cases)
    return f"""      <Condition>
        <Expressions>
{exprs}
        </Expressions>
{compares}
        <Default>
{layers("bg_clear_day")}
        </Default>
      </Condition>"""


def weather_icon_block():
    """Colored icon of the current condition, hidden in ambient mode."""
    cases = [("ic_storm", is_weather("storm"), "storm"),
             ("ic_snow", is_weather("snow"), "snow"),
             ("ic_rain", is_weather("rain"), "rain"),
             ("ic_fog", is_weather("fog"), "fog"),
             ("ic_cloudy_night", f"{is_weather('cloudy')} && {IS_NIGHT}", "cloud_night"),
             ("ic_cloudy_day", is_weather("cloudy"), "cloud_day"),
             ("ic_clear_night", IS_NIGHT, "moon")]
    exprs = "\n".join(f'        <Expression name="{n}"><![CDATA[{e}]]></Expression>'
                      for n, e, _ in cases)
    compares = "\n".join(
        f'      <Compare expression="{n}">{image("icon_" + r, ICON_SIZE)}</Compare>'
        for n, _, r in cases)
    return f"""    <Group name="weather_icon" x="{(SIZE - ICON_SIZE) // 2}" y="{ICON_Y}" width="{ICON_SIZE}" height="{ICON_SIZE}">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Condition>
        <Expressions>
{exprs}
        </Expressions>
{compares}
        <Default>{image("icon_sun", ICON_SIZE)}</Default>
      </Condition>
    </Group>"""


def bitmap_fonts(manifest):
    out = ["  <BitmapFonts>"]
    for font, chars in manifest.items():
        out.append(f'    <BitmapFont name="{font}">')
        for ch, (res, w, h) in chars.items():
            out.append(f'      <Character name={quoteattr(ch)} resource="{res}" width="{w}" height="{h}"/>')
        out.append("    </BitmapFont>")
    out.append("  </BitmapFonts>")
    return "\n".join(out)


def text(name, x, y, w, h, font, size, template, params, alpha=None, variant=None):
    ps = "\n".join(f'              <Parameter expression={quoteattr(p)}/>' for p in params)
    a = f' alpha="{alpha}"' if alpha is not None else ""
    v = f'\n        <Variant mode="AMBIENT" target="alpha" value="{variant}"/>' if variant is not None else ""
    return f"""      <PartText name="{name}" x="{x}" y="{y}" width="{w}" height="{h}"{a}>{v}
        <Text align="CENTER">
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
    return ternary([(f"[DAY_OF_WEEK] == {i + 1}", d) for i, d in enumerate(DAYS_RU[:-1])],
                   DAYS_RU[-1])


def steps_bar():
    params = [f'[STEP_PERCENT] >= {(i + 1) * 10} ? "1" : "0"' for i in range(10)]
    return text("steps_bar", (SIZE - BAR_W) // 2, BAR_Y, BAR_W, BAR_CELL_H,
                "bar", BAR_CELL_H, "%s" * 10, params, variant=0)


def build(manifest):
    time_params = ["[HOUR_0_23_Z]", "[MINUTE_Z]"]
    date_params = [day_of_week(), "[DAY_Z]", "[MONTH_Z]"]
    temp_sign = '[WEATHER.TEMPERATURE] > 0 ? "+" : ""'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated by tools/gen_watchface.py - do not edit by hand. -->
<WatchFace width="{SIZE}" height="{SIZE}">
  <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
  <Metadata key="PREVIEW_TIME" value="14:37:00"/>
{bitmap_fonts(manifest)}
  <Scene backgroundColor="#ff000000">
    <Group name="scene" x="0" y="0" width="{SIZE}" height="{SIZE}">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
{background_condition()}
    </Group>

{text("time", 0, TIME_Y, SIZE, BIG_H, "big", BIG_H, "%s:%s", time_params, variant=0)}
{text("time_ambient", 0, TIME_Y, SIZE, BIG_H, "biga", BIG_H, "%s:%s", time_params, alpha=0, variant=255)}

    <Group name="date_row" x="0" y="{DATE_Y}" width="{SIZE}" height="{SMALL_H}">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Condition>
        <Expressions>
          <Expression name="weather"><![CDATA[[WEATHER.IS_AVAILABLE] == 1]]></Expression>
        </Expressions>
        <Compare expression="weather">
{text("date_temp", 0, 0, SIZE, SMALL_H, "sm", SMALL_H, "%s %s.%s  %s%s°", date_params + [temp_sign, "[WEATHER.TEMPERATURE]"])}
        </Compare>
        <Default>
{text("date", 0, 0, SIZE, SMALL_H, "sm", SMALL_H, "%s %s.%s", date_params)}
        </Default>
      </Condition>
    </Group>
{text("date_ambient", 0, DATE_Y, SIZE, SMALL_H, "sma", SMALL_H, "%s %s.%s", date_params, alpha=0, variant=255)}

{weather_icon_block()}

{text("steps", 0, STEPS_Y, SIZE, SMALL_H, "sm", SMALL_H, "%s%s", ['"a"', "[STEP_COUNT]"], variant=0)}
{steps_bar()}
  </Scene>
</WatchFace>
"""


def main():
    manifest = build_assets.main()
    import mockups
    preview = mockups.round_face(mockups.mockup("clear", "day"))
    preview.save(os.path.join(build_assets.DRAWABLE, "preview.png"), optimize=True)
    os.makedirs(RAW, exist_ok=True)
    with open(os.path.join(RAW, "watchface.xml"), "w", encoding="utf-8") as f:
        f.write(build(manifest))
    print("watchface.xml written")


if __name__ == "__main__":
    main()
