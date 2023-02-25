"""FastAPI atuyka routes."""
import collections.abc

import fastapi
import fastapi.param_functions as params
import fastapi.params
import starlette.requests
import starlette.responses

import atuyka.services

__all__ = ["router"]

# /users/...
# /users/.../likes
# /users/.../following
# /users/.../followers
# /users/.../posts
# /users/.../posts/...
# /users/.../posts/.../comments
# /users/.../posts/.../similar
# /feed/following ~ /user/.../feed/following
# /feed/recommended ~ /user/.../feed/recommended
# /search/posts?q
# /search/users?q


router: fastapi.APIRouter = fastapi.APIRouter(tags=["services"])


def _parse_user(user: str | None) -> str | None:
    """Parse a user identifier."""
    if user and user != "me" and user != "0":
        return user

    return None


async def get_client(
    request: starlette.requests.Request,
    response: starlette.responses.Response,
    service: str = params.Query(description="Target service slug.", example="twitter"),
    token: str | None = params.Query(None, description="Token for the chosen service."),
) -> collections.abc.AsyncIterator[atuyka.services.ServiceClient]:
    """Get a client as a dependency.

    Reads the token from the Authorization header, the token query parameter, or <service>_token cookies.
    """
    token_header = request.headers.get("Authorization") or request.headers.get("x-service-token")
    token = token_header or token or request.cookies.get(f"{service}_token")
    if not token:
        raise ValueError("No token provided.")  # TODO: custom exceptions

    response.set_cookie(f"{service}_token", token)

    client = atuyka.services.ServiceClient.create(service, token)
    await client.start()

    try:
        yield client
    except Exception:
        raise  # TODO: handle exceptions
    finally:
        await client.close()


@router.get("/users/{user}/likes")
async def get_liked_posts(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(get_client),
    user: str | None = params.Path("me", description="User identifier.", example="me"),
) -> atuyka.services.models.Page[atuyka.services.models.Post]:
    """Get liked posts."""
    user = _parse_user(user)
    return await client.get_liked_posts(user, **request.query_params)


def upgrade_response_model(router: fastapi.routing.APIRouter) -> None:
    """Upgrade response models to exclude defaults."""
    for route in router.routes:
        if isinstance(route, fastapi.routing.APIRoute):
            route.response_model_exclude_defaults = True


if __name__ != "__main__":
    upgrade_response_model(router)
