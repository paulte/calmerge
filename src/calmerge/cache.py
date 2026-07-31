import json
from pathlib import Path


class CalendarCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def _get_calendar_path(self, name: str) -> Path:
        return self.cache_dir / f"{name}.ics"

    def load(self, name: str) -> bytes | None:
        path = self._get_calendar_path(name)

        if not path.exists():
            return None

        return path.read_bytes()

    def save(self, name: str, content: bytes):
        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._get_calendar_path(name).write_bytes(content)

    def _get_metadata_path(self) -> Path:
        return self.cache_dir / "metadata.json"

    def load_metadata(self, name: str) -> dict[str, str]:
        path = self._get_metadata_path()

        if not path.exists():
            return {}

        try:
            metadata = json.loads(path.read_text())

            return metadata.get(name, {})

        except json.JSONDecodeError:
            return {}

    def save_metadata(
        self,
        name: str,
        metadata: dict[str, str],
    ) -> None:
        path = self._get_metadata_path()

        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():
            try:
                all_metadata = json.loads(path.read_text())
            except json.JSONDecodeError:
                all_metadata = {}
        else:
            all_metadata = {}

        all_metadata[name] = metadata

        path.write_text(
            json.dumps(
                all_metadata,
                indent=2,
                sort_keys=True,
            )
        )
