library(sits)
samples_filtered <- readRDS("./data/derived/samples_filtered.rds")

cube <- sits_cube(
    source = "BDC",
    collection = "SENTINEL-2-16D",
    tiles = "028022",
    start_date = "2021-07-01",
    end_date = "2022-08-31",
    bands = c("EVI", "B02", "B8A", "B12", "NDVI", "CLOUD")
)

ts <- sits_get_data(
    cube = cube,
    samples = samples_filtered,
    multicores = 12,
    label_attr = "label"
)

saveRDS(ts, "./data/derived/ts.rds")

plot(
    sits_patterns(sits_select(ts, bands = c("NDVI", "EVI")))
)
