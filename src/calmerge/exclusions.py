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
    # Accept ISO-8601 datetimes with Z or offset, or date-only strings (YYYY-MM-DD)
    if not value:
        raise ValueError("empty datetime string")

    s = value
    # Handle trailing Z as UTC
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
                value = event.decoded(key)

                # If it's a date, normalise to datetime at start of day
                if isinstance(value, date) and not isinstance(value, datetime):
                    value = datetime.combine(value, time.min)

                if isinstance(value, datetime) and value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)

            except Exception:  # noqa: BLE001
                # If we cannot decode the event field, the condition does not match
                return False

            if "min" in condition:
                try:
                    min_dt = _parse_datetime_string(condition["min"])
                except Exception:
                    return False

                if value < min_dt:
                    return False

            if "max" in condition:
                try:
                    max_dt = _parse_datetime_string(condition["max"])
                except Exception:
                    return False

                if value > max_dt:
                    return False

            continue

        # Unknown condition type, fail safe and do not match
        return False

    return True
