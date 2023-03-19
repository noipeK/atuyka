"""Twitter API models."""
from __future__ import annotations

import collections.abc
import datetime
import re
import typing
import warnings

import pydantic

from atuyka.services.base import models as base

T = typing.TypeVar("T")


class TweetHashtag(pydantic.BaseModel):
    """Hashtag in the tweet."""

    text: str
    """Hashtag text."""
    indices: tuple[int, int]
    """Position of the hashtag in the tweet."""


class TweetUserMention(pydantic.BaseModel):
    """User mention in the tweet."""

    screen_name: str
    """Screen name of the user mentioned."""
    name: str
    """Name of the user mentioned."""
    id: int
    """ID of the user mentioned."""
    id_str: int
    """ID of the user mentioned as a string."""
    indices: tuple[int, int]
    """Position of the user mention in the tweet."""


class TweetURL(pydantic.BaseModel):
    """URL in the tweet."""

    url: str
    """URL."""
    expanded_url: str
    """Real URL."""
    display_url: str
    """Shortened URL."""
    indices: tuple[int, int]
    """Position of the URL in the tweet."""


class TwitterMediaSize(pydantic.BaseModel):
    """Size of media."""

    w: int
    """Width of the media."""
    h: int
    """Height of the media."""
    resize: str
    """Resize method."""


class TwitterMediaRect(pydantic.BaseModel):
    """Rect of media."""

    x: int
    """X position of the rect."""
    y: int
    """Y position of the rect."""
    h: int
    """Height of the rect."""
    w: int
    """Width of the rect."""


class TwitterMediaSizeWithRect(pydantic.BaseModel):
    """Size of media with a rect."""

    width: int
    """Width of the media."""
    height: int
    """Height of the media."""
    focus_rects: collections.abc.Sequence[TwitterMediaRect] | None
    """IDK."""


class TwitterMediaSizes(pydantic.BaseModel):
    """Available sizes of the media."""

    thumb: TwitterMediaSize
    """Size of the thumbnail media."""
    small: TwitterMediaSize
    """Size of the small media."""
    large: TwitterMediaSize
    """Size of the large media."""
    medium: TwitterMediaSize
    """Size of the medium media."""


class TwitterMediaFaces(pydantic.BaseModel):
    """Faces in the media."""

    faces: collections.abc.Sequence[TwitterMediaRect] = []
    """Faces in the media."""


class TwitterMediaEntityFeatures(pydantic.BaseModel):
    """Faces in the media."""

    all: TwitterMediaFaces | None
    """Faces in all media."""
    small: TwitterMediaFaces | None
    """Faces in small media."""
    medium: TwitterMediaFaces | None
    """Faces in medium media."""
    large: TwitterMediaFaces | None
    """Faces in large media."""
    orig: TwitterMediaFaces | None
    """Faces in original media."""


class TwitterMediaEntity(pydantic.BaseModel):
    """Media in the tweet."""

    id: int
    """Media ID."""
    id_str: int
    """Media ID as a string."""
    indices: tuple[int, int]
    """Position of the media in the entity."""
    media_url: str
    """Media thumbnail."""
    media_url_https: str
    """Media thumbnail."""
    url: str
    """Twitter proxy url."""
    display_url: str
    """Shortened URL."""
    expanded_url: str
    """Real URL."""
    type: str
    """Media type."""
    original_info: TwitterMediaSizeWithRect
    """Sizes of the original media."""
    sizes: TwitterMediaSizes
    """Sizes of the media."""
    features: TwitterMediaEntityFeatures | None
    """Faces in the media."""

    def to_universal(self) -> base.Attachment:
        """Convert to universal attachment."""
        # TODO: deduplicate code
        if self.type == "photo":
            filename = self.media_url_https.split("/")[-1]

            attachment_urls: dict[str, base.AttachmentURL] = {}
            for size in ("thumb", "small", "medium", "large"):
                size_name = {"thumb": "thumbnail"}.get(size, size)
                url = self.media_url_https + ":" + size
                attachment_urls[size_name] = base.AttachmentURL(
                    service="twitter",
                    width=self.sizes.__getattribute__(size).w,
                    height=self.sizes.__getattribute__(size).h,
                    filename=filename,
                    url=url,
                    alt_url=f"https://nitter.net/pic/orig/media%2F{filename}:{size}",
                )

            url = self.media_url_https + ":orig"
            attachment_urls["original"] = base.AttachmentURL(
                service="twitter",
                width=self.original_info.width,
                height=self.original_info.height,
                filename=filename,
                url=url,
                alt_url=f"https://nitter.net/pic/orig/media%2F{filename}:orig",
            )

            return base.Attachment(
                service="twitter",
                thumbnail=attachment_urls["thumbnail"],
                small=attachment_urls["small"],
                medium=attachment_urls["medium"],
                large=attachment_urls["large"],
                original=attachment_urls["original"],
            )

        warnings.warn(f"Unknown twitter media entity type: {self.type}", stacklevel=2)
        return base.Attachment(
            service="twitter",
            original=base.AttachmentURL(
                service="twitter",
                url=self.media_url_https,
            ),
        )


class TweetEntities(pydantic.BaseModel):
    """Entities in a tweet."""

    hashtags: collections.abc.Sequence[TweetHashtag]
    """Hashtags in the tweet."""
    symbols: collections.abc.Sequence[object]
    """IDK."""
    user_mentions: collections.abc.Sequence[TweetUserMention]
    """User mentions in the tweet."""
    urls: collections.abc.Sequence[TweetURL]
    """URLs in the tweet."""
    media: collections.abc.Sequence[TwitterMediaEntity] | None
    """Media in the tweet."""


class TwitterVideoVariant(pydantic.BaseModel):
    """Video variant info."""

    bitrate: int | None
    """Bitrate of the video variant."""
    content_type: str
    """Content type of the video variant."""
    url: str
    """URL of the video variant."""


class TwitterVideoInfo(pydantic.BaseModel):
    """Video info."""

    aspect_ratio: tuple[int, int]
    """Aspect ratio of the video."""
    duration_millis: int | None
    """Duration of the video in milliseconds."""
    variants: collections.abc.Sequence[TwitterVideoVariant]
    """Variants of the video."""


class TwitterMediaTag(pydantic.BaseModel):
    """Twitter tag in the media."""

    type: str
    """Type of thing tagged."""
    user_id: int
    """ID of the user tagged."""
    screen_name: str
    """Screen name of the user tagged."""
    name: str
    """Name of the user tagged."""


class TwitterMediaTags(pydantic.BaseModel):
    """Twitter tags in the media."""

    tags: collections.abc.Sequence[TwitterMediaTag] = []
    """Twitter tags."""


class TwitterMediaFeatures(pydantic.BaseModel):
    """Twitter tags in the media."""

    all: TwitterMediaTags | None
    """Tags in all media."""
    small: TwitterMediaTags | None
    """Tags in small media."""
    medium: TwitterMediaTags | None
    """Tags in medium media."""
    large: TwitterMediaTags | None
    """Tags in large media."""
    orig: TwitterMediaTags | None
    """Tags in original media."""


class TwitterMediaExtraInfo(pydantic.BaseModel):
    """Extra info about the media."""

    monetizable: bool
    """IDK."""


class TwitterMedia(pydantic.BaseModel):
    """Media in a tweet."""

    id: int
    """Media ID."""
    id_str: int
    """Media ID as a string."""
    indices: tuple[int, int]
    """Position of the media in the entity."""
    media_url: str
    """Media thumbnail."""
    media_url_https: str
    """Media thumbnail."""
    url: str
    """Twitter proxy url."""
    display_url: str
    """Shortened URL."""
    expanded_url: str
    """Real URL."""
    type: str
    """Media type."""
    original_info: TwitterMediaSizeWithRect
    """Sizes of the original media."""
    sizes: TwitterMediaSizes
    """Sizes of the media."""
    video_info: TwitterVideoInfo | None
    """IDK."""
    features: TwitterMediaFeatures | None
    """Media features."""
    media_key: str
    """IDK."""
    additional_media_info: TwitterMediaExtraInfo | None
    """IDK."""

    def to_universal(self) -> base.Attachment:
        """Convert to universal attachment."""
        if self.type == "photo":
            filename = self.media_url_https.split("/")[-1]

            attachment_urls: dict[str, base.AttachmentURL] = {}
            for size in ("thumb", "small", "medium", "large"):
                size_name = {"thumb": "thumbnail"}.get(size, size)
                url = self.media_url_https + ":" + size
                attachment_urls[size_name] = base.AttachmentURL(
                    service="twitter",
                    width=self.sizes.__getattribute__(size).w,
                    height=self.sizes.__getattribute__(size).h,
                    filename=filename,
                    url=url,
                    alt_url=f"https://nitter.net/pic/orig/media%2F{filename}:{size}",
                )

            url = self.media_url_https + ":orig"
            attachment_urls["original"] = base.AttachmentURL(
                service="twitter",
                width=self.original_info.width,
                height=self.original_info.height,
                filename=filename,
                url=url,
                alt_url=f"https://nitter.net/pic/orig/media%2F{filename}:orig",
            )

            return base.Attachment(
                service="twitter",
                thumbnail=attachment_urls["thumbnail"],
                small=attachment_urls["small"],
                medium=attachment_urls["medium"],
                large=attachment_urls["large"],
                original=attachment_urls["original"],
            )

        if self.type == "video":
            assert self.video_info
            attachment_urls: dict[str, base.AttachmentURL] = {}
            variants = sorted(self.video_info.variants, key=lambda v: v.bitrate or 0)
            for size, variant in zip(("m3u8", "small", "medium", "large"), variants):
                filename = variant.url.rsplit("?", 1)[0].split("/")[-1]
                if size == "m3u8":
                    attachment_urls["metadata"] = base.AttachmentURL(
                        service="twitter",
                        filename=filename,
                        content_type=variant.content_type,
                        url=variant.url,
                        # nitter requires the hash which we don't have
                    )
                else:
                    attachment_urls[size] = base.AttachmentURL(
                        service="twitter",
                        width=self.sizes.__getattribute__(size).w,
                        height=self.sizes.__getattribute__(size).h,
                        duration=self.video_info.duration_millis and self.video_info.duration_millis / 1000,
                        filename=filename,
                        content_type=variant.content_type,
                        url=variant.url,
                        alt_url=f"https://nitter.net/video/{filename.split('.')[0].upper()}/{base.quote_url(variant.url)}",
                    )

            attachment_urls["thumbnail"] = base.AttachmentURL(
                service="twitter",
                width=self.sizes.thumb.w,
                height=self.sizes.thumb.h,
                filename=self.media_url_https.split("/")[-1],
                url=self.media_url_https,
                alt_url=f"https://nitter.net/pic/{base.quote_url(self.media_url_https.split('com/', 1)[1])}",
            )

            return base.Attachment(
                service="twitter",
                thumbnail=attachment_urls["thumbnail"],
                small=attachment_urls["small"],
                medium=attachment_urls["medium"],
                large=attachment_urls["large"],
                metadata=attachment_urls["metadata"],
                original=attachment_urls["large"],
            )

        if self.type == "animated_gif":
            assert self.video_info
            attachment_urls: dict[str, base.AttachmentURL] = {}
            variant = self.video_info.variants[0]

            attachment_urls["thumbnail"] = base.AttachmentURL(
                service="twitter",
                width=self.sizes.thumb.w,
                height=self.sizes.thumb.h,
                filename=self.media_url_https.split("/")[-1],
                url=self.media_url_https,
                alt_url=f"https://nitter.net/pic/{base.quote_url(self.media_url_https.split('com/', 1)[1])}",
            )

            attachment_urls["original"] = base.AttachmentURL(
                service="twitter",
                width=self.sizes.large.w,
                height=self.sizes.large.h,
                filename=base.get_filename(variant.url),
                content_type=variant.content_type,
                loop=True,
                url=variant.url,
                alt_url=f"https://nitter.net/pic/{base.quote_url(self.media_url_https.split('com/', 1)[1])}",
            )

            return base.Attachment(
                service="twitter",
                thumbnail=attachment_urls["thumbnail"],
                original=attachment_urls["original"],
            )

        warnings.warn(f"Unknown twitter media type: {self.type}", stacklevel=2)
        return base.Attachment(
            service="twitter",
            original=base.AttachmentURL(
                service="twitter",
                url=self.media_url_https,
            ),
        )


class TweetExtendedEntities(pydantic.BaseModel):
    """Extended entities in a tweet directly uploaded to twitter."""

    media: collections.abc.Sequence[TwitterMedia]
    """Media entities."""


class TwitterURLEntity(pydantic.BaseModel):
    """A URL entity."""

    url: str
    """Twitter proxy URL."""
    expanded_url: str
    """Real URL."""
    display_url: str
    """Shortened URL."""
    indices: tuple[int, int]
    """Position of the URL in the entity."""


class TwitterURLableEntity(pydantic.BaseModel):
    """An entity that can contain URLs."""

    urls: collections.abc.Sequence[TwitterURLEntity]
    """URLs in the entity."""


class TwitterUserEntities(pydantic.BaseModel):
    """The entities in a Twitter user profile."""

    url: TwitterURLableEntity | None
    """URL details."""
    description: TwitterURLableEntity
    """Description details."""


class TwitterUser(pydantic.BaseModel):
    """A Twitter user."""

    id: int
    """The ID of the user."""
    id_str: str
    """The ID of the user as a string."""
    name: str
    """The name of the user."""
    screen_name: str
    """The screen name of the user that appears in their url."""
    location: str
    """The location of the user."""
    description: str
    """The description of the user."""
    url: str | None
    """The website of the user."""
    entities: TwitterUserEntities
    """The entities on the user."""
    protected: bool
    """Whether the account is protected."""
    followers_count: int
    """The number of followers the user has."""
    fast_followers_count: int
    """IDK."""
    normal_followers_count: int
    """The number of followers the user has."""
    friends_count: int
    """The number of people the user is following."""
    listed_count: int
    """IDK."""
    created_at: str
    """Human-readable date of when the account was created."""
    favourites_count: int
    """The number of likes the user has."""
    utc_offset: object | None
    """IDK."""
    time_zone: object | None
    """IDK."""
    geo_enabled: bool
    """IDK."""
    verified: bool
    """Whether the account is verified."""
    statuses_count: int
    """The number of tweets the user has."""
    media_count: int
    """The number of media the user has posted."""
    lang: object | None
    """IDK."""
    status: Tweet | None
    """The pinned tweet."""
    contributors_enabled: bool
    """IDK."""
    is_translator: bool
    """IDK."""
    is_translation_enabled: bool
    """IDK."""
    profile_background_color: str
    """The background theme color of the user's profile."""
    profile_background_image_url: str | None
    """The background theme image of the user's profile."""
    profile_background_image_url_https: str | None
    """The background theme image of the user's profile."""
    profile_background_tile: bool
    """IDK."""
    profile_image_url: str
    """The profile image of the user."""
    profile_image_url_https: str
    """The profile image of the user."""
    profile_banner_url: str | None
    """The profile banner of the user."""
    profile_link_color: str
    """The link color of the user's profile."""
    profile_sidebar_border_color: str
    """IDK."""
    profile_sidebar_fill_color: str
    """IDK."""
    profile_text_color: str
    """IDK."""
    profile_use_background_image: bool
    """IDK."""
    has_extended_profile: bool
    """IDK."""
    default_profile: bool
    """IDK."""
    default_profile_image: bool
    """IDK."""
    pinned_tweet_ids: collections.abc.Sequence[int] | None
    """The IDs of the pinned tweets."""
    pinned_tweet_ids_str: collections.abc.Sequence[int] | None
    """The IDs of the pinned tweets as strings."""
    has_custom_timelines: bool
    """IDK."""
    can_media_tag: bool | None
    """IDK."""
    followed_by: bool | None
    """Whether the authenticated user is followed by the user."""
    following: bool | None
    """Whether the authenticated user is following the user."""
    follow_request_sent: bool | None
    """Whether the authenticated user has sent a follow request to the user."""
    notifications: bool | None
    """IDK."""
    advertiser_account_type: str | None
    """IDK."""
    advertiser_account_service_levels: collections.abc.Sequence[str] | None
    """IDK."""
    business_profile_state: str
    """IDK."""
    translator_type: str
    """IDK."""
    withheld_in_countries: collections.abc.Sequence[object]
    """IDK."""
    require_some_consent: bool
    """IDK."""

    def to_universal(self) -> base.User:
        """Convert the Twitter user to a universal user."""
        urls = {url.url: url.expanded_url for url in self.entities.description.urls}
        bio = re.sub(r"https://t.co/\w+", lambda m: urls.get(m[0], m[0]), self.description)

        avatar_urls: dict[str, base.AttachmentURL] = {}
        for size, name, width in [
            ("mini", "small", 24),
            ("normal", "medium", 48),
            ("bigger", "large", 73),
            ("", "original", None),
        ]:
            url = self.profile_image_url_https.replace("_normal", f"_{size}" if size else "")
            avatar_urls[name] = base.AttachmentURL(
                service="twitter",
                width=width,
                height=width,
                filename=url.split("/")[-1],
                url=url,
                alt_url=f"https://nitter.net/pic/{base.quote_url(url, protocol=False)}",
            )

        banner_urls: dict[str, base.AttachmentURL] = {}
        if self.profile_banner_url:
            for name, width, height in [
                ("small", 300, 100),
                ("medium", 600, 200),
                ("large", 1500, 500),
            ]:
                url = self.profile_banner_url + f"/{width}x{height}"
                banner_urls[name] = base.AttachmentURL(
                    service="twitter",
                    width=width,
                    height=height,
                    filename=url.split("/")[-2] + ".jpg",
                    url=url,
                    alt_url=f"https://nitter.net/pic/{base.quote_url(url)}",
                )

        mentioned_urls: list[str] = []
        if self.entities.description:
            for url in self.entities.description.urls:
                mentioned_urls.append(url.expanded_url)

        return base.User(
            service="twitter",
            created_at=datetime.datetime.fromtimestamp(
                ((self.id >> 22) + 1288834974657) / 1000,
                tz=datetime.timezone.utc,
            ),
            id=self.id_str,
            name=self.name,
            unique_name=self.screen_name,
            bio=bio,
            url=f"https://twitter.com/{self.screen_name}",
            alt_url=f"https://nitter.net/{self.screen_name}",
            avatar=base.Attachment(
                service="twitter",
                small=avatar_urls["small"],
                medium=avatar_urls["medium"],
                large=avatar_urls["large"],
                original=avatar_urls["original"],
            ),
            banner=base.Attachment(
                service="twitter",
                small=banner_urls["small"],
                medium=banner_urls["medium"],
                large=banner_urls["large"],
                original=banner_urls["large"],  # likely not stored
            )
            if banner_urls
            else None,
            followers=self.followers_count,
            connections=[],  # TODO: Detect connections from mentions
            mentions=[base.Mention(url=url) for url in mentioned_urls],
            tags=[base.Tag(service="twitter", name=hashtag) for hashtag in re.findall(r"#(\w+)", self.description)],
            language=None,  # TODO
            following=self.following,
        )


class Tweet(pydantic.BaseModel):
    """A tweet."""

    created_at: str
    """Human-readable creation date of the tweet."""
    id: int
    """The ID of the tweet."""
    id_str: str
    """The ID of the tweet as a string."""
    full_text: str
    """The content of the tweet."""
    truncated: bool
    """Whether the tweet content is truncated."""
    display_text_range: tuple[int, int]
    """The range of the tweet content that is displayed in compact mode."""
    entities: TweetEntities
    """The special entities of the tweet."""
    extended_entities: TweetExtendedEntities | None
    """Details about the media in the tweet."""
    source: str
    """Which platform this tweet was made from."""
    in_reply_to_status_id: int | None
    """IDK."""
    in_reply_to_status_id_str: str | None
    """IDK."""
    in_reply_to_user_id: object | None
    """IDK."""
    in_reply_to_user_id_str: object | None
    """IDK."""
    in_reply_to_screen_name: object | None
    """IDK."""
    user: TwitterUser | None
    """The user who posted the tweet."""
    geo: object | None
    """IDK."""
    coordinates: object | None
    """IDK."""
    place: object | None
    """IDK."""
    contributors: object | None
    """IDK."""
    retweeted_status: Tweet | None
    """The original tweet if this is a retweet."""
    is_quote_status: bool
    """Whether the tweet is a quote."""
    retweet_count: int
    """Number of retweets."""
    favorite_count: int
    """Number of likes."""
    conversation_id: int | None
    """Special ID for the conversation. None if a status."""
    conversation_id_str: int | None
    """Special ID for the conversation as a string. None if a status."""
    favorited: bool
    """Whether the tweet is liked by the authenticated user."""
    retweeted: bool
    """Whether the tweet is retweeted by the authenticated user."""
    possibly_sensitive: bool | None
    """Whether the tweet is possibly sensitive."""
    possibly_sensitive_editable: bool | None
    """IDK."""
    lang: str
    """Language of the tweet."""
    supplemental_language: object | None
    """IDK."""

    def to_universal(self) -> base.Post:
        """Convert the tweet to a post."""
        assert self.user

        urls = {url.url: url.expanded_url for url in self.entities.urls}
        text = re.sub(r"https://t.co/\w+", lambda m: urls.get(m[0], m[0]), self.full_text)

        found_urls: list[str] = []
        attachments: list[base.Attachment] = []
        if self.extended_entities and self.extended_entities.media:
            # attached media
            for media in self.extended_entities.media:
                found_urls.append(media.url)
                attachments.append(media.to_universal())

        if self.entities.media:
            # links to the media
            for media in self.entities.media:
                # attached, no need for less info
                if media.url in found_urls:
                    continue
                # thumbnail to an extended entity
                if "http://pbs.twimg.com/ext_tw_video_thumb" in media.media_url:
                    continue

                attachments.append(media.to_universal())

        return base.Post(
            service="twitter",
            created_at=datetime.datetime.fromtimestamp(
                ((self.id >> 22) + 1288834974657) / 1000,
                tz=datetime.timezone.utc,
            ),
            id=self.id_str,
            url=f"https://twitter.com/{self.user.screen_name}/status/{self.id_str}",
            alt_url=f"https://nitter.net/{self.user.screen_name}/status/{self.id_str}",
            description=text,
            likes=self.favorite_count,
            attachments=attachments,
            tags=[base.Tag(service="twitter", name=hashtag.text) for hashtag in self.entities.hashtags],
            author=self.user.to_universal(),
            connections=[],  # TODO: No viable connections to Twitter posts
            mentions=[base.Mention(url=url.expanded_url) for url in self.entities.urls],
            captioned_post=self.retweeted_status.to_universal() if self.retweeted_status else None,
            nsfw=self.possibly_sensitive or None,
            language=self.lang,
            liked=self.favorited,
        )


# ====================


class SearchMetadata(pydantic.BaseModel):
    """Metadata about a search result."""

    completed_in: float
    """The number of seconds it took to complete the search."""
    max_id: int
    """The maximum ID of the tweets in the search result."""
    max_id_str: str
    """The maximum ID of the tweets in the search result as a string."""
    next_results: str | None
    """The URL to the next page of results."""
    query: str
    """The query used to search."""
    refresh_url: str
    """The URL to refresh the search."""
    count: int
    """The number of tweets in the search result."""
    since_id: int
    """The minimum ID of the tweets in the search result."""
    since_id_str: str
    """The minimum ID of the tweets in the search result as a string."""


class SearchResult(pydantic.BaseModel):
    """A search result."""

    statuses: list[Tweet]
    """The tweets in the search result."""
    search_metadata: SearchMetadata
    """Metadata about the search result."""

    def to_universal(self) -> base.Page[base.Post]:
        """Convert the search result to a universal search result."""
        n = dict(max_id=self.search_metadata.max_id_str) if self.search_metadata.next_results else None
        return base.Page(
            items=[item.to_universal() for item in self.statuses],
            next=n,
        )


class Cursor(pydantic.BaseModel):
    """A cursor."""

    next_cursor: int
    """The next cursor."""
    next_cursor_str: str
    """The next cursor as a string."""
    previous_cursor: int
    """The previous cursor."""
    previous_cursor_str: str
    """The previous cursor as a string."""
    total_count: int | None
    """The total number of items left in the cursor."""

    def _to_universal(self, items: collections.abc.Sequence[T]) -> base.Page[T]:
        """Convert the cursor to a universal cursor."""
        return base.Page(
            items=items,
            remaining=self.total_count,
            next={"cursor": str(self.next_cursor)} if self.next_cursor else None,
        )


class UserCursor(Cursor):
    """A cursor of users."""

    users: collections.abc.Sequence[TwitterUser]
    """The users in the cursor."""

    def to_universal(self) -> base.Page[base.User]:
        """Convert the cursor to a universal cursor."""
        return self._to_universal([user.to_universal() for user in self.users])


# ====================


class TimelineObjects(pydantic.BaseModel):
    """A collection of timeline objects."""

    tweets: collections.abc.Mapping[int, Tweet]
    """Tweets in the timeline."""
    users: collections.abc.Mapping[int, TwitterUser]
    """Users in the timeline."""


class Timeline(pydantic.BaseModel):
    """A timeline summary."""

    globalObjects: TimelineObjects  # noqa: N815
    """Timeline objects."""
    timeline: object
    """Timeline order."""


TwitterUser.update_forward_refs()
