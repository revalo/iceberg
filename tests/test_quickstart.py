import iceberg as ice

from .scene_tester import check_render


def test_quickstart():
    # What font?
    _FONT_FAMILY = "Arial"

    # Create a blank canvas.
    canvas = ice.Blank(ice.Bounds(size=(1080, 720)))

    # Create a rectangle.
    rectangle = ice.Rectangle(
        ice.Bounds(size=(500, 100)),
        ice.Colors.WHITE,
        border_thickness=3,
    )

    # Create some text.
    text = ice.SimpleText(
        text="Hello, World!",
        font_style=ice.FontStyle(
            family=_FONT_FAMILY,
            size=28,
            color=ice.Colors.WHITE,
        ),
    )

    # Combine the rectangle and text into a _new_ object that has
    # the text placed 10 pixels under the rectangle.
    rectangle_and_text = rectangle.next_to(text, ice.Directions.DOWN * 10)

    # Place the rectangle and text in the center of the canvas.
    scene = canvas.add_centered(rectangle_and_text)

    check_render(scene, "quickstart.png")
