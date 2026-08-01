import os
import subprocess
import sys
from pathlib import Path

import pytest
from icalendar import Calendar

from calmerge import cli

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


def write_config(tmp_path: Path, content: dict) -> Path:
    config_file = tmp_path / "calendars.yaml"
    config_file.write_text(
        "calendar_name: Test Calendar\n"
        "calendars:\n"
        "  - name: Test Source\n"
        "    url: https://example.com/calendar.ics\n"
    )
    return config_file


def test_main_runs_full_pipeline_and_writes_output(tmp_path, monkeypatch):
    config_file = tmp_path / "calendars.yaml"
    config_file.write_text(
        "calendar_name: Test Calendar\n"
        "calendars:\n"
        "  - name: Test Source\n"
        "    url: https://example.com/calendar.ics\n"
    )

    output_dir = tmp_path / "output"
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        "sys.argv",
        [
            "calmerge",
            "--config",
            str(config_file),
            "--cache",
            str(cache_dir),
            "--output",
            str(output_dir),
        ],
    )

    def fake_load_source_calendar(session, source, cache):
        return Calendar.from_ical(ICAL)

    monkeypatch.setattr(
        "calmerge.merger.load_source_calendar",
        fake_load_source_calendar,
    )

    cli.main()

    merged_path = output_dir / "merged.ics"
    assert merged_path.exists()

    merged_calendar = Calendar.from_ical(merged_path.read_bytes())
    assert merged_calendar["X-WR-CALNAME"] == "Test Calendar"

    events = list(merged_calendar.walk("VEVENT"))
    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Test Event"


def test_main_uses_default_paths_when_no_args_are_given(tmp_path, monkeypatch):
    config_file = tmp_path / "calendars.yaml"
    config_file.write_text(
        "calendar_name: Test Calendar\n"
        "calendars:\n"
        "  - name: Test Source\n"
        "    url: https://example.com/calendar.ics\n"
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["calmerge"])

    def fake_load_source_calendar(session, source, cache):
        return Calendar.from_ical(ICAL)

    monkeypatch.setattr(
        "calmerge.merger.load_source_calendar",
        fake_load_source_calendar,
    )

    cli.main()

    merged_path = tmp_path / "calendars" / "merged.ics"
    assert merged_path.exists()


def test_main_propagates_merge_failures(tmp_path, monkeypatch):
    config_file = tmp_path / "calendars.yaml"
    config_file.write_text(
        "calendar_name: Test Calendar\n"
        "calendars:\n"
        "  - name: Test Source\n"
        "    url: https://example.com/calendar.ics\n"
    )

    output_dir = tmp_path / "output"
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        "sys.argv",
        [
            "calmerge",
            "--config",
            str(config_file),
            "--cache",
            str(cache_dir),
            "--output",
            str(output_dir),
        ],
    )

    def fake_merge_calendars(config, paths):
        raise RuntimeError("merge failed")

    monkeypatch.setattr("calmerge.cli.merge_calendars", fake_merge_calendars)

    with pytest.raises(RuntimeError, match="merge failed"):
        cli.main()


def test_module_entrypoint_runs_main_when_executed_directly(tmp_path, monkeypatch):
    config_file = tmp_path / "calendars.yaml"
    config_file.write_text(
        "calendar_name: Test Calendar\n"
        "calendars:\n"
        "  - name: Test Source\n"
        "    url: https://example.com/calendar.ics\n"
    )

    output_dir = tmp_path / "output"
    cache_dir = tmp_path / "cache"

    site_dir = tmp_path / "sitecustomize"
    site_dir.mkdir()
    (site_dir / "sitecustomize.py").write_text(
        "from icalendar import Calendar\n"
        "from calmerge import merger\n"
        'ICAL = b"""\n'
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "BEGIN:VEVENT\n"
        "UID:test-event\n"
        "SUMMARY:Test Event\n"
        "DTSTART:20260725T120000Z\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
        '"""\n'
        "def fake_load_source_calendar(session, source, cache):\n"
        "    return Calendar.from_ical(ICAL)\n"
        "merger.load_source_calendar = fake_load_source_calendar\n"
    )

    source_dir = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(site_dir)
        + os.pathsep
        + str(source_dir)
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "calmerge.cli",
            "--config",
            str(config_file),
            "--cache",
            str(cache_dir),
            "--output",
            str(output_dir),
        ],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    merged_path = output_dir / "merged.ics"
    assert merged_path.exists()
