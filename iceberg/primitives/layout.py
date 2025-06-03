from dataclasses import field
from enum import Enum
from typing import List, Sequence, Tuple, Union

import numpy as np
import skia

from iceberg import Bounds, Color, Colors, Drawable, DrawableWithChild, dont_animate
from iceberg.geometry import apply_transform, get_transform


class Directions:
    """Constants for the four cardinal directions.

    These can be multiplied by a scalar to get a vector in that direction
    (e.g. `Directions.UP * 5` is a vector pointing up with magnitude 5).
    """

    ORIGIN = np.array([0, 0])
    UP = np.array([0, -1])
    DOWN = np.array([0, 1])
    LEFT = np.array([-1, 0])
    RIGHT = np.array([1, 0])


class Blank(Drawable):
    rectangle: Bounds
    background_color: Color = Colors.BLACK

    def __init__(self, bounds: Bounds, background_color: Color = Colors.BLACK):
        """A drawable that is an expansive blank space.

        Args:
            bounds: The bounds of the blank space.
            background_color: The background color of the blank space.
        """

        self.init_from_fields(rectangle=bounds, background_color=background_color)

    def setup(self) -> None:
        self._paint = skia.Paint(
            Style=skia.Paint.kFill_Style,
            AntiAlias=True,
            Color4f=self.background_color.to_skia(),
        )

    @property
    def bounds(self) -> Bounds:
        return self.rectangle

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawRect(self.rectangle.to_skia(), self._paint)

    @classmethod
    def from_size(
        cls, width: float, height: float, background_color: Color = Colors.BLACK
    ):
        return cls(Bounds.from_size(width, height), background_color)


class Compose(Drawable):
    components: Tuple[Drawable, ...]

    def __init__(self, *children: Union[Drawable, Sequence[Drawable]]):
        """A drawable that composes its children.

        Args:
            children: The children to compose.
        """

        flattened_children = []

        for child in children:
            if isinstance(child, Drawable):
                flattened_children.append(child)
            else:
                flattened_children.extend(child)

        self.init_from_fields(components=tuple(flattened_children))

    def setup(self):
        self._composed_bounds = Bounds.empty()

        if len(self.components):
            # Compute the bounds of the composed children.
            left = min([child.bounds.left for child in self.children])
            top = min([child.bounds.top for child in self.children])
            right = max([child.bounds.right for child in self.children])
            bottom = max([child.bounds.bottom for child in self.children])

            self._composed_bounds = Bounds(
                left=left,
                top=top,
                right=right,
                bottom=bottom,
            )

    @property
    def children(self) -> Sequence[Drawable]:
        return self.components

    @property
    def bounds(self) -> Bounds:
        return self._composed_bounds

    def draw(self, canvas: skia.Canvas):
        for child in self.components:
            child.draw(canvas)


class Transform(Drawable):
    """A drawable that transforms its child.

    Args:
        child: The child drawable to transform.
        position: The position of the child drawable.
        scale: The scale of the child drawable.
        anchor: The anchor of the child drawable.
        rotation: The rotation of the child drawable.
        rotation_in_degrees: Whether the rotation is in degrees.
    """

    child: Drawable
    position: Tuple[float, float] = (0, 0)
    scaling: Tuple[float, float] = (1, 1)
    anchor: Tuple[float, float] = (0, 0)
    rotation: float = 0.0
    rotation_in_degrees: bool = True
    modify_bounds: bool = True

    def setup(self) -> None:
        self._child_bounds = self.child.bounds

        # Compute the bounds of the transformed child.
        left, top = self._child_bounds.left, self._child_bounds.top
        right, bottom = self._child_bounds.right, self._child_bounds.bottom

        self._transform = get_transform(
            position=self.position,
            scale=self.scaling,
            anchor=self.anchor,
            rotation=self.rotation,
            in_degrees=self.rotation_in_degrees,
        )
        self._skia_matrix = skia.Matrix(self._transform)

        # Transform the corners of the child's bounds.
        transformed_corners = apply_transform(
            points=[
                (left, top),
                (right, top),
                (right, bottom),
                (left, bottom),
            ],
            transform=self._transform,
        )

        # Compute the bounds of the transformed child.
        left = min([corner[0] for corner in transformed_corners])
        top = min([corner[1] for corner in transformed_corners])
        right = max([corner[0] for corner in transformed_corners])
        bottom = max([corner[1] for corner in transformed_corners])

        self._transformed_bounds = Bounds(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )

    @property
    def children(self) -> Sequence[Drawable]:
        """Return the children of the drawable."""

        return [self.child]

    @property
    def transform(self) -> np.ndarray:
        """The internal transform matrix."""

        return self._transform

    @property
    def bounds(self) -> Bounds:
        return self._transformed_bounds if self.modify_bounds else self._child_bounds

    def draw(self, canvas: skia.Canvas):
        canvas.save()
        canvas.concat(self._skia_matrix)
        self.child.draw(canvas)
        canvas.restore()


class Padding(DrawableWithChild):
    """A drawable that pads its child.

    Padding can be specified as:
    - A single float, which is applied to all sides.
    - A tuple of two floats, which are applied to the left/right and top/bottom.
    - A tuple of four floats, which are applied to the left, top, right, and bottom.

    Args:
        child: The child drawable to pad.
        padding: The padding to apply to the child drawable.
    """

    child: Drawable
    padding: Union[Tuple[float, float, float, float], Tuple[float, float], float]

    def setup(self):
        """Initialize a padding drawable."""
        padding = self.padding

        if isinstance(padding, tuple):
            if len(padding) == 2:
                padding = (padding[0], padding[1], padding[0], padding[1])
            elif len(padding) == 4:
                pass
        elif isinstance(padding, (int, float)):
            padding = (padding, padding, padding, padding)
        else:
            raise ValueError(
                "Invalid padding value. Padding must be a float or a tuple."
            )

        self._child_bounds = self.child.bounds

        pl, pt, pr, pb = padding

        self._pl = pl
        self._pt = pt
        self._pr = pr
        self._pb = pb

        self._padded_bounds = Bounds(
            left=self._child_bounds.left - pl,
            top=self._child_bounds.top - pt,
            right=self._child_bounds.right + pr,
            bottom=self._child_bounds.bottom + pb,
        )

        self.set_child(self.child)

    @property
    def bounds(self) -> Bounds:
        return self._padded_bounds


class Anchor(Compose):
    anchor_index: int = 0

    def __init__(
        self, *children: Union[Drawable, Sequence[Drawable]], anchor_index: int = 0
    ):
        """A drawable that composes it's children without expanding the
        borders.

        This drawable will compose its children without expanding the borders.

        Args:
            children: The children to compose.
            anchor_index: The index of the child to use as the anchor, which is
                the child that will be used to compute the bounds of the drawable.
        """

        flattened_children = []

        for child in children:
            if isinstance(child, Drawable):
                flattened_children.append(child)
            else:
                flattened_children.extend(child)

        self.init_from_fields(
            components=tuple(flattened_children),
            anchor_index=anchor_index,
        )

    @property
    def anchor(self) -> Drawable:
        return self.components[self.anchor_index]

    @property
    def bounds(self) -> Bounds:
        return self.anchor.bounds


class Align(DrawableWithChild):
    anchor: Drawable
    child: Drawable
    anchor_corner: int = dont_animate()
    child_corner: int = dont_animate()
    direction: np.ndarray = field(default_factory=lambda: Directions.ORIGIN)
    include_anchor: bool = True

    def __init__(
        self,
        anchor: Drawable,
        child: Drawable,
        anchor_corner: int,
        child_corner: int,
        direction: np.ndarray = Directions.ORIGIN,
        include_anchor: bool = True,
    ):
        """Initialize an align drawable.

        This drawable will align the child drawable to the anchor drawable. You can specify the
        two corners to align, and the direction to move the child drawable in.

        Example:
        ```python
        from iceberg.core import Corner
        Align(
            anchor=anchor,
            child=child,
            anchor_corner=Corner.TOP_LEFT,
            child_corner=Corner.TOP_RIGHT,
        )
        ```

        Args:
            anchor: The anchor drawable.
            child: The child drawable.
            anchor_corner: The corner of the anchor to align.
            child_corner: The corner of the child to align.
            direction: The direction to move the child drawable in.
        """

        self.init_from_fields(
            anchor=anchor,
            child=child,
            anchor_corner=anchor_corner,
            child_corner=child_corner,
            direction=direction,
            include_anchor=include_anchor,
        )

    def setup(self):
        anchor_corner = self.anchor.relative_bounds.corners[self.anchor_corner]
        child_corner = self.child.relative_bounds.corners[self.child_corner]

        dx = anchor_corner[0] - child_corner[0]
        dy = anchor_corner[1] - child_corner[1]

        dx += self.direction[0]
        dy += self.direction[1]

        child_transformed = Transform(
            child=self.child,
            position=(dx, dy),
        )

        if self.include_anchor:
            self.set_child(Compose(self.anchor, child_transformed))
        else:
            self.set_child(child_transformed)


class PointAlign(DrawableWithChild):
    anchor: Tuple[float, float]
    child: Drawable
    child_corner: int = dont_animate()
    direction: np.ndarray = field(default_factory=lambda: Directions.ORIGIN)

    def __init__(
        self,
        anchor: Tuple[float, float],
        child: Drawable,
        child_corner: int,
        direction: np.ndarray = Directions.ORIGIN,
    ):
        """Initialize a point align drawable.

        This drawable will align the child drawable to the anchor point. You can specify the
        corner to align, and the direction to move the child drawable in.

        Args:
            anchor: The anchor point.
            child: The child drawable.
            child_corner: The corner of the child to align.
            direction: The direction to move the child drawable in.
        """

        self.init_from_fields(
            anchor=anchor,
            child=child,
            child_corner=child_corner,
            direction=direction,
        )

    def setup(self):
        child_corner = self.child.bounds.corners[self.child_corner]

        dx = self.anchor[0] - child_corner[0]
        dy = self.anchor[1] - child_corner[1]

        dx += self.direction[0]
        dy += self.direction[1]

        child_transformed = Transform(
            child=self.child,
            position=(dx, dy),
        )

        self.set_child(child_transformed)


class Arrange(DrawableWithChild):
    class Direction(Enum):
        HORIZONTAL = 0
        VERTICAL = 1

    components: Sequence[Drawable]
    arrange_direction: Direction = Direction.HORIZONTAL
    gap: float = 1

    def __init__(
        self,
        *children: Union[Drawable, Sequence[Drawable]],
        arrange_direction: Direction = Direction.HORIZONTAL,
        gap: float = 1,
    ):
        """Initialize an arrange drawable.

        This drawable will arrange the children in a horizontal or vertical line.

        Args:
            children: The children to arrange.
            arrange_direction: The direction to arrange the children in.
            gap: The gap between the children.
        """

        flattened_children = []

        for child in children:
            if isinstance(child, Drawable):
                flattened_children.append(child)
            else:
                flattened_children.extend(child)

        self.init_from_fields(
            components=tuple(flattened_children),
            arrange_direction=arrange_direction,
            gap=gap,
        )

    def setup(self):
        next_to_direction = (
            Directions.RIGHT
            if self.arrange_direction == Arrange.Direction.HORIZONTAL
            else Directions.DOWN
        )
        arrangement = self.components[0]
        for next_child in self.components[1:]:
            if self.gap == 0:
                arrangement = arrangement.next_to(
                    next_child, next_to_direction, no_gap=True
                )
            else:
                arrangement = arrangement.next_to(
                    next_child, next_to_direction * self.gap
                )

        self.set_child(arrangement)


class Grid(DrawableWithChild):
    """A drawable that arranges its children in a grid.

    Args:
        children_matrix: The matrix of children to arrange.
        gap: The gap between the children.
    """

    children_matrix: List[List[Drawable]]
    gap: float = 0

    def setup(self):
        self._children_matrix = self.children_matrix
        self._nrows = len(self._children_matrix)
        self._ncols = len(self._children_matrix[0])
        self._gap_by_2 = self.gap / 2

        def _conditional_padding(x, y):
            pl = 0 if x == 0 else self._gap_by_2
            # pt = 0 if y == 0 else self._gap_by_2
            pt = 0
            pr = 0 if x == self._ncols - 1 else self._gap_by_2
            pb = 0 if y == self._nrows - 1 else self._gap_by_2
            return pl, pt, pr, pb

        self._padded_children = []

        current_x = 0
        current_y = 0

        for y, row in enumerate(self._children_matrix):
            for x, child in enumerate(row):
                child = child.pad(_conditional_padding(x, y)).move(current_x, current_y)
                self._padded_children.append(child)

                current_x += child.bounds.width

            current_y += child.bounds.height
            current_x = 0

        self.set_child(Compose(self._padded_children))


class ClipRect(Drawable):
    child: Drawable
    rect: Bounds

    def __init__(self, child: Drawable, rect: Bounds):
        self.init_from_fields(child=child, rect=rect)

    def setup(self):
        self._child = self.child
        self._rect = self.rect

    def draw(self, canvas: skia.Canvas):
        canvas.save()
        canvas.clipRect(self._rect.to_skia())
        self._child.draw(canvas)
        canvas.restore()

    @property
    def bounds(self) -> Bounds:
        return self._rect

    @property
    def children(self) -> Sequence[Drawable]:
        return [self._child]
