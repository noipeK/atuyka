"""Twitter front-end API client."""
import asyncio
import collections.abc
import re
import typing

import aiohttp
import pydantic

from . import models

UA = "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"
GUEST_AUTHORIZATION = (
    "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

__all__ = ["Twitter"]


class Twitter:
    """Twitter front-end API client."""

    auth_token: str | None
    ct0: str | None
    guest_token: str | None
    guest_authorization: str
    user_agent: str

    def __init__(
        self,
        token: str | None = None,
        ct0: str | None = None,
        guest_token: str | None = None,
        guest_authorization: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.auth_token = token
        self.ct0 = ct0
        self.guest_token = guest_token
        self.guest_authorization = guest_authorization or GUEST_AUTHORIZATION
        self.user_agent = user_agent or UA

    async def generate_guest_token(self) -> str:
        """Generate the token."""
        headers = {"User-Agent": self.user_agent, "Authorization": self.guest_authorization}
        async with aiohttp.request(
            "POST",
            "https://api.twitter.com/1.1/guest/activate.json",
            headers=headers,
        ) as response:
            data = await response.json()

        return data["guest_token"]

    async def generate_ct0(self) -> str:
        """Generate the ct0 token."""
        async with aiohttp.request("GET", "https://twitter.com/i/release_notes") as response:
            return response.cookies["ct0"].value

    async def generate_authenticity_token(self) -> str:
        """Generate the authenticity token."""
        async with aiohttp.request("GET", "https://twitter.com/account/begin_password_reset") as response:
            text = await response.text()

        match = re.search(r'"authenticity_token" value="(.*?)"', text)
        assert match
        return match[1]

    async def get_guest_headers(self) -> collections.abc.Mapping[str, str]:
        """Return the headers for the request."""
        if not self.guest_token:
            self.guest_token = await self.generate_guest_token()

        return {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Authorization": self.guest_authorization,
            "x-guest-token": self.guest_token,
        }

    async def get_authenticated_headers(self) -> collections.abc.Mapping[str, str]:
        """Return the authenticated headers for the request."""
        if not self.auth_token:
            raise ValueError("No auth token provided.")

        if not self.ct0:
            self.ct0 = await self.generate_ct0()

        return {
            "Origin": "https://twitter.com",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Authorization": GUEST_AUTHORIZATION,
            "Cookie": f"auth_token={self.auth_token}; ct0={self.ct0}",
            "x-csrf-token": self.ct0,
        }

    async def get_headers(self) -> collections.abc.Mapping[str, str]:
        """Return the headers for the request."""
        if self.auth_token:
            return await self.get_authenticated_headers()

        return await self.get_guest_headers()

    async def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: collections.abc.Mapping[str, str] | None = None,
        params: collections.abc.Mapping[str, str | int | None] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        """Make a request to the Twitter API."""
        if headers is None:
            headers = await self.get_headers()

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        async with aiohttp.request(method, url, headers=headers, **kwargs) as response:
            data = await response.json(content_type=None)

        if "error" in data:
            raise ValueError(data["error"])
        if "errors" in data:
            raise ValueError(data["errors"])

        return data

    async def get_favorites(
        self,
        screen_name: str,
        count: int | None = None,
        since_id: int | None = None,
        max_id: int | None = None,
        include_entities: str | None = None,
        tweet_mode: str | None = None,
    ) -> collections.abc.Sequence[models.Tweet]:
        """Get the favorites of a user."""
        url = "https://api.twitter.com/1.1/favorites/list.json"
        params = dict(
            screen_name=screen_name,
            count=count,
            since_id=since_id,
            max_id=max_id,
            include_entities=include_entities,
            tweet_mode=tweet_mode,
        )
        data = await self.request(url, params=params)
        return pydantic.parse_obj_as(collections.abc.Sequence[models.Tweet], data)


async def main() -> None:
    """Run the main function."""
    user = input("Enter your twitter username: ")
    token = input("Enter your twitter auth token: ")
    client = Twitter(token)

    favorites = await client.get_favorites(user)
    print(repr(favorites))  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
