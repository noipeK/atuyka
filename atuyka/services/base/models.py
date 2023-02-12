"""Universal models."""
import collections.abc
import datetime
import typing

import pydantic

T = typing.TypeVar("T")


class Connection(pydantic.BaseModel):
    """A connection to a different service."""

    service: str | None = None
    """The service name."""

    url: str
    """The service URL."""
    id: str | None = None
    """The target ID."""
    author_id: str | None = None
    """The author of the target ID."""


class Mention(pydantic.BaseModel):
    """A mention of some other resource."""

    url: str
    """The URL of the mentioned resource."""


class AttachmentURL(pydantic.BaseModel):
    """An attachment URL."""

    service: str
    """The service name."""

    width: int | None = None
    """The attachment width."""
    height: int | None = None
    """The attachment height."""
    duration: float | None = None
    """The video duration in seconds."""

    filename: str | None = None
    """The attachment filename."""
    content_type: str | None = None
    """The attachment content type."""

    url: str
    """The original attachment URL."""
    routed_url: str | None = None
    """The relative routed attachment URL."""
    alt_url: str | None = None
    """Link to the attachment on an alternative front-end of the service."""


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

    created_at: datetime.datetime
    """The user creation date."""
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
    connections: collections.abc.Sequence[Connection]
    """The author connections."""
    mentions: collections.abc.Sequence[Mention]
    """The post mentions."""
    tags: collections.abc.Sequence[Tag]
    """The author tags."""
    language: str | None = None
    """The author language."""

    following: bool | None = None
    """Whether the author is being followed by the authenticated user."""


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
    attachments: collections.abc.Sequence[Attachment]
    """The post attachments."""
    tags: collections.abc.Sequence[Tag]
    """The post tags."""
    author: User | None = None
    """The post author."""
    connections: collections.abc.Sequence[Connection]
    """The post connections."""
    mentions: collections.abc.Sequence[Mention]
    """The post mentions."""
    nsfw: bool | None = None
    """Whether the post is NSFW."""
    language: str | None = None
    """The post language."""

    liked: bool | None = None
    """Whether the post is liked by the authenticated user."""


class Page(pydantic.BaseModel, typing.Generic[T]):
    """A page."""

    items: collections.abc.Sequence[T]
    """The item list."""
    total: int | None = None
    """The total amount of items."""
    next: collections.abc.Mapping[str, int | str] | None = None
    """The parameters for the next page."""
