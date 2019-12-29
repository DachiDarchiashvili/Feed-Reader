import datetime
import aiopg
import aiohttp
import asyncio
from urllib.parse import urlparse
from aiohttp import ClientConnectionError

from django.conf import settings
from django.utils import timezone

from feed_fetcher.helpers import get_feed_as_dict, push_to_db


async def get_db_pool():
    db = settings.DATABASES['default']
    dsn = (f'dbname={db["NAME"]} user={db["USER"]} password={db["PASSWORD"]} '
           f'host={db["HOST"]} port={db["PORT"]}')
    return await aiopg.create_pool(dsn)


async def terminate_feed(feed_id, conn):
    """
    Sets Feed flag terminated true after set of failures

    :param feed_id: Feed ID
    :param conn: DB connection
    :return: None
    """
    async with conn.cursor() as cur:
        query = f'UPDATE feed SET terminated = TRUE WHERE id = {feed_id}'
        await cur.execute(query)


async def fill_queue(data: asyncio.Queue, cur):
    """
    Adds feeds to the queue

    :param data: Queue
    :param cur: DB Cursor
    :return: None
    """
    query = (f"SELECT id, link, terminated, scan_after, ttl, user_id "
             f"FROM feed WHERE (scan_after <= '{timezone.now()}' OR "
             f"scan_after IS NULL ) AND terminated IS NOT TRUE")
    await cur.execute(query)
    feeds = await cur.fetchall()
    for feed in feeds:
        feed_id, url, terminated, scan_after, ttl, uid = feed
        scan_after = scan_after + datetime.timedelta(seconds=ttl)
        query = (f"UPDATE feed SET scan_after = '{scan_after}' "
                 f"WHERE id = {feed_id}")
        await cur.execute(query)
        await data.put(feed)


async def pull_data(data, conn):
    """
    Gets tasks from the queue, pulls feed content from the url, updates db

    :param data: Queue
    :param conn: DB Connection
    :return: None
    """
    feed_id, url, terminated, scan_after, ttl, uid = await data.get()
    retries = 5
    current_retry = 0
    backoff_factor = 0.1
    async with aiohttp.ClientSession() as session:
        while current_retry < retries:
            try:
                async with session.get(url) as response:
                    code = response.status
                    if code == 200:
                        text = await response.text()
                        url_prsd = urlparse(url)
                        feed_dict = await get_feed_as_dict(text,
                                                           url_prsd.hostname)
                        await push_to_db(feed_id, feed_dict, conn, uid)
                        break
            except ClientConnectionError:
                pass
            if current_retry > 0:
                current_wait = backoff_factor * 2 ** (current_retry - 1)
                if current_wait > 1:
                    # Maximum wait between waits is 1 second
                    current_wait = 1
                await asyncio.sleep(current_wait)
            current_retry += 1
    if current_retry == retries:
        await terminate_feed(feed_id, conn)


async def collect_tasks(data: asyncio.Queue):
    """
    Adds tasks to the queue

    :param data: Queue
    :return: None
    """
    print('Collect Tasks Worker Started')
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            while True:
                await fill_queue(data, cur)
                await asyncio.sleep(0.2)


async def worker(data: asyncio.Queue, num):
    """
    Consumes tasks from the queue and process them

    :param data: Queue
    :param num: Worker number (for logging)
    :return: None
    """
    print(f'Worker [{num}] Started')
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        while True:
            await pull_data(data, conn)
            queue_size = data.qsize()
            if queue_size:
                await asyncio.sleep(0)
            else:
                await asyncio.sleep(0.2)
