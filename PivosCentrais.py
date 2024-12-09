
import os
import argparse
import rasterio
from shapely.geometry import box
import geopandas as gpd

def process_raster_and_shapefile(tif_file):
    # Determine the input shapefile path based on the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shapefile_input = os.path.join(script_dir, "./Data/ANA_PivosCentrais_2022_BR_env.shp")
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
