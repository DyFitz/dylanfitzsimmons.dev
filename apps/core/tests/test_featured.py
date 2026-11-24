import pytest
from django.template.loader import get_template

from apps.core.featured import FEATURED_PROJECTS, FeaturedProject, Screen


@pytest.mark.parametrize("screen", list(Screen))
def test_every_screen_has_a_still_image(screen: Screen) -> None:
    project = FeaturedProject(slug="test", title="Test", summary="", tags=(), screen=screen)

    # Raises TemplateDoesNotExist if the still image is missing.
    get_template(project.still_template)


def test_featured_projects_have_unique_slugs() -> None:
    slugs = [project.slug for project in FEATURED_PROJECTS]

    assert len(slugs) == len(set(slugs))
