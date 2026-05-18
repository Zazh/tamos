from django.urls import path

from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('leads/', views.leads_list, name='leads_list'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/status/', views.lead_quick_status, name='lead_quick_status'),

    # Content
    path('content/home/', views.content_home_list, name='content_home_list'),
    path('content/home/<int:pk>/', views.content_home_edit, name='content_home_edit'),
    path('content/home/<int:pk>/gallery/upload/', views.content_home_gallery_upload, name='content_home_gallery_upload'),
    path('content/home/<int:pk>/gallery/reorder/', views.content_home_gallery_reorder, name='content_home_gallery_reorder'),
    path('content/home/<int:pk>/gallery/<int:gpk>/', views.content_home_gallery_update, name='content_home_gallery_update'),
    path('content/home/<int:pk>/gallery/<int:gpk>/delete/', views.content_home_gallery_delete, name='content_home_gallery_delete'),
    path('content/home/<int:pk>/translate/', views.content_home_translate, name='content_home_translate'),
    path('content/home/<int:pk>/seo/', views.content_home_seo, name='content_home_seo'),
    path('content/contacts/', views.content_contacts_list, name='content_contacts_list'),
    path('content/contacts/<int:pk>/', views.content_contacts_edit, name='content_contacts_edit'),
    path('content/contacts/<int:pk>/translate/', views.content_contacts_translate, name='content_contacts_translate'),
    path('content/contacts/<int:pk>/seo/', views.content_contacts_seo, name='content_contacts_seo'),
    path('content/program/', views.content_program_list, name='content_program_list'),
    path('content/program/<int:pk>/', views.content_program_edit, name='content_program_edit'),
    path('content/program/<int:pk>/translate/', views.content_program_translate, name='content_program_translate'),
    path('content/program/<int:pk>/seo/', views.content_program_seo, name='content_program_seo'),
    path('content/admission/', views.content_admission_list, name='content_admission_list'),
    path('content/admission/<int:pk>/', views.content_admission_edit, name='content_admission_edit'),
    path('content/admission/<int:pk>/translate/', views.content_admission_translate, name='content_admission_translate'),
    path('content/admission/variant/<int:vpk>/', views.content_admission_variant_edit, name='content_admission_variant_edit'),
    path('content/admission/variant/<int:vpk>/translate/', views.content_admission_variant_translate, name='content_admission_variant_translate'),
    path('content/admission/variant/<int:vpk>/seo/', views.content_admission_variant_seo, name='content_admission_variant_seo'),

    # Activities (Activity + ActivityGroup + ScheduleSlot)
    path('content/activities/', views.content_activities_list, name='content_activities_list'),
    path('content/activities/region/<int:region_pk>/', views.content_activities_region, name='content_activities_region'),
    path('content/activities/region/<int:region_pk>/add/', views.content_activities_activity_add, name='content_activities_activity_add'),
    path('content/activities/region/<int:region_pk>/reorder/', views.content_activities_reorder, name='content_activities_reorder'),
    path('content/activities/<int:pk>/save/', views.content_activities_save, name='content_activities_save'),
    path('content/activities/<int:pk>/delete/', views.content_activities_activity_delete, name='content_activities_activity_delete'),
    path('content/activities/<int:pk>/translate/', views.content_activities_translate, name='content_activities_translate'),
    path('content/activities/<int:pk>/group/add/', views.content_activities_group_add, name='content_activities_group_add'),
    path('content/activities/group/<int:gpk>/', views.content_activities_group_edit, name='content_activities_group_edit'),
    path('content/activities/group/<int:gpk>/delete/', views.content_activities_group_delete, name='content_activities_group_delete'),
    path('content/activities/group/<int:gpk>/translate/', views.content_activities_group_translate, name='content_activities_group_translate'),
]
