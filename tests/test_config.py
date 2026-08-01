from pathlib import Path

import pytest
import yaml

from calmerge.config import load_config


def write_config(tmp_path: Path, content: dict) -> Path:
    config_file = tmp_path / "calendars.yaml"

    with config_file.open("w") as f:
        yaml.safe_dump(content, f)

    return config_file


def test_config_without_prefix_is_valid(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendar_name": "Test Calendar",
            "calendars": [
                {
                    "name": "Family",
                    "url": "https://example.com/family.ics",
                }
            ],
        },
    )

    config = load_config(config_file)

    assert config["calendars"][0]["name"] == "Family"


def test_config_with_prefix_is_valid(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendar_name": "Test Calendar",
            "calendars": [
                {
                    "name": "Work",
                    "prefix": "WORK",
                    "url": "https://example.com/work.ics",
                }
            ],
        },
    )

    config = load_config(config_file)

    assert config["calendars"][0]["prefix"] == "WORK"


def test_config_missing_name_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "url": "https://example.com/calendar.ics",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="missing fields"):
        load_config(config_file)


def test_config_missing_url_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "Calendar",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="missing fields"):
        load_config(config_file)


def test_config_invalid_url_scheme_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "Calendar",
                    "url": "ftp://example.com/calendar.ics",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="invalid url scheme"):
        load_config(config_file)


def test_empty_config_fails(tmp_path: Path):
    config_file = write_config(tmp_path, {})

    with pytest.raises(ValueError, match="Empty configuration"):
        load_config(config_file)


def test_missing_calendars_section_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendar_name": "Test Calendar",
        },
    )

    with pytest.raises(ValueError, match="Missing 'calendars' section"):
        load_config(config_file)


def test_calendars_must_be_non_empty_list(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [],
        },
    )

    with pytest.raises(ValueError, match="non-empty list"):
        load_config(config_file)


def test_calendar_entry_must_be_mapping(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": ["not a mapping"],
        },
    )

    with pytest.raises(TypeError, match="must be a mapping"):
        load_config(config_file)


def test_config_invalid_name_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "   ",
                    "url": "https://example.com/calendar.ics",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="invalid name"):
        load_config(config_file)


def test_config_invalid_prefix_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "Calendar",
                    "prefix": "   ",
                    "url": "https://example.com/calendar.ics",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="invalid prefix"):
        load_config(config_file)


def test_config_blank_url_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "Calendar",
                    "url": "   ",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="invalid url"):
        load_config(config_file)


def test_config_missing_netloc_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "Calendar",
                    "url": "https://",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="invalid url"):
        load_config(config_file)


def test_config_duplicate_name_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "Calendar",
                    "url": "https://example.com/calendar.ics",
                },
                {
                    "name": "Calendar",
                    "url": "https://example.com/other.ics",
                },
            ],
        },
    )

    with pytest.raises(ValueError, match="Duplicate calendar name"):
        load_config(config_file)


def test_config_duplicate_url_fails(tmp_path: Path):
    config_file = write_config(
        tmp_path,
        {
            "calendars": [
                {
                    "name": "Calendar One",
                    "url": "https://example.com/calendar.ics",
                },
                {
                    "name": "Calendar Two",
                    "url": "https://example.com/calendar.ics",
                },
            ],
        },
    )

    with pytest.raises(ValueError, match="Duplicate calendar url"):
        load_config(config_file)
