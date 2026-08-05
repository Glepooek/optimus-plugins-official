"""SVG linear-gradient parsing shared by the WPF conversion outputs."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from typing import Callable


Matrix = tuple[float, float, float, float, float, float]
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
_URL_REFERENCE = re.compile(r"url\(\s*#([^)\s]+)\s*\)\Z", re.IGNORECASE)


@dataclass(frozen=True)
class GradientStop:
    """One resolved SVG gradient stop, expressed as a WPF colour."""

    color: str
    offset: float


@dataclass(frozen=True)
class LinearGradient:
    """A WPF-representable SVG ``linearGradient`` definition."""

    identifier: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    mapping_mode: str
    stops: tuple[GradientStop, ...]
    transform: Matrix = IDENTITY


def local_name(tag: object) -> str:
    """Return an XML tag's namespace-free name."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def parse_style(value: str) -> dict[str, str]:
    """Parse inline declarations; SVG style wins over presentation attributes."""
    declarations: dict[str, str] = {}
    for declaration in value.split(";"):
        name, separator, raw_value = declaration.partition(":")
        if separator:
            declarations[name.strip().lower()] = raw_value.strip()
    return declarations


def _attribute(element: ElementTree.Element, declarations: dict[str, str], name: str, default: str) -> str:
    return declarations.get(name, element.attrib.get(name, default)).strip()


def _number(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text in {"", "-", "-0"} else text


def _fraction(value: str, default: float) -> float:
    raw = value.strip()
    if not raw:
        return default
    try:
        number = float(raw[:-1]) / 100 if raw.endswith("%") else float(raw)
    except ValueError as error:
        raise ValueError(f"linearGradient has an unreadable coordinate {value!r}") from error
    return number


def _offset(value: str) -> float:
    try:
        offset = float(value[:-1]) / 100 if value.strip().endswith("%") else float(value)
    except ValueError as error:
        raise ValueError(f"linearGradient stop has an unreadable offset {value!r}") from error
    if not 0 <= offset <= 1:
        raise ValueError(f"linearGradient stop offset {value!r} is outside 0..1")
    return offset


def _opacity(value: str) -> float:
    try:
        opacity = float(value[:-1]) / 100 if value.strip().endswith("%") else float(value)
    except ValueError as error:
        raise ValueError(f"linearGradient stop has an unreadable stop-opacity {value!r}") from error
    if not 0 <= opacity <= 1:
        raise ValueError(f"linearGradient stop-opacity {value!r} is outside 0..1")
    return opacity


def _with_opacity(color: str, opacity: float) -> str:
    """Apply SVG stop-opacity to an already-WPF-formatted hex colour."""
    if opacity == 1:
        return color
    digits = color[1:] if color.startswith("#") else ""
    if len(digits) == 3:
        red, green, blue = (component * 2 for component in digits)
        return f"#{round(opacity * 255):02X}{red}{green}{blue}"
    if len(digits) == 6:
        return f"#{round(opacity * 255):02X}{digits}"
    if len(digits) == 8:
        alpha = round(int(digits[:2], 16) * opacity)
        return f"#{alpha:02X}{digits[2:]}"
    raise ValueError(
        "linearGradient stop-opacity requires a hex or rgba() stop-color; "
        f"got {color!r}"
    )


def collect_linear_gradients(
    root: ElementTree.Element,
    paint_parser: Callable[[str, str], str],
    transform_parser: Callable[[str], Matrix],
) -> dict[str, LinearGradient]:
    """Resolve supported ``linearGradient`` definitions before render-tree traversal."""
    gradients: dict[str, LinearGradient] = {}
    for element in root.iter():
        if local_name(element.tag) != "linearGradient":
            continue
        identifier = element.attrib.get("id", "").strip()
        if not identifier:
            continue
        declarations = parse_style(element.attrib.get("style", ""))
        units = _attribute(element, declarations, "gradientUnits", "objectBoundingBox")
        if units not in {"objectBoundingBox", "userSpaceOnUse"}:
            raise ValueError(
                f"linearGradient #{identifier} has unsupported gradientUnits {units!r}; "
                "use objectBoundingBox or userSpaceOnUse"
            )
        mapping_mode = "Absolute" if units == "userSpaceOnUse" else "RelativeToBoundingBox"
        start_x = _fraction(_attribute(element, declarations, "x1", "0%"), 0.0)
        start_y = _fraction(_attribute(element, declarations, "y1", "0%"), 0.0)
        end_x = _fraction(_attribute(element, declarations, "x2", "100%"), 1.0)
        end_y = _fraction(_attribute(element, declarations, "y2", "0%"), 0.0)
        transform_source = _attribute(element, declarations, "gradientTransform", "")
        transform = transform_parser(transform_source) if transform_source else IDENTITY
        stops: list[GradientStop] = []
        for child in element:
            if local_name(child.tag) != "stop":
                continue
            stop_style = parse_style(child.attrib.get("style", ""))
            color_source = _attribute(child, stop_style, "stop-color", "black")
            color = paint_parser(color_source, "linearGradient stop-color")
            opacity_source = _attribute(child, stop_style, "stop-opacity", "1")
            stops.append(GradientStop(_with_opacity(color, _opacity(opacity_source)), _offset(child.attrib.get("offset", "0"))))
        if len(stops) < 2:
            raise ValueError(f"linearGradient #{identifier} must contain at least two <stop> elements")
        gradients[identifier] = LinearGradient(
            identifier=identifier,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            mapping_mode=mapping_mode,
            stops=tuple(stops),
            transform=transform,
        )
    return gradients


def resolve_paint(value: str | None, role: str, gradients: dict[str, LinearGradient], paint_parser: Callable[[str, str], str]) -> str | LinearGradient | None:
    """Resolve solid SVG paint or a local linear-gradient reference for WPF output."""
    if value is None or value.strip().lower() == "none":
        return None
    source = value.strip()
    match = _URL_REFERENCE.match(source)
    if not match:
        return paint_parser(source, role)
    identifier = match.group(1)
    gradient = gradients.get(identifier)
    if gradient is None:
        raise ValueError(
            f"{role} value {source!r} references an unsupported or undefined gradient; "
            "flatten the gradient or pattern, or use a local <linearGradient> with at least two stops"
        )
    return gradient


def point(x: float, y: float) -> str:
    """Render WPF Point text without unnecessary fractional digits."""
    return f"{_number(x)},{_number(y)}"
