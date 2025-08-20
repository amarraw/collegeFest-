from django.urls import path
from . import views, api_views
from django.conf.urls.static import static
from django.conf import settings
from . import admin_views


urlpatterns = [
    # Traditional Django views
    path('', views.home, name='home'),
    path('register/<int:event_id>/', views.register, name='register'),
    path('success/<int:participant_id>/', views.success, name='success'),
    path('verify-otp/<int:participant_id>/', views.verify_otp, name='verify_otp'),
    path('dashboard/<int:participant_id>/', views.dashboard, name='dashboard'),
    
    # API endpoints
    path('api/events/', api_views.event_list, name='home_api'),
    path('api/register/<int:event_id>/', api_views.register_participant, name='register_api'),
    path('api/register-existing-user/<int:event_id>/', api_views.register_existing_user, name='register_existing_user_api'),
    path('api/verify-otp/<int:participant_id>/', api_views.verify_otp, name='verify_otp_api'),
    path('api/dashboard/<int:participant_id>/', api_views.dashboard, name='dashboard_api'),
    path('api/test-otp/', api_views.test_otp, name='test_otp_api'),
    path('api/resend-qr/<int:participant_id>/', api_views.resend_qr, name='resend_qr_api'),
    path('api/check-participant/', api_views.check_participant, name='check_participant_api'),
    
    # Admin API endpoints
    path('api/admin/login/', api_views.admin_login, name='admin_login_api'),
    path('api/admin/participants/', api_views.admin_participants, name='admin_participants_api'),
    path('api/admin/check-in/<int:participant_id>/', api_views.check_in_participant, name='check_in_participant_api'),
    path('api/admin/dashboard-stats/', api_views.admin_dashboard_stats, name='admin_dashboard_stats_api'),

    path('admin/adminlogin/', admin_views.admin_login_view, name='adminlogin'),
    path('admin/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/verify/<int:participant_id>/', admin_views.verify_participant, name='verify_participant'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
