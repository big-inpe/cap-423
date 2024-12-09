#
# Load package
#
library(sits)

#
# Read terraclass data
#
tc <- sits_cube(
    source = "BDC",
    collection = "SENTINEL-2-16D",
    bands = "class",
    data_dir = "./data/raw/",
    labels = c(
        "0" = "nodata",
        "1" = "VEGETACAO NATURAL PRIMARIA",
        "2" = "VEGETACAO NATURAL SECUNDARIA",
        "9" = "SILVICULTURA",
        "11" = "PASTAGEM",
        "12" = "CULTURA AGRICOLA PERENE",
        "13" = "CULTURA AGRICOLA SEMIPERENE",
        "14" = "CULTURA AGRICOLA TEMPORARIA DE 1 CICLO",
        "15" = "CULTURA AGRICOLA TEMPORARIA DE MAIS DE 1 CICLO",
        "16" = "MINERACAO",
        "17" = "URBANIZADA",
        "20" = "OUTROS USOS",
        "21" = "OUTRAS ÁREAS EDIFICADAS",
        "22" = "DESFLORESTAMENTO NO ANO",
        "23" = "CORPO DAGUA",
        "25" = "NAO OBSERVADO"

    ),
    version = "tc"
)

#
# Read classified data
#
class <- sits_cube(
    source = "BDC",
    collection = "SENTINEL-2-16D",
    bands = "class",
    data_dir = "./data/derived/",
    labels = c(
        "1" = "pastagem",
        "2" = "temporaria-1-ciclo",
        "3" = "vegetacao",
        "4" = "temporaria-mais-1-ciclo",
        "5" = "silvicultura",
        "6" = "agua",
        "7" = "perene"
    )
)

#
# Apply first mask
#
mask <- sits_reclassify(
    class,
    tc,
    rules = list(
        "no-perene" = cube == "perene" & mask %in% c(
            "nodata", "VEGETACAO NATURAL PRIMARIA",
            "VEGETACAO NATURAL SECUNDARIA", "SILVICULTURA",
            "PASTAGEM", "MINERACAO", "URBANIZADA",
            "OUTROS USOS", "OUTRAS ÁREAS EDIFICADAS",
            "DESFLORESTAMENTO NO ANO", "CORPO DAGUA",
            "NAO OBSERVADO")
    ),
    memsize = 10,
    multicores = 6,
    version = "masked-tc-v3",
    output_dir = "./data/derived/"
)

#
# Apply second mask
#
mask <- sits_reclassify(
    mask,
    tc,
    rules = list(
        "no-perene" = cube != "perene"
    ),
    memsize = 10,
    multicores = 6,
    version = "masked-bin",
    output_dir = "./data/derived/"
)
