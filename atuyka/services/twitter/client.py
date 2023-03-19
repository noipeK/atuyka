"""Twitter front-end API client."""
import collections.abc
import contextlib
import os
import re
import typing

import aiohttp
import pydantic

import atuyka.errors
import atuyka.utility
from atuyka.services import base

from . import models

# https://github.com/KohnoseLami/Twitter_Frontend_API
# https://github.com/p1atdev/whisper

# This is not a private token
GUEST_AUTHORIZATION = (
    "Bearer "
    "AAAAAAAAAAAAAAAAAAAAAF7aAAAAAAAASCiRjWvh7R5wxaKkFp7MM%2BhYBqM="
    "bQ0JPmjU9F6ZoMhDfI4uTNAaQuTDm2uO9x3WFVr2xBZ2nhjdP0"
)
UA = "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"

__all__ = ["Twitter"]


class TwitterError(typing.TypedDict):
    """Twitter error."""

    code: int
    message: str


class Twitter(base.ServiceClient, service="twitter", url="twitter.com"):
    """Twitter front-end API client."""

    NAME_CACHE: atuyka.utility.Cache[str, str] = atuyka.utility.Cache()

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
        """Generate the ct0 token. Used for advertising."""
        async with aiohttp.request("GET", "https://twitter.com/i/release_notes") as response:
            return response.cookies["ct0"].value

    def _generate_fake_ct0(self) -> str:
        """Generate the ct0 token. Used for advertising."""
        return hex(int.from_bytes(os.urandom(16), "big"))[2:]

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
            raise atuyka.errors.MissingTokenError("twitter")

        if not self.ct0:
            self.ct0 = self._generate_fake_ct0()
            # self.ct0 = await self._generate_ct0()

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

    async def start(self) -> None:
        """Start the client."""
        if self.auth_token:
            await self._get_my_screen_name()

    def _raise_errors(self, error: TwitterError | str, *errors: TwitterError, url: str) -> typing.NoReturn:
        """Raise errors."""
        if isinstance(error, str):
            code, message = 0, error
        else:
            code, message = error["code"], error["message"]

        if code in (32,):
            raise atuyka.errors.InvalidTokenError("twitter", self.auth_token or "")
        if code in (220,):
            raise atuyka.errors.MissingUserIDError("twitter")
        if code in (34, 50):
            raise atuyka.errors.InvalidResourceError("twitter", url)
        if code in (63, 421, 422, 425):
            raise atuyka.errors.SuspendedResourceError("twitter", url)
        if code in (88,):
            raise atuyka.errors.RateLimitedError("twitter")

        if message == "Not authorized.":
            raise atuyka.errors.PrivateResourceError("twitter", url)

        raise atuyka.errors.ServiceError("twitter", message)

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

        async with aiohttp.request(
            method,
            url,
            params=params,  # pyright: ignore  # untyped
            headers=headers,
            **kwargs,
        ) as response:
            try:
                data = await response.json(content_type=None)
            except aiohttp.ContentTypeError:
                response.raise_for_status()
                raise

        if "error" in data:
            self._raise_errors(data["error"], url=str(response.url))
        elif "errors" in data:
            self._raise_errors(*data["errors"], url=str(response.url))
        else:
            response.raise_for_status()

        return data

    async def request_json_api(
        self,
        endpoint: str,
        *,
        version: str = "1.1",
        params: typing.Mapping[str, str | int | None] | None = None,
        data: typing.Mapping[str, object] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        """Make a request to the Twitter v1 API."""
        url = f"https://api.twitter.com/{version}/{endpoint}"

        if version == "1.1":
            params = dict(params or {})
            params.update(
                include_user_entities="true",
                tweet_mode="extended",
            )

        return await self.request(
            url,
            params=params,
            json=data,
            method=kwargs.get("header") or ("POST" if data else "GET"),
            **kwargs,
        )

    async def _get_account_settings(self) -> dict[str, typing.Any]:
        """Get the settings."""
        return await self.request_json_api("account/settings.json")

    async def _get_my_screen_name(self) -> str:
        """Get the authenticated user screen name."""
        if self.my_screen_name:
            return self.my_screen_name

        if self.auth_token and self.auth_token in self.NAME_CACHE:
            self.my_screen_name = self.NAME_CACHE[self.auth_token]
            return self.my_screen_name

        settings = await self._get_account_settings()
        self.my_screen_name = settings["screen_name"]

        if self.auth_token:
            self.NAME_CACHE[self.auth_token] = self.my_screen_name

        return self.my_screen_name

    @property
    def my_user_id(self) -> str | None:
        """The authenticated user's ID."""
        return self.my_screen_name

    async def _parse_user(self, user: int | str | None) -> collections.abc.Mapping[str, typing.Any]:
        """Parse a user into a params dict."""
        if user is None:
            user = await self._get_my_screen_name()

        if isinstance(user, int) or user.isdigit():
            return {"user_id": user}

        return {"screen_name": user}

    # ------------------------------------------------------------
    # RAW API:

    async def get_favorites(
        self,
        user: str | int | None = None,
        *,
        count: int | None = None,
        since_id: int | None = None,
        max_id: int | None = None,
    ) -> collections.abc.Sequence[models.Tweet]:
        """Get the favorites of a user."""
        params = dict(
            **(await self._parse_user(user)),
            count=count,
            since_id=since_id,
            max_id=max_id,
        )
        data = await self.request_json_api("favorites/list.json", params=params)
        return pydantic.parse_obj_as(collections.abc.Sequence[models.Tweet], data)

    async def get_friends(
        self,
        user: str | int | None = None,
        *,
        cursor: int | None = None,
        count: int | None = None,
    ) -> models.UserCursor:
        """Get the friends of a user."""
        params = dict(
            **(await self._parse_user(user)),
            cursor=cursor,
            count=count,
        )
        data = await self.request_json_api("friends/list.json", params=params)
        return pydantic.parse_obj_as(models.UserCursor, data)

    async def get_follows(
        self,
        user: str | int | None = None,
        *,
        cursor: int | None = None,
        count: int | None = None,
    ) -> models.UserCursor:
        """Get the follows of a user."""
        params = dict(
            **(await self._parse_user(user)),
            cursor=cursor,
            count=count,
        )
        data = await self.request_json_api("followers/list.json", params=params)
        return pydantic.parse_obj_as(models.UserCursor, data)

    async def get_user_info(self, user: int | str | None = None) -> models.TwitterUser:
        """Get the info of a user."""
        params = await self._parse_user(user)

        data = await self.request_json_api("users/show.json", params=params)
        return pydantic.parse_obj_as(models.TwitterUser, data)

    async def get_user_tweets(
        self,
        user: int | str | None = None,
        *,
        count: int | None = None,
        since_id: int | None = None,
        max_id: int | None = None,
    ) -> collections.abc.Sequence[models.Tweet]:
        """Get the tweets of a user."""
        params = dict(
            **(await self._parse_user(user)),
            count=count,
            since_id=since_id,
            max_id=max_id,
        )

        data = await self.request_json_api("statuses/user_timeline.json", params=params)
        return pydantic.parse_obj_as(collections.abc.Sequence[models.Tweet], data)

    async def get_tweet(self, tweet_id: int) -> models.Tweet:
        """Get a tweet."""
        params = dict(id=tweet_id)
        data = await self.request_json_api("statuses/show.json", params=params)
        return pydantic.parse_obj_as(models.Tweet, data)

    # ------------------------------------------------------------
    # UNIVERSAL:

    async def get_user(self, user: str | None = None, **kwargs: object) -> base.models.User:
        """Get user."""
        data = await self.get_user_info(user)
        return data.to_universal()

    async def get_liked_posts(
        self,
        user: str | None = None,
        *,
        since_id: int | None = None,
        max_id: int | None = None,
        count: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get liked posts."""
        tweets = await self.get_favorites(user, since_id=since_id, max_id=max_id, count=count)
        posts = [tweet.to_universal() for tweet in tweets]

        page = base.models.Page(items=posts, next=dict(since_id=str(tweets[-1].id)))
        return page

    async def get_following(
        self,
        user: str | None = None,
        *,
        cursor: int | None = None,
        count: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.User]:
        """Get following users."""
        users = await self.get_friends(user, cursor=cursor, count=count)
        return users.to_universal()

    async def get_followers(
        self,
        user: str | None = None,
        *,
        cursor: int | None = None,
        count: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.User]:
        """Get followers."""
        users = await self.get_follows(user, cursor=cursor, count=count)
        return users.to_universal()

    async def get_posts(
        self,
        user: str | None = None,
        *,
        since_id: int | None = None,
        max_id: int | None = None,
        count: int | None = None,
        **kwargs: object,
    ) -> base.models.Page[base.models.Post]:
        """Get posts made by a user."""
        tweets = await self.get_user_tweets(user, since_id=since_id, max_id=max_id, count=count)
        posts = [tweet.to_universal() for tweet in tweets]

        page = base.models.Page(items=posts, next=dict(since_id=str(tweets[-1].id)))
        return page

    async def get_post(self, user: str | None, post: str, **kwargs: object) -> base.models.Post:
        """Get a post."""
        tweet = await self.get_tweet(int(post))
        return tweet.to_universal()

    async def get_comments(
        self,
        user: str | None,
        post: str,
        comment: str | None = None,
        **kwargs: object,
    ) -> typing.NoReturn:
        """Get comments."""
        raise NotImplementedError

    async def get_similar_posts(self, user: str | None, post: str, **kwargs: object) -> typing.NoReturn:
        """Get similar posts."""
        raise atuyka.errors.MissingEndpointError("twitter", "posts/similar")

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

    @contextlib.asynccontextmanager
    async def _proxy(
        self,
        url: str,
        /,
        **kwargs: object,
    ) -> typing.AsyncIterator[atuyka.utility.ProxyEnteredContextType]:
        """Download a file."""
        async with aiohttp.ClientSession(auto_decompress=False) as session:
            async with session.get(url, **kwargs) as response:
                headers = dict(response.headers)
                headers["x-status-code"] = str(response.status)
                yield (response.content.iter_any(), headers)
