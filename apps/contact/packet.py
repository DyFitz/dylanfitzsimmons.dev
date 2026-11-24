"""The message as the confirmation page shows it going out: its bytes as a hex dump, and a
checksum of them. Purely for show; nothing checks them."""


def hex_dump(text: str, row: int = 16, rows: int = 3, offsets: bool = True) -> list[str]:
    """The opening bytes of the text as rows of hex with the text alongside, then a line
    saying how much more there is.

    Three rows of 16 by default, each starting with its offset. Phones get four rows of 8
    without offsets, which fits their width. Rows are always full, padded with dots, so the
    dump is the same size for a message of any length.
    """
    data = text.encode()
    shown = row * rows
    lines = []
    for start in range(0, shown, row):
        chunk = data[start : start + row]
        hex_part = " ".join([*(f"{byte:02x}" for byte in chunk), *["··"] * (row - len(chunk))])
        text_part = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)
        line = f"{hex_part}  |{text_part.ljust(row)}|"
        lines.append(f"{start:04x}  {line}" if offsets else line)

    # The last line lines up with the hex, past the offsets where there are any.
    rest = len(data) - shown
    if rest > 0:
        lines.append(f"{'…     ' if offsets else '… '}{rest:,} more byte{'' if rest == 1 else 's'}")
    else:
        lines.append(f"{'      ' if offsets else ''}end of message")
    return lines


def checksum(text: str) -> str:
    """A weighted sum of the bytes, as four hex digits, e.g. 0x9DF6."""
    total = sum(byte * (index % 7 + 1) for index, byte in enumerate(text.encode())) % 65536
    return f"0x{total:04X}"
