"""Run setuptools."""
from setuptools import find_packages, setup

setup(
    name="{{repository_name}}",
    version="0.0.1",
    description="{{repository_description}}",
    url="https://github.com/{{repository_owner}}/{{repository_name}}",
    packages=find_packages(exclude=["tests.*"]),
    include_package_data=True,
    package_data={"{{repository_name}}": ["py.typed"]},
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
)
