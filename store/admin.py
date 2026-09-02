from django.contrib import admin
from .models import Product,Variation,ReviewRating,ProductGallery,VariationCategory
import admin_thumbnails
from modeltranslation.admin import TranslationAdmin
from django.utils.html import format_html
from import_export.admin import ExportActionMixin
from import_export import resources
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from orders.models import OrderProduct, ReturnRequest
from warehousing.models import PurchaseItem, ReturnItem

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('product_code', 'sku', 'upc', 'product_name', 'price', 'cost_price', 'margin_amount', 'margin_percentage', 'stock', 'category', 'supplier', 'warehouse', 'is_available')
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
        'sku',
        'upc',
        'product_name', 
        'price', 
        'stock', 
        'category__category_name', 
        'modified_date',           
        'slug'
    )
    # Other helpful admin settings
    list_display = ('product_code', 'sku', 'upc', 'product_name', 'price', 'cost_price', 'margin_amount', 'margin_percentage', 'stock', 'category', 'supplier', 'warehouse', 'image_preview', 'is_available')
    list_filter = ('supplier', 'warehouse', 'category', StockStatusFilter, 'is_available', 'modified_date')
    prepopulated_fields = {'slug': ('product_name',)}
    readonly_fields = ('image_preview', 'barcode_preview', 'margin_amount', 'margin_percentage')
    actions = ('regenerate_barcodes',)

    fields = (
        'product_code', 'product_name', 'slug', 'description', 'price',
        'cost_price', 'margin_amount', 'margin_percentage',
        'images', 'image_preview',   
        'stock', 'category', 'age', 'supplier', 'warehouse', 'is_available',
        'sku', 'upc', 'barcode_preview'
    )
    
    change_form_template = 'admin/store/product_change_form.html'
    inlines = [ProductGalleryInline]

    def get_urls(self):
        urls = super().get_urls()
        barcode_urls = [
            path(
                '<path:object_id>/barcode/print/',
                self.admin_site.admin_view(self.print_barcode),
                name='store_product_print_barcode',
            ),
        ]
        return barcode_urls + urls

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.generate_barcode():
            obj.save(update_fields=['barcode_image'])

    @admin.action(description='Regenerate barcode images for selected products')
    def regenerate_barcodes(self, request, queryset):
        generated_count = 0
        for product in queryset:
            if product.generate_barcode():
                product.save(update_fields=['barcode_image'])
                generated_count += 1
        self.message_user(request, f'Generated {generated_count} barcode image(s).')

    def barcode_preview(self, obj):
        if not obj or not obj.barcode_image:
            return 'The barcode image is generated after the product is saved.'
        print_url = reverse('admin:store_product_print_barcode', args=[obj.pk])
        return format_html(
            '<img src="{}" width="260" alt="Barcode for {}"/><br>'
            '<a class="button" href="{}" target="_blank">Print barcode</a>',
            obj.barcode_image.url,
            obj.product_name,
            print_url,
        )

    barcode_preview.short_description = 'Barcode'

    def print_barcode(self, request, object_id):
        product = get_object_or_404(Product, pk=object_id)
        if not product.barcode_image:
            self.message_user(request, 'Save or regenerate this product to create its barcode image.')
            return redirect(reverse('admin:store_product_change', args=[product.pk]))
        return render(request, 'admin/barcode_print.html', {'product': product})

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            product = self.get_object(request, object_id)
            if product:
                # 1. TOP CARDS STATS
                inv_qty = product.stock or 0
                inv_val = float(product.price or 0) * inv_qty

                sales_agg = OrderProduct.objects.filter(product=product, ordered=True).aggregate(
                    total_qty=Sum('quantity'),
                    total_amt=Sum(F('quantity') * F('product_price'))
                )
                sales_qty = sales_agg['total_qty'] or 0
                sales_amt = sales_agg['total_amt'] or 0.0

                return_qty = ReturnRequest.objects.filter(
                    order__orderproduct__product=product
                ).distinct().count()

                # 2. TABLES DATA
                purchase_items = PurchaseItem.objects.filter(product=product).select_related('purchase', 'purchase__supplier', 'purchase__warehouse')
                purchase_returns = ReturnItem.objects.filter(product=product).select_related('return_record', 'return_record__supplier', 'return_record__warehouse')
                customer_orders = OrderProduct.objects.filter(product=product).select_related('order')

                extra_context.update({
                    'inv_qty': inv_qty,
                    'inv_val': inv_val,
                    'sales_qty': sales_qty,
                    'sales_amt': sales_amt,
                    'return_qty': return_qty,
                    'purchase_items': purchase_items,
                    'purchase_returns': purchase_returns,
                    'customer_orders': customer_orders,
                })

        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def image_preview(self, obj):
        if obj and obj.images:
            return format_html(
                '<img class="admin-preview-image" src="{}" width="100" style="border-radius:5px;"/>',
                obj.images.url
            )
        # This empty tag is the "target" for our JavaScript
        return format_html('<img class="admin-preview-image" width="100" style="display:none; border-radius:5px;"/>')

    
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
