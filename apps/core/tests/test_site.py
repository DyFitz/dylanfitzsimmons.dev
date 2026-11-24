from apps.core.site import SiteConfig


def make_site(
    *, base_url: str = "https://example.com", source_url: str = "", commit_sha: str = ""
) -> SiteConfig:
    return SiteConfig(
        name="Test",
        tagline="Tagline",
        description="Description",
        base_url=base_url,
        source_url=source_url,
        commit_sha=commit_sha,
    )


def test_domain_is_the_host_from_the_base_url() -> None:
    assert make_site(base_url="https://example.com").domain == "example.com"
    assert make_site(base_url="http://localhost:8000").domain == "localhost:8000"


def test_short_sha_is_the_first_seven_characters() -> None:
    assert make_site(commit_sha="0123456789abcdef").short_sha == "0123456"


def test_commit_url_points_at_the_commit_in_the_repository() -> None:
    site = make_site(source_url="https://github.com/example/site", commit_sha="abc123")

    assert site.commit_url == "https://github.com/example/site/commit/abc123"


def test_commit_url_needs_both_the_repository_and_the_commit() -> None:
    assert make_site(commit_sha="abc123").commit_url == ""
    assert make_site(source_url="https://github.com/example/site").commit_url == ""
