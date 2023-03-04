"""Timed cache."""
from __future__ import annotations

import collections.abc
import time
import typing

__all__ = ["Cache"]

T = typing.TypeVar("T")
KT = typing.TypeVar("KT")
VT = typing.TypeVar("VT")

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
WEEK = DAY * 7


class Cache(typing.Generic[KT, VT], collections.abc.MutableMapping[KT, VT]):
    """Timed cache."""

    cache: dict[KT, tuple[float, VT]]
    maxsize: int
    ttl: float

    def __init__(self, maxsize: int = 1024, *, ttl: float = HOUR) -> None:
        self.cache = {}
        self.maxsize = maxsize

        self.ttl = ttl

    def _clear_cache(self) -> None:
        """Clear timed-out items."""
        # since this is always called from an async function we don't need locks
        now = time.time()

        for key, value in self.cache.copy().items():
            if value[0] < now:
                del self.cache[key]

        if len(self.cache) > self.maxsize:
            overflow = len(self.cache) - self.maxsize
            oldest_keys = list(self.cache.keys())[:overflow]

            for key in oldest_keys:
                del self.cache[key]

    def get(self, key: KT, default: T = ...) -> VT | T:
        """Get an object with a key."""
        self._clear_cache()

        if key not in self.cache:
            if default is ...:
                raise KeyError(key)

            return default

        return self.cache[key][1]

    def set(self, key: typing.Any, value: typing.Any, *, ttl: float | None = None) -> None:
        """Save an object with a key."""
        if key in self.cache:
            del self.cache[key]  # ordering matters for maxsize

        self.cache[key] = (time.time() + (ttl or self.ttl), value)

        self._clear_cache()

    def pop(self, key: KT, default: T = ...) -> VT | T:
        """Pop an object with a key."""
        self._clear_cache()

        if key not in self.cache:
            if default is ...:
                raise KeyError(key)

            return default

        return self.cache.pop(key)[1]

    def bump(self, key: KT, *, ttl: float | None = None) -> None:
        """Bump the TTL of an object."""
        self.set(key, self.get(key), ttl=ttl)

        self._clear_cache()

    def __getitem__(self, key: KT) -> VT:
        return self.get(key)

    def __setitem__(self, key: KT, value: VT) -> None:
        self.set(key, value)

    def __delitem__(self, key: KT) -> None:
        del self.cache[key]

    def __len__(self) -> int:
        self._clear_cache()
        return len(self.cache)

    def __iter__(self) -> typing.Iterator[KT]:
        self._clear_cache()
        return iter(self.cache)

    def __repr__(self) -> str:
        return f"Cache(maxsize={self.maxsize!r}, ttl={self.ttl!r})"
