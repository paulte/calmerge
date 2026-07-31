import logging
from pathlib import Path

from icalendar import Calendar

logger = logging.getLogger(__name__)


def write_calendar(
    calendar: Calendar,
    output_dir: Path,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_file = output_dir / "merged.ics"

    temp = output_file.with_suffix(".tmp")

    temp.write_bytes(calendar.to_ical())

    temp.replace(output_file)

    logger.info("Written %s", output_file)
