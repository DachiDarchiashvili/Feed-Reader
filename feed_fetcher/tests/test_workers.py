import asyncio
import datetime
import re
from datetime import timedelta

import asynctest
from django.utils import timezone

from feed_fetcher.tests.utils import get_cursor, get_session
from feed_fetcher.workers import fill_queue, pull_data


class FillQueueTestCase(asynctest.TestCase):
    async def setUp(self):
        self.test_feeds = [
            (1, 'https://www.dachi.me/rss/news', False, timezone.now(), 60, 1)
        ]
        self.cur = get_cursor(self.test_feeds)
        self.data = asyncio.Queue()

    async def test_tasks_are_added_to_the_queue(self):
        await fill_queue(self.data, self.cur)
        self.assertEqual(self.data.qsize(), 1)
        data = await self.data.get()
        self.cur.execute.assert_awaited()
        self.cur.fetchall.assert_awaited()
        self.assertEqual(data[1], 'https://www.dachi.me/rss/news')

    async def test_tasks_are_being_scheduled_correctly(self):
        await fill_queue(self.data, self.cur)
        self.assertEqual(self.data.qsize(), 1)
        data = await self.data.get()
        self.cur.execute.assert_awaited()
        self.cur.fetchall.assert_awaited()
        scheduled_date = data[3] + timedelta(seconds=data[4])
        scheduled_date_str = datetime.datetime.strftime(
            scheduled_date, "%Y-%m-%d %H:%M:%S.%f")
        query = (f"UPDATE feed SET scan_after = '{scheduled_date_str}' "
                 f"WHERE id = 1")
        cur_execute_args_list = self.cur.execute.await_args_list
        self.assertEqual(len(cur_execute_args_list), 2)
        executed_query = self.cur.execute.await_args_list[1][0][0]
        executed_query = re.sub(r"\+\d{2}\:\d{2}'", r"'", executed_query)
        self.assertEqual(query, executed_query)


class PullData(asynctest.TestCase):
    async def setUp(self):
        self.test_feeds = [
            (1, 'https://www.dachi.me/rss/news', False, timezone.now(), 60, 1)
        ]
        self.data = asyncio.Queue()
        await self.data.put(self.test_feeds[0])

    @asynctest.patch('feed_fetcher.workers.terminate_feed')
    @asynctest.patch('feed_fetcher.workers.push_to_db')
    @asynctest.patch('feed_fetcher.workers.get_feed_as_dict')
    @asynctest.patch('feed_fetcher.workers.aiohttp.ClientSession')
    async def test_success_request_leads_to_correct_calls(
            self, mock_client_session, mock_parser, mock_db_insert,
            mock_feed_termination
    ):
        client, response = get_session("Dummy content", 200)
        mock_client_session.return_value.__aenter__.side_effect = client
        conn = asynctest.CoroutineMock()
        await pull_data(self.data, conn)
        self.assertEqual(self.data.qsize(), 0)
        response.assert_called_once()
        mock_parser.assert_awaited()
        mock_db_insert.assert_awaited()
        mock_feed_termination.assert_not_awaited()

    @asynctest.patch('feed_fetcher.workers.terminate_feed')
    @asynctest.patch('feed_fetcher.workers.push_to_db')
    @asynctest.patch('feed_fetcher.workers.get_feed_as_dict')
    @asynctest.patch('feed_fetcher.workers.aiohttp.ClientSession')
    async def test_back_off_mechanism(
            self, mock_client_session, mock_parser, mock_db_insert,
            mock_feed_termination
    ):
        client, response = get_session("Dummy content", 400)
        mock_client_session.return_value.__aenter__.side_effect = client
        conn = asynctest.CoroutineMock()
        await pull_data(self.data, conn)
        self.assertEqual(self.data.qsize(), 0)
        response.assert_called()
        self.assertEqual(response.call_count, 5)
        mock_parser.assert_not_awaited()
        mock_db_insert.assert_not_awaited()
        mock_feed_termination.assert_awaited()
