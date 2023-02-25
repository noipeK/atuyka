"""Run setuptools."""
import pathlib

from setuptools import find_packages, setup

setup(
    name="atuyka",
    version="0.0.1",
    description="Sea string.",
    url="https://github.com/noipeK/atuyka",
    packages=find_packages(exclude=["tests.*"]),
    include_package_data=True,
    package_data={"atuyka": ["py.typed"]},
    requires=["aiohttp", "pydantic", "fastapi"],
    extras_require={
        "pixiv": ["pixivpy_async"],
    },
    long_description=pathlib.Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    license="MIT",
)
