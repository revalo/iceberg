import skia

from iceberg import Drawable, Bounds, Color
from iceberg.core import Bounds

import numpy as np


class Image(Drawable):
    def __init__(self, filename: str = None, image: np.ndarray = None) -> None:
        """Initialize the Image drawable.

        Can either load an image from a file or use a pre-loaded image.

        Args:
            filename: The filename of the image file to load.
            image: The image to use. If not specified, the image will be loaded from the filename.

        Raises:
            ValueError: If neither filename nor image is specified.
            FileNotFoundError: If the filename does not exist.
        """

        if filename is None and image is None:
            raise ValueError("Must specify either filename or image.")

        if filename is not None:
            self._skia_image = skia.Image.open(filename)
        else:
            self._skia_image = skia.Image.fromarray(image)

        self._bounds = Bounds(
            left=0,
            top=0,
            right=self._skia_image.width(),
            bottom=self._skia_image.height(),
        )

    @property
    def bounds(self) -> Bounds:
        return self._bounds

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawImage(self._skia_image, 0, 0)
