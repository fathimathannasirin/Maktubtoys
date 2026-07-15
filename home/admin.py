from django.contrib import admin
from .models import Announcement, Banner


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('text', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('text',)
    ordering = ('order', 'created_at')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'subtitle')
    list_filter = ('is_active',)
    ordering = ('order', 'created_at')
