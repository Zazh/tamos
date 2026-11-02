from django.urls import path

from .views import EventLandingDetailView

app_name = 'eventlandings'

urlpatterns = [
    path('event/<slug:slug>/', EventLandingDetailView.as_view(), name='detail'),
]
