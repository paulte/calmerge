from datetime import datetime, timedelta, timezone

from icalendar import Event

from calmerge.exclusions import matches_event


def create_event_with_dtstart(dt: datetime) -> Event:
    event = Event()
    event.add("summary", "Any event")
    event.add("dtstart", dt)
    return event


def test_min_excludes_before_min():
    # Event at 2026-08-10 UTC
    event = create_event_with_dtstart(datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))

    matcher = {
        "dtstart": {
            "min": "2026-08-11",
        }
    }

    assert matches_event(event, matcher) is False


def test_max_excludes_after_max():
    event = create_event_with_dtstart(datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc))

    matcher = {
        "dtstart": {
            "max": "2026-08-19T23:59:59Z",
        }
    }

    assert matches_event(event, matcher) is False


def test_min_max_includes_within_range():
    event = create_event_with_dtstart(datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc))

    matcher = {
        "dtstart": {
            "min": "2026-08-10",
            "max": "2026-08-20",
        }
    }

    assert matches_event(event, matcher) is True


def test_date_only_string_parsed_as_start_of_day():
    # Event at start of day 2026-08-10 (naive datetime gets treated as UTC)
    event = create_event_with_dtstart(datetime(2026, 8, 10, 0, 0, tzinfo=timezone.utc))

    matcher = {
        "dtstart": {
            "min": "2026-08-10",
        }
    }

    assert matches_event(event, matcher) is True


def test_undecodable_field_fails_match():
    event = Event()
    event.add("summary", "No dtstart")

    matcher = {
        "dtstart": {
            "min": "2026-08-01",
        }
    }

    assert matches_event(event, matcher) is False
