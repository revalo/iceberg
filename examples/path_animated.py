import iceberg as ice


class Play(ice.Playbook):
    def timeline(self) -> ice.Drawable:
        blank = ice.Blank(ice.Bounds(size=(512, 512)), ice.Colors.WHITE)

        path_style = ice.PathStyle(
            ice.Colors.BLUE,
            thickness=5,
            dashed=True,
            dash_intervals=[20.0, 10.0],
            dash_phase=10.0,
        )

        line = ice.CurvedCubicLine(
            points=[
                (10, 10),
                (256, 10),
                (256, 256),
            ],
            path_style=path_style,
        )

        animated_line = ice.Animated(
            [
                ice.PartialPath(line, 0, 0.01),
                ice.PartialPath(line, 0, 1.0),
            ],
            0.5,
        )

        frozen_line = animated_line.frozen()
        label = ice.MathTex("x^3").scale(4)
        circle = (
            ice.Ellipse(
                rectangle=ice.Bounds(size=(100, 100)),
                border_color=ice.Color.from_hex("#d63031"),
                border_thickness=8,
                fill_color=ice.Color.from_hex("#ff7675"),
            )
            .pad(5)
            .with_anchor(ice.Corner.CENTER)
        ).add_centered(label)
        container = ice.Blank(
            ice.Bounds(size=circle.bounds.size), ice.Colors.TRANSPARENT
        )
        container = ice.PointAlign(
            frozen_line.points[-1],
            container,
            ice.Corner.TOP_MIDDLE,
        )

        animated_circle = ice.Animated(
            [circle.scale(0.0), circle.scale(1.1), circle.scale(1)],
            [0.3, 0.1],
            start_time=0.3,
        )
        container = container.add_centered(animated_circle)

        scene = ice.Anchor([blank, animated_line, container])
        self.play(scene)

        with scene:
            new_line = ice.Line(
                container.relative_bounds.corners[ice.Corner.BOTTOM_MIDDLE],
                (container.relative_bounds.corners[ice.Corner.BOTTOM_MIDDLE][0], 500),
                path_style,
            )

        animated_line = ice.Animated(
            [
                ice.PartialPath(new_line, 0, 0.01),
                ice.PartialPath(new_line, 0, 1.0),
            ],
            0.3,
        )
        scene = ice.Anchor(
            [blank, frozen_line, ice.Frozen(child=container), animated_line]
        )
        self.play(scene)


if __name__ == "__main__":
    scene = Play().combined_scene
    scene = scene + scene.reverse()
    scene.render("test.mp4")
