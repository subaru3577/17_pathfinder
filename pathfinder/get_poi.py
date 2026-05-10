import logging

from pathfinder import Coordinate
import httpx

logger = logging.getLogger(__name__)

def get_poi_coordinates(place_name: str) -> Coordinate:
    """Get coordinate for a place using OpenStreetMap.
    
    Argument:
    ----
    place_name: A Point of Interest (POI) to search coordnate.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": "your-library/1.0"}
    response = httpx.get(url, params=params, headers=headers)
    data = response.json()
    if not data:
        raise ValueError(f"{place_name} not found.")
    logger.info(f"Found coordinate for {place_name}.")
    return Coordinate(float(data[0]["lon"]), float(data[0]["lat"]), )

