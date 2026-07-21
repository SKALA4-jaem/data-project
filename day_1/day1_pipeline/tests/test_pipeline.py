"""Pydantic 날씨 스키마 테스트."""

import pytest
from pydantic import ValidationError

from day_1.day1_pipeline.pipeline import WeatherRecord


def test_weather_record_accepts_valid_data():
    """올바른 날씨 데이터가 검증을 통과하는지 확인한다."""

    record = WeatherRecord(
        latitude=37.55,
        longitude=127.0,
        timezone="Asia/Seoul",
        observed_at=["2026-07-20T00:00", "2026-07-20T01:00"],
        temperature_2m=[23.2, 22.8],
        precipitation_probability=[6, 10],
    )

    assert record.source == "weather"
    assert record.latitude == 37.55
    assert record.temperature_2m == [23.2, 22.8]
    assert record.precipitation_probability == [6, 10]


def test_weather_record_rejects_invalid_probability():
    """강수 확률이 100을 넘으면 검증 오류가 발생하는지 확인한다."""

    with pytest.raises(ValidationError):
        WeatherRecord(
            latitude=37.55,
            longitude=127.0,
            timezone="Asia/Seoul",
            observed_at=["2026-07-20T00:00"],
            temperature_2m=[23.2],
            precipitation_probability=[150],
        )
