"""Latex rendering adapted from
https://github.com/ManimCommunity/manim
"""

import os
import re
import shutil

from absl import logging

from iceberg import Color, Colors, DrawableWithChild
from iceberg.primitives.svg import SVG, SVGPath
from iceberg.utils import temp_directory, temp_filename


class LatexError(Exception):
    pass


def _create_tex_svg(full_tex: str, svg_file: str, compiler: str):
    if compiler == "latex":
        program = "latex"
        dvi_ext = ".dvi"
    elif compiler == "xelatex":
        program = "xelatex -no-pdf"
        dvi_ext = ".xdv"
    else:
        raise NotImplementedError(f"Compiler '{compiler}' is not implemented")

    # Check if program is installed.
    if shutil.which(program.split()[0]) is None:
        raise LatexError(
            f"Program '{program.split()[0]}' is not installed for LaTeX rendering. "
            f"Please install it and make it available in your PATH environment variable."
        )

    # Write tex file
    root, _ = os.path.splitext(svg_file)
    with open(root + ".tex", "w", encoding="utf-8") as tex_file:
        tex_file.write(full_tex)

    # tex to dvi
    if os.system(
        " ".join(
            (
                program,
                "-interaction=batchmode",
                "-halt-on-error",
                f'-output-directory="{os.path.dirname(svg_file)}"',
                f'"{root}.tex"',
                ">",
                os.devnull,
            )
        )
    ):
        logging.error("LaTeX Error!  Not a worry, it happens to the best of us.")
        error_str = ""
        with open(root + ".log", "r", encoding="utf-8") as log_file:
            error_match_obj = re.search(r"(?<=\n! ).*\n.*\n", log_file.read())
            if error_match_obj:
                error_str = error_match_obj.group()
                logging.debug(
                    f"The error could be:\n`{error_str}`",
                )
        raise LatexError(error_str)

    # dvi to svg
    os.system(
        " ".join(
            (
                "dvisvgm",
                f'"{root}{dvi_ext}"',
                "-n",
                "-v",
                "0",
                "-o",
                f'"{svg_file}"',
                ">",
                os.devnull,
            )
        )
    )

    # Cleanup superfluous documents
    for ext in (".tex", dvi_ext, ".log", ".aux"):
        try:
            os.remove(root + ext)
        except FileNotFoundError:
            pass


def tex_content_to_svg_file(
    content: str,
    preamble: str,
    compiler: str = "latex",
) -> str:
    full_tex = (
        "\n\n".join(
            (
                "\\documentclass[preview]{standalone}",
                preamble,
                "\\begin{document}",
                content,
                "\\end{document}",
            )
        )
        + "\n"
    )

    svg_file = os.path.join(temp_directory(), temp_filename(tex=full_tex) + ".svg")
    if not os.path.exists(svg_file):
        _create_tex_svg(full_tex, svg_file, compiler)
    return svg_file


_DEFAULT_PREAMBLE = r"""
\usepackage[english]{babel}
\usepackage[utf8]{inputenc}
%\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{dsfont}
\usepackage{setspace}
\usepackage{tipa}
\usepackage{relsize}
\usepackage{textcomp}
\usepackage{mathrsfs}
\usepackage{calligra}
\usepackage{wasysym}
\usepackage{ragged2e}
\usepackage{physics}
\usepackage{xcolor}
\usepackage{microtype}
\usepackage{pifont}
\DisableLigatures{encoding = *, family = * }
\linespread{1}
"""


class Tex(DrawableWithChild):
    """A LaTeX object, which renders LaTeX using dvisvgm.

    Args:
        tex: The LaTeX code to render.
        preamble: The LaTeX preamble to use.
        compiler: The LaTeX compiler to use.
        svg_scale: The scale of the SVG.
        color: The color of the SVG.
    """

    tex: str
    preamble: str = _DEFAULT_PREAMBLE
    compiler: str = "latex"
    svg_scale: float = 1.0
    color: Color = Color(0, 0, 0, 1)

    def setup(self) -> None:
        svg_filename = tex_content_to_svg_file(self.tex, self.preamble, self.compiler)
        self._svg = SVG(svg_filename=svg_filename, color=self.color)
        self.set_child(self._svg.scale(self.svg_scale))


class MathTex(DrawableWithChild):
    """A LaTeX math formula using the align* environment by default.

    Args:
        tex: The LaTeX code to render in math mode.
        preamble: The LaTeX preamble to use.
        environment: The LaTeX environment to use. Defaults to "align*".
        compiler: The LaTeX compiler to use.
        svg_scale: The scale of the SVG.
        color: The color of the SVG.
    """

    tex: str
    preamble: str = _DEFAULT_PREAMBLE
    environment: str = "align*"
    compiler: str = "latex"
    color: Color = Color(0, 0, 0, 1)
    svg_scale: float = 1.0

    def __init__(
        self,
        tex: str,
        preamble: str = _DEFAULT_PREAMBLE,
        environment: str = "align*",
        compiler: str = "latex",
        color: Color = Color(0, 0, 0, 1),
        svg_scale: float = 1.0,
    ):
        self.init_from_fields(
            tex=tex,
            preamble=preamble,
            environment=environment,
            compiler=compiler,
            color=color,
            svg_scale=svg_scale,
        )

    def setup(self) -> None:
        self._environment = self.environment
        self._raw_tex = self.tex
        tex = f"\\begin{{{self.environment}}}\n{self.tex}\n\\end{{{self.environment}}}"

        self.set_child(
            Tex(
                tex=tex,
                preamble=self.preamble,
                compiler=self.compiler,
                svg_scale=self.svg_scale,
                color=self.color,
            )
        )


# Also adapted from github.com/ManimCommunity/manim under MIT License.
class Brace(DrawableWithChild):
    """A LaTeX style brace.

    Args:
        target_width: The width of the brace.
        target_height: The height of the brace.
        sharpness: The sharpness of the brace.
        color: The color of the brace.
    """

    target_width: float
    target_height: float = 15
    sharpness: float = 2.0
    color: Color = Colors.BLACK

    def __init__(
        self,
        target_width: float,
        target_height: float = 15,
        sharpness: float = 2.0,
        color: Color = Colors.BLACK,
    ):
        self.init_from_fields(
            target_width=target_width,
            target_height=target_height,
            sharpness=sharpness,
            color=color,
        )

    def setup(self):
        path_string_template = (
            "m0.01216 0c-0.01152 0-0.01216 6.103e-4 -0.01216 0.01311v0.007762c0.06776 "
            "0.122 0.1799 0.1455 0.2307 0.1455h{0}c0.03046 3.899e-4 0.07964 0.00449 "
            "0.1246 0.02636 0.0537 0.02695 0.07418 0.05816 0.08648 0.07769 0.001562 "
            "0.002538 0.004539 0.002563 0.01098 0.002563 0.006444-2e-8 0.009421-2.47e-"
            "5 0.01098-0.002563 0.0123-0.01953 0.03278-0.05074 0.08648-0.07769 0.04491"
            "-0.02187 0.09409-0.02597 0.1246-0.02636h{0}c0.05077 0 0.1629-0.02346 "
            "0.2307-0.1455v-0.007762c-1.78e-6 -0.0125-6.365e-4 -0.01311-0.01216-0.0131"
            "1-0.006444-3.919e-8 -0.009348 2.448e-5 -0.01091 0.002563-0.0123 0.01953-"
            "0.03278 0.05074-0.08648 0.07769-0.04491 0.02187-0.09416 0.02597-0.1246 "
            "0.02636h{1}c-0.04786 0-0.1502 0.02094-0.2185 0.1256-0.06833-0.1046-0.1706"
            "-0.1256-0.2185-0.1256h{1}c-0.03046-3.899e-4 -0.07972-0.004491-0.1246-0.02"
            "636-0.0537-0.02695-0.07418-0.05816-0.08648-0.07769-0.001562-0.002538-"
            "0.004467-0.002563-0.01091-0.002563z"
        )
        default_min_width = 0.90552
        default_height = 0.272985

        y_scale = self.target_height / default_height
        target_width_scaled = self.target_width / y_scale

        linear_section_length = max(
            0,
            (target_width_scaled / 2 * self.sharpness - default_min_width) / 2,
        )
        path = SVGPath(
            path_string_template.format(
                linear_section_length,
                -linear_section_length,
            ),
            fill_color=self.color,
        )

        x_scale = self.target_width / path.bounds.width
        y_scale = self.target_height / path.bounds.height
        path = path.scale(x_scale, y_scale)

        self.set_child(path)
