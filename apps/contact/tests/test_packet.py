from apps.contact.packet import checksum, hex_dump


def test_a_long_message_shows_its_first_48_bytes_and_how_many_more() -> None:
    lines = hex_dump("x" * 2000)

    assert len(lines) == 4
    assert lines[0] == "0000  " + " ".join(["78"] * 16) + "  |" + "x" * 16 + "|"
    assert lines[2].startswith("0020  ")
    assert lines[3] == "…     1,952 more bytes"


def test_a_short_message_is_padded_to_three_rows() -> None:
    lines = hex_dump("Hi Dylan!")

    assert lines[0] == "0000  48 69 20 44 79 6c 61 6e 21 ·· ·· ·· ·· ·· ·· ··  |Hi Dylan!       |"
    assert lines[1] == "0010  " + " ".join(["··"] * 16) + "  |" + " " * 16 + "|"
    assert lines[3] == "      end of message"


def test_rows_are_the_same_width_whatever_the_message() -> None:
    widths = {len(line) for text in ("", "Hi", "x" * 100) for line in hex_dump(text)[:3]}

    assert len(widths) == 1


def test_bytes_that_are_not_plain_text_show_as_dots() -> None:
    lines = hex_dump("café\n")

    assert lines[0].startswith("0000  63 61 66 c3 a9 0a ")
    assert "|caf...  " in lines[0]


def test_one_more_byte_is_singular() -> None:
    assert hex_dump("x" * 49)[3] == "…     1 more byte"


def test_checksum() -> None:
    message = (
        "Hi Dylan, we have a graduate developer role on our trading systems team. "
        "Would you be up for a chat next week?"
    )

    # The same as the design's, worked out in the browser.
    assert checksum(message) == "0x9DF6"
    assert checksum("") == "0x0000"


def test_the_narrow_dump_is_four_rows_of_eight_without_offsets() -> None:
    lines = hex_dump("Hi Dylan, we have a role", row=8, rows=4, offsets=False)

    assert lines[0] == "48 69 20 44 79 6c 61 6e  |Hi Dylan|"
    assert lines[3] == " ".join(["··"] * 8) + "  |" + " " * 8 + "|"
    assert lines[4] == "end of message"
    assert hex_dump("x" * 40, row=8, rows=4, offsets=False)[4] == "… 8 more bytes"
