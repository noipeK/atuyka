"""Universal asynchronous base paginator."""
import abc
import asyncio
import collections.abc
import functools
import heapq
import random
import typing

import typing_extensions

from . import models

__all__ = [
    "BufferedPaginator",
    "MergedPaginator",
    "Paginator",
    "UniversalPaginator",
    "paginate",
]

P = typing_extensions.ParamSpec("P")
T = typing.TypeVar("T")


async def flatten(iterable: collections.abc.AsyncIterable[T]) -> collections.abc.Sequence[T]:
    """Flatten an async iterable."""
    if isinstance(iterable, Paginator):
        return await iterable.flatten()

    return [x async for x in iterable]


async def aiterate(iterable: collections.abc.Iterable[T]) -> collections.abc.AsyncIterator[T]:
    """Turn a plain iterable into an async iterator."""
    for i in iterable:
        yield i


class Paginator(typing.Generic[T], abc.ABC):
    """Base paginator."""

    __slots__ = ()

    async def next(self) -> T:
        """Return the next element."""
        try:
            return await self.__anext__()
        except StopAsyncIteration:
            raise LookupError("No elements were found") from None

    def _complete(self) -> typing.NoReturn:
        """Mark paginator as complete and clear memory."""
        raise StopAsyncIteration("No more items exist in this paginator. It has been exhausted.") from None

    def __aiter__(self) -> typing_extensions.Self:
        return self

    async def flatten(self) -> collections.abc.Sequence[T]:
        """Flatten the paginator."""
        return [item async for item in self]

    def __await__(self) -> collections.abc.Generator[None, None, collections.abc.Sequence[T]]:
        return self.flatten().__await__()

    @abc.abstractmethod
    async def __anext__(self) -> T:
        ...


class BasicPaginator(typing.Generic[T], Paginator[T], abc.ABC):
    """Paginator that simply iterates over an iterable."""

    __slots__ = ("iterator",)

    iterator: collections.abc.AsyncIterator[T]
    """Underlying iterator."""

    def __init__(self, iterable: collections.abc.Iterable[T] | collections.abc.AsyncIterable[T]) -> None:
        if isinstance(iterable, collections.abc.AsyncIterable):
            self.iterator = iterable.__aiter__()
        else:
            self.iterator = aiterate(iterable)

    async def __anext__(self) -> T:
        try:
            return await self.iterator.__anext__()
        except StopAsyncIteration:
            self._complete()


class BufferedPaginator(typing.Generic[T], Paginator[T], abc.ABC):
    """Paginator with a support for buffers."""

    __slots__ = ("limit", "_buffer", "_counter")

    limit: int | None
    """Limit of items to be yielded."""

    _buffer: collections.abc.Iterator[T] | None
    """Item buffer. If none then exhausted."""

    _counter: int
    """Amount of yielded items so far. No guarantee to be synchronized."""

    def __init__(self, *, limit: int | None = None) -> None:
        self.limit = limit

        self._buffer = iter(())
        self._counter = 0

    @property
    def exhausted(self) -> bool:
        """Whether all pages have been fetched."""
        return self._buffer is None

    def _complete(self) -> typing.NoReturn:
        self._buffer = None

        super()._complete()

    @abc.abstractmethod
    async def next_page(self) -> collections.abc.Iterable[T] | None:
        """Get the next page of the paginator."""

    async def __anext__(self) -> T:
        if not self._buffer:
            self._complete()

        if self.limit and self._counter >= self.limit:
            self._complete()

        self._counter += 1

        try:
            return next(self._buffer)
        except StopIteration:
            pass

        buffer = await self.next_page()
        if not buffer:
            self._complete()

        self._buffer = iter(buffer)
        return next(self._buffer)


class MergedPaginator(typing.Generic[T], Paginator[T]):
    """A paginator merging a collection of iterators."""

    __slots__ = ("iterators", "_heap", "limit", "_key", "_prepared", "_counter")

    # TODO: Use named tuples for the heap

    iterators: collections.abc.Sequence[collections.abc.AsyncIterator[T]]
    """Entry iterators.
    Only used as pointers to a heap.
    """

    _heap: list[tuple[typing.Any, int, T, collections.abc.AsyncIterator[T]]]
    """Underlying heap queue.
    List of (comparable, unique order id, value, iterator)
    """

    limit: int | None
    """Limit of items to be yielded"""

    _key: collections.abc.Callable[[T], typing.Any] | None
    """Sorting key."""

    _prepared: bool
    """Whether the paginator is prepared"""

    _counter: int
    """Amount of yielded items so far. No guarantee to be synchronized."""

    def __init__(
        self,
        iterables: collections.abc.Collection[collections.abc.AsyncIterable[T]],
        *,
        key: collections.abc.Callable[[T], typing.Any] | None = None,
        limit: int | None = None,
    ) -> None:
        self.iterators = [iterable.__aiter__() for iterable in iterables]
        self._key = key
        self.limit = limit

        self._prepared = False
        self._counter = 0

    def _complete(self) -> typing.NoReturn:
        """Mark paginator as complete and clear memory."""
        # free memory in heaps
        self._heap = []
        self.iterators = []

        super()._complete()

    def _create_heap_item(
        self,
        value: T,
        iterator: collections.abc.AsyncIterator[T],
        order: int | None = None,
    ) -> tuple[typing.Any, int, T, collections.abc.AsyncIterator[T]]:
        """Create a new item for the heap queue."""
        sort_value = self._key(value) if self._key else value
        if order is None:
            order = random.getrandbits(16)

        return (sort_value, order, value, iterator)

    async def _prepare(self) -> None:
        """Prepare the heap queue by filling it with initial values."""
        coros = (it.__anext__() for it in self.iterators)
        first_values = await asyncio.gather(*coros, return_exceptions=True)

        self._heap = []
        for order, (it, value) in enumerate(zip(self.iterators, first_values)):
            if isinstance(value, BaseException):
                if isinstance(value, StopAsyncIteration):
                    continue

                raise value

            item = self._create_heap_item(value, iterator=it, order=order)
            heapq.heappush(self._heap, item)

        self._prepared = True

    async def __anext__(self) -> T:
        if not self._prepared:
            await self._prepare()

        if not self._heap:
            self._complete()

        if self.limit and self._counter >= self.limit:
            self._complete()

        self._counter += 1

        _, order, value, it = self._heap[0]

        try:
            new_value = await it.__anext__()
        except StopAsyncIteration:
            heapq.heappop(self._heap)
            return value

        heapq.heapreplace(self._heap, self._create_heap_item(new_value, iterator=it, order=order))

        return value

    async def flatten(self, *, lazy: bool = False) -> collections.abc.Sequence[T]:
        """Flatten the paginator."""
        if self.limit is not None and lazy:
            return [item async for item in self]

        coros = (flatten(i) for i in self.iterators)
        lists = await asyncio.gather(*coros)

        return list(heapq.merge(*lists, key=self._key))[: self.limit]


class UniversalPaginator(typing.Generic[T], BufferedPaginator[T]):
    """Paginator for atuyka's universal pages."""

    endpoint: typing.Callable[..., typing.Awaitable[models.Page[T]]]
    _next_params: collections.abc.Mapping[str, typing.Any] | None

    def __init__(
        self,
        endpoint: typing.Callable[..., typing.Awaitable[models.Page[T]]],
        *,
        limit: int | None = None,
    ) -> None:
        super().__init__(limit=limit)
        self.endpoint = endpoint
        self._next_params = {}

    async def next_page(self) -> collections.abc.Iterable[T] | None:
        """Get the next page of the paginator."""
        if self._next_params is None:
            return None

        page = await self.endpoint(**self._next_params)
        self._next_params = page.next
        return page.items


def paginate(callback: typing.Callable[P, typing.Awaitable[models.Page[T]]]) -> typing.Callable[P, Paginator[T]]:
    """Create a paginator from an endpoint."""

    @functools.wraps(callback)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Paginator[T]:
        return UniversalPaginator(functools.partial(callback, *args, **kwargs))

    return wrapper
