from typing import Literal
import logging
from dataclasses import dataclass, field
from functools import cached_property

import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from networkx import Graph
from shapely.geometry import LineString, Point


logger = logging.getLogger(__name__)
@dataclass
class Coordinate:
    """Coordinate dataclass."""

    longitude: float
    latitude: float

    def __post_init__(self):
        if (not isinstance(self.longitude, float)) or (
            not isinstance(self.latitude, float)
        ):
            raise TypeError(
                "longitude and latitude must be float:"
                f"- longitude: {type(self.longitude)}"
                f"- latitude: {type(self.latitude)}"
            )
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        
    @property
    def point(self) -> Point:
        """Shapely Point geometry using the coordinate."""
        return Point(self.longitude, self.latitude)

    @property
    def point_crs_df(self, epsg:int = 27700) -> gpd.GeoDataFrame:
        """Return GeoDataframe with CRS 27700."""
        gdf = gpd.GeoDataFrame(geometry=[self.point], crs=4326)
        return gdf.to_crs(epsg=epsg)        


_NETWORK_TYPE = Literal["walk", "drive"]

class Network:
    """Network class for running analysis."""

    def __init__(
        self,
        place_name: str = "Leeds, United Kingdom",
        network_type: _NETWORK_TYPE = "walk",
    ):
        """Instantiate Network class.

        Args:
            place_name: Name of location to get network.
            network_type: Network type to get. Normally "walk" or "drive".
        """
        self.place_name = place_name
        self.network_type = network_type

        self.graph_nodes: gpd.GeoDataFrame | None = None
        self.graph_edges: gpd.GeoDataFrame | None = None
        self.graph_edges_unique: gpd.GeoDataFrame | None = None

        self._get_network()

    @cached_property
    def graph(self) -> Graph:
        """Get network graph from osmnx."""
        return ox.graph_from_place(self.place_name, network_type=self.network_type)

    def _get_network(self) -> None:
        """Get network graph and its nodes and edges from OSM."""
        self.graph_nodes, self.graph_edges = ox.convert.graph_to_gdfs(
            self.graph,
            nodes=True,
            edges=True,
            node_geometry=True,
            fill_edge_geometry=True,
        )
        self.graph_nodes = self.graph_nodes.to_crs(27700).reset_index(drop=False)
        self.graph_edges = self.graph_edges.to_crs(27700).reset_index(drop=False)
        self.graph_edges_unique = self.graph_edges.sort_values(
            "length"
        ).drop_duplicates(subset=["u", "v"])

    def find_distance_path_by_shortest(
        self,
        source_coordinate: Coordinate,
        search_distance: int = 10000,
        tolerance: int = 10,
    ) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Get all nodes at the passed distance within the tolerance from a source point and their shortest path.

        Processing:
        -   Find the nearest node in the graph from the source.
        -   Find the shortest path from the source to all nodes in the graph.
        -   Extract nodes with distance within the tolerance around the search_distance.
        -   Extract nodes df and their shortest path from the source.
        -   Generate shortest path df dissolving geometries of nodes in each path.

        Arguments:
        ----
        - source_point: Coordinate dataclass of Source point to search shortest distance.
        - search_distance: Distance to search nodes and edges (m).
        - tolerance: Acceptable tolerance from search_distance (m).

        """
        logger.info("Searching shortest path from \n"
                    f"- from {source_coordinate}\n"
                    f"- distance {search_distance}m\n"
                    f"- tolerance {tolerance}m"
                    )
        if not isinstance(source_coordinate, Coordinate):
            raise TypeError(
                f"source_coordinate must be tuple, not {type(source_coordinate)}"
            )
        if not isinstance(search_distance, int):
            raise TypeError(f"search_distance must be int, not {type(search_distance)}")

        if (self.graph is None) | (self.graph_nodes is None):
            raise NotImplementedError("Graph is not set yet.")

        nearest_node = ox.distance.nearest_nodes(
            self.graph, source_coordinate.longitude, source_coordinate.latitude
        )
        if not isinstance(nearest_node, int):
            raise TypeError(f"Multiple nearest node found: {nearest_node}")

        distances, paths = nx.single_source_dijkstra(
            self.graph, source=nearest_node, weight="length"
        )
        nodes_within = [
            node
            for node, distance in distances.items()
            if (search_distance - tolerance)
            <= distance
            <= (search_distance + tolerance)
        ]
        nodes_within_df = self.graph_nodes[self.graph_nodes["osmid"].isin(nodes_within)]

        # shortest paths exmaple: paths = {"A": ["A"],"B": ["A", "B"],}
        nodes_within_paths = {node: paths[node] for node in nodes_within}

        paths_within_df = pd.DataFrame(
            {"node": nodes_within_paths.keys(), "path": nodes_within_paths.values()}
        )
        paths_within_df["geometry"] = paths_within_df["path"].apply(
            lambda path: self._path_to_linestring(path)
        )
        paths_within_df = (gpd.GeoDataFrame(
            paths_within_df, geometry="geometry", crs=27700)
            .drop(columns=['path'])
            .rename(columns={'node': 'osmid'}))
        paths_within_df["length"] = paths_within_df["geometry"].length.round(0)
        paths_within_df['route_id'] = paths_within_df.index + 1

        nodes_within_df = nodes_within_df.reset_index(drop=True)
        nodes_within_df = nodes_within_df[['osmid', 'geometry']]
        nodes_within_df['attribute'] = 'goal'

        start_point = source_coordinate.point_crs_df
        start_point['attribute'] = 'start'
        nodes_within_df = pd.concat([nodes_within_df, start_point])

        return nodes_within_df, paths_within_df

    def _path_to_linestring(self, path: int) -> LineString:
        if self.graph_nodes is None:
            raise ValueError("graph nodes has not been set.")
        coords = (
            self.graph_nodes.set_index("osmid")
            .loc[path]
            .geometry.apply(lambda point: (point.x, point.y))
            .tolist()
        )
        return LineString(coords)
