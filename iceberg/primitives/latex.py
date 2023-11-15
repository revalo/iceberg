"""Latex rendering adapted from
https://github.com/ManimCommunity/manim
"""

from absl import logging

import os
import re
import shutil
from iceberg.animation.animatable import AnimatableSequence

from iceberg.primitives.layout import Transform

from iceberg.utils import temp_filename, temp_directory
from iceberg import DrawableWithChild, Bounds, Color
from iceberg.core import Bounds
from iceberg.primitives.svg import SVG
from iceberg.animation import Animatable

from dataclasses import dataclass


class LatexError(Exception):
    pass


def create_tex_svg(full_tex: str, svg_file: str, compiler: str):
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
        create_tex_svg(full_tex, svg_file, compiler)
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
    tex: str
    preamble: str = _DEFAULT_PREAMBLE
    compiler: str = "latex"
    svg_scale: float = 1.0
    color: Color = Color(0, 0, 0, 1)

    def setup(self) -> None:
        svg_filename = tex_content_to_svg_file(self.tex, self.preamble, self.compiler)
        self._svg = SVG(svg_filename, color=self.color)
        self.set_scene(Transform(self._svg, scale=(self.svg_scale, self.svg_scale)))


class MathTex(Tex):
    def __init__(
        self,
        tex: str,
        preamble: str = _DEFAULT_PREAMBLE,
        environment: str = "align*",
        compiler: str = "latex",
        color: Color = Color(0, 0, 0, 1),
        scale: float = 1.0,
    ) -> None:
        self._environment = environment
        self._raw_tex = tex
        tex = f"\\begin{{{environment}}}\n{tex}\n\\end{{{environment}}}"
        super().__init__(tex, preamble, compiler, scale, color)

    @property
    def animatables(self) -> AnimatableSequence:
        return [self.svg_scale, self.color]

    def copy_with_animatables(self, animatables: AnimatableSequence):
        svg_scale, color = animatables

        return MathTex(
            self._raw_tex,
            self.preamble,
            self._environment,
            self.compiler,
            color,
            svg_scale,
        )
