from pathlib import Path

from calmerge.cache import CalendarCache
from calmerge.downloader import download_calendar


class MockResponse:
    def __init__(self):
        self.status_code = 304
        self.content = b""
        self.headers = {}


class MockSession:
    def get(self, url, headers, timeout):
        assert headers["If-None-Match"] == '"test-etag"'
        assert headers["If-Modified-Since"] == "Sat, 25 Jul 2026 12:00:00 GMT"
        return MockResponse()


def test_http_304_uses_cache(tmp_path: Path):
    cache = CalendarCache(tmp_path)

    calendar_name = "Test Calendar"

    cached_calendar = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test-event
SUMMARY:Cached Event
DTSTART:20260725T120000Z
END:VEVENT
END:VCALENDAR
"""

    metadata = {
        "etag": '"test-etag"',
        "last_modified": "Sat, 25 Jul 2026 12:00:00 GMT",
    }

    cache.save(
        calendar_name,
        cached_calendar,
    )

    cache.save_metadata(
        calendar_name,
        metadata,
    )

    result = download_calendar(
        MockSession(),
        "https://example.com/calendar.ics",
        metadata,
    )

    assert result.not_modified is True
    assert result.content is None
    assert result.metadata == metadata

    assert cache.load(calendar_name) == cached_calendar
