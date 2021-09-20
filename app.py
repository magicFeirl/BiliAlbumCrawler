import asyncio
import logging
import os
import typer

# Progress
from tqdm.asyncio import tqdm

from app import BiliUserAlbumCrawler
from app import AsyncFile

logging.basicConfig(level=logging.INFO)


async def run(crawler: BiliUserAlbumCrawler, uid: str, begin: int, end: int, ps: int = 30, coro: int = 5):
    async for idx, data in crawler.get_many(uid, begin=begin, end=end, ps=ps, coro=coro):
        code, message = data['code'], data['message']

        if code != 0:
            logging.error(f'\n接口返回值出错: {code}, Message: {message}\n')
            break

        if not data['data']:
            # logging.info(f'用户 {uid} 第 {idx} 页无数据，退出')
            break

        items = data['data']['items']

        for item in items:
            for pic in item['pictures']:
                yield pic['img_src']


async def download_task(semaphore, session, url: str, dirpath: str, filename: str):
    file = AsyncFile(dirpath, filename)
    async with semaphore:
        await file.save_file_url(session, url, cover=False, timeout=10)


def main(
    uid: str, dirpath: str = '.', begin: int = 0, end: int = 1,
    ps: int = 30, req_coro_num: int = 5, download_coro_num: int = 5
):
    async def worker(dirpath):
        tasks = []
        semaphore = asyncio.Semaphore(download_coro_num)

        if dirpath == '.':
            dirpath = os.path.join('.', uid)

        async with BiliUserAlbumCrawler() as crawler:
            session = crawler.get_session()
            download_count = 0

            logging.info(f'开始获取 {uid} 的相簿数据...')

            with tqdm(run(crawler, uid, begin=begin, end=end, ps=ps, coro=req_coro_num)) as pbar:
                async for url in pbar:
                    filename = url[url.rfind('/')+1:]
                    task = asyncio.create_task(download_task(
                        semaphore, session, url, dirpath, filename))
                    tasks.append(task)

                    download_count += 1

            await asyncio.wait(tasks)
            logging.info(f'{download_count} 条数据已保存至 > {dirpath}')

    asyncio.run(worker(dirpath))


if __name__ == '__main__':
    typer.run(main)
