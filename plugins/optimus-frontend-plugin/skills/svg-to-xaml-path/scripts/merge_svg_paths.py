"""Merge SVG path data into WPF XAML Path elements."""

from __future__ import annotations

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, replace
from html import escape
from pathlib import Path
from typing import Iterable

from svg_gradients import LinearGradient, collect_linear_gradients, point, resolve_paint


#: An affine transform as SVG writes it: a, b, c, d, e, f.
Matrix = tuple[float, float, float, float, float, float]
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
#: One `name(arguments)` item of a transform list.
TRANSFORM_FUNCTION = re.compile(
    r"(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)"
)
#: Transform arguments are separated by commas, whitespace, or neither before a sign.
NUMBER_SEPARATOR = re.compile(r"[\s,]+|(?<=[0-9.])(?=-)")
#: A DOCTYPE carrying an internal subset, which is where entity bombs are declared.
INTERNAL_DTD_SUBSET = re.compile(r"<!DOCTYPE[^>\[]*\[", re.IGNORECASE)


#: Container elements whose descendants are never rendered directly.
NON_RENDERED_TAGS = frozenset({"defs", "clipPath", "mask", "symbol", "marker", "pattern"})
#: Basic shapes with an exact, algebraic path equivalent defined by the SVG 2 spec.
CONVERTED_SHAPE_TAGS = frozenset({"rect", "circle", "ellipse", "line", "polyline", "polygon"})
#: Renderable elements no path can reproduce; warn rather than drop them silently.
UNCONVERTIBLE_TAGS = frozenset({"text", "tspan", "textPath", "image", "use", "foreignObject"})
#: Presentation properties read out of inline `style` declarations.
CONVERTED_STYLE_PROPERTIES = frozenset(
    {"fill", "stroke", "fill-rule", "display", "visibility", "transform"}
)
#: WPF fill rule prefixes; SVG defaults to nonzero while WPF defaults to EvenOdd.
FILL_RULE_PREFIXES = {"nonzero": "F1", "evenodd": "F0"}
#: Hex colours WPF's Brush type converter accepts, as #RGB/#ARGB/#RRGGBB/#AARRGGBB.
HEX_COLOUR = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\Z")
#: Functional `rgb()`/`rgba()` notation, which WPF cannot parse but we can rewrite.
RGB_FUNCTION = re.compile(
    r"rgba?\(\s*([^,\s)]+)[\s,]+([^,\s)]+)[\s,]+([^,\s)]+)"
    r"(?:\s*[,/]\s*([^,\s)]+))?\s*\)\Z",
    re.IGNORECASE,
)
#: SVG/CSS3 keywords WPF spells with `gray`; its own list has no `grey` variant at all.
GREY_SPELLINGS = {
    "grey": "gray",
    "darkgrey": "darkgray",
    "dimgrey": "dimgray",
    "lightgrey": "lightgray",
    "slategrey": "slategray",
    "lightslategrey": "lightslategray",
    "darkslategrey": "darkslategray",
}
#: SVG/CSS3 colour keywords. WPF's own keyword list is the same set plus `Transparent`,
#: minus the `grey` spellings above, which are rewritten rather than rejected.
COLOUR_KEYWORDS = frozenset(
    """aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue
    blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk
    crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki
    darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen
    darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue
    dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite
    gold goldenrod gray grey green greenyellow honeydew hotpink indianred indigo ivory khaki
    lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
    lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen
    lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen
    magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen
    mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream
    mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid
    palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum
    powderblue purple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell
    sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal
    thistle tomato transparent turquoise violet wheat white whitesmoke yellow
    yellowgreen""".split()
)


class ConversionError(Exception):
    """An input or SVG conversion error that should be shown to the user."""


@dataclass(frozen=True)
class SvgPath:
    """A usable SVG path and its effective inherited presentation attributes."""

    data: str
    fill: str | LinearGradient | None
    stroke: str | LinearGradient | None
    fill_rule: str
    matrix: Matrix


@dataclass(frozen=True)
class Inherited:
    """Presentation state an element inherits from its ancestors."""

    fill: str = "#000000"
    stroke: str = "none"
    fill_rule: str = "nonzero"
    visibility: str = "visible"
    matrix: Matrix = IDENTITY


def local_name(tag: object) -> str:
    """Return an XML element's local name, including for namespaced tags."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def colour_channel(value: str, source: str) -> int:
    """Convert one `rgb()` channel, which is either a percentage or a 0-255 number."""
    try:
        if value.endswith("%"):
            scaled = round(float(value[:-1]) * 255 / 100)
        else:
            scaled = round(float(value))
    except ValueError:
        raise ConversionError(
            f"paint value {source!r} has an unreadable channel {value!r}"
        ) from None
    if not 0 <= scaled <= 255:
        raise ConversionError(f"paint value {source!r} has an out-of-range channel {value!r}")
    return scaled


def alpha_channel(value: str, source: str) -> int:
    """Convert an `rgba()` alpha, which is a 0-1 fraction or a percentage."""
    try:
        fraction = float(value[:-1]) / 100 if value.endswith("%") else float(value)
    except ValueError:
        raise ConversionError(f"paint value {source!r} has an unreadable alpha {value!r}") from None
    if not 0.0 <= fraction <= 1.0:
        raise ConversionError(f"paint value {source!r} has an out-of-range alpha {value!r}")
    return round(fraction * 255)


def wpf_hex(value: str) -> str:
    """Reorder a CSS hex colour into WPF's channel order.

    CSS writes `#RGBA` / `#RRGGBBAA`; WPF reads `#ARGB` / `#AARRGGBB`. The 3- and
    6-digit forms carry no alpha and are identical in both, but passing a literal
    4- or 8-digit value through unchanged rotates the channels silently.
    """
    digits = value[1:]
    if len(digits) == 4:
        return f"#{digits[3]}{digits[0]}{digits[1]}{digits[2]}"
    if len(digits) == 8:
        return f"#{digits[6:8]}{digits[0:6]}"
    return value


def wpf_paint(value: str, role: str) -> str:
    """Return a paint value WPF can parse, rewriting what it can and rejecting the rest.

    WPF's brush converter accepts hex and colour keywords only. Passing anything else
    through would exit successfully but fail at XAML load time, so reject it here.
    """
    value = value.strip()
    if HEX_COLOUR.match(value):
        return wpf_hex(value)
    lowered = value.lower()
    if lowered in GREY_SPELLINGS:
        return GREY_SPELLINGS[lowered]
    if lowered in COLOUR_KEYWORDS:
        return value

    match = RGB_FUNCTION.match(value)
    if match:
        red, green, blue, alpha = match.groups()
        channels = [colour_channel(channel, value) for channel in (red, green, blue)]
        prefix = f"{alpha_channel(alpha, value):02X}" if alpha is not None else ""
        return "#" + prefix + "".join(f"{channel:02X}" for channel in channels)

    lowered = value.lower()
    if lowered == "currentcolor":
        hint = "bind the WPF brush explicitly or replace it with a concrete colour"
    elif lowered.startswith("url("):
        hint = "flatten the gradient or pattern to a solid colour in the source SVG"
    else:
        hint = "use a hex colour such as #B8C6E0, or a colour keyword"
    raise ConversionError(f"{role} value {value!r} is not a WPF colour; {hint}")


def effective_paint(
    value: str | None,
    role: str,
    gradients: dict[str, LinearGradient],
) -> str | LinearGradient | None:
    """Resolve solid paint or a local SVG linear-gradient into a WPF paint."""
    try:
        return resolve_paint(value, role, gradients, wpf_paint)
    except ValueError as error:
        raise ConversionError(str(error)) from error


def parse_style(value: str) -> dict[str, str]:
    """Parse an inline `style` attribute into lowercase property declarations."""
    declarations: dict[str, str] = {}
    for declaration in value.split(";"):
        name, separator, raw_value = declaration.partition(":")
        if separator:
            declarations[name.strip().lower()] = raw_value.strip()
    return declarations


def presentation(
    element: ElementTree.Element, declarations: dict[str, str], name: str, fallback: str
) -> str:
    """Resolve a presentation property; an inline `style` outranks the plain attribute."""
    return declarations.get(name, element.attrib.get(name, fallback))


def normalized_fill_rule(value: str) -> str:
    """Normalize an SVG fill-rule, defaulting anything unrecognized to nonzero."""
    return "evenodd" if value.strip().lower() == "evenodd" else "nonzero"


def number(value: float) -> str:
    """Format a coordinate without a trailing fraction, so output stays readable."""
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-", "-0") else text


def length(element: ElementTree.Element, name: str, default: float = 0.0) -> float:
    """Read a user-unit length; percentages need a viewport this converter never reads."""
    raw = element.attrib.get(name, "").strip()
    if not raw:
        return default
    normalized = raw[:-2].strip() if raw.lower().endswith("px") else raw
    try:
        return float(normalized)
    except ValueError:
        shape = local_name(element.tag)
        hint = (
            "percentages need a viewport, which is not converted; use user units"
            if raw.endswith("%")
            else "use a plain number in user units"
        )
        raise ConversionError(f"<{shape}> has an unsupported {name} of {raw!r}; {hint}") from None


def corner_radii(element: ElementTree.Element, width: float, height: float) -> tuple[float, float]:
    """Resolve a rect's rx/ry, where either one alone mirrors onto the other."""
    has_rx = "rx" in element.attrib and element.attrib["rx"].strip().lower() != "auto"
    has_ry = "ry" in element.attrib and element.attrib["ry"].strip().lower() != "auto"
    if not has_rx and not has_ry:
        return 0.0, 0.0
    rx = length(element, "rx") if has_rx else length(element, "ry")
    ry = length(element, "ry") if has_ry else rx
    return min(max(rx, 0.0), width / 2), min(max(ry, 0.0), height / 2)


def rect_data(element: ElementTree.Element) -> str | None:
    """Build the SVG 2 normative equivalent path for <rect>."""
    width, height = length(element, "width"), length(element, "height")
    if width <= 0 or height <= 0:
        return None
    x, y = length(element, "x"), length(element, "y")
    rx, ry = corner_radii(element, width, height)
    if rx <= 0 or ry <= 0:
        return (
            f"M{number(x)},{number(y)} H{number(x + width)} "
            f"V{number(y + height)} H{number(x)} Z"
        )
    arc = f"A{number(rx)},{number(ry)} 0 0 1"
    return (
        f"M{number(x + rx)},{number(y)} "
        f"H{number(x + width - rx)} "
        f"{arc} {number(x + width)},{number(y + ry)} "
        f"V{number(y + height - ry)} "
        f"{arc} {number(x + width - rx)},{number(y + height)} "
        f"H{number(x + rx)} "
        f"{arc} {number(x)},{number(y + height - ry)} "
        f"V{number(y + ry)} "
        f"{arc} {number(x + rx)},{number(y)} Z"
    )


def ellipse_data(element: ElementTree.Element, rx: float, ry: float) -> str | None:
    """Build the SVG 2 normative four-arc equivalent path for <circle> and <ellipse>."""
    if rx <= 0 or ry <= 0:
        return None
    cx, cy = length(element, "cx"), length(element, "cy")
    arc = f"A{number(rx)},{number(ry)} 0 0 1"
    return (
        f"M{number(cx + rx)},{number(cy)} "
        f"{arc} {number(cx)},{number(cy + ry)} "
        f"{arc} {number(cx - rx)},{number(cy)} "
        f"{arc} {number(cx)},{number(cy - ry)} "
        f"{arc} {number(cx + rx)},{number(cy)} Z"
    )


def points_data(element: ElementTree.Element, close: bool) -> str | None:
    """Build the equivalent path for <polyline> and <polygon>."""
    raw = element.attrib.get("points", "").replace(",", " ").split()
    try:
        values = [float(value) for value in raw]
    except ValueError:
        shape = local_name(element.tag)
        raise ConversionError(f"<{shape}> has unreadable points {element.attrib['points']!r}")
    if len(values) < 4:
        return None
    pairs = list(zip(values[::2], values[1::2]))
    moveto = f"M{number(pairs[0][0])},{number(pairs[0][1])}"
    lines = " ".join(f"L{number(x)},{number(y)}" for x, y in pairs[1:])
    return f"{moveto} {lines}{' Z' if close else ''}"


def shape_data(element: ElementTree.Element) -> str | None:
    """Convert a basic shape to exactly equivalent path data, or None if it never paints."""
    name = local_name(element.tag)
    if name == "rect":
        return rect_data(element)
    if name == "circle":
        radius = length(element, "r")
        return ellipse_data(element, radius, radius)
    if name == "ellipse":
        return ellipse_data(element, length(element, "rx"), length(element, "ry"))
    if name == "line":
        x1, y1 = length(element, "x1"), length(element, "y1")
        x2, y2 = length(element, "x2"), length(element, "y2")
        return f"M{number(x1)},{number(y1)} L{number(x2)},{number(y2)}"
    if name in ("polyline", "polygon"):
        return points_data(element, close=name == "polygon")
    return None


def multiply(left: Matrix, right: Matrix) -> Matrix:
    """Compose two affine transforms, applying `right` before `left` as SVG does."""
    a1, b1, c1, d1, e1, f1 = left
    a2, b2, c2, d2, e2, f2 = right
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def transform_function(name: str, values: list[float], source: str) -> Matrix:
    """Build the matrix for one SVG transform function."""
    count = len(values)
    if name == "matrix" and count == 6:
        return (values[0], values[1], values[2], values[3], values[4], values[5])
    if name == "translate" and count in (1, 2):
        return (1.0, 0.0, 0.0, 1.0, values[0], values[1] if count == 2 else 0.0)
    if name == "scale" and count in (1, 2):
        return (values[0], 0.0, 0.0, values[1] if count == 2 else values[0], 0.0, 0.0)
    if name == "rotate" and count in (1, 3):
        radians = math.radians(values[0])
        cosine, sine = math.cos(radians), math.sin(radians)
        rotation = (cosine, sine, -sine, cosine, 0.0, 0.0)
        if count == 1:
            return rotation
        centre_x, centre_y = values[1], values[2]
        return multiply(
            multiply((1.0, 0.0, 0.0, 1.0, centre_x, centre_y), rotation),
            (1.0, 0.0, 0.0, 1.0, -centre_x, -centre_y),
        )
    if name in ("skewX", "skewY") and count == 1:
        tangent = math.tan(math.radians(values[0]))
        if name == "skewX":
            return (1.0, 0.0, tangent, 1.0, 0.0, 0.0)
        return (1.0, tangent, 0.0, 1.0, 0.0, 0.0)
    raise ConversionError(
        f"transform {source!r} uses {name}() with {count} argument(s), which is not a "
        "valid SVG transform; fix or flatten the transform in the source SVG"
    )


def parse_transform(source: str) -> Matrix:
    """Compose an SVG transform list into a single affine matrix, left to right."""
    result = IDENTITY
    position = 0
    for match in TRANSFORM_FUNCTION.finditer(source):
        if source[position:match.start()].strip(", \t\r\n"):
            raise ConversionError(f"transform {source!r} could not be parsed")
        position = match.end()
        name, arguments = match.group(1), match.group(2)
        raw = [value for value in NUMBER_SEPARATOR.split(arguments.strip()) if value]
        try:
            values = [float(value) for value in raw]
        except ValueError:
            raise ConversionError(
                f"transform {source!r} has an unreadable argument in {name}({arguments.strip()})"
            ) from None
        result = multiply(result, transform_function(name, values, source))
    if position == 0 or source[position:].strip(", \t\r\n"):
        raise ConversionError(f"transform {source!r} could not be parsed")
    return result


def matrix_attribute(matrix: Matrix) -> str:
    """Render a WPF Matrix, whose M11..OffsetY order matches SVG's a,b,c,d,e,f."""
    return ",".join(number(value) for value in matrix)


def collect_paths(root: ElementTree.Element) -> tuple[list[SvgPath], list[str]]:
    """Collect rendered paths in document order and conversion warnings."""
    try:
        gradients = collect_linear_gradients(root, wpf_paint, parse_transform)
    except ValueError as error:
        raise ConversionError(str(error)) from error
    paths: list[SvgPath] = []
    warnings: list[str] = []
    saw_class = False
    ignored_properties: set[str] = set()
    skipped_shapes: set[str] = set()
    stack = [(root, Inherited())]

    while stack:
        element, inherited = stack.pop()
        element_name = local_name(element.tag)
        if element_name in NON_RENDERED_TAGS:
            continue
        if element_name in UNCONVERTIBLE_TAGS:
            # Prune the subtree: <text> children would otherwise each warn again.
            skipped_shapes.add(element_name)
            continue

        saw_class = saw_class or "class" in element.attrib
        declarations = parse_style(element.attrib.get("style", ""))
        ignored_properties.update(set(declarations) - CONVERTED_STYLE_PROPERTIES)
        if presentation(element, declarations, "display", "").strip().lower() == "none":
            continue

        current = Inherited(
            fill=presentation(element, declarations, "fill", inherited.fill),
            stroke=presentation(element, declarations, "stroke", inherited.stroke),
            fill_rule=presentation(element, declarations, "fill-rule", inherited.fill_rule),
            visibility=presentation(element, declarations, "visibility", inherited.visibility),
            matrix=inherited.matrix,
        )
        transform = presentation(element, declarations, "transform", "").strip()
        if transform:
            current = replace(
                current, matrix=multiply(current.matrix, parse_transform(transform))
            )

        if element_name == "path":
            data = element.attrib.get("d", "").strip()
        elif element_name in CONVERTED_SHAPE_TAGS:
            data = shape_data(element)
        else:
            data = None

        if data and current.visibility.strip().lower() != "hidden":
            paths.append(
                SvgPath(
                    data=data,
                    fill=effective_paint(current.fill, "fill", gradients),
                    stroke=effective_paint(current.stroke, "stroke", gradients),
                    fill_rule=normalized_fill_rule(current.fill_rule),
                    matrix=current.matrix,
                )
            )

        for child in reversed(list(element)):
            stack.append((child, current))

    if saw_class:
        warnings.append(
            "warning: class attributes were encountered; CSS classes were not converted."
        )
    if ignored_properties:
        warnings.append(
            "warning: unconverted style declarations were ignored: "
            + ", ".join(sorted(ignored_properties))
            + "."
        )
    if skipped_shapes:
        warnings.append(
            "warning: these elements have no exact path equivalent and were skipped: "
            + ", ".join(f"<{shape}>" for shape in sorted(skipped_shapes))
            + "; convert them to paths in the source SVG if they are needed."
        )
    if not paths:
        raise ConversionError(
            "No convertible geometry found; expected <path> with a nonempty d, "
            "or a <rect>/<circle>/<ellipse>/<line>/<polyline>/<polygon>"
        )

    return paths, warnings


def attribute(name: str, value: str) -> str:
    """Render an XML attribute using double quotes and XML escaping."""
    return f'{name}="{escape(value, quote=True)}"'


def absolute_start(data: str) -> str:
    """Force a path's leading moveto to be absolute before it is concatenated.

    SVG treats the first moveto of a `d` attribute as absolute whichever case it is
    written in, but a lowercase `m` further along the same geometry is relative to the
    previous subpath's current point. Concatenating a path that starts with `m` would
    therefore silently displace it — which is exactly how SVGO and Bootstrap Icons
    write every path after the first.
    """
    stripped = data.lstrip()
    return "M" + stripped[1:] if stripped[:1] == "m" else data


def concatenated(paths: Iterable[SvgPath]) -> str:
    """Join path data in document order, keeping each path anchored where it was."""
    return " ".join(absolute_start(path.data) for path in paths)


def geometry(fill_rule: str, data: str) -> str:
    """Prefix path data with the WPF fill rule matching SVG's nonzero default."""
    return f"{FILL_RULE_PREFIXES[fill_rule]} {data}"


def render_linear_gradient(gradient: LinearGradient, indent: str) -> list[str]:
    """Render a resolved SVG gradient as a WPF LinearGradientBrush."""
    attributes = [
        attribute("StartPoint", point(gradient.start_x, gradient.start_y)),
        attribute("EndPoint", point(gradient.end_x, gradient.end_y)),
        attribute("MappingMode", gradient.mapping_mode),
    ]
    lines = [f"{indent}<LinearGradientBrush {' '.join(attributes)}>"]
    for stop in gradient.stops:
        lines.append(
            f"{indent}  <GradientStop {attribute('Color', stop.color)} "
            f"{attribute('Offset', number(stop.offset))} />"
        )
    if gradient.transform != IDENTITY:
        lines.extend([
            f"{indent}  <LinearGradientBrush.Transform>",
            f'{indent}    <MatrixTransform Matrix="{matrix_attribute(gradient.transform)}" />',
            f"{indent}  </LinearGradientBrush.Transform>",
        ])
    lines.append(f"{indent}</LinearGradientBrush>")
    return lines


def render_path(path: SvgPath) -> str:
    """Render one WPF Path, preserving solid and local linear-gradient brushes."""
    attributes: list[str] = []
    if isinstance(path.fill, str):
        attributes.append(attribute("Fill", path.fill))
    if isinstance(path.stroke, str):
        attributes.append(attribute("Stroke", path.stroke))
    attributes.append(attribute("Data", geometry(path.fill_rule, path.data)))
    has_nested = isinstance(path.fill, LinearGradient) or isinstance(path.stroke, LinearGradient) or path.matrix != IDENTITY
    element = f"<Path {' '.join(attributes)}"
    if not has_nested:
        return element + " />"
    lines = [element + ">"]
    if isinstance(path.fill, LinearGradient):
        lines.append("  <Path.Fill>")
        lines.extend(render_linear_gradient(path.fill, "    "))
        lines.append("  </Path.Fill>")
    if isinstance(path.stroke, LinearGradient):
        lines.append("  <Path.Stroke>")
        lines.extend(render_linear_gradient(path.stroke, "    "))
        lines.append("  </Path.Stroke>")
    if path.matrix != IDENTITY:
        lines.extend([
            "  <Path.RenderTransform>",
            f'    <MatrixTransform Matrix="{matrix_attribute(path.matrix)}" />',
            "  </Path.RenderTransform>",
        ])
    lines.append("</Path>")
    return "\n".join(lines)


def render_geometry_drawing(path: SvgPath, indent: str) -> list[str]:
    """Render one source shape inside a DrawingGroup without losing paint order."""
    if path.stroke is not None:
        raise ConversionError("drawing output does not yet support SVG stroke; use --format xaml")
    data = attribute("Geometry", geometry(path.fill_rule, path.data))
    if isinstance(path.fill, str):
        return [f"{indent}<GeometryDrawing {attribute('Brush', path.fill)} {data} />"]
    lines = [f"{indent}<GeometryDrawing {data}>"]
    if isinstance(path.fill, LinearGradient):
        lines.append(f"{indent}  <GeometryDrawing.Brush>")
        lines.extend(render_linear_gradient(path.fill, indent + "    "))
        lines.append(f"{indent}  </GeometryDrawing.Brush>")
    lines.append(f"{indent}</GeometryDrawing>")
    return lines


def render_drawing(paths: Iterable[SvgPath], parent_matrix: Matrix) -> str:
    """Render ordered source paths as a parent-coordinate WPF DrawingGroup."""
    lines = ["<DrawingGroup>"]
    if parent_matrix != IDENTITY:
        lines.extend([
            "  <DrawingGroup.Transform>",
            f'    <MatrixTransform Matrix="{matrix_attribute(parent_matrix)}" />',
            "  </DrawingGroup.Transform>",
        ])
    for path in paths:
        if path.matrix == IDENTITY:
            lines.extend(render_geometry_drawing(path, "  "))
            continue
        lines.append("  <DrawingGroup>")
        lines.extend([
            "    <DrawingGroup.Transform>",
            f'      <MatrixTransform Matrix="{matrix_attribute(path.matrix)}" />',
            "    </DrawingGroup.Transform>",
        ])
        lines.extend(render_geometry_drawing(path, "    "))
        lines.append("  </DrawingGroup>")
    lines.append("</DrawingGroup>")
    return "\n".join(lines) + "\n"


def render_xaml(paths: Iterable[SvgPath], merge: bool = True) -> tuple[str, list[str]]:
    """Render one merged Path when presentation matches, otherwise render every path."""
    path_list = list(paths)
    styles = {(path.fill, path.stroke, path.fill_rule, path.matrix) for path in path_list}
    if merge and len(styles) == 1:
        first = path_list[0]
        merged = SvgPath(
            concatenated(path_list),
            first.fill,
            first.stroke,
            first.fill_rule,
            first.matrix,
        )
        return render_path(merged) + "\n", []

    warnings = (
        []
        if merge is False or len(path_list) == 1
        else [
            "warning: multiple fill/stroke/fill-rule/transform combinations found; "
            "emitting separate Path elements."
        ]
    )
    return "\n".join(render_path(path) for path in path_list) + "\n", warnings


def render_data(paths: list[SvgPath]) -> tuple[str, list[str]]:
    """Render every path's data as one geometry, which carries a single fill rule."""
    if any(isinstance(path.fill, LinearGradient) or isinstance(path.stroke, LinearGradient) for path in paths):
        raise ConversionError(
            "SVG linear gradients cannot be represented by Path.Data; use --format drawing or --format xaml"
        )
    transformed = [path for path in paths if path.matrix != IDENTITY]
    if transformed:
        raise ConversionError(
            f"{len(transformed)} of {len(paths)} paths carry an SVG transform, which path "
            "data alone cannot express; use --format xaml to emit a MatrixTransform, or "
            "flatten the transform in the source SVG"
        )
    warnings: list[str] = []
    if len({path.fill_rule for path in paths}) > 1:
        warnings.append(
            "warning: multiple fill rules found; data output uses the first path's rule."
        )
    return geometry(paths[0].fill_rule, concatenated(paths)) + "\n", warnings


def read_source(arguments: argparse.Namespace) -> str:
    """Read the mutually exclusive selected source using the specified encoding."""
    if arguments.file is not None:
        try:
            return Path(arguments.file).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError, ValueError) as error:
            raise ConversionError(f"could not read input file: {error}") from error
    if arguments.svg is not None:
        return arguments.svg
    try:
        # Match --file: decode as UTF-8 regardless of the console code page, which is
        # GBK on Chinese Windows and would mangle non-ASCII markup piped in.
        sys.stdin.reconfigure(encoding="utf-8-sig", errors="strict")
        return sys.stdin.read()
    except (OSError, UnicodeError, ValueError) as error:
        raise ConversionError(f"could not read standard input: {error}") from error


def parse_svg(source: str) -> ElementTree.Element:
    """Parse SVG XML and normalize parser errors for the command-line interface."""
    # An internal DTD subset is what lets a hostile file mount an entity-expansion
    # attack on Python versions predating expat's amplification limit; rejecting it
    # keeps this converter dependency-free. A bare external DTD reference is the
    # normal iconfont/Illustrator preamble and carries no entities to expand, since
    # expat does not fetch external DTDs.
    if INTERNAL_DTD_SUBSET.search(source):
        raise ConversionError(
            "SVG declares an internal DTD subset, whose entities are not expanded; "
            "remove the [...] block from the DOCTYPE and convert again"
        )
    try:
        return ElementTree.fromstring(source)
    except ElementTree.ParseError as error:
        raise ConversionError(f"invalid XML: {error}") from error


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Merge SVG paths into WPF XAML paths.")
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--file", metavar="PATH", help="read SVG XML from a UTF-8 file")
    sources.add_argument("--svg", metavar="TEXT", help="SVG XML text")
    sources.add_argument("--stdin", action="store_true", help="read SVG XML from standard input")
    parser.add_argument("--format", choices=("data", "xaml", "drawing"), default="xaml")
    parser.add_argument(
        "--parent-transform", default="", metavar="SVG_TRANSFORM",
        help="optional parent DrawingGroup SVG transform, e.g. 'translate(12 8)'",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="emit one Path per source path even when their paint matches",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the SVG conversion CLI."""
    arguments = build_parser().parse_args(argv)
    try:
        root = parse_svg(read_source(arguments))
        paths, warnings = collect_paths(root)
        if arguments.format == "data":
            output, format_warnings = render_data(paths)
        elif arguments.format == "drawing":
            parent_matrix = parse_transform(arguments.parent_transform) if arguments.parent_transform.strip() else IDENTITY
            output, format_warnings = render_drawing(paths, parent_matrix), []
        else:
            output, format_warnings = render_xaml(paths, merge=not arguments.no_merge)
        warnings.extend(format_warnings)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(warning, file=sys.stderr)
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
