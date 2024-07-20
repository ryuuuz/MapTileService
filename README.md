# MapTileService

MapTileService 是一个 Python 项目，用于从多个支持的 WMTS 服务（目前支持 Mapbox、高德地图和天地图）下载地图切片（PNG 格式）到 tiles 文件夹，并通过 Flask 提供本地 WMTS 服务。项目通过提供 GeoJSON 文件和配置参数，筛选出指定经纬度范围内的水路（waterway）数据，并获取这些区域附近的瓦片。这样可以确保 GeoJSON 文件中的所有点都被缓存下来，提高了缓存的效率和相关性，尤其适用于需要重点关注的区域（如航道）。
这是优化后的项目描述，进一步明确了从 GeoJSON 数据中选择经纬度范围内的数据，并获取附近瓦片的过程：

## 功能

- 从多个 WMTS 服务（Mapbox、高德地图、天地图）下载地图切片。
- 基于 GeoJSON 数据和缓冲区范围筛选和下载切片，优化缓存效率。
- 通过 Flask 提供本地 WMTS 服务。
- 提供静态文件和地图服务。

## 安装

1. 克隆仓库到本地：

   ```bash
   git clone <repository-url>
   cd MapTileService
   ```

2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 配置

1. 复制配置文件示例，并重命名为 `config.py`：

   ```bash
   cp config_example.py config.py
   ```

2. 编辑 `config.py` 文件，配置以下参数：

   - `TILE_DIRECTORY`: 切片存储目录
   - `HTML_DIRECTORY`: HTML 文件存储目录
   - `CENTER_LOCATION`: 地图中心点的经纬度
   - 其他 API 相关配置

## 使用

1. **下载切片**

   运行 `download_tiles.py` 脚本，根据配置文件中的参数和 GeoJSON 数据下载指定范围内的 PNG 切片：

   ```bash
   python download_tiles.py
   ```

2. **启动本地 WMTS 服务**

   运行 `app.py` 脚本，启动 Flask 本地服务器提供 WMTS 服务：

   ```bash
   python app.py
   ```

## 路由

- `/`：提供首页（`index.html`）。
- `/map`：提供地图页面（`map.html`）。
- `/geojson`：加载并显示指定的 GeoJSON 文件。
- `/static/<path:filename>`：提供静态文件服务。
- `/tiles/`：列出所有下载的切片文件。
- `/tiles/<path:filename>`：提供单个切片文件下载。
- `/download-tiles`：打包所有切片文件并提供下载。
- 404 错误处理：如果请求的切片文件不存在，返回 404 错误。

## 示例

以下是一个示例项目结构：

```
MapTileService/
├── config_example.py
├── config.py
├── download_tiles.py
├── app.py
├── templates/
│   ├── index.html
│   ├── map.html
│   ├── geojson.html
│   └── tiles.html
├── static/
│   └── geojson/
│       └── waterways/
│           └── 520000.geojson
└── tiles/
    └── ...
```

## 贡献

欢迎贡献代码！请提交 Pull Request 或报告 Issue。

## 许可证

该项目基于 MIT 许可证开源。
