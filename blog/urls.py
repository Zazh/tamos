from django.urls import path

from .views import BlogDetailView, BlogListView

app_name = 'blog'

urlpatterns = [
    path('blog/', BlogListView.as_view(), name='list'),
    path('blog/<slug:slug>/', BlogDetailView.as_view(), name='detail'),
]
