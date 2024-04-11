__version__ = "0.1.2"

from iceberg.core import (
    Drawable,
    DrawableWithChild,
    Bounds,
    Color,
    Colors,
    Renderer,
    PathStyle,
    FontStyle,
    Corner,
    StrokeCap,
    render_svg,
    AnimatableProperty,
    drawable_field,
    dont_animate,
    SplineType,
)

from iceberg.primitives import (
    Rectangle,
    Ellipse,
    Line,
    BorderPosition,
    Path,
    CurvedCubicLine,
    PartialPath,
    Transform,
    Padding,
    Compose,
    Grid,
    Blank,
    Align,
    PointAlign,
    Arrange,
    Directions,
    Anchor,
    SimpleText,
    Text,
    SVG,
    Tex,
    MathTex,
    Typst,
    MathTypst,
    Blur,
    Opacity,
    Image,
    GeneralLine,
    AutoLine,
)


from iceberg.primitives.plotting import _MATPLOTLIB_INSTALLED

if _MATPLOTLIB_INSTALLED:
    from iceberg.primitives.plotting import MatplotlibFigure


from iceberg.arrows import (
    Arrow,
    ArrowHead,
    ArrowHeadStyle,
    ArrowAlignDirection,
    LabelArrow,
)

from iceberg.animation import tween, EaseType
from iceberg.animation.scene import Playbook, Animated, Scene, Frozen
