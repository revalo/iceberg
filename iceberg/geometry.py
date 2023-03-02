"""Utitlities for working with geometry.
"""

from typing import Tuple, Sequence

import numpy as np


def get_position_transform(
    position: Tuple[float, float] = (0, 0),
):
    """Returns a transform matrix that translates by the given position.

    Args:
        position: The position to translate by.

    Returns:
        A transform matrix that translates by the given position.
    """
    x, y = position

    return np.array(
        [
            [1, 0, x],
            [0, 1, y],
            [0, 0, 1],
        ]
    )


def get_rotation_transform(
    rotation: float = 0.0,
    in_degrees: bool = False,
):
    """Returns a transform matrix that rotates by the given rotation.

    Args:
        rotation: The rotation to rotate by.

    Returns:
        A transform matrix that rotates by the given rotation.
    """

    if in_degrees:
        rotation = np.radians(rotation)

    return np.array(
        [
            [np.cos(rotation), -np.sin(rotation), 0],
            [np.sin(rotation), np.cos(rotation), 0],
            [0, 0, 1],
        ]
    )


def get_scale_transform(
    scale: Tuple[float, float] = (1, 1),
):
    """Returns a transform matrix that scales by the given scale.

    Args:
        scale: The scale to scale by.

    Returns:
        A transform matrix that scales by the given scale.
    """
    x, y = scale

    return np.array(
        [
            [x, 0, 0],
            [0, y, 0],
            [0, 0, 1],
        ]
    )


def get_transform(
    scale: Tuple[float, float] = (1, 1),
    position: Tuple[float, float] = (0, 0),
    rotation: float = 0.0,
    anchor: Tuple[float, float] = (0, 0),
    in_degrees: bool = False,
):
    anchor_x, anchor_y = anchor
    neg_anchor = (-anchor_x, -anchor_y)
    anchor_matrix = get_position_transform(neg_anchor)
    reverse_anchor_matrix = get_position_transform(anchor)

    position_matrix = get_position_transform(position)
    rotation_matrix = get_rotation_transform(rotation, in_degrees)
    scale_matrix = get_scale_transform(scale)

    return (
        anchor_matrix
        @ rotation_matrix
        @ position_matrix
        @ scale_matrix
        @ reverse_anchor_matrix
    )


def apply_transform(
    points: Sequence[Tuple[float, float]],
    transform: np.ndarray,
):
    """Applies the given transform to the given points.

    Args:
        points: The points to transform.
        transform: The transform to apply.

    Returns:
        The transformed points.
    """
    return [
        tuple(
            np.matmul(
                transform,
                np.array([x, y, 1]),
            )[:2]
        )
        for x, y in points
    ]
