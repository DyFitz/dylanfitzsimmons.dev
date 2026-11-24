from html.parser import HTMLParser

type Attributes = dict[str, str | None]


class _TagCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, Attributes]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


def start_tags(html: str, tag: str | None = None) -> list[Attributes]:
    """The attributes of every element in the page, or of every element of one kind.

    Attributes without a value, such as `hidden`, map to None.
    """
    collector = _TagCollector()
    collector.feed(html)
    collector.close()
    return [attrs for name, attrs in collector.tags if tag is None or name == tag]
