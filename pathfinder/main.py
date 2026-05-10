import logging
from pathlib import Path

from .network import Network
from .get_poi import get_poi_coordinates
from .visualisation import generate_map


logger = logging.getLogger(__name__)

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)


def find_running_routes(
    area_name: str,
    start_poi: str,
    search_distance: int,
    html_export: bool = True,
    gpkg_export: bool = False,
    **kwargs,
):
    """Run the analysis.

    Argument:
    ----
    - area_name:        Area name to get nework data.
    - start_poi:        POI of start point. (e.g. Leeds Station)
    - search_distance:  Distance to search paths (m).
    - html_export:      Export results as an HTML file.
    - gpkg_export:      Export results as gpkg files.
    - kwargs:           Optional arguments for pathfinding. e.g. tolerance=100
    """
    logger.info(
        f"Searching routes in {area_name} from {start_poi} for {search_distance}m."
    )
    network = Network(place_name=area_name)
    source_coordinate = get_poi_coordinates(start_poi)
    nodes_within_df, paths_within_df = network.find_distance_path_by_shortest(
        source_coordinate=source_coordinate, search_distance=10000, **kwargs
    )
    logger.info(f"Found {len(paths_within_df)} path(s).")
    export_title = f"from_{start_poi.replace(' ', '_')}_{search_distance}m"

    if html_export:
        vis_dfs = {"routes": paths_within_df, "points": nodes_within_df}
        output_map_dir = output_dir / f"map_{export_title}.html"
        generate_map(
            dfs=vis_dfs, centre=source_coordinate, output_map_dir=output_map_dir
        )
        logger.info("Exported result as HTML file.")

    if gpkg_export:
        output_path_dir = output_dir / f"path_{export_title}.gpkg"
        output_point_dir = output_dir / f"path_{export_title}.gpkg"
        paths_within_df.to_file(output_path_dir)
        nodes_within_df.to_file(output_point_dir)
        logger.info("Exported result as gpkg files.")
