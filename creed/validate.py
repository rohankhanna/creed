"""Validate a repository's declared and installed creed."""

from pathlib import Path

from creed.apply import CREED_FILENAME, read_configuration, validate_configuration
from creed.block import AGENTS_FILENAME, MIRROR_FILENAMES, validate_block
from creed.profiles import render_block


def validate_repository(root: Path) -> list[str]:
    """Return all creed and instruction-mirror validation issues."""

    try:
        configuration = read_configuration(root / CREED_FILENAME)
        declared_creeds = str(configuration["creed"])
        validate_configuration(declared_creeds, configuration)
        expected_block = render_block(declared_creeds)
    except (OSError, ValueError) as error:
        return [f"CREED.json is invalid: {error}"]

    issues: list[str] = []
    agents_path = root / AGENTS_FILENAME
    if not agents_path.exists():
        issues.append("AGENTS.md is missing.")
        content = ""
    else:
        content = agents_path.read_text(encoding="utf-8")

    issues.extend(validate_block(content, expected_block))

    for mirror_filename in MIRROR_FILENAMES:
        mirror_path = root / mirror_filename
        if not mirror_path.exists():
            issues.append(f"{mirror_filename} is missing.")
            continue
        if mirror_path.read_text(encoding="utf-8") != content:
            issues.append(f"{mirror_filename} is not an exact replica of AGENTS.md.")

    return issues
