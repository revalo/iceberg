# IceBerg

![PyPI](https://img.shields.io/pypi/v/iceberg-dsl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/iceberg-dsl)
![GitHub](https://img.shields.io/github/license/revalo/iceberg)


<p align="center">
<img src="images/logo.gif" width="150">
</p>

Iceberg is a compositional diagramming and graphics library embedded in Python. It is designed to be performant, extensible, and easy to use.

<p align="center">
<img src="images/neural_network_compute.gif" width="500">
</p>
<p align="center">
<i>The above animation was 33 lines of code</i>
</p>

## Playground
<a target="_blank" href="https://colab.research.google.com/github/revalo/iceberg/blob/main/docs/blank.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

[Online Interactive Playground on Colab!](https://colab.research.google.com/github/revalo/iceberg/blob/main/docs/blank.ipynb)

<!-- ## Testimonials

<p align="left">
<img src="images/testimonial.jpg" width="400">
</p>
<p align="left">
<img src="images/testimonial2.jpg" width="400">
</p> -->

## Documentation

A walkthrough tutorial on diagramming with Iceberg can be found [here](https://github.com/revalo/iceberg/blob/main/docs/tutorial.ipynb).

## Showcase

### Geometry

<img src="images/angle.gif" width="300">


### Neural Network

A composable Neural Network diagramming class written in iceberg. Full example in `examples/neural_network.py`.

<img src="images/nn.gif" width="500">

```python
import icerberg as ice

network = NeuralNetwork(
    # Number of nodes in each layer!
    layer_node_counts=[3, 4, 4, 2],
    node_border_color=ice.Colors.BLACK,
    line_path_style=ice.PathStyle(ice.Colors.BLACK, thickness=3),
)

canvas = ice.Blank(ice.Bounds(size=(1080, 720)), background=ice.Colors.WHITE)
scene = canvas.add_centered(network)
scene.render("test.png")

```

### Tex, Arrangements, SVG Outputs

Iceberg supports Tex and Arrangements. Full example in `examples/connect.py`.

<p align="left">
<img src="images/connect.svg" width="400">
</p>

```python
import iceberg as ice

left_ellipse = ice.Ellipse(
    rectangle=ice.Bounds(size=(_CIRCLE_WIDTH, _CIRCLE_WIDTH)),
    border_color=ice.Color.from_hex("#d63031"),
    border_thickness=_BORDER_THICKNESS,
    fill_color=ice.Color.from_hex("#ff7675"),
).pad(_CIRCLE_PAD)

right_ellipse = ice.Ellipse(
    rectangle=ice.Bounds(size=(_CIRCLE_WIDTH, _CIRCLE_WIDTH)),
    border_color=ice.Color.from_hex("#0984e3"),
    border_thickness=_BORDER_THICKNESS,
    fill_color=ice.Color.from_hex("#74b9ff"),
).pad(_CIRCLE_PAD)

ellipses = ice.Arrange(
    [left_ellipse, right_ellipse],
    gap=500,
)

with ellipses:
    # Within this context, we can use `relative_bounds` to get the bounds of the
    # `left_ellipse` and `right_ellipse` relative to the `ellipses` object.
    arrow = ice.Arrow(
        left_ellipse.relative_bounds.corners[Corner.MIDDLE_RIGHT],
        right_ellipse.relative_bounds.corners[Corner.MIDDLE_LEFT],
        line_path_style=ice.PathStyle(
            color=ice.Colors.BLACK,
            thickness=3,
        ),
    )

arrow_label = ice.MathTex("f(x) = x^2").scale(4)
arrow = ice.LabelArrow(
    arrow,
    arrow_label,
    ice.Corner.BOTTOM_MIDDLE,
    distance=20,
)
connection = ice.Compose([ellipses, arrow])

text_block = ice.Text(
    "This is some really long text, and it's going to wrap around at some point, because it's so long and I spent a lot of time on it.",
    font_style=ice.FontStyle(
        family=_FONT_FAMILY,
        size=28,
        color=ice.Colors.BLACK,
    ),
    width=connection.bounds.width,
)

scene = ice.Arrange(
    [connection, text_block],
    gap=10,
    arrange_direction=ice.Arrange.Direction.VERTICAL,
)
```

### Animations

IceBerg can take a difference between two scenes and interpolate the difference.

```python
sceneA = blank.add_centered(arrangeA)
sceneB = blank.add_centered(arrangeB)

# Interpolate between two different arrangements.
scene = tween(sceneA, sceneB, t / self.duration)
```

<p align="left">
<img src="images/arrange_animate.gif" width="300">
</p>

## Install

The library is still under development, hence updates are frequent. To install the latest version, run the following command:

```
pip install git+https://github.com/revalo/iceberg.git
```

**Not recommended yet**, but if you want a stable version, use the PyPI package.:


```
pip install -U iceberg-dsl
```

## Quickstart

Full example in `examples/quickstart.py`.

```python
import iceberg as ice

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
scene.render("test.png")
```

Should produce:

<img src="images/quickstart.png" width="500">

## Citation

Cite Iceberg by clicking the "cite this repository" button on the right sidebar.

```
@software{IceBerg_Contributors_IceBerg_Compositional_2023,
    author = {{IceBerg Contributors}},
    license = {MIT},
    month = jul,
    title = {{IceBerg – Compositional Graphics & Diagramming}},
    url = {https://github.com/revalo/iceberg},
    year = {2023}
}
```
