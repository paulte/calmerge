from __future__ import annotations

import copy
import logging
import uuid
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING, Any

from icalendar import Calendar

from calmerge.exclusions import should_exclude_event

from .cache import CalendarCache
from .config import AppPaths, get_exclusion_rules
from .downloader import create_session, load_source_calendar

if TYPE_CHECKING:
    from .config import AppPaths

TIMEZONE = "Europe/London"
VEVENT = "VEVENT"
UID = "UID"
SUMMARY = "SUMMARY"
DTSTART = "DTSTART"
DTSTAMP = "DTSTAMP"

logger = logging.getLogger(__name__)


def create_deterministic_uid(
    source_name: str,
    event,
) -> str:
    summary = str(event.get(SUMMARY, ""))

    try:
        start = str(event.decoded(DTSTART))
    except Exception:  # noqa: BLE001
        start = ""

    unique_string = repr((
        source_name,
        summary,
        start,
    ))

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            unique_string,
        )
    )


def ensure_uid(event, source_name: str) -> None:
    if UID not in event:
        event.add(
            "uid",
            create_deterministic_uid(
                source_name,
                event,
            ),
        )


def ensure_dtstamp(event) -> None:
    if DTSTAMP not in event:
        event.add(
            "dtstamp",
            datetime.now(UTC),
        )


def get_event_start(event) -> datetime:
    try:
        value = event.decoded(DTSTART)

        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime.combine(
                value,
                time.min,
            )

        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)

        return value

    except Exception:  # noqa: BLE001
        return datetime.max.replace(tzinfo=UTC)


def process_event(
    component,
    source: dict[str, Any],
):
    name = source["name"]
    prefix = source.get("prefix", "")

    event = copy.deepcopy(component)

    ensure_uid(event, name)
    ensure_dtstamp(event)

    event.add(
        "x-source-calendar",
        name,
    )

    if "color" in source:
        event.add(
            "x-apple-calendar-color",
            source["color"],
        )

    logger.info(f"  {event.get(SUMMARY)}")

    return {
        "event": event,
        "prefix": prefix,
        "source": name,
    }


def create_output_calendar(
    config: dict[str, Any],
) -> Calendar:
    calendar = Calendar()

    calendar.add(
        "prodid",
        "-//CalMerge//Combined Calendar//",
    )
    calendar.add(
        "version",
        "2.0",
    )
    calendar.add(
        "calscale",
        "GREGORIAN",
    )
    calendar.add(
        "method",
        "PUBLISH",
    )
    calendar.add(
        "x-wr-calname",
        config.get(
            "calendar_name",
            "Scouting Calendar",
        ),
    )
    calendar.add(
        "x-wr-timezone",
        TIMEZONE,
    )

    return calendar


def merge_calendars(
    config: dict[str, Any],
    paths: AppPaths,
) -> Calendar:
    output = create_output_calendar(config)

    merged_events = {}
    failed_calendars = []

    rules = get_exclusion_rules(config)

    cache = CalendarCache(paths.cache_dir)

    with create_session() as session:
        for source in config["calendars"]:
            name = source["name"]

            logger.info(f"Processing {name}")

            try:
                calendar = load_source_calendar(
                    session,
                    source,
                    cache,
                )

            except Exception:
                logger.exception("Failed loading %s", name)
                failed_calendars.append(name)
                continue

            for component in calendar.walk():
                if component.name != VEVENT:
                    continue
                if should_exclude_event(
                    component,
                    source,
                    rules,
                ):
                    logger.info(
                        "Excluded event: %s",
                        component.get(SUMMARY),
                    )
                    continue

                result = process_event(
                    component,
                    source,
                )

                if result:
                    event = result["event"]
                    uid = str(event[UID])

                    if uid not in merged_events:
                        merged_events[uid] = {
                            "event": event,
                            "prefixes": set(),
                            "sources": set(),
                        }
                    else:
                        existing = merged_events[uid]
                        logger.info(
                            "  Merging duplicate event '%s' from %s into %s",
                            event.get(SUMMARY),
                            result["source"],
                            ", ".join(existing["sources"]),
                        )

                    if result["prefix"]:
                        merged_events[uid]["prefixes"].add(result["prefix"])
                    merged_events[uid]["sources"].add(result["source"])

    if failed_calendars:
        raise RuntimeError(
            f"{len(failed_calendars)} calendar(s) failed: "
            + ", ".join(failed_calendars)
        )

    events = []

    for item in merged_events.values():
        event = item["event"]

        prefixes = sorted(
            item["prefixes"],
            key=str.casefold,
        )

        if prefixes and SUMMARY in event:
            current = str(event[SUMMARY])
            event[SUMMARY] = f"{'/'.join(prefixes)}: {current}"

        events.append(event)

    events.sort(key=get_event_start)

    for event in events:
        output.add_component(event)

    logger.info(f"Merged {len(events)} events")

    return output
