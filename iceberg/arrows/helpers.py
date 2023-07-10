from copy import copy
from enum import Enum
from typing import Optional, Tuple

import numpy as np
import skia

from iceberg import PathStyle
from iceberg.animation.animatable import AnimatableSequence
from iceberg.primitives import Compose, Path, PartialPath


def arrow_corners_from_direction_and_point(
    point: Tuple[float, float],
    direction: Tuple[float, float],
    angle_degrees: float,
    distance: float,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    # Compute the direction of the arrow.
    direction = -np.array(direction, dtype=np.float32)
    direction /= np.linalg.norm(direction)

    point = np.array(point, dtype=np.float32)

    # Compute the angle of the arrow.
    angle = np.deg2rad(angle_degrees)

    # Compute the two corners of the arrow.
    corner1 = point + distance * (
        direction * np.cos(angle)
        + np.array([-direction[1], direction[0]]) * np.sin(angle)
    )
    corner2 = point + distance * (
        direction * np.cos(angle)
        + np.array([direction[1], -direction[0]]) * np.sin(angle)
    )

    return corner1, corner2


def arrow_corners(
    start: Tuple[float, float],
    end: Tuple[float, float],
    angle_degrees: float,
    distance: float,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Given a start and end coordinate, and an angle, compute where the two corners of the arrow are.

    Args:
        start: The start coordinate.
        end: The end coordinate.
        angle_degrees: The angle of the arrow.
        distance: The distance from the end coordinate to the arrow tip.

    Returns:
        The two corners of the arrow.
    """

    # Compute the direction of the arrow.
    direction = np.array(end, dtype=np.float32) - np.array(start)
    direction /= np.linalg.norm(direction)

    return arrow_corners_from_direction_and_point(
        end, direction, angle_degrees, distance
    )


class ArrowHeadStyle(Enum):
    TRIANGLE = 0
    FILLED_TRIANGLE = 1


class ArrowHead(Compose):
    def __init__(
        self,
        point: Tuple[float, float],
        direction: Tuple[float, float],
        line_path_style: PathStyle,
        angle: float = 30,
        head_length: float = 20,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
    ):
        """Just the arrow head.

        Args:
            point: The point of the arrow head.
            direction: The direction of the arrow head.
            line_path_style: The style of the line.
            angle: The angle of the arrow head in degrees.
            head_length: The length of the arrow head.
            arrow_head_style: The style of the arrow head.
        """

        items = []

        corners = arrow_corners_from_direction_and_point(
            point, direction, angle, head_length
        )

        if arrow_head_style == ArrowHeadStyle.FILLED_TRIANGLE:
            head_path_style = PathStyle(
                color=line_path_style.color,
                stroke=False,
                anti_alias=line_path_style.anti_alias,
            )

            path = skia.Path()
            path.moveTo(*corners[0])
            path.lineTo(*point)
            path.lineTo(*corners[1])
            path.close()

            items.append(Path(path, head_path_style))
            items.append(Path(path, line_path_style))
        elif arrow_head_style == ArrowHeadStyle.TRIANGLE:
            path = skia.Path()
            path.moveTo(*corners[0])
            path.lineTo(*point)
            path.lineTo(*corners[1])

            items.append(Path(path, line_path_style))
        else:
            raise ValueError(f"Unknown arrow head style {arrow_head_style}.")

        super().__init__(items)


class ArrowPath(Compose):
    def __init__(
        self,
        path: Path,
        arrow_head_start: bool = False,
        arrow_head_end: bool = True,
        arrow_path_style: Optional[PathStyle] = None,
        angle: float = 30,
        head_length: float = 20,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
        partial_start: float = 0,
        partial_end: float = 1,
        subdivide_increment: float = 0.01,
    ):
        if arrow_path_style is None:
            arrow_path_style = copy(path._path_style)

        self._path = path
        self._arrow_head_start = arrow_head_start
        self._arrow_head_end = arrow_head_end
        self._arrow_path_style = arrow_path_style
        self._angle = angle
        self._head_length = head_length
        self._arrow_head_style = arrow_head_style
        self._partial_start = partial_start
        self._partial_end = partial_end
        self._subdivide_increment = subdivide_increment

        backup_t = 0

        if arrow_head_end or arrow_head_start:
            # Create a fake arrow head to measure its length.
            fake_head = ArrowHead(
                (0, 0),
                (1, 0),
                arrow_path_style,
                angle,
                head_length,
                arrow_head_style,
            )
            backup_length = fake_head.bounds.right
            # Create a fake line to figure out where to backup to
            fake_line = PartialPath(
                path,
                partial_start,
                partial_end,
                subdivide_increment,
            )
            backup_t = backup_length / fake_line.total_length

        # Modified start and end points.
        # By default there is no modification.
        self._partial_start = partial_start
        self._partial_end = partial_end

        # Back-up or advance the start and end points.
        if arrow_head_end:
            self._partial_end -= backup_t
            self._partial_end = max(self._partial_end, 0)

        if arrow_head_start:
            self._partial_start += backup_t
            self._partial_start = min(self._partial_start, self._partial_end)

        items = []

        # Draw the line.
        line = PartialPath(
            path,
            self._partial_start,
            self._partial_end,
            subdivide_increment,
        )
        items.append(line)

        # Make the arrow head smaller if necessary, to ensure that (a) the two heads
        # don't collide, and (b) the arrow head doesn't extend past the end of the line.
        # This can be useful when animating an arrow growing from nothing.
        # These calculations assume a straight line, so (a) and (b) may not actually be
        # satisfied if the line has high curvature.
        available_length = line.total_length * (self._partial_end - self._partial_start)
        if arrow_head_start and arrow_head_end:
            available_length /= 2
        cos = np.cos(np.deg2rad(angle))
        if cos > 0:
            max_head_length = available_length / cos
            head_length = min(head_length, max_head_length)

        # Draw the arrow heads.
        head_start = line.points[0]
        head_end = line.points[-1]
        head_start_tangent = line.tangents[0]
        head_end_tangent = line.tangents[-1]

        if arrow_head_end:
            items.append(
                ArrowHead(
                    head_end,
                    head_end_tangent,
                    arrow_path_style,
                    angle,
                    head_length,
                    arrow_head_style,
                )
            )

        if arrow_head_start:
            # Negate the tangent to get the direction of the arrow head.
            x, y = head_start_tangent
            head_start_tangent = (-x, -y)

            items.append(
                ArrowHead(
                    head_start,
                    head_start_tangent,
                    arrow_path_style,
                    angle,
                    head_length,
                    arrow_head_style,
                )
            )

        super().__init__(items)

    @property
    def start(self) -> np.ndarray:
        """The start of the arrow."""
        return self._start

    @property
    def end(self) -> np.ndarray:
        """The end of the arrow."""
        return self._end

    @property
    def animatables(self) -> AnimatableSequence:
        return [
            self._arrow_path_style,
            self._angle,
            self._head_length,
            self._partial_start,
            self._partial_end,
        ]

    def copy_with_animatables(self, animatables: AnimatableSequence):
        (
            arrow_path_style,
            angle,
            head_length,
            partial_start,
            partial_end,
        ) = animatables

        return ArrowPath(
            self._path,
            self._arrow_head_start,
            self._arrow_head_end,
            arrow_path_style,
            angle,
            head_length,
            self._arrow_head_style,
            partial_start,
            partial_end,
            self._subdivide_increment,
        )
