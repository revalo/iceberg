from typing import Callable, Sequence, Union

from iceberg import Drawable, Renderer, DrawableWithChild
from iceberg.animation import tween, EaseType
from PIL import Image
import av
import tqdm

from iceberg.core import Bounds
from iceberg.core.drawable import Drawable
from abc import ABC, abstractmethod
from absl import logging
import numpy as np


class Animated(Drawable):
    """A drawable that depends on time."""

    states: Sequence[Drawable]
    durations: Union[Sequence[float], float]
    ease_types: Union[Sequence[EaseType], EaseType] = EaseType.EASE_IN_OUT_QUAD
    ease_fns: Union[Sequence[Callable], Callable] = None
    start_time: float = 0

    def __init__(
        self,
        states: Sequence[Drawable],
        durations: Union[Sequence[float], float],
        ease_types: Union[Sequence[EaseType], EaseType] = EaseType.EASE_IN_OUT_QUAD,
        ease_fns: Union[Sequence[Callable], Callable] = None,
        start_time: float = 0,
    ) -> None:
        self.init_from_fields(
            states=states,
            durations=durations,
            ease_types=ease_types,
            ease_fns=ease_fns,
            start_time=start_time,
        )

    def setup(self):
        """A drawable that depends on time, given a sequence of drawables and durations.

        This drawable will animate between the given states, with the given durations and ease
        types.

        Args:
            states: The states to animate between.
            durations: The durations of each state in seconds or a single duration to use if
                all states have the same duration.
            ease_types: The ease types to use for each pair of states, or a single ease type
                to use for all states.
            ease_fns: The ease functions to use for each pair of states, or a single ease
                function to use for all states. If specified, this overrides the `ease_types`.
            start_time: The time at which to start the animation.
        """

        self._ease_fns = self.ease_fns
        if self._ease_fns is None:
            self._ease_fns = self.ease_types

        self._durations = self.durations
        if isinstance(self._durations, float) or isinstance(self._durations, int):
            self._durations = [self._durations] * (len(self.states) - 1)

        if not isinstance(self._ease_fns, Sequence):
            self._ease_fns = [self._ease_fns] * (len(self.states) - 1)

        assert (
            len(self.states) >= 2
        ), "Must have at least two states to animate between."
        assert (
            len(self.states) == len(self._durations) + 1
        ), "Every pair of states must have a duration."
        assert (
            len(self.states) == len(self._ease_fns) + 1
        ), "Every pair of states must have an ease."

        self._states = self.states
        self._total_duration = sum(self._durations) + self.start_time
        self._start_time = self.start_time
        self.cursor = 0

    @property
    def total_duration(self) -> float:
        return self._total_duration

    def _get_drawable_at_t(self, t: float) -> Drawable:
        """Get the drawable at time t.

        Args:
            t: The time in seconds.

        Returns:
            The drawable at time t.
        """

        t -= self._start_time

        if t < 0:
            return self._states[0]

        if t >= self._total_duration - self._start_time:
            return self._states[-1]

        time_so_far = 0
        for i, duration in enumerate(self._durations):
            if time_so_far + duration > t:
                break
            time_so_far += duration

        # Animate between the states.
        progress = (t - time_so_far) / duration
        return tween(
            self._states[i], self._states[i + 1], progress, ease_fn=self._ease_fns[i]
        )

    @property
    def bounds(self) -> Bounds:
        return self._get_drawable_at_t(self._time).bounds

    @property
    def children(self) -> Sequence[Drawable]:
        return self._get_drawable_at_t(self._time).children

    def draw(self, canvas):
        self._get_drawable_at_t(self._time).draw(canvas)

    def frozen(self, t: float = None):
        """Get a frozen version of this drawable at time t.

        Args:
            t: The time to freeze the drawable at.

        Returns:
            A frozen version of this drawable at time t.
        """

        if t is None:
            t = self._total_duration

        return self._get_drawable_at_t(t)


def _get_drawable_duration(drawable: Drawable) -> float:
    """Gets the duration of a drawable by finding the longest duration of any animated drawable.

    Args:
        drawable: The drawable to find the duration of.

    Returns:
        The duration of the drawable.
    """
    duration = 0
    current_animated: Sequence[Animated] = drawable.find_all(
        lambda d: isinstance(d, Animated)
    )
    for animated in current_animated:
        duration = max(duration, animated.total_duration)
    return duration


class Frozen(DrawableWithChild):
    child: Drawable
    t: float = None

    def setup(self):
        """Get a frozen drawable at time t. If t is None, then the drawable is frozen at the
        end of its animation.

        Args:
            child: The drawable to freeze.
            t: The time to freeze the drawable at.
        """

        self.__t = self.t
        if self.__t is None:
            self.__t = _get_drawable_duration(self.child)

    def _time_freeze(self):
        self.child.set_time(self.__t)

    @property
    def bounds(self) -> Bounds:
        self._time_freeze()
        return self.child.bounds

    @property
    def children(self) -> Sequence[Drawable]:
        self._time_freeze()
        return self.child.children

    def draw(self, canvas):
        self._time_freeze()
        self.child.draw(canvas)


class Scene(object):
    """A scene is a short segment of animation.

    A scene is a short segment of animations. Scenes can be added together to create longer
    animations. Scenes provide the most basic way to create animations, where you specify the
    duration of the scene and a function that returns a drawable as a function of time.
    """

    def __init__(self, duration: float, make_frame: Callable[[float], Drawable]):
        """A scene is a short segment of animation.

        Args:
            duration: The duration of the scene in seconds.
            make_frame: A function that returns a drawable as a function of time.
        """

        self._duration = duration
        self._make_frame = make_frame

    @property
    def duration(self) -> float:
        """The duration of the scene in seconds."""
        return self._duration

    def make_frame(self, t: float) -> Drawable:
        """Returns the drawable at time t."""

        return self._make_frame(t)

    def __add__(self, other: "Scene") -> "Scene":
        """Concatenates two scenes together."""

        def _make_frame(t: float) -> Drawable:
            if t < self.duration:
                return self.make_frame(t)
            else:
                return other.make_frame(t - self.duration)

        return Scene(self.duration + other.duration, _make_frame)

    def concat(self, scene: "Scene") -> "Scene":
        """Concatenates two scenes together."""
        return self + scene

    def freeze(self, duration: float) -> "Scene":
        """Freezes the scene for a given duration."""
        return Scene(duration, lambda t: self._make_frame(self.duration))

    def reverse(self) -> "Scene":
        """Reverses the scene."""
        return Scene(self.duration, lambda t: self.make_frame(self.duration - t))

    def render(
        self,
        filename: str,
        renderer: Renderer = None,
        fps: int = 60,
        progress_bar: bool = True,
    ) -> None:
        """Renders the scene to a file.

        Args:
            filename: The filename to render to.
            renderer: The renderer to use. If not specified, a default renderer will be used.
            fps: The frames per second to render at.
            progress_bar: Whether to show a progress bar while rendering.
        """
        _IS_GIF = False

        if filename.endswith(".gif"):
            _IS_GIF = True
            possible_fps = [25, 33.3, 50, 100]

            if fps not in possible_fps:
                logging.warning(
                    f"FPS {fps} is not a standard GIF FPS, rounding to nearest."
                )

            fps = min(possible_fps, key=lambda x: abs(x - fps))

        total_frames = int(fps * self.duration)

        if renderer is None:
            renderer = Renderer()

        bounds = None

        pil_images = []
        container = None
        stream = None

        if not _IS_GIF:
            container = av.open(filename, mode="w")
            stream = container.add_stream("libx264", rate=fps)

        for frame_index in tqdm.trange(total_frames, disable=not progress_bar):
            t = frame_index / fps
            frame_drawable = self.make_frame(t)

            if bounds is None:
                bounds = frame_drawable.bounds.round()

                if not _IS_GIF:
                    stream.width = bounds.width
                    stream.height = bounds.height

            frame_drawable = frame_drawable.crop(bounds)

            renderer.render(frame_drawable)
            frame_pixels = renderer.get_rendered_image()

            if not _IS_GIF:
                frame_pixels = np.round(frame_pixels[:, :, :3]).astype(np.uint8)
                frame = av.VideoFrame.from_ndarray(frame_pixels, format="rgb24")
                for packet in stream.encode(frame):
                    container.mux(packet)

            if _IS_GIF:
                pil_images.append(Image.fromarray(frame_pixels, mode="RGBA"))

        if not _IS_GIF:
            # Flush stream
            for packet in stream.encode():
                container.mux(packet)
            container.close()

        if _IS_GIF:
            assert len(pil_images) > 1, "No frames were rendered."
            pil_images[0].save(
                filename,
                save_all=True,
                append_images=pil_images[1:],
                duration=1000 // fps,
                loop=0,
                disposal=2,
            )

    def ipython_display(
        self, fps: int = 60, loop: bool = True, display_format: str = "mp4"
    ) -> None:
        from IPython.display import Video, display, HTML
        import base64

        if display_format == "mp4":
            html_attributes = ["controls"]

            if loop:
                html_attributes.append("loop")

            self.render("__temp__.mp4", fps=fps)
            display(
                Video(
                    filename="__temp__.mp4",
                    embed=True,
                    html_attributes=" ".join(html_attributes),
                )
            )
        elif display_format == "gif":
            self.render("__temp__.gif", fps=fps)

            with open("__temp__.gif", "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            display(HTML(f'<img src="data:image/gif;base64,{b64}" />'))


class Playbook(ABC):
    """A playbook is an easy way to create linear animations.

    Playbooks have a method called play that takes a time-aware drawable and adds it
    to the timeline. Users must implement the timeline method to create a linear sequence of
    """

    def __init__(self) -> None:
        self._cursor = 0
        self._scenes = []

        self.timeline()

    @property
    def combined_scene(self) -> Scene:
        """Returns the combined scene."""

        assert len(self._scenes) > 0, "No scenes have been added to the playbook."

        # Add all the scenes together.
        scene = self._scenes[0]
        for next_scene in self._scenes[1:]:
            scene += next_scene

        return scene

    def frozen(self, drawable: Drawable, t: float = None) -> Drawable:
        """Returns a frozen drawable at time t. If t is not specified, the end of the animation is
        returned.

        Args:
            t: The time in seconds, or None to return the end of the animation.

        Returns:
            The frozen drawable at time t.
        """

        if t is None:
            t = self._get_drawable_duration()

        return self._get_drawable_at_t(t)

    def freeze(self, duration: float):
        """Freezes the last scene for a given duration."""

        if len(self._scenes) == 0:
            raise ValueError(
                "No scenes have been added to the playbook. So cannot freeze."
            )

        self._scenes.append(self._scenes[-1].freeze(duration))
        self._cursor += duration

    def add_scene(self, scene: Scene):
        """Manually add a scene to the playbook."""

        self._scenes.append(scene)
        self._cursor += scene.duration

    def play(self, drawable: Drawable, duration: float = None) -> None:
        """Adds a time-aware drawable to the timeline.

        Args:
            drawable: The drawable to add to the timeline.
            duration: The duration of the drawable. If not specified, the total duration of the
                drawable is used.
        """

        # Find the duration of the animation, by finding all the animated objects.

        if duration is None:
            duration = _get_drawable_duration(drawable)

        # Build the scene.
        def _make_frame(t: float) -> Drawable:
            drawable.set_time(t)
            return drawable

        scene = Scene(duration, _make_frame)
        self._scenes.append(scene)
        self._cursor += duration

    @abstractmethod
    def timeline(self):
        """The timeline method is where the user should add scenes to the playbook."""
        pass

    def ipython_display(
        self, fps: int = 60, loop: bool = True, display_format: str = "mp4"
    ) -> None:
        """Displays the animation in IPython."""

        self.combined_scene.ipython_display(
            fps=fps, loop=loop, display_format=display_format
        )
