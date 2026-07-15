from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from import_export.admin import ExportActionMixin
from import_export import resources
from .models import Order, OrderProduct
from store.models import Product
from Accounts.models import Account
from carts.models import Cart
from category.models import Category
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from rangefilter.filters import DateRangeFilter
import datetime

class BaseAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin_form_validation.js',)

# Keep the dashboard simple and stable without depending on the stats plugin.
class AdminChartMixin:
    pass

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    fields = ('product', 'variations', 'quantity', 'product_price', 'ordered')
    readonly_fields = ('ordered',)
    extra = 1
    can_delete = True

    def display_variations(self, obj):
        variations = obj.variations.all()
        if variations.exists():
            return ", ".join([f"{v.variation_category}: {v.variation_value}" for v in variations])
        return ""
    display_variations.short_description = 'Variations'

    def get_total(self, obj):
        if obj.product_price is not None and obj.quantity is not None:
            return f"{obj.product_price * obj.quantity} QAR"
        return "0 QAR"
    get_total.short_description = 'Subtotal'

class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        # These are the fields that will appear as columns in your Excel sheet
        fields = (
            'order_number', 'first_name', 'last_name', 'email', 
            'phone', 'order_total', 'tax', 'status', 
            'payment_method', 'is_ordered', 'created_at'
        )
        export_order = fields

class OrderAdmin(ExportActionMixin,BaseAdmin,AdminChartMixin, admin.ModelAdmin):
    resource_class = OrderResource
    list_display = ['order_number', 'status_badge', 'status', 'created_at', 'full_name', 'phone', 'view_invoice', 'total_formatted']
    list_display_links = ('order_number', 'full_name')
    list_filter = ['status', ('created_at', DateRangeFilter)]
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    list_per_page = 20
    list_editable = ['status']
    inlines = [OrderProductInline]

    def save_model(self, request, obj, form, change):
        # 1. PROTECT WEBSITE ORDERS: 
        # If the order is coming from the website, it already has an order_number.
        # We only generate 'WA-' numbers for BRAND NEW manual entries.
        if not change and not obj.order_number:
            current_date = datetime.date.today().strftime("%Y%m%d")
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            obj.order_number = f"WA-{current_date}-{timestamp}"
        
        # 2. IP ADDRESS:
        # Website orders set the IP in the view. Manual orders get the Admin's IP.
        if not obj.ip:
            obj.ip = request.META.get('REMOTE_ADDR')
            
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Ensures OrderProducts get the same user as the main Order.
        If no user is selected (Manual Order), it remains None (Safe).
        """
        instances = formset.save(commit=False)
        selected_user = form.cleaned_data.get('user')

        for instance in instances:
            if isinstance(instance, OrderProduct):
                # This ONLY overwrites if the user is present in the form
                # preventing any 'NOT NULL' errors
                instance.user = selected_user
                instance.save()
        formset.save_m2m()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:order_id>/invoice/',
                self.admin_site.admin_view(self.admin_invoice_view),
                name='orders_order_invoice',
            ),
        ]
        return custom_urls + urls

    def admin_invoice_view(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        order_detail = OrderProduct.objects.filter(order=order)
        context = {
            'order': order,
            'order_detail': order_detail,
            'is_admin_view': True,
        }
        return TemplateResponse(request, 'orders/admin_invoice_pdf.html', context)

    def view_invoice(self, obj):
        if obj.id:
            url = reverse('admin:orders_order_invoice', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background:#6D001F; color:white; padding:6px 10px; border-radius:4px; text-decoration:none;">VIEW</a>',
                url
            )
        return "N/A"
    view_invoice.short_description = 'Invoice'

    def status_badge(self, obj):
        color_map = {
            'New': '#28a745',       
            'Accepted': '#17a2b8',  
            'Packed': '#6f42c1',    
            'On The Way': '#fd7e14',
            'Completed': '#007bff', 
            'Cancelled': '#dc3545', 
        }
        color = color_map.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold; text-transform: uppercase; font-size: 10px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'

    def total_formatted(self, obj):
        formatted_total = "{:,.2f} QAR".format(float(obj.order_total))
        return format_html('<span style="font-weight: bold; color: #212529;">{}</span>', formatted_total)
    total_formatted.short_description = 'Total Amount'

    fieldsets = (
        ('Order Overview', {
            'fields': ('user', 'order_number', 'status', 'is_ordered', 'payment_method', 'view_invoice')
        }),
        ('Customer & Delivery Information', {
            'fields': (
                ('first_name', 'last_name'), 
                ('email', 'phone'), 
                'address_line_1', 'address_line_2', 
                ('street_number', 'building_number', 'zone_number')
            )
        }),
        ('Payment Summary', {
            'fields': ('order_total', 'tax', 'payment', 'ip')
        }),
        ('Order Notes', {
            'fields': ('order_note',)}),
    )
    readonly_fields = ('order_number', 'payment', 'ip', 'created_at', 'view_invoice')

    class Media:
        js = (
            'js/admin_form_validation.js', # Keep your validation
            'js/admin_orders.js',          # Load the new automation
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = ('order_number', 'payment', 'ip', 'created_at', 'view_invoice')
        if obj:
            return readonly + ('order_total', 'tax')
        return readonly 
# --- DASHBOARD LOGIC ---
original_admin_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    extra_context = extra_context or {}
    
    try:
        # Standard KPI calculations
        extra_context['total_orders_count'] = Order.objects.count()
        extra_context['total_sales_amount'] = Order.objects.filter(is_ordered=True).aggregate(Sum('order_total'))['order_total__sum'] or 0
        extra_context['total_customers_count'] = Account.objects.filter(is_staff=False, is_admin=False).count()
        extra_context['active_products_count'] = Product.objects.filter(is_available=True).count()
        extra_context['out_of_stock_count'] = Product.objects.filter(stock=0).count()
        extra_context['abandoned_carts_count'] = Cart.objects.count()
        extra_context['recent_orders_list'] = Order.objects.all().order_by('-created_at')[:5]
        
    except Exception as e:
        print(f"Dashboard calculation error: {e}")

    # Always provide a safe empty chart list so the admin dashboard renders without errors.
    extra_context['kpi_graph'] = []

    return original_admin_index(request, extra_context)

admin.site.index = custom_admin_index
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)