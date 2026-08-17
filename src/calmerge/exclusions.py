from __future__ import annotations

import re
from typing import Any
from datetime import datetime, date, time, timezone


def should_exclude_event(
    event: Any,
    source: dict[str, Any],
    rules: list[dict[str, Any]],
) -> bool:
    for rule in rules:
        if not matches_calendar(source, rule.get("calendar")):
            continue

        if not matches_event(event, rule.get("event")):
            continue

        return True

    return False


def matches_calendar(
    source: dict[str, Any],
    matcher: dict[str, Any] | None,
) -> bool:
    if matcher is None:
        return True

    for field, condition in matcher.items():
        value = str(source.get(field, ""))

        if not re.search(
            condition["regex"],
            value,
        ):
            return False

    return True


def _parse_datetime_string(value: str) -> datetime:
    """Parse an ISO-8601 date/time or date string into an aware UTC datetime.

    Accepted forms:
      - Date-only: "YYYY-MM-DD" -> interpreted as YYYY-MM-DDT00:00:00Z
      - Datetime with Z: "YYYY-MM-DDTHH:MM:SSZ"
      - Datetime with offset: "YYYY-MM-DDTHH:MM:SS+HH:MM"
      - ISO datetimes without timezone are treated as UTC (explicit design choice)

    Raises ValueError on parse failure.
    """
    if not value:
        raise ValueError("empty datetime string")

    s = value
    # Handle trailing Z as UTC for fromisoformat compatibility
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        # Try parsing as full datetime
        dt = datetime.fromisoformat(s)
    except ValueError:
        # Fallback to date-only
        d = date.fromisoformat(s)
        dt = datetime.combine(d, time.min)
        dt = dt.replace(tzinfo=timezone.utc)

    # If dt is naive, treat as UTC (explicit, documented behaviour)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def matches_event(
    event: Any,
    matcher: dict[str, Any] | None,
) -> bool:
    if matcher is None:
        return True

    for field, condition in matcher.items():
        # If condition contains regex, use the existing behaviour
        if "regex" in condition:
            value = str(event.get(field, ""))

            if not re.search(
                condition["regex"],
                value,
            ):
                return False

            continue

        # Support range matching using min/max on date-like fields
        if "min" in condition or "max" in condition:
            # Field names in events are typically uppercase (e.g. DTSTART)
            key = field.upper()

            try:
                # Decoding can raise a variety of exceptions depending on the
                # event object; narrow the exceptions we catch so unexpected
                # errors still surface during development.
                value = event.decoded(key)
            except (KeyError, AttributeError, TypeError):
                # Field missing or not decodable: rule does not match
                return False

            # If it's a date, normalise to datetime at start of day
            if isinstance(value, date) and not isinstance(value, datetime):
                value = datetime.combine(value, time.min)

            # If datetime is naive, treat it as UTC (explicit choice)
            if isinstance(value, datetime) and value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)

            if "min" in condition:
                try:
                    min_dt = _parse_datetime_string(condition["min"])
                except ValueError:
                    # Misconfigured min value -> treat as non-match
                    return False

                if value < min_dt:
                    return False

            if "max" in condition:
                try:
                    max_dt = _parse_datetime_string(condition["max"])
                except ValueError:
                    # Misconfigured max value -> treat as non-match
                    return False

                if value > max_dt:
                    return False

            continue

        # Unknown condition type, fail safe and do not match
        return False

    return True
