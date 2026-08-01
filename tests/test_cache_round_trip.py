from calmerge.cache import CalendarCache


def test_cache_round_trip(tmp_path):
    cache = CalendarCache(tmp_path)

    cache.save("test", b"hello")

    assert cache.load("test") == b"hello"


def test_load_missing_calendar_returns_none(tmp_path):
    cache = CalendarCache(tmp_path)

    assert cache.load("missing") is None
