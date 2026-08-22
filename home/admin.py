from django.contrib import admin
from .models import Announcement, Banner, SectionOfferBanner, PromoBanner


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


@admin.register(SectionOfferBanner)
class SectionOfferBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'subtitle', 'category__category_name')
    list_filter = ('is_active', 'category')
    ordering = ('order', 'created_at')

@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('title',)
    list_filter = ('is_active',)
    ordering = ('created_at',)
