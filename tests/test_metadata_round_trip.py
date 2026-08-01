from calmerge.cache import CalendarCache


def test_metadata_round_trip(tmp_path):
    cache = CalendarCache(tmp_path)

    cache.save_metadata(
        "test",
        {
            "etag": "12345",
        },
    )

    assert cache.load_metadata("test") == {
        "etag": "12345",
    }


def test_load_metadata_returns_empty_for_invalid_json(tmp_path):
    cache = CalendarCache(tmp_path)
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text("{not valid json}")

    assert cache.load_metadata("test") == {}


def test_save_metadata_recovers_from_invalid_json(tmp_path):
    cache = CalendarCache(tmp_path)
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text("{not valid json}")

    cache.save_metadata(
        "test",
        {
            "etag": "12345",
        },
    )

    assert cache.load_metadata("test") == {
        "etag": "12345",
    }
