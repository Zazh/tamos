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
]
