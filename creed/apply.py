"""Apply a declared creed to repository instruction files."""

import json
from pathlib import Path

from creed.block import AGENTS_FILENAME, MIRROR_FILENAMES, install_block
from creed.profiles import CONFIGURATION_FIELDS, PROFILES, render_block


CREED_FILENAME = "CREED.json"


def read_configuration(path: Path) -> dict[str, object]:
    """Read and structurally validate CREED.json."""

    try:
        with path.open("r", encoding="utf-8") as configuration_file:
            configuration = json.load(configuration_file)
    except json.JSONDecodeError as error:
        raise ValueError(f"CREED.json is not valid JSON: {error}") from error

    if not isinstance(configuration, dict):
        raise ValueError("CREED.json must contain a JSON object.")

    if "creed" not in configuration:
        raise ValueError("CREED.json is missing the required 'creed' field.")

    creed_name = configuration["creed"]
    if not isinstance(creed_name, str) or creed_name not in PROFILES:
        known_names = ", ".join(PROFILES)
        raise ValueError(f"CREED.json declares an unknown creed. Available creeds: {known_names}.")

    for field_name, field_value in configuration.items():
        if field_name == "creed":
            continue
        if field_name not in CONFIGURATION_FIELDS:
            raise ValueError(f"CREED.json contains an unknown field: {field_name}.")
        if not isinstance(field_value, bool):
            raise ValueError(f"CREED.json field '{field_name}' must be true or false.")

    return configuration


def validate_configuration(profile_name: str, configuration: dict[str, object]) -> None:
    """Check optional declaration fields against the selected profile."""

    profile = PROFILES[profile_name]
    for field_name, expected_value in profile.configuration.items():
        if field_name in configuration and configuration[field_name] != expected_value:
            actual_value = configuration[field_name]
            raise ValueError(
                f"CREED.json field '{field_name}' must be {str(expected_value).lower()} "
                f"for the {profile_name} creed; it is {str(actual_value).lower()}."
            )


def apply_creeds(root: Path, override: str | None = None) -> str:
    """Install the selected creed block and synchronize instruction mirrors."""

    configuration_path = root / CREED_FILENAME
    configuration = read_configuration(configuration_path)
    selected_creeds = override or str(configuration["creed"])
    if selected_creeds not in PROFILES:
        known_names = ", ".join(PROFILES)
        raise ValueError(f"Unknown creed: {selected_creeds}. Available creeds: {known_names}.")

    validate_configuration(selected_creeds, configuration)
    block_text = render_block(selected_creeds)

    agents_path = root / AGENTS_FILENAME
    content = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    updated_content = install_block(content, block_text)
    agents_path.write_text(updated_content, encoding="utf-8")

    for mirror_filename in MIRROR_FILENAMES:
        (root / mirror_filename).write_text(updated_content, encoding="utf-8")

    return selected_creeds
