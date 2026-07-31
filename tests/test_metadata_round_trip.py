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
