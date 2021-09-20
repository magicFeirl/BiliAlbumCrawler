"""
请求接口，获取相册数据
"""
import asyncio

from aiohttp import ClientSession


class BiliUserAlbumCrawler():
    def __init__(self, settings: dict = None):
        self.session = ClientSession()

        # 一些请求参数，如代理、超时时间等
        self.settings = settings or {}

        self.default_headers = {
            'user-agent':
            ('user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36')
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    def get_session(self):
        """获取创建的 session，为了 session 的复用"""
        return self.session

    async def get_one(self, uid: str, pn: int, ps: int = 30):
        """
        获取一页b站用户相册数据
        :param: uid 用户 uid
        :param: pn 相册的页数，第一页的下标为 0
        :param: ps 一页返回的数据个数，最大值为 50，大于这个值会报错

        :return: 请求的接口数据，格式参考 https://api.bilibili.com/x/dynamic/feed/draw/doc_list?uid=2
        """
        api = f'https://api.bilibili.com/x/dynamic/feed/draw/doc_list?uid={uid}&page_num={pn}&page_size={ps}'

        async with self.session.get(api, headers=self.default_headers, **self.settings) as resp:
            return await resp.json()

    async def get_many(self, uid: str, begin: int, end: int, ps: int = 30, coro: int = 5):
        """
        获取多页b站用户相册数据
        :param: begin 起始页
        :param: end 结束页  范围是 [begin, end)
        :param: coro 最大并发请求数

        :return: 一个 async 迭代器，使用 async for 遍历，数据项为 (当前页数, 接口数据)
        """
        semaphore = asyncio.Semaphore(coro)

        async def worker(pn):
            async with semaphore:
                return await self.get_one(uid, pn, ps)

        tasks = [asyncio.create_task(worker(pn)) for pn in range(begin, end)]

        for task in tasks:
            yield await task
