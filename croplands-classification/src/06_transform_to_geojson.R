#
# Load package
#
library(terra)

#
# Reading raster
#
r <- terra::rast("./data/derived/SENTINEL-2_MSI_028022_2021-06-26_2021-06-26_class_masked-bin.tif")

#
# Polygonize raster
#
poly <- terra::as.polygons(r)

#
# Add new column
#
poly[["label"]] <- ifelse(poly[["lyr.1"]] == 7, "Agricultura", "Não Agricultura")

#
# Write GeoJson
#
terra::writeVector(
  poly,
  filename = "./data/derived/SENTINEL-2_MSI_028022_2021-06-26_2021-06-26_class_masked-bin.json"
)
