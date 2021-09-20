"""
保存二进制文件
"""
import os
import aiofiles

from typing import BinaryIO, Union, List


class AsyncFile():
    def __init__(self, dirpath, filename) -> None:
        self.dirpath = dirpath
        self.filename = filename
        self.fullpath = os.path.join(dirpath, filename)
        self.mkdirs()

    def isfile(self):
        return os.path.isfile(self.fullpath)

    def mkdirs(self):
        if not os.path.exists(self.dirpath):
            os.makedirs(self.dirpath)

    async def save_file(self, binfile: BinaryIO, cover=False) -> bool:
        """保存文件到本地
        :param: dirpath 保存文件的根目录，如果不存在会自动创建
        :param: filename 二进制数据
        :param: cover 指定是否覆盖指定的目录下存在的 filename 同名文件

        :return: True or False 表示是否成功保存文件"""

        if not binfile:
            return False

        if not cover and self.isfile():
            # print(fullpath, 'is already exists')
            return True

        async with aiofiles.open(self.fullpath, 'wb') as f:
            await f.write(binfile)

        return True

    async def save_file_url(self, session, url: str, cover=False, **kwargs) -> bool:
        """
        下载 URL 指向的文件并保存至本地
        :param: session aiohttp.ClientSession 的实例
        :param: kwargs 请求参数

        :return: (是否成功下载, HTTP 状态码）
        """
        bin, status = None, 200

        if not cover and os.path.isfile(self.fullpath):
            return True

        async with session.get(url, **kwargs) as resp:
            if resp.status >= 200 and resp.status < 300:
                bin = await resp.read()
            status = resp.status

        return (await self.save_file(binfile=bin, cover=cover), status)

    async def save_file_text(self, text: Union[List, str], mode: str = 'a', **kwargs) -> bool:
        if isinstance(text, str):
            text = [text]

        count = 1
        FLUSH = 10

        async with aiofiles.open(self.fullpath, mode=mode, newline=os.linesep, **kwargs) as f:
            for line in text:
                count += 1
                await f.write(line)
                await f.write(os.linesep)

            if count % FLUSH == 0:
                await f.flush()
