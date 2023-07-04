# IceBerg

![PyPI](https://img.shields.io/pypi/v/iceberg-dsl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/iceberg-dsl)
![GitHub](https://img.shields.io/github/license/revalo/iceberg)


<p align="center">
<img src="images/logo.png" width="150">
</p>

Iceberg is a compositional diagramming and graphics library embedding in Python. It is designed to be performant, extensible, and easy to use.

## Testimonials

<p align="left">
<img src="images/testimonial.jpg" width="400">
</p>

## Showcase

### Neural Network

A composable Neural Network diagramming class written in iceberg. Full example in `examples/neural_network.py`.

<img src="images/nn.png" width="500">

```python
network = NeuralNetwork(
    # Number of nodes in each layer!
    [3, 4, 4, 2],
    node_border_color=Colors.BLACK,
    line_path_style=PathStyle(Colors.BLACK, thickness=3),
)
node = network.layer_nodes[1][0]
node.border_color = Colors.RED
node.border_thickness = 5

canvas = Blank(Bounds(size=(1080, 720)), background=Colors.WHITE)
scene = canvas.add_centered(network)

renderer = Renderer()
renderer.render(scene)
renderer.save_rendered_image("test.png")

```

### Tex, Arrangements, SVG Outputs

Iceberg supports Tex and Arrangements. Full example in `examples/connect.py`.

<p align="left">
<img src="images/connect.svg" width="400">
</p>

```python
left_ellipse = Ellipse(
    Bounds(size=(_CIRCLE_WIDTH, _CIRCLE_WIDTH)),
    border_color=Color.from_hex("#d63031"),
    border_thickness=_BORDER_THICKNESS,
    fill_color=Color.from_hex("#ff7675"),
).pad(_CIRCLE_PAD)

right_ellipse = Ellipse(
    Bounds(size=(_CIRCLE_WIDTH, _CIRCLE_WIDTH)),
    border_color=Color.from_hex("#0984e3"),
    border_thickness=_BORDER_THICKNESS,
    fill_color=Color.from_hex("#74b9ff"),
).pad(_CIRCLE_PAD)

ellipses = Arrange(
    [left_ellipse, right_ellipse],
    gap=500,
)

with ellipses:
    arrow = Arrow(
        left_ellipse.bounds.corners[Corner.MIDDLE_RIGHT],
        right_ellipse.bounds.corners[Corner.MIDDLE_LEFT],
        line_path_style=PathStyle(
            color=Colors.BLACK,
            thickness=3,
        ),
    )
arrow_label = MathTex("f(x) = x^2", scale=4)
arrow = LabelArrow(
    arrow,
    arrow_label,
    Corner.BOTTOM_MIDDLE,
    distance=20,
)
connection = Compose([ellipses, arrow])

text_block = Text(
    "This is some really long text, and it's going to wrap around at some point, because it's so long and I spent a lot of time on it.",
    font_style=FontStyle(
        family=_FONT_FAMILY,
        size=28,
        color=Colors.BLACK,
    ),
    width=connection.bounds.width,
)

scene = Arrange(
    [connection, text_block],
    gap=10,
    arrange_direction=Arrange.Direction.VERTICAL,
)
```


## Install

The library is still under development, hence updates are frequent. To install the latest version, run the following command:

```
pip install git+https://github.com/revalo/iceberg.git
```

## Quickstart

Full example in `examples/quickstart.py`.

```python
from iceberg import Renderer, Bounds, Colors, FontStyle
from iceberg.primitives import Rectangle, Blank, SimpleText, Directions

# Blank is a large empty rectangle.
canvas = Blank(Bounds(size=(1080, 720)))

# Create a rectangle.
rectangle = Rectangle(
    Bounds(size=(500, 100)),
    Colors.WHITE,
    border_thickness=3,
)

# Create a text.
text = Text(
    text="Hello, World!",
    font_style=FontStyle(
        family="Arial",
        size=28,
        color=Colors.WHITE,
    ),
)

# Place the text below the rectangle.
rectangle_and_text = rectangle.next_to(text, Directions.DOWN * 10)

# Center the rectangle and text combination to the canvas.
scene = canvas.add_centered(rectangle_and_text)

# Render the scene and save it to a file.
renderer = Renderer()
renderer.render(scene)
renderer.save_rendered_image("test.png")
```

Should produce:

<img src="images/quickstart.png" width="500">
