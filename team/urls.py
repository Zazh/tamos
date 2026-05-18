from django.urls import path

from .views import TeamDetailView, TeamListView

app_name = 'team'

urlpatterns = [
    path('team/', TeamListView.as_view(), name='list'),
    path('team/<slug:slug>/', TeamDetailView.as_view(), name='detail'),
]
