library(sits)
library(tidyr)

data <- readRDS("./data/derived/ts.rds")
labels <- sits::sits_labels(data)
bands <- sits::sits_bands(data)

create_median <- function(melted, band) {
    qts <- melted |>
        dplyr::group_by(.data[["Index"]]) |>
        dplyr::summarise(
            med  = stats::median(.data[["value"]]),
        )

    colnames(qts) <- c("Index", band)
    return(dplyr::ungroup(qts)[, band])
}

bands_median <- labels |>
    purrr::map(function(l) {
        lb <- as.character(l)
        # filter only those rows with the same label
        data2 <- dplyr::filter(data, .data[["label"]] == lb)
        # how many time series are to be plotted?
        number <- nrow(data2)
        # what are the band names?
        bands <- sits:::.samples_bands(data2, include_base = FALSE)
        # what are the reference dates?
        ref_dates <- sits:::.samples_timeline(data2)
        # align all time series to the same dates
        data2 <- sits:::.tibble_align_dates(data2, ref_dates)

        bands_stats <- bands |>
            purrr::map(function(band) {
                # select the band to be shown
                band_tb <- sits_select(data2, band)

                melted <- band_tb |>
                    dplyr::select("time_series") |>
                    dplyr::mutate(variable = seq_len(dplyr::n())) |>
                    tidyr::unnest(cols = "time_series")
                names(melted) <- c("Index", "value", "variable")

                qts <- create_median(melted, band)
                # plot the time series together
                # (highlighting the median and quartiles 25% and 75%)
                return(qts)
            })
        bands_tbl <- tibble::tibble(do.call(cbind, bands_stats))
        tibble::add_column(
            bands_tbl,
            Index = sits_timeline(data2),
            .before = 1)
    })

names(bands_median) <- labels
saveRDS(bands_median, "./data/derived/bands_median.rds")
