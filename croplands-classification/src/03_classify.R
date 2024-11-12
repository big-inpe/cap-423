library(sits)

ts <- readRDS("./data/derived/ts.rds")

cube <- sits::sits_cube(
    source = "BDC",
    collection = "SENTINEL-2-16D",
    tiles = "028022",
    start_date = "2021-07-01",
    end_date = "2022-08-31",
    bands = c("EVI", "B02", "B8A", "B12", "NDVI", "CLOUD")
)

rfor_model <- sits_train(
    ts, ml_method = sits::sits_rfor()
)

plot(rfor_model)
saveRDS(rfor_model, "./data/derived/model.rds")
rfor_model <- readRDS("./data/derived/model.rds")

probs_cube <- sits_classify(
    data = cube,
    ml_model = rfor_model,
    multicores = 12,
    memsize = 10,
    output_dir = "./data/derived/"
)

smooth_cube <- sits_smooth(
    cube = probs_cube,
    multicores = 12,
    memsize = 10,
    output_dir = "./data/derived/"
)
