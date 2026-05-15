from django.urls import path

from .views import EventDetailView, EventListView

app_name = 'events'

urlpatterns = [
    path('events/', EventListView.as_view(), name='list'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='detail'),
]
