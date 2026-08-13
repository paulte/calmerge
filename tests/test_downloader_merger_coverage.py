from unittest.mock import Mock

import pytest

from calmerge.downloader import (
    create_session,
    download_calendar,
    load_source_calendar,
    validate_calendar_content,
)

VALID_CALENDAR = b"""\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//CalMerge Test//EN
BEGIN:VEVENT
UID:test-event@example.com
DTSTART:20260813T190000Z
DTSTAMP:20260813T180000Z
SUMMARY:Test event
END:VEVENT
END:VCALENDAR
"""


HTML_RESPONSE = b"""\
<!doctype html>
<html>
<head>
    <title>Error</title>
</head>
<body>
    Something went wrong
</body>
</html>
"""


INVALID_CALENDAR = b"""\
BEGIN:VCALENDAR
VERSION:2.0
THIS IS NOT A VALID ICALENDAR CONTENT LINE
END:VCALENDAR
"""


def test_create_session_configures_retries():
    session = create_session()

    assert "http://" in session.adapters
    assert "https://" in session.adapters

    http_adapter = session.adapters["https://"]

    assert http_adapter.max_retries.total == 3
    assert http_adapter.max_retries.backoff_factor == 1
    assert 429 in http_adapter.max_retries.status_forcelist
    assert 500 in http_adapter.max_retries.status_forcelist
    assert 502 in http_adapter.max_retries.status_forcelist
    assert 503 in http_adapter.max_retries.status_forcelist
    assert 504 in http_adapter.max_retries.status_forcelist
    assert "GET" in http_adapter.max_retries.allowed_methods


def test_validate_calendar_content_accepts_valid_calendar():
    calendar = validate_calendar_content(
        VALID_CALENDAR,
        content_type="text/calendar",
    )

    assert calendar.name == "VCALENDAR"

    events = list(calendar.walk("VEVENT"))

    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Test event"


def test_validate_calendar_content_rejects_empty_content():
    with pytest.raises(
        ValueError,
        match="Calendar response was empty",
    ):
        validate_calendar_content(b"")


def test_validate_calendar_content_rejects_html():
    with pytest.raises(
        ValueError,
        match="does not contain an iCalendar VCALENDAR component",
    ):
        validate_calendar_content(
            HTML_RESPONSE,
            content_type="text/html",
        )


def test_validate_calendar_content_reports_response_preview_for_html():
    with pytest.raises(
        ValueError,
        match="<!doctype html>",
    ):
        validate_calendar_content(
            HTML_RESPONSE,
            content_type="text/html",
        )


def test_validate_calendar_content_rejects_invalid_icalendar():
    with pytest.raises(
        ValueError,
        match="could not be parsed as iCalendar",
    ):
        validate_calendar_content(
            INVALID_CALENDAR,
            content_type="text/calendar",
        )


def test_validate_calendar_content_accepts_valid_calendar_with_wrong_content_type():
    calendar = validate_calendar_content(
        VALID_CALENDAR,
        content_type="text/plain",
    )

    assert calendar.name == "VCALENDAR"


def test_download_calendar_returns_calendar_content():
    session = Mock()

    session.get.return_value = Mock(
        status_code=200,
        content=VALID_CALENDAR,
        headers={
            "Content-Type": "text/calendar",
            "ETag": '"abc123"',
            "Last-Modified": "Wed, 12 Aug 2026 12:00:00 GMT",
        },
    )

    result = download_calendar(
        session,
        "https://example.com/calendar.ics",
        {},
    )

    assert result.content == VALID_CALENDAR
    assert result.not_modified is False
    assert result.content_type == "text/calendar"
    assert result.metadata == {
        "etag": '"abc123"',
        "last_modified": "Wed, 12 Aug 2026 12:00:00 GMT",
    }

    session.get.assert_called_once()


def test_download_calendar_sends_conditional_request_headers():
    session = Mock()

    session.get.return_value = Mock(
        status_code=200,
        content=VALID_CALENDAR,
        headers={
            "Content-Type": "text/calendar",
            "ETag": '"new-etag"',
            "Last-Modified": "Thu, 13 Aug 2026 12:00:00 GMT",
        },
    )

    metadata = {
        "etag": '"old-etag"',
        "last_modified": "Wed, 12 Aug 2026 12:00:00 GMT",
    }

    download_calendar(
        session,
        "https://example.com/calendar.ics",
        metadata,
    )

    _, kwargs = session.get.call_args

    assert kwargs["headers"]["If-None-Match"] == '"old-etag"'
    assert kwargs["headers"]["If-Modified-Since"] == "Wed, 12 Aug 2026 12:00:00 GMT"
    assert kwargs["headers"]["User-Agent"] == "CalMerge Scout Calendar Aggregator/1.0"
    assert kwargs["timeout"] == 30


def test_download_calendar_handles_304():
    session = Mock()

    session.get.return_value = Mock(
        status_code=304,
        content=b"",
        headers={},
    )

    metadata = {
        "etag": '"abc123"',
        "last_modified": "Wed, 12 Aug 2026 12:00:00 GMT",
    }

    result = download_calendar(
        session,
        "https://example.com/calendar.ics",
        metadata,
    )

    assert result.content is None
    assert result.not_modified is True
    assert result.metadata == metadata
    assert result.content_type == ""


def test_download_calendar_raises_for_http_error():
    session = Mock()

    response = Mock()
    response.status_code = 404
    response.raise_for_status.side_effect = RuntimeError("404 error")

    session.get.return_value = response

    with pytest.raises(RuntimeError, match="404 error"):
        download_calendar(
            session,
            "https://example.com/calendar.ics",
            {},
        )


def test_load_source_calendar_downloads_valid_calendar_and_caches_it(
    tmp_path,
):
    session = Mock()

    session.get.return_value = Mock(
        status_code=200,
        content=VALID_CALENDAR,
        headers={
            "Content-Type": "text/calendar",
            "ETag": '"abc123"',
            "Last-Modified": "Wed, 12 Aug 2026 12:00:00 GMT",
        },
    )

    from calmerge.cache import CalendarCache

    cache = CalendarCache(tmp_path)

    source = {
        "name": "Test Calendar",
        "url": "https://example.com/calendar.ics",
    }

    calendar = load_source_calendar(
        session,
        source,
        cache,
    )

    assert calendar.name == "VCALENDAR"
    assert cache.load("Test Calendar") == VALID_CALENDAR

    metadata = cache.load_metadata("Test Calendar")

    assert metadata == {
        "etag": '"abc123"',
        "last_modified": "Wed, 12 Aug 2026 12:00:00 GMT",
    }


def test_invalid_download_does_not_overwrite_valid_cache(tmp_path):
    session = Mock()

    session.get.return_value = Mock(
        status_code=200,
        content=HTML_RESPONSE,
        headers={
            "Content-Type": "text/html",
        },
    )

    from calmerge.cache import CalendarCache

    cache = CalendarCache(tmp_path)

    cache.save(
        "Test Calendar",
        VALID_CALENDAR,
    )

    source = {
        "name": "Test Calendar",
        "url": "https://example.com/calendar.ics",
    }

    calendar = load_source_calendar(
        session,
        source,
        cache,
    )

    events = list(calendar.walk("VEVENT"))

    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Test event"

    # The invalid HTML response must never replace the valid cache.
    assert cache.load("Test Calendar") == VALID_CALENDAR


def test_invalid_download_without_cache_raises_clear_error(tmp_path):
    session = Mock()

    session.get.return_value = Mock(
        status_code=200,
        content=HTML_RESPONSE,
        headers={
            "Content-Type": "text/html",
        },
    )

    from calmerge.cache import CalendarCache

    cache = CalendarCache(tmp_path)

    source = {
        "name": "Test Calendar",
        "url": "https://example.com/calendar.ics",
    }

    with pytest.raises(
        RuntimeError,
        match="No cached copy available for Test Calendar",
    ):
        load_source_calendar(
            session,
            source,
            cache,
        )


def test_valid_download_replaces_existing_cache(tmp_path):
    session = Mock()

    new_calendar = VALID_CALENDAR.replace(
        b"Test event",
        b"New event",
    )

    session.get.return_value = Mock(
        status_code=200,
        content=new_calendar,
        headers={
            "Content-Type": "text/calendar",
        },
    )

    from calmerge.cache import CalendarCache

    cache = CalendarCache(tmp_path)

    old_calendar = VALID_CALENDAR.replace(
        b"Test event",
        b"Old event",
    )

    cache.save(
        "Test Calendar",
        old_calendar,
    )

    source = {
        "name": "Test Calendar",
        "url": "https://example.com/calendar.ics",
    }

    calendar = load_source_calendar(
        session,
        source,
        cache,
    )

    events = list(calendar.walk("VEVENT"))

    assert str(events[0]["SUMMARY"]) == "New event"
    assert cache.load("Test Calendar") == new_calendar


def test_304_uses_cached_calendar(tmp_path):
    session = Mock()

    session.get.return_value = Mock(
        status_code=304,
        content=b"",
        headers={},
    )

    from calmerge.cache import CalendarCache

    cache = CalendarCache(tmp_path)

    cache.save(
        "Test Calendar",
        VALID_CALENDAR,
    )

    source = {
        "name": "Test Calendar",
        "url": "https://example.com/calendar.ics",
    }

    calendar = load_source_calendar(
        session,
        source,
        cache,
    )

    events = list(calendar.walk("VEVENT"))

    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Test event"


def test_304_without_cache_raises_clear_error(tmp_path):
    session = Mock()

    session.get.return_value = Mock(
        status_code=304,
        content=b"",
        headers={},
    )

    from calmerge.cache import CalendarCache

    cache = CalendarCache(tmp_path)

    source = {
        "name": "Test Calendar",
        "url": "https://example.com/calendar.ics",
    }

    with pytest.raises(
        RuntimeError,
        match="No cached copy available for Test Calendar",
    ):
        load_source_calendar(
            session,
            source,
            cache,
        )


def test_invalid_cached_calendar_fails_clearly(tmp_path):
    session = Mock()

    session.get.return_value = Mock(
        status_code=200,
        content=HTML_RESPONSE,
        headers={
            "Content-Type": "text/html",
        },
    )

    from calmerge.cache import CalendarCache

    cache = CalendarCache(tmp_path)

    cache.save(
        "Test Calendar",
        INVALID_CALENDAR,
    )

    source = {
        "name": "Test Calendar",
        "url": "https://example.com/calendar.ics",
    }

    with pytest.raises(
        RuntimeError,
        match="Cached calendar for Test Calendar is invalid",
    ):
        load_source_calendar(
            session,
            source,
            cache,
        )
