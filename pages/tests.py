from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase


def _img(name, orientation):
    return SimpleNamespace(
        orientation=orientation,
        image_webp=SimpleNamespace(url=f'/{name}.webp'),
        image_compressed=SimpleNamespace(url=f'/{name}.jpg'),
        alt_text=name.upper(),
    )


class SchoolCarouselPartialTests(SimpleTestCase):
    def test_two_tracks_no_js_directive(self):
        html = render_to_string(
            'partials/school_carousel.html',
            {'images': [_img('a', 'wide'), _img('b', 'tall')]},
        )
        self.assertEqual(html.count('class="carousel-track"'), 2)
        self.assertEqual(html.count('class="carousel-item '), 4)
        self.assertIn('<ul class="carousel-track" aria-hidden="true">', html)
        self.assertNotIn('x-carousel-scroll', html)
        self.assertIn('carousel-item-wide', html)
        self.assertIn('alt="A"', html)
