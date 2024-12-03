library(sits)
library(matrixStats)

identify_crops <- function(current_date, bands, multicores, output_dir) {
    bands_median <- readRDS("./data/derived/bands_median.rds")

    tile <- sits_cube(
        source = "BDC",
        collection = "SENTINEL-2-16D",
        tiles = "028022",
        start_date = "2021-06-26",
        end_date = "2021-06-26",
        bands = bands
    )

    block <- c("nrows" = 512, "ncols" = 512)

    chunks <- sits:::.tile_chunks_create(
        tile = tile,
        overlap = 0,
        block = block
    )

    out_file <- sits:::.file_derived_name(
        tile = tile,
        band = "probs",
        version = "v1",
        output_dir = output_dir
    )

    sits:::.parallel_start(
        workers = multicores, log = FALSE,
        output_dir = output_dir
    )
    on.exit(sits:::.parallel_stop(), add = TRUE)
    block_files <- sits:::.jobs_map_parallel_chr(chunks, function(chunk) {
        # Job block
        block <- sits:::.block(chunk)
        # Block file name
        block_file <- sits:::.file_block_name(
            pattern = sits:::.file_pattern(out_file),
            block = block,
            output_dir = output_dir
        )
        # Resume processing in case of failure
        if (sits:::.raster_is_valid(block_file)) {
            return(block_file)
        }
        # Read and preprocess values
        values <- sits:::.classify_data_read(
            tile = tile,
            block = block,
            bands = bands,
            base_bands = NULL,
            ml_model = NULL,
            impute_fn = identity,
            filter_fn = NULL
        )

        values <- purrr::map_dfc(bands_median, function(band_median) {
            median <- dplyr::filter(
                band_median, .data[["Index"]] == current_date
            ) |> dplyr::select(-"Index") |> as.matrix()


            res <- unname(sqrt(sweep(values, 2, median[1,])^2))
            matrixStats::rowMedians(res)
        })

        values <- as.matrix(values)
        values <- matrixStats::rowMins(values) / values

        # Prepare probability to be saved
        band_conf <- sits:::.conf_derived_band(
            derived_class = "probs_cube",
            band = "probs"
        )
        scale <- sits:::.scale(band_conf)
        if ( sits:::.has(scale) && scale != 1) {
            values <- values / scale
        }
        # Log
        sits:::.debug_log(
            event = "start_block_data_save",
            key = "file",
            value = block_file
        )
        # Prepare and save results as raster
        sits:::.raster_write_block(
            files = block_file,
            block = block,
            bbox =  sits:::.bbox(chunk),
            values = values,
            data_type =  sits:::.data_type(band_conf),
            missing_value =  sits:::.miss_value(band_conf),
            crop_block = NULL
        )
        # Free memory
        gc()
        # Returned block file
        block_file
    }, progress = TRUE)

    probs_tile <- sits:::.tile_derived_merge_blocks(
        file = out_file,
        band = "probs",
        labels = labels,
        base_tile = tile,
        block_files = block_files,
        derived_class = "probs_cube",
        multicores = 6,
        update_bbox = FALSE
    )

    probs_tile
}

probs_tile <- identify_crops(
    current_date = "2021-06-26",
    bands = c(""),
    multicores = 6,
    output_dir = "./data/derived/"
)

probs_smooth <- sits_smooth(
    probs_tile,
    window_size = 9,
    smoothness = 20,
    memsize = 10,
    multicores = 6,
    output_dir = "./data/derived/",
    version = "v1"
)

class <- sits_label_classification(
    probs_smooth,
    memsize = 10,
    multicores = 6,
    output_dir = "./data/derived/",
)
