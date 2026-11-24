from apps.projects.markdown import render_write_up


def test_write_up_is_split_at_its_headings() -> None:
    text = "Opening words.\n\n## What it does\n\nOne.\n\n## How it works\n\nTwo."

    write_up = render_write_up(text)

    assert "Opening words." in write_up.intro
    assert [section.title for section in write_up.sections] == ["What it does", "How it works"]
    assert [section.anchor for section in write_up.sections] == ["what-it-does", "how-it-works"]
    assert "<p>Two.</p>" in write_up.sections[1].html


def test_smaller_headings_stay_inside_their_section() -> None:
    write_up = render_write_up("## Results\n\n### In numbers\n\nFast.")

    assert len(write_up.sections) == 1
    assert "<h3>In numbers</h3>" in write_up.sections[0].html


def test_a_heading_inside_code_is_not_a_section() -> None:
    write_up = render_write_up("## Notes\n\n```\n## not a heading\n```\n")

    assert [section.title for section in write_up.sections] == ["Notes"]
    assert "## not a heading" in write_up.sections[0].html


def test_repeated_headings_get_ids_of_their_own() -> None:
    write_up = render_write_up("## Results\n\nA.\n\n## Results\n\nB.")

    assert [section.anchor for section in write_up.sections] == ["results", "results-2"]


def test_an_empty_write_up_has_nothing_in_it() -> None:
    write_up = render_write_up("")

    assert write_up.intro == ""
    assert write_up.sections == ()
