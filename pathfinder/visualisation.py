import geopandas as gpd
import folium
import logging
from pathlib import Path

from pathfinder import Coordinate

logger = logging.getLogger(__name__)


def generate_map(
    dfs: dict[str, gpd.GeoDataFrame], centre: Coordinate, output_map_dir: Path
):
    if not isinstance(centre, Coordinate):
        raise TypeError(f"centre must be Coordinate object, not {type(centre)}")
    if not isinstance(output_map_dir, Path):
        raise TypeError(
            f"output_map_dir must be Path object, not {type(output_map_dir)}"
        )
    map_obj = folium.Map(location=[centre.latitude, centre.longitude], zoom_start=12)

    for name, df in dfs.items():
        df_vis = df.to_crs(epsg=4326)
        folium.GeoJson(df_vis.to_json(), name=name).add_to(map_obj)

    folium.Marker(
        location=[centre.latitude, centre.longitude],
        popup="Start",
        tooltip="Centre",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(map_obj)

    map_obj.save(output_map_dir)
