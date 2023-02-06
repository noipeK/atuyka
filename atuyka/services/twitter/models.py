"""Twitter API models."""
import collections.abc

import pydantic


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
    """Media ID.""" ""
    id_str: int
    """Media ID as a string.""" ""
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
    features: TwitterMediaEntityFeatures
    """Faces in the media."""


class TweetEntities(pydantic.BaseModel):
    """Entities in a tweet."""

    hashtags: collections.abc.Sequence[TweetHashtag]
    """Hashtags in the tweet."""
    symbols: collections.abc.Sequence[object]
    """Symbols in the tweet."""
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
    duration_millis: int
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
    """Media ID.""" ""
    id_str: int
    """Media ID as a string.""" ""
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
    features: TwitterMediaFeatures
    """Media features."""
    media_key: str
    """IDK."""
    additional_media_info: TwitterMediaExtraInfo | None
    """IDK."""


class TweetExtendedEntities(pydantic.BaseModel):
    """Extended entities in a tweet."""

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
    id_str: int
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


class Tweet(pydantic.BaseModel):
    """A tweet."""

    created_at: str
    """Human-readable creation date of the tweet."""
    id: int
    """The ID of the tweet."""
    id_str: int
    """The ID of the tweet as a string."""
    text: str
    """The content of the tweet."""
    truncated: bool
    """Whether the tweet content is truncated."""
    entities: TweetEntities
    """The special entities of the tweet."""
    extended_entities: TweetExtendedEntities | None
    """Details about the media in the tweet."""
    source: str
    """Source platform of the tweet."""
    in_reply_to_status_id: object | None
    """IDK."""
    in_reply_to_status_id_str: object | None
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
    is_quote_status: bool
    """Whether the tweet is a quote."""
    retweet_count: int
    """Number of retweets."""
    favorite_count: int
    """Number of likes."""
    conversation_id: int
    """Special ID for the conversation."""
    conversation_id_str: int
    """Special ID for the conversation as a string."""
    favorited: bool
    """Whether the tweet is liked by the authenticated user."""
    retweeted: bool
    """Whether the tweet is retweeted by the authenticated user."""
    possibly_sensitive: bool | None
    """Whether the tweet is possibly sensitive."""
    possibly_sensitive_editable: bool | None
    """Whether the tweet sensitivity is not precisely known."""
    lang: str
    """Language of the tweet."""
    supplemental_language: object | None
    """IDK."""


# ====================


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
    """The total number of items in the cursor."""


class UserCursor(Cursor):
    """A cursor of users."""

    users: collections.abc.Sequence[TwitterUser]
    """The users in the cursor."""


# ====================


class TimelineObjects(pydantic.BaseModel):
    """A collection of timeline objects."""

    tweets: collections.abc.Mapping[int, Tweet]
    """Tweets in the timeline."""
    users: collections.abc.Mapping[int, TwitterUser]
    """Users in the timeline."""


class Timeline(pydantic.BaseModel):
    """A timeline summary."""

    globalObjects: TimelineObjects
    """Timeline objects."""
    timeline: object
    """Timeline order."""
