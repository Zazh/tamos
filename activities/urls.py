from django.urls import path

from .views import ActivitiesListView

app_name = 'activities'

urlpatterns = [
    path('activities/', ActivitiesListView.as_view(), name='list'),
]
