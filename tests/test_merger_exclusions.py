from icalendar import Calendar

from calmerge.merger import merge_calendars


def test_merge_excludes_matching_events(tmp_path, monkeypatch):
    calendar_file = tmp_path / "test.ics"

    calendar_file.write_text(
        """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:normal-event
DTSTART:20260802T100000Z
SUMMARY:Normal Event
DTEND:20260802T110000Z
END:VEVENT
BEGIN:VEVENT
UID:cancelled-event
DTSTART:20260802T120000Z
SUMMARY:Cancelled Event
DTEND:20260802T130000Z
END:VEVENT
END:VCALENDAR
""",
        encoding="utf-8",
    )

    source_calendar = Calendar.from_ical(
        calendar_file.read_text(
            encoding="utf-8",
        )
    )

    monkeypatch.setattr(
        "calmerge.merger.load_source_calendar",
        lambda session, source, cache: source_calendar,
    )

    config = {
        "calendar_name": "Test Calendar",
        "calendars": [
            {
                "name": "Test Calendar",
                "prefix": "Test",
            },
        ],
        "exclusions": {
            "rules": [
                {
                    "id": "exclude-cancelled",
                    "event": {
                        "summary": {
                            "regex": "Cancelled",
                        },
                    },
                },
            ],
        },
    }

    paths = type(
        "AppPaths",
        (),
        {
            "cache_dir": tmp_path / ".cache",
        },
    )()

    calendar = merge_calendars(
        config,
        paths,
    )

    summaries = [
        str(event.get("SUMMARY")) for event in calendar.walk() if event.name == "VEVENT"
    ]

    assert "Test: Normal Event" in summaries
    assert "Test: Cancelled Event" not in summaries
