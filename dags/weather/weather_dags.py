from datetime import datetime
import requests
import os

from pathfinder.weather.weather_fetch import fetch_weather
from pathfinder import get_poi_coordinates

from airflow.decorators import dag, task

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

if not SLACK_WEBHOOK_URL:
    raise ValueError("SLACK_WEBHOOK_URL is not set in environment variables")


@dag(
    dag_id="weather_to_slack",
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 7 * * *",
    catchup=False,
    tags=["practice"],
)
def weather_to_slack():
    @task
    def get_coordinates():
        coordinates = get_poi_coordinates("Barbican Station")
        coordinates_dict = {}
        coordinates_dict["longitude"] = coordinates.longitude
        coordinates_dict["latitude"] = coordinates.latitude
        return coordinates_dict

    @task
    def get_weather(coordinates_dict):
        weather = fetch_weather(location=coordinates_dict, find_fine_weather_today=True)
        return weather

    @task
    def notify_slack(weather):
        if weather is None:
            message = "Today's weather is not suitable for running :("
        else:
            message = f"Today's recommended time for running: {weather}"
        payload = {"text": message}
        res = requests.post(SLACK_WEBHOOK_URL, json=payload)
        res.raise_for_status()

    coordinates_dict = get_coordinates()
    weather = get_weather(coordinates_dict)
    notify_slack(weather)


dag = weather_to_slack()
