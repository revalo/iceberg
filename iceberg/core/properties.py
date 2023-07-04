from dataclasses import dataclass

from typing import List, Optional, Tuple
from enum import Enum

import skia
import numpy as np

from iceberg.geometry import apply_transform
from iceberg.animation import Animatable


class Corner(object):
    """Specifies the index of the corner in a corners array."""

    TOP_LEFT = 0
    TOP_MIDDLE = 1
    TOP_RIGHT = 2
    MIDDLE_RIGHT = 3
    BOTTOM_RIGHT = 4
    BOTTOM_MIDDLE = 5
    BOTTOM_LEFT = 6
    MIDDLE_LEFT = 7
    CENTER = 8


class Bounds(Animatable):
    """Represents a bounding box."""

    def __init__(
        self,
        top: float = 0,
        left: float = 0,
        bottom: float = None,
        right: float = None,
        center: Tuple[float, float] = None,
        size: Tuple[float, float] = None,
        position: Tuple[float, float] = None,
    ) -> None:
        """Create a new bounds object.

        Args:
            top: The top of the bounds.
            left: The left of the bounds.
            bottom: The bottom of the bounds.
            right: The right of the bounds.
            center: The center of the bounds.
            size: The size of the bounds.
            position: The position of the bounds.
        """

        # Convert everything that has been mentioned to a standard left, top, right, bottom.
        if center is not None and size is not None:
            cx, cy = center
            w, h = size

            left = cx - w / 2
            right = cx + w / 2
            top = cy - h / 2
            bottom = cy + h / 2
        elif position is not None and size is not None:
            x, y = position
            w, h = size

            left = x
            right = x + w
            top = y
            bottom = y + h
        elif position is None and size is not None:
            w, h = size
            right = left + w
            bottom = top + h

        self._left = left
        self._right = right
        self._top = top
        self._bottom = bottom

        self._compute_corners()

    @property
    def animatables(self):
        return [np.array([self.left, self.top, self.right, self.bottom])]

    def copy_with_animatables(self, animatables):
        scalars = animatables[0]
        return Bounds(*scalars)

    def transform(self, transform: np.ndarray):
        """Transform the bounds by the specified transform matrix.

        Args:
            transform: The 3x3 transform matrix to apply.

        Returns:
            The transformed bounds.
        """

        corners = self.corners
        transformed_corners = apply_transform(corners, transform)

        left, top = transformed_corners[Corner.TOP_LEFT]
        right, bottom = transformed_corners[Corner.BOTTOM_RIGHT]

        return Bounds(top, left, bottom, right)

    @property
    def left(self) -> float:
        return self._left

    @property
    def right(self) -> float:
        return self._right

    @property
    def top(self) -> float:
        return self._top

    @property
    def bottom(self) -> float:
        return self._bottom

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def center(self) -> Tuple[float, float]:
        return (self.left + self.right) / 2, (self.top + self.bottom) / 2

    def inset(self, dx: float, dy: Optional[float] = None) -> "Bounds":
        """Inset the bounds by the specified amount.

        Args:
            dx: The amount to inset the bounds in the x direction.
            dy: The amount to inset the bounds in the y direction.
                If `None`, then `dx` is used.

        Returns:
            The inset bounds.
        """
        if dy is None:
            dy = dx

        return Bounds(
            left=self.left + dx,
            right=self.right - dx,
            top=self.top + dy,
            bottom=self.bottom - dy,
        )

    def to_skia(self) -> skia.Rect:
        """Get the bounds as a skia.Rect."""

        return skia.Rect.MakeLTRB(self.left, self.top, self.right, self.bottom)

    def __repr__(self) -> str:
        return f"Bounds({self.left}, {self.top}, {self.right}, {self.bottom})"

    @classmethod
    def from_skia(cls, rect: skia.Rect) -> "Bounds":
        """Create a bounds object from a skia.Rect."""

        return cls(
            left=rect.left(),
            right=rect.right(),
            top=rect.top(),
            bottom=rect.bottom(),
        )

    @classmethod
    def empty(cls) -> "Bounds":
        """Create an empty bounds object."""

        return cls(
            left=0,
            right=0,
            bottom=0,
            top=0,
        )

    @classmethod
    def from_points(cls, points: Tuple[Tuple[float, float], ...]) -> "Bounds":
        """Create a bounds object from a list of points.

        Args:
            points: The 2D points to create the bounds from.

        Returns:
            The bounds object.
        """

        left = min([point[0] for point in points])
        right = max([point[0] for point in points])
        top = min([point[1] for point in points])
        bottom = max([point[1] for point in points])

        return cls(left=left, right=right, top=top, bottom=bottom)

    def _compute_corners(self) -> Tuple[Tuple[float, float], ...]:
        """Compute the corners of the bounds.

        Returns:
            The corners of the bounds.
        """

        top_left = (self.left, self.top)
        top_right = (self.right, self.top)
        bottom_right = (self.right, self.bottom)
        bottom_left = (self.left, self.bottom)
        top_middle = (self.left + self.width / 2, self.top)
        middle_right = (self.right, self.top + self.height / 2)
        bottom_middle = (self.left + self.width / 2, self.bottom)
        middle_left = (self.left, self.top + self.height / 2)
        center = (self.left + self.width / 2, self.top + self.height / 2)

        self._computed_corners = (
            top_left,
            top_middle,
            top_right,
            middle_right,
            bottom_right,
            bottom_middle,
            bottom_left,
            middle_left,
            center,
        )

    @property
    def corners(self) -> Tuple[Tuple[float, float], ...]:
        """Get the corners of the bounds.

        Returns:
            The corners of the bounds.
        """

        return self._computed_corners


class Color(Animatable):
    def __init__(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        """Create a color object.

        The color components should be in the range [0, 1].

        Args:
            r: The red component of the color.
            g: The green component of the color.
            b: The blue component of the color.
            a: The alpha component of the color.
        """

        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1
        assert 0 <= a <= 1

        self._r = r
        self._g = g
        self._b = b
        self._a = a

    @property
    def animatables(self):
        return [np.array([self.r, self.g, self.b, self.a])]

    def copy_with_animatables(self, animatables):
        r, g, b, a = animatables[0]
        return Color(r, g, b, a)

    @property
    def r(self) -> float:
        return self._r

    @property
    def g(self) -> float:
        return self._g

    @property
    def b(self) -> float:
        return self._b

    @property
    def a(self) -> float:
        return self._a

    def to_skia(self) -> skia.Color4f:
        """Get the color as a skia.Color4f."""
        return skia.Color4f(self.r, self.g, self.b, self.a)

    @classmethod
    def from_skia(cls, color: skia.Color4f) -> "Color":
        """Create a color object from a skia.Color4f."""
        return cls(color.r, color.g, color.b, color.a)

    @classmethod
    def from_hex(cls, hex: str) -> "Color":
        """Create a color object from a hex string.

        Args:
            hex: The hex string to create the color from.

        Returns:
            The color object.
        """

        hex = hex.lstrip("#")

        # Get RGB or RGBA from hex.
        if len(hex) == 6:
            return cls.from_rgb(
                int(hex[0:2], 16),
                int(hex[2:4], 16),
                int(hex[4:6], 16),
            )
        elif len(hex) == 8:
            return cls.from_rgba(
                int(hex[0:2], 16),
                int(hex[2:4], 16),
                int(hex[4:6], 16),
                int(hex[6:8], 16),
            )
        else:
            raise ValueError(f"Invalid hex value: {hex}")

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "Color":
        """Create a color object from RGB values in the range [0, 255].

        Args:
            r: The red component of the color.
            g: The green component of the color.
            b: The blue component of the color.

        Returns:
            The color object.
        """

        return cls(r / 255, g / 255, b / 255)

    @classmethod
    def from_rgba(cls, r: int, g: int, b: int, a: int) -> "Color":
        """Create a color object from RGBA values in the range [0, 255].

        Args:
            r: The red component of the color.
            g: The green component of the color.
            b: The blue component of the color.
            a: The alpha component of the color.

        Returns:
            The color object.
        """

        return cls(r / 255, g / 255, b / 255, a / 255)

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented

        return (
            self.r == other.r
            and self.g == other.g
            and self.b == other.b
            and self.a == other.a
        )

    def __hash__(self) -> int:
        return hash((self.r, self.g, self.b, self.a))

    def to_blend_int(self) -> int:
        """Get the color as an integer for blending.

        The format is 0xAARRGGBB. And the components are in the range [0, 255].

        Returns:
            The color as an integer.
        """

        a = int(self.a * 255)
        r = int(self.r * 255)
        g = int(self.g * 255)
        b = int(self.b * 255)

        return (a << 24) | (r << 16) | (g << 8) | b


class Colors(object):
    """A collection of common colors."""

    BLACK = Color.from_hex("#000000")
    WHITE = Color.from_hex("#FFFFFF")
    RED = Color.from_hex("#FF0000")
    GREEN = Color.from_hex("#00FF00")
    BLUE = Color.from_hex("#0000FF")
    YELLOW = Color.from_hex("#FFFF00")
    CYAN = Color.from_hex("#00FFFF")
    MAGENTA = Color.from_hex("#FF00FF")
    TRANSPARENT = Color.from_rgba(0, 0, 0, 0)


class StrokeCap(Enum):
    """The cap at the end of a stroke."""

    BUTT = skia.Paint.kButt_Cap
    ROUND = skia.Paint.kRound_Cap
    SQUARE = skia.Paint.kSquare_Cap


class PathStyle(Animatable):
    """A style for drawing paths."""

    def __init__(
        self,
        color: Color,
        thickness: float = 1.0,
        anti_alias: bool = True,
        stroke: bool = True,
        stroke_cap: StrokeCap = StrokeCap.BUTT,
    ):
        """Create a path style.

        Args:
            color: The color of the path.
            thickness: The thickness of the path.
            anti_alias: Whether to use anti-aliasing.
            stroke: Whether to stroke the path or fill it.
            stroke_cap: The cap at the end of a stroke.
        """

        self._color = color
        self._thickness = thickness
        self._anti_alias = anti_alias
        self._stroke = stroke
        self._stroke_cap = stroke_cap

        self._skia_paint = skia.Paint(
            Style=skia.Paint.kStroke_Style if stroke else skia.Paint.kFill_Style,
            AntiAlias=anti_alias,
            StrokeWidth=thickness,
            Color4f=color.to_skia(),
            StrokeCap=stroke_cap.value,
        )

    @property
    def animatables(self):
        return [self.color, self.thickness]

    def copy_with_animatables(self, animatables):
        color, thickness = animatables

        return PathStyle(
            color, thickness, self._anti_alias, self._stroke, self._stroke_cap
        )

    @property
    def color(self) -> Color:
        return self._color

    @property
    def thickness(self) -> float:
        return self._thickness

    @property
    def anti_alias(self) -> bool:
        return self._anti_alias

    @property
    def skia_paint(self) -> skia.Paint:
        return self._skia_paint

    def __repr__(self) -> str:
        return f"PathStyle({self.color}, {self.thickness}, {self.anti_alias}, {self._stroke}, {self._stroke_cap})"


@dataclass
class FontStyle(object):
    class Style(Enum):
        NORMAL = skia.FontStyle.Normal()
        ITALIC = skia.FontStyle.Italic()
        BOLD = skia.FontStyle.Bold()
        BOLD_ITALIC = skia.FontStyle.BoldItalic()

    family: str
    filename: str = None
    size: float = 16
    font_weight: int = 400
    font_style: Style = Style.NORMAL
    color: Color = Color(0, 0, 0)
    anti_alias: bool = True

    def __post_init__(self):
        families = set(FontStyle.available_fonts())
        if self.filename is None and not self.family in families:
            raise ValueError(
                f"Invalid font family: {self.family}. Please call FontStyle.get_available_fonts_families() to get the list of available fonts."
            )

    def get_skia_paint(self) -> skia.Paint:
        return skia.Paint(
            Style=skia.Paint.kFill_Style,
            AntiAlias=self.anti_alias,
            Color4f=self.color.to_skia(),
        )

    def get_skia_font(self) -> skia.Font:
        if self.filename is not None:
            return skia.Font(
                skia.Typeface.MakeFromFile(self.filename, self.font_style.value),
                self.size,
            )

        return skia.Font(
            skia.Typeface(self.family, self.font_style.value),
            self.size,
        )

    @staticmethod
    def available_fonts() -> List[str]:
        return list(skia.FontMgr())
