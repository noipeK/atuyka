"""Universal models."""
import collections.abc
import datetime
import mimetypes
import typing
import urllib.parse

import pydantic
import pydantic.generics

from . import client

T = typing.TypeVar("T")


def quote_url(url: str, *, safe: str = "", protocol: bool = True) -> str:
    """Quote a URL."""
    if not protocol:
        url = url.split("://", 1)[1]

    return urllib.parse.quote(url, safe)


def get_filename(url: str) -> str:
    """Get the filename from a URL."""
    return url.split("/")[-1]


class Connection(pydantic.BaseModel):
    """A connection to a different service."""

    service: str
    """The service name."""

    url: str
    """The service URL."""
    user: str | None = None
    """The target user url component."""
    post: str | None = None
    """The target post url component."""


class Mention(pydantic.BaseModel):
    """A mention of some other resource."""

    url: str
    """The URL of the mentioned resource."""

    connection: Connection | None = None
    """The connection to the mentioned resource."""

    @pydantic.root_validator()
    def __set_connection(cls, values: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Set the connection."""
        values["connection"] = client.ServiceClient.parse_connection_url(url=values["url"])

        return values


class AttachmentURL(pydantic.BaseModel):
    """An attachment URL."""

    service: str
    """The service name."""

    width: int | None = None
    """The attachment width. Mostly not reliable, fetch image headers for real values."""
    height: int | None = None
    """The attachment height. Mostly not reliable, fetch image headers for real values."""
    duration: float | None = None
    """The video duration in seconds."""

    filename: str | None = None
    """The attachment filename."""
    content_type: str | None = None
    """The attachment content type."""
    loop: bool = False
    """Whether the video should loop like a GIF."""

    url: str
    """The original attachment URL."""
    alt_url: str | None = None
    """Link to the attachment on an alternative front-end of the service."""

    @pydantic.root_validator()  # pyright: reportUnknownMemberType=false
    def __complete_values(cls, values: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Add the routed URL."""
        values["filename"] = values.get("filename") or get_filename(values["url"])
        values["content_type"] = values.get("content_type") or mimetypes.guess_type(values["url"])[0]

        return values


class Attachment(pydantic.BaseModel):
    """An attachment."""

    service: str
    """The service name."""

    thumbnail: AttachmentURL | None = None
    """The thumbnail attachment URL."""
    small: AttachmentURL | None = None
    """The small attachment URL."""
    medium: AttachmentURL | None = None
    """The medium attachment URL."""
    large: AttachmentURL | None = None
    """The large attachment URL."""
    metadata: AttachmentURL | None = None
    """Extra metadata for the file."""
    original: AttachmentURL
    """The original attachment URL."""


class Tag(pydantic.BaseModel):
    """A post tag."""

    service: str
    """The service name."""

    id: str | None = None
    """The unique tag ID."""
    name: str
    """The tag name."""
    localized_name: str | None = None
    """The localized tag name."""
    description: str | None = None
    """The tag description."""
    localized_description: str | None = None
    """The localized tag description."""
    post_count: int | None = None
    """The amount of posts with this tag."""


class User(pydantic.BaseModel):
    """A post author."""

    service: str
    """The service name."""

    created_at: datetime.datetime | None = None
    """The user creation date."""
    request_id: str
    """ID used for requests. May be derived from the username."""
    id: str
    """The unique author ID."""
    name: str
    """The author name."""
    unique_name: str | None = None
    """The author unique name."""
    bio: str | None = None
    """The author bio."""
    url: str
    """Link to the author on the service."""
    alt_url: str | None = None
    """Link to the author on an alternative front-end of the service."""
    avatar: Attachment | None = None
    """The author avatar URL."""
    banner: Attachment | None = None
    """The author banner URL."""
    followers: int | None = None
    """The amount of followers."""
    connections: collections.abc.Sequence[Connection] = []
    """The author connections."""
    mentions: collections.abc.Sequence[Mention] = []
    """The post mentions."""
    tags: collections.abc.Sequence[Tag] = []
    """The author tags."""
    language: str | None = None
    """The author language."""

    following: bool | None = None
    """Whether the author is being followed by the authenticated user."""


class Comment(pydantic.BaseModel):
    """A post comment."""

    service: str
    """The service name."""

    created_at: datetime.datetime
    """The comment creation date."""
    id: str
    """The unique comment ID."""
    content: str
    """The comment text."""
    url: str
    """Link to the comment on the service."""
    alt_url: str | None = None
    """Link to the comment on an alternative front-end of the service."""
    author: User
    """The comment author."""
    parent_id: str | None = None
    """The parent comment ID."""
    likes: int | None = None
    """The amount of likes."""
    views: int | None = None
    """The amount of views."""
    replies: int | None = None
    """The amount of replies."""
    available_replies: collections.abc.Sequence["Comment"] = []
    """Available replies"""
    mentions: collections.abc.Sequence[Mention] = []
    """The comment mentions."""
    attachments: collections.abc.Sequence[Attachment] = []
    """The post attachments."""
    language: str | None = None
    """The comment language."""

    liked: bool | None = None
    """Whether the comment is liked by the authenticated user."""


class Post(pydantic.BaseModel):
    """A post."""

    service: str
    """The service name."""

    created_at: datetime.datetime
    """The post creation date."""
    id: str
    """The unique post ID."""
    url: str
    """Link to the post on the service."""
    alt_url: str | None = None
    """Link to the post on an alternative front-end of the service."""
    title: str | None = None
    """The post title."""
    description: str | None = None
    """The post description."""
    views: int | None = None
    """The amount of views."""
    likes: int | None = None
    """The amount of likes."""
    comments: int | None = None
    """The amount of comments."""
    attachments: collections.abc.Sequence[Attachment] = []
    """The post attachments."""
    tags: collections.abc.Sequence[Tag] = []
    """The post tags."""
    author: User | None = None
    """The post author."""
    connections: collections.abc.Sequence[Connection] = []
    """The post connections."""
    mentions: collections.abc.Sequence[Mention] = []
    """The post mentions."""
    comment_previews: collections.abc.Sequence[Comment] = []
    """The post comment previews."""
    captioned_post: "Post | None" = None
    """The post that is being captioned."""
    nsfw: bool | None = None
    """Whether the post is NSFW."""
    language: str | None = None
    """The post language."""

    liked: bool | None = None
    """Whether the post is liked by the authenticated user."""


class Page(pydantic.generics.GenericModel, typing.Generic[T]):
    """A page."""

    items: collections.abc.Sequence[T] = []
    """The item list."""
    total: int | None = None
    """The total amount of items."""
    remaining: int | None = None
    """The remaining amount of items."""
    next: collections.abc.Mapping[str, str] | None = None
    """The parameters for the next page."""
