from django.contrib import admin
from .models import Product,Variation,ReviewRating,ProductGallery,VariationCategory
import admin_thumbnails
from modeltranslation.admin import TranslationAdmin
from django.utils.html import format_html
from import_export.admin import ExportActionMixin
from import_export import resources

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('product_code', 'product_name', 'price', 'cost_price', 'margin_amount', 'margin_percentage', 'stock', 'category', 'supplier', 'warehouse', 'is_available')
        export_order = fields
class StockStatusFilter(admin.SimpleListFilter):
    title = 'Stock Status'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', 'In Stock (> 0)'),
            ('out_of_stock', 'Out of Stock (0)'),
            ('low_stock', 'Low Stock (<= 5)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock__gt=0)
        if self.value() == 'out_of_stock':
            return queryset.filter(stock=0)
        if self.value() == 'low_stock':
            return queryset.filter(stock__lte=5, stock__gt=0)
        return queryset


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
class ProductAdmin(ExportActionMixin, TranslationAdmin):
    resource_class = ProductResource
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
    list_display = ('product_code', 'product_name', 'price', 'cost_price', 'margin_amount', 'margin_percentage', 'stock', 'category', 'supplier', 'warehouse', 'image_preview', 'is_available')
    list_filter = ('supplier', 'warehouse', 'category', StockStatusFilter, 'is_available', 'modified_date')
    prepopulated_fields = {'slug': ('product_name',)}
    readonly_fields = ('image_preview', 'margin_amount', 'margin_percentage')

    fields = (
        'product_code', 'product_name', 'slug', 'description', 'price',
        'cost_price', 'margin_amount', 'margin_percentage',
        'images', 'image_preview',   
        'stock', 'category', 'age', 'supplier', 'warehouse', 'is_available'
    )
    
    change_form_template = 'admin/store/product_change_form.html'
    
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
