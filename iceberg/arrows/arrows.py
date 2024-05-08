from enum import Enum
from typing import Tuple

import numpy as np

from iceberg import Drawable, DrawableWithChild, PathStyle
from iceberg.primitives import Compose, Line, PartialPath, Transform

from .helpers import ArrowHead, ArrowHeadStyle


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


class Arrow(DrawableWithChild):
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

    start: Tuple[float, float]
    end: Tuple[float, float]
    line_path_style: PathStyle
    head_length: float = 20
    angle: float = 30
    arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE
    arrow_head_start: bool = False
    arrow_head_end: bool = True
    partial_start: float = 0
    partial_end: float = 1

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
        self.init_from_fields(
            start=start,
            end=end,
            line_path_style=line_path_style,
            head_length=head_length,
            angle=angle,
            arrow_head_style=arrow_head_style,
            arrow_head_start=arrow_head_start,
            arrow_head_end=arrow_head_end,
            partial_start=partial_start,
            partial_end=partial_end,
        )

    def setup(self):
        self._midpoint = (np.array(self.start) + np.array(self.end)) / 2
        self._start = np.array(self.start)
        self._end = np.array(self.end)
        self._path_style = self.line_path_style
        self._head_length = self.head_length
        self._angle = self.angle
        self._arrow_head_style = self.arrow_head_style
        self._arrow_head_start = self.arrow_head_start
        self._arrow_head_end = self.arrow_head_end
        self._partial_start = self.partial_start
        self._partial_end = self.partial_end

        # Compute the direction of the arrow.
        direction = self._end - self._start
        direction /= np.linalg.norm(direction)

        # We put in a lot of effort to make sure that the arrow head actually =
        # ends at the end of the line. If the arrow head has thickness, then
        # it extends past the end of the line. We compute the length of the
        # arrow head, and then shorten the line by that amount.

        backup_length = 0

        if self._arrow_head_end or self._arrow_head_start:
            # Create a fake arrow head to measure its length.
            fake_head = ArrowHead(
                (0, 0),
                (1, 0),
                self._path_style,
                self._angle,
                self._head_length,
                self._arrow_head_style,
            )
            backup_length = fake_head.bounds.right

        # Modified start and end points.
        # By default there is no modification.
        self._line_start = self._start
        self._line_end = self._end

        # Back-up or advance the start and end points.
        if self._arrow_head_end:
            self._line_end -= direction * backup_length

        if self._arrow_head_start:
            self._line_start += direction * backup_length

        items = []

        # Draw the line.
        line = PartialPath(
            Line(self._line_start, self._line_end, self._path_style),
            self._partial_start,
            self._partial_end,
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

        head_start = tuple(head_start)
        head_end = tuple(head_end)
        head_start_tangent = tuple(head_start_tangent)
        head_end_tangent = tuple(head_end_tangent)

        if self._arrow_head_end:
            items.append(
                ArrowHead(
                    head_end,
                    head_end_tangent,
                    self._path_style,
                    self._angle,
                    self._head_length,
                    self._arrow_head_style,
                )
            )

        if self._arrow_head_start:
            # Negate the tangent to get the direction of the arrow head.
            x, y = head_start_tangent
            head_start_tangent = (-x, -y)

            items.append(
                ArrowHead(
                    head_start,
                    head_start_tangent,
                    self._path_style,
                    self._angle,
                    self._head_length,
                    self._arrow_head_style,
                )
            )

        self.set_child(Compose(items))

    @property
    def midpoint(self) -> np.ndarray:
        """The midpoint of the arrow."""
        return self._midpoint


class ArrowAlignDirection(Enum):
    ABOVE = 0
    BELOW = 1


class LabelArrow(DrawableWithChild):
    """Combine an arrow alongside another drawable in a way that labels the arrow.

    Args:
        arrow: The arrow to be labeled.
        child: The label to be placed alongside the arrow.
        child_corner: The corner of the child to align with. See `Corner` for details.
        placement: Whether to place the specified corner of the child above or below the arrow.
        distance: The distance between the arrow and the child's specified corner.
        rotated: Whether to rotate the child to match the arrow.
    """

    arrow: Arrow
    child: Drawable
    child_corner: int
    placement: ArrowAlignDirection = ArrowAlignDirection.ABOVE
    distance: float = 0
    rotated: bool = False

    def setup(self):
        # Find normal vector.
        direction = (np.array(self.arrow.end) - np.array(self.arrow.start)).astype(
            np.float32
        )
        direction /= np.linalg.norm(direction)
        normal = np.array([-direction[1], direction[0]], dtype=np.float32)
        normal /= np.linalg.norm(normal)

        angle = np.arctan2(direction[1], direction[0]) if self.rotated else 0

        # Compute the displacement.
        displacement = self.distance * normal

        # Placement above or below.
        if self.placement == ArrowAlignDirection.ABOVE:
            displacement *= -1

        arrow_point = self.arrow.midpoint + displacement

        delta = arrow_point - self.child.bounds.corners[self.child_corner]
        dx, dy = delta

        if self.rotated:
            cx, cy = self.child.bounds.center
            self.child = Transform(
                self.child,
                rotation=angle,
                rotation_in_degrees=False,
                anchor=(-cx, -cy),
            )

        child_transformed = self.child.move(dx, dy)

        self.set_child(Compose([self.arrow, child_transformed]))
