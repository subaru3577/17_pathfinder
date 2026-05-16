import geopandas as gpd
import folium
import logging
from pathlib import Path

from pathfinder import Coordinate

logger = logging.getLogger(__name__)


def generate_map(
    dfs: dict[str, gpd.GeoDataFrame],
    centre: Coordinate,
    output_map_dir: Path,
    key_id_name: str = "route_id",
):
    """Generate interactive map of found routes.

    Argument:
    ----
    -   dfs:            Dict of DataFrames as layer name as a key.
    -   centre:         Coorfinate object of centre point.
    -   output_map_dir: Path of created map for export.
    -   key_id_name:    Column name of Dataframes to group data.

    """
    if not isinstance(centre, Coordinate):
        raise TypeError(f"centre must be Coordinate object, not {type(centre)}")
    if not isinstance(output_map_dir, Path):
        raise TypeError(
            f"output_map_dir must be Path object, not {type(output_map_dir)}"
        )
    map_obj = folium.Map(location=[centre.latitude, centre.longitude], zoom_start=12)

    key_ids = set()
    dfs_vis = {}
    for name, df in dfs.items():
        df_vis = df.to_crs(epsg=4326)
        dfs_vis[name] = df_vis
        key_ids.update(df[key_id_name].unique())

    for key_id in key_ids:
        fg = folium.FeatureGroup(name=f"{key_id_name}_{key_id}")
        for name, df_vis in dfs_vis.items():
            df_vis_id = df_vis[df_vis[key_id_name] == key_id]
            folium.GeoJson(df_vis_id.to_json()).add_to(fg)
        fg.add_to(map_obj)

    folium.Marker(
        location=[centre.latitude, centre.longitude],
        popup="Start",
        tooltip="Centre",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(map_obj)

    folium.LayerControl().add_to(map_obj)
    map_obj.save(output_map_dir)
