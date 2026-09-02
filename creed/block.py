"""Managed-block installation and validation."""

import re


BLOCK_START = "<!-- creed:managed:start -->"
BLOCK_END = "<!-- creed:managed:end -->"
AGENTS_FILENAME = "AGENTS.md"
MIRROR_FILENAMES = ("CLAUDE.md", "GEMINI.md", "HERMES.md")

_BLOCK_PATTERN = re.compile(
    re.escape(BLOCK_START) + r"\r?\n.*?" + re.escape(BLOCK_END),
    re.DOTALL,
)


def install_block(content: str | None, block_text: str) -> str:
    """Replace an existing managed block in place, or append a new one."""

    text = content or ""
    replacement = block_text.rstrip("\r\n")
    if _BLOCK_PATTERN.search(text):
        return _BLOCK_PATTERN.sub(lambda _match: replacement, text, count=1)

    prefix = text.rstrip("\r\n")
    separator = "\n\n" if prefix else ""
    return prefix + separator + replacement + "\n"


def validate_block(content: str | None, expected_block: str) -> list[str]:
    """Return human-readable validation issues; an empty list means valid."""

    text = content or ""
    expected = expected_block.rstrip("\r\n")
    matches = list(_BLOCK_PATTERN.finditer(text))

    if not matches:
        if BLOCK_START in text or BLOCK_END in text:
            return ["AGENTS.md contains an incomplete or malformed managed creed block."]
        return ["AGENTS.md is missing the managed creed block."]

    issues: list[str] = []
    if len(matches) > 1:
        issues.append("AGENTS.md contains more than one managed creed block.")

    if any(match.group(0).rstrip("\r\n") != expected for match in matches):
        issues.append("The managed creed block does not match the declared creed.")

    return issues
