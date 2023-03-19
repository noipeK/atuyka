"""FastAPI atuyka routes."""
import collections.abc
import logging
import typing

import fastapi
import fastapi.param_functions as params
import fastapi.params
import starlette.requests
import starlette.responses

import atuyka.errors
import atuyka.services

__all__ = ["exception_handler", "router"]

T = typing.TypeVar("T")

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


async def dependency_client(
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
    if token:
        response.set_cookie(f"{service}_token", token)

    client = atuyka.services.ServiceClient.create(service, token)
    await client.start()

    if client.my_user_id:
        response.set_cookie(f"{service}_id", client.my_user_id)

    try:
        yield client
    finally:
        await client.close()


async def dependency_user_id(
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = params.Path(description="User identifier.", example="me"),
) -> str | None:
    """Get a user ID."""
    if user and user != "me" and user != "0":
        return user

    service = client.__class__.service_name or ""
    raise atuyka.errors.MissingUserIDError(service, client.my_user_id)


async def dependency_post_id(post: str = params.Path(description="Post identifier.")) -> str:
    """Get a post ID."""
    return post


@router.get("/services")
async def get_services() -> list[atuyka.services.models.AtuykaService]:
    """Get available services."""
    return [
        atuyka.services.models.AtuykaService(
            name=service.service_name or service.__name__,
            authorization=service.requires_authorization,
        )
        for service in atuyka.services.ServiceClient.available_services.values()
    ]


@router.get("/users/me/id")
async def get_my_user_id(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
) -> collections.abc.Sequence[str]:
    """Get my user ID."""
    return [client.my_user_id] if client.my_user_id else []


@router.get("/users/{user}")
async def get_user(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
) -> atuyka.services.models.User:
    """Get a user."""
    return await client.get_user(user, **request.query_params)


@router.get("/users/{user}/likes")
async def get_liked_posts(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
) -> atuyka.services.models.Page[atuyka.services.models.Post]:
    """Get liked posts."""
    return await client.get_liked_posts(user, **request.query_params)


@router.get("/users/{user}/following")
async def get_following(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
) -> atuyka.services.models.Page[atuyka.services.models.User]:
    """Get followed users."""
    return await client.get_following(user, **request.query_params)


@router.get("/users/{user}/followers")
async def get_followers(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
) -> atuyka.services.models.Page[atuyka.services.models.User]:
    """Get followers."""
    return await client.get_followers(user, **request.query_params)


@router.get("/users/{user}/posts")
async def get_posts(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
) -> atuyka.services.models.Page[atuyka.services.models.Post]:
    """Get posts."""
    return await client.get_posts(user, **request.query_params)


@router.get("/users/{user}/posts/{post}")
async def get_post(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
    post: str = fastapi.Depends(dependency_post_id),
) -> atuyka.services.models.Post:
    """Get a post."""
    return await client.get_post(user, post, **request.query_params)


@router.get("/posts/{post}")
async def get_post_alt(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    post: str = fastapi.Depends(dependency_post_id),
) -> atuyka.services.models.Post:
    """Get a post."""
    return await client.get_post(None, post, **request.query_params)


@router.get("/users/{user}/posts/{post}/comments")
async def get_comments(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
    post: str = fastapi.Depends(dependency_post_id),
) -> atuyka.services.models.Page[atuyka.services.models.Comment]:
    """Get comments."""
    return await client.get_comments(user, post, **request.query_params)


@router.get("/posts/{post}/comments")
async def get_comments_alt(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    post: str = fastapi.Depends(dependency_post_id),
) -> atuyka.services.models.Page[atuyka.services.models.Comment]:
    """Get comments."""
    return await client.get_comments(None, post, **request.query_params)


@router.get("/users/{user}/posts/{post}/comments/{comment}/comments")
async def get_comment_replies(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
    post: str = fastapi.Depends(dependency_post_id),
    comment: str = fastapi.Path(..., description="Comment identifier"),
) -> atuyka.services.models.Page[atuyka.services.models.Comment]:
    """Get comment replies."""
    return await client.get_comments(user, post, comment, **request.query_params)


@router.get("/posts/{post}/comments/{comment}/comments")
async def get_comment_replies_alt(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    post: str = fastapi.Depends(dependency_post_id),
    comment: str = fastapi.Path(..., description="Comment identifier"),
) -> atuyka.services.models.Page[atuyka.services.models.Comment]:
    """Get comment replies."""
    return await client.get_comments(None, post, comment, **request.query_params)


@router.get("/users/{user}/posts/{post}/similar")
async def get_similar_posts(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    user: str = fastapi.Depends(dependency_user_id),
    post: str = fastapi.Depends(dependency_post_id),
) -> atuyka.services.models.Page[atuyka.services.models.Post]:
    """Get similar posts."""
    return await client.get_similar_posts(user, post, **request.query_params)


@router.get("/posts/{post}/similar")
async def get_similar_posts_alt(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    post: str = fastapi.Depends(dependency_post_id),
) -> atuyka.services.models.Page[atuyka.services.models.Post]:
    """Get similar posts."""
    return await client.get_similar_posts(None, post, **request.query_params)


PROXY_HEADERS = (
    "x-status-code",
    "accept-ranges",
    "age",
    "Cache-control",
    "content-encoding",
    "content-length",
    "content-type",
    "expires",
    "last-modified",
)


@router.get("/proxy")
async def proxy(
    url: str = fastapi.Query(..., description="URL to proxy"),
    client: atuyka.services.ServiceClient = fastapi.Depends(dependency_client),
    range_header: str | None = fastapi.Header(None, alias="Range", include_in_schema=False),
) -> starlette.responses.Response:
    """Proxy a request."""
    request_headers = {"Range": range_header}
    request_headers = {k: v for k, v in request_headers.items() if v is not None}

    proxied_stream = client.proxy(url, headers=request_headers)
    headers = await proxied_stream.get_headers()

    accepted_headers = {k.lower(): v for k, v in headers.items() if k.lower() in PROXY_HEADERS}
    accepted_headers["x-proxy-url"] = url

    return starlette.responses.StreamingResponse(
        proxied_stream.stream,
        status_code=int(accepted_headers.get("x-status-code", 200)),
        headers=accepted_headers,
    )


def exception_handler(
    request: starlette.requests.Request,
    exc: atuyka.errors.AtuykaError,
) -> starlette.responses.Response:
    """Handle atuyka exceptions."""
    data = {}

    error_type = type(exc).__name__.replace("Error", "")

    match exc:
        case atuyka.errors.InvalidServiceError(available_services=available_services):
            status_code = 404
            data = {"available_services": available_services}
        case atuyka.errors.MissingUserIDError(suggestion=suggestion) if suggestion is not None:
            url = request.url.replace(path=request.url.path.replace("/me", f"/{suggestion}", 1))
            return starlette.responses.RedirectResponse(url)
        case atuyka.errors.MissingUserIDError:
            status_code = 422
        case atuyka.errors.InvalidIDError(id=id):
            status_code = 404
            data = {"id": id}
        case atuyka.errors.InvalidResourceError(resource=resource):
            status_code = 404
            data = {"resource": resource}
        case atuyka.errors.PrivateResourceError(resource=resource):
            status_code = 403
            data = {"resource": resource}
        case atuyka.errors.InvalidTokenError(token=token):
            status_code = 401
            data = {"token": token}
        case atuyka.errors.AuthenticationError:
            status_code = 401
        case atuyka.errors.ServiceError:
            status_code = 400
        case _:
            status_code = 500
            error_type = "Internal"
            logging.exception(exc)

    return starlette.responses.JSONResponse(
        status_code=status_code,
        content={"error": exc.message, "error_type": error_type, "service": exc.service, **data},
    )


def upgrade_response_model(router: fastapi.routing.APIRouter) -> None:
    """Upgrade response models to exclude defaults."""
    for route in router.routes:
        if isinstance(route, fastapi.routing.APIRoute):
            route.response_model_exclude_defaults = True


if __name__ != "__main__":
    # include defaults only when debugging
    upgrade_response_model(router)
