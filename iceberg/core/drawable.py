from typing import Union, Tuple

from abc import ABC, abstractmethod, abstractproperty
from iceberg.core import Bounds


class Drawable(ABC):
    @abstractproperty
    def bounds(self) -> Bounds:
        """Return the bounds of the drawable."""
        pass

    @abstractmethod
    def draw(self, canvas):
        """Execute the Skia drawing commands on the canvas."""
        pass

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
