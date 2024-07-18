import math
import os

import requests
from PIL import Image

from config import MAPBOX_TOKEN, TILE_DIRECTORY, ZOOM_LEVELS, LONGITUDE_RANGE, LATITUDE_RANGE

layer_url = {
    'streets-v11': 'https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token={token}',
    'satellite-v9': 'https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token={token}',
    'google-satellite': 'https://khms2.google.com/kh/v=982?x={x}&y={y}&z={z}'
}

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def download_tile(zoom, x, y, layer):
    # url = f'https://api.mapbox.com/styles/v1/mapbox/{layer}/tiles/{zoom}/{x}/{y}?access_token={mapbox_access_token}'
    url = layer_url[layer].format(z=zoom, x=x, y=y, token=MAPBOX_TOKEN)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        return Image.open(response.raw)
    else:
        print(f'Failed to download tile {zoom}/{x}/{y} from layer {layer}')
        return None


def save_tile(image, zoom, x, y, layer):
    directory = os.path.join(TILE_DIRECTORY, f'{layer}/{zoom}')
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, f'{x}_{y}.png')
    image.save(file_path, 'PNG')
    print(f'Saved {file_path}')


def tile_exists(zoom, x, y, layer):
    file_path = os.path.join(TILE_DIRECTORY, f'{layer}/{zoom}', f'{x}_{y}.png')
    return os.path.exists(file_path)


def download_tiles(layer):
    min_lng, min_lat = LONGITUDE_RANGE[0], LATITUDE_RANGE[0]
    max_lng, max_lat = LONGITUDE_RANGE[1], LATITUDE_RANGE[1]
    for zoom in ZOOM_LEVELS:
        min_x, min_y = deg2num(max_lat, min_lng, zoom)
        max_x, max_y = deg2num(min_lat, max_lng, zoom)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if not tile_exists(zoom, x, y, layer):
                    tile = download_tile(zoom, x, y, layer)
                    if tile:
                        save_tile(tile, zoom, x, y, layer)
                else:
                    print(f'Tile {zoom}/{x}/{y} from layer {layer} already exists. Skipping download.')


if __name__ == '__main__':
    download_tiles('google-satellite')
