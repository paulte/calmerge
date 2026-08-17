from datetime import UTC, date, datetime

from icalendar import Event

from calmerge.exclusions import matches_event


def create_event_with_dtstart(dt: datetime) -> Event:
    event = Event()
    event.add("summary", "Any event")
    event.add("dtstart", dt)
    return event


def create_event_with_date_dtstart(d: date) -> Event:
    event = Event()
    event.add("summary", "Any event")
    event.add("dtstart", d)
    return event


def test_min_excludes_before_min():
    # Event at 2026-08-10 UTC
    event = create_event_with_dtstart(datetime(2026, 8, 10, 12, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "min": "2026-08-11",
        }
    }

    assert matches_event(event, matcher) is False


def test_min_includes_at_min_boundary():
    # Event exactly at the 2026-08-11 UTC min boundary
    event = create_event_with_dtstart(datetime(2026, 8, 11, 0, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "min": "2026-08-11",
        }
    }

    assert matches_event(event, matcher) is True


def test_max_excludes_after_max():
    event = create_event_with_dtstart(datetime(2026, 8, 20, 12, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "max": "2026-08-19T23:59:59Z",
        }
    }

    assert matches_event(event, matcher) is False


def test_max_includes_at_max_boundary():
    event = create_event_with_dtstart(datetime(2026, 8, 19, 23, 59, 59, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "max": "2026-08-19T23:59:59Z",
        }
    }

    assert matches_event(event, matcher) is True


def test_min_only_includes_event_after_min():
    event = create_event_with_dtstart(datetime(2026, 8, 12, 12, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "min": "2026-08-11",
        }
    }

    assert matches_event(event, matcher) is True


def test_max_only_includes_event_before_max():
    event = create_event_with_dtstart(datetime(2026, 8, 18, 12, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "max": "2026-08-19T23:59:59Z",
        }
    }

    assert matches_event(event, matcher) is True


def test_min_max_includes_within_range():
    event = create_event_with_dtstart(datetime(2026, 8, 15, 9, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "min": "2026-08-10",
            "max": "2026-08-20",
        }
    }

    assert matches_event(event, matcher) is True


def test_date_only_string_parsed_as_start_of_day():
    # Event at start of day 2026-08-10 (date-only DTSTART)
    event = create_event_with_date_dtstart(date(2026, 8, 10))

    matcher = {
        "dtstart": {
            "min": "2026-08-10",
        }
    }

    assert matches_event(event, matcher) is True


def test_date_only_dtstart_matches_range():
    event = create_event_with_date_dtstart(date(2026, 8, 10))

    matcher = {
        "dtstart": {
            "min": "2026-08-10",
            "max": "2026-08-20",
        }
    }

    assert matches_event(event, matcher) is True

    # Verify maximum boundary is also inclusive
    event_at_max = create_event_with_date_dtstart(date(2026, 8, 20))
    assert matches_event(event_at_max, matcher) is True


def test_date_only_dtstart_outside_range_does_not_match():
    event = create_event_with_date_dtstart(date(2026, 8, 21))

    matcher = {
        "dtstart": {
            "min": "2026-08-10",
            "max": "2026-08-20",
        }
    }

    assert matches_event(event, matcher) is False


def test_invalid_min_string_treated_as_non_match():
    event = create_event_with_dtstart(datetime(2026, 8, 10, 12, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "min": "not-a-date",
        }
    }

    assert matches_event(event, matcher) is False


def test_invalid_max_string_treated_as_non_match():
    event = create_event_with_dtstart(datetime(2026, 8, 10, 12, 0, tzinfo=UTC))

    matcher = {
        "dtstart": {
            "max": "2026-13-01",
        }
    }

    assert matches_event(event, matcher) is False


def test_undecodable_field_fails_match():
    event = Event()
    event.add("summary", "No dtstart")

    matcher = {
        "dtstart": {
            "min": "2026-08-01",
        }
    }

    assert matches_event(event, matcher) is False


def test_naive_dtstart_with_utc_z_bounds():
    # Naive datetime should be normalized to UTC internally
    naive_dt = datetime(2026, 8, 10, 8, 0, 0, tzinfo=UTC)
    event = create_event_with_dtstart(naive_dt)

    matcher = {
        "dtstart": {
            "min": "2026-08-10T08:00:00Z",
            "max": "2026-08-10T18:00:00Z",
        }
    }

    assert matches_event(event, matcher) is True


def test_naive_dtstart_with_offset_bounds():
    # 10:00+02:00 == 08:00Z, so the event at 08:00 UTC should be inside this range
    naive_dt = datetime(2026, 8, 10, 8, 0, 0, tzinfo=UTC)
    event = create_event_with_dtstart(naive_dt)

    matcher = {
        "dtstart": {
            "min": "2026-08-10T10:00:00+02:00",
            "max": "2026-08-10T20:00:00+02:00",
        }
    }

    assert matches_event(event, matcher) is True
