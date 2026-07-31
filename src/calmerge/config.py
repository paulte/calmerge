import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


@dataclass
class AppPaths:
    config_file: Path
    output_dir: Path
    cache_dir: Path


def parse_args() -> AppPaths:
    parser = argparse.ArgumentParser(
        description="Merge ICS calendars",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("calendars.yaml"),
        help="Calendar configuration file",
    )

    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".cache/calendars"),
        help="Calendar cache directory",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("calendars"),
        help="Output directory for merged calendar",
    )

    args = parser.parse_args()

    return AppPaths(
        config_file=args.config,
        cache_dir=args.cache,
        output_dir=args.output,
    )


def load_config(
    config_file: Path,
) -> dict[str, Any]:
    with config_file.open() as f:
        config = yaml.safe_load(f)

    if not config:
        raise ValueError("Empty configuration")

    if "calendars" not in config:
        raise ValueError("Missing 'calendars' section")

    calendars = config["calendars"]

    if not isinstance(calendars, list) or not calendars:
        raise ValueError("'calendars' must be a non-empty list")

    validate_config(calendars)

    return config


def validate_config(calendars: list[dict[str, Any]]) -> None:
    required_fields = {"name", "url"}

    names = set()
    urls = set()

    for index, calendar in enumerate(calendars, start=1):
        if not isinstance(calendar, dict):
            raise TypeError(f"Calendar entry {index} must be a mapping")

        missing = required_fields - calendar.keys()

        if missing:
            raise ValueError(
                f"Calendar entry {index} missing fields: {', '.join(sorted(missing))}"
            )
        name = calendar["name"].strip()
        url = calendar["url"].strip()

        if not name:
            raise ValueError(f"Calendar entry {index} has invalid name")

        if not url:
            raise ValueError(f"Calendar entry {index} has invalid url")

        if "prefix" in calendar and not calendar["prefix"].strip():
            raise ValueError(f"Calendar entry {index} has invalid prefix")

        parsed_url = urlparse(url)

        if parsed_url.scheme not in ("http", "https"):
            raise ValueError(f"Calendar entry {index} has invalid url scheme: {url}")

        if not parsed_url.netloc:
            raise ValueError(f"Calendar entry {index} has invalid url: {url}")

        if name in names:
            raise ValueError(f"Duplicate calendar name: {name}")

        if url in urls:
            raise ValueError(f"Duplicate calendar url: {url}")

        names.add(name)
        urls.add(url)
