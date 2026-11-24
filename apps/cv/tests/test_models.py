import pytest

from apps.cv.models import CvProject, Entry, Profile, lines


def test_lines_drops_blank_lines_and_spaces() -> None:
    assert lines("  one \n\n two\n") == ["one", "two"]


@pytest.mark.parametrize(
    ("url", "text"),
    [
        ("https://github.com/DyFitz", "github.com/DyFitz"),
        ("https://www.linkedin.com/in/dylan-fitzsimmons/", "linkedin.com/in/dylan-fitzsimmons"),
        ("", ""),
    ],
)
def test_link_text(url: str, text: str) -> None:
    assert Profile.link_text(url) == text


def test_an_entry_with_no_end_is_current() -> None:
    assert Entry(ended="").is_current
    assert not Entry(ended="Jan 2023").is_current


def test_project_stack_splits_on_commas() -> None:
    assert CvProject(stack="Django, SQLite ,Render").stack_list == ["Django", "SQLite", "Render"]
