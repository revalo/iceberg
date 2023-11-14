import iceberg as ice


class Scene1(ice.Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> ice.Drawable:
        blank = ice.Blank(ice.Bounds(size=(1920, 1080)), ice.Colors.WHITE)

        _SIZE = 500
        _DISPLACEMENT = 600
        y = blank.bounds.height / 2 - _SIZE / 2
        start_x = blank.bounds.width / 2 - _SIZE / 2 - _DISPLACEMENT
        end_x = blank.bounds.width / 2 - _SIZE / 2 + _DISPLACEMENT

        rect = ice.tween(
            ice.Rectangle(
                ice.Bounds(size=(_SIZE, _SIZE)),
                fill_color=ice.Colors.BLUE,
                border_radius=0,
            ).move(start_x, y),
            ice.Rectangle(
                ice.Bounds(size=(_SIZE, _SIZE)),
                fill_color=ice.Colors.RED,
                border_radius=1000,
            ).move(end_x, y),
            t / self.duration,
        )

        return ice.Compose([blank, rect])


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.5) + scene.reverse()
    final.render("test.gif", fps=60)
