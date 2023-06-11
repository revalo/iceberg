# IceBerg

A diagramming eDSL in Python built on Skia.

## Quickstart

```python
canvas = Blank(Bounds(size=(1080, 720)))

rectangle = Rectangle(
    Bounds(size=(500, 100)),
    Colors.WHITE,
    border_thickness=3,
)

text = Text(
    text="Hello, World!",
    font_style=FontStyle(
        family="Arial",
        size=28,
        color=Colors.WHITE,
    ),
)

rectangle_and_text = rectangle.next_to(text, Directions.DOWN * 10)
scene = canvas.center_to(rectangle_and_text)

Renderer(scene).save("test.png")
```