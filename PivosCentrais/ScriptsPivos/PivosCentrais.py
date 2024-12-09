import os
import argparse
import rasterio
from shapely.geometry import box
import geopandas as gpd

def determine_closest_year(metadata_year, available_years):
    """Determine the closest year to the metadata year."""
    return min(available_years, key=lambda x: abs(x - metadata_year))

def get_metadata_year(tif_file):
    """Extract the year from the metadata of a .tif file if available."""
    try:
        with rasterio.open(tif_file) as src:
            metadata = src.tags()
            # Assuming the year is stored in a key like "year" or similar in metadata
            for key, value in metadata.items():
                if "year" in key.lower():
                    return int(value)
    except Exception as e:
        print(f"Could not extract year from metadata: {e}")
    return None

def process_raster_and_shapefile(tif_file):
    # Determine the closest available year
    available_years = [2010, 2014, 2017, 2022]

    # Get the year from metadata, default to 2022 if unavailable
    metadata_year = get_metadata_year(tif_file) or 2022
    closest_year = determine_closest_year(metadata_year, available_years)

    # Determine the input shapefile path based on the closest year
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shapefile_input = os.path.join(script_dir, f"../DataPivos/ANA_PivosCentrais_{closest_year}_BR_env.shp")
    shapefile_output = os.path.join(script_dir, "cropped_output.shp")

    # Get bounding box from raster
    with rasterio.open(tif_file) as src:
        bbox = src.bounds
        raster_crs = src.crs

    # Convert bounding box to a GeoDataFrame
    bbox_geom = box(*bbox)
    bbox_gdf = gpd.GeoDataFrame({"geometry": [bbox_geom]}, crs=raster_crs)

    # Read shapefile
    shapefile_gdf = gpd.read_file(shapefile_input)

    # Ensure shapefile is in the same CRS as the raster
    if shapefile_gdf.crs != raster_crs:
        shapefile_gdf = shapefile_gdf.to_crs(raster_crs)

    # Clip shapefile to raster bounding box
    cropped_gdf = gpd.clip(shapefile_gdf, bbox_gdf)

    # Save cropped shapefile
    cropped_gdf.to_file(shapefile_output)
    print(f"Cropped shapefile saved to: {shapefile_output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a raster and shapefile.")
    parser.add_argument("tif_file", help="Path to the input .tif file.")

    args = parser.parse_args()

    process_raster_and_shapefile(args.tif_file)
