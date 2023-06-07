from typing import List, Tuple, Union
import skia

from iceberg import Drawable, Bounds, Color
from iceberg.geometry import get_transform, apply_transform
from dataclasses import dataclass
from enum import Enum


class Transform(Drawable):
    """A drawable that transforms its child."""

    def __init__(
        self,
        child: Drawable,
        position: Tuple[float, float] = (0, 0),
        scale: Tuple[float, float] = (1, 1),
        anchor: Tuple[float, float] = (0, 0),
    ):
        super().__init__()

        self._child = child
        self._position = position
        self._scale = scale
        self._anchor = anchor

        self._child_bounds = self._child.bounds

        # Compute the bounds of the transformed child.
        left, top = self._child_bounds.left, self._child_bounds.top
        right, bottom = self._child_bounds.right, self._child_bounds.bottom

        self._transform = get_transform(
            position=self._position,
            scale=self._scale,
            anchor=self._anchor,
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
    def bounds(self) -> Bounds:
        return self._transformed_bounds

    def draw(self, canvas: skia.Canvas):
        canvas.save()
        canvas.concat(self._skia_matrix)
        self._child.draw(canvas)
        canvas.restore()


class Padding(Transform):
    """A drawable that pads its child."""

    def __init__(
        self,
        child: Drawable,
        padding: Union[Tuple[float, float, float, float], Tuple[float, float], float],
    ):
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
            left=self._child_bounds.left,
            top=self._child_bounds.top,
            right=self._child_bounds.right + pl + pr,
            bottom=self._child_bounds.bottom + pt + pb,
        )

        super().__init__(
            child=child,
            position=(pl, pt),
            anchor=(0, 0),
        )

    @property
    def bounds(self) -> Bounds:
        return self._padded_bounds


class Compose(Drawable):
    """A drawable that composes its children."""

    def __init__(self, children: Tuple[Drawable, ...]):
        self._children = children

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

    @property
    def bounds(self) -> Bounds:
        return self._composed_bounds

    def draw(self, canvas: skia.Canvas):
        for child in self._children:
            child.draw(canvas)


class Grid(Compose):
    def __init__(self, children_matrix: List[List[Drawable]], gap=0):
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
