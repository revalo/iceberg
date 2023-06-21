import numpy as np
import hashlib
import os


def direction_equal(direction_a: np.ndarray, direction_b: np.ndarray):
    return np.all(np.sign(direction_a) == np.sign(direction_b))


def temp_filename(**kwargs):
    # Sort the kwargs so that the filename is deterministic.
    kwargs = list(sorted(kwargs.items()))

    h = hashlib.sha1()
    for key, value in kwargs:
        h.update(f"{key}={value}".encode("utf-8"))

    return h.hexdigest()


def temp_directory():
    _DIR_NAME = ".iceberg"
    os.makedirs(_DIR_NAME, exist_ok=True)
    return _DIR_NAME
