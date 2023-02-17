"""API entrypoint."""
import fastapi
import starlette
import starlette.responses

# activate all clients
import atuyka.services.pixiv  # type: ignore  # noqa: F401
import atuyka.services.twitter  # type: ignore  # noqa: F401

from . import routes

__all__ = ["app"]

app: fastapi.FastAPI = fastapi.FastAPI()
app.include_router(routes.router)


@app.get("/", include_in_schema=False)
async def index() -> starlette.responses.Response:
    return starlette.responses.RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn  # pyright: ignore # noqa: I900

    uvicorn.run(app)  # pyright: ignore
