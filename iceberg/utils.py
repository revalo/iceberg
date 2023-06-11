import numpy as np


def direction_equal(direction_a: np.ndarray, direction_b: np.ndarray):
    return np.all(np.sign(direction_a) == np.sign(direction_b))
