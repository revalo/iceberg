import math
from abc import ABC
from enum import Enum
from typing import List, Sequence, Tuple, Union

import skia

from iceberg import (
    Bounds,
    Color,
    Colors,
    Corner,
    Drawable,
    DrawableWithChild,
    FontStyle,
)
from iceberg.core.properties import PathStyle

from .layout import Compose
from .text import SimpleText


class BorderPosition(Enum):
    CENTER = "center"
    INSIDE = "inside"
    OUTSIDE = "outside"


class Rectangle(Drawable):
    """A rectangle.

    Args:
        rectangle: The bounds of the rectangle.
        border_color: The color of the border.
        fill_color: The color of the fill.
        border_thickness: The thickness of the border.
        anti_alias: Whether to use anti-aliasing.
        border_position: The position of the border.
        border_radius: The radius of the border.
        dont_modify_bounds: Whether to modify the bounds of the rectangle to account for the border.
    """

    rectangle: Bounds
    border_color: Color = None
    fill_color: Color = None
    border_thickness: float = 1.0
    anti_alias: bool = True
    border_position: BorderPosition = BorderPosition.CENTER
    border_radius: Union[float, Tuple[float, float]] = 0.0
    dont_modify_bounds: bool = False

    def __init__(
        self,
        rectangle: Bounds,
        border_color: Color = None,
        fill_color: Color = None,
        border_thickness: float = 1.0,
        anti_alias: bool = True,
        border_position: BorderPosition = BorderPosition.CENTER,
        border_radius: Union[float, Tuple[float, float]] = 0.0,
        dont_modify_bounds: bool = False,
    ):
        self.init_from_fields(
            rectangle=rectangle,
            border_color=border_color,
            fill_color=fill_color,
            border_thickness=border_thickness,
            anti_alias=anti_alias,
            border_position=border_position,
            border_radius=border_radius,
            dont_modify_bounds=dont_modify_bounds,
        )

    def setup(
        self,
    ) -> None:
        self._border_paint = (
            skia.Paint(
                Style=skia.Paint.kStroke_Style,
                AntiAlias=self.anti_alias,
                StrokeWidth=self.border_thickness,
                Color4f=self.border_color.to_skia(),
            )
            if self.border_color
            else None
        )

        self._fill_paint = (
            skia.Paint(
                Style=skia.Paint.kFill_Style,
                AntiAlias=self.anti_alias,
                Color4f=self.fill_color.to_skia(),
            )
            if self.fill_color
            else None
        )

        self._passed_bounds = self.rectangle
        self._bounds = self.rectangle
        self._skia_rect = self.rectangle.to_skia()
        self._border_skia_rect = self.rectangle.inset(
            self.border_thickness / 2, self.border_thickness / 2
        ).to_skia()

        # Increase the bounds to account for the border.
        if self.border_position == BorderPosition.CENTER:
            self._bounds = self._bounds.inset(
                -self.border_thickness / 2, -self.border_thickness / 2
            )
            self._border_skia_rect = self.rectangle.to_skia()
        elif self.border_position == BorderPosition.OUTSIDE:
            self._bounds = self._bounds.inset(
                -self.border_thickness, -self.border_thickness
            )
            self._border_skia_rect = self.rectangle.inset(
                -self.border_thickness / 2, -self.border_thickness / 2
            ).to_skia()

    @property
    def bounds(self) -> Bounds:
        if self.dont_modify_bounds:
            return self._passed_bounds

        return self._bounds

    @property
    def border_radius_tuple(self) -> Tuple[float, float]:
        if isinstance(self.border_radius, tuple):
            rx, ry = self.border_radius
        else:
            rx = ry = self.border_radius

        return rx, ry

    def draw(self, canvas):
        rx, ry = self.border_radius_tuple

        if self._fill_paint:
            canvas.drawRoundRect(self._skia_rect, rx, ry, self._fill_paint)

        if self._border_paint:
            canvas.drawRoundRect(self._border_skia_rect, rx, ry, self._border_paint)


class Ellipse(Rectangle):
    """An ellipse. Has the same arguments as Rectangle, except renders an ellipse."""

    def draw(self, canvas):
        if self._fill_paint:
            canvas.drawOval(self._skia_rect, self._fill_paint)

        if self._border_paint:
            canvas.drawOval(self._border_skia_rect, self._border_paint)


class Path(Drawable, ABC):
    """Base class for paths."""

    def set_path(self, skia_path: skia.Path, path_style: PathStyle):
        """Set the path and path style from the setup of a derived class.

        Args:
            skia_path: The path to set.
            path_style: The path style to set.
        """

        self._skia_path = skia_path
        self._path_style = path_style

        self._fill_path = skia.Path()
        self._path_style.skia_paint.getFillPath(self._skia_path, self._fill_path)
        self._bounds = Bounds.from_skia(self._fill_path.computeTightBounds())

    @classmethod
    def from_skia(cls, skia_path: skia.Path, path_style: PathStyle):
        """Initialize a standalone path from a Skia path and path style.

        Args:
            skia_path: The Skia path.
            path_style: The path style.

        Returns:
            The path.
        """

        path = cls()
        path.set_path(skia_path, path_style)
        return path

    @property
    def skia_path(self) -> skia.Path:
        """The Skia path."""
        return self._skia_path

    @property
    def bounds(self) -> Bounds:
        return self._bounds

    def draw(self, canvas):
        canvas.drawPath(self._skia_path, self._path_style.skia_paint)


class PartialPath(Drawable):
    """Part of a path, from start to end.

    Args:
        child_path: The path to draw.
        start: The start of the partial path, between 0 and 1.
        end: The end of the partial path, between 0 and 1.
        subdivide_increment: The increment to use when subdividing the path.
        interpolation: The interpolation to use when drawing the path.

    Raises:
        AssertionError: If start or end are not between 0 and 1 or if start > end.
    """

    class Interpolation(Enum):
        LINEAR = 0
        CUBIC = 1

    child_path: Path
    start: float = 0
    end: float = 1
    subdivide_increment: float = 0.01
    interpolation: Interpolation = Interpolation.CUBIC

    def __init__(
        self,
        child_path: Path,
        start: float = 0,
        end: float = 1,
        subdivide_increment: float = 0.01,
        interpolation: Interpolation = Interpolation.CUBIC,
    ):
        self.init_from_fields(
            child_path=child_path,
            start=start,
            end=end,
            subdivide_increment=subdivide_increment,
            interpolation=interpolation,
        )

    def setup(self):
        assert (
            0 <= self.start <= self.end <= 1
        ), "Start and end must be between 0 and 1."

        self._child_path = self.child_path
        self._start = self.start
        self._end = self.end
        self._subdivide_increment = self.subdivide_increment
        self._interpolation = self.interpolation

        self._path_measure = skia.PathMeasure(self._child_path.skia_path, False)
        self._total_length = self._path_measure.getLength()

        self._points = []
        self._tangents = []

        # Subdivide the path and store the points and tangents.
        current_t = self.start

        while current_t < self.end:
            current_distance = self._total_length * current_t

            point, tangent = self._path_measure.getPosTan(current_distance)

            self._points.append(point)
            self._tangents.append(tangent)

            current_t += self.subdivide_increment

        # Add the end point.
        point, tangent = self._path_measure.getPosTan(self._total_length * self.end)

        self._points.append(point)
        self._tangents.append(tangent)

        self._partial_path = skia.Path()
        self._partial_path.moveTo(self._points[0])

        if self.interpolation == self.Interpolation.LINEAR:
            for point in self._points[1:]:
                self._partial_path.lineTo(point)
        elif self.interpolation == self.Interpolation.CUBIC:
            segment_length = self._total_length * self.subdivide_increment

            for point, tangent, next_point, next_tangent in zip(
                self._points[:-1],
                self._tangents[:-1],
                self._points[1:],
                self._tangents[1:],
            ):
                # The tangents are unit vectors, but we would like actual time
                # derivatives for the conversion below. That's an underspecified
                # problem (the original path may not even have a notion of time.
                # But by scaling with the segment length we at least get
                # a reasonable choice (in particular, this makes the shape of the
                # interpolation invariant to scaling the entire path).
                tangent = tangent * segment_length
                next_tangent = next_tangent * segment_length
                # Compute control points (i.e. convert from Hermite to Bezier curve):
                p1 = point + tangent * 0.333
                p2 = next_point - next_tangent * 0.333
                self._partial_path.cubicTo(p1, p2, next_point)
        else:
            raise ValueError(f"Unknown interpolation {self.interpolation}.")

    def draw(self, canvas: skia.Canvas):
        canvas.drawPath(self._partial_path, self._child_path._path_style.skia_paint)

    @property
    def tangents(self) -> Sequence[skia.Point]:
        return self._tangents

    @property
    def points(self) -> Sequence[skia.Point]:
        return self._points

    @property
    def children(self) -> Sequence[Drawable]:
        return [self._child_path]

    @property
    def bounds(self) -> Bounds:
        return self._child_path.bounds

    @property
    def total_length(self) -> float:
        return self._total_length


class Line(Path):
    """A line.

    Args:
        start: The start of the line.
        end: The end of the line.
        path_style: The path style.
    """

    start: Tuple[float, float]
    end: Tuple[float, float]
    path_style: PathStyle

    def __init__(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        path_style: PathStyle,
    ):
        self.init_from_fields(start=start, end=end, path_style=path_style)

    def setup(self):
        path = skia.Path()
        path.moveTo(*self.start)
        path.lineTo(*self.end)

        self.set_path(path, self.path_style)


class CurvedCubicLine(Path):
    """A cubic line with curved edges.

    Args:
        points: The points of the curve.
        path_style: The path style.

    Raises:
        AssertionError: If there are fewer than 3 points.
    """

    points: List[Tuple[float, float]]
    path_style: PathStyle

    def setup(self):
        assert len(self.points) >= 3, "A cubic line requires at least 3 points."

        path = skia.Path()
        path.moveTo(*self.points[0])

        # Take points in groups of 3 and draw a cubic line.
        for i in range(0, len(self.points) - 2, 2):
            path.cubicTo(*self.points[i], *self.points[i + 1], *self.points[i + 2])

        self.set_path(path, self.path_style)


class GridOverlay(DrawableWithChild):
    """Overlays a grid on top of a scene, for debugging and design.

    Args:
        scene: The scene to overlay the grid on.
        spacing: The spacing between grid lines.
        label_every: Label every nth grid line.
        color: The color of the grid.
    """

    scene: Drawable
    spacing: float = 20
    label_every: int = 5
    color: Color = Colors.BLACK

    def setup(self):
        x_lower, x_upper = self.scene.bounds.left, self.scene.bounds.right
        y_lower, y_upper = self.scene.bounds.top, self.scene.bounds.bottom

        # Round the lower bounds to the previous multiple of the spacing.
        x_lower = math.floor(x_lower / self.spacing) * self.spacing
        y_lower = math.floor(y_lower / self.spacing) * self.spacing

        # Number of horizontal and vertical lines
        num_verticals = math.floor((x_upper - x_lower) / self.spacing)
        num_horizontals = math.floor((y_upper - y_lower) / self.spacing)

        # Line positions
        xs = [x_lower + self.spacing * i for i in range(num_verticals + 1)]
        ys = [y_lower + self.spacing * i for i in range(num_horizontals + 1)]

        # Extend the lines a bit to make the grid look nicer
        x_lower -= self.spacing / 2
        y_lower -= self.spacing / 2
        x_upper = max(x_upper, xs[-1] + self.spacing / 2)
        y_upper = max(y_upper, ys[-1] + self.spacing / 2)

        style = PathStyle(Color(self.color.r, self.color.g, self.color.b, 0.3), 1)
        important_style = PathStyle(
            Color(self.color.r, self.color.g, self.color.b, 0.85), 1
        )

        # Index of the zero line, to figure out which lines to bold and label.
        x_offset_index = xs.index(0) % self.label_every
        y_offset_index = ys.index(0) % self.label_every

        vertical_lines = [
            Line(
                (x, y_lower),
                (x, y_upper),
                important_style if i % self.label_every == x_offset_index else style,
            )
            for i, x in enumerate(xs)
        ]
        horizontal_lines = [
            Line(
                (x_lower, y),
                (x_upper, y),
                important_style if i % self.label_every == y_offset_index else style,
            )
            for i, y in enumerate(ys)
        ]

        labels = []
        font_style = FontStyle(
            family="Arial",
            size=12,
            color=self.color,
        )

        for i, x in enumerate(xs):
            if i % self.label_every == x_offset_index:
                labels.append(
                    SimpleText(
                        text=str(round(x)),
                        font_style=font_style,
                    ).move(x, y_lower - 5, corner=Corner.BOTTOM_MIDDLE)
                )

        for i, y in enumerate(ys):
            if i % self.label_every == y_offset_index:
                labels.append(
                    SimpleText(
                        text=str(round(y)),
                        font_style=font_style,
                    ).move(x_lower - 5, y, corner=Corner.MIDDLE_RIGHT)
                )

        self.set_child(
            Compose([self.scene] + vertical_lines + horizontal_lines + labels)
        )


class Point(DrawableWithChild):
    """A utility class to draw a point at a given location."""

    point: Tuple[float, float] = (0, 0)
    color: Color = Colors.RED
    radius: float = 2

    def __init__(
        self, point: Tuple[float, float], color: Color = Colors.RED, radius: float = 2
    ):
        self.init_from_fields(point=point, color=color, radius=radius)

    def setup(self):
        self.set_child(
            Ellipse(
                rectangle=Bounds(
                    center=self.point,
                    size=(self.radius * 2, self.radius * 2),
                ),
                fill_color=self.color,
            )
        )
