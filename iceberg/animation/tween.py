from typing import Union

from enum import Enum
import numpy as np

from .animatable import Animatable


def linear(x):
    return x


def ease_in_out_quad(x):
    if x < 0.5:
        return 2 * x * x
    else:
        return 1 - (-2 * x + 2) ** 2 / 2


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    return x**3


class EaseType(Enum):
    LINEAR = linear
    EASE_IN_OUT_QUAD = ease_in_out_quad
    EASE_OUT_CUBIC = ease_out_cubic
    EASE_IN_CUBIC = ease_in_cubic


def tween(
    start: Union[Animatable, np.ndarray, float],
    end: Union[Animatable, np.ndarray, float],
    progress: float,
    ease_type: EaseType = EaseType.EASE_IN_OUT_QUAD,
    ease_fn=None,
    ping_pong: bool = False,
) -> Union[np.ndarray, float]:
    """Tween between two values.

    Args:
        start: The start value either as a scalar or a numpy array.
        end: The end value either as a scalar or a numpy array.
        progress: The progress between the start and end values between 0 and 1.
        ease_type: The type of easing to use.
        ease_fn: The easing function to use. If specified, this overrides the `ease_type`.
        ping_pong: Whether to ping pong the tween, i.e. tween back and forth between the
            start and end values.

    Returns:
        The tweened value.
    """

    if ease_fn is None:
        ease_fn = ease_type

    if ping_pong:
        if progress < 0.5:
            progress = progress * 2
        elif progress >= 0.5:
            progress = 1 - (progress - 0.5) * 2

    if isinstance(start, Animatable):
        start_scalars = start.animatables_to_vector()
        end_scalars = end.animatables_to_vector()

        tweened_scalars = tween(
            start_scalars,
            end_scalars,
            progress,
            ease_type=ease_type,
            ease_fn=ease_fn,
        )

        # if progress < 0.99:
        return start.copy_with_animatable_vector(tweened_scalars)

        # return end.copy_with_animatable_vector(tweened_scalars)

    return start + (end - start) * ease_fn(progress)


# Alias for tween.
animate = tween
