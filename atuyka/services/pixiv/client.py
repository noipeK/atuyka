"""Pixiv client."""
import asyncio
import collections.abc
import contextlib
import re
import typing

import aiohttp
import pixivpy_async as pixivpy
import pydantic

import atuyka.errors
import atuyka.utility
from atuyka.services import base

from . import models

# https://github.com/Mikubill/pixivpy-async

__all__ = ["Pixiv"]


class Pixiv(base.ServiceClient, slug="pixiv", url="pixiv.net", alt_url="pixiv.moe", auth=True):
    """Pixiv client."""

    # TODO: Encode with the token
    CACHED_TOKENS: atuyka.utility.Cache[str, dict[str, object]] = atuyka.utility.Cache()

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

        if self.token in self.CACHED_TOKENS:
            parts = self.CACHED_TOKENS[self.token]
            self.api.access_token = parts["access_token"]
            self.api.refresh_token = parts["refresh_token"]
            self.api.user_id = parts["user_id"]

            return

        await self.api.login(refresh_token=self.token)  # pyright: reportUnknownMemberType=false

        self.CACHED_TOKENS[self.token] = {
            "access_token": self.api.access_token,
            "refresh_token": self.api.refresh_token,
            "user_id": self.api.user_id,
        }

    async def close(self) -> None:
        """Close the client."""
        await asyncio.sleep(0)
        await self.client.client.close()

    @property
    def user_id(self) -> int:
        """Authenticated user ID."""
        return self.api.user_id  # pyright: reportUnknownMemberType=false

    @property
    def my_user_id(self) -> str | None:
        """Logged-in user's ID."""
        return str(self.user_id)

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
            offset=offset,  # pyright: ignore
        )

        return pydantic.parse_obj_as(models.PixivPaginatedIllusts, data)

    async def get_illust_details(self, illust_id: int) -> models.PixivIllust:
        """Get an illust."""
        data = await self.api.illust_detail(illust_id)
        return pydantic.parse_obj_as(models.PixivIllust, data.illust)

    async def get_illust_comments(
        self,
        illust_id: int,
        *,
        offset: int | None = None,
    ) -> models.PixivPaginatedComments:
        """Get illust comments."""
        data = await self.api.illust_comments(illust_id, offset=offset, include_total_comments=True)
        return pydantic.parse_obj_as(models.PixivPaginatedComments, data)

    async def get_related_illusts(
        self,
        illust_id: int,
        *,
        offset: int | None = None,
        seed_illust_ids: collections.abc.Collection[str] | None = None,
        viewed: collections.abc.Collection[str] | None = None,
    ) -> models.PixivPaginatedIllusts:
        """Get related illusts."""
        # self.api.illust_related does not support viewed, only seed_illust_ids
        # set_params does not support proper serialization of seed_illust_ids
        method, url = self.api.api.illust_related
        params: dict[str, str] = self.api.set_params(
            illust_id=illust_id,
            offset=offset,
            filter="for_ios",
            viewed=list(viewed) if viewed else None,
        )
        # NOTE: pyright bug, unknown return type requires cast
        id_params = typing.cast(
            "dict[str, str]",
            self.api.set_params(viewed=list(seed_illust_ids) if seed_illust_ids else None),
        )
        for key, param in id_params.items():
            params[key.replace("viewed", "seed_illust_ids")] = param

        data = await self.api.requests_(method=method, url=url, params=params)
        return pydantic.parse_obj_as(models.PixivPaginatedIllusts, data)

    async def get_following_illusts(
        self,
        *,
        restrict: str = "public",
        offset: int | None = None,
    ) -> models.PixivPaginatedIllusts:
        """Get following illusts."""
        data = await self.api.illust_follow(
            restrict=restrict,  # pyright: ignore
            offset=offset,  # pyright: ignore
        )
        return pydantic.parse_obj_as(models.PixivPaginatedIllusts, data)

    async def get_recommended_illusts(
        self,
        *,
        min_bookmark_id_for_recent_illust: int | None = None,
        max_bookmark_id_for_recommend: int | None = None,
        offset: int | None = None,
    ) -> models.PixivPaginatedIllusts:
        """Get recommended illusts."""
        data = await self.api.illust_recommended(
            min_bookmark_id_for_recent_illust=min_bookmark_id_for_recent_illust,  # pyright: ignore
            max_bookmark_id_for_recommend=max_bookmark_id_for_recommend,  # pyright: ignore
            offset=offset,  # pyright: ignore
        )
        return pydantic.parse_obj_as(models.PixivPaginatedIllusts, data)

    async def get_ranking_illusts(
        self,
        mode: str = "day",
        date: str | None = None,
        *,
        offset: int | None = None,
    ) -> models.PixivPaginatedIllusts:
        """Get ranking illusts."""
        data = await self.api.illust_ranking(
            mode=mode,
            date=date,  # pyright: ignore
            offset=offset,  # pyright: ignore
        )
        return pydantic.parse_obj_as(models.PixivPaginatedIllusts, data)

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
        offset: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.User]:
        """Get followers."""
        data = await self.get_user_followers(self._parse_user(user), offset=offset)
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

    async def get_post(self, user: str | None, post: str, **kwargs: object) -> base.models.Post:
        """Get an illust."""
        illust = await self.get_illust_details(int(post))
        return illust.to_universal()

    async def get_comments(
        self,
        user: str | None,
        post: str,
        comment: str | None = None,
        *,
        offset: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Comment]:
        """Get comments."""
        data = await self.get_illust_comments(int(post), offset=offset)
        return data.to_universal()

    async def get_similar_posts(
        self,
        user: str | None,
        post: str,
        *,
        offset: int | None = None,
        seed_illust_ids: str | None = None,
        viewed: str | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get similar posts."""
        data = await self.get_related_illusts(
            int(post),
            offset=offset,
            seed_illust_ids=seed_illust_ids.split(",") if seed_illust_ids else None,
            viewed=viewed.split(",") if viewed else None,
        )
        return data.to_universal()

    async def get_following_feed(
        self,
        *,
        restrict: str = "public",
        offset: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get posts made by followed users."""
        data = await self.get_following_illusts(restrict=restrict, offset=offset)
        return data.to_universal()

    async def get_recommended_feed(
        self,
        *,
        min_bookmark_id_for_recent_illust: int | None = None,
        max_bookmark_id_for_recommend: int | None = None,
        offset: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get recommended posts."""
        data = await self.get_recommended_illusts(
            min_bookmark_id_for_recent_illust=min_bookmark_id_for_recent_illust,
            max_bookmark_id_for_recommend=max_bookmark_id_for_recommend,
            offset=offset,
        )
        return data.to_universal()

    async def search_posts(self, query: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Search posts."""
        raise NotImplementedError

    async def search_users(self, query: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Search users."""
        raise NotImplementedError

    @contextlib.asynccontextmanager
    async def _proxy(
        self,
        url: str,
        /,
        headers: collections.abc.Mapping[str, str] | None = None,
        **kwargs: object,
    ) -> typing.AsyncIterator[atuyka.utility.ProxyEnteredContextType]:
        """Proxy a request."""
        # Copied from AppPixivAPI.download
        headers = dict(headers or {})
        headers["Referer"] = "https://app-api.pixiv.net/"

        async with aiohttp.ClientSession(auto_decompress=False) as session:
            async with session.get(url, **kwargs) as response:
                headers = dict(response.headers)
                headers["x-status-code"] = str(response.status)
                yield (response.content.iter_any(), headers)

    @classmethod
    def parse_connection_url(cls, url: str) -> base.models.Connection | None:
        """Parse connection URL."""
        match = re.match(r"https?://(?:www\.)?pixiv\.net/(?:en/)?(?:users|members)/(\d+)", url)
        if match:
            return base.models.Connection(service="pixiv", url=url, user=match[1])

        match = re.match(r"https?://(?:www\.)?pixiv\.net/(?:en/)?(?:artworks|illustrations)/(\d+)", url)
        if match:
            return base.models.Connection(service="pixiv", url=url, post=match[1])

        return None
