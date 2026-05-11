from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from .models import HomePage


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        home = get_object_or_404(HomePage, region=self.request.region)
        ctx['home'] = home
        ctx['gallery'] = list(home.gallery.all())
        return ctx
