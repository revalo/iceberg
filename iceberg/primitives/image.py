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
                The image must be a numpy array with shape one of
                  - (height, width) or (height, width, 1) for grayscale
                  - (height, width, 3) for RGB
                  - (height, width, 4) for RGBA
                Values can be either integers from 0 to 255 or floats between 0 and 1.

        Raises:
            ValueError: If neither filename nor image is specified.
            FileNotFoundError: If the filename does not exist.
        """

        if filename is None and image is None:
            raise ValueError("Must specify either filename or image.")

        if filename is not None:
            self._skia_image = skia.Image.open(filename)
        else:
            assert image.ndim in {
                2,
                3,
            }, f"Invalid image shape: {image.shape}, must be 2- or 3-dimensional."

            if image.ndim == 2:
                # grayscale image, add channel
                image = image[..., np.newaxis]

            if image.shape[-1] == 1:
                # grayscale image, copy channels
                image = np.repeat(image, 3, axis=-1)

            if image.shape[-1] == 3:
                # Add alpha channel
                image = np.concatenate([image, np.ones_like(image[..., :1])], axis=-1)

            if not np.issubdtype(image.dtype, np.integer):
                assert np.all(image >= 0) and np.all(image <= 1)
                image = image * 255
            image = image.astype(np.uint8)

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
