import numpy as np
import pytest

from pathfinder import Coordinate


@pytest.fixture
def sample_coordinate() -> Coordinate:
    """A valid Coordinate for Leeds, UK."""
    return Coordinate(-1.55, 53.80)


class _FakeVariable:
    """Mimics an openmeteo_requests `Variable` object."""

    def __init__(self, values):
        self._values = values

    def ValuesAsNumpy(self):
        return np.array(self._values, dtype=float)

    def ValuesInt64AsNumpy(self):
        return np.array(self._values, dtype=np.int64)


class _FakeSeries:
    """Mimics the `Daily`/`Hourly` accessor of an openmeteo_requests response."""

    def __init__(self, time: int, time_end: int, interval: int, variables_values: list):
        self._time = time
        self._time_end = time_end
        self._interval = interval
        self._variables = [_FakeVariable(values) for values in variables_values]

    def Time(self):
        return self._time

    def TimeEnd(self):
        return self._time_end

    def Interval(self):
        return self._interval

    def Variables(self, index: int):
        return self._variables[index]


class _FakeResponse:
    """Mimics a single response returned by `openmeteo_requests.Client().weather_api()`."""

    def __init__(self, daily: _FakeSeries, hourly: _FakeSeries):
        self._daily = daily
        self._hourly = hourly

    def Daily(self):
        return self._daily

    def Hourly(self):
        return self._hourly


@pytest.fixture
def make_fake_openmeteo_response():
    """Factory to build a fake openmeteo_requests response for mocking `weather_api`.

    Argument:
    ----
    - daily: (time, time_end, interval, [values_per_param, ...])
    - hourly: (time, time_end, interval, [values_per_param, ...])
    """

    def _make(daily: tuple, hourly: tuple) -> _FakeResponse:
        daily_series = _FakeSeries(*daily)
        hourly_series = _FakeSeries(*hourly)
        return _FakeResponse(daily_series, hourly_series)

    return _make
