import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS, Transformer
from rasterio.features import rasterize
import rasterio
from tqdm import tqdm
import pystac_client

class BBox:
    def __init__(self, minx, miny, maxx, maxy):
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

    def to_dict(self):
        return {"minx": self.minx, "miny": self.miny, "maxx": self.maxx, "maxy": self.maxy}


class FireSpots:
    def __init__(self, bbox, year, date_range):
        self.bbox = bbox
        self.year = year
        self.date_range = date_range

    def fetch_fire_spots(self):
        lon_min, lat_min, lon_max, lat_max = self.bbox.minx, self.bbox.miny, self.bbox.maxx, self.bbox.maxy
        first_date, second_date = self.date_range
        path = (f"https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0"
                f"&TYPENAMES=bdqueimadas3:focos&TYPENAME=bdqueimadas3:focos&SRSNAME=urn:ogc:def:crs:EPSG::4326"
                f"&CQL_FILTER=data_hora_gmt%20between%20{first_date}%20and%20{second_date}%20AND%20"
                f"longitude%20%3E%20{lon_min}%20AND%20longitude%20%3C%20{lon_max}%20AND%20latitude%20%3E%20{lat_min}%20AND%20latitude%20%3C%20{lat_max}")
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

        df = pd.DataFrame({'latitude': lat, 'longitude': lon, 'date': date})
        df['geometry'] = gpd.points_from_xy(df.longitude, df.latitude)
        return gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')


class SatelliteData:
    def __init__(self, year, tile, cloud_percentage=50):
        self.year = year
        self.tile = tile
        self.cloud_percentage = cloud_percentage

    def fetch_satellite_data(self):
        catalog_url = 'https://data.inpe.br/bdc/stac/v1/'
        client = pystac_client.Client.open(catalog_url)
        start_date, end_date = f"{self.year}-01-01", f"{self.year}-12-31"
        search = client.search(
            collections=['S2_L2A-1'],
            datetime=f"{start_date}/{end_date}",
            query={"bdc:tiles": {"in": [self.tile]}, "eo:cloud_cover": {"lt": self.cloud_percentage}},
            sortby=[{'field': 'properties.datetime', 'direction': 'asc'}],
            limit=100
        )
        items = list(search.get_all_items())
        return self._parse_items(items)

    def _parse_items(self, items):
        data_dict = {
            'dates_before': [], 'dates_after': [],
            'item_before': [], 'item_after': [],
            'href_b8a_before': [], 'href_b8a_after': [],
            'href_b11_before': [], 'href_b11_after': [],
            'href_b12_before': [], 'href_b12_after': [],
            'href_scl_before': [], 'href_scl_after': []
        }
        for i in range(1, len(items)):
            current_item, prev_item = items[i], items[i - 1]
            data_dict['dates_after'].append(current_item.datetime.date())
            data_dict['dates_before'].append(prev_item.datetime.date())
            data_dict['item_after'].append(current_item.id)
            data_dict['item_before'].append(prev_item.id)
            for band in ['B8A', 'B11', 'B12', 'SCL']:
                data_dict[f'href_{band.lower()}_after'].append(current_item.assets[band].href)
                data_dict[f'href_{band.lower()}_before'].append(prev_item.assets[band].href)
        return pd.DataFrame(data_dict)


class BurnedAreaDetection:
    def __init__(self, year, tile, cloud_percentage=50):
        self.satellite_data = SatelliteData(year, tile, cloud_percentage)

    def detect_burned_areas(self):
        df = self.satellite_data.fetch_satellite_data()
        results = []

        for i in tqdm(range(len(df)), desc="Processing Burned Areas"):
            result = self._process_pair(df.iloc[i])
            results.append(result)

        result_df = pd.DataFrame(results)
        result_df.to_json(f'burned_area_detection_{self.satellite_data.tile}_{self.satellite_data.year}.json', orient='records')
        return result_df

    def _process_pair(self, row):
        # Implement processing of each pair (before and after) to detect burned areas.
        pass  # Replace with specific logic for detection


if __name__ == '__main__':
    detector = BurnedAreaDetection(year=2022, tile='22LHH')
    detector.detect_burned_areas()
