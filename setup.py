import re

from setuptools import setup, find_packages

with open("iceberg/__init__.py", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="iceberg-dsl",
    version=version,
    install_requires=[
        "absl-py>=1.0.0",
        "glfw==2.5.1",
        "numpy>=1.21.0",
        "skia-python==87.5",
        "tqdm>=4.62.3",
        "av>=11.0.0",
        "Pillow>=10.1.0",
    ],
)
