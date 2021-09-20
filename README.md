# B站用户相簿图片爬虫

## 简介

批量爬取指定的B站用户相簿图片并保存到本地，支持多并发请求和多并发下载，采用CLI方式交互。

**运行**

1. `pip install -r requirements.txt` 安装依赖
2. 升级到 Python3.7+

3. `python app.py --help` 运行程序

**截图**

> 显示帮助

![img1.JPG](https://i.loli.net/2021/09/20/NRLPOCKcx9m6G1h.jpg)

> 运行

![img2.JPG](https://i.loli.net/2021/09/20/6wX8lOTkhErDHQt.jpg)

## 用到的技术

1. asyncio 的各种 API
2. FastAPI 作者写的 [Typer CLI]([CLI Option Name - Typer (tiangolo.com)](https://typer.tiangolo.com/tutorial/options/name/)) 工具（吐槽一下貌似这玩意不支持 aio）
3. [tqdm](https://github.com/tqdm/tqdm#description-and-additional-stats) 进度条轮子
4. aiofiles、aiohttp