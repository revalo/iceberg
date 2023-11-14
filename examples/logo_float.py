import iceberg as ice
import os


class Scene1(ice.Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> ice.Drawable:
        progress = t / self.duration

        logo = ice.Image(os.path.join("images", "logo.png"))
        blank = ice.Blank(logo.bounds, ice.Colors.TRANSPARENT)

        dy = ice.tween(-10, 10, progress)

        scene = ice.Anchor([blank, logo.move(0, dy)])

        return scene


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.1) + scene.reverse()
    final.render("test.gif", fps=60)
