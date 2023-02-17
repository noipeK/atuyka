"""Twitter front-end API client."""
import collections.abc
import re
import typing

import aiohttp
import pydantic

from atuyka.services import base

from . import models

# https://github.com/KohnoseLami/Twitter_Frontend_API
# https://github.com/p1atdev/whisper

# This is not a private token
GUEST_AUTHORIZATION = (
    "Bearer "
    + "AAAAAAAAAAAAAAAAAAAAAF7aAAAAAAAASCiRjWvh7R5wxaKkFp7MM%2BhYBqM="
    + "bQ0JPmjU9F6ZoMhDfI4uTNAaQuTDm2uO9x3WFVr2xBZ2nhjdP0"
)
UA = "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"

__all__ = ["Twitter"]


class Twitter(base.ServiceClient):
    """Twitter front-end API client."""

    auth_token: str | None

    ct0: str | None
    guest_token: str | None
    guest_authorization: str
    user_agent: str

    my_screen_name: str | None

    def __init__(
        self,
        token: str | None = None,
        *,
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

        self.my_screen_name = None

    async def _generate_guest_token(self) -> str:
        """Generate the token."""
        headers = {"User-Agent": self.user_agent, "Authorization": self.guest_authorization}
        async with aiohttp.request(
            "POST",
            "https://api.twitter.com/1.1/guest/activate.json",
            headers=headers,
        ) as response:
            data = await response.json()

        return data["guest_token"]

    async def _generate_ct0(self) -> str:
        """Generate the ct0 token."""
        async with aiohttp.request("GET", "https://twitter.com/i/release_notes") as response:
            return response.cookies["ct0"].value

    async def _generate_authenticity_token(self) -> str:
        """Generate the authenticity token."""
        async with aiohttp.request("GET", "https://twitter.com/account/begin_password_reset") as response:
            text = await response.text()

        match = re.search(r'"authenticity_token" value="(.*?)"', text)
        assert match
        return match[1]

    async def get_guest_headers(self) -> collections.abc.Mapping[str, str]:
        """Return the headers for the request."""
        if not self.guest_token:
            self.guest_token = await self._generate_guest_token()

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
            self.ct0 = await self._generate_ct0()

        return {
            "Origin": "https://twitter.com",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Authorization": self.guest_authorization,
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

        async with aiohttp.request(method, url, params=params, headers=headers, **kwargs) as response:  # type: ignore
            response.raise_for_status()
            data = await response.json(content_type=None)

        if "error" in data:
            raise ValueError(data["error"])
        if "errors" in data:
            raise ValueError(data["errors"])

        return data

    async def _get_account_settings(self) -> dict[str, typing.Any]:
        """Get the settings."""
        url = "https://api.twitter.com/1.1/account/settings.json"
        return await self.request(url)

    async def _get_my_screen_name(self) -> str:
        """Get the authenticated user screen name."""
        if self.my_screen_name:
            return self.my_screen_name

        settings = await self._get_account_settings()
        self.my_screen_name = settings["screen_name"]
        return self.my_screen_name

    async def get_favorites(
        self,
        screen_name: str | None = None,
        *,
        count: int | None = None,
        since_id: int | None = None,
        max_id: int | None = None,
    ) -> collections.abc.Sequence[models.Tweet]:
        """Get the favorites of a user."""
        url = "https://api.twitter.com/1.1/favorites/list.json"
        params = dict(
            screen_name=screen_name or await self._get_my_screen_name(),
            count=count,
            since_id=since_id,
            max_id=max_id,
            include_entities="true",
            tweet_mode="extended",
        )
        data = await self.request(url, params=params)
        return pydantic.parse_obj_as(collections.abc.Sequence[models.Tweet], data)

    async def get_friends(
        self,
        screen_name: str | None = None,
        *,
        cursor: int | None = None,
        count: int | None = None,
        skip_status: bool | None = None,
        include_user_entities: bool | None = None,
        tweet_mode: str | None = None,
    ) -> models.UserCursor:
        """Get the friends of a user."""
        url = "https://api.twitter.com/1.1/friends/list.json"
        params = dict(
            screen_name=screen_name or await self._get_my_screen_name(),
            cursor=cursor,
            count=count,
            skip_status=skip_status,
            include_user_entities=include_user_entities,
            tweet_mode=tweet_mode,
        )
        data = await self.request(url, params=params)
        return pydantic.parse_obj_as(models.UserCursor, data)

    async def get_user_info(self, user: int | str) -> models.TwitterUser:
        """Get the info of a user."""
        url = "https://api.twitter.com/1.1/users/show.json"
        if isinstance(user, int):
            params = dict(user_id=user)
        else:
            params = dict(screen_name=user)

        data = await self.request(url, params=params)
        return pydantic.parse_obj_as(models.TwitterUser, data)

    async def get_user_tweets(self, user: int | str) -> models.Timeline:
        """Get the tweets of a user."""
        if isinstance(user, str):
            user = (await self.get_user_info(user)).id

        url = f"https://api.twitter.com/2/timeline/profile/{user}.json"
        data = await self.request(url)
        return pydantic.parse_obj_as(models.Timeline, data)

    # ------------------------------------------------------------
    # UNIVERSAL:

    async def get_user(self, user: str | None = ..., **kwargs: object) -> typing.NoReturn:
        """Get user."""
        raise NotImplementedError

    async def get_liked_posts(
        self,
        user: str | None = None,
        *,
        since_id: int | None = None,
        max_id: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get liked posts."""
        tweets = await self.get_favorites(user, since_id=since_id, max_id=max_id)
        posts = [tweet.to_universal() for tweet in tweets]

        page = base.models.Page(items=posts, next=dict(since_id=tweets[-1].id))
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
