import re

import pytest
from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from apps.cv.models import CvProject, Entry, Evidence
from apps.projects.models import Project

pytestmark = pytest.mark.django_db

UK_MOBILE = re.compile(r"(?:\+44\s?|0)7\d{3}\s?\d{3}\s?\d{3}")


def test_cv_page_shows_the_cv(client: Client) -> None:
    response = client.get(reverse("cv:page"))

    assert response.status_code == 200
    assertContains(response, "Dylan Fitzsimmons")
    assertContains(response, "MSc Software Development")
    assertContains(response, "Co-Founder and Software Developer")
    assertContains(response, "IESIS Best Student Award")


def test_education_comes_before_experience(client: Client) -> None:
    html = client.get(reverse("cv:page")).content.decode()

    assert html.index('id="education"') < html.index('id="experience"')


def test_the_pdf_is_there_to_download(client: Client) -> None:
    response = client.get(reverse("cv:page"))

    assertContains(response, "files/Dylan_Fitzsimmons_CV.pdf")
    assert finders.find("files/Dylan_Fitzsimmons_CV.pdf") is not None


def test_send_a_message_goes_to_the_contact_page(client: Client) -> None:
    response = client.get(reverse("cv:page"))

    assertContains(response, f'href="{reverse("contact:page")}"><span>mail</span>')


def test_no_phone_number_or_personal_email_on_the_page(client: Client) -> None:
    response = client.get(reverse("cv:page"))

    # Any UK mobile number, so the test doesn't give away part of mine.
    assert not UK_MOBILE.search(response.content.decode())
    assertNotContains(response, "+44")
    assertNotContains(response, "hotmail")


def test_entries_link_to_published_write_ups_only(client: Client) -> None:
    enular = Project.objects.get(slug="enular")
    url = enular.get_absolute_url()

    assertContains(client.get(reverse("cv:page")), url)

    Project.objects.filter(slug="enular").update(is_published=False)

    assertNotContains(client.get(reverse("cv:page")), url)


def test_the_current_job_is_marked_as_now(client: Client) -> None:
    current = Entry.objects.get(title="A&E Call Handler")
    assert current.is_current

    assertContains(client.get(reverse("cv:page")), "entry--now", count=1)


def test_more_is_rendered_as_safe_html(client: Client) -> None:
    Entry.objects.filter(title="A&E Call Handler").update(more="**Calm** <script>alert(1)</script>")

    response = client.get(reverse("cv:page"))

    assertContains(response, "<strong>Calm</strong>", html=True)
    assertNotContains(response, "<script>alert(1)</script>")


def test_skill_evidence_links_to_write_ups(client: Client) -> None:
    linked = Evidence.objects.filter(project__isnull=False).first()
    assert linked is not None

    assertContains(client.get(reverse("cv:page")), linked.project.get_absolute_url())


def test_jump_strip_links_to_every_section(client: Client) -> None:
    response = client.get(reverse("cv:page"))

    for section in ("profile", "education", "experience", "projects", "skills"):
        assertContains(response, f'class="jump__link" href="#{section}"')
        assertContains(response, f'id="{section}"')


@pytest.mark.django_db
def test_this_site_is_a_key_project_after_opus_equi(client: Client) -> None:
    key = list(CvProject.objects.filter(is_key=True).values_list("title", flat=True))
    assert key == [
        "Opus Equi: financial time-series forecasting",
        "dylanfitzsimmons.dev: this site",
    ]
    response = client.get(reverse("cv:page"))
    assertContains(response, "project--key", count=2)


@pytest.mark.django_db
def test_the_finance_modules_and_new_skills_are_on_the_cv(client: Client) -> None:
    response = client.get(reverse("cv:page"))
    assertContains(response, "C++ in Finance and Applied Mathematical Finance")
    for skill in ("Docker", "GitHub Actions", "REST APIs", "HTML and CSS", "pytest, MSTest"):
        assertContains(response, skill)
    assertContains(response, "MSc Financial Economics: C++ in Finance, options pricing")
