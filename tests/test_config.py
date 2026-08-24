"""Config-driven, not hardcoded: the values the pipeline depends on must exist in
configs/ and be internally consistent."""

from datetime import datetime

import pytest

from src.utils.config import load_config, resolve_path

REQUIRED_KEYS = [
    "time.timezone",
    "time.start_date",
    "time.end_date",
    "time.interval_minutes",
    "time.horizons",
    "split.train.start",
    "split.train.end",
    "split.validate.start",
    "split.validate.end",
    "split.test.start",
    "split.test.end",
    "dev_sample.start",
    "dev_sample.end",
    "cleaning.min_duration_seconds",
    "cleaning.max_duration_seconds",
    "cleaning.bbox.lat_min",
    "calendar.morning_rush.start_hour",
    "calendar.evening_rush.end_hour",
    "station_registry.coord_jump_km_threshold",
    "weather.latitude",
    "weather.longitude",
    "sources.citibike_trip_dir",
]


@pytest.mark.parametrize("key", REQUIRED_KEYS)
def test_required_key_present(cfg, key):
    assert cfg.dotted(key) is not None


def test_overlays_load():
    for overlay in ("h3", "s2", "lightgbm", "tft", "stgnn"):
        assert load_config(overlay) is not None


def test_splits_are_chronological_and_contiguous(cfg):
    train, validate, test = (cfg.dotted(f"split.{name}") for name in ("train", "validate", "test"))
    as_date = datetime.fromisoformat
    assert as_date(train["start"]) < as_date(train["end"])
    assert as_date(train["end"]) < as_date(validate["start"])
    assert as_date(validate["end"]) < as_date(test["start"])
    assert as_date(test["end"]) <= as_date(cfg.dotted("time.end_date"))
    assert as_date(train["start"]) >= as_date(cfg.dotted("time.start_date"))
    # no gaps: each split starts the day after the previous one ends
    assert (as_date(validate["start"]) - as_date(train["end"])).days == 1
    assert (as_date(test["start"]) - as_date(validate["end"])).days == 1


def test_dev_sample_is_seven_days_inside_train(cfg):
    start = datetime.fromisoformat(cfg.dotted("dev_sample.start"))
    end = datetime.fromisoformat(cfg.dotted("dev_sample.end"))
    assert (end - start).days == 6, "dev sample must span 7 calendar days"
    train = cfg.dotted("split.train")
    assert datetime.fromisoformat(train["start"]) <= start
    assert end <= datetime.fromisoformat(train["end"])


def test_interval_divides_the_hour(cfg):
    assert 60 % cfg.dotted("time.interval_minutes") == 0


def test_paths_resolve_under_repo(cfg):
    for key in ("paths.raw", "paths.interim", "paths.processed", "paths.dev_sample"):
        assert resolve_path(cfg, key).is_absolute()


def test_traffic_source_is_marked_unusable(cfg):
    """The downloaded DOT traffic export covers 2018 only; the config must say so
    until it is re-pulled, so no phase silently builds features from it."""
    assert cfg.dotted("sources.traffic_usable") is False
