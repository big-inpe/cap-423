# CAP-423 - Ciência de Dados Geoespaciais

## Detecção de Pivos Centrais

Este projeto tem como objetivo criar uma base de dados com informações extraídas das imagens de satélite disponíveis no INPE através de técnicas de IA para possibilitar a recuperação por conteúdo. Ele contem os codigos para identificar a localização dos pivos usando o banco de da Ana e Embrapa, e identificação automatica por metodo de Hough.

## DownloadTile

Codigo para ser usado no RStudio, importe de pacotes:
  install.packages("rstac")
  library(rstac)
 
Recebe uma bounding box para download de .tif de https://data.inpe.br/bdc/stac/v1

## Opção 1: (Jupyter Notebook) Hough.ipynb e PivosCentrais.ipynb
 Rodar os pip install no colab e fornecer um Tif ao google colab
 Recebe um Tiff e retorna um string indicado se existe pivo ou não, a quantia de pivos, e um shapefile com a localização dos pivos 

## Opção 2: Codigos Terminal PivosCentrais.py e Hough.py
 Rodar
   > pip install opencv-python-headless
-------
   > pip install numpy matplotlib 
-------
   > pip install geopandas rasterio shapely
-------
Executar o codigo passando o caminho do tif de entrada
-------
> python Hough.py <path_to_tif_file_NDVI_BAND>
--------
> python PivosCentrais.py <path_to_tif_file>
--------
Os codigos vão imprimir a quantia de pivos detectados.
O codigo dos pivosCentrais gera um .shp com a localização dos pivos detectados
