from enum import Enum
from typing import List, Optional, Sequence, Tuple, Union
import itertools

import numpy as np
import skia

from iceberg import PathStyle, Drawable, Bounds, Corner
from iceberg.primitives import Compose, Line, Path, PartialPath, Transform
from .helpers import ArrowHeadStyle, ArrowPath


class Arrow(ArrowPath):
    def __init__(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        line_path_style: PathStyle,
        head_length: float = 20,
        angle: float = 30,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
        arrow_head_start: bool = False,
        arrow_head_end: bool = True,
        partial_start: float = 0,
        partial_end: float = 1,
    ):
        """Create an arrow.

        Args:
            start: The start coordinate.
            end: The end coordinate.
            line_path_style: The style of the line.
            head_length: The length of the arrow head.
            angle: The angle of the arrow head in degrees.
            arrow_head_style: The style of the arrow head.
            arrow_head_start: Whether to draw an arrow head at the start.
            arrow_head_end: Whether to draw an arrow head at the end.
            partial_start: The fraction of the arrow to draw at the start.
            partial_end: The fraction of the arrow to draw at the end.
        """
        path = Line(start, end, line_path_style)
        super().__init__(
            path=path,
            arrow_head_start=arrow_head_start,
            arrow_head_end=arrow_head_end,
            angle=angle,
            head_length=head_length,
            arrow_head_style=arrow_head_style,
            partial_start=partial_start,
            partial_end=partial_end,
            subdivide_increment=1,
        )


class ArrowAlignDirection(Enum):
    ABOVE = 0
    BELOW = 1


class LabelArrowPath(Compose):
    def __init__(
        self,
        arrow: ArrowPath,
        child: Drawable,
        child_corner: int,
        t: float,
        placement: ArrowAlignDirection = ArrowAlignDirection.ABOVE,
        distance: float = 0,
        rotated: bool = False,
    ):
        """Combine an arrow alongside another drawable in a way that labels the arrow.

        Args:
            arrow: The arrow to be labeled.
            child: The label to be placed alongside the arrow.
            child_corner: The corner of the child to align with. See `Corner` for details.
            t: Where to place the label along the arrow (between 0 for start and 1 for end).
            placement: Whether to place the specified corner of the child above or below the arrow.
            distance: The distance between the arrow and the child's specified corner.
            rotated: Whether to rotate the child to match the arrow.
        """

        position, tangent = arrow.point_and_tangent_at(t)
        position = np.array(position, dtype=np.float32)

        # Find normal vector.
        # Note that tangent is already normalized.
        normal = np.array([-tangent[1], tangent[0]], dtype=np.float32)

        angle = np.arctan2(tangent[1], tangent[0]) if rotated else 0

        # Compute the displacement.
        displacement = distance * normal

        # Placement above or below.
        if placement == ArrowAlignDirection.ABOVE:
            displacement *= -1

        arrow_point = position + displacement

        delta = arrow_point - child.bounds.corners[child_corner]
        dx, dy = delta

        if rotated:
            cx, cy = child.bounds.center
            child = Transform(
                child,
                rotation=angle,
                rotation_in_degrees=False,
                anchor=(-cx, -cy),
            )

        child_transformed = Transform(
            child,
            position=(dx, dy),
        )

        super().__init__([arrow, child_transformed])


class LabelArrow(LabelArrowPath):
    def __init__(
        self,
        arrow: Arrow,
        child: Drawable,
        child_corner: int,
        placement: ArrowAlignDirection = ArrowAlignDirection.ABOVE,
        distance: float = 0,
        rotated: bool = False,
    ):
        """Combine an arrow alongside another drawable in a way that labels the arrow.

        Args:
            arrow: The arrow to be labeled.
            child: The label to be placed alongside the arrow.
            child_corner: The corner of the child to align with. See `Corner` for details.
            placement: Whether to place the specified corner of the child above or below the arrow.
            distance: The distance between the arrow and the child's specified corner.
            rotated: Whether to rotate the child to match the arrow.
        """

        super().__init__(
            arrow=arrow,
            child=child,
            child_corner=child_corner,
            t=0.5,
            placement=placement,
            distance=distance,
            rotated=rotated,
        )


class MultiArrow(ArrowPath):
    def __init__(
        self,
        points: Sequence[Tuple[float, float]],
        line_path_style: PathStyle,
        arrow_path_style: Optional[PathStyle] = None,
        head_length: float = 20,
        angle: float = 30,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
        arrow_head_start: bool = False,
        arrow_head_end: bool = False,
        corner_radius: float = 0,
        smooth: bool = False,
        partial_start: float = 0,
        partial_end: float = 1,
        subdivide_increment: float = 0.01,
        interpolation: PartialPath.Interpolation = PartialPath.Interpolation.CUBIC,
    ):
        assert len(points) >= 2

        self._points = np.array(points)
        self._midpoints = (self.points[:-1] + self.points[1:]) / 2

        start = points[0]
        end = points[-1]

        path = skia.Path()
        path.moveTo(start)

        if smooth:
            assert corner_radius == 0
            for direction_point, target_point in zip(points[1:-1], self.midpoints[1:]):
                path.quadTo(*direction_point, *target_point)
            path.lineTo(*end)
        elif corner_radius == 0:
            for point in points[1:]:
                path.lineTo(*point)
        else:
            for point, next_point in zip(points[1:-1], points[2:]):
                path.arcTo(point, next_point, corner_radius)
            path.lineTo(*end)

        super().__init__(
            Path(path, line_path_style),
            arrow_head_start=arrow_head_start,
            arrow_head_end=arrow_head_end,
            arrow_path_style=arrow_path_style,
            angle=angle,
            head_length=head_length,
            arrow_head_style=arrow_head_style,
            partial_start=partial_start,
            partial_end=partial_end,
            subdivide_increment=subdivide_increment,
            interpolation=interpolation,
        )

    @property
    def points(self) -> np.ndarray:
        """The corner points of the line, shape (n, 2)."""
        return self._points

    @property
    def midpoints(self) -> np.ndarray:
        """The midpoints of the line segments."""
        return self._midpoints

    @property
    def start(self) -> np.ndarray:
        """The start of the line."""
        return self.points[0]

    @property
    def end(self) -> np.ndarray:
        """The end of the lined."""
        return self.points[-1]


class AutoArrow(MultiArrow):
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
