"""Pixiv API models."""
import collections.abc
import datetime
import re
import typing

import pydantic
import pydantic.generics
from pixivpy_async.utils import Utils as pixivpy_utils  # noqa: N813 # pyright: ignore[reportUnknownVariableType]

from atuyka.services.base import models as base

T = typing.TypeVar("T")


def _to_alt_image(url: str) -> str:
    """Convert a pixiv image URL to an alternative image URL."""
    return "https://api.pixiv.moe/image/" + url.split("//", 1)[1]


class PixivImageURLs(pydantic.BaseModel):
    """A pixiv image URLs."""

    square_medium: str
    """The square medium image URL."""
    medium: str
    """The medium image URL."""
    large: str
    """The large image URL."""

    def to_universal(self) -> base.Attachment:
        """Convert to a universal attachment URL."""
        # TODO: implement videos

        # https://i.pximg.net/img-original/img/2017/04/05/00/00/02/62258773_p0.png
        # img/2017/04/05/00/00/02/62258773_p0
        match = re.search(r"img(?:/\d+){6}/\d+(?:_p(\d+))?", self.medium)
        assert match, self.medium
        substring = match[0]

        urls: dict[str, base.AttachmentURL] = {}
        for size, (width, height), template in [
            ("thumbnail", (540, 540), "https://i.pximg.net/c/540x540_10_webp/img-master/{}_square1200.jpg"),
            ("small", (540, 540), "https://i.pximg.net/c/540x540_70/img-master/{}_master1200.jpg"),
            ("medium", (600, None), "https://i.pximg.net/c/600x1200_90_webp/img-master/{}_master1200.jpg"),
            ("large", (None, 1200), "https://i.pximg.net/img-master/{}_master1200.jpg"),
            ("original", (None, None), "https://i.pximg.net/img-original/{}.jpg"),
        ]:
            url = template.format(substring)
            urls[size] = base.AttachmentURL(
                service="pixiv",
                width=width,
                height=height,
                url=url,
                alt_url=_to_alt_image(url),
            )

        return base.Attachment(
            service="pixiv",
            thumbnail=urls["thumbnail"],
            small=urls["small"],
            medium=urls["medium"],
            large=urls["large"],
            original=urls["original"],
        )


class PixivProfileImageURLs(pydantic.BaseModel):
    """A pixiv profile image URLs."""

    medium: str
    """The medium image URL."""

    def to_universal(self) -> base.Attachment:
        """Convert to a universal attachment URL."""
        if "no_profile" in self.medium:
            return base.Attachment(
                service="pixiv",
                original=base.AttachmentURL(
                    service="pixiv",
                    width=170,
                    height=170,
                    url=self.medium,
                    alt_url=None,  # pixiv.moe doesn't proxy this
                ),
            )

        return base.Attachment(
            service="pixiv",
            small=base.AttachmentURL(
                service="pixiv",
                width=50,
                height=50,
                url=self.medium.replace("_170", "_50"),
                alt_url=_to_alt_image(self.medium.replace("_170", "_50")),
            ),
            medium=base.AttachmentURL(
                service="pixiv",
                width=170,
                height=170,
                url=self.medium,
                alt_url=_to_alt_image(self.medium),
            ),
            original=base.AttachmentURL(
                service="pixiv",
                url=self.medium.replace("_170", ""),
                alt_url=_to_alt_image(self.medium.replace("_170", "")),
            ),
        )


class PixivIllustSingleMetaImageURLs(pydantic.BaseModel):
    """A pixiv single meta image URLs."""

    original_image_url: str | None
    """The original image URL."""


class PixivIllustMeta(pydantic.BaseModel):
    """A pixiv illustration meta."""

    image_urls: PixivImageURLs
    """The illustration thumbnail URLs."""


class PixivUser(pydantic.BaseModel):
    """A pixiv illust author."""

    id: int
    """The user ID."""
    name: str
    """The user name."""
    account: str
    """The user account name."""
    profile_image_urls: PixivProfileImageURLs
    """The user profile image URLs."""
    comment: str | None
    """The user bio. Only in user details."""
    is_followed: bool | None
    """Whether the user is being followed by the authenticated user. Not present in comments."""
    is_access_blocking_user: bool | None
    """Whether the authenticated user blocked this user. Only in user details."""

    def to_universal(self) -> base.User:
        """Convert to a universal user."""
        return base.User(
            service="pixiv",
            request_id=str(self.id),
            id=str(self.id),
            name=self.name,
            unique_name=self.account,
            url=f"https://www.pixiv.net/users/{self.id}",
            alt_url=f"https://www.pixiv.moe/user/{self.id}",
            avatar=self.profile_image_urls.to_universal(),
            connections=[],  # TODO: Detect connections from mentions
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


class PixivComment(pydantic.BaseModel):
    """A pixiv comment."""

    id: int
    """The comment ID."""
    comment: str
    """The comment text."""
    date: datetime.datetime
    """The comment creation date."""
    user: PixivUser
    """The comment author."""
    parent_comment: "PixivComment | None"
    """The parent comment, if any."""

    @pydantic.validator("parent_comment", pre=True)
    def __remove_empty_dict(cls, v: dict[str, object]) -> object:
        return v or None

    def to_universal(self) -> base.Comment:
        """Convert to a universal comment."""
        return base.Comment(
            service="pixiv",
            id=str(self.id),
            created_at=self.date,
            content=self.comment,
            url="https://www.pixiv.net/",
            author=self.user.to_universal(),
            parent_id=str(self.parent_comment.id) if self.parent_comment else None,
        )


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
        if self.meta_pages:  # noqa: SIM108  # ternary is weird here
            urls = [meta.image_urls for meta in self.meta_pages]
        else:
            urls = [self.image_urls]

        mentions: list[str] = []
        caption = re.sub(r"<br\s+?\/>", "\n", self.caption, flags=re.DOTALL)
        caption = re.sub(
            r'<a.*?href="(.+?)".*?>(.+?)<\/a>',
            lambda m: mentions.append(m[1]) or m[1],
            caption,
            flags=re.DOTALL,
        )

        return base.Post(
            service="pixiv",
            created_at=self.create_date,
            id=str(self.id),
            url=f"https://www.pixiv.net/artworks/{self.id}",
            alt_url=f"https://www.pixiv.moe/illust/{self.id}",
            title=self.title,
            description=caption,
            views=self.total_view,
            likes=self.total_bookmarks,
            attachments=[url.to_universal() for url in urls],
            tags=[base.Tag(service="pixiv", name=tag.name, localized_name=tag.translated_name) for tag in self.tags],
            author=self.user.to_universal(),
            connections=[],  # TODO: Detect connections from mentions
            mentions=[base.Mention(url=url) for url in mentions],
            nsfw=self.sanity_level > 4,  # TODO: Figure this out precisely
            liked=self.is_bookmarked,
        )


class PixivProfile(pydantic.BaseModel):
    """A pixiv user profile."""

    webpage: str | None
    """URL to the user's website."""
    gender: str
    """The user's gender."""
    birth: str
    """The user's birth date."""
    region: str
    """The user's region."""
    job: str
    """The user's job."""
    total_follow_users: int
    """The total number of users following the user."""
    total_mypixiv_users: int
    """IDK."""
    total_illusts: int
    """The total number of illustrations the user has posted."""
    total_manga: int
    """The total number of manga the user has posted."""
    total_novels: int
    """The total number of novels the user has posted."""
    total_illust_bookmarks_public: int
    """The total number of public bookmarks the user has received."""
    background_image_url: str | None
    """The user's background image URL."""
    twitter_account: str | None
    """The user's twitter account."""
    twitter_url: str | None
    """The user's twitter URL."""
    is_premium: bool
    """Whether the user is a premium user."""

    def background_image_to_universal(self) -> base.Attachment | None:
        """Convert the background image to a universal image."""
        if self.background_image_url is None:
            return None

        # https://i.pximg.net/c/1200x600_90_a2_g5/background/img/2020/09/14/15/32/52/24234_1f609991b032620ead844f487e88fe7b_master1200.jpg
        # https://i.pximg.net/c/1920x960_80_a2_g5/background/img/2020/09/14/15/32/52/24234_1f609991b032620ead844f487e88fe7b.jpg
        original_url = self.background_image_url.replace("_master1200", "")
        original_url = original_url.replace("1200x600_90_a2_g5", "1920x960_80_a2_g5")

        urls: dict[str, base.AttachmentURL] = {}
        for size, url, (width, height) in [
            ("large", self.background_image_url, (1200, 600)),
            ("original", original_url, (1920, 960)),
        ]:
            urls[size] = base.AttachmentURL(
                service="pixiv",
                width=width,
                height=height,
                url=url,
                alt_url=_to_alt_image(url),
            )

        return base.Attachment(
            service="pixiv",
            large=urls["large"],
            original=urls["original"],
        )


class PixivUserDetails(pydantic.BaseModel):
    """A pixiv user."""

    user: PixivUser
    """Partial user details."""
    profile: PixivProfile
    """Profile details."""
    workspace: collections.abc.Mapping[str, str | None]
    """IDK. Useless."""

    def to_universal(self) -> base.User:
        """Convert the user to a universal user."""
        connections: list[base.Connection] = []
        mentions: list[base.Mention] = []

        if self.profile.twitter_url:
            connections.append(
                base.Connection(
                    service="twitter",
                    url=self.profile.twitter_url,
                    user=self.profile.twitter_account,
                ),
            )
            mentions.append(base.Mention(url=self.profile.twitter_url))

        if self.profile.webpage:
            mentions.append(base.Mention(url=self.profile.webpage))
        if self.user.comment:
            for url in re.findall(r"https?://[^\s]+", self.user.comment):
                mentions.append(base.Mention(url=url))

        return base.User(
            service="pixiv",
            id=str(self.user.id),
            request_id=str(self.user.id),
            name=self.user.name,
            unique_name=self.user.account,
            bio=self.user.comment,
            url=f"https://www.pixiv.net/users/{self.user.id}",
            alt_url=f"https://www.pixiv.moe/user/{self.user.id}",
            avatar=self.user.profile_image_urls.to_universal(),
            banner=self.profile.background_image_to_universal(),
            # not followers but how many they're following? The heck pixiv!?
            # followers=self.profile.total_follow_users,
            connections=connections,
            mentions=mentions,
            following=self.user.is_followed,
        )


class PixivUserPreview(pydantic.BaseModel):
    """A pixiv user with a few illusts and novels."""

    # illusts and novels are not parsed for optimizations
    # 30x3 = 90 full illust objects per request are too much

    user: PixivUser
    """Partial user details."""
    illusts: collections.abc.Sequence[object]
    """The user's illustrations."""
    novels: collections.abc.Sequence[object]
    """The user's novels."""
    is_muted: bool
    """Whether the user is muted."""

    def to_universal(self) -> base.User:
        """Convert the user to a universal user."""
        return self.user.to_universal()


KEYS = [
    "offset",
    "seed_illust_ids",
    "max_bookmark_id",
    "viewed",
    "min_bookmark_id_for_recent_illust",
    "max_bookmark_id_for_recommend",
]


class PixivPaginatedResource(pydantic.BaseModel):
    """Pixiv paginated resource."""

    next_url: str | None
    """The next page URL."""

    def get_next_query(self, key: str | list[str] = KEYS) -> collections.abc.Mapping[str, str] | None:
        """Convert the resource to a universal paginated resource."""
        if self.next_url is None:
            return None

        keys = [key] if isinstance(key, str) else key

        # pixiv uses php query arrays (e.g. ?a[0]=1&a[1]=2)
        # we use comma separated values (e.g. ?a=1,2)
        # NOTE: pyright bug, unknown return type requires cast
        raw_query = typing.cast(
            "dict[str, str | list[str]]",
            pixivpy_utils.parse_qs(self.next_url),  # pyright: reportUnknownMemberType=false
        )

        query: dict[str, str] = {}
        for key in keys:
            value = raw_query.get(key)
            if not value:
                continue

            if isinstance(value, list):
                query[key] = ",".join(value)
            else:
                query[key] = value

        return query


class PixivPaginatedIllusts(PixivPaginatedResource):
    """Pixiv paginated illustrations."""

    illusts: collections.abc.Sequence[PixivIllust]
    """The illustrations."""

    def to_universal(self) -> base.Page[base.Post]:
        """Convert the resource to a universal paginated resource."""
        return base.Page(
            items=[illust.to_universal() for illust in self.illusts],
            next=self.get_next_query(),
        )


class PixivPaginatedBookmarks(PixivPaginatedResource):
    """Pixiv paginated bookmarks."""

    illusts: collections.abc.Sequence[PixivIllust]
    """The illustrations."""
    next_url: str | None
    """The next page URL."""

    def to_universal(self) -> base.Page[base.Post]:
        """Convert the resource to a universal paginated resource."""
        return base.Page(
            items=[illust.to_universal() for illust in self.illusts],
            next=self.get_next_query(),
        )


class PixivPaginatedUsers(PixivPaginatedResource):
    """Pixiv paginated users."""

    users: collections.abc.Sequence[PixivUser]
    """The users."""

    def to_universal(self) -> base.Page[base.User]:
        """Convert the resource to a universal paginated resource."""
        return base.Page(
            items=[user.to_universal() for user in self.users],
            next=self.get_next_query(),
        )


class PixivPaginatedUserPreviews(PixivPaginatedResource):
    """Pixiv paginated user previews."""

    user_previews: collections.abc.Sequence[PixivUserPreview]
    """The user previews."""

    def to_universal(self) -> base.Page[base.User]:
        """Convert the resource to a universal paginated resource."""
        return base.Page(
            items=[user.to_universal() for user in self.user_previews],
            next=self.get_next_query(),
        )


class PixivPaginatedComments(PixivPaginatedResource):
    """Pixiv paginated comments."""

    total_comments: int
    """The total number of comments."""

    comments: collections.abc.Sequence[PixivComment]
    """The comments."""

    def to_universal(self) -> base.Page[base.Comment]:
        """Convert the resource to a universal paginated resource."""
        comments: dict[str, base.Comment] = {str(comment.id): comment.to_universal() for comment in self.comments}

        root_comments: list[base.Comment] = []
        children_comments: dict[str, list[base.Comment]] = {}
        for comment in comments.values():
            if comment.parent_id:
                children_comments.setdefault(comment.parent_id, []).append(comment)
            else:
                root_comments.append(comment)

        stack = root_comments.copy()
        while stack:
            parent_comment = stack.pop()
            children = children_comments.get(parent_comment.id)
            if children:
                parent_comment.available_replies = children
                stack.extend(children)

        return base.Page(
            items=root_comments,
            total=self.total_comments,
            next=self.get_next_query(),
        )
