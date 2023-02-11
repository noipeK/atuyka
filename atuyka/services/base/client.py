"""Base client."""
import abc
import collections.abc
import functools
import inspect
import re
import typing

import typing_extensions

from . import models

__all__ = ["ServiceClient", "endpoint"]

P = typing_extensions.ParamSpec("P")
T = typing.TypeVar("T")

CallableT = typing.TypeVar("CallableT", bound=collections.abc.Callable[..., object])


class ServiceEndpointParam:
    """Service endpoint parameter."""

    def __init__(
        self,
        name: str,
        description: str,
        type: type[object],
        required: bool,
    ) -> None:
        self.name = name
        self.description = description
        self.type = type
        self.required = required


class ServiceEndpoint(typing.Generic[P, T]):
    """Service endpoint with metadata."""

    def __init__(
        self,
        callback: collections.abc.Callable[P, T],
        name: str,
        description: str,
        params: list[ServiceEndpointParam],
    ) -> None:
        self.callback = callback
        self.name = name
        self.description = description
        self.params = params

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.callback(*args, **kwargs)


def endpoint(callback: CallableT) -> CallableT:
    """Create a service endpoint."""
    # get_recommended_posts -> recommended posts
    name = callback.__name__.replace("get_", "").replace("_", " ")

    docstring = inspect.cleandoc(callback.__doc__ or "")
    signature = inspect.signature(callback)

    description = docstring.splitlines()[0]
    params: list[ServiceEndpointParam] = []

    match = re.search(r"Args\s*:\s*\n((?:.|\n)*)(\n{2,})?", docstring)
    param_docs = match[1] if match else ""

    for match in re.finditer(r"\s*(\w+)\s*(?:\(.+?\))?:\s+(.+)", param_docs):
        name, desc = match[1], match[2]
        desc = " ".join(x.strip() for x in desc.splitlines())
        sig_param = signature.parameters[name]

        param = ServiceEndpointParam(name, desc, sig_param.annotation, sig_param.default is inspect.Parameter.empty)
        params.append(param)

    endpoint = ServiceEndpoint(callback, name, description, params)
    return typing.cast(CallableT, functools.update_wrapper(endpoint, callback))


class ServiceClient(abc.ABC):
    """Base service client."""

    @abc.abstractmethod
    async def get_recommended_posts(self) -> models.Page[models.Post]:
        """Get recommended posts."""

    @abc.abstractmethod
    async def get_following_posts(self) -> models.Page[models.Post]:
        """Get posts made by followed users."""

    @abc.abstractmethod
    async def get_liked_posts(self) -> models.Page[models.Post]:
        """Get liked posts."""

    @abc.abstractmethod
    async def get_author_posts(self) -> models.Page[models.Post]:
        """Get posts made by an author."""

    @abc.abstractmethod
    async def search_posts(self) -> models.Page[models.Post]:
        """Search posts."""

    @abc.abstractmethod
    async def search_authors(self) -> models.Page[models.User]:
        """Search authors."""
