import dataclasses
import typing
from typing import Sequence

import numpy as np

import iceberg as ice

from .ease import EaseType

_PRIMITIVE_INTERPOLATORS = {
    int: lambda a, b, t: float(a + (b - a) * t),
    float: lambda a, b, t: a + (b - a) * t,
    np.ndarray: lambda a, b, t: a + (b - a) * t,
    bool: lambda a, b, t: a if t < 0.5 else b,
}


def _field_names(fields):
    return set(field.name for field in fields)


def _should_not_animate(field):
    return field.metadata.get("iceberg_dont_animate", False)


def _interpolate(sceneA, sceneB, t, a_type=None, b_type=None):
    # Recursively walk through the scene graph and interpolate between the two scenes.
    # Use the fact that everything is a dataclass, so we can use dataclasses.asdict
    # to get a dictionary representation of the scene.

    if sceneA is None or sceneB is None:
        return sceneA if t < 0.5 else sceneB

    a_hint = a_type if a_type is not None else None

    a_type = type(sceneA) if a_type is None else a_type
    b_type = type(sceneB) if b_type is None else b_type

    a_origin = typing.get_origin(a_type)
    b_origin = typing.get_origin(b_type)

    a_type = a_origin if a_origin is not None else a_type
    b_type = b_origin if b_origin is not None else b_type

    if a_type != b_type:
        raise ValueError(
            f"Scene graphs don't have the same structure. Type of {sceneA} is {a_type}, but type of {sceneB} is {b_type}."
        )

    if a_type == typing.Union or a_type == typing.Optional or a_type == Ellipsis:
        a_type = type(sceneA)

    if issubclass(a_type, ice.Drawable):
        fieldsA = dataclasses.fields(sceneA)
        fieldsB = dataclasses.fields(sceneB)

        if _field_names(fieldsA) != _field_names(fieldsB):
            raise ValueError(
                f"Scene graphs don't have the same structure. {sceneA} has fields {fieldsA}, but {sceneB} has fields {fieldsB}."
            )

        new_scene_fields = {}

        for field, fieldB in zip(fieldsA, fieldsB):
            fieldA_value = getattr(sceneA, field.name)
            fieldB_value = getattr(sceneB, field.name)

            if _should_not_animate(field):
                assert _should_not_animate(fieldB)
                new_scene_fields[field.name] = fieldA_value if t < 0.5 else fieldB_value
                continue

            new_scene_fields[field.name] = _interpolate(
                fieldA_value,
                fieldB_value,
                t,
                a_type=field.type,
                b_type=fieldB.type,
            )

        return sceneA.__class__.from_fields(**new_scene_fields)
    # Sequence captures a lot, excluding str is a hack for now.
    elif issubclass(a_type, (list, tuple, Sequence)) and not issubclass(a_type, str):
        sub_type = [None] * len(sceneA)
        if a_hint:
            if len(a_hint.__args__) == len(sceneA):
                sub_type = a_hint.__args__
            elif len(a_hint.__args__) == 1:
                sub_type = [a_hint.__args__[0]] * len(sceneA)

        rv = [
            _interpolate(a, b, t, a_type=s, b_type=s)
            for a, b, s in zip(sceneA, sceneB, sub_type)
        ]
        if isinstance(sceneA, tuple):
            return tuple(rv)
        return rv
    elif issubclass(a_type, (int, float, np.ndarray)):
        for type_, func in _PRIMITIVE_INTERPOLATORS.items():
            if issubclass(a_type, type_):
                return func(sceneA, sceneB, t)
    elif issubclass(a_type, ice.AnimatableProperty):
        sceneA: ice.AnimatableProperty = sceneA
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
