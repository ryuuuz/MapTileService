import io
import os
import socket
import zipfile
from urllib.parse import quote

import folium
from flask import Flask, send_from_directory, abort, render_template_string, send_file, render_template

from config import TILE_DIRECTORY, HTML_DIRECTORY, CENTER_LOCATION

app = Flask(__name__)
app.config['TILE_DIRECTORY'] = TILE_DIRECTORY
app.config['HTML_DIRECTORY'] = HTML_DIRECTORY


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


@app.route('/')
def serve_offlinemap():
    return send_file(os.path.join(app.config['HTML_DIRECTORY'], 'offlinemap.html'))


@app.route('/map')
def serve_map():
    return send_file(os.path.join(app.config['HTML_DIRECTORY'], 'map.html'))


@app.route('/mapbox')
def serve_mapbox():
    return send_file(os.path.join(app.config['HTML_DIRECTORY'], 'mapbox.html'))


@app.route('/geojson')
def serve_geojson():
    # Create a map centered at the specified location
    map = folium.Map(location=[CENTER_LOCATION[1], CENTER_LOCATION[0]], zoom_start=10)
    # Load the GeoJSON file
    geojson_path = 'static/geojson/waterways/520000.geojson'
    folium.GeoJson(geojson_path).add_to(map)
    # Save the map to an HTML file
    map.save('templates/geojson.html')

    return render_template('geojson.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


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
