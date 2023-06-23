"""Built-in library for arrows.
"""

from enum import Enum
from typing import Tuple

import numpy as np
import skia

from iceberg import PathStyle
from iceberg.primitives import Compose, Line, Path


def arrow_corners(
    start: Tuple[float, float],
    end: Tuple[float, float],
    angle_degrees: float,
    distance: float,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Given a start and end coordinate, and an angle, compute where the two corners of the arrow are.

    Args:
        start: The start coordinate.
        end: The end coordinate.
        angle_degrees: The angle of the arrow.
        distance: The distance from the end coordinate to the arrow tip.

    Returns:
        The two corners of the arrow.
    """

    # Compute the direction of the arrow.
    direction = np.array(end, dtype=np.float32) - np.array(start)
    direction *= -1
    direction /= np.linalg.norm(direction)

    # Compute the angle of the arrow.
    angle = np.deg2rad(angle_degrees)

    # Compute the two corners of the arrow.
    corner1 = end + distance * (
        direction * np.cos(angle)
        + np.array([-direction[1], direction[0]]) * np.sin(angle)
    )
    corner2 = end + distance * (
        direction * np.cos(angle)
        + np.array([direction[1], -direction[0]]) * np.sin(angle)
    )

    return corner1, corner2


class ArrowHeadStyle(Enum):
    TRIANGLE = 0
    FILLED_TRIANGLE = 1


class Arrow(Compose):
    def __init__(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        line_path_style: PathStyle,
        head_length: float = 20,
        angle: float = 30,
        arrow_head_style: ArrowHeadStyle = ArrowHeadStyle.TRIANGLE,
        arrow_head_start: bool = False,
        arrow_head_end: bool = True,
    ):
        start_corners = arrow_corners(end, start, angle, head_length)
        end_corners = arrow_corners(start, end, angle, head_length)

        if arrow_head_style == ArrowHeadStyle.FILLED_TRIANGLE:
            items = [Line(start, end, line_path_style)]

            head_path_style = PathStyle(
                color=line_path_style.color,
                stroke=False,
                anti_alias=line_path_style.anti_alias,
            )

            if arrow_head_end:
                path = skia.Path()
                path.moveTo(*end_corners[0])
                path.lineTo(*end)
                path.lineTo(*end_corners[1])
                path.close()
                arrow_head = Path(path, head_path_style)
                arrow_head_2 = Path(path, line_path_style)
                items.append(arrow_head)
                items.append(arrow_head_2)

            if arrow_head_start:
                path = skia.Path()
                path.moveTo(*start_corners[0])
                path.lineTo(*start)
                path.lineTo(*start_corners[1])
                path.close()
                arrow_head = Path(path, head_path_style)
                arrow_head_2 = Path(path, line_path_style)
                items.append(arrow_head)
                items.append(arrow_head_2)

            super().__init__(items)
        elif arrow_head_style == ArrowHeadStyle.TRIANGLE:
            items = []
            if arrow_head_end:
                path = skia.Path()
                path.moveTo(*end_corners[0])
                path.lineTo(*end)
                path.lineTo(*end_corners[1])
                path.moveTo(*end)
                path.lineTo(*start)
                items.append(Path(path, line_path_style))

            if arrow_head_start:
                path = skia.Path()
                path.moveTo(*start_corners[0])
                path.lineTo(*start)
                path.lineTo(*start_corners[1])
                path.moveTo(*start)
                path.lineTo(*end)
                items.append(Path(path, line_path_style))

            super().__init__(items)
        else:
            raise ValueError(f"Unknown arrow head style: {arrow_head_style}")
