"""Pixiv client."""
import asyncio
import typing

import pixivpy_async as pixivpy
import pydantic

import atuyka.errors
from atuyka.services import base

from . import models

# https://github.com/Mikubill/pixivpy-async

__all__ = ["Pixiv"]


class Pixiv(base.ServiceClient, service="pixiv", url="pixiv.net", auth=True):
    """Pixiv client."""

    token: str | None

    client: pixivpy.PixivClient
    api: pixivpy.AppPixivAPI

    def __init__(
        self,
        token: str | None,
        *,
        language: str = "en",
        limit: int = 30,
        timeout: int = 10,
        env: bool = False,
        internal: bool = False,
        proxy: str | None = None,
        bypass: bool = False,
    ) -> None:
        self.token = token

        self.client = pixivpy.PixivClient(
            limit=limit,
            timeout=timeout,
            env=env,
            internal=internal,
            proxy=proxy,
            bypass=bypass,
        )
        self.api = pixivpy.AppPixivAPI(client=self.client.client)
        self.api.set_accept_language(language)

    async def start(self) -> None:
        """Start the client."""
        if self.token is None:
            await self.api.login_web()
            return

        await self.api.login(refresh_token=self.token)  # pyright: reportUnknownMemberType=false

    async def close(self) -> None:
        """Close the client."""
        await asyncio.sleep(0)
        await self.client.client.close()

    @property
    def user_id(self) -> int:
        """Authenticated user ID."""
        return self.api.user_id  # pyright: reportUnknownMemberType=false

    def _parse_user(self, user: str | int | None) -> int:
        """Parse user ID."""
        if user is None:
            return self.user_id

        if isinstance(user, int) or user.isdigit():
            return int(user)

        raise atuyka.errors.InvalidIDError("pixiv", user, "user")

    async def get_user_details(self, user: int | None = None) -> models.PixivUserDetails:
        """Get a pixiv user."""
        data = await self.api.user_detail(user or self.user_id)
        return pydantic.parse_obj_as(models.PixivUserDetails, data)

    async def get_user_bookmarks(
        self,
        user: int | None = None,
        *,
        restrict: str = "public",
        max_bookmark_id: int | None = None,
        tag: str | None = None,
    ) -> models.PixivPaginatedBookmarks:
        """Get user bookmarks."""
        data = await self.api.user_bookmarks_illust(
            user or self.user_id,
            restrict=restrict,
            max_bookmark_id=max_bookmark_id,  # pyright: ignore
            tag=tag,  # pyright: ignore
        )

        parsed = pydantic.parse_obj_as(models.PixivPaginatedBookmarks, data)
        return parsed

    async def get_user_following(
        self,
        user: int | None = None,
        *,
        restrict: str = "public",
        offset: int | None = None,
    ) -> models.PixivPaginatedUserPreviews:
        """Get user following."""
        data = await self.api.user_following(
            user or self.user_id,
            restrict=restrict,
            offset=offset,  # pyright: ignore
        )

        parsed = pydantic.parse_obj_as(models.PixivPaginatedUserPreviews, data)
        return parsed

    async def get_user_followers(
        self,
        user: int | None = None,
        *,
        restrict: str = "public",
        offset: int | None = None,
    ) -> models.PixivPaginatedUserPreviews:
        """Get user followers."""
        data = await self.api.user_follower(
            user or self.user_id,
            offset=offset,  # pyright: ignore
        )

        parsed = pydantic.parse_obj_as(models.PixivPaginatedUserPreviews, data)
        return parsed

    async def get_user_illusts(
        self,
        user: int | None = None,
        *,
        offset: int | None = None,
    ) -> models.PixivPaginatedIllusts:
        """Get user illusts."""
        data = await self.api.user_illusts(  # pyright: reportUnknownVariableType=false
            user or self.user_id,
            type="illust",
            offset=offset,  # pyright: ignore
        )

        return pydantic.parse_obj_as(models.PixivPaginatedIllusts, data)

    async def get_illust_details(self, illust_id: int) -> models.PixivIllust:
        """Get an illust."""
        data = await self.api.illust_detail(illust_id)
        return pydantic.parse_obj_as(models.PixivIllust, data.illust)

    # ------------------------------------------------------------
    # UNIVERSAL:

    async def get_user(self, user: str | None = None, **kwargs: object) -> base.models.User:
        """Get user."""
        details = await self.get_user_details(self._parse_user(user))
        return details.to_universal()

    async def get_liked_posts(
        self,
        user: str | None = None,
        *,
        max_bookmark_id: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get bookmarked illusts."""
        data = await self.get_user_bookmarks(self._parse_user(user), max_bookmark_id=max_bookmark_id)
        return data.to_universal()

    async def get_following(
        self,
        user: str | None = None,
        *,
        restrict: str = "public",
        offset: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.User]:
        """Get following users."""
        data = await self.get_user_following(self._parse_user(user), restrict=restrict, offset=offset)
        return data.to_universal()

    async def get_followers(
        self,
        user: str | None = None,
        *,
        restrict: str = "public",
        offset: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.User]:
        """Get followers."""
        data = await self.get_user_followers(self._parse_user(user), restrict=restrict, offset=offset)
        return data.to_universal()

    async def get_posts(
        self,
        user: str | None = None,
        *,
        offset: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get posts made by a user."""
        data = await self.get_user_illusts(self._parse_user(user), offset=offset)
        return data.to_universal()

    async def get_post(self, user: str, post: str, **kwargs: object) -> base.models.Post:
        """Get an illust."""
        illust = await self.get_illust_details(int(post))
        return illust.to_universal()

    async def get_similar_posts(self, user: str, post: str, **kwargs: object) -> typing.NoReturn:
        """Get similar posts."""
        raise NotImplementedError

    async def get_following_feed(self, user: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Get posts made by followed users."""
        raise NotImplementedError

    async def get_recommended_feed(self, user: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Get recommended posts."""
        raise NotImplementedError

    async def search_posts(self, query: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Search posts."""
        raise NotImplementedError

    async def search_users(self, query: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Search users."""
        raise NotImplementedError
