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
    path('content/footer/', views.content_footer_list, name='content_footer_list'),
    path('content/footer/<int:pk>/', views.content_footer_edit, name='content_footer_edit'),
    path('content/footer/<int:pk>/translate/', views.content_footer_translate, name='content_footer_translate'),
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

    # Blog
    path('content/blog/', views.content_blog_list, name='content_blog_list'),
    path('content/blog/new/', views.content_blog_create, name='content_blog_create'),
    path('content/blog/<int:pk>/', views.content_blog_edit, name='content_blog_edit'),
    path('content/blog/<int:pk>/delete/', views.content_blog_delete, name='content_blog_delete'),
    path('content/blog/<int:pk>/translate/', views.content_blog_translate, name='content_blog_translate'),
    path('content/blog/<int:pk>/seo/', views.content_blog_seo, name='content_blog_seo'),
    path('content/blog/<int:pk>/suggest-tags/', views.content_blog_suggest_tags, name='content_blog_suggest_tags'),
    path('content/blog/<int:pk>/gallery/upload/', views.content_blog_gallery_upload, name='content_blog_gallery_upload'),
    path('content/blog/<int:pk>/gallery/reorder/', views.content_blog_gallery_reorder, name='content_blog_gallery_reorder'),
    path('content/blog/<int:pk>/gallery/<int:gpk>/', views.content_blog_gallery_update, name='content_blog_gallery_update'),
    path('content/blog/<int:pk>/gallery/<int:gpk>/delete/', views.content_blog_gallery_delete, name='content_blog_gallery_delete'),
    path('content/blog/taxonomy/', views.content_blog_taxonomy, name='content_blog_taxonomy'),
    path('content/blog/taxonomy/category/save/', views.content_blog_category_save, name='content_blog_category_save'),
    path('content/blog/taxonomy/category/<int:pk>/delete/', views.content_blog_category_delete, name='content_blog_category_delete'),
    path('content/blog/taxonomy/tag/save/', views.content_blog_tag_save, name='content_blog_tag_save'),
    path('content/blog/taxonomy/tag/<int:pk>/delete/', views.content_blog_tag_delete, name='content_blog_tag_delete'),

    # Events
    path('content/events/', views.content_events_list, name='content_events_list'),
    path('content/events/new/', views.content_events_create, name='content_events_create'),
    path('content/events/<int:pk>/', views.content_events_edit, name='content_events_edit'),
    path('content/events/<int:pk>/delete/', views.content_events_delete, name='content_events_delete'),
    path('content/events/<int:pk>/translate/', views.content_events_translate, name='content_events_translate'),
    path('content/events/<int:pk>/seo/', views.content_events_seo, name='content_events_seo'),
    path('content/events/<int:pk>/gallery/upload/', views.content_events_gallery_upload, name='content_events_gallery_upload'),
    path('content/events/<int:pk>/gallery/reorder/', views.content_events_gallery_reorder, name='content_events_gallery_reorder'),
    path('content/events/<int:pk>/gallery/<int:gpk>/', views.content_events_gallery_update, name='content_events_gallery_update'),
    path('content/events/<int:pk>/gallery/<int:gpk>/delete/', views.content_events_gallery_delete, name='content_events_gallery_delete'),

    # Gallery (фотогалерея — album-based)
    path('content/gallery/', views.content_gallery_list, name='content_gallery_list'),
    path('content/gallery/new/', views.content_gallery_create, name='content_gallery_create'),
    path('content/gallery/taxonomy/', views.content_gallery_taxonomy, name='content_gallery_taxonomy'),
    path('content/gallery/taxonomy/save/', views.content_gallery_category_save, name='content_gallery_category_save'),
    path('content/gallery/taxonomy/<int:pk>/delete/', views.content_gallery_category_delete, name='content_gallery_category_delete'),
    path('content/gallery/<int:pk>/', views.content_gallery_edit, name='content_gallery_edit'),
    path('content/gallery/<int:pk>/delete/', views.content_gallery_delete, name='content_gallery_delete'),
    # Фото внутри альбома (AJAX)
    path('content/gallery/<int:pk>/photo/upload/', views.content_gallery_photo_upload, name='content_gallery_photo_upload'),
    path('content/gallery/<int:pk>/photo/<int:ipk>/toggle/', views.content_gallery_photo_toggle, name='content_gallery_photo_toggle'),
    path('content/gallery/<int:pk>/photo/<int:ipk>/update/', views.content_gallery_photo_update, name='content_gallery_photo_update'),
    path('content/gallery/<int:pk>/photo/<int:ipk>/delete/', views.content_gallery_photo_delete, name='content_gallery_photo_delete'),
    path('content/gallery/<int:pk>/photo/<int:ipk>/translate/', views.content_gallery_photo_translate, name='content_gallery_photo_translate'),

    # Flat Pages (доп. страницы — about, uniform, privacy и т.п.)
    path('content/flatpages/', views.content_flatpages_list, name='content_flatpages_list'),
    path('content/flatpages/new/', views.content_flatpages_create, name='content_flatpages_create'),
    path('content/flatpages/<int:pk>/', views.content_flatpages_edit, name='content_flatpages_edit'),
    path('content/flatpages/<int:pk>/delete/', views.content_flatpages_delete, name='content_flatpages_delete'),
    path('content/flatpages/<int:pk>/translate/', views.content_flatpages_translate, name='content_flatpages_translate'),
    path('content/flatpages/<int:pk>/seo/', views.content_flatpages_seo, name='content_flatpages_seo'),

    # Team
    path('content/team/', views.content_team_list, name='content_team_list'),
    path('content/team/region/<int:region_pk>/', views.content_team_region, name='content_team_region'),
    path('content/team/region/<int:region_pk>/reorder/', views.content_team_reorder, name='content_team_reorder'),
    path('content/team/new/', views.content_team_create, name='content_team_create'),
    path('content/team/<int:pk>/', views.content_team_edit, name='content_team_edit'),
    path('content/team/<int:pk>/delete/', views.content_team_delete, name='content_team_delete'),
    path('content/team/<int:pk>/translate/', views.content_team_translate, name='content_team_translate'),
    path('content/team/<int:pk>/seo/', views.content_team_seo, name='content_team_seo'),

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

    # Site → Menu (NavSection + NavItem)
    path('site/menu/', views.site_menu_list, name='site_menu_list'),
    path('site/menu/new/', views.site_menu_create, name='site_menu_create'),
    path('site/menu/<int:pk>/', views.site_menu_edit, name='site_menu_edit'),
    path('site/menu/<int:pk>/delete/', views.site_menu_delete, name='site_menu_delete'),
    path('site/menu/item/<int:pk>/delete/', views.site_menu_item_delete, name='site_menu_item_delete'),

    # Settings → Regions
    path('settings/regions/', views.settings_regions_list, name='settings_regions_list'),
    path('settings/regions/new/', views.settings_regions_create, name='settings_regions_create'),
    path('settings/regions/<int:pk>/', views.settings_regions_edit, name='settings_regions_edit'),
    path('settings/regions/<int:pk>/delete/', views.settings_regions_delete, name='settings_regions_delete'),

    # Settings → Users
    path('settings/users/', views.settings_users_list, name='settings_users_list'),
    path('settings/users/new/', views.settings_users_create, name='settings_users_create'),
    path('settings/users/<int:pk>/', views.settings_users_edit, name='settings_users_edit'),
    path('settings/users/<int:pk>/password/', views.settings_users_password, name='settings_users_password'),
    path('settings/users/<int:pk>/delete/', views.settings_users_delete, name='settings_users_delete'),
]
