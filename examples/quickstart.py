from iceberg import Renderer, Bounds, Colors, FontStyle
from iceberg.primitives import Rectangle, Blank, SimpleText, Directions

if __name__ == "__main__":
    # What font?
    _FONT_FAMILY = "Arial"

    # Create a blank canvas.
    canvas = Blank(Bounds(size=(1080, 720)))

    # Create a rectangle.
    rectangle = Rectangle(
        Bounds(size=(500, 100)),
        Colors.WHITE,
        border_thickness=3,
    )

    # Create some text.
    text = SimpleText(
        text="Hello, World!",
        font_style=FontStyle(
            family=_FONT_FAMILY,
            size=28,
            color=Colors.WHITE,
        ),
    )

    # Combine the rectangle and text into a _new_ object that has
    # the text placed 10 pixels under the rectangle.
    rectangle_and_text = rectangle.next_to(text, Directions.DOWN * 10)

    # Place the rectangle and text in the center of the canvas.
    scene = canvas.add_centered(rectangle_and_text)

    # Render the scene into a file called `test.png`.
    renderer = Renderer()
    renderer.render(scene)
    renderer.save_rendered_image("test.png")
