from typing import List, Tuple

import skia

from iceberg.core.properties import PathStyle
from iceberg.primitives.shapes import Path


class SmoothPath(Path):
    """A path that takes in a bunch of points and interpolates them.

    Internally uses Catmull-Rom splines to interpolate the points.

    Args:
        points: The points of the curve.
        path_style: The path style.
        tension: The tension of the curve.
    """

    points: List[Tuple[float, float]]
    path_style: PathStyle = PathStyle()
    tension: float = 1.0

    def __init__(
        self,
        points: List[Tuple[float, float]],
        path_style: PathStyle = PathStyle(),
        tension: float = 1.0,
    ):
        self.init_from_fields(
            points=points,
            path_style=path_style,
            tension=tension,
        )

    def setup(self):
        points = [x for p in self.points for x in p]
        size = len(points)
        last = size - 4
        path = skia.Path()
        path.moveTo(points[0], points[1])

        for i in range(0, size - 2, 2):
            x0 = points[i - 2] if i > 0 else points[0]
            y0 = points[i - 1] if i > 0 else points[1]

            x1 = points[i]
            y1 = points[i + 1]

            x2 = points[i + 2]
            y2 = points[i + 3]

            x3 = points[i + 4] if i != last else x2
            y3 = points[i + 5] if i != last else y2

            # Calculate control points with tension
            cp1x = x1 + (x2 - x0) / 6 * self.tension
            cp1y = y1 + (y2 - y0) / 6 * self.tension

            cp2x = x2 - (x3 - x1) / 6 * self.tension
            cp2y = y2 - (y3 - y1) / 6 * self.tension

            path.cubicTo(cp1x, cp1y, cp2x, cp2y, x2, y2)

        self.set_path(path, self.path_style)
