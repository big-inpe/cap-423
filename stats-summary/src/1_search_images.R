library(rstac)

items <- rstac::stac("https://data.inpe.br/bdc/stac/v1") |>
    rstac::stac_search(collections = "S2-16D-2",
                       datetime = "2022-01-01/2023-01-01") |>
    rstac::ext_query("bdc:tile" %in% "028022") |>
    rstac::post_request() |>
    rstac::items_fetch()
