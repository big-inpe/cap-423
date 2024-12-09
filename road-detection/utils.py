import numpy as np
from osgeo import gdal

def gray_to_arr(path):
    '''Open graysclae image and return as np array'''
    raster = gdal.Open(path)
    arr = raster.GetRasterBand(1).ReadAsArray()
    del raster
    return arr


def s2_to_arr(path, bands=['red', 'green', 'blue']):
    '''
    Open Sentinel-2 imagery with specified bands.
    Bands: red, green, blue, nir, swir1, swir2, edge1, edge2, edge3 and edge4.
    Output array has shape (height, width, n_channels)
    '''
    bands_dict = {'blue': 2, 'green': 3, 'red': 4, 'edge1': 5, 'edge2': 6, 'edge3': 7,\
             'nir': 8, 'edge4': 9, 'swir1': 12, 'swir2': 13}

    raster = gdal.Open(path)

    arr = np.dstack(
        [raster.GetRasterBand(bands_dict[band]).ReadAsArray() for band in bands]
    )

    del raster

    return arr
