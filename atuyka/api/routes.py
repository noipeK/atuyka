"""FastAPI atuyka routes."""
import collections.abc

import fastapi
import fastapi.param_functions as params
import fastapi.params
import starlette.requests
import starlette.responses

import atuyka.errors
import atuyka.services

__all__ = ["exception_handler", "router"]

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
    if token:
        response.set_cookie(f"{service}_token", token)

    client = atuyka.services.ServiceClient.create(service, token)
    await client.start()

    try:
        yield client
    finally:
        await client.close()


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


@router.get("/users/{user}/likes")
async def get_liked_posts(
    request: starlette.requests.Request,
    client: atuyka.services.ServiceClient = fastapi.Depends(get_client),
    user: str | None = params.Path("me", description="User identifier.", example="me"),
) -> atuyka.services.models.Page[atuyka.services.models.Post]:
    """Get liked posts."""
    user = _parse_user(user)
    return await client.get_liked_posts(user, **request.query_params)


def exception_handler(
    request: starlette.requests.Request,
    exc: atuyka.errors.AtuykaError,
) -> starlette.responses.JSONResponse:
    """Handle atuyka exceptions."""
    data = {}

    error_type = type(exc).__name__.replace("Error", "")

    match exc:
        case atuyka.errors.InvalidServiceError(available_services=available_services):
            status_code = 404
            data = {"available_services": available_services}
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
        case _:
            status_code = 500
            error_type = "Internal"

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
    upgrade_response_model(router)
