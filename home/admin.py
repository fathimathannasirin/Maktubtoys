from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from .models import AdminPinnedApp, Announcement, Banner, SectionOfferBanner, PromoBanner


@admin.register(AdminPinnedApp)
class AdminPinnedAppAdmin(admin.ModelAdmin):
    list_display = ('app_label', 'order', 'is_pinned')
    list_editable = ('order', 'is_pinned')
    list_display_links = ('app_label',)
    ordering = ('order', 'app_label')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'toggle/<str:app_label>/',
                self.admin_site.admin_view(self.toggle_pin),
                name='home_adminpinnedapp_toggle',
            ),
        ]
        return custom_urls + urls

    def toggle_pin(self, request, app_label):
        if request.method != 'POST':
            return redirect('admin:index')

        setting, created = AdminPinnedApp.objects.get_or_create(
            app_label=app_label,
            defaults={'order': 100, 'is_pinned': False},
        )
        setting.is_pinned = not setting.is_pinned
        if setting.is_pinned:
            highest_order = AdminPinnedApp.objects.filter(is_pinned=True).exclude(pk=setting.pk).order_by('-order').values_list('order', flat=True).first()
            setting.order = (highest_order or 0) + 10
        setting.save(update_fields=['is_pinned', 'order'])
        messages.success(request, f'{setting} updated in the admin sidebar.')
        return redirect(request.META.get('HTTP_REFERER') or 'admin:index')


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
