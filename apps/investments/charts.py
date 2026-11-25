"""Shapes for the page's charts, worked out on the server so the page is whole without scripts.

The site's content security policy allows no inline styles, so sizes and positions go in SVG
attributes, and colours in classes. Heat runs in eleven steps, from -5 (worst) to 5 (best).
"""

import math
from collections.abc import Sequence


def line_path(
    values: Sequence[float], width: float, height: float, lo: float, hi: float, log: bool = False
) -> str:
    """An SVG path through the values, scaled into a box."""
    if not values:
        return ""

    def f(v: float) -> float:
        return math.log(v) if log else v

    span = f(hi) - f(lo) or 1.0
    step = width / (len(values) - 1) if len(values) > 1 else 0
    points = (
        f"{'L' if i else 'M'}{i * step:.1f} {height - (f(v) - f(lo)) / span * height:.1f}"
        for i, v in enumerate(values)
    )
    return "".join(points)


def area_path(line: str, width: float, height: float) -> str:
    """The area under a line, down to the bottom of its box."""
    return f"{line}L{width} {height}L0 {height}Z" if line else ""


def band_path(top: Sequence[float], bottom: Sequence[float], width: float, height: float) -> str:
    """A band between two lines of fractions (0 at the top, 1 at the bottom)."""
    if not top:
        return ""
    step = width / (len(top) - 1) if len(top) > 1 else 0
    upper = "".join(
        f"{'L' if i else 'M'}{i * step:.1f} {v * height:.1f}" for i, v in enumerate(top)
    )
    lower = "".join(
        f"L{i * step:.1f} {v * height:.1f}" for i, v in reversed(list(enumerate(bottom)))
    )
    return upper + lower + "Z"


def heat(value: float, scale: float) -> str:
    """A heat class for a value, full strength at ±scale."""
    step = round(max(-1.0, min(1.0, value / scale)) * 5) if scale else 0
    return f"iv-h{'n' if step < 0 else 'p'}{abs(step)}"


def tone(value: float | None) -> str:
    if value is None:
        return "iv-flat"
    return "iv-up" if value > 0.00005 else "iv-down" if value < -0.00005 else "iv-flat"


def treemap(items: list[dict], x=0.0, y=0.0, w=100.0, h=100.0, out=None) -> list[dict]:
    """Splits the list into two halves of about equal weight, along the longer side, until each
    box holds one thing. Positions are percentages of the whole."""
    out = [] if out is None else out
    if not items:
        return out
    if len(items) == 1:
        out.append({**items[0], "x": x, "y": y, "w": w, "h": h})
        return out
    total = sum(i["weight"] for i in items) or 1.0
    running, split = 0.0, 1
    for i, item in enumerate(items[:-1]):
        running += item["weight"]
        split = i + 1
        if running >= total / 2:
            break
    share = sum(i["weight"] for i in items[:split]) / total
    # The box is about 1.6 times as wide as it is tall on screen, so "longer" allows for that.
    if w * 1.6 >= h * 1.1:
        treemap(items[:split], x, y, w * share, h, out)
        treemap(items[split:], x + w * share, y, w * (1 - share), h, out)
    else:
        treemap(items[:split], x, y, w, h * share, out)
        treemap(items[split:], x, y + h * share, w, h * (1 - share), out)
    return out
