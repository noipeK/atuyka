"""Proxy utilities."""
import asyncio
import collections.abc
import contextlib
import typing

import typing_extensions

__all__ = ["ProxyContextType", "ProxyEnteredContextType", "ProxyStream", "aiohttp_proxy_stream", "as_proxy_stream"]

P = typing_extensions.ParamSpec("P")

RawStreamType = collections.abc.AsyncIterator[bytes]
HeadersType = collections.abc.Mapping[str, str]
ProxyEnteredContextType = tuple[RawStreamType, HeadersType | None] | RawStreamType
ProxyContextType = typing.AsyncContextManager[ProxyEnteredContextType]


class ProxyStream:
    """Stream proxy."""

    _context: ProxyContextType
    _stream: RawStreamType | None = None
    _headers: HeadersType | None = None

    def __init__(self, context: ProxyContextType) -> None:
        self._context = context

    async def __aenter__(self) -> typing_extensions.Self:
        """Prepare the stream."""
        if self._stream is not None:
            raise RuntimeError("Already in context manager.")

        items = await self._context.__aenter__()
        if isinstance(items, tuple):
            self._stream, self._headers = items
        else:
            self._stream = items

        return self

    async def __aexit__(self, *exc: typing.Any) -> None:
        await self._context.__aexit__(*exc)

    def __del__(self) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.__aexit__(None, None, None))
            else:
                loop.run_until_complete(self.__aexit__(None, None, None))
        except:  # noqa: E722
            pass

    async def __aiter__(self) -> RawStreamType:
        return self.raw_stream

    async def __await__(self) -> collections.abc.AsyncIterator[tuple[RawStreamType, HeadersType]]:
        """Return the stream and headers."""
        yield (self._get_auto_closing_stream(), self.headers)

    async def _get_auto_closing_stream(self) -> RawStreamType:
        """Get the stream and close it when done."""
        if self._stream is None:
            await self.__aenter__()

        async for chunk in self.raw_stream:
            yield chunk

        await self.__aexit__(None, None, None)

    @property
    def raw_stream(self) -> RawStreamType:
        """The chunked byte stream."""
        if self._stream is None:
            raise RuntimeError("Not in context manager.")

        return self._stream

    @property
    def stream(self) -> RawStreamType:
        """Get the stream and close it when done."""
        return self._get_auto_closing_stream()

    @property
    def headers(self) -> HeadersType:
        """The response headers."""
        return self._headers or {}

    async def get_headers(self) -> HeadersType:
        """Get the response headers and prepare the stream."""
        if self._stream is None:
            await self.__aenter__()

        return self.headers

    async def read(self) -> bytes:
        """Read the stream."""
        if self._stream is None:
            async with self as stream:
                return await stream.read()

        return b"".join([chunk async for chunk in self._stream])


def as_proxy_stream(callback: typing.Callable[P, ProxyContextType]) -> typing.Callable[P, ProxyStream]:
    """Decorate a callable context manager to a proxy stream."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> ProxyStream:
        return ProxyStream(callback(*args, **kwargs))

    return wrapper


@as_proxy_stream
@contextlib.asynccontextmanager
async def aiohttp_proxy_stream(
    url: str,
    **kwargs: typing.Any,
) -> typing.AsyncIterator[ProxyEnteredContextType]:
    """Create a proxy stream from an aiohttp stream."""
    import aiohttp

    async with aiohttp.ClientSession(auto_decompress=False) as session:
        async with session.get(url, **kwargs) as response:
            headers = dict(response.headers)
            headers["x-status-code"] = str(response.status)
            yield (response.content.iter_any(), headers)
