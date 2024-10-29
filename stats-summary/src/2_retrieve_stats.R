library(terra)
source("./src/0_search_images.R")

assets_names <- rstac::items_assets(items)
assets_names <- setdiff(assets_names, c("PROVENANCE", "thumbnail", "TOTALOB", "CLEAROB", "EVI"))

assets_sum <- lapply(assets_names, function(asset_name) {
    items_filtered <- rstac::assets_select(
        items = items, asset_names = asset_name
    )
    assets_url <- rstac::assets_url(items_filtered, append_gdalvsi = TRUE)

    assets_rast <- terra::rast(assets_url)
    assets_sum <- terra::summary(assets_rast)
    assets_sum <- as.data.frame(t(assets_sum))

    assets_sum <- tidyr::separate_wider_delim(
        assets_sum, cols = "Freq", delim = ":", names = c("stats", "value")
    )

    assets_sum <- dplyr::mutate(
        assets_sum,
        stats = gsub("[[:space:]]", "", .data[["stats"]]),
        value = as.numeric(gsub("[[:space:]]", "", .data[["value"]]))
    )

    assets_sum <- tidyr::pivot_wider(
        assets_sum, names_from = "stats", values_from = "value"
    )

    assets_sum <- assets_sum[, setdiff(colnames(assets_sum), "Var2")]
    colnames(assets_sum) <- c("fid", "min", "firstqu", "median",
                              "mean", "trirdqu", "max")

    assets_sum$band <- asset_name

    assets_sum
})

assts_tbl <- do.call(rbind, assets_sum)

write.csv(assts_tbl, "./data/summary.csv")
