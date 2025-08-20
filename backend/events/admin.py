from django.contrib import admin
from .models import Event, Participant, AdminUser

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'venue', 'date', 'max_participants']
    list_filter = ['date', 'venue']
    search_fields = ['name', 'venue', 'description']

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'email', 'event', 'otp_verified', 'checked_in']
    list_filter = ['otp_verified', 'checked_in', 'event']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['qr_code']

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_college_admin', 'can_scan_qr', 'can_manage_participants', 'can_manage_events']
    list_filter = ['is_college_admin', 'can_scan_qr', 'can_manage_participants', 'can_manage_events']
    search_fields = ['user__username', 'user__email']
