# Bibliotecas padrão
import xml.etree.ElementTree as ET  # Para trabalhar com XML
from urllib.request import urlretrieve
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint
from pyproj import Proj, Transformer, transform
from datetime import datetime, timedelta
import rasterio
import pystac_client
import folium
from rasterio.features import shapes
from shapely.geometry import shape
import numpy as np
import rasterio
from matplotlib import pyplot as plt
from pyproj import Transformer
from pyproj.crs import CRS
from rasterio.windows import bounds, from_bounds, Window
from pyproj import CRS
from rasterio.features import rasterize
import geopandas as gpd
import requests
import pandas as pd
import numpy as np
import shapely
import lxml
import xml.etree.ElementTree as ET
import tqdm
from tqdm import tqdm
from shapely import Point


def cluster_fire_spots(bbox_4326, year='2024', first_month='09', first_day='10', second_month='09', second_day='15'):
    try:
        lon_min = bbox_4326['minx']
        lat_min = bbox_4326['miny']
        lon_max = bbox_4326['maxx']
        lat_max = bbox_4326['maxy']
        gdf = print_points(lat_min, lon_min, lat_max, lon_max, year, first_month, first_day, second_month, second_day)
        return gdf

    except Exception as e:
        print(f"Error: {e}")
        return False

def print_points(lat_min, lon_min, lat_max, lon_max, year, first_month, first_day, second_month, second_day):
    path = f"https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&TYPENAMES=bdqueimadas3:focos&TYPENAME=bdqueimadas3:focos&SRSNAME=urn:ogc:def:crs:EPSG::4326&CQL_FILTER=data_hora_gmt%20between%20{year}-{first_month}-{first_day}T00%3A00%3A00%20and%20{year}-{second_month}-{second_day}T23%3A59%3A59%20AND%20longitude%20%3E%20{lon_min}%20AND%20longitude%20%3C%20{lon_max}%20AND%20latitude%20%3E%20{lat_min}%20AND%20latitude%20%3C%20{lat_max}"
    response = requests.get(path)
    lat, lon, date = [], [], []
    xml_data = response.content
    root = ET.fromstring(xml_data)
    namespaces = {
        'wfs': 'http://www.opengis.net/wfs/2.0',
        'gml': 'http://www.opengis.net/gml/3.2',
        'bdqueimadas3': 'https://www.inpe.br/queimadas/bdqueimadas3'
    }
    for foco in root.findall('.//wfs:member/bdqueimadas3:focos', namespaces):
        latitude = foco.find('bdqueimadas3:latitude', namespaces).text
        longitude = foco.find('bdqueimadas3:longitude', namespaces).text
        data_hora = foco.find('bdqueimadas3:data_hora_gmt', namespaces).text
        lat.append(latitude)
        lon.append(longitude)
        date.append(data_hora)

    focos_lat = np.array(lat)
    focos_lon = np.array(lon)
    focos_date = np.array(date)
    
    result = list(zip(map(lambda x: float(x), focos_lon), map(lambda x: float(x), focos_lat)))
    d = {'coordinates': result, 'date': focos_date}
    df = pd.DataFrame(data=d)
    df['geometry'] = df['coordinates'].apply(lambda x: Point(x[0], x[1]))
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.crs = {"init": "epsg:4326"}
    return gdf

def calculate_dscl(scl_path_before,scl_path_after):
    scl_data_before, transform, crs, scl_bounds_before,bbox_4326 = read_tiff_image(scl_path_before)
    scl_data_after, _, _, scl_bounds_after,bbox_4326 = read_tiff_image(scl_path_after)

    scl_mask_before = np.isin(scl_data_before, [4, 5])  
    scl_mask_after = np.isin(scl_data_after, [4, 5])

    scl_before = np.where (scl_mask_before, 1, np.nan)
    scl_after = np.where (scl_mask_after, 1, np.nan)
    dscl = scl_before*scl_after

    return dscl, transform, crs,bbox_4326

def generate_data_frame(year,tile='22LHH',cloud_porcentage=50):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-30"
    catalog_url = 'https://data.inpe.br/bdc/stac/v1/'
    client = pystac_client.Client.open(catalog_url) 
    search = client.search(
        collections=['S2_L2A-1'],  # Colection name
        datetime=f"{start_date}/{end_date}",  # Filtro por data  
        query={"bdc:tiles":{'in':[f'{tile}']}, 'eo:cloud_cover':{"lt":cloud_porcentage}},
        sortby=[{
            'field': 'properties.datetime',
            'direction': 'asc'
        }],
        limit=100 
    )
    itens = list(search.get_all_items())
    dates_after = []
    dates_before = []
    item_after = []
    item_before = []
    href_b8a_after = []
    href_b8a_before = []
    href_b11_after = []
    href_b11_before = []
    href_b12_after = []
    href_b12_before = []
    href_scl_after = []
    href_scl_before = []
    k=-1
    for i in range(1, len(itens)):
        current_item = itens[i]
        prev_item = itens[i - 1]
        if current_item.datetime.date() != prev_item.datetime.date():
            reference_item = prev_item
            # print(itens[i].datetime.date(),itens[i-1].datetime.date())
            if k==-1:
                if prev_item.datetime.date() != itens[i-2].datetime.date():
                    k=-1
                else:
                    i-=1
                    k+=1
            else:
                prev_item=itens[i-2]
                k=-1
        if current_item.datetime.date() == prev_item.datetime.date():
            # Comparação com o item dois passos atrás
            reference_item = itens[i - 2]
            if k==-1:
                if reference_item.datetime.date() != itens[i-3].datetime.date():
                    k=-1
                else:
                    i-=1
                    k+=1
            else:
                prev_item=itens[i-3].datetime.date()
                k=-1
            # print(itens[i].datetime.date(),itens[i-2].datetime.date())

        # Adicionando dados das datas
        dates_after.append(current_item.datetime.date())
        dates_before.append(reference_item.datetime.date())

        # Adicionando IDs
        item_after.append(current_item.id)
        item_before.append(reference_item.id)

        # Adicionando links
        href_b8a_after.append(current_item.assets['B8A'].href)
        href_b8a_before.append(reference_item.assets['B8A'].href)

        href_b11_after.append(current_item.assets['B11'].href)
        href_b11_before.append(reference_item.assets['B11'].href)

        href_b12_after.append(current_item.assets['B12'].href)
        href_b12_before.append(reference_item.assets['B12'].href)

        href_scl_after.append(current_item.assets['SCL'].href)
        href_scl_before.append(reference_item.assets['SCL'].href)

    data_dict = {
        'dates_before': dates_before,
        'dates_after': dates_after,
        'item_before': item_before,
        'item_after': item_after,
        'href_b8a_before': href_b8a_before,
        'href_b8a_after': href_b8a_after,
        'href_b11_before': href_b11_before,
        'href_b11_after': href_b11_after,
        'href_b12_before': href_b12_before,
        'href_b12_after': href_b12_after,
        'href_scl_before': href_scl_before,
        'href_scl_after': href_scl_after
    }

    df = pd.DataFrame(data_dict)

    return df


def read_tiff_image(file_path):
    with rasterio.open(file_path) as src:
        image_data = src.read(1) 
        transform = src.transform  
        crs = src.crs  
        bounds = src.bounds 
        epsg_code = crs.to_epsg()
        crs_original = CRS.from_epsg(epsg_code)  
        crs_destino = CRS.from_epsg(4326)

        # Transformando os limites para o EPSG:4326
        bounds_4326 = rasterio.warp.transform_bounds(crs_original, crs_destino, 
                                        bounds.left, bounds.bottom, 
                                        bounds.right, bounds.top)
        
        # Resultado no formato de BBOX
        bbox_4326 = {
            "minx": bounds_4326[0],  # Longitude mínima
            "miny": bounds_4326[1],  # Latitude mínima
            "maxx": bounds_4326[2],  # Longitude máxima
            "maxy": bounds_4326[3],  # Latitude máxima
        }   
    return image_data, transform, crs, bounds,bbox_4326

def genereta_nbr_and_nbr_swir(ddscl_mask, NIR2_path,SWIR2_path,SWIR1_path):
    NIR2_data, transform, crs, NIR2_bounds,bbox_4326 = read_tiff_image(NIR2_path)
    SWIR2_data, _, _, SWIR2_bounds,bbox_4326 = read_tiff_image(SWIR2_path)
    SWIR1_data, _, _, SWIR1_bounds,bbox_4326 = read_tiff_image(SWIR1_path)
    ddscl_mask=np.isin(ddscl_mask, [1])
    NIR2_data = np.where (ddscl_mask, np.array(NIR2_data, dtype=np.float32), np.nan)
    SWIR1_data = np.where (ddscl_mask, np.array(SWIR1_data, dtype=np.float32), np.nan)
    SWIR2_data = np.where (ddscl_mask, np.array(SWIR2_data, dtype=np.float32), np.nan)

    nbr = np.where(ddscl_mask, (NIR2_data - SWIR2_data) / (NIR2_data + SWIR2_data + 1e-20), np.nan) # this is as well a normalization
    nbr_swir = np.where(ddscl_mask, (SWIR1_data - SWIR2_data - 0.02) / (SWIR1_data + SWIR2_data + 1e-20 + 0.1), np.nan)
    return nbr, nbr_swir,bbox_4326

def dnbr_and_dnbr_swir(dscl,ref_b8a_before,href_b11_before,href_b12_before,ref_b8a_after,href_b11_after,href_b12_after):

    nbr_before, nbr_swir_before,bbox_4326 = genereta_nbr_and_nbr_swir(dscl,ref_b8a_before,href_b11_before,href_b12_before)
    nbr_after, nbr_swir_after,bbox_4326 = genereta_nbr_and_nbr_swir(dscl,ref_b8a_after,href_b11_after,href_b12_after)

    dnbr_swir = (nbr_swir_before -nbr_swir_after)/np.abs(nbr_swir_before+ 1e-20)
    dnbr = (nbr_before -nbr_after)/np.abs(nbr_before+1e-20)
    
    dnbr_swir_mask = np.zeros_like(dnbr_swir)
    dnbr_swir_mask[dnbr_swir < 1] =1 
    dnbr_swir_mask[dnbr_swir > 0.3] = 1  # Alta severidade
    dnbr_swir_mask[dnbr_swir <= 0.3] = np.nan  # Sem mudança
    dnbr_mask = np.zeros_like(dnbr) 
    dnbr_mask[dnbr > 0.2] = 1  # Alta severidade
    dnbr_mask[dnbr <= 0.2] = np.nan  # Sem mudança

    return dnbr_mask, dnbr_swir_mask,bbox_4326


def aearly_ba_detection(year='2022', tile='22LHH', cloud_porcentage=50):
    df = generate_data_frame(year, tile, cloud_porcentage)

    ba_files = []
    day_before_files = []
    day_after_files = []
    item_before_files = []
    item_after_files = []

    # for i in tqdm(range(1), desc="Processando assets", unit="asset"):
    for i in tqdm(range(len(df)-1), desc="Processando assets", unit="asset"):    
        # asset_exemple = 76
        asset_exemple = i+1

        scl_before = df.iloc[asset_exemple, 10]
        scl_after = df.iloc[asset_exemple, 11]
        href_b12_before = df.iloc[asset_exemple, 8]
        href_b12_after = df.iloc[asset_exemple, 9]
        href_b11_before = df.iloc[asset_exemple, 6]
        href_b11_after = df.iloc[asset_exemple, 7]
        href_b8a_before = df.iloc[asset_exemple, 4]
        href_b8a_after = df.iloc[asset_exemple, 5]
        item_before = df.iloc[asset_exemple, 2]
        item_after = df.iloc[asset_exemple, 3]
        dates_before = df.iloc[asset_exemple, 0]
        dates_after = df.iloc[asset_exemple, 1]

        dscl, transform, crs_original, bbox_4326 = calculate_dscl(scl_before, scl_after)
        dnbr_mask, dnbr_swir_mask, bbox_4326 = dnbr_and_dnbr_swir(
            dscl, 
            href_b8a_before, href_b11_before, href_b12_before, 
            href_b8a_after, href_b11_after, href_b12_after
        )

        year = str(dates_before.year)
        first_month = f"{dates_before.month:02d}"  
        first_day = f"{dates_before.day:02d}"

        year = str(dates_after.year) 
        second_month = f"{dates_after.month:02d}" 
        second_day = f"{dates_after.day:02d}" 
        caminho_arquivo = bbox_4326

        # Gera buffers e máscaras rasterizadas para focos de incêndio
        focos = cluster_fire_spots(bbox_4326, year, first_month, first_day, second_month, second_day)
        focos = focos.to_crs(epsg=f'{crs_original.to_epsg()}')
        focos_buffer = focos.buffer(300)

        gdf_focos_buffer = gpd.GeoDataFrame(geometry=focos_buffer, crs=focos.crs)
        focos_buffer_mask = gdf_focos_buffer.dissolve()
        shapes = ((geom, 1,) for geom in focos_buffer_mask.geometry)
        focos_buffer_mask_rasterized = rasterize(shapes, out_shape=dnbr_swir_mask.shape, transform=transform)

        # Calcula imagem modificada
        image_modified = dnbr_mask * dnbr_swir_mask * focos_buffer_mask_rasterized

        # Aplica a condição para gerar a máscara final
        image_conditioned = np.where(image_modified == 1, 1, np.nan)

        # Soma os valores diferentes de NaN
        sum_values = np.nansum(image_conditioned)
        pixels_sum = int(sum_values)
        file_in_the_df = asset_exemple

        # Verifica a soma de pixels e armazena os dados
        if pixels_sum > 50:
            data_antes = df.iloc[file_in_the_df, 0].strftime('%Y-%m-%d') if isinstance(df.iloc[file_in_the_df, 0], pd.Timestamp) else str(df.iloc[file_in_the_df, 0])
            data_depois = df.iloc[file_in_the_df, 1].strftime('%Y-%m-%d') if isinstance(df.iloc[file_in_the_df, 1], pd.Timestamp) else str(df.iloc[file_in_the_df, 1])
            item_before = df.iloc[file_in_the_df, 2]
            item_after = df.iloc[file_in_the_df, 3]
            ba_detect = 1

            
        else:
            data_antes = df.iloc[file_in_the_df, 0].strftime('%Y-%m-%d') if isinstance(df.iloc[file_in_the_df, 0], pd.Timestamp) else str(df.iloc[file_in_the_df, 0])
            data_depois = df.iloc[file_in_the_df, 1].strftime('%Y-%m-%d') if isinstance(df.iloc[file_in_the_df, 1], pd.Timestamp) else str(df.iloc[file_in_the_df, 1])
            item_before = df.iloc[file_in_the_df, 2]
            item_after = df.iloc[file_in_the_df, 3]
            ba_detect = 0
        day_before_files.append(data_antes)
        day_after_files.append(data_depois)
        item_before_files.append(item_before)
        item_after_files.append(item_after)
        ba_files.append(ba_detect)
    day_before_files= np.array(day_before_files)
    day_after_files = np.array(day_after_files)
    item_before_files = np.array(item_before_files)
    item_after_files = np.array(item_after_files)
    ba_files = np.array(ba_files)
        # Cria um DataFrame final com os resultados
    resultado_df = pd.DataFrame({
        "day_before": day_before_files,
        "day_after": day_after_files,
        "item_before": item_before_files,
        "item_after": item_after_files,
        "ba_detect": ba_files
    })
    resultado_df.to_json(f'early_burned_area_at_tile_{tile}_year_{year}.json', orient='records', lines=False, force_ascii=False, indent=4)
    print(f"file 'early_burned_area_at_tile_{tile}_year_{year}.json' saved!")
    return resultado_df


if __name__=='__main__':
    aearly_ba_detection()
    
