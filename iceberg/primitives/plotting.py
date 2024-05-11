import io

import numpy as np
from PIL import Image as PILImage

from iceberg import DrawableWithChild
from iceberg.primitives.image import Image
from iceberg.primitives.svg import SVG

_MATPLOTLIB_INSTALLED = False

# Check if matplotlib is installed.
try:
    import matplotlib

    _MATPLOTLIB_INSTALLED = True
except ImportError:
    pass


if _MATPLOTLIB_INSTALLED:
    import matplotlib.figure
    import matplotlib.axes

    class MatplotlibFigure(DrawableWithChild):
        """Import a matplotlib figure as a drawable for iceberg.

        Note, if not using SVG mode, control the dpi of the figure using the
        matplotlib figure's dpi property.

        Args:
            figure: The matplotlib figure to import.
            use_svg: Whether to use svg or png as the intermediate format.
            transparent: Whether to use a transparent background.
        """

        figure: matplotlib.figure.Figure
        use_svg: bool = True
        transparent: bool = False
        filter_quality: Image.ImageFilterQuality = Image.ImageFilterQuality.HIGH

        def setup(self) -> None:
            buffer = io.BytesIO()
            self.figure.savefig(
                buffer,
                format="svg" if self.use_svg else "png",
                transparent=self.transparent,
            )
            buffer.seek(0)

            if self.use_svg:
                child = SVG(raw_svg=buffer.getvalue().decode("utf-8"))
            else:
                pil_image = PILImage.open(buffer)
                child = Image(
                    image=np.array(pil_image.convert("RGBA")),
                    filter_quality=self.filter_quality,
                )

            self.set_child(child)

        def axes_coordinates(
            self, x: float, y: float, axes: matplotlib.axes.Axes = None
        ) -> tuple[float, float]:
            """Convert axes coordinates to figure coordinates.

            If called within a scene, will return the relative coordinates to the scene.

            Args:
                x: The x coordinate.
                y: The y coordinate.
                axes: The axes to use. If None, uses the first axes in the figure.

            Returns:
                The transformed coordinates.
            """
            if axes is None:
                assert len(self.figure.axes) > 0, "No axes in the figure."
                axes = self.figure.axes[0]

            transform = axes.transData + self.figure.transFigure.inverted()
            tx, ty = transform.transform([x, y])
            ty = 1 - ty
            tx *= self.relative_bounds.width
            ty *= self.relative_bounds.height

            tx += self.relative_bounds.left
            ty += self.relative_bounds.top

            return tx, ty
