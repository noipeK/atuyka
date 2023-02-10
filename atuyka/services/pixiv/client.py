"""Pixiv client."""
import asyncio
import typing

import pixivpy_async as pixivpy
import pydantic
import typing_extensions

from . import models

# https://github.com/Mikubill/pixivpy-async

__all__ = ["Pixiv"]


class Pixiv:
    """Pixiv client."""

    token: str | None
    client: pixivpy.PixivClient
    api: pixivpy.AppPixivAPI

    def __init__(
        self,
        token: str | None,
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
        user: int,
        restrict: str = "public",
        filter: str = "for_ios",
        max_bookmark_id: int | None = None,
        tag: str | None = None,
    ) -> models.PixivPaginatedResource[models.PixivIllust]:
        """Get user bookmarks."""
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
        user: int,
        type: str = "illust",
        filter: str = "for_ios",
        offset: int | None = None,
        req_auth: bool = True,
    ) -> models.PixivPaginatedResource[models.PixivIllust]:
        """Get user illusts."""
        data = await self.api.user_illusts(  # pyright: reportUnknownVariableType=false
            user,
            type=type,
            filter=filter,
            offset=offset,  # pyright: ignore
            req_auth=req_auth,
        )

        return pydantic.parse_obj_as(models.PixivPaginatedResource[models.PixivIllust], data)
