import typer
import logging

from pathfinder import find_running_routes

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)
app = typer.Typer(help="Pathfinder CLI")


@app.command()
def run(
    area_name: str = typer.Argument(..., help="area name to get network"),
    start_poi: str = typer.Option(..., "-s", "--start", help="POI as a start point"),
    search_distance: int = typer.Option(
        5000, "-d", "--distance", help="distance (m) to search"
    ),
):
    """Run the pathfinder."""
    find_running_routes(area_name, start_poi, search_distance=search_distance)


def main():
    app()
