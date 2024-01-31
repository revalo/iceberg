from typing import Tuple, Union, Sequence
from iceberg import (
    DrawableWithChild,
    Drawable,
    Corner,
    Line,
    PathStyle,
    Colors,
    Compose,
)

from .tree_layout import buchheim, LayoutTreeNode, LayoutTree


class TreeNode(DrawableWithChild):
    drawable: Drawable
    tree_children: Tuple["TreeNode", ...]

    def __init__(
        self,
        drawable: Drawable,
        children: Sequence[Union["TreeNode", Drawable]] = None,
    ):
        """A container class for a tree node for drawing trees.

        Args:
            drawable: The drawable for this node.
            children: The children of this node, must also be of type `TreeNode`.
        """

        converted_children = []

        if not children is None:
            for child in children:
                if isinstance(child, TreeNode):
                    converted_children.append(child)
                elif isinstance(child, Drawable):
                    converted_children.append(TreeNode(child))

        self.init_from_fields(
            drawable=drawable, tree_children=tuple(converted_children)
        )

    def setup(self):
        self.set_child(self.drawable)


class Tree(DrawableWithChild):
    root: TreeNode
    unit_size: float = 70

    def setup(self):
        # Convert our TreeNode to LayoutTreeNode.

        def convert(node: TreeNode) -> LayoutTreeNode:
            return LayoutTreeNode(
                contents=node, children=[convert(x) for x in node.tree_children]
            )

        layout_root = convert(self.root)
        layout_tree = buchheim(layout_root)

        objects = []
        lines = []

        def walk(node: LayoutTree, parent=None):
            x, y = node.x * self.unit_size, node.y * self.unit_size
            draw_node = node.tree.contents.drawable.move_to(x, y, Corner.CENTER)
            objects.append(draw_node)

            if parent:
                px, py = parent.bounds.corners[Corner.BOTTOM_MIDDLE]
                mx, my = draw_node.bounds.corners[Corner.TOP_MIDDLE]
                line = Line(
                    (px, py), (mx, my), path_style=PathStyle(color=Colors.WHITE)
                )
                lines.append(line)

            for child in node.children:
                walk(child, parent=draw_node)

        walk(layout_tree)

        self.set_child(Compose(lines + objects))
