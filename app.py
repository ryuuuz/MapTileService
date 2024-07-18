from flask import Flask, send_from_directory, abort, render_template_string, request, send_file, jsonify
import os
import requests
import socket
from urllib.parse import quote
from config import TILE_DIRECTORY, HTML_DIRECTORY, TILE_SIZE, ZOOM_LEVELS, LONGITUDE_RANGE, \
    LATITUDE_RANGE
import zipfile
import io

app = Flask(__name__)
app.config['TILE_DIRECTORY'] = TILE_DIRECTORY
app.config['HTML_DIRECTORY'] = HTML_DIRECTORY


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def download_tile(lon, lat, zoom):
    tile_dir = os.path.join(app.config['TILE_DIRECTORY'], f'{zoom}/{lon}_{lat}')
    tile_path = os.path.join(tile_dir, 'tile.png')

    if os.path.exists(tile_path):
        print(f"Tile {tile_path} already exists. Skipping download.")
        return

    url = f"https://restapi.amap.com/v3/staticmap?location={lon},{lat}&zoom={zoom}&size={TILE_SIZE[0]}*{TILE_SIZE[1]}&key={GAODE_API_KEY}"
    response = requests.get(url, timeout=3)

    if response.status_code == 200:
        os.makedirs(tile_dir, exist_ok=True)
        with open(tile_path, 'wb') as f:
            f.write(response.content)
        print(f"Tile {tile_path} downloaded successfully")
    else:
        print(f"Failed to download tile at {lon}, {lat}, zoom {zoom}")


def download_tiles():
    lon_min, lon_max = LONGITUDE_RANGE
    lat_min, lat_max = LATITUDE_RANGE

    lon_step = (lon_max - lon_min) / 5
    lat_step = (lat_max - lat_min) / 5

    for zoom in ZOOM_LEVELS:
        lon = lon_min
        while lon <= lon_max:
            lat = lat_min
            while lat <= lat_max:
                download_tile(lon, lat, zoom)
                lat += lat_step
            lon += lon_step


@app.route('/')
def serve_offlinemap():
    return send_file(os.path.join(app.config['HTML_DIRECTORY'], 'offlinemap.html'))

@app.route('/map')
def serve_map():
    return send_file(os.path.join(app.config['HTML_DIRECTORY'], 'map.html'))

@app.route('/mapbox')
def serve_mapbox():
    return send_file(os.path.join(app.config['HTML_DIRECTORY'], 'mapbox.html'))


@app.route('/tiles/')
def list_tiles():
    files = []
    for root, _, filenames in os.walk(app.config['TILE_DIRECTORY']):
        for filename in filenames:
            files.append(os.path.relpath(os.path.join(root, filename), app.config['TILE_DIRECTORY']))
    file_links = [f'<a href="/tiles_bak/{quote(file)}">{file}</a>' for file in files]
    return render_template_string('<html><body>{{ files|safe }}</body></html>', files='  '.join(file_links))


@app.route('/tiles/<path:filename>')
def serve_tile(filename):
    tile_path = os.path.join(app.config['TILE_DIRECTORY'], filename)
    if not os.path.exists(tile_path):
        abort(404, description="Tile not found")
    return send_from_directory(os.path.dirname(tile_path), os.path.basename(tile_path), mimetype='image/png')


@app.route('/download-tiles')
def download_tiles_as_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for root, _, files in os.walk(app.config['TILE_DIRECTORY']):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, app.config['TILE_DIRECTORY'])
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='tiles_bak.zip')


@app.errorhandler(404)
def handle_404(error):
    return "Tile not found", 404


if __name__ == '__main__':
    port = 8080
    if is_port_in_use(port):
        print(f"Port {port} is already in use.")
    else:
        # download_tiles()  # 下载瓦片
        app.run(port=port)
