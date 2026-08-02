from icalendar import Event

from calmerge.exclusions import should_exclude_event


def create_event(
    summary: str = "",
    description: str = "",
    location: str = "",
) -> Event:
    event = Event()

    event.add(
        "summary",
        summary,
    )

    if description:
        event.add(
            "description",
            description,
        )

    if location:
        event.add(
            "location",
            location,
        )

    return event


def create_source(
    name: str = "Test Calendar",
    prefix: str = "Test",
) -> dict:
    return {
        "name": name,
        "prefix": prefix,
    }


def test_no_rules_does_not_exclude_event():
    event = create_event(
        summary="Normal event",
    )

    source = create_source()

    assert (
        should_exclude_event(
            event,
            source,
            [],
        )
        is False
    )


def test_matching_summary_regex_excludes_event():
    event = create_event(
        summary="Cancelled camp",
    )

    source = create_source()

    rules = [
        {
            "id": "ignore-cancelled",
            "event": {
                "summary": {
                    "regex": "(?i)cancelled",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is True
    )


def test_non_matching_summary_regex_keeps_event():
    event = create_event(
        summary="Summer camp",
    )

    source = create_source()

    rules = [
        {
            "id": "ignore-cancelled",
            "event": {
                "summary": {
                    "regex": "(?i)cancelled",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is False
    )


def test_matching_calendar_name_excludes_event():
    event = create_event(
        summary="Any event",
    )

    source = create_source(
        name="1st Malden Scout Program",
    )

    rules = [
        {
            "id": "ignore-programs",
            "calendar": {
                "name": {
                    "regex": "Program$",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is True
    )


def test_non_matching_calendar_name_keeps_event():
    event = create_event(
        summary="Any event",
    )

    source = create_source(
        name="1st Malden Scout Events",
    )

    rules = [
        {
            "id": "ignore-programs",
            "calendar": {
                "name": {
                    "regex": "Program$",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is False
    )


def test_matching_calendar_prefix_excludes_event():
    event = create_event(
        summary="Any event",
    )

    source = create_source(
        prefix="Polyapes",
    )

    rules = [
        {
            "id": "ignore-polyapes",
            "calendar": {
                "prefix": {
                    "regex": "^Polyapes$",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is True
    )


def test_event_and_calendar_conditions_both_required():
    event = create_event(
        summary="Committee Meeting",
    )

    source = create_source(
        name="Polyapes",
    )

    rules = [
        {
            "id": "ignore-polyapes-meetings",
            "calendar": {
                "prefix": {
                    "regex": "^Other$",
                },
            },
            "event": {
                "summary": {
                    "regex": "Meeting",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is False
    )


def test_multiple_rules_are_or_conditions():
    event = create_event(
        summary="Committee Meeting",
    )

    source = create_source(
        name="Normal Calendar",
    )

    rules = [
        {
            "id": "ignore-cancelled",
            "event": {
                "summary": {
                    "regex": "Cancelled",
                },
            },
        },
        {
            "id": "ignore-meetings",
            "event": {
                "summary": {
                    "regex": "Meeting",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is True
    )


def test_multiple_calendar_conditions_are_and():
    event = create_event(
        summary="Any event",
    )

    source = create_source(
        name="1st Malden Scout Program",
        prefix="Scouts",
    )

    rules = [
        {
            "id": "ignore-specific-calendar",
            "calendar": {
                "name": {
                    "regex": "Program$",
                },
                "prefix": {
                    "regex": "^Cubs$",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is False
    )


def test_missing_event_field_does_not_match():
    event = create_event(
        summary="Normal event",
    )

    source = create_source()

    rules = [
        {
            "id": "ignore-location",
            "event": {
                "location": {
                    "regex": "HQ",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is False
    )


def test_all_event_conditions_must_match():
    event = create_event(
        summary="Committee Meeting",
        location="HQ",
    )

    source = create_source()

    rules = [
        {
            "id": "ignore-specific-event",
            "event": {
                "summary": {
                    "regex": "Committee",
                },
                "location": {
                    "regex": "Remote",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is False
    )


def test_all_event_conditions_match():
    event = create_event(
        summary="Committee Meeting",
        location="Remote",
    )

    source = create_source()

    rules = [
        {
            "id": "ignore-remote-committee",
            "event": {
                "summary": {
                    "regex": "Committee",
                },
                "location": {
                    "regex": "Remote",
                },
            },
        },
    ]

    assert (
        should_exclude_event(
            event,
            source,
            rules,
        )
        is True
    )
