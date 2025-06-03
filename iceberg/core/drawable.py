from pathlib import Path
from typing import Any, Dict, Optional, Union, Tuple, Sequence, Callable
import typing
import typing_extensions as tpe
import types
import functools

from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass, MISSING
from iceberg.core import Bounds, Corner, Color, Colors
from iceberg.utils import direction_equal
import numpy as np
import skia
import dataclasses


def copy_func(f):
    """Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)"""

    g = types.FunctionType(
        f.__code__,
        f.__globals__,
        name=f.__name__,
        argdefs=f.__defaults__,
        closure=f.__closure__,
    )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


# Global variable to store the stack of scene contexts.
_scene_context_stack = []


class ChildNotFoundError(ValueError):
    """Raised when a child is not found in a drawable tree."""

    pass


def drawable_field(
    *,
    default=MISSING,
    default_factory=MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    kw_only=MISSING,
    dont_animate: bool = False,
    interpolator: Optional[Callable[[Any, Any, float], Any]] = None,
):
    """A field of a dataclass that is a drawable object.

    This is a special field that is used to transform a dataclass into a drawable object.
    """

    metadata = {}

    if dont_animate:
        metadata["iceberg_dont_animate"] = True

    if interpolator is not None:
        metadata["iceberg_interpolator"] = interpolator

    return dataclasses.field(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata=metadata,
        kw_only=kw_only,
    )


def dont_animate(
    *,
    default=MISSING,
    default_factory=MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    kw_only=MISSING,
):
    return drawable_field(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        kw_only=kw_only,
        dont_animate=True,
    )


def _drawable_field(*, kw_only: bool = False, default: Optional[Any] = ...) -> Any: ...


@tpe.dataclass_transform(field_specifiers=(_drawable_field,))  # type: ignore[literal-required]
class DrawableBase:
    if typing.TYPE_CHECKING:
        __dataclass_fields__: Dict[str, dataclasses.Field]


class Drawable(ABC, DrawableBase):
    """Abstract base class for all drawable objects.

    Each drawable object must know its bounds, and be able to draw itself on a Skia canvas.
    It may also have children, which are also drawable objects.

    You almost always want to inherit from `iceberg.layout.Compose` instead of this class
    so that you can easily compose multiple drawables together without having to worry about
    the details of drawing them on a canvas with skia.
    """

    def setup(self):
        """Setup the drawable.

        This method is called after the drawable is initialized.
        """

        pass

    def __post_init__(self) -> None:
        self._time = 0

        self.setup()

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Automatically initializes all subclasses as custom dataclasses."""
        super().__init_subclass__(**kwargs)

        init_already_defined = cls.__init__ is not cls.__mro__[1].__init__

        if init_already_defined:
            cls._original_init = cls.__init__
            del cls.__init__

        dataclass(
            cls,
            kw_only=True,
            **kwargs,
        )  # pytype: disable=wrong-keyword-args

        cls.init_from_fields = copy_func(cls.__init__)

        if init_already_defined:
            cls.__init__ = cls._original_init
            del cls._original_init

        @classmethod
        def from_fields(cls: "Drawable", **kwargs: Any):
            self = cls.__new__(cls)
            self.init_from_fields(**kwargs)
            return self

        cls.from_fields = from_fields

    @abstractproperty
    def bounds(self) -> Bounds:
        """Return the bounds of the drawable."""
        pass

    @abstractmethod
    def draw(self, canvas: skia.Canvas):
        """Execute the Skia drawing commands on the canvas.

        Args:
            canvas: The canvas to draw on.
        """
        pass

    @property
    def children(self) -> Sequence["Drawable"]:
        """Return the children of the drawable."""
        return []

    def set_time(self, t: float):
        """Recursively set the time of all drawables in the tree.

        Most drawables do not need to implement this method, but it is useful for animations.
        A drawable may choose to use `self._time` as the time for its animation to draw itself.
        """

        self._time = t

        for child in self.children:
            child.set_time(t)

    @property
    def relative_bounds(self) -> Bounds:
        """Get the bounds of the drawable relative to the current scene context.

        Example:
            >>> with some_drawable:
            >>>     print(child_drawable.relative_bounds)

        The above code will print the bounds of `child_drawable` relative to `some_drawable`.
        """

        # Go from innermost to outermost context and return the transformed bounds
        # if self is a child of that context.
        for scene in reversed(_scene_context_stack):
            try:
                return scene.child_bounds(self)
            except ChildNotFoundError:
                pass

        # Self is not a child of any context, so raise an error.
        return self.bounds

    def add(self, other: "Drawable") -> "Drawable":
        """Add another drawable to this one.

        Args:
            other: The other drawable to add.

        Returns:
            The new drawable that contains both this drawable and the other drawable.
        """

        from iceberg.primitives.layout import Compose

        return Compose([self, other])

    def __add__(self, other: "Drawable") -> "Drawable":
        return self.add(other)

    def background(self, background_color: Color) -> "Drawable":
        """Add a background to the drawable.

        Args:
            background_color: The color of the background.

        Returns:
            The new drawable with the background.
        """

        from iceberg.primitives.layout import Blank

        background = Blank(self.bounds, background_color=background_color)
        return background.add(self)

    def with_anchor(self, corner: int):
        """Anchor the drawable to the specified corner.

        Args:
            corner: The corner to anchor to.

        Returns:
            The new drawable that is anchored.
        """
        cx, cy = self.bounds.corners[corner]
        return self.move(-cx, -cy)

    def move(
        self,
        x: float,
        y: float,
        corner: Optional[Corner] = None,
        modify_bounds: bool = True,
    ):
        """Move the drawable by the specified amount.

        Args:
            x: The amount to move in the x direction.
            y: The amount to move in the y direction.
            corner: If specified, then the specified corner will be moved by the
                specified amount, relative to the current position of the *top-left*
                corner. In particular, if the top-left corner is currently at (0, 0),
                then the specified corner will be moved to (x, y).
            modify_bounds: If False, the bounds of the drawable will not be modified.
        """
        from iceberg.primitives.layout import Transform

        if corner is not None:
            cx, cy = self.bounds.corners[corner]
            x -= cx
            y -= cy

        return Transform(
            child=self,
            position=(x, y),
            modify_bounds=modify_bounds,
        )

    def move_to(self, x: float, y: float, corner: Optional[Corner] = Corner.TOP_LEFT):
        """Move the drawable to the specified absolute position.

        Unlike `move`, this method moves the drawable to the specified absolute position.

        Args:
            x: The x position to move to.
            y: The y position to move to.
            corner: If specified, then the specified corner will be moved to the
                specified position.
        """
        return self.with_anchor(corner).move(x, y)

    def relative_to(
        self,
        other: "Drawable",
        self_corner_or_direction: Union[Corner, np.ndarray] = Corner.TOP_LEFT,
        other_corner: Optional[Corner] = Corner.TOP_RIGHT,
        no_gap: bool = False,
    ):
        """Move the drawable to be relative to another drawable.

        Args:
            other: The other drawable to be relative to.
            self_corner: The corner of this drawable to be relative to.
            other_corner: The corner of the other drawable to be relative to.
        """

        if isinstance(self_corner_or_direction, np.ndarray):
            return other.next_to(
                self, self_corner_or_direction, no_gap=no_gap, include_anchor=False
            )

        ox, oy = other.relative_bounds.corners[other_corner]
        sx, sy = self.relative_bounds.corners[self_corner_or_direction]
        return self.move(ox - sx, oy - sy)

    def scale(
        self, x: float, y: float = None, corner: Optional[Corner] = Corner.CENTER
    ):
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

        lx, ly = self.bounds.corners[corner]
        child = self.move_to(0, 0, corner)
        child = Transform(
            child=child,
            scaling=(x, y),
        )
        return child.move_to(lx, ly, corner)

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

    def pad_left(self, padding: float):
        """Pad the drawable on the left by the specified amount."""
        return self.pad((padding, 0, 0, 0))

    def pad_top(self, padding: float):
        """Pad the drawable on the top by the specified amount."""
        return self.pad((0, padding, 0, 0))

    def pad_right(self, padding: float):
        """Pad the drawable on the right by the specified amount."""
        return self.pad((0, 0, padding, 0))

    def pad_bottom(self, padding: float):
        """Pad the drawable on the bottom by the specified amount."""
        return self.pad((0, 0, 0, padding))

    def crop(self, bounds: Bounds, clip: bool = False) -> "Drawable":
        """Crop the drawable to the specified bounds."""

        from iceberg import Colors
        from iceberg.primitives.layout import Anchor, Blank, ClipRect

        if clip:
            return ClipRect(self, bounds)
        else:
            blank = Blank(bounds, Colors.TRANSPARENT)
            return Anchor(
                [blank, self],
            )

    def opacity(self, opacity: float) -> "Drawable":
        """Set the opacity of the drawable.

        Args:
            opacity: The opacity to set.

        Returns:
            The new drawable with the opacity set.
        """

        from iceberg.primitives.filters import Opacity

        return Opacity(
            child=self,
            opacity=opacity,
        )

    def blur(self, sigma: float, sigma_y: float = None) -> "Drawable":
        """Blur the drawable by sigma.

        Args:
            sigma: The sigma of the blur.
            sigma_y: The sigma of the blur in the y direction. If None, sigma is used.

        Returns:
            The new drawable that is blurred.
        """

        from iceberg.primitives.filters import Blur

        return Blur(
            child=self,
            sigma=sigma,
            sigma_y=sigma_y,
        )

    def next_to(
        self,
        other: "Drawable",
        direction: np.ndarray = np.zeros(2),
        no_gap: bool = False,
        include_anchor: bool = True,
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
            include_anchor: If False, the final drawable will not include the anchor drawable.

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

        return Align(
            self, other, anchor_corner, other_corner, direction, include_anchor
        )

    def add_centered(self, other: "Drawable") -> "Drawable":
        """Place another drawable in the center of this one, and return the new drawable.

        Args:
            other: The other drawable to place in the center of this one.

        Returns:
            The new drawable that contains both this drawable and the other drawable.
        """

        return self.next_to(other)

    def debug_bounds(
        self, color: Color = Colors.RED, thickness: float = 1.0
    ) -> "Drawable":
        """Draw the bounds of the drawable on top of it for debugging purposes.

        Note that this does't change the bounds of the drawable, so it may be clipped,
        and more importantly, it may not be visible if you just render the drawable as is
        without any padding.

        Args:
            color: The color of the bounds.
            thickness: The width of the bounds.

        Returns:
            The new drawable with the bounds drawn on top of it.
        """

        from iceberg.primitives import Rectangle, Anchor

        bounds_rect = Rectangle(
            self.bounds, border_color=color, border_thickness=thickness
        )
        return Anchor([self, bounds_rect])

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

        if self is search_child:
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

    def child_transformed_point(
        self, search_child: "Drawable", point: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Get the point of the specified child relative to this drawable.

        Args:
            search_child: The child to search for.
            point: The point to transform.

        Returns:
            The point of the specified child relative to this drawable.

        Raises:
            ChildNotFoundError: If the specified child is not a child of this drawable.
        """

        from iceberg.geometry import apply_transform

        transform = self.child_transform(search_child)
        return apply_transform([point], transform)[0]

    def find_all(self, condition: Callable[["Drawable"], bool]) -> Sequence["Drawable"]:
        """Find all children that satisfy the specified condition recursively.

        Args:
            condition: The condition to satisfy.

        Returns:
            A list of all children that satisfy the specified condition.
        """

        children = []

        if condition(self):
            children.append(self)

        for child in self.children:
            children.extend(child.find_all(condition))

        return children

    def __enter__(self):
        _scene_context_stack.append(self)

    def __exit__(self, exc_type, exc_value, traceback):
        assert _scene_context_stack.pop() is self

    def render(
        self,
        filename: Union[str, Path] = None,
        background_color: Color = None,
        renderer=None,
    ) -> Optional[np.ndarray]:
        """Render the drawable to an image. If filename is specified, save the image to that file.
        Otherwise, return the image as a numpy array.

        Args:
            filename: The filename to save the image to. If None, the image is not saved, instead the image is returned.
            background_color: The background color to use. If None, the background will be transparent.
            renderer: The renderer to use. If None, a new renderer will be created.

        Returns:
            The rendered image as a numpy array if filename is None, otherwise None.
        """

        from iceberg import Renderer, render_svg

        if filename is not None and filename.endswith(".svg"):
            return render_svg(self, filename, background_color)

        if renderer is None:
            renderer = Renderer()

        renderer.render(self, background_color)

        if filename is None:
            return renderer.get_rendered_image()

        renderer.save_rendered_image(filename)

    def _repr_png_(self):
        """Render the drawable as a PNG image in a Jupyter notebook."""
        from PIL import Image
        import io

        b = io.BytesIO()
        rendered_pixels = self.render()
        pil_image = Image.fromarray(rendered_pixels)
        try:
            pil_image.save(b, "png")
        except Exception:
            return None

        return b.getvalue()


class DrawableWithChild(Drawable, ABC):
    def __post_init__(self) -> None:
        self._child = None
        return super().__post_init__()

    def set_child(self, scene: "Drawable"):
        self._child = scene

    @property
    def children(self) -> Sequence[Drawable]:
        return [self._child]

    @property
    def bounds(self) -> Bounds:
        return self._child.bounds

    def draw(self, canvas: skia.Canvas):
        self._child.draw(canvas)
