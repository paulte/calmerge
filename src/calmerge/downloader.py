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


def create_session() -> requests.Session:
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


def download_calendar(
    session: requests.Session,
    url: str,
    metadata: dict[str, str],
) -> DownloadResult:
    logger.info("Downloading %s", url)

    headers = {"User-Agent": "CalMerge Scout Calendar Aggregator/1.0"}
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
        )
    response.raise_for_status()

    return DownloadResult(
        content=response.content,
        not_modified=False,
        metadata={
            "etag": response.headers.get("ETag", ""),
            "last_modified": response.headers.get("Last-Modified", ""),
        },
    )


def load_source_calendar(
    session: requests.Session,
    source: dict[str, Any],
    cache: CalendarCache,
) -> Calendar:
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

            logger.info(f"Using cached calendar {name} (HTTP 304)")

        else:
            raw_bytes = result.content

            if raw_bytes is None:
                raise RuntimeError(f"No calendar content received for {name}")

            cache.save(
                name,
                raw_bytes,
            )

            logger.info(f"Downloaded new calendar {name}")

        cache.save_metadata(
            name,
            result.metadata,
        )

    except Exception as e:
        logger.warning(f"Failed loading {name} from web: {e}")

        raw_bytes = cache.load(name)

        if raw_bytes is None:
            raise RuntimeError(f"No cached copy available for {name}") from e

        logger.info(f"Using cached calendar {name} (download failed)")

    return Calendar.from_ical(raw_bytes)
