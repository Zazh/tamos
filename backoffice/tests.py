import re

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from eventlandings.models import EventLanding
from regions.models import Region
from team.models import TeamMember

from .forms import EventLandingEditForm


def _form_to_data(form):
    """POST-данные из unbound-формы: текущие значения полей под их html-именами."""
    data = {}
    for name in form.fields:
        bf = form[name]
        value = bf.value()
        if value is None or value is False:
            continue
        if value is True:
            data[bf.html_name] = 'on'
        elif isinstance(value, (list, tuple)):
            data[bf.html_name] = [str(v) for v in value]
        else:
            data[bf.html_name] = str(value)
    return data


class BackofficeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.astana = Region.objects.get(slug='astana')
        cls.aktau = Region.objects.get(slug='aktau')
        cls.superuser = User.objects.create_superuser('su', 'su@example.com', 'pass')
        cls.manager_aktau = User.objects.create_user(
            'manager-aktau', password='pass', is_staff=True, manager_region=cls.aktau)

    def setUp(self):
        self.client.force_login(self.superuser)


class EventLandingSectionTests(BackofficeTestCase):
    """EF-10: раздел «Мероприятия» — список, lazy-create, edit, translate."""

    def setUp(self):
        super().setUp()
        self.day = EventLanding.objects.get(region=self.astana, slug='cambridge-day')

    def _edit_url(self, landing):
        return reverse('backoffice:content_eventlandings_edit', kwargs={'pk': landing.pk})

    def _post_edit(self, landing, **overrides):
        data = _form_to_data(EventLandingEditForm(instance=landing, user=self.superuser))
        for key, value in overrides.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
        return self.client.post(self._edit_url(landing), data)

    def test_list_superuser_sees_astana_landings(self):
        resp = self.client.get(reverse('backoffice:content_eventlandings_list'))
        self.assertEqual(resp.status_code, 200)
        slugs = {lp.slug for lp in resp.context['page'].object_list}
        self.assertEqual(slugs, {'cambridge-day', 'skills-xxi', 'cambridge-programme-leader'})

    def test_create_makes_draft_in_default_region(self):
        resp = self.client.post(reverse('backoffice:content_eventlandings_create'))
        landing = EventLanding.objects.latest('pk')
        self.assertRedirects(resp, self._edit_url(landing), fetch_redirect_response=False)
        self.assertTrue(landing.slug.startswith('draft-'))
        self.assertEqual(landing.region, Region.objects.get(is_default=True))
        self.assertFalse(landing.is_published)

    def test_first_title_turns_draft_slug_readable(self):
        self.client.post(reverse('backoffice:content_eventlandings_create'))
        landing = EventLanding.objects.latest('pk')
        resp = self._post_edit(landing, title_ru='Тест')
        self.assertRedirects(resp, self._edit_url(landing), fetch_redirect_response=False)
        landing.refresh_from_db()
        self.assertRegex(landing.slug, r'^test-[0-9a-f]{4}$')
        # Второе сохранение slug не трогает.
        self._post_edit(landing, title_ru='Другое название')
        slug = landing.slug
        landing.refresh_from_db()
        self.assertEqual(landing.slug, slug)

    def test_paid_price_saved(self):
        resp = self._post_edit(self.day, is_paid='on', price='1000')
        self.assertEqual(resp.status_code, 302)
        self.day.refresh_from_db()
        self.assertTrue(self.day.is_paid)
        self.assertEqual(self.day.price, 1000)

    def test_paid_without_price_is_error(self):
        resp = self._post_edit(self.day, is_paid='on', price=None)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('price', resp.context['form'].errors)
        self.day.refresh_from_db()
        self.assertFalse(self.day.is_paid)

    def test_free_event_drops_parent_checkbox(self):
        self._post_edit(self.day, show_parent_checkbox='on')
        self.day.refresh_from_db()
        self.assertFalse(self.day.show_parent_checkbox)

    def test_publish_without_title_is_error_on_top(self):
        resp = self._post_edit(self.day, title_ru='', is_published='on')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['form'].non_field_errors())
        self.assertContains(resp, 'заполните заголовок на русском')
        self.day.refresh_from_db()
        self.assertEqual(self.day.title_ru, 'Cambridge Day')

    def test_slug_and_region_not_editable_via_post(self):
        self._post_edit(self.day, slug='hacked', region=str(self.aktau.pk))
        self.day.refresh_from_db()
        self.assertEqual((self.day.slug, self.day.region_id), ('cambridge-day', self.astana.pk))

    def test_leader_from_other_region_rejected(self):
        stranger = TeamMember.objects.create(
            region=self.aktau, slug='stranger', name='Чужой', role='Педагог', is_published=True)
        before = set(self.day.leaders.values_list('pk', flat=True))
        resp = self._post_edit(self.day, leaders=[str(stranger.pk)])
        self.assertEqual(resp.status_code, 200)
        self.assertIn('leaders', resp.context['form'].errors)
        self.assertEqual(set(self.day.leaders.values_list('pk', flat=True)), before)

    def test_leaders_saved(self):
        member = TeamMember.objects.create(
            region=self.astana, slug='ef10-leader', name='Ведущий', role='Педагог', is_published=True)
        self._post_edit(self.day, leaders=[str(member.pk)])
        self.assertEqual(list(self.day.leaders.all()), [member])

    @override_settings(GEMINI_API_KEY='')
    def test_translate_without_key_is_503_json(self):
        resp = self.client.post(
            reverse('backoffice:content_eventlandings_translate', kwargs={'pk': self.day.pk}),
            data='{"by_lang": {"kk": {"title_kk": "Cambridge Day"}}}',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 503)
        self.assertIn('error', resp.json())

    def test_delete(self):
        resp = self.client.post(
            reverse('backoffice:content_eventlandings_delete', kwargs={'pk': self.day.pk}))
        self.assertRedirects(
            resp, reverse('backoffice:content_eventlandings_list'), fetch_redirect_response=False)
        self.assertFalse(EventLanding.objects.filter(pk=self.day.pk).exists())

    def test_manager_of_other_region_gets_404(self):
        self.client.force_login(self.manager_aktau)
        resp = self.client.get(reverse('backoffice:content_eventlandings_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['page'].object_list), [])
        pk = {'pk': self.day.pk}
        self.assertEqual(self.client.get(self._edit_url(self.day)).status_code, 404)
        for name in ('translate', 'seo', 'delete'):
            url = reverse(f'backoffice:content_eventlandings_{name}', kwargs=pk)
            self.assertEqual(self.client.post(url).status_code, 404, name)
        self.assertTrue(EventLanding.objects.filter(pk=self.day.pk).exists())

    def test_manager_creates_in_own_region(self):
        self.client.force_login(self.manager_aktau)
        self.client.post(reverse('backoffice:content_eventlandings_create'))
        self.assertEqual(EventLanding.objects.latest('pk').region, self.aktau)

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        resp = self.client.get(reverse('backoffice:content_eventlandings_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(re.match(re.escape(reverse('backoffice:login')), resp.url))
