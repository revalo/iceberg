from enum import Enum
import skia

from iceberg import Drawable, Bounds, Color
from iceberg.core import Bounds

import numpy as np


class Image(Drawable):
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

    class ImageFilterQuality(Enum):
        NEAREST_NEIGHBOR = skia.kNone_FilterQuality
        LOW = skia.kLow_FilterQuality
        MEDIUM = skia.kMedium_FilterQuality
        HIGH = skia.kHigh_FilterQuality

    filename: str = None
    image: np.ndarray = None
    filter_quality: ImageFilterQuality = ImageFilterQuality.HIGH

    def __init__(
        self,
        filename: str = None,
        image: np.ndarray = None,
        filter_quality: ImageFilterQuality = ImageFilterQuality.HIGH,
    ):
        self.init_from_fields(
            filename=filename, image=image, filter_quality=filter_quality
        )

    def setup(self) -> None:
        if self.filename is None and self.image is None:
            raise ValueError("Must specify either filename or image.")

        image = self.image

        if self.filename is not None:
            self._skia_image = skia.Image.open(self.filename)
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

            self._skia_image = skia.Image.fromarray(
                image, colorType=skia.ColorType.kRGBA_8888_ColorType
            )

        self._paint = skia.Paint(
            AntiAlias=True,
            FilterQuality=self.filter_quality.value,
        )

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
        canvas.drawImage(self._skia_image, 0, 0, paint=self._paint)
