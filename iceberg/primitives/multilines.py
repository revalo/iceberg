import itertools
from typing import List, Optional, Sequence, Tuple, Union
import numpy as np
import skia

from iceberg.core import Drawable, Bounds
from iceberg.core.properties import PathStyle, Corner
from iceberg.primitives.shapes import Path, Line
from iceberg.primitives.layout import Compose
from iceberg.arrows import arrow_corners, ArrowHeadStyle


class MultiLine(Compose):
    def __init__(
        self,
        points: Sequence[Tuple[float, float]],
        path_style: PathStyle,
        head_length: float = 20,
        angle: float = 30,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
        arrow_head_start: bool = False,
        arrow_head_end: bool = False,
        corner_radius: float = 0,
        smooth: bool = False,
    ):
        assert len(points) >= 2

        self._points = points

        start = points[0]
        end = points[-1]
        start_corners = arrow_corners(points[1], start, angle, head_length)
        end_corners = arrow_corners(points[-2], end, angle, head_length)

        if arrow_head_style == ArrowHeadStyle.FILLED_TRIANGLE:
            items = [Line(start, end, path_style)]

            head_path_style = PathStyle(
                color=path_style.color,
                stroke=False,
                anti_alias=path_style.anti_alias,
            )

            if arrow_head_end:
                path = skia.Path()
                path.moveTo(*end_corners[0])
                path.lineTo(*end)
                path.lineTo(*end_corners[1])
                path.close()
                arrow_head = Path(path, head_path_style)
                arrow_head_2 = Path(path, path_style)
                items.append(arrow_head)
                items.append(arrow_head_2)

            if arrow_head_start:
                path = skia.Path()
                path.moveTo(*start_corners[0])
                path.lineTo(*start)
                path.lineTo(*start_corners[1])
                path.close()
                arrow_head = Path(path, head_path_style)
                arrow_head_2 = Path(path, path_style)
                items.append(arrow_head)
                items.append(arrow_head_2)

            super().__init__(items)
        elif arrow_head_style == ArrowHeadStyle.TRIANGLE:
            items = []
            if arrow_head_end:
                path = skia.Path()
                path.moveTo(*end_corners[0])
                path.lineTo(*end)
                path.lineTo(*end_corners[1])
                path.moveTo(*end)
                if smooth:
                    assert corner_radius == 0
                    midpoints = [start]
                    midpoints += [
                        ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                        for p1, p2 in zip(points[1:-2], points[2:-1])
                    ]
                    midpoints.append(end)
                    for direction_point, midpoint in zip(
                        points[-2:0:-1], midpoints[-2::-1]
                    ):
                        path.quadTo(direction_point, midpoint)
                    path.lineTo(*start)
                elif corner_radius == 0:
                    for point in points[-2::-1]:
                        path.lineTo(*point)
                else:
                    for point, next in zip(points[-2:0:-1], points[-3::-1]):
                        path.arcTo(point, next, corner_radius)
                    path.lineTo(*start)

                items.append(Path(path, path_style))

            if arrow_head_start:
                path = skia.Path()
                path.moveTo(*start_corners[0])
                path.lineTo(*start)
                path.lineTo(*start_corners[1])
                path.moveTo(*start)
                if smooth:
                    assert corner_radius == 0
                    midpoints = [start]
                    midpoints += [
                        ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                        for p1, p2 in zip(points[1:-2], points[2:-1])
                    ]
                    midpoints.append(end)
                    for direction_point, midpoint in zip(points[1:-1], midpoints[1:]):
                        path.quadTo(direction_point, midpoint)
                    path.lineTo(*end)
                elif corner_radius == 0:
                    for point in points[1:]:
                        path.lineTo(*point)
                else:
                    for point, next in zip(points[1:-1], points[2:]):
                        path.arcTo(point, next, corner_radius)
                    path.lineTo(*end)
                items.append(Path(path, path_style))

            super().__init__(items)
        else:
            raise ValueError(f"Unknown arrow head style: {arrow_head_style}")

    @property
    def points(self) -> Sequence[Tuple[float, float]]:
        return self._points


class AutoLine(MultiLine):
    UP = "u"
    LEFT = "l"
    DOWN = "d"
    RIGHT = "r"

    _VERTICAL = {UP, DOWN}
    _HORIZONTAL = {LEFT, RIGHT}

    _VERTICAL_DICT = {
        UP: -1,
        LEFT: 0,
        DOWN: 1,
        RIGHT: 0,
    }

    _HORIZONTAL_DICT = {
        UP: 0,
        LEFT: -1,
        DOWN: 0,
        RIGHT: 1,
    }

    def __init__(
        self,
        start: Union[Tuple[float, float], Drawable, Bounds],
        end: Union[Tuple[float, float], Drawable, Bounds],
        directions: str,
        path_style: PathStyle,
        x_padding: float = 0,
        y_padding: Optional[float] = None,
        context: Optional[Drawable] = None,
        **kwargs,
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
            if directions[0] == self.UP:
                start = start.corners[Corner.TOP_MIDDLE]
            elif directions[0] == self.LEFT:
                start = start.corners[Corner.MIDDLE_LEFT]
            elif directions[0] == self.DOWN:
                start = start.corners[Corner.BOTTOM_MIDDLE]
            elif directions[0] == self.RIGHT:
                start = start.corners[Corner.MIDDLE_RIGHT]
        if isinstance(end, Bounds):
            if directions[-1] == self.UP:
                end = end.corners[Corner.BOTTOM_MIDDLE]
            elif directions[-1] == self.LEFT:
                end = end.corners[Corner.MIDDLE_RIGHT]
            elif directions[-1] == self.DOWN:
                end = end.corners[Corner.TOP_MIDDLE]
            elif directions[-1] == self.RIGHT:
                end = end.corners[Corner.MIDDLE_LEFT]

        assert isinstance(start, tuple)
        assert isinstance(end, tuple)

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        if not set(directions) <= (self._VERTICAL | self._HORIZONTAL):
            print(set(directions))
            print(self._VERTICAL | self._HORIZONTAL)
            raise ValueError("Directions must be a sequence of 'u', 'l', 'd', or 'r'.")

        x_movements = [self._HORIZONTAL_DICT[direction] for direction in directions]
        y_movements = [self._VERTICAL_DICT[direction] for direction in directions]

        x_deltas = self._parse_1d_directions(x_movements, dx, x_padding)
        y_deltas = self._parse_1d_directions(y_movements, dy, y_padding)

        x_positions = [start[0] + delta for delta in x_deltas]
        y_positions = [start[1] + delta for delta in y_deltas]

        points = list(zip(x_positions, y_positions))

        assert points[-1] == end, f"{points[-1]} != {end}"

        super().__init__(points, path_style, **kwargs)

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
