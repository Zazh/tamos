from django.urls import path

from .views import AdmissionDepartmentRedirectView, AdmissionRootRedirectView, AdmissionView

app_name = 'admission'

urlpatterns = [
    path('admission/', AdmissionRootRedirectView.as_view(), name='root'),
    path(
        'admission/<slug:department_slug>/',
        AdmissionDepartmentRedirectView.as_view(),
        name='department',
    ),
    path(
        'admission/<slug:department_slug>/grade-<slug:grade_slug>/',
        AdmissionView.as_view(),
        name='detail',
    ),
]
