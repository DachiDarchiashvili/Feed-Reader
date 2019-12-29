import os
import asynctest

from feed_fetcher.helpers import get_feed_as_dict


class XMLFeedParserTestCase(asynctest.TestCase):
    async def test_algemeen_xml_parses_successfully(self):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'data/algemeen.xml')
        service_name = 'www.nu.nl'
        with open(file_path, 'r') as f:
            res = await get_feed_as_dict(f.read(), service_name)
            self.assertTrue(isinstance(res, dict))
            self.assertEqual(len(res['items']), 3)
            self.assertEqual(res['ttl'], 60)
            self.assertEqual(res['link'], 'https://www.nu.nl/algemeen')
            self.assertEqual(res['title'], 'NU - Algemeen')

    async def test_feedburner_xml_parses_successfully(self):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'data/feedburner_tweakers_mixed.xml')
        service_name = 'feeds.feedburner.com'
        with open(file_path, 'r') as f:
            res = await get_feed_as_dict(f.read(), service_name)
            self.assertTrue(isinstance(res, dict))
            self.assertEqual(len(res['items']), 3)
            self.assertEqual(res['link'], 'https://tweakers.net/')
            self.assertEqual(res['title'], 'Tweakers Mixed RSS Feed')
