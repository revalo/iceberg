"""Latex rendering adapted from
https://github.com/ManimCommunity/manim
"""

import os
import re
import shutil

from absl import logging

from iceberg import Color, DrawableWithChild
from iceberg.primitives.svg import SVG
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
