from enum import Enum
from typing import List, Optional, Sequence, Tuple, Union
import itertools

import numpy as np
import skia

from iceberg import PathStyle, Drawable, Bounds, Corner, SplineType, Interpolation
from iceberg.primitives import Compose, Line, GeneralLine, Transform, AutoLine
from iceberg.animation import Animatable
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
        arrow_path_style: Optional[PathStyle] = None,
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
        self._start = np.array(start)
        self._end = np.array(end)
        self._line_path_style = line_path_style

        path = Line(start, end, line_path_style)
        super().__init__(
            path=path,
            arrow_head_start=arrow_head_start,
            arrow_head_end=arrow_head_end,
            arrow_path_style=arrow_path_style,
            angle=angle,
            head_length=head_length,
            arrow_head_style=arrow_head_style,
            partial_start=partial_start,
            partial_end=partial_end,
            subdivide_increment=1,
            interpolation=Interpolation.LINEAR,
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
        spline: SplineType = SplineType.LINEAR,
        corner_radius: float = 0,
        arrow_path_style: Optional[PathStyle] = None,
        head_length: float = 20,
        angle: float = 30,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
        arrow_head_start: bool = False,
        arrow_head_end: bool = False,
        partial_start: float = 0,
        partial_end: float = 1,
        subdivide_increment: float = 0.01,
        interpolation: Interpolation = Interpolation.CUBIC,
    ):
        super().__init__(
            GeneralLine(points, line_path_style, spline, corner_radius),
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


class AutoArrow(ArrowPath):
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
        arrow_head_start: bool = False,
        arrow_head_end: bool = False,
        arrow_path_style: Optional[PathStyle] = None,
        angle: float = 30,
        head_length: float = 20,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
        partial_start: float = 0,
        partial_end: float = 1,
        subdivide_increment: float = 0.01,
        interpolation: Interpolation = Interpolation.CUBIC,
    ):
        super().__init__(
            AutoLine(
                start,
                end,
                directions,
                path_style,
                x_padding,
                y_padding,
                context,
                spline,
                corner_radius,
            ),
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
