import numpy as np
import hashlib
import os


def direction_equal(direction_a: np.ndarray, direction_b: np.ndarray) -> bool:
    """Check if two directions are equal (i.e. they point in the same direction).

    Args:
        direction_a: The first direction.
        direction_b: The second direction.

    Returns:
        True if the directions are equal, False otherwise.
    """

    return np.all(np.sign(direction_a) == np.sign(direction_b))


def temp_filename(**kwargs):
    """Generate a temporary filename that is deterministic based on the kwargs.

    Args:
        kwargs: The kwargs to use to generate the filename.

    Returns:
        The temporary filename without the extension.
    """

    # Sort the kwargs so that the filename is deterministic.
    kwargs = list(sorted(kwargs.items()))

    h = hashlib.sha1()
    for key, value in kwargs:
        h.update(f"{key}={value}".encode("utf-8"))

    return h.hexdigest()


def temp_directory():
    """Get the temporary directory for iceberg.

    This will create the directory if it does not exist.

    Returns:
        The temporary directory for iceberg.
    """

    _DIR_NAME = ".iceberg"
    os.makedirs(_DIR_NAME, exist_ok=True)
    return _DIR_NAME
