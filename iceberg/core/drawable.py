from typing import Union, Tuple, Sequence

from abc import ABC, abstractmethod, abstractproperty
from iceberg.core import Bounds, Corner
from iceberg.utils import direction_equal
import numpy as np


class ChildNotFoundError(ValueError):
    ...


class Drawable(ABC):
    @abstractproperty
    def bounds(self) -> Bounds:
        """Return the bounds of the drawable."""
        pass

    @abstractmethod
    def draw(self, canvas):
        """Execute the Skia drawing commands on the canvas."""
        pass

    @property
    def children(self) -> Sequence["Drawable"]:
        return []

    def move(self, x: float, y: float):
        """Move the drawable by the specified amount."""
        from iceberg.primitives.layout import Transform

        return Transform(
            child=self,
            position=(x, y),
        )

    def pad(
        self,
        padding: Union[Tuple[float, float, float, float], Tuple[float, float], float],
    ):
        """Pad the drawable by the specified amount."""
        from iceberg.primitives.layout import Padding

        return Padding(
            child=self,
            padding=padding,
        )

    def next_to(
        self, other: "Drawable", direction: np.ndarray = np.zeros(2)
    ) -> "Drawable":
        from iceberg.primitives.layout import Align, Directions

        sign = np.sign(direction)

        if np.sum(np.abs(sign)) > 1:
            raise ValueError("`next_to` can only move in cardinal directions.")

        anchor_corner = Corner.CENTER
        other_corner = Corner.CENTER

        if direction_equal(direction, Directions.RIGHT):
            anchor_corner = Corner.MIDDLE_RIGHT
            other_corner = Corner.MIDDLE_LEFT
        elif direction_equal(direction, Directions.DOWN):
            anchor_corner = Corner.BOTTOM_MIDDLE
            other_corner = Corner.TOP_MIDDLE
        elif direction_equal(direction, Directions.LEFT):
            anchor_corner = Corner.MIDDLE_LEFT
            other_corner = Corner.MIDDLE_RIGHT
        elif direction_equal(direction, Directions.UP):
            anchor_corner = Corner.TOP_MIDDLE
            other_corner = Corner.BOTTOM_MIDDLE

        return Align(self, other, anchor_corner, other_corner, direction)

    def center_to(self, other: "Drawable") -> "Drawable":
        return self.next_to(other)

    def child_transform(self, search_child: "Drawable") -> np.ndarray:
        from iceberg.primitives.layout import Transform

        if self == search_child:
            return np.eye(3)

        for child in self.children:
            try:
                transform = child.child_transform(search_child)

                if isinstance(child, Transform):
                    return child.transform @ transform

                return transform
            except ChildNotFoundError:
                pass

        raise ChildNotFoundError()

    def child_bounds(self, search_child: "Drawable") -> Bounds:
        transform = self.child_transform(search_child)
        return search_child.bounds.transform(transform)
