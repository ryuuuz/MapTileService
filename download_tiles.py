import json
import math
import os

import requests
from PIL import Image
from shapely.geometry import box, shape

from config import MAPBOX_TOKEN, TIANDI_TOKEN, TILE_DIRECTORY, ZOOM_LEVELS, LONGITUDE_RANGE, LATITUDE_RANGE

layer_url = {
    'streets-v11': 'https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token={mapbox_token}',
    'satellite-v9': 'https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token={mapbox_token}',
    'google-satellite': 'https://khms2.google.com/kh/v=982?x={x}&y={y}&z={z}',
    'tianditu_vec': 'https://t4.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={tiandi_token}',
    'tianditu_cva': 'https://t4.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={tiandi_token}',
}


# 读取 GeoJSON 文件
def load_geojson(filepath):
    with open(filepath, encoding='utf-8') as f:
        geojson = json.load(f)
    return geojson


# 过滤 GeoJSON 数据，只保留在指定经纬度范围内的 waterway
def filter_geojson_by_bbox(geojson, min_lng, min_lat, max_lng, max_lat):
    bbox = box(min_lng, min_lat, max_lng, max_lat)
    filtered_features = []

    for feature in geojson['features']:
        geom = shape(feature['geometry'])
        if geom.intersects(bbox):
            filtered_features.append(feature)

    filtered_geojson = {
        "type": "FeatureCollection",
        "features": filtered_features
    }
    return filtered_geojson


# 经纬度转换为瓦片编号
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x_tile = int((lon_deg + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return x_tile, y_tile


# 瓦片编号转换为经纬度
def num2deg(x_tile, y_tile, zoom):
    n = 2 ** zoom
    lon_deg = x_tile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile / n)))
    lat_deg = math.degrees(lat_rad)

    # 返回四个角的经纬度构成的矩形
    tile_poly = box(lon_deg, lat_deg, lon_deg + 360.0 / n,
                    lat_deg + (180.0 / math.pi * math.atan(math.sinh(math.pi * (1 - 2 * (y_tile + 1) / n)))))
    return tile_poly


def is_tile_contain_waterway(tile_poly, geojson):
    for feature in geojson['features']:
        geom = shape(feature['geometry'])
        # 检查水域几何是否至少有一个点在瓦片内
        if tile_poly.intersects(geom):
            return True
    return False


def expand_tiles(x, y, expansion_range):
    expanded_tiles = []
    for dx in range(-expansion_range, expansion_range + 1):
        for dy in range(-expansion_range, expansion_range + 1):
            expanded_tiles.append((x + dx, y + dy))
    return expanded_tiles


def tile_exists(zoom, x, y, layer):
    file_path = os.path.join(TILE_DIRECTORY, f'{layer}/{zoom}', f'{x}_{y}.png')
    return os.path.exists(file_path)


def download_tile(zoom, x, y, layer):
    url = layer_url[layer].format(z=zoom, x=x, y=y, mapbox_token=MAPBOX_TOKEN, tiandi_token=TIANDI_TOKEN)
    response = requests.get(url, stream=True, timeout=1)
    if response.status_code == 200:
        return Image.open(response.raw)
    else:
        print(f'Failed to download tile {zoom}/{x}/{y} from layer {layer}')
        print(response.text)
        return None


def save_tile(image, zoom, x, y, layer):
    directory = os.path.join(TILE_DIRECTORY, f'{layer}/{zoom}')
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, f'{x}_{y}.png')
    image.save(file_path, 'PNG')
    print(f'Saved {file_path}')


def download_tiles(layer):
    geojson = load_geojson('static/geojson/waterways/520000.geojson')

    min_lng, min_lat = LONGITUDE_RANGE[0], LATITUDE_RANGE[0]
    max_lng, max_lat = LONGITUDE_RANGE[1], LATITUDE_RANGE[1]
    filtered_geojson = filter_geojson_by_bbox(geojson, min_lng, min_lat, max_lng, max_lat)

    for zoom in ZOOM_LEVELS:
        min_x, min_y = deg2num(max_lat, min_lng, zoom)
        max_x, max_y = deg2num(min_lat, max_lng, zoom)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tile_poly = num2deg(x, y, zoom)
                if is_tile_contain_waterway(tile_poly, filtered_geojson):
                    expanded_tiles = expand_tiles(x, y, 1)  # 可以调整扩张范围
                    for ex, ey in expanded_tiles:
                        if not tile_exists(zoom, ex, ey, layer):
                            tile = download_tile(zoom, ex, ey, layer)
                            if tile:
                                save_tile(tile, zoom, ex, ey, layer)
                        else:
                            print(f'Tile {zoom}/{ex}/{ey} from layer {layer} already exists. Skipping download.')


if __name__ == '__main__':
    download_tiles('google-satellite')
    download_tiles('tianditu_vec')
    download_tiles('tianditu_cva')

