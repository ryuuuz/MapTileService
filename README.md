# MapTileService

MapTileService 是一个Python项目，用于调用高德地图API下载PNG切片，并通过TileStache提供WMTS服务。

## 安装

```bash
pip install -r requirements.txt
```

## 使用

1.	配置 config.py 文件中的API key和其他参数。
2.	运行 download_tiles.py 下载指定经纬度范围内的PNG切片。
3.	运行 serve_tiles.py 启动TileStache服务器。