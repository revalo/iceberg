from typing import List, Sequence, Tuple, Union
import skia

from iceberg import Drawable, Bounds, Color, Colors
from iceberg.animation import Animatable
from iceberg.animation.animatable import AnimatableSequence
from iceberg.core.drawable import Drawable
from iceberg.geometry import get_transform, apply_transform
from dataclasses import dataclass
from abc import ABC, abstractmethod, abstractproperty
from enum import Enum
import numpy as np


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
    """A drawable that is an expansive blank space."""

    def __init__(self, bounds: Bounds, background: Color = Colors.BLACK) -> None:
        """Initialize a blank drawable.

        Args:
            bounds: The bounds of the drawable.
            background: The background color of the drawable.
        """

        super().__init__()

        self._bounds = bounds
        self._background = background

        self._paint = skia.Paint(
            Style=skia.Paint.kFill_Style,
            AntiAlias=True,
            Color4f=self._background.to_skia(),
        )

    @property
    def bounds(self) -> Bounds:
        return self._bounds

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawRect(self._bounds.to_skia(), self._paint)


class Transform(Drawable, Animatable):
    """A drawable that transforms its child."""

    def __init__(
        self,
        child: Drawable,
        position: Tuple[float, float] = (0, 0),
        scale: Tuple[float, float] = (1, 1),
        anchor: Tuple[float, float] = (0, 0),
        rotation: float = 0.0,
        rotation_in_degrees: bool = True,
    ):
        """Initialize a transform drawable.

        Args:
            child: The child drawable to transform.
            position: The position of the child drawable.
            scale: The scale of the child drawable.
            anchor: The anchor of the child drawable.
            rotation: The rotation of the child drawable.
            rotation_in_degrees: Whether the rotation is in degrees.
        """

        super().__init__()

        self._child = child
        self._position = position
        self._scale = scale
        self._anchor = anchor
        self._rotation = rotation
        self._rotation_in_degrees = rotation_in_degrees

        self._child_bounds = self._child.bounds

        # Compute the bounds of the transformed child.
        left, top = self._child_bounds.left, self._child_bounds.top
        right, bottom = self._child_bounds.right, self._child_bounds.bottom

        self._transform = get_transform(
            position=self._position,
            scale=self._scale,
            anchor=self._anchor,
            rotation=rotation,
            in_degrees=rotation_in_degrees,
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

        return [self._child]

    @property
    def transform(self) -> np.ndarray:
        """The internal transform matrix."""

        return self._transform

    @property
    def child(self) -> np.ndarray:
        return self._child

    @property
    def bounds(self) -> Bounds:
        return self._transformed_bounds

    def draw(self, canvas: skia.Canvas):
        canvas.save()
        canvas.concat(self._skia_matrix)
        self._child.draw(canvas)
        canvas.restore()

    @property
    def animatables(self) -> AnimatableSequence:
        position = np.array(self._position)
        scale = np.array(self._scale)
        anchor = np.array(self._anchor)

        rv = [
            position,
            scale,
            anchor,
            self._rotation,
        ]

        if isinstance(self._child, Animatable):
            rv.append(self._child)

        return rv

    def copy_with_animatables(self, animatables: AnimatableSequence):
        if len(animatables) == 4:
            position, scale, anchor, rotation = animatables
            child = self._child
        else:
            position, scale, anchor, rotation, child = animatables

        return Transform(
            child=child,
            position=tuple(position),
            scale=tuple(scale),
            anchor=tuple(anchor),
            rotation=rotation,
            rotation_in_degrees=self._rotation_in_degrees,
        )


class Padding(Transform):
    """A drawable that pads its child."""

    def __init__(
        self,
        child: Drawable,
        padding: Union[Tuple[float, float, float, float], Tuple[float, float], float],
    ):
        """Initialize a padding drawable.

        Padding can be specified as:
            - A single float, which is applied to all sides.
            - A tuple of two floats, which are applied to the left/right and top/bottom.
            - A tuple of four floats, which are applied to the left, top, right, and bottom.

        Args:
            child: The child drawable to pad.
            padding: The padding to apply to the child drawable.
        """

        self._child = child

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

        self._padding = padding
        self._child_bounds = self._child.bounds

        pl, pt, pr, pb = self._padding

        self._padded_bounds = Bounds(
            left=self._child_bounds.left - pl,
            top=self._child_bounds.top - pt,
            right=self._child_bounds.right + pr,
            bottom=self._child_bounds.bottom + pb,
        )

        super().__init__(
            child=child,
            position=(0, 0),
        )

    @property
    def bounds(self) -> Bounds:
        return self._padded_bounds


class Compose(Drawable, Animatable):
    """A drawable that composes its children."""

    def __init__(self, children: Tuple[Drawable, ...]):
        """Initialize a compose drawable.

        Args:
            children: The children to compose.
        """

        self._children = children
        self._composed_bounds = Bounds.empty()

        if len(self._children):
            # Compute the bounds of the composed children.
            left = min([child.bounds.left for child in self._children])
            top = min([child.bounds.top for child in self._children])
            right = max([child.bounds.right for child in self._children])
            bottom = max([child.bounds.bottom for child in self._children])

            self._composed_bounds = Bounds(
                left=left,
                top=top,
                right=right,
                bottom=bottom,
            )

        self._animatables = []
        self._animatables_indices = []

        for i, child in enumerate(self._children):
            if isinstance(child, Animatable):
                self._animatables.append(child)
                self._animatables_indices.append(i)

    @property
    def children(self) -> Sequence[Drawable]:
        return self._children

    @property
    def bounds(self) -> Bounds:
        return self._composed_bounds

    def draw(self, canvas: skia.Canvas):
        for child in self._children:
            child.draw(canvas)

    @property
    def animatables(self) -> AnimatableSequence:
        return self._animatables

    def copy_with_animatables(self, animatables: AnimatableSequence):
        children = list(self.children)
        for i, animatable in zip(self._animatables_indices, animatables):
            children[i] = animatable
        return Compose(tuple(children))


class Anchor(Compose):
    """A drawable that composes it's children without expanding the
    borders.
    """

    def __init__(self, children: Tuple[Drawable, ...], anchor_index: int = 0):
        """Initialize an anchor drawable.

        This drawable will compose its children without expanding the borders.

        Args:
            children: The children to compose.
            anchor_index: The index of the child to use as the anchor, which is
                the child that will be used to compute the bounds of the drawable.
        """

        self._anchor_index = anchor_index

        super().__init__(children)

    @property
    def anchor(self) -> Drawable:
        return self._children[self._anchor_index]

    @property
    def bounds(self) -> Bounds:
        return self.anchor.bounds


class Align(Compose):
    def __init__(
        self,
        anchor: Drawable,
        child: Drawable,
        anchor_corner: int,
        child_corner: int,
        direction: np.ndarray = Directions.ORIGIN,
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

        anchor_corner = anchor.bounds.corners[anchor_corner]
        child_corner = child.bounds.corners[child_corner]

        dx = anchor_corner[0] - child_corner[0]
        dy = anchor_corner[1] - child_corner[1]

        dx += direction[0]
        dy += direction[1]

        child_transformed = Transform(
            child=child,
            position=(dx, dy),
        )

        super().__init__(
            children=[
                anchor,
                child_transformed,
            ]
        )


class Arrange(Compose):
    class Direction(Enum):
        HORIZONTAL = 0
        VERTICAL = 1

    def __init__(
        self,
        children: List[Drawable],
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

        next_to_direction = (
            Directions.RIGHT
            if arrange_direction == Arrange.Direction.HORIZONTAL
            else Directions.DOWN
        )
        arrangement = children[0]
        for next_child in children[1:]:
            if gap == 0:
                arrangement = arrangement.next_to(
                    next_child, next_to_direction, no_gap=True
                )
            else:
                arrangement = arrangement.next_to(next_child, next_to_direction * gap)

        super().__init__([arrangement])


class Grid(Compose):
    def __init__(self, children_matrix: List[List[Drawable]], gap=0):
        """Initialize a grid drawable.

        This drawable will arrange the children in a grid.

        Args:
            children_matrix: The matrix of children to arrange.
            gap: The gap between the children.
        """

        self._children_matrix = children_matrix
        self._nrows = len(children_matrix)
        self._ncols = len(children_matrix[0])
        self._gap_by_2 = gap / 2

        def _conditional_padding(x, y):
            pl = 0 if x == 0 else self._gap_by_2
            pt = 0 if y == 0 else self._gap_by_2
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

        super().__init__(children=tuple(self._padded_children))
