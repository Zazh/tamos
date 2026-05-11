from django.urls import path
from django.views.generic import TemplateView

from .views import ContactsView, HomeView

app_name = 'pages'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('landing/', TemplateView.as_view(template_name='pages/landing.html'), name='landing'),
    path('contacts/', ContactsView.as_view(), name='contacts'),
    path('gallery/', TemplateView.as_view(template_name='pages/gallery.html'), name='gallery'),
]
