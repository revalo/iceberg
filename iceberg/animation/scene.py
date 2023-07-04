from typing import Callable

from iceberg import Drawable, Renderer
import imageio
import tqdm


class Scene(object):
    def __init__(self, duration: float, make_frame: Callable[[float], Drawable]):
        self._duration = duration
        self._make_frame = make_frame

    @property
    def duration(self) -> float:
        return self._duration

    def make_frame(self, t: float) -> Drawable:
        return self._make_frame(t)

    def __add__(self, other: "Scene") -> "Scene":
        def _make_frame(t: float) -> Drawable:
            if t < self.duration:
                return self.make_frame(t)
            else:
                return other.make_frame(t - self.duration)

        return Scene(self.duration + other.duration, _make_frame)

    def concat(self, scene: "Scene") -> "Scene":
        return self + scene

    def freeze(self, duration: float) -> "Scene":
        return Scene(duration, lambda t: self._make_frame(self.duration))

    def reverse(self) -> "Scene":
        return Scene(self.duration, lambda t: self.make_frame(self.duration - t))

    def render(
        self,
        filename: str,
        renderer: Renderer = None,
        fps: int = 60,
        progress_bar: bool = True,
    ) -> None:
        total_frames = int(fps * self.duration)

        if renderer is None:
            renderer = Renderer()

        bounds = None

        with imageio.get_writer(filename, mode="I", fps=fps) as writer:
            for frame_index in tqdm.trange(total_frames, disable=not progress_bar):
                t = frame_index / fps
                frame_drawable = self.make_frame(t)

                if bounds is None:
                    bounds = frame_drawable.bounds

                frame_drawable = frame_drawable.crop(bounds)

                renderer.render(frame_drawable)
                frame_pixels = renderer.get_rendered_image()
                writer.append_data(frame_pixels)
