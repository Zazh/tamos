from django.urls import path

from .views import ContactsView, FlatPageView, HomeView

app_name = 'pages'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('contacts/', ContactsView.as_view(), name='contacts'),
    path('info/<slug:slug>/', FlatPageView.as_view(), name='flat'),
]
