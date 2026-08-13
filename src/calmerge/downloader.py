from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests
from icalendar import Calendar
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .cache import CalendarCache

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    content: bytes | None
    not_modified: bool
    metadata: dict[str, str]
    content_type: str


def create_session() -> requests.Session:
    """Create an HTTP session with retry handling."""
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def validate_calendar_content(
    content: bytes,
    *,
    content_type: str = "",
) -> Calendar:
    """Validate and parse downloaded iCalendar content.

    The response must contain a VCALENDAR component and must be
    successfully parsed by the icalendar library.

    Content-Type is recorded for diagnostics but is deliberately not
    used as the sole validation mechanism because some calendar
    providers return incorrect MIME types.
    """
    if not content:
        raise ValueError("Calendar response was empty")

    if b"BEGIN:VCALENDAR" not in content.upper():
        preview = (
            content[:100]
            .decode(
                "utf-8",
                errors="replace",
            )
            .strip()
        )

        raise ValueError(
            "Response does not contain an iCalendar VCALENDAR component "
            f"(Content-Type: {content_type or 'missing'}, "
            f"response begins with: {preview!r})"
        )

    try:
        calendar = Calendar.from_ical(content)
    except Exception as exc:
        raise ValueError(
            "Response contains VCALENDAR but could not be parsed "
            "as iCalendar "
            f"(Content-Type: {content_type or 'missing'})"
        ) from exc

    if calendar.name != "VCALENDAR":
        raise ValueError(
            f"Parsed calendar has unexpected component type: {calendar.name}"
        )

    return calendar


def download_calendar(
    session: requests.Session,
    url: str,
    metadata: dict[str, str],
) -> DownloadResult:
    """Download a calendar, using conditional request metadata."""
    logger.info("Downloading %s", url)

    headers = {
        "User-Agent": "CalMerge Scout Calendar Aggregator/1.0",
    }

    if metadata.get("etag"):
        headers["If-None-Match"] = metadata["etag"]

    if metadata.get("last_modified"):
        headers["If-Modified-Since"] = metadata["last_modified"]

    response = session.get(
        url,
        headers=headers,
        timeout=30,
    )

    if response.status_code == 304:
        return DownloadResult(
            content=None,
            not_modified=True,
            metadata=metadata,
            content_type="",
        )

    response.raise_for_status()

    return DownloadResult(
        content=response.content,
        not_modified=False,
        metadata={
            "etag": response.headers.get("ETag", ""),
            "last_modified": response.headers.get("Last-Modified", ""),
        },
        content_type=response.headers.get("Content-Type", ""),
    )


def load_source_calendar(
    session: requests.Session,
    source: dict[str, Any],
    cache: CalendarCache,
) -> Calendar:
    """Load and validate a source calendar, falling back to cache."""
    name = source["name"]
    url = source["url"]

    try:
        metadata = cache.load_metadata(name)

        result = download_calendar(
            session,
            url,
            metadata,
        )

        if result.not_modified:
            raw_bytes = cache.load(name)

            if raw_bytes is None:
                raise RuntimeError(
                    f"Server returned 304 but no cached calendar exists for {name}"
                )

            logger.info(
                "Using cached calendar %s (HTTP 304)",
                name,
            )

            # Validate the cached copy as well.
            calendar = validate_calendar_content(raw_bytes)

        else:
            raw_bytes = result.content

            if raw_bytes is None:
                raise RuntimeError(f"No calendar content received for {name}")

            # Validate BEFORE writing anything to the cache.
            calendar = validate_calendar_content(
                raw_bytes,
                content_type=result.content_type,
            )

            cache.save(
                name,
                raw_bytes,
            )

            logger.info(
                "Downloaded and validated calendar %s",
                name,
            )

        cache.save_metadata(
            name,
            result.metadata,
        )

        return calendar

    except Exception as exc:
        logger.warning(
            "Failed loading %s from web: %s",
            name,
            exc,
        )

        raw_bytes = cache.load(name)

        if raw_bytes is None:
            raise RuntimeError(f"No cached copy available for {name}") from exc

        logger.info(
            "Using cached calendar %s (download failed)",
            name,
        )

        try:
            return validate_calendar_content(raw_bytes)
        except Exception as cache_exc:
            raise RuntimeError(f"Cached calendar for {name} is invalid") from cache_exc
