library(terra)

#
# Read TerraClass rast
#
tc_rast <- terra::rast("./data/raw/TC_ROI.tif")


samples <- terra::spatSample(
    x = tc_rast,
    size = 1000,
    method = "stratified",
    values = TRUE,
    as.points = TRUE
)

samples <- sf::st_as_sf(samples)

samples <- samples |>
    dplyr::mutate(
        label = dplyr::case_when(
            TC_ROI_2022 %in% c(1, 2) ~ "vegetacao",
            TC_ROI_2022 %in% c(9)  ~ "silvicultura",
            TC_ROI_2022 %in% c(11) ~ "pastagem",
            TC_ROI_2022 %in% c(12) ~ "perene",
            TC_ROI_2022 %in% c(13) ~ "semi-perene",
            TC_ROI_2022 %in% c(14) ~ "temporaria-1-ciclo",
            TC_ROI_2022 %in% c(15) ~ "temporaria-mais-1-ciclo",
            TC_ROI_2022 %in% c(23) ~ "agua"
        )
    )


samples_filtered <- dplyr::slice_sample(
    samples,
    by = dplyr::all_of("label"),
    n = 150
)

samples_filtered <- dplyr::filter(
    samples_filtered, label != "semi-perene"
)

saveRDS(samples_filtered, "./data/derived/samples_filtered.rds")
