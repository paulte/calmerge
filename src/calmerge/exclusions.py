from __future__ import annotations

import re
from typing import Any


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


def matches_event(
    event: Any,
    matcher: dict[str, Any] | None,
) -> bool:
    if matcher is None:
        return True

    for field, condition in matcher.items():
        value = str(event.get(field, ""))

        if not re.search(
            condition["regex"],
            value,
        ):
            return False

    return True
