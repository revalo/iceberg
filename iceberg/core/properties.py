from typing import Tuple

import skia


class Bounds(object):
    def __init__(
        self,
        top: float = None,
        left: float = None,
        bottom: float = None,
        right: float = None,
        center: Tuple[float, float] = None,
        size: Tuple[float, float] = None,
        position: Tuple[float, float] = None,
    ) -> None:
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

        self._left = left
        self._right = right
        self._top = top
        self._bottom = bottom

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

    def inset(self, dx: float, dy: float) -> "Bounds":
        return Bounds(
            left=self.left + dx,
            right=self.right - dx,
            top=self.top + dy,
            bottom=self.bottom - dy,
        )

    def to_skia(self) -> skia.Rect:
        return skia.Rect.MakeLTRB(self.left, self.top, self.right, self.bottom)

    def __repr__(self) -> str:
        return f"Bounds({self.left}, {self.top}, {self.right}, {self.bottom})"


class Color(object):
    def __init__(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self._r = r
        self._g = g
        self._b = b
        self._a = a

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
        return skia.Color4f(self.r, self.g, self.b, self.a)

    @classmethod
    def from_skia(cls, color: skia.Color4f) -> "Color":
        return cls(color.r, color.g, color.b, color.a)

    @classmethod
    def from_hex(cls, hex: str) -> "Color":
        return cls(*skia.Color4f(hex).as4int())

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "Color":
        return cls(r / 255, g / 255, b / 255)

    @classmethod
    def from_rgba(cls, r: int, g: int, b: int, a: int) -> "Color":
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
