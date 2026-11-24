import json
import posixpath
import re
from pathlib import Path

from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from pytest_django import Settings

from apps.core.tests.html import start_tags

IMPORT_PATH = re.compile(r"""\bfrom\s*["'](?P<path>\.{1,2}/[^"']+)["']""")


def test_every_static_file_the_home_page_uses_exists(client: Client, settings: Settings) -> None:
    html = client.get(reverse("core:home")).content.decode()

    paths = {
        value.removeprefix(settings.STATIC_URL)
        for attrs in start_tags(html)
        for name, value in attrs.items()
        if name in {"src", "href"} and value and value.startswith(settings.STATIC_URL)
    }

    assert paths
    assert [path for path in paths if finders.find(path) is None] == []


def test_collectstatic_carries_hashed_names_into_javascript_imports(
    settings: Settings, tmp_path: Path
) -> None:
    # Runs the production storage over the real static files, so a broken
    # reference fails here rather than in the Docker build.
    settings.STATIC_ROOT = tmp_path
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "apps.core.storage.StaticStorage"},
    }

    call_command("collectstatic", interactive=False, verbosity=0)

    hashed = json.loads((tmp_path / "staticfiles.json").read_text())["paths"]
    imports = {}
    for original, stored in hashed.items():
        if original.startswith("js/") and original.endswith(".js"):
            source = (tmp_path / stored).read_text(encoding="utf-8")
            folder = posixpath.dirname(stored)
            imports[original] = [
                posixpath.normpath(posixpath.join(folder, match["path"]))
                for match in IMPORT_PATH.finditer(source)
            ]

    assert imports["js/site.js"]
    assert imports["js/home.js"]
    for original, targets in imports.items():
        for target in targets:
            assert target in hashed.values(), f"{original} imports {target}, which isn't hashed"
