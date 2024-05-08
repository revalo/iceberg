import iceberg as ice
from .scene_tester import check_render


def test_arrow_path():
    s = 256
    d = 10

    blank = ice.Blank(ice.Bounds.from_size(s, s), background_color=ice.Colors.WHITE)
    pts = ((d, s // 2), (s // 2, s // 2 + 50), (s - d, s // 2))
    line = ice.SmoothPath(pts, ice.PathStyle(thickness=2), tension=1)
    arrow_path = ice.ArrowPath(line, partial_end=0.7)
    scene = blank.add(arrow_path)

    check_render(scene, "smooth_arrow_path.png")
