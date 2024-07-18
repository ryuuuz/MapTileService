import json
import math
import os

import requests
from PIL import Image
from shapely.geometry import box, shape, mapping

from config import MAPBOX_TOKEN, TILE_DIRECTORY, ZOOM_LEVELS, LONGITUDE_RANGE, LATITUDE_RANGE, BUFFER_DISTANCE

layer_url = {
    'streets-v11': 'https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token={token}',
    'satellite-v9': 'https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token={token}',
    'google-satellite': 'https://khms2.google.com/kh/v=982?x={x}&y={y}&z={z}'
}


# 读取 GeoJSON 文件
def load_geojson(filepath):
    with open(filepath) as f:
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


# 获取 GeoJSON 数据的缓冲区（buffer）范围
def get_buffered_geojson(geojson, buffer_distance):
    buffered_features = []

    for feature in geojson['features']:
        geom = shape(feature['geometry'])
        buffered_geom = geom.buffer(buffer_distance)
        buffered_features.append({
            "type": "Feature",
            "geometry": mapping(buffered_geom)
        })

    buffered_geojson = {
        "type": "FeatureCollection",
        "features": buffered_features
    }
    return buffered_geojson


# 检查瓦片是否在缓冲区内
def is_tile_near_waterway(tile_poly, buffered_geojson):
    for feature in buffered_geojson['features']:
        geom = shape(feature['geometry'])
        if tile_poly.intersects(geom):
            return True
    return False


# 经纬度转换为瓦片编号
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


# 瓦片编号转换为经纬度
def num2deg(xtile, ytile, zoom):
    n = 2 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)

    # 返回四个角的经纬度构成的矩形
    tile_poly = box(lon_deg, lat_deg, lon_deg + 360.0 / n,
                    lat_deg + (180.0 / math.pi * math.atan(math.sinh(math.pi * (1 - 2 * (ytile + 1) / n)))))
    return tile_poly


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
    geojson = load_geojson('static/geojson/waterways/520000.geojson')

    min_lng, min_lat = LONGITUDE_RANGE[0], LATITUDE_RANGE[0]
    max_lng, max_lat = LONGITUDE_RANGE[1], LATITUDE_RANGE[1]
    filtered_geojson = filter_geojson_by_bbox(geojson, min_lng, min_lat, max_lng, max_lat)
    buffered_geojson = get_buffered_geojson(filtered_geojson, BUFFER_DISTANCE)

    for zoom in ZOOM_LEVELS:
        min_x, min_y = deg2num(max_lat, min_lng, zoom)
        max_x, max_y = deg2num(min_lat, max_lng, zoom)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tile_poly = num2deg(x, y, zoom)
                if is_tile_near_waterway(tile_poly, buffered_geojson):
                    if not tile_exists(zoom, x, y, layer):
                        tile = download_tile(zoom, x, y, layer)
                        if tile:
                            save_tile(tile, zoom, x, y, layer)
                    else:
                        print(f'Tile {zoom}/{x}/{y} from layer {layer} already exists. Skipping download.')


if __name__ == '__main__':
    download_tiles('google-satellite')
