"""Pixiv client."""
import asyncio
import typing
import urllib.parse

import pixivpy_async as pixivpy
import pydantic
import typing_extensions

from atuyka.services import base

from . import models

# https://github.com/Mikubill/pixivpy-async

__all__ = ["Pixiv"]


class Pixiv(base.ServiceClient):
    """Pixiv client."""

    token: str | None
    my_id: int | None

    client: pixivpy.PixivClient
    api: pixivpy.AppPixivAPI

    def __init__(
        self,
        token: str | None,
        my_id: int | None = None,
        language: str = "en",
        *,
        limit: int = 30,
        timeout: int = 10,
        env: bool = False,
        internal: bool = False,
        proxy: str | None = None,
        bypass: bool = False,
    ) -> None:
        self.token = token
        self.my_id = my_id

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

    async def __aenter__(self) -> typing_extensions.Self:
        await self.start()
        return self

    async def __aexit__(self, *exc: typing.Any) -> None:
        await self.close()

    async def get_user_bookmarks(
        self,
        user: int | None = None,
        restrict: str = "public",
        filter: str = "for_ios",
        max_bookmark_id: int | None = None,
        tag: str | None = None,
    ) -> models.PixivPaginatedResource[models.PixivIllust]:
        """Get user bookmarks."""
        user = user or self.my_id
        assert user

        data = await self.api.user_bookmarks_illust(
            user,
            restrict=restrict,
            filter=filter,
            max_bookmark_id=max_bookmark_id,  # pyright: ignore
            tag=tag,  # pyright: ignore
        )

        return pydantic.parse_obj_as(models.PixivPaginatedResource[models.PixivIllust], data)

    async def get_user_illusts(
        self,
        user: int | None = None,
        type: str = "illust",
        filter: str = "for_ios",
        offset: int | None = None,
        req_auth: bool = True,
    ) -> models.PixivPaginatedResource[models.PixivIllust]:
        """Get user illusts."""
        user = user or self.my_id
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

    async def get_recommended_posts(self) -> typing.NoReturn:
        """Get recommended posts."""
        raise NotImplementedError

    async def get_following_posts(self) -> typing.NoReturn:
        """Get posts made by followed users."""
        raise NotImplementedError

    async def get_liked_posts(
        self,
        user: int | None = None,
        *,
        max_bookmark_id: int | None = None,
    ) -> base.models.Page[base.models.Post]:
        """Get bookmarked illusts.

        Parameters
        ----------
        user : int
            ID of the user. The authenticated user by default.
        """
        illusts = await self.get_user_bookmarks(user, max_bookmark_id=max_bookmark_id)
        posts = [illust.to_universal() for illust in illusts.illusts]

        if illusts.next_url:
            parsed = urllib.parse.urlparse(illusts.next_url)
            query = dict(urllib.parse.parse_qsl(parsed.query))
            next_query = dict(max_bookmark_id=int(query["max_bookmark_id"]))
        else:
            next_query = None

        page = base.models.Page(items=posts, next=next_query)
        return page

    async def get_author_posts(self) -> typing.NoReturn:
        """Get posts made by an author."""
        raise NotImplementedError

    async def search_posts(self) -> typing.NoReturn:
        """Search posts."""
        raise NotImplementedError

    async def search_authors(self) -> typing.NoReturn:
        """Search authors."""
        raise NotImplementedError
