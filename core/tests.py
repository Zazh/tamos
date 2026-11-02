from django.test import TestCase

from eventlandings.models import EventLanding
from regions.models import Region


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

    def test_inactive_region_landing_excluded(self):
        almaty = Region.objects.get(slug='almaty')  # is_active=False (regions/0005)
        EventLanding.objects.create(region=almaty, slug='inactive-region', title='X', is_published=True)
        self.assertNotIn('inactive-region', self.client.get('/sitemap.xml').content.decode())
