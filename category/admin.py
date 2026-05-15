from django.contrib import admin
from . models import Category
from modeltranslation.admin import TranslationAdmin
from django.utils.html import format_html
# Register your models here.
 
class BaseAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin_form_validation.js',)

class CategoryAdmin(BaseAdmin,TranslationAdmin):
    prepopulated_fields={'slug':('category_name',)}
    list_display = ('category_name', 'parent', 'slug', 'image_preview')
    list_filter = ('parent',)
    search_fields = ['category_name', 'slug']
    readonly_fields = ('image_preview',)

    fields = (
        'parent',
        'category_name', 'slug',
        'image', 'image_preview',   # 👈 preview here
        'description'
    )

    # Inside CategoryAdmin(BaseAdmin, TranslationAdmin):

    def image_preview(self, obj):
        if obj and obj.image:
            # Shows existing image
            return format_html(
                '<img class="admin-preview-image" src="{}" width="100" style="border-radius:5px;" />',
                obj.image.url
            )
        return format_html(
            '<img class="admin-preview-image" width="100" style="display:none; border-radius:5px;" />'
        )

    
    image_preview.short_description = 'Preview'

    class Media:
        js = (
            'js/admin_form_validation.js',
            'js/image_preview.js', 
        )

admin.site.register(Category, CategoryAdmin)
