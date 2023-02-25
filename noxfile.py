"""Nox file."""
from __future__ import annotations

import logging
import pathlib
import typing

import nox

nox.options.sessions = ["reformat", "lint", "type-check", "verify-types", "test", "prettier"]
nox.options.reuse_existing_virtualenvs = True
PACKAGE = "atuyka"
GENERAL_TARGETS = ["./atuyka", "./tests", "./noxfile.py", "docs/conf.py"]
PRETTIER_TARGETS = ["*.md", "docs/*.md", "docs/**/*.md", "*.toml"]
PYRIGHT_ENV = {"PYRIGHT_PYTHON_FORCE_VERSION": "latest"}

LOGGER = logging.getLogger("nox")


def isverbose() -> bool:
    """Whether the verbose flag is set."""
    return LOGGER.getEffectiveLevel() == logging.DEBUG - 1


def verbose_args() -> typing.Sequence[str]:
    """Return --verbose if the verbose flag is set."""
    return ["--verbose"] if isverbose() else []


def install_requirements(session: nox.Session, *requirements: str, literal: bool = False) -> None:
    """Install requirements."""
    if not literal and all(requirement.isalpha() for requirement in requirements):
        files = ["requirements.txt"]
        files += [f"./dev-requirements/{requirement}.txt" for requirement in requirements]
        requirements = tuple(arg for file in files for arg in ("-r", file))

    session.install("--upgrade", "pip", *requirements, silent=not isverbose())


@nox.session()
def docs(session: nox.Session) -> None:
    """Generate docs for this project using sphinx."""
    install_requirements(session, "docs")

    output = "docs/_build/html"

    if "--autobuild" in session.posargs:
        # sphinx-autobuild absolutely cannot do relative paths
        session.run(
            "sphinx-autobuild",
            "docs",
            output,
            "--watch",
            pathlib.Path(PACKAGE).resolve().as_posix(),
            "--ignore",
            pathlib.Path("docs/reference").resolve().as_posix(),
            "--ignore",
            "*.tmp",
        )
    else:
        session.run("sphinx-build", "-M", "dirhtml", "docs", output)


@nox.session()
def lint(session: nox.Session) -> None:
    """Run this project's modules against ruff."""
    install_requirements(session, "lint")
    session.run("ruff", "check", *GENERAL_TARGETS, "--fix", *verbose_args())
    session.run("python", "-m", "slotscheck", "-m", PACKAGE, *verbose_args())


@nox.session()
def reformat(session: nox.Session) -> None:
    """Reformat this project's modules to fit the standard style."""
    install_requirements(session, "reformat")
    session.run("black", *GENERAL_TARGETS, *verbose_args())

    session.log("sort-all")
    LOGGER.disabled = True
    session.run("sort-all", *map(str, pathlib.Path(PACKAGE).glob("**/*.py")), success_codes=[0, 1])
    LOGGER.disabled = False


@nox.session(name="test", python=["3.10", "3.11"])
def test(session: nox.Session) -> None:
    """Run this project's tests using pytest."""
    install_requirements(session, "pytest")

    args: typing.Sequence[str] = []

    if isverbose():
        args += ["-vv", "--showlocals"]

    if "--no-cov" in session.posargs:
        session.posargs.remove("--no-cov")
    else:
        args += [
            "--cov",
            PACKAGE,
            "--cov-report",
            "term",
            "--cov-report",
            "html:coverage_html",
            "--cov-report",
            "xml",
        ]

    session.run(
        "python",
        "-m",
        "pytest",
        "-r",
        "sfE",
        *verbose_args(),
        *args,
        *session.posargs,
    )

    if "--cov" in args:
        session.log(f"HTML coverage report: {pathlib.Path('coverage_html/index.html').resolve()}")


@nox.session(name="type-check")
def type_check(session: nox.Session) -> None:
    """Statically analyse and veirfy this project using pyright and mypy."""
    install_requirements(session, "typecheck")
    session.run("pyright", PACKAGE, *verbose_args(), env=PYRIGHT_ENV)


@nox.session(name="verify-types")
def verify_types(session: nox.Session) -> None:
    """Verify the "type completeness" of types exported by the library using pyright."""
    install_requirements(session, ".", "--force-reinstall", "--no-deps")
    install_requirements(session, "typecheck")

    session.run("pyright", "--verifytypes", PACKAGE, "--ignoreexternal", *verbose_args(), env=PYRIGHT_ENV)


def _try_install_prettier(session: nox.Session) -> bool:
    """Try to install prettier. Return False if failed."""
    try:
        session.run("npm", "install", "prettier", "prettier-plugin-toml", "--global", external=True)
    except Exception as exception:  # noqa: BLE001: Nox throws a bare Exception
        if str(exception) != "Program npm not found":
            raise
    else:
        return True

    return False


@nox.session(python=False)
def prettier(session: nox.Session) -> None:
    """Run prettier on markdown files."""
    if not _try_install_prettier(session):
        session.skip("Prettier not installed")

    session.run("prettier", "-w", "*.md", "docs/*.md", "docs/**/*.md", "*.yml", "*.toml", external=True)
