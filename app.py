import asyncio
import logging
import os
import time

import typer
# Progress
from tqdm.asyncio import tqdm

from app import BiliUserAlbumCrawler
from app import AsyncFile

logging.basicConfig(level=logging.INFO)


async def run(crawler: BiliUserAlbumCrawler, uid: str, begin: int, end: int, ps: int = 30, coro: int = 5):
    pn = begin
	
    async for data in crawler.get_many(uid, begin=begin, end=end, ps=ps, coro=coro):
        code, message = data['code'], data['message']

        if code != 0:
            logging.error(f'\n接口返回值出错: {code}, Message: {message}\n')
            break
		
        items = data['data']['items'] or []

        if not items:
            logging.info(f'用户 {uid} 第 {pn} 页无数据，退出')
            break
			
        pn += 1 
		
        for item in items:
            for pic in item['pictures']:
                yield pic['img_src']


async def download_task(semaphore, session, url: str, dirpath: str, filename: str):
    file = AsyncFile(dirpath, filename)
    async with semaphore:
        await file.save_file_url(session, url, cover=False, timeout=10)


def main(
    uid: str = typer.Argument(..., help='用户uid'),
    dirpath: str = typer.Option('.', help='保存数据的目录路径'),
    begin: int = typer.Option(0, help='相簿起始页'),
    end: int = typer.Option(1, help='相簿结束页  下载范围为 [begin, end)'),
    ps: int = typer.Option(30, help='一页返回的数据个数，最大值为 50，大于这个值会报错'),
    req_coro_num: int = typer.Option(5, help='并发请求数'),
    download_coro_num: int = typer.Option(5, help='并发下载数'),
    text: bool = typer.Option(
        False, help='是否只保存图片链接到文本文件  适用于导入到下载工具批量下载或节省空间的情形'),
    tfilename: str = typer.Option('', help='保存链接的名称，默认为 ${用户uid}.txt')
):
    """
    下载b站指定用户的相簿图片并保存至本地

    e.g.: python app.py 2 --begin 0 --end 10 --dirpath './images/piaoxiu'
    """
    async def worker(dirpath, tfilename):

        semaphore = asyncio.Semaphore(download_coro_num)

        if dirpath == '.':
            dirpath = os.path.join('.', uid)

        async with BiliUserAlbumCrawler() as crawler:
            session = crawler.get_session()
            download_count = 0

            # 初始化文本文件名
            if not tfilename:
                tfilename = uid

            if not tfilename.endswith('.txt'):
                tfilename = tfilename + '.txt'
            # 文本文件写入对象
            file = AsyncFile(dirpath=dirpath, filename=tfilename)
            # 如果文本文件事先存在，清空
            if file.isfile():
                await file.save_file_text('', mode='w')

            logging.info(f'开始获取 {uid} 的相簿数据...')

            with tqdm(run(crawler, uid, begin=begin, end=end, ps=ps, coro=req_coro_num)) as pbar:
                # 用于保存图片 url
                url_list = []
                # 保存图片的协程列表
                tasks = []

                async for url in pbar:
                    if not text:  # 下载图片到本地
                        filename = url[url.rfind('/')+1:]
                        task = asyncio.create_task(download_task(
                            semaphore, session, url, dirpath, filename))
                        tasks.append(task)
                    else:  # 只保存图片链接到文本文件
                        url_list.append(url)
                    download_count += 1

                await file.save_file_text(url_list)

                if tasks:
                    await asyncio.wait(tasks)

            logging.info(f'{download_count} 条数据已保存至 > {dirpath}\\')

    start = time.time()

    # 给闭包传参，避免 eferenced before assignment
    asyncio.run(worker(dirpath, tfilename))

    end = round(time.time() - start, 2)
    logging.info(f'程序运行结束，耗时 {end}s')


if __name__ == '__main__':
    # 在这里计时并不会显示
    typer.run(main)

