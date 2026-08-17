import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
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

    validate_config(config)

    return config


def validate_config(config: dict[str, Any]) -> None:
    calendars = config["calendars"]
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

        validate_exclusions(
            config.get(
                "exclusions",
                {},
            ),
        )


def get_exclusion_rules(
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    return config.get(
        "exclusions",
        {},
    ).get(
        "rules",
        [],
    )


def _parse_iso_date_or_datetime(value: str) -> None:
    """Validate that a string is a valid ISO date or datetime.

    Accepts:
      - YYYY-MM-DD
      - YYYY-MM-DDTHH:MM:SS
      - YYYY-MM-DDTHH:MM:SSZ
      - YYYY-MM-DDTHH:MM:SS+HH:MM

    Raises ValueError if invalid.
    """
    if not isinstance(value, str) or not value:
        raise ValueError("empty date/datetime string")

    s = value
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        # Try datetime first
        datetime.fromisoformat(s)
    except ValueError:
        # Fallback to date-only
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO date/datetime: {value}") from exc


def validate_exclusions(
    exclusions: dict[str, Any],
) -> None:
    rules = exclusions.get(
        "rules",
        [],
    )

    if not isinstance(rules, list):
        raise TypeError("exclusions.rules must be a list")

    for rule in rules:
        if "id" not in rule:
            raise ValueError(
                "Exclusion rule missing id",
            )

        for section in ("calendar", "event"):
            conditions = rule.get(
                section,
                {},
            )

            if not isinstance(conditions, dict):
                raise TypeError(
                    f"Exclusion rule {rule.get('id')} {section} must be a mapping"
                )

            for field, matcher in conditions.items():
                if not isinstance(matcher, dict):
                    raise TypeError(
                        f"Exclusion rule {rule['id']} {section}.{field} matcher must be a mapping"
                    )

                # Calendar matchers must be regex-based
                if section == "calendar":
                    regex = matcher.get("regex")

                    if not regex:
                        raise ValueError(
                            f"Exclusion rule {rule['id']} {section}.{field} missing regex",
                        )

                    try:
                        re.compile(regex)
                    except re.error as exc:
                        raise ValueError(
                            f"Invalid regex in exclusion rule {rule['id']}: {regex}",
                        ) from exc

                    continue

                # Event matchers may be regex or range (min/max)
                if "regex" in matcher:
                    regex = matcher.get("regex")

                    if not regex:
                        raise ValueError(
                            f"Exclusion rule {rule['id']} {section}.{field} missing regex",
                        )

                    try:
                        re.compile(regex)
                    except re.error as exc:
                        raise ValueError(
                            f"Invalid regex in exclusion rule {rule['id']}: {regex}",
                        ) from exc

                    continue

                if "min" in matcher or "max" in matcher:
                    for bound in ("min", "max"):
                        if bound in matcher:
                            try:
                                _parse_iso_date_or_datetime(matcher[bound])
                            except ValueError as exc:
                                raise ValueError(
                                    f"Invalid {bound} in exclusion rule {rule['id']}: {matcher[bound]}",
                                ) from exc

                    continue

                # Unknown matcher type for event - treat as misconfiguration
                raise ValueError(
                    f"Exclusion rule {rule['id']} {section}.{field} must contain 'regex' or 'min'/'max'",
                )
