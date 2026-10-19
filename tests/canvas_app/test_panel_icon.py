"""TASK-43: the panel's header icon is drawn in colours of its own that stand out on
Canvas's header, since Canvas renders it as an image, where currentColor is black."""

import re
import xml.etree.ElementTree as ET
from importlib import resources

ICON = resources.files("deep_reasoning.canvas_app").joinpath("panel.svg")
CANVAS_HEADER = "#0B0E14"  # Canvas's dark header background
MIN_CONTRAST = 3.0  # WCAG 2.1's non-text contrast, for a graphical object
HEX = re.compile(r"#([0-9a-fA-F]{6})")


def luminance(colour: str) -> float:
    channels = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    red, green, blue = linear
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(one: str, other: str) -> float:
    lighter, darker = sorted((luminance(one), luminance(other)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_the_panel_icon_is_visible_on_canvas_header():
    painted = [
        value
        for element in ET.fromstring(ICON.read_text()).iter()
        for name, value in element.attrib.items()
        if name in ("stroke", "fill") and value != "none"
    ]
    assert painted, "the icon paints nothing"
    for value in painted:
        assert HEX.fullmatch(value), f"{value} is not a colour of the icon's own"
        assert contrast(value, CANVAS_HEADER) >= MIN_CONTRAST, value
