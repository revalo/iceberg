import math
from enum import Enum


def linear(x):
    return x


def ease_in_sine(x):
    return -math.cos(x * math.pi / 2) + 1


def ease_out_sine(x):
    return math.sin(x * math.pi / 2)


def ease_in_out_sine(x):
    return -(math.cos(math.pi * x) - 1) / 2


def ease_in_quad(x):
    return x * x


def ease_out_quad(x):
    return -x * (x - 2)


def ease_in_out_quad(x):
    x *= 2
    if x < 1:
        return x * x / 2
    else:
        x -= 1
        return -(x * (x - 2) - 1) / 2


def ease_in_cubic(x):
    return x * x * x


def ease_out_cubic(x):
    x -= 1
    return x * x * x + 1


def ease_in_out_cubic(x):
    x *= 2
    if x < 1:
        return x * x * x / 2
    else:
        x -= 2
        return (x * x * x + 2) / 2


def ease_in_quart(x):
    return x * x * x * x


def ease_out_quart(x):
    x -= 1
    return -(x * x * x * x - 1)


def ease_in_out_quart(x):
    x *= 2
    if x < 1:
        return x * x * x * x / 2
    else:
        x -= 2
        return -(x * x * x * x - 2) / 2


def ease_in_quint(x):
    return x * x * x * x * x


def ease_out_quint(x):
    x -= 1
    return x * x * x * x * x + 1


def ease_in_out_quint(x):
    x *= 2
    if x < 1:
        return x * x * x * x * x / 2
    else:
        x -= 2
        return (x * x * x * x * x + 2) / 2


def ease_in_expo(x):
    return math.pow(2, 10 * (x - 1))


def ease_out_expo(x):
    return -math.pow(2, -10 * x) + 1


def ease_in_out_expo(x):
    x *= 2
    if x < 1:
        return math.pow(2, 10 * (x - 1)) / 2
    else:
        x -= 1
        return -math.pow(2, -10 * x) - 1


def ease_in_circ(x):
    return 1 - math.sqrt(1 - x * x)


def ease_out_circ(x):
    x -= 1
    return math.sqrt(1 - x * x)


def ease_in_out_circ(x):
    x *= 2
    if x < 1:
        return -(math.sqrt(1 - x * x) - 1) / 2
    else:
        x -= 2
        return (math.sqrt(1 - x * x) + 1) / 2


class EaseType(Enum):
    LINEAR = linear
    EASE_IN_SINE = ease_in_sine
    EASE_OUT_SINE = ease_out_sine
    EASE_IN_OUT_SINE = ease_in_out_sine
    EASE_IN_QUAD = ease_in_quad
    EASE_OUT_QUAD = ease_out_quad
    EASE_IN_OUT_QUAD = ease_in_out_quad
    EASE_IN_CUBIC = ease_in_cubic
    EASE_OUT_CUBIC = ease_out_cubic
    EASE_IN_OUT_CUBIC = ease_in_out_cubic
    EASE_IN_QUART = ease_in_quart
    EASE_OUT_QUART = ease_out_quart
    EASE_IN_OUT_QUART = ease_in_out_quart
    EASE_IN_QUINT = ease_in_quint
    EASE_OUT_QUINT = ease_out_quint
    EASE_IN_OUT_QUINT = ease_in_out_quint
    EASE_IN_EXPO = ease_in_expo
    EASE_OUT_EXPO = ease_out_expo
    EASE_IN_OUT_EXPO = ease_in_out_expo
    EASE_IN_CIRC = ease_in_circ
    EASE_OUT_CIRC = ease_out_circ
    EASE_IN_OUT_CIRC = ease_in_out_circ
