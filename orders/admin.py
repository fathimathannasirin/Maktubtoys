from collections import Counter

from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q, Sum
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.utils import timezone
from import_export.admin import ExportActionMixin
from import_export import resources
from .models import (
    Order,
    OrderProduct,
    PendingOrder,
    PendingReturn,
    Parcel,
    ReturnRequest,
    ReturnRequestImage,
    ReturnStatusHistory,
)
from store.models import Product
from Accounts.models import Account
from carts.models import Cart
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from rangefilter.filters import DateRangeFilter

class BaseAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin_form_validation.js',)

# Keep the dashboard simple and stable without depending on the stats plugin.
class AdminChartMixin:
    pass

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    fields = ('product', 'supplier', 'warehouse', 'display_variations', 'quantity', 'product_price', 'ordered', 'get_total')
    readonly_fields = ('product', 'supplier', 'warehouse', 'display_variations', 'quantity', 'product_price', 'ordered', 'get_total')
    extra = 0
    can_delete = False

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

    def has_add_permission(self, request, obj=None):
        return False

class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        # These are the fields that will appear as columns in your Excel sheet
        fields = (
            'order_number', 'first_name', 'last_name', 'email', 
            'phone', 'order_total', 'delivery_charge', 'status', 
            'payment_method', 'is_ordered', 'created_at'
        )
        export_order = fields


class NoAddAdminMixin:
    def has_add_permission(self, request):
        return False


class NoAddDeleteAdminMixin(NoAddAdminMixin):
    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions


class BaseOrderAdmin(NoAddAdminMixin, ExportActionMixin, BaseAdmin, AdminChartMixin, admin.ModelAdmin):
    resource_class = OrderResource
    list_display = ['order_number', 'status_badge', 'status', 'created_at', 'full_name', 'phone', 'view_invoice', 'total_formatted']
    list_display_links = ('order_number', 'full_name')
    list_filter = ['status', ('created_at', DateRangeFilter)]
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    list_per_page = 20
    list_editable = ['status']
    inlines = [OrderProductInline]

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
        order_detail = list(OrderProduct.objects.filter(order=order).select_related('supplier', 'warehouse', 'product'))
        for item in order_detail:
            item.line_total = item.product_price * item.quantity
        subtotal = sum(item.line_total for item in order_detail)

        warehouses = []
        suppliers = []
        for item in order_detail:
            if item.warehouse and item.warehouse not in warehouses:
                warehouses.append(item.warehouse)
            if item.supplier and item.supplier not in suppliers:
                suppliers.append(item.supplier)

        payment = getattr(order, 'payment', None)
        payment_method_value = getattr(payment, 'Payment_method', None) or order.payment_method
        payment_status_value = getattr(payment, 'status', None)
        payment_id_value = getattr(payment, 'Payment_id', None)
        invoice_number_value = f"INV-{order.created_at.strftime('%Y%m%d')}-{order.id:06d}"

        context = {
            'order': order,
            'order_detail': order_detail,
            'subtotal': subtotal,
            'warehouses': warehouses,
            'suppliers': suppliers,
            'payment_method_value': payment_method_value,
            'payment_status_value': payment_status_value,
            'payment_id_value': payment_id_value,
            'invoice_number_value': invoice_number_value,
            'parcel_number_value': order.parcel_id,
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
            'Processing': '#28a745',             
            'Collecting':'#17a2b8',
            'Ready for Preparing': '#9c7b3e',
            'Preparing': '#8f63c7',
            'Ready for Delivery': '#4f86c6',
            'On The Way': '#fd7e14',
            'Delivered': '#198754',
            'Completed': '#007bff',
            'Return Requested': '#f39c12',
            'Returned': '#6c757d',
            'Refunded': '#20c997',
            'Failed': '#6c757d',
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
            'fields': ('order_total', 'delivery_charge', 'payment', 'ip')
        }),
        ('Order Notes', {
            'fields': ('order_note',)}),
    )
    readonly_fields = (
        'user', 'order_number', 'is_ordered', 'payment_method',
        'first_name', 'last_name', 'email', 'phone', 'address_line_1', 'address_line_2',
        'street_number', 'building_number', 'zone_number', 'order_total', 'delivery_charge',
        'payment', 'ip', 'created_at', 'order_note', 'view_invoice'
    )

    class Media:
        js = (
            'js/admin_form_validation.js', # Keep your validation
            'js/admin_orders.js',          # Load the new automation
        )


@admin.register(Order)
class OrderAdmin(BaseOrderAdmin):
    pass


@admin.register(PendingOrder)
class PendingOrderAdmin(BaseOrderAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.exclude(status__in=['Completed', 'Delivered', 'Cancelled', 'Return Requested', 'Returned', 'Refunded'])


@admin.register(PendingReturn)
class PendingReturnAdmin(BaseOrderAdmin):
    list_display = ['order_number', 'status_badge', 'status', 'created_at', 'full_name', 'phone', 'view_invoice', 'total_formatted']
    list_display_links = ('order_number', 'full_name')
    list_filter = [('created_at', DateRangeFilter)]
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(status__in=['Return Requested', 'Returned', 'Refunded'])


class ReturnRequestImageInline(admin.TabularInline):
    model = ReturnRequestImage
    extra = 0
    fields = ('image_preview', 'created_at')
    readonly_fields = ('image_preview', 'created_at')
    can_delete = False

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<a href="{0}" target="_blank" rel="noopener"><img src="{0}" style="max-width:120px; max-height:120px; object-fit:cover; border-radius:6px; border:1px solid #ddd;" /></a>',
                obj.image.url,
            )
        return '-'

    image_preview.short_description = 'Preview'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReturnStatusHistoryInline(admin.TabularInline):
    model = ReturnStatusHistory
    extra = 0
    readonly_fields = ('status', 'note', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = (
        'return_request_id',
        'order',
        'customer',
        'status',
        'refund_status',
        'created_at',
    )
    list_filter = ('status', 'refund_status', 'created_at')
    search_fields = (
        'return_request_id',
        'order__order_number',
        'customer__first_name',
        'customer__last_name',
        'customer__email',
    )
    readonly_fields = (
        'return_request_id',
        'order',
        'customer',
        'reason',
        'description',
        'ordered_products_summary',
        'return_shipping_acknowledged',
        'policy_terms_accepted',
        'created_at',
        'updated_at',
    )
    inlines = [ReturnRequestImageInline, ReturnStatusHistoryInline]
    actions = ['approve_returns', 'reject_returns', 'mark_refund_processing', 'mark_refund_completed']

    fieldsets = (
        ('Request Information', {
            'fields': (
                'return_request_id',
                'order',
                'customer',
                'reason',
                'description',
                'ordered_products_summary',
                'status',
                'created_at',
                'updated_at',
            )
        }),
        ('Refund & Resolution', {
            'fields': (
                'refund_status',
                'resolution_type',
                'refund_amount',
                'refund_completed_at',
            )
        }),
        ('Operational Notes', {
            'fields': (
                'admin_notes',
                'return_shipping_acknowledged',
                'policy_terms_accepted',
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == 'Refund Completed' and obj.refund_status != 'Completed':
            obj.refund_status = 'Completed'
            obj.save(update_fields=['refund_status', 'updated_at'])

    def ordered_products_summary(self, obj):
        items = OrderProduct.objects.filter(order=obj.order).select_related('product')
        if not items.exists():
            return '-'

        return format_html('<br>'.join(f"{item.product.product_name} x {item.quantity}" for item in items))

    ordered_products_summary.short_description = 'Ordered Products'

    def approve_returns(self, request, queryset):
        updated = queryset.update(status='Approved')
        for item in queryset:
            ReturnStatusHistory.objects.create(return_request=item, status='Approved', note='Approved by admin.')
        self.message_user(request, f'{updated} return requests were approved.', level=messages.SUCCESS)

    approve_returns.short_description = 'Approve selected returns'

    def reject_returns(self, request, queryset):
        updated = queryset.update(status='Rejected')
        for item in queryset:
            item.order.status = 'Completed'
            item.order.save(update_fields=['status', 'updated_at'])
            ReturnStatusHistory.objects.create(return_request=item, status='Rejected', note='Rejected by admin.')
        self.message_user(request, f'{updated} return requests were rejected.', level=messages.WARNING)

    reject_returns.short_description = 'Reject selected returns'

    def mark_refund_processing(self, request, queryset):
        updated = queryset.update(refund_status='Processing', status='Refund Processing')
        for item in queryset:
            ReturnStatusHistory.objects.create(return_request=item, status='Refund Processing', note='Manual COD refund processing started.')
        self.message_user(request, f'{updated} refunds moved to processing.', level=messages.SUCCESS)

    mark_refund_processing.short_description = 'Mark refund as processing'

    def mark_refund_completed(self, request, queryset):
        for item in queryset:
            item.status = 'Refund Completed'
            item.refund_status = 'Completed'
            item.save()
        self.message_user(request, 'Selected refunds marked as completed.', level=messages.SUCCESS)

    mark_refund_completed.short_description = 'Mark refund as completed'


@admin.register(Parcel)
class ParcelAdmin(NoAddDeleteAdminMixin, BaseAdmin, admin.ModelAdmin):
    change_list_template = 'admin/orders/parcel/change_list.html'

    STATUS_ALIASES = {
        'Completed': 'Preparing',
    }

    COLUMN_CONFIG = [
        {'value': 'New', 'title': 'Processing', 'tone': "#47e160"},
        {'value': 'Accepted', 'title': 'Delivered', 'tone': '#7d8fcb'},
        {'value': 'Packed', 'title': 'Collecting', 'tone': '#87b6a2'},
        {'value': 'Ready for Preparing', 'title': 'Ready for Preparing', 'tone': '#b8a47a'},
        {'value': 'Preparing', 'title': 'Preparing', 'tone': '#b38bd6'},
        {'value': 'Ready for Delivery', 'title': 'Ready for Delivery', 'tone': '#78a8d8'},
        {'value': 'On The Way', 'title': 'On the way', 'tone': '#f1a559'},
        {'value': 'Cancelled', 'title': 'Cancelled', 'tone': '#d8777d'},
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(is_ordered=True)
            .order_by('-created_at')
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:order_id>/detail/',
                self.admin_site.admin_view(self.parcel_detail_view),
                name='orders_parcel_detail',
            ),
            path(
                '<int:order_id>/set-status/',
                self.admin_site.admin_view(self.set_parcel_status),
                name='orders_parcel_set_status',
            ),
        ]
        return custom_urls + urls

    def set_parcel_status(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        new_status = request.POST.get('status')
        valid_status_values = {column['value'] for column in self.COLUMN_CONFIG} | {'Completed'}

        if request.method == 'POST' and new_status in valid_status_values:
            order.status = new_status
            order.status_updated_by = request.user if request.user.is_authenticated else None
            order.status_updated_at = timezone.now()
            order.save(update_fields=['status', 'status_updated_by', 'status_updated_at', 'updated_at'])
            self.log_change(request, order, f'Parcel status changed to "{new_status}" from board.')
            messages.success(request, f'Order {order.order_number} moved to {new_status}.')
        else:
            messages.error(request, 'Invalid status update request.')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': request.method == 'POST' and new_status in valid_status_values,
                'status': order.status,
                'status_label': self.STATUS_ALIASES.get(order.status, order.status),
                'order_id': order.id,
                'updated_by_label': self._user_display_label(order.status_updated_by),
            })

        return redirect(request.META.get('HTTP_REFERER') or reverse('admin:orders_parcel_changelist'))

    def _user_display_label(self, user):
        if not user:
            return 'System'
        full_name = f'{getattr(user, "first_name", "")} {getattr(user, "last_name", "")}'.strip()
        return full_name or getattr(user, 'email', '') or getattr(user, 'username', '') or str(user)

    def parcel_detail_view(self, request, order_id):
        order = get_object_or_404(
            Order.objects.select_related('user', 'payment'),
            pk=order_id,
            is_ordered=True,
        )
        ordered_products = list(
            OrderProduct.objects.filter(order=order).select_related('supplier', 'warehouse', 'product')
        )

        sku_rows = []
        for item in ordered_products:
            sku_rows.append({
                'id': item.id,
                'image': getattr(item.product, 'images', None),
                'name': item.product.product_name,
                'item_code': item.product.product_code,
                'qty': item.quantity,
                'weight': getattr(item.product, 'weight', None) or '-',
            })

        content_type = ContentType.objects.get_for_model(Order)
        history_entries = list(
            LogEntry.objects.filter(content_type=content_type, object_id=str(order.pk)).order_by('-action_time')[:10]
        )

        warehouse_label = '-'
        if ordered_products:
            first_warehouse = next((item.warehouse for item in ordered_products if item.warehouse), None)
            if first_warehouse:
                warehouse_label = str(first_warehouse)

        history_rows = []
        for entry in history_entries:
            try:
                history_label = entry.get_change_message()
            except Exception:
                history_label = entry.get_action_flag_display()

            history_rows.append({
                'label': history_label,
                'age': timesince(entry.action_time),
            })

        context = {
            'title': f'Parcel #{order.parcel_id or order.order_number}',
            'order': order,
            'ordered_products': ordered_products,
            'sku_rows': sku_rows,
            'history_rows': history_rows,
            'related_warehouses': list(dict.fromkeys(str(item.warehouse) for item in ordered_products if item.warehouse)),
            'related_suppliers': [item.supplier for item in ordered_products if item.supplier],
            'detail_status_label': self.STATUS_ALIASES.get(order.status, order.status),
            'detail_invoice_url': reverse('admin:orders_order_invoice', args=[order.id]),
            'detail_created_age': timesince(order.created_at),
            'warehouse_label': warehouse_label,
        }
        return TemplateResponse(request, 'admin/orders/parcel/detail.html', context)

    def changelist_view(self, request, extra_context=None):
        search_term = (request.GET.get('q') or '').strip()
        status_filter = (request.GET.get('status') or '').strip()
        warehouse_filter = (request.GET.get('warehouse') or '').strip()
        try:
            page_index = max(int(request.GET.get('p', 0)), 0)
        except (TypeError, ValueError):
            page_index = 0
        page_number = page_index + 1

        order_products = OrderProduct.objects.select_related('warehouse', 'product')
        queryset = self.get_queryset(request).select_related('user').prefetch_related(
            Prefetch('orderproduct_set', queryset=order_products)
        )

        if search_term:
            queryset = queryset.filter(
                Q(order_number__icontains=search_term)
                | Q(first_name__icontains=search_term)
                | Q(last_name__icontains=search_term)
                | Q(phone__icontains=search_term)
                | Q(email__icontains=search_term)
                | Q(address_line_1__icontains=search_term)
                | Q(address_line_2__icontains=search_term)
                | Q(zone_number__icontains=search_term)
                | Q(street_number__icontains=search_term)
                | Q(building_number__icontains=search_term)
            ).distinct()

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if warehouse_filter:
            queryset = queryset.filter(orderproduct__warehouse_id=warehouse_filter).distinct()

        status_counts = Counter(
            self.STATUS_ALIASES.get(status, status)
            for status in queryset.values_list('status', flat=True)
        )

        warehouse_choices = (
            order_products.values_list('warehouse_id', 'warehouse__name', 'warehouse__code')
            .distinct()
            .order_by('warehouse__name')
        )

        paginator = Paginator(queryset, 16)
        page_obj = paginator.get_page(page_number)
        order_cards = list(page_obj.object_list)
        total_item_count = sum(
            sum(item.quantity for item in order.orderproduct_set.all())
            for order in order_cards
        )

        columns = []
        for column in self.COLUMN_CONFIG:
            cards = []
            for order in order_cards:
                mapped_status = self.STATUS_ALIASES.get(order.status, order.status)
                if mapped_status != column['value']:
                    continue

                order_items = list(order.orderproduct_set.all())
                item_count = sum(item.quantity for item in order_items)
                warehouse_name = 'Unassigned'
                warehouse = next((item.warehouse for item in order_items if item.warehouse), None)
                if warehouse:
                    warehouse_name = warehouse.name

                cards.append({
                    'id': order.id,
                    'parcel_id': order.parcel_id,
                    'order_number': order.order_number,
                    'customer_name': order.full_name(),
                    'phone': order.phone,
                    'delivery_date_label': order.created_at.strftime('%d %b %Y'),
                    'delivery_date': order.created_at,
                    'warehouse_name': warehouse_name,
                    'item_count': item_count,
                    'since_label': timesince(order.created_at),
                    'status': mapped_status,
                    'status_tone': column['tone'],
                    'updated_by_label': self._user_display_label(order.status_updated_by),
                    'detail_url': reverse('admin:orders_parcel_detail', args=[order.id]),
                    'invoice_url': reverse('admin:orders_order_invoice', args=[order.id]),
                })

            columns.append({
                'value': column['value'],
                'title': column['title'],
                'tone': column['tone'],
                'count': status_counts.get(column['value'], 0),
                'cards': cards,
            })

        page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)
        pagination_query = request.GET.copy()
        pagination_query.pop('p', None)

        extra_context = extra_context or {}
        extra_context.update({
            'columns': columns,
            'status_choices': [column['value'] for column in self.COLUMN_CONFIG],
            'status_choice_pairs': [
                {
                    'value': column['value'],
                    'title': column['title'],
                }
                for column in self.COLUMN_CONFIG
            ],
            'search_term': search_term,
            'status_filter': status_filter,
            'warehouse_filter': warehouse_filter,
            'warehouse_choices': [
                {'id': warehouse_id, 'name': warehouse_name, 'code': warehouse_code}
                for warehouse_id, warehouse_name, warehouse_code in warehouse_choices
                if warehouse_id is not None
            ],
            'page_obj': page_obj,
            'page_range': page_range,
            'pagination_query': pagination_query.urlencode(),
            'total_parcels': queryset.count(),
            'visible_parcels': len(order_cards),
            'total_item_count': total_item_count,
            'title': 'Parcel Board',
        })
        return super().changelist_view(request, extra_context=extra_context)

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