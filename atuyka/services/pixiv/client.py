"""Pixiv client."""
import asyncio
import typing
import urllib.parse

import pixivpy_async as pixivpy
import pydantic

import atuyka.errors
from atuyka.services import base

from . import models

# https://github.com/Mikubill/pixivpy-async

__all__ = ["Pixiv"]


class Pixiv(base.ServiceClient):
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

    async def get_user_bookmarks(
        self,
        user: int | None = None,
        restrict: str = "public",
        filter: str = "for_ios",
        max_bookmark_id: int | None = None,
        tag: str | None = None,
    ) -> models.PixivPaginatedResource[models.PixivIllust]:
        """Get user bookmarks."""
        user = user or self.user_id
        assert user

        data = await self.api.user_bookmarks_illust(
            user,
            restrict=restrict,
            filter=filter,
            max_bookmark_id=max_bookmark_id,  # pyright: ignore
            tag=tag,  # pyright: ignore
        )

        parsed = pydantic.parse_obj_as(models.PixivPaginatedResource[models.PixivIllust], data)
        return parsed

    async def get_user_illusts(
        self,
        user: int | None = None,
        type: str = "illust",
        filter: str = "for_ios",
        offset: int | None = None,
        req_auth: bool = True,
    ) -> models.PixivPaginatedResource[models.PixivIllust]:
        """Get user illusts."""
        user = user or self.user_id
        assert user

        data = await self.api.user_illusts(  # pyright: reportUnknownVariableType=false
            user,
            type=type,
            filter=filter,
            offset=offset,  # pyright: ignore
            req_auth=req_auth,
        )

        return pydantic.parse_obj_as(models.PixivPaginatedResource[models.PixivIllust], data)

    # ------------------------------------------------------------
    # UNIVERSAL:

    async def get_user(self, user: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Get user."""
        raise NotImplementedError

    async def get_liked_posts(
        self,
        user: str | None = None,
        *,
        max_bookmark_id: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get bookmarked illusts."""
        if isinstance(user, str) and not user.isdigit():
            raise atuyka.errors.InvalidIDError("pixiv", user, "user")

        user_id = int(user) if user else self.user_id
        illusts = await self.get_user_bookmarks(user_id, max_bookmark_id=max_bookmark_id)
        posts = [illust.to_universal() for illust in illusts.illusts]

        if illusts.next_url:
            parsed = urllib.parse.urlparse(illusts.next_url)
            query = dict(urllib.parse.parse_qsl(parsed.query))
            next_query = dict(max_bookmark_id=int(query["max_bookmark_id"]))
        else:
            next_query = None

        page = base.models.Page(items=posts, next=next_query)
        return page

    async def get_following(self, user: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Get following users."""
        raise NotImplementedError

    async def get_followers(self, user: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Get followers."""
        raise NotImplementedError

    async def get_posts(self, user: str, **kwargs: object) -> typing.NoReturn:
        """Get posts made by a user."""
        raise NotImplementedError

    async def get_post(self, user: str, post: str, **kwargs: object) -> typing.NoReturn:
        """Get a post."""
        raise NotImplementedError

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
