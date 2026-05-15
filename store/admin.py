from django.contrib import admin
from .models import Product,Variation,ReviewRating,ProductGallery,VariationCategory
import admin_thumbnails
from modeltranslation.admin import TranslationAdmin
from django.utils.html import format_html


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

    readonly_fields = ('image_preview',)  # ✅ ADD
    fields = ('image', 'image_preview')   # ✅ ADD

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img class="preview-img" src="{}" width="80" style="border-radius:5px;"/>',
                obj.image.url
            )
        return format_html('<img class="preview-img" width="80" style="display:none; border-radius:5px;"/>')

    image_preview.short_description = 'Preview'

# Register your models here.
class ProductAdmin(TranslationAdmin):
    # This line tells Django to "auto-fill" the slug based on the product_name
    prepopulated_fields = {'slug': ('product_name',)} 
    search_fields = (
        'product_code', 
        'product_name', 
        'price', 
        'stock', 
        'category__category_name', 
        'modified_date',           
        'slug'
    )
    # Other helpful admin settings
    list_display = ('product_code', 'product_name', 'price', 'stock', 'category', 'image_preview', 'modified_date', 'is_available')
    readonly_fields = ('image_preview',)

    fields = (
        'product_code', 'product_name', 'slug', 'description', 'price',
        'images', 'image_preview',   
        'stock', 'category', 'is_available'
    )
    
    def image_preview(self, obj):
        if obj and obj.images:
            return format_html(
                '<img class="admin-preview-image" src="{}" width="100" style="border-radius:5px;"/>',
                obj.images.url
            )
        # This empty tag is the "target" for our JavaScript
        return format_html('<img class="admin-preview-image" width="100" style="display:none; border-radius:5px;"/>')

    inlines = [ProductGalleryInline]

    class Media:
        js = (
            'js/admin_form_validation.js', 
            'js/image_preview.js',
        )

# Make sure you register the model with the Admin class
admin.site.register(Product, ProductAdmin)

@admin.register(VariationCategory)
class VariationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    search_fields = ('product__product_name', 'variation_category__name', 'variation_value')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)