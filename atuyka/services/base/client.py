"""Base client."""
from __future__ import annotations

import abc
import collections.abc
import dataclasses
import importlib
import importlib.machinery
import importlib.util
import pkgutil
import types
import typing
import warnings

import typing_extensions

import atuyka.errors
import atuyka.utility

from . import models

__all__ = ["ServiceClient", "load_services"]

T = typing.TypeVar("T")


def load_services(
    include: collections.abc.Collection[str] | None = None,
    exclude: collections.abc.Collection[str] | None = None,
) -> typing.Sequence[types.ModuleType]:
    """Load services by importing them."""
    path = (__file__.rsplit("/", 2)[0],)

    imported: list[types.ModuleType] = []
    for _, module_name, _ in pkgutil.iter_modules(path):
        if include and module_name not in include:
            continue
        if exclude and module_name in exclude:
            continue

        try:
            module = importlib.import_module("atuyka.services." + module_name)
        except BaseException as e:  # noqa: BLE001  # bare except
            warnings.warn(f"Failed to import {module_name}: {e}", stacklevel=2)
        else:
            imported.append(module)

    return imported


@dataclasses.dataclass
class ServiceClientConfig:
    """Configuration for a service client."""

    slug: str
    """Service slug."""
    name: str
    """Service name."""
    url: str | None = None
    """Service URL."""
    alt_url: str | None = None
    """Alternative frontend URL."""
    requires_authorization: bool = False
    """Whether the service requires authorization."""
    proxy_service: str | None = None
    """Proxy service used for the API."""

    @property
    def detailed_name(self) -> str:
        """Get detailed name."""
        if self.proxy_service:
            return f"{self.name} ({self.proxy_service})"

        return self.name


class ServiceClientMeta(abc.ABCMeta):
    """Metaclass for service clients."""

    config: ServiceClientConfig

    def __init__(  # pyright: reportInconsistentConstructor=false
        cls,
        clsname: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        *,
        slug: str | None = None,
        name: str | None = None,
        url: str | None = None,
        alt_url: str | None = None,
        auth: bool = False,
        proxy: str | None = None,
        **kwargs: object,
    ) -> None:
        if slug:
            cls.config = ServiceClientConfig(
                slug=slug,
                name=name or slug.replace("_", " ").title(),
                url=url,
                alt_url=alt_url,
                requires_authorization=auth,
                proxy_service=proxy,
            )

        super().__init__(clsname, bases, namespace)

    @property
    def _is_available(cls) -> bool:
        return hasattr(cls, "config")

    def __get_subclasses__(cls, load: bool = False, available: bool = True) -> list[type[ServiceClient]]:
        """Get subclasses of this client class."""
        subclasses = [c for c in cls.__subclasses__() if c._is_available or not available]
        if not subclasses and load:
            load_services()
            return cls.__get_subclasses__(available=available)

        return subclasses  # pyright: ignore # metaclass

    @property
    def available_services(cls) -> dict[str, type[ServiceClient]]:
        """Get subclasses."""
        services = {c.config.slug: c for c in cls.__get_subclasses__()}
        if not services:
            raise RuntimeError("No services loaded.")

        return services

    def create(
        cls: type[ServiceClient],  # pyright: ignore # metaclass
        service: str,
        token: str | None = None,
    ) -> ServiceClient:
        """Create a client."""
        client_cls = cls.available_services.get(service)

        if client_cls is None:
            raise atuyka.errors.InvalidServiceError(service, list(cls.available_services))

        if client_cls.config.requires_authorization and token is None:
            raise atuyka.errors.MissingTokenError(service)

        return client_cls(token)


class ServiceClient(abc.ABC, metaclass=ServiceClientMeta):
    """Base service client."""

    @abc.abstractmethod
    def __init__(self, token: str | None = ...) -> None:
        ...

    def __init_subclass__(cls, **kwargs: object) -> None:
        return super().__init_subclass__()

    async def start(self) -> None:
        """Start the client."""

    async def close(self) -> None:
        """Close the client."""

    async def __aenter__(self) -> typing_extensions.Self:
        await self.start()
        return self

    async def __aexit__(self, *exc: typing.Any) -> None:
        await self.close()

    @property
    @abc.abstractmethod
    def my_user_id(self) -> str | None:
        """Logged-in user's ID."""

    @abc.abstractmethod
    async def get_user(self, user: str | None = ..., /, **kwargs: object) -> models.User:
        """Get user."""

    @abc.abstractmethod
    async def get_liked_posts(self, user: str | None = ..., /, **kwargs: object) -> models.Page[models.Post]:
        """Get liked posts."""

    @abc.abstractmethod
    async def get_following(self, user: str | None = ..., /, **kwargs: object) -> models.Page[models.User]:
        """Get following users."""

    @abc.abstractmethod
    async def get_followers(self, user: str | None = ..., /, **kwargs: object) -> models.Page[models.User]:
        """Get followers."""

    @abc.abstractmethod
    async def get_posts(self, user: str | None = ..., /, **kwargs: object) -> models.Page[models.Post]:
        """Get posts made by a user."""

    @abc.abstractmethod
    async def get_post(self, user: str | None, post: str, /, **kwargs: object) -> models.Post:
        """Get a post."""

    @abc.abstractmethod
    async def get_comments(
        self,
        user: str | None,
        post: str,
        comment: str | None = ...,
        /,
        **kwargs: object,
    ) -> models.Page[models.Comment]:
        """Get comments."""

    @abc.abstractmethod
    async def get_similar_posts(self, user: str | None, post: str, /, **kwargs: object) -> models.Page[models.Post]:
        """Get similar posts."""

    @abc.abstractmethod
    async def get_following_feed(self, **kwargs: object) -> models.Page[models.Post]:
        """Get posts made by followed users."""

    @abc.abstractmethod
    async def get_recommended_feed(self, **kwargs: object) -> models.Page[models.Post]:
        """Get recommended posts."""

    @abc.abstractmethod
    async def search_posts(self, query: str | None = ..., /, **kwargs: object) -> models.Page[models.Post]:
        """Search posts."""

    @abc.abstractmethod
    async def search_users(self, query: str | None = ..., /, **kwargs: object) -> models.Page[models.User]:
        """Search users."""

    @abc.abstractmethod
    def _proxy(self, url: str, /, **kwargs: object) -> atuyka.utility.ProxyContextType:
        """Proxy a url.

        Returns a stream and headers.
        """

    def proxy(self, url: str, /, **kwargs: object) -> atuyka.utility.ProxyStream:
        """Proxy a url."""
        return atuyka.utility.ProxyStream(self._proxy(url, **kwargs))

    async def download(self, url: str, /, **kwargs: object) -> bytes:
        """Download a url."""
        async with self.proxy(url, **kwargs) as stream:
            return await stream.read()
