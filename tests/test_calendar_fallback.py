from calmerge.cache import CalendarCache
from calmerge.downloader import load_source_calendar

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


class FailedSession:
    def get(self, *args, **kwargs):
        raise RuntimeError("Network unavailable")


def test_calendar_falls_back_to_cache(tmp_path):
    cache = CalendarCache(tmp_path)

    cache.save(
        "test-calendar",
        ICAL,
    )

    source = {
        "name": "test-calendar",
        "url": "https://example.com/calendar.ics",
    }

    calendar = load_source_calendar(
        FailedSession(),
        source,
        cache,
    )

    events = list(calendar.walk("VEVENT"))

    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Test Event"
