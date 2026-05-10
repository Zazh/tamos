from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

from .views import root_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', root_redirect, name='root'),
]

urlpatterns += i18n_patterns(
    path('<slug:region_slug>/', include('pages.urls')),
    prefix_default_language=False,
)
