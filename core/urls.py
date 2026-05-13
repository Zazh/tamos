from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import llms_txt, robots_txt, root_redirect, sitemap_xml

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('robots.txt', robots_txt, name='robots'),
    path('llms.txt', llms_txt, name='llms'),
    path('sitemap.xml', sitemap_xml, name='sitemap'),
    path('', root_redirect, name='root'),
]

urlpatterns += i18n_patterns(
    path('<slug:region_slug>/', include('pages.urls')),
    path('<slug:region_slug>/', include('programs.urls')),
    path('<slug:region_slug>/', include('activities.urls')),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
