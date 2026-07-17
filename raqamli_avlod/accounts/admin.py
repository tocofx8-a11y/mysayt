from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ActivityLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'phone', 'observed_student', 'created_by', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumot', {'fields': ('role', 'phone', 'observed_student', 'telegram_chat_id', 'created_by')}),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'description', 'created_at')
    list_filter = ('actor__role',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
