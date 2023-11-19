from iceberg import Renderer, Drawable, Scene
from PIL import Image

import numpy as np
import os
import shutil
from pixelmatch.contrib.PIL import pixelmatch


def _compare_images(
    expected_filename,
    expected_image,
    rendered_image,
    pixel_tolerance,
    fractional_mismatch_tolerance,
):
    img_diff = Image.new("RGBA", expected_image.size)

    # Use numpy to calculate the number of pixels that don't match.
    number_of_total_pixels = expected_image.size[0] * expected_image.size[1]
    try:
        number_of_mismatched_pixels = np.sum(
            (
                (np.array(expected_image, dtype=np.float32) / 255)
                - (np.array(rendered_image, dtype=np.float32) / 255)
            )
            > pixel_tolerance
        )
    except ValueError:
        number_of_mismatched_pixels = number_of_total_pixels

    fraction_mismatched = number_of_mismatched_pixels / number_of_total_pixels

    if fraction_mismatched > fractional_mismatch_tolerance:
        pixelmatch(expected_image, rendered_image, img_diff, pixel_tolerance)

        # Save the rendered image, the expected image, and the diff image.
        debug_dir = os.path.join("tests", "testoutput")
        os.makedirs(debug_dir, exist_ok=True)
        rendered_image.save(os.path.join(debug_dir, f"rendered_{expected_filename}"))
        expected_image.save(os.path.join(debug_dir, f"expected_{expected_filename}"))
        img_diff.save(os.path.join(debug_dir, f"diff_{expected_filename}"))
        assert False, f"Image mismatch: {fraction_mismatched * 100:.2f}%"


def check_render(
    drawable: Drawable,
    expected_filename: str,
    generate_expected: bool = False,
    pixel_tolerance: float = 0.1,
    fractional_mismatch_tolerance: float = 0.01,
):
    """Checks that the given Drawable renders to the expected image.

    Args:
        drawable: The Drawable to render.
        expected_filename: The filename of the expected image.
        generate_expected: Whether to generate the expected image if it does not exist.
        pixel_tolerance: The maximum difference in pixel values between the rendered image and the expected image.
        fractional_mismatch_tolerance: The maximum fraction of pixels that can differ between the rendered image and the expected image.

    Raises:
        AssertionError: If the rendered image does not match the expected image.
    """

    expected_full_filename = os.path.join("tests", "testdata", expected_filename)

    renderer = Renderer()
    renderer.render(drawable)
    rendered_image = renderer.get_rendered_image()

    if generate_expected:
        renderer.save_rendered_image(expected_full_filename)
        return

    expected_image = Image.open(expected_full_filename)
    rendered_image = Image.fromarray(rendered_image)

    _compare_images(
        expected_filename,
        expected_image,
        rendered_image,
        pixel_tolerance,
        fractional_mismatch_tolerance,
    )


def _test_times(duration: float, num_frames_to_test: int):
    """Returns a list of times to test.

    Args:
        duration: The duration of the animation.
        num_frames_to_test: The number of frames to test. This will be evenly spaced throughout the animation.

    Returns:
        A list of times to test.
    """

    return [duration * i / num_frames_to_test for i in range(num_frames_to_test)]


def check_animation(
    scene: Scene,
    expected_name: str,
    generate_expected: bool = False,
    pixel_tolerance: float = 0.1,
    fractional_mismatch_tolerance: float = 0.01,
    num_frames_to_test: int = 10,
    duration_tolerance: float = 0.01,
):
    """Checks that the given Animated scene renders to the expected animation.

    Args:
        scene: The animated scene to render.
        expected_name: The name of the expected animation.
        generate_expected: Whether to generate the expected animation if it does not exist.
        pixel_tolerance: The maximum difference in pixel values between the rendered image and the expected image.
        fractional_mismatch_tolerance: The maximum fraction of pixels that can differ between the rendered image and the expected image.
        num_frames_to_test: The number of frames to test. This will be evenly spaced throughout the animation.
        duration_tolerance: The maximum difference in duration between the rendered animation and the expected animation.

    Raises:
        AssertionError: If the rendered animation does not match the expected animation.
    """

    expected_directory_name = os.path.join("tests", "testdata", expected_name)
    duration_info_filename = os.path.join(expected_directory_name, "duration.txt")

    renderer = Renderer()

    if generate_expected:
        # Delete the directory if it already exists.
        if os.path.exists(expected_directory_name):
            shutil.rmtree(expected_directory_name)

        os.makedirs(expected_directory_name, exist_ok=True)

        expected_duration = scene.duration
        with open(duration_info_filename, "w") as f:
            f.write(str(expected_duration))

        times = _test_times(expected_duration, num_frames_to_test)
        images = []
        for time in times:
            renderer.render(scene.make_frame(time))
            images.append(renderer.get_rendered_image())

        for i, image in enumerate(images):
            Image.fromarray(image).save(
                os.path.join(expected_directory_name, f"{i}.png")
            )

        return

    with open(duration_info_filename, "r") as f:
        expected_duration = float(f.read())

    assert (
        abs(expected_duration - scene.duration) <= duration_tolerance
    ), f"Duration mismatch, expected {expected_duration}, got {scene.duration}, difference {abs(expected_duration - scene.duration)}"

    times = _test_times(scene.duration, num_frames_to_test)

    for i, time in enumerate(times):
        renderer.render(scene.make_frame(time))
        expected_image = Image.open(
            os.path.join(expected_directory_name, f"{i}.png")
        ).convert("RGBA")
        rendered_image = Image.fromarray(renderer.get_rendered_image())

        _compare_images(
            f"{expected_name}_{i}.png",
            expected_image,
            rendered_image,
            pixel_tolerance,
            fractional_mismatch_tolerance,
        )
