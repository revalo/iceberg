from typing import Union, Tuple, Sequence

from abc import ABC, abstractmethod, abstractproperty
from iceberg.core import Bounds, Corner
from iceberg.utils import direction_equal
import numpy as np
import skia


class ChildNotFoundError(ValueError):
    pass


class Drawable(ABC):
    """Abstract base class for all drawable objects.

    Each drawable object must know its bounds, and be able to draw itself on a Skia canvas.
    It may also have children, which are also drawable objects.

    You almost always want to inherit from `iceberg.layout.Compose` instead of this class
    so that you can easily compose multiple drawables together without having to worry about
    the details of drawing them on a canvas with skia.
    """

    @abstractproperty
    def bounds(self) -> Bounds:
        """Return the bounds of the drawable."""
        pass

    @abstractmethod
    def draw(self, canvas: skia.Canvas):
        """Execute the Skia drawing commands on the canvas."""
        pass

    @property
    def children(self) -> Sequence["Drawable"]:
        """Return the children of the drawable."""
        return []

    def move(self, x: float, y: float):
        """Move the drawable by the specified amount."""
        from iceberg.primitives.layout import Transform

        return Transform(
            child=self,
            position=(x, y),
        )

    def scale(self, x: float, y: float = None):
        """Scale the drawable by the specified amount.

        Can be used as `drawable.scale(2)` or `drawable.scale(2, 3)`.

        Args:
            x: The amount to scale in the x direction.
            y: The amount to scale in the y direction. If not specified, this is the same as `x`.

        Returns:
            The new drawable that is scaled.
        """
        from iceberg.primitives.layout import Transform

        if y is None:
            y = x

        return Transform(
            child=self,
            scale=(x, y),
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

    def crop(self, bounds: Bounds):
        """Crop the drawable to the specified bounds."""
        from iceberg import Colors
        from iceberg.primitives.layout import Anchor, Blank

        blank = Blank(bounds, Colors.TRANSPARENT)

        return Anchor(
            [blank, self],
        )

    def next_to(
        self,
        other: "Drawable",
        direction: np.ndarray = np.zeros(2),
        no_gap: bool = False,
    ) -> "Drawable":
        """Place another drawable next to this one, and return the new drawable.

        The `direction` parameter specifies the direction to place the other drawable.

        Example:
            >>> from iceberg.primitives import Rectangle, Directions
            >>> rect1 = Rectangle(100, 100)
            >>> rect2 = Rectangle(100, 100)
            >>> rect1_and_rect2 = rect1.next_to(rect2, Directions.RIGHT * 10)

        Args:
            other: The other drawable to place next to this one.
            direction: The direction to place the other drawable. This is a 2D vector.
            no_gap: If True, the other drawable will be placed right next to this one, with no gap.
                The scale of `direction` is ignored in this case (`direction` is only used
                to determine which corners to align).

        Returns:
            The new drawable that contains both this drawable and the other drawable.
        """

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

        if no_gap:
            direction = Directions.ORIGIN

        return Align(self, other, anchor_corner, other_corner, direction)

    def add_centered(self, other: "Drawable") -> "Drawable":
        """Place another drawable in the center of this one, and return the new drawable.

        Args:
            other: The other drawable to place in the center of this one.

        Returns:
            The new drawable that contains both this drawable and the other drawable.
        """

        return self.next_to(other)

    def child_transform(self, search_child: "Drawable") -> np.ndarray:
        """Get the transformation matrix from this drawable to the specified child.

        Args:
            search_child: The child to search for.

        Returns:
            The transformation matrix from this drawable to the specified child.

        Raises:
            ChildNotFoundError: If the specified child is not a child of this drawable.
        """

        # TODO(revalo): Virtual DOM Tree with caching would significantly improve performance.

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
        """Get the bounds of the specified child relative to this drawable.

        Args:
            search_child: The child to search for.

        Returns:
            The bounds of the specified child relative to this drawable.

        Raises:
            ChildNotFoundError: If the specified child is not a child of this drawable.
        """

        transform = self.child_transform(search_child)
        return search_child.bounds.transform(transform)
