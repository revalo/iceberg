import itertools
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import skia

from iceberg.core.drawable import Drawable
from iceberg.core.properties import Bounds, Corner, PathStyle, SplineType

from .shapes import Path


class GeneralLine(Path):
    points: Sequence[Tuple[float, float]]
    path_style: PathStyle
    spline: SplineType = SplineType.LINEAR
    corner_radius: float = 0

    def setup(self):
        assert len(self.points) >= 2

        self._points = np.array(self.points)
        self._midpoints = (self._points[:-1] + self._points[1:]) / 2

        path = skia.Path()
        path.moveTo(*self.points[0])

        if self.corner_radius != 0:
            if self.spline != SplineType.LINEAR:
                raise ValueError(
                    f"Corner radius can only be used with linear splines, got {self.spline}."
                )
            for point, next_point in zip(self.points[1:-1], self.points[2:]):
                path.arcTo(point, next_point, self.corner_radius)
            path.lineTo(*self.points[-1])
        elif self.spline == SplineType.LINEAR:
            for point in self.points[1:]:
                path.lineTo(*point)
        elif self.spline == SplineType.QUADRATIC:
            # Take points in groups of 2 and draw a quadratic line.
            for i in range(1, len(self.points) - 1, 2):
                path.quadTo(*self.points[i], *self.points[i + 1])
        elif self.spline == SplineType.CUBIC:
            # Take points in groups of 3 and draw a cubic line.
            for i in range(1, len(self.points) - 2, 3):
                path.cubicTo(*self.points[i], *self.points[i + 1], *self.points[i + 2])
        else:
            raise ValueError(f"Unknown spline type {self.spline}.")

        super().set_path(skia_path=path, path_style=self.path_style)

    # @property
    # def points(self) -> np.ndarray:
    #     """The corner points of the line, shape (n, 2)."""
    #     return self._points

    # @property
    # def midpoints(self) -> np.ndarray:
    #     """The midpoints of the line segments."""
    #     return self._midpoints

    # @property
    # def start(self) -> np.ndarray:
    #     """The start of the line."""
    #     return self.points[0]

    # @property
    # def end(self) -> np.ndarray:
    #     """The end of the line."""
    #     return self.points[-1]


_UP = "u"
_LEFT = "l"
_DOWN = "d"
_RIGHT = "r"

_VERTICAL = {_UP, _DOWN}
_HORIZONTAL = {_LEFT, _RIGHT}

_VERTICAL_DICT = {
    _UP: -1,
    _LEFT: 0,
    _DOWN: 1,
    _RIGHT: 0,
}

_HORIZONTAL_DICT = {
    _UP: 0,
    _LEFT: -1,
    _DOWN: 0,
    _RIGHT: 1,
}


class AutoLine(GeneralLine):
    def __init__(
        self,
        start: Union[Tuple[float, float], Drawable, Bounds],
        end: Union[Tuple[float, float], Drawable, Bounds],
        directions: str,
        path_style: PathStyle,
        x_padding: float = 0,
        y_padding: Optional[float] = None,
        context: Optional[Drawable] = None,
        spline: SplineType = SplineType.LINEAR,
        corner_radius: float = 0,
    ):
        if y_padding is None:
            y_padding = x_padding

        if context is not None:
            with context:
                if isinstance(start, Drawable):
                    start = start.relative_bounds
                if isinstance(end, Drawable):
                    end = end.relative_bounds
        else:
            if isinstance(start, Drawable):
                start = start.bounds
            if isinstance(end, Drawable):
                end = end.bounds

        if isinstance(start, Bounds):
            if directions[0] == _UP:
                start = start.corners[Corner.TOP_MIDDLE]
            elif directions[0] == _LEFT:
                start = start.corners[Corner.MIDDLE_LEFT]
            elif directions[0] == _DOWN:
                start = start.corners[Corner.BOTTOM_MIDDLE]
            elif directions[0] == _RIGHT:
                start = start.corners[Corner.MIDDLE_RIGHT]
        if isinstance(end, Bounds):
            if directions[-1] == _UP:
                end = end.corners[Corner.BOTTOM_MIDDLE]
            elif directions[-1] == _LEFT:
                end = end.corners[Corner.MIDDLE_RIGHT]
            elif directions[-1] == _DOWN:
                end = end.corners[Corner.TOP_MIDDLE]
            elif directions[-1] == _RIGHT:
                end = end.corners[Corner.MIDDLE_LEFT]

        assert isinstance(start, tuple)
        assert isinstance(end, tuple)

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        if not set(directions) <= (_VERTICAL | _HORIZONTAL):
            raise ValueError("Directions must be a sequence of 'u', 'l', 'd', or 'r'.")

        x_movements = [_HORIZONTAL_DICT[direction] for direction in directions]
        y_movements = [_VERTICAL_DICT[direction] for direction in directions]

        x_deltas = self._parse_1d_directions(x_movements, dx, x_padding)
        y_deltas = self._parse_1d_directions(y_movements, dy, y_padding)

        x_positions = [start[0] + delta for delta in x_deltas]
        y_positions = [start[1] + delta for delta in y_deltas]

        points = list(zip(x_positions, y_positions))

        assert points[-1] == end, f"{points[-1]} != {end}"

        self.init_from_fields(
            points=points,
            path_style=path_style,
            spline=spline,
            corner_radius=corner_radius,
        )

    def _parse_1d_directions(self, directions: List[int], delta: float, pad: float):
        assert set(directions) <= {1, 0, -1}

        non_zero_directions = [d for d in directions if d != 0]
        groups = [list(group) for key, group in itertools.groupby(non_zero_directions)]

        maximum = max(0, delta) + pad
        minimum = min(0, delta) - pad

        key_points = [0]
        for i, group in enumerate(groups):
            current = key_points[-1]
            if i == len(groups) - 1:
                target = delta
            elif group[0] == 1:
                target = maximum
            else:
                target = minimum

            key_points.extend(np.linspace(current, target, len(group) + 1)[1:])

        # Now we need to take the zeros into account
        result = [key_points.pop(0)]
        for d in directions:
            if d == 0:
                result.append(result[-1])
            else:
                result.append(key_points.pop(0))

        assert len(key_points) == 0
        assert result[-1] == delta

        return result
