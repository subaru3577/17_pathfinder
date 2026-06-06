import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
import datetime

from pathfinder import Coordinate


def fetch_weather(
    location: Coordinate | dict[str, float],
    daily_params: list[str] | None = None,
    hourly_params: list[str] | None = None,
    find_fine_weather_today: bool = False,
) -> pd.DataFrame | str | None:
    """Get the weather forcast using Open-Meteo API.

    Argument:
    ----
    - location:         Coordinate object or dictionary of coordinates of the location
                        to get feather forecast for.
    - daily_params:     Parameters (names of parameters) for daily forecast.
    - hourly_params:    Parameters (names of parameters) for hourly forecast.
    - find_fine_weather_today:  Option to return recommeneded time range as text based
                                on the obtained forecast.

    """
    if daily_params is None:
        daily_params = ["sunrise", "sunset"]
    if hourly_params is None:
        hourly_params = [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "snow_depth",
            "weather_code",
        ]
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    if isinstance(location, Coordinate):
        latitude = location.latitude
        longitude = location.longitude
    elif isinstance(location, dict):
        latitude = location["latitude"]
        longitude = location["longitude"]
    else:
        raise TypeError(
            f"location must be Coordnate object or dict, not {type(location)}"
        )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": daily_params,
        "hourly": hourly_params,
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    daily = response.Daily()
    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        )
    }
    for item_id, daily_item in enumerate(daily_params):
        daily_data[f"daily_{daily_item}"] = daily.Variables(
            item_id
        ).ValuesInt64AsNumpy()
        if daily_item in ["sunrise", "sunset"]:
            daily_data[f"daily_{daily_item}"] = pd.to_datetime(
                daily_data[f"daily_{daily_item}"], unit="s", utc=True
            ).tz_convert("Europe/London")

    daily_df = pd.DataFrame(data=daily_data)
    daily_df["date"] = (
        pd.to_datetime(daily_df["date"].dt.tz_convert("Europe/London"))
        .dt.tz_localize(None)
        .dt.date
    )

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_data = {
        "date_time": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }
    for item_id, hourly_item in enumerate(hourly_params):
        hourly_data[hourly_item] = hourly.Variables(item_id).ValuesAsNumpy()

    hourly_df = pd.DataFrame(data=hourly_data)
    hourly_df["date_time"] = hourly_df["date_time"].dt.tz_convert("Europe/London")
    hourly_df["date"] = hourly_df["date_time"].dt.date

    weather_data = hourly_df.merge(daily_df, on=["date"], how="left", validate="m:1")

    if find_fine_weather_today:
        today = pd.to_datetime(datetime.datetime.now()).date()
        toda_weather_data = weather_data[weather_data["date"] == today]
        return _identify_fine_weather(toda_weather_data)

    return weather_data


def _identify_fine_weather(df: pd.DataFrame) -> str | None:
    """Identify time range suitable for running meeting conditions."""
    df = (
        df.copy()
        .set_index(keys=["date_time"])
        .sort_values(by=["date_time"], ascending=True)
    )
    df["fine_weather_flag"] = False
    sunny = df["precipitation_probability"] <= 20
    after_sunrise = df.index > df["daily_sunrise"]
    before_sunset = df.index < df["daily_sunset"]
    df.loc[sunny & after_sunrise & before_sunset, "fine_weather_flag"] = True
    group = (df["fine_weather_flag"] != df["fine_weather_flag"].shift()).cumsum()
    true_blocks = df[df["fine_weather_flag"]].groupby(group)

    fine_weather_time = []
    for _, g in true_blocks:
        start = g.index.min()
        end = g.index.max() + pd.Timedelta(hours=1)
        start_time = start.strftime("%H:%M")
        end_time = end.strftime("%H:%M")
        duration = f"{str(start_time)} to {str(end_time)}"
        fine_weather_time.append(duration)
    if len(fine_weather_time) == 0:
        return None
    return ", ".join(fine_weather_time)
