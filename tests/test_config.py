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
