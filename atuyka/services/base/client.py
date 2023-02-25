"""Base client."""
import abc
import typing

import typing_extensions

from . import models

__all__ = ["ServiceClient"]


class ServiceClient(abc.ABC):
    """Base service client."""

    @abc.abstractmethod
    def __init__(self, token: str | None = ...) -> None:
        ...

    async def start(self) -> None:
        """Start the client."""

    async def close(self) -> None:
        """Close the client."""

    async def __aenter__(self) -> typing_extensions.Self:
        await self.start()
        return self

    async def __aexit__(self, *exc: typing.Any) -> None:
        await self.close()

    @classmethod
    def create(cls, service: str, token: str | None = None) -> typing_extensions.Self:
        """Create a client."""
        # TODO: Use metaclasses to register subclasses.
        subclasses = {c.__name__.lower(): c for c in cls.__subclasses__()}
        if service not in subclasses:
            raise ValueError(f"Service {service!r} not found: {', '.join(subclasses)!r}")

        return subclasses[service](token)

    @abc.abstractmethod
    async def get_user(self, user: str | None = ..., **kwargs: object) -> models.User:
        """Get user."""

    @abc.abstractmethod
    async def get_liked_posts(self, user: str | None = ..., **kwargs: object) -> models.Page[models.Post]:
        """Get liked posts."""

    @abc.abstractmethod
    async def get_following(self, user: str | None = ..., **kwargs: object) -> models.Page[models.User]:
        """Get following users."""

    @abc.abstractmethod
    async def get_followers(self, user: str | None = ..., **kwargs: object) -> models.Page[models.User]:
        """Get followers."""

    @abc.abstractmethod
    async def get_posts(self, user: str, **kwargs: object) -> models.Page[models.Post]:
        """Get posts made by a user."""

    @abc.abstractmethod
    async def get_post(self, user: str, post: str, **kwargs: object) -> models.Post:
        """Get a post."""

    @abc.abstractmethod
    async def get_similar_posts(self, user: str, post: str, **kwargs: object) -> models.Page[models.Post]:
        """Get similar posts."""

    @abc.abstractmethod
    async def get_following_feed(self, user: str | None = ..., **kwargs: object) -> models.Page[models.Post]:
        """Get posts made by followed users."""

    @abc.abstractmethod
    async def get_recommended_feed(self, user: str | None = ..., **kwargs: object) -> models.Page[models.Post]:
        """Get recommended posts."""

    @abc.abstractmethod
    async def search_posts(self, query: str | None = ..., **kwargs: object) -> models.Page[models.Post]:
        """Search posts."""

    @abc.abstractmethod
    async def search_users(self, query: str | None = ..., **kwargs: object) -> models.Page[models.User]:
        """Search users."""
