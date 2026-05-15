from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView

from .models import ContactsPage, FlatPage, HomePage


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        home = get_object_or_404(HomePage, region=self.request.region)
        ctx['home'] = home
        ctx['gallery'] = list(home.gallery.all())
        return ctx


class ContactsView(TemplateView):
    template_name = 'pages/contacts.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        contacts = get_object_or_404(ContactsPage, region=self.request.region)
        ctx['contacts'] = contacts
        ctx['departments'] = list(contacts.departments.all())
        return ctx


class FlatPageView(DetailView):
    """Статичная контентная страница: about, uniform, privacy и т.п.

    Подсветка NavItem — через `active_page = page.slug` в шаблоне.
    """

    template_name = 'pages/flat.html'
    context_object_name = 'page'

    def get_object(self, queryset=None):
        return get_object_or_404(
            FlatPage.objects.filter(
                region=self.request.region,
                is_published=True,
            ),
            slug=self.kwargs['slug'],
        )
