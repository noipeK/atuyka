"""Mock package to install the dev requirements."""
import pathlib
import typing

import setuptools


def parse_requirements_file(path: pathlib.Path) -> typing.List[str]:
    """Parse a requirements file into a list of requirements."""
    with open(path) as fp:
        raw_dependencies = fp.readlines()

    dependencies: typing.List[str] = []
    for dependency in raw_dependencies:
        comment_index = dependency.find("#")
        if comment_index == 0:
            continue

        if comment_index != -1:  # Remove any comments after the requirement
            dependency = dependency[:comment_index]

        if d := dependency.strip():
            dependencies.append(d)

    return dependencies


def get_normal_requirements(directory: pathlib.Path) -> typing.List[str]:
    """Get all normal requirements in a dev requirements directory."""
    return parse_requirements_file(directory / ".." / "requirements.txt")


def get_extras(directory: pathlib.Path) -> typing.Dict[str, typing.List[str]]:
    """Get all extras in a dev requirements directory."""
    all_extras: typing.Set[str] = set()
    extras: typing.Dict[str, typing.List[str]] = {}

    for path in directory.glob("*.txt"):
        name = path.name.split(".")[0]

        requirements = parse_requirements_file(path)

        all_extras = all_extras.union(requirements)
        extras[name] = requirements

    extras["all"] = list(all_extras)

    return extras


dev_directory = pathlib.Path(__file__).parent
setuptools.setup(
    name="{{repository_name}}-dev",
    install_requires=get_normal_requirements(dev_directory) + ["nox"],
    extras_require=get_extras(dev_directory),
)
