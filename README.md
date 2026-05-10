## Pathfinder

A Python tool to generate interactive maps using OpenStreetMap data and GeoPandas.

## Features
- Get network for the designated area and coordinate for POI
- Find path from POI within the designated distance suitable for running
- Find places using OpenStreetMap Nominatim
- Generate interactive maps and export as a HTML file

## Installation

```bash
git clone https://github.com/subaru3577/17_pathfinder.git
cd 17_pathfinder
uv sync
```

## Script for CLI

1. To find a path for running
```bash
uv run pathfinder "Leeds, United Kingdom" --start "Leeds Station"
```


## Notes

This project uses OpenStreetMap data and Nominatim API.
© OpenStreetMap contributors.
Please respect usage policy: https://operations.osmfoundation.org/policies/nominatim/

This project is not affiliated with OpenStreetMap Foundation.

## License

MIT