from typing import Union, Sequence

from enum import Enum
import numpy as np
import math

import iceberg as ice
import dataclasses

from .ease import EaseType

_PRIMITIVE_INTERPOLATORS = {
    int: lambda a, b, t: float(a + (b - a) * t),
    float: lambda a, b, t: a + (b - a) * t,
    np.ndarray: lambda a, b, t: a + (b - a) * t,
    bool: lambda a, b, t: a if t < 0.5 else b,
}


def _field_names(obj):
    return set([x.name for x in dataclasses.fields(obj)])


def _interpolate(sceneA, sceneB, t):
    # Recursively walk through the scene graph and interpolate between the two scenes.
    # Use the fact that everything is a dataclass, so we can use dataclasses.asdict
    # to get a dictionary representation of the scene.

    if type(sceneA) != type(sceneB):
        raise ValueError(
            f"Scene graphs don't have the same structure. Type of {sceneA} is {type(sceneA)}, but type of {sceneB} is {type(sceneB)}."
        )

    if isinstance(sceneA, ice.Drawable):
        fieldsA = _field_names(sceneA)
        fieldsB = _field_names(sceneB)

        if fieldsA != fieldsB:
            raise ValueError(
                f"Scene graphs don't have the same structure. {sceneA} has fields {fieldsA}, but {sceneB} has fields {fieldsB}."
            )

        new_scene_fields = {}

        for field_name in fieldsA:
            fieldA_value = getattr(sceneA, field_name)
            fieldB_value = getattr(sceneB, field_name)

            new_scene_fields[field_name] = _interpolate(fieldA_value, fieldB_value, t)

        return sceneA.__class__.from_fields(**new_scene_fields)
    elif isinstance(sceneA, (list, tuple)):
        rv = [_interpolate(a, b, t) for a, b in zip(sceneA, sceneB)]
        if isinstance(sceneA, tuple):
            return tuple(rv)
        return rv
    elif isinstance(sceneA, (int, float, np.ndarray)):
        for type_, func in _PRIMITIVE_INTERPOLATORS.items():
            if isinstance(sceneA, type_):
                return func(sceneA, sceneB, t)
    elif isinstance(sceneA, ice.AnimatableProperty):
        return sceneA.__class__.interpolate(sceneA, sceneB, t)

    return sceneA if t < 0.5 else sceneB


def tween(
    start,
    end,
    progress: float,
    ease_type: EaseType = EaseType.EASE_IN_OUT_QUAD,
    ease_fn=None,
    ping_pong: bool = False,
):
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

    return _interpolate(start, end, ease_fn(progress))
