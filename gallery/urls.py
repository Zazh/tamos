from django.urls import path

from .views import GalleryListView

app_name = 'gallery'

urlpatterns = [
    path('gallery/', GalleryListView.as_view(), name='list'),
]
