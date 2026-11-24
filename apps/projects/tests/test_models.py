import pytest

from apps.projects.models import Project


def test_tags_come_from_the_stack() -> None:
    project = Project(stack="Python, FastAPI,  C# ,")

    assert project.tags == ["Python", "FastAPI", "C#"]


@pytest.mark.parametrize(
    ("status", "code"),
    [("In progress", "WIP"), ("complete", "DONE"), ("[Status]", "[?]"), ("", "[?]")],
)
def test_status_code(status: str, code: str) -> None:
    assert Project(status=status).status_code == code


def test_still_template_follows_the_screen() -> None:
    assert Project(screen=Project.Screen.FORECAST).still_template == "core/screens/forecast.svg"


def test_short_stack_names_the_main_tool_and_counts_the_rest() -> None:
    assert Project(stack="Django, PostgreSQL, Docker").short_stack == "Django +2"
    assert Project(stack="Python").short_stack == "Python"
    assert Project(stack="").short_stack == ""
