import logging

from .config import load_config, parse_args
from .merger import merge_calendars
from .output import write_calendar


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    paths = parse_args()

    config = load_config(
        paths.config_file,
    )

    merged = merge_calendars(
        config,
        paths,
    )

    write_calendar(
        merged,
        paths.output_dir,
    )


if __name__ == "__main__":
    main()
