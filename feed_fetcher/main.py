#!/usr/bin/env python3

import asyncio
from asyncio import AbstractEventLoop

from django.conf import settings
from feed_fetcher.workers import worker, collect_tasks


def main():
    loop: AbstractEventLoop = asyncio.get_event_loop()
    loop.set_debug(settings.DEBUG)
    data = asyncio.Queue()

    tasks = [worker(data, _) for _ in range(settings.FEED_WORKERS_COUNT)]
    tasks.append(collect_tasks(data))
    task = asyncio.gather(*tasks)
    loop.run_until_complete(task)
    loop.close()


if __name__ == '__main__':
    import sys
    import os
    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'feed_reader.settings.prod')
    main()
