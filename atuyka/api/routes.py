"""FastAPI atuyka routes."""
import fastapi
import fastapi.param_functions as params
import fastapi.params
import fastapi.security

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

router: fastapi.APIRouter = fastapi.APIRouter()


def _parse_user(user: str | None) -> str | None:
    """Parse a user identifier."""
    if user and user != "me":
        return user

    return None


api_key_header: fastapi.security.APIKeyHeader = fastapi.security.APIKeyHeader(
    name="Authorization",
    description="Token for the chosen service.",
)


def get_client(
    service: str = params.Query(description="Target service slug.", example="twitter"),
    # token: str | None = params.Header(None, alias="Authorization", description="Token for the chosen service."),
    token: str | None = params.Security(api_key_header),
) -> atuyka.services.ServiceClient:
    """Get a client as a dependency."""
    return atuyka.services.ServiceClient.create(service, token)


@router.get("/users/{user}/likes", response_model=atuyka.services.models.Page[atuyka.services.models.Post])
async def get_liked_posts(
    client: atuyka.services.ServiceClient = fastapi.Depends(get_client),
    user: str | None = params.Path("me", description="User identifier.", example="me"),
) -> atuyka.services.models.Page[atuyka.services.models.Post]:
    """Get liked posts."""
    user = _parse_user(user)
    return await client.get_liked_posts(user)
