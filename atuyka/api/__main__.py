"""API entrypoint."""
import fastapi

# activate all clients
import atuyka.services.pixiv  # type: ignore  # noqa: F401
import atuyka.services.twitter  # type: ignore  # noqa: F401

from . import routes

__all__ = ["app"]

app: fastapi.FastAPI = fastapi.FastAPI()
app.include_router(routes.router)

if __name__ == "__main__":
    import uvicorn  # pyright: ignore # noqa: I900

    uvicorn.run(app)  # pyright: ignore
