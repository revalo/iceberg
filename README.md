# IceBerg

<p align="center">
<img src="images/logo.png" width="150">
</p>

Iceberg is a compositional diagramming and graphics library embedding in Python. It is designed to be performant, extensible, and easy to use.

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
scene = canvas.center_to(network)

renderer = Renderer()
renderer.render(scene)
renderer.save_rendered_image("test.png")

```


## Install

The library is still under heavy development, hence updates are frequent. To install the latest version, run the following command:

```
pip install git+https://github.com/revalo/iceberg.git
```

## Quickstart

Full example in `examples/quickstart.py`.

```python
from iceberg import Blank, Bounds, Rectangle, Colors, Text, FontStyle, Directions, Renderer

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
scene = canvas.center_to(rectangle_and_text)

# Render the scene and save it to a file.
renderer = Renderer()
renderer.render(scene)
renderer.save_rendered_image("test.png")
```

Should produce:

<img src="images/quickstart.png" width="500">
