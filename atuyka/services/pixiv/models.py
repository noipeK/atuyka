"""Pixiv API models."""
import collections.abc
import datetime
import typing
import urllib.parse

import pydantic

T = typing.TypeVar("T")


class PixivImageURLs(pydantic.BaseModel):
    """A pixiv image URLs."""

    square_medium: str | None = None
    """The square medium image URL."""
    medium: str
    """The medium image URL."""
    large: str | None = None
    """The large image URL."""


class PixivIllustSingleMetaImageURLs(pydantic.BaseModel):
    """A pixiv single meta image URLs."""

    original_image_url: str | None
    """The original image URL."""


class PixivIllustMeta(pydantic.BaseModel):
    """A pixiv illustration meta."""

    image_urls: PixivImageURLs
    """The illustration thumbnail URLs."""


class PixivUser(pydantic.BaseModel):
    """A pixiv user."""

    id: int
    """The user ID."""
    name: str
    """The user name."""
    account: str
    """The user account name."""
    profile_image_urls: PixivImageURLs
    """The user profile image URLs."""
    is_followed: bool
    """Whether the user is being followed by the authenticated user."""


class PixivTag(pydantic.BaseModel):
    """A pixiv tag."""

    name: str
    """The tag name."""
    translated_name: str | None = None
    """The translated tag name."""


class PixivSeries(pydantic.BaseModel):
    """A pixiv series."""

    id: int
    """The series ID."""
    title: str
    """The series title."""


class PixivIllust(pydantic.BaseModel):
    """A pixiv illustration."""

    id: int
    """The illustration ID."""
    title: str
    """The illustration title."""
    type: str
    """The illustration type."""
    image_urls: PixivImageURLs
    """The illustration thumbnail URLs."""
    caption: str
    """The illustration caption in html."""
    restrict: bool
    """IDK."""
    user: PixivUser
    """The illustration author."""
    tags: collections.abc.Sequence[PixivTag]
    """The illustration tags."""
    tools: collections.abc.Sequence[str]
    """Tools used to create the illustration."""
    create_date: datetime.datetime
    """The post creation date."""
    page_count: int
    """The number of pages in the post."""
    width: int
    """The illustration thumbnail width."""
    height: int
    """The illustration thumbnail height."""
    sanity_level: int
    """IDK."""
    x_restrict: int
    """IDK."""
    series: PixivSeries | None = None
    """The pixiv series this artwork is part of."""
    meta_single_page: PixivIllustSingleMetaImageURLs | None = None
    """Metadata for a single image post."""
    meta_pages: collections.abc.Sequence[PixivIllustMeta] | None = None
    """Metadata for a multi-image post."""
    total_view: int
    """The total number of views."""
    total_bookmarks: int
    """The total number of bookmarks."""
    is_bookmarked: bool
    """Whether the post is bookmarked by the authenticated user."""
    visible: bool
    """IDK."""
    is_muted: bool
    """Whether posts from this user are muted."""
    illust_ai_type: bool
    """IDK."""
    illust_book_style: bool
    """IDK."""


class PixivPaginatedResource(pydantic.BaseModel, typing.Generic[T]):
    """Pixiv paginated resource."""

    illusts: collections.abc.Sequence[T]
    """The illustrations."""
    next_url: str | None
    """The next page URL."""

    @property
    def next_params(self) -> dict[str, str] | None:
        """The next page parameters."""
        if self.next_url is None:
            return None

        return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.next_url).query))
