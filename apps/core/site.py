from dataclasses import dataclass
from typing import Self
from urllib.parse import urlsplit

from django.conf import settings

SHORT_SHA_LENGTH = 7


@dataclass(frozen=True, slots=True, kw_only=True)
class SiteConfig:
    name: str
    tagline: str
    description: str
    base_url: str
    source_url: str
    commit_sha: str

    @classmethod
    def from_settings(cls) -> Self:
        return cls(
            name=settings.SITE_NAME,
            tagline=settings.SITE_TAGLINE,
            description=settings.SITE_DESCRIPTION,
            base_url=settings.SITE_URL,
            source_url=settings.SITE_SOURCE_URL,
            commit_sha=settings.GIT_SHA,
        )

    @property
    def domain(self) -> str:
        return urlsplit(self.base_url).netloc

    @property
    def short_sha(self) -> str:
        return self.commit_sha[:SHORT_SHA_LENGTH]

    @property
    def commit_url(self) -> str:
        if self.source_url and self.commit_sha:
            return f"{self.source_url}/commit/{self.commit_sha}"
        return ""
