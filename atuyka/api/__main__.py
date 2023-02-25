"""API entrypoint."""
import fastapi
import starlette
import starlette.requests
import starlette.responses

import atuyka.errors

# activate all clients
import atuyka.services.pixiv  # type: ignore # noqa: TODO: FIX
import atuyka.services.twitter  # type: ignore  # noqa: TODO: FIX

from . import routes

__all__ = ["app"]

app: fastapi.FastAPI = fastapi.FastAPI()
app.include_router(routes.router)
app.add_exception_handler(atuyka.errors.AtuykaError, routes.exception_handler)  # pyright: reportUnknownMemberType=false


@app.get("/", include_in_schema=False)
async def index() -> starlette.responses.Response:
    """Redirect to docs."""
    return starlette.responses.RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn  # pyright: ignore

    uvicorn.run(app)  # pyright: ignore
