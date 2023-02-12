"""Pixiv API models."""
import collections.abc
import datetime
import mimetypes
import re
import typing

import pydantic
import pydantic.generics

from atuyka.services.base import models as base

T = typing.TypeVar("T")


def _to_alt_image(url: str) -> str:
    """Convert a pixiv image URL to an alternative image URL."""
    return "https://api.pixiv.moe/image/" + url.split("//", 1)[1]


class PixivImageURLs(pydantic.BaseModel):
    """A pixiv image URLs."""

    square_medium: str | None
    """The square medium image URL."""
    medium: str
    """The medium image URL."""
    large: str | None
    """The large image URL."""

    def to_universal(self) -> base.Attachment:
        """Convert to a universal attachment URL."""
        urls: dict[str, base.AttachmentURL | None] = {}
        for size, url in [
            ("thumbnail", self.square_medium),
            ("medium", self.medium),
            ("large", self.large),
        ]:
            if url is None:
                urls[size] = None
                continue

            match = re.search(r"(\d+)x(\d+)", url)
            if match:
                width, height = int(match[1]), int(match[2])
            else:
                width, height = None, None

            urls[size] = base.AttachmentURL(
                service="pixiv",
                width=width,
                height=height,
                filename=url.split("/")[-1],
                content_type=mimetypes.guess_type(url)[0],
                url=url,
                alt_url=_to_alt_image(url),
            )

        return base.Attachment(
            service="pixiv",
            thumbnail=urls["thumbnail"],
            medium=urls["medium"],
            large=urls["large"],
            original=urls["large"] or urls["medium"],  # pyright: ignore
        )


class PixivIllustSingleMetaImageURLs(pydantic.BaseModel):
    """A pixiv single meta image URLs."""

    original_image_url: str | None
    """The original image URL."""


class PixivIllustMeta(pydantic.BaseModel):
    """A pixiv illustration meta."""

    image_urls: PixivImageURLs
    """The illustration thumbnail URLs."""


class PixivIllustAuthor(pydantic.BaseModel):
    """A pixiv illust author."""

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

    def to_universal(self) -> base.User:
        """Convert to a universal user."""
        return base.User(
            service="pixiv",
            created_at=None,
            id=str(self.id),
            name=self.name,
            unique_name=self.account,
            url=f"https://www.pixiv.net/users/{self.id}",
            alt_url=f"https://www.pixiv.moe/user/{self.id}",
            avatar=base.Attachment(
                service="pixiv",
                original=base.AttachmentURL(
                    service="pixiv",
                    filename=self.profile_image_urls.medium.split("/")[-1],
                    content_type="image/jpeg",
                    url=self.profile_image_urls.medium,
                    alt_url=_to_alt_image(self.profile_image_urls.medium),
                ),
            ),
            connections=[],  # TODO: Detect connections from mentions
            mentions=[],  # no bio
            tags=[],  # no bio
            following=self.is_followed,
        )


class PixivTag(pydantic.BaseModel):
    """A pixiv tag."""

    name: str
    """The tag name."""
    translated_name: str | None
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
    user: PixivIllustAuthor
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
    series: PixivSeries | None
    """The pixiv series this artwork is part of."""
    meta_single_page: PixivIllustSingleMetaImageURLs | None
    """Metadata for a single image post."""
    meta_pages: collections.abc.Sequence[PixivIllustMeta] | None
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

    def to_universal(self) -> base.Post:
        """Convert the illust to a universal post."""
        if self.meta_pages:
            urls = [meta.image_urls for meta in self.meta_pages]
        else:
            urls = [self.image_urls]

        return base.Post(
            service="pixiv",
            created_at=self.create_date,
            id=str(self.id),
            url=f"https://www.pixiv.net/artworks/{self.id}",
            alt_url=f"https://www.pixiv.moe/illust/{self.id}",
            title=self.title,
            description=self.caption,
            views=self.total_view,
            likes=self.total_bookmarks,
            attachments=[url.to_universal() for url in urls],
            tags=[base.Tag(service="pixiv", name=tag.name, localized_name=tag.translated_name) for tag in self.tags],
            author=self.user.to_universal(),
            connections=[],  # TODO: Detect connections from mentions
            mentions=[base.Mention(url=url) for url in re.findall(r"https?://[^\s]+", self.title + " " + self.caption)],
            nsfw=self.sanity_level > 1,  # TODO: Figure this out precisely
            liked=self.is_bookmarked,
        )


class PixivPaginatedResource(pydantic.generics.GenericModel, typing.Generic[T]):
    """Pixiv paginated resource."""

    illusts: collections.abc.Sequence[T]
    """The illustrations."""
    next_url: str | None
    """The next page URL."""
