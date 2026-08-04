from datetime import UTC, date, datetime

import pytest
from icalendar import Calendar, Event

from calmerge.cache import CalendarCache
from calmerge.downloader import download_calendar, load_source_calendar
from calmerge.merger import (
    create_output_calendar,
    get_event_start,
    merge_calendars,
    process_event,
)

ICAL = b"""
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test-event
SUMMARY:Test Event
DTSTART:20260725T120000Z
END:VEVENT
END:VCALENDAR
"""


class MockResponse:
    def __init__(self, status_code, content, headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class MockSession:
    def __init__(self, response):
        self.response = response

    def get(self, url, headers, timeout):
        return self.response


def test_download_calendar_returns_200_payload_and_headers():
    session = MockSession(
        MockResponse(
            200,
            b"new-calendar",
            {
                "ETag": '"etag-value"',
                "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT",
            },
        )
    )

    result = download_calendar(
        session,
        "https://example.com/calendar.ics",
        {
            "etag": '"old-etag"',
            "last_modified": "Sun, 31 Dec 2023 00:00:00 GMT",
        },
    )

    assert result.not_modified is False
    assert result.content == b"new-calendar"
    assert result.metadata == {
        "etag": '"etag-value"',
        "last_modified": "Mon, 01 Jan 2024 00:00:00 GMT",
    }


def test_load_source_calendar_uses_cache_after_304(tmp_path):
    cache = CalendarCache(tmp_path)
    cache.save("test-calendar", ICAL)
    cache.save_metadata(
        "test-calendar",
        {
            "etag": '"test-etag"',
            "last_modified": "Sat, 25 Jul 2026 12:00:00 GMT",
        },
    )

    session = MockSession(MockResponse(304, b"", {}))

    calendar = load_source_calendar(
        session,
        {
            "name": "test-calendar",
            "url": "https://example.com/calendar.ics",
        },
        cache,
    )

    events = list(calendar.walk("VEVENT"))
    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Test Event"


def test_load_source_calendar_downloads_and_caches_new_payload(tmp_path):
    cache = CalendarCache(tmp_path)
    session = MockSession(
        MockResponse(
            200,
            ICAL,
            {
                "ETag": '"fresh-etag"',
                "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT",
            },
        )
    )

    calendar = load_source_calendar(
        session,
        {
            "name": "test-calendar",
            "url": "https://example.com/calendar.ics",
        },
        cache,
    )

    events = list(calendar.walk("VEVENT"))
    assert len(events) == 1
    assert cache.load("test-calendar") == ICAL
    assert cache.load_metadata("test-calendar") == {
        "etag": '"fresh-etag"',
        "last_modified": "Mon, 01 Jan 2024 00:00:00 GMT",
    }


def test_load_source_calendar_raises_when_cache_missing_after_failed_download(
    tmp_path,
):
    cache = CalendarCache(tmp_path)
    session = MockSession(MockResponse(500, b"", {}))

    with pytest.raises(RuntimeError, match="No cached copy available"):
        load_source_calendar(
            session,
            {
                "name": "test-calendar",
                "url": "https://example.com/calendar.ics",
            },
            cache,
        )


def test_load_source_calendar_raises_when_304_response_has_no_cached_calendar(
    tmp_path,
):
    cache = CalendarCache(tmp_path)
    session = MockSession(MockResponse(304, b"", {}))

    with pytest.raises(RuntimeError, match="No cached copy available"):
        load_source_calendar(
            session,
            {
                "name": "test-calendar",
                "url": "https://example.com/calendar.ics",
            },
            cache,
        )


def test_process_event_adds_uid_dtstamp_metadata_and_color():
    event = next(iter(Calendar.from_ical(ICAL).walk("VEVENT")))

    source = {
        "name": "Family",
        "prefix": "FAMILY",
        "color": "#ff00ff",
    }

    processed = process_event(event, source)

    assert processed is not None

    processed_event = processed["event"]

    assert "UID" in processed_event
    assert "DTSTAMP" in processed_event
    assert str(processed_event["SUMMARY"]) == "Test Event"
    assert processed["prefix"] == "FAMILY"
    assert processed["source"] == "Family"
    assert str(processed_event["X-SOURCE-CALENDAR"]) == "Family"
    assert str(processed_event["X-APPLE-CALENDAR-COLOR"]) == "#ff00ff"


def test_get_event_start_handles_date_and_missing_value():
    event = Event()
    event.add("dtstart", date(2026, 7, 25))
    assert get_event_start(event) == datetime(2026, 7, 25, 0, 0, tzinfo=UTC)

    naive_datetime_event = Event()
    naive_datetime_event.add(
        "dtstart",
        datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
    )
    assert get_event_start(naive_datetime_event) == datetime(
        2026,
        7,
        25,
        12,
        0,
        tzinfo=UTC,
    )

    event_without_start = Event()
    assert get_event_start(event_without_start) == datetime.max.replace(tzinfo=UTC)


def test_process_event_generates_missing_uid_and_dtstamp():
    event = Event()
    event.add("summary", "Missing UID Event")
    source = {"name": "Family"}

    processed = process_event(event, source)

    assert processed is not None

    processed_event = processed["event"]

    assert "UID" in processed_event
    assert "DTSTAMP" in processed_event
    assert str(processed_event["SUMMARY"]) == "Missing UID Event"
    assert str(processed_event["X-SOURCE-CALENDAR"]) == "Family"
    assert processed["source"] == "Family"


def test_merge_calendars_returns_sorted_output(monkeypatch, tmp_path):
    first_event = b"""
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:first
SUMMARY:First Event
DTSTART:20260725T120000Z
END:VEVENT
END:VCALENDAR
"""

    second_event = b"""
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:second
SUMMARY:Second Event
DTSTART:20260726T120000Z
END:VEVENT
END:VCALENDAR
"""

    def fake_load_source_calendar(session, source, cache):
        if source["name"] == "Alpha":
            return Calendar.from_ical(first_event)
        return Calendar.from_ical(second_event)

    monkeypatch.setattr(
        "calmerge.merger.load_source_calendar", fake_load_source_calendar
    )

    config = {
        "calendar_name": "Merged Calendar",
        "calendars": [
            {"name": "Alpha", "url": "https://example.com/alpha.ics"},
            {"name": "Beta", "url": "https://example.com/beta.ics"},
        ],
    }

    output = merge_calendars(config, type("Paths", (), {"cache_dir": tmp_path})())

    output_events = list(output.walk("VEVENT"))
    assert len(output_events) == 2
    assert str(output_events[0]["SUMMARY"]) == "First Event"
    assert str(output_events[1]["SUMMARY"]) == "Second Event"
    assert str(output["X-WR-CALNAME"]) == "Merged Calendar"


def test_merge_calendars_raises_for_failed_sources(monkeypatch, tmp_path):
    def fake_load_source_calendar(session, source, cache):
        if source["name"] == "Broken":
            raise RuntimeError("network down")
        return Calendar.from_ical(ICAL)

    monkeypatch.setattr(
        "calmerge.merger.load_source_calendar", fake_load_source_calendar
    )

    with pytest.raises(RuntimeError, match=r"1 calendar\(s\) failed: Broken"):
        merge_calendars(
            {
                "calendar_name": "Merged Calendar",
                "calendars": [
                    {"name": "Broken", "url": "https://example.com/broken.ics"},
                ],
            },
            type("Paths", (), {"cache_dir": tmp_path})(),
        )


def test_create_output_calendar_sets_expected_metadata():
    output = create_output_calendar({"calendar_name": "Demo"})

    assert str(output["X-WR-CALNAME"]) == "Demo"
    assert str(output["X-WR-TIMEZONE"]) == "Europe/London"


def test_merge_calendars_merges_duplicate_events_and_combines_prefixes(
    monkeypatch,
    tmp_path,
):
    first_calendar = b"""
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:sky-camp
SUMMARY:Sky Camp
DTSTART:20260925T180000Z
END:VEVENT
END:VCALENDAR
"""

    second_calendar = b"""
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:sky-camp
SUMMARY:Sky Camp
DTSTART:20260925T180000Z
END:VEVENT
END:VCALENDAR
"""

    def fake_load_source_calendar(session, source, cache):
        if source["name"] == "Lucy":
            return Calendar.from_ical(first_calendar)

        return Calendar.from_ical(second_calendar)

    monkeypatch.setattr(
        "calmerge.merger.load_source_calendar",
        fake_load_source_calendar,
    )

    config = {
        "calendar_name": "Merged Calendar",
        "calendars": [
            {
                "name": "Alice Calendar",
                "prefix": "AliceHols",
                "url": "https://example.com/lucy.ics",
            },
            {
                "name": "Bob Calendar",
                "prefix": "BobHols",
                "url": "https://example.com/alice.ics",
            },
        ],
    }

    output = merge_calendars(
        config,
        type("Paths", (), {"cache_dir": tmp_path})(),
    )

    events = list(output.walk("VEVENT"))

    assert len(events) == 1
    assert str(events[0]["UID"]) == "sky-camp"
    assert str(events[0]["SUMMARY"]) == ("AliceHols/BobHols: Sky Camp")
