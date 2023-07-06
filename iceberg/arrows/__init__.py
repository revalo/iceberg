"""Built-in library for arrows.
"""

from enum import Enum
from typing import Tuple

import numpy as np
import skia

from iceberg import PathStyle, Drawable
from iceberg.primitives import Compose, Line, Path, PartialPath, Transform


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


class Arrow(Compose):
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

        self._midpoint = (np.array(start) + np.array(end)) / 2
        self._start = np.array(start)
        self._end = np.array(end)

        items = []

        # Draw the line.
        line = PartialPath(
            Line(start, end, line_path_style),
            partial_start,
            partial_end,
            # We want to subdivide the line into 1 pixel increments
            # for performance reasons because we know that the line
            # is straight.
            subdivide_increment=1,
        )
        items.append(line)

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
                    line_path_style,
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
                    line_path_style,
                    angle,
                    head_length,
                    arrow_head_style,
                )
            )

        super().__init__(items)

    @property
    def midpoint(self) -> np.ndarray:
        """The midpoint of the arrow."""
        return self._midpoint

    @property
    def start(self) -> np.ndarray:
        """The start of the arrow."""
        return self._start

    @property
    def end(self) -> np.ndarray:
        """The end of the arrow."""
        return self._end


class ArrowAlignDirection(Enum):
    ABOVE = 0
    BELOW = 1


class LabelArrow(Compose):
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

        # Find normal vector.
        direction = (arrow.end - arrow.start).astype(np.float32)
        direction /= np.linalg.norm(direction)
        normal = np.array([-direction[1], direction[0]], dtype=np.float32)
        normal /= np.linalg.norm(normal)

        angle = np.arctan2(direction[1], direction[0]) if rotated else 0

        # Compute the displacement.
        displacement = distance * normal

        # Placement above or below.
        if placement == ArrowAlignDirection.ABOVE:
            displacement *= -1

        arrow_point = arrow.midpoint + displacement

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
