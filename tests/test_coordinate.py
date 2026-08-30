import pytest
from shapely.geometry import Point

from pathfinder import Coordinate


class TestConstruction:
    """Coordinate.__post_init__ validation."""

    def test_stores_longitude_and_latitude(self, sample_coordinate):
        """A valid Coordinate keeps the longitude and latitude it was given."""
        assert (sample_coordinate.longitude, sample_coordinate.latitude) == (
            -1.55,
            53.80,
        )

    @pytest.mark.parametrize(
        "longitude, latitude",
        [
            (0.0, 0.0),
            (-180.0, -90.0),
            (180.0, 90.0),
            (-1.55, 53.80),
        ],
    )
    def test_accepts_in_range_floats_including_boundaries(self, longitude, latitude):
        """In-range floats are accepted, and the +/-180 / +/-90 limits are inclusive."""
        coord = Coordinate(longitude, latitude)
        assert (coord.longitude, coord.latitude) == (longitude, latitude)

    @pytest.mark.parametrize(
        "longitude, latitude",
        [
            (0, 0),
            (-1, 53.80),
            (-1.55, 54),
        ],
    )
    def test_rejects_non_float_values(self, longitude, latitude):
        """int (or any non-float) longitude/latitude raises TypeError, even when in range."""
        with pytest.raises(TypeError, match="must be float"):
            Coordinate(longitude, latitude)

    @pytest.mark.parametrize(
        "longitude, latitude, match",
        [
            (180.1, 0.0, "Invalid longitude"),
            (-180.1, 0.0, "Invalid longitude"),
            (0.0, 90.1, "Invalid latitude"),
            (0.0, -90.1, "Invalid latitude"),
        ],
    )
    def test_rejects_out_of_range_values(self, longitude, latitude, match):
        """A float just past +/-180 (longitude) or +/-90 (latitude) raises ValueError,
        naming the offending axis."""
        with pytest.raises(ValueError, match=match):
            Coordinate(longitude, latitude)


class TestPoint:
    """Coordinate.point geometry accessor."""

    def test_returns_shapely_point(self, sample_coordinate):
        """.point is a shapely Point instance."""
        assert isinstance(sample_coordinate.point, Point)

    def test_uses_longitude_as_x_and_latitude_as_y(self, sample_coordinate):
        """.point places longitude on x and latitude on y (GIS lon/lat ordering),
        not the other way round."""
        point = sample_coordinate.point
        assert (point.x, point.y) == (
            sample_coordinate.longitude,
            sample_coordinate.latitude,
        )
