from django.test import TestCase


class SitemapTests(TestCase):
    def test_event_landings_and_feed(self):
        resp = self.client.get('/sitemap.xml')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('application/xml'))
        xml = resp.content.decode()
        self.assertIn('/ru/astana/event/cambridge-day/', xml)
        self.assertIn('/kk/astana/event/cambridge-programme-leader/', xml)
        self.assertNotIn('skills-xxi', xml)  # черновик
        self.assertIn('/ru/astana/events/', xml)
        self.assertNotIn('/aktau/event/', xml)
