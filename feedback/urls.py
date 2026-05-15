from django.urls import path

from .views import LeadCreateView

app_name = 'feedback'

urlpatterns = [
    path('feedback/', LeadCreateView.as_view(), name='create'),
]
