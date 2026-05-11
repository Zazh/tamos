from django.urls import path

from .views import ProgramView

app_name = 'programs'

urlpatterns = [
    path('program/', ProgramView.as_view(), name='detail'),
]
