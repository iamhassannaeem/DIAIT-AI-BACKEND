from django.contrib import admin
from .models import User, PermissionGroup

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_admin', 'is_active')
    list_filter = ('is_admin', 'is_active')
    search_fields = ('email', 'name')
    ordering = ('email',)

@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
