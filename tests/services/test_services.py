"""Test services."""
import contextlib
import os
import typing

import pytest

import atuyka.errors
import atuyka.services

atuyka.services.load_services()


@contextlib.asynccontextmanager
async def get_service(service: str) -> typing.AsyncIterator[atuyka.services.ServiceClient]:
    """Get a client for a service."""
    token = os.environ.get(f"{service.upper()}_TOKEN")
    async with atuyka.services.ServiceClient.create(service, token=token) as client:
        with contextlib.suppress(atuyka.errors.MissingEndpointError):
            yield client


@pytest.mark.parametrize(("service", "user"), [("twitter", "twitterdev")], ids=lambda x: x[0])
async def test_get_user(service: str, user: str) -> None:
    async with get_service(service) as client:
        result = await client.get_user(user)
        # TODO: Respect config
        assert result.unique_name
        assert result.unique_name.lower() == user


@pytest.mark.asyncio()
@pytest.mark.parametrize(("service", "user"), [("twitter", "twitterdev")], ids=lambda x: x[0])
async def test_liked_posts(service: str, user: str) -> None:
    async with get_service(service) as client:
        result = await client.get_liked_posts(user)
        assert len(result.items) > 10


@pytest.mark.asyncio()
@pytest.mark.parametrize(("service", "user"), [("twitter", "twitterdev")], ids=lambda x: x[0])
async def test_following(service: str, user: str) -> None:
    async with get_service(service) as client:
        result = await client.get_following(user)
        assert len(result.items) > 10


@pytest.mark.asyncio()
@pytest.mark.parametrize(("service", "user"), [("twitter", "twitterdev")], ids=lambda x: x[0])
async def test_followers(service: str, user: str) -> None:
    async with get_service(service) as client:
        result = await client.get_followers(user)
        assert len(result.items) > 10


@pytest.fixture(params=[("twitter", "twitterdev")])
async def new_post(request: pytest.FixtureRequest) -> tuple[str, str, str]:
    service, user = request.param

    async with get_service(service) as client:
        result = await client.get_posts(user)
        assert len(result.items) > 10
        return service, user, result.items[0].id


@pytest.mark.asyncio()
async def test_post(new_post: tuple[str, str, str]) -> None:
    service, user, post = new_post

    async with get_service(service) as client:
        result = await client.get_post(user, post)
        assert result.id == post


@pytest.mark.asyncio()
async def test_comments(new_post: tuple[str, str, str]) -> None:
    service, user, post = new_post

    async with get_service(service) as client:
        result = await client.get_comments(user, post)
        assert len(result.items) > 10
