from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.html import format_html
from django.urls import path, reverse
from store.models import Product
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as ReportLabImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import PurchaseItemInlineForm, ReturnItemInlineForm
from .models import Purchase, PurchaseItem, Return, ReturnItem, Supplier, Warehouse


class WarehouseInline(admin.TabularInline):
    model = Warehouse
    extra = 1
    fields = ('name', 'code', 'location', 'manager_name', 'manager_email', 'is_active')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'is_active')
    search_fields = ('name', 'contact_person', 'email', 'phone')
    list_filter = ('is_active',)
    inlines = [WarehouseInline]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        supplier = get_object_or_404(Supplier, pk=object_id)

        # 1. Related Products (SKUs)
        extra_context['related_products'] = Product.objects.filter(supplier=supplier)

        # 2. Related Purchase Orders
        extra_context['related_purchases'] = Purchase.objects.filter(supplier=supplier)

        # 3. Related Purchase Returns
        extra_context['related_returns'] = Return.objects.filter(supplier=supplier)

        return super().change_view(request, object_id, form_url, extra_context=extra_context)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'name', 'code', 'location', 'manager_name', 'manager_email', 'is_active')
    search_fields = ('name', 'code', 'location', 'manager_name', 'manager_email', 'supplier__name')
    list_filter = ('is_active', 'supplier')
    autocomplete_fields = ('supplier',)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        warehouse = get_object_or_404(Warehouse, pk=object_id)

        # 1. Related Products in this Warehouse
        extra_context['related_products'] = Product.objects.filter(warehouse=warehouse)

        # 2. Related Purchase Orders
        extra_context['related_purchases'] = Purchase.objects.filter(warehouse=warehouse)

        # 3. Related Purchase Returns
        extra_context['related_returns'] = Return.objects.filter(warehouse=warehouse)

        return super().change_view(request, object_id, form_url, extra_context=extra_context)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    form = PurchaseItemInlineForm
    extra = 1
    fields = ('product_code', 'product', 'old_upc', 'quantity', 'unit_cost', 'received_quantity')

    class Media:
        js = ('js/purchaseitem_code_sync.js',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchase_number', 'supplier', 'warehouse', 'status', 'ordered_at', 'purchase_order_links')
    list_filter = ('status', 'warehouse', 'supplier')
    search_fields = ('purchase_number', 'supplier__name', 'warehouse__name')
    inlines = [PurchaseItemInline]
    fields = (
        'purchase_number', 'document_type', 'supplier', 'warehouse', 'status', 'ordered_at', 'expected_delivery',
        'storekeeper', 'agreement', 'adjustment', 'reference_number', 'vat_rate', 'notes',
    )
    readonly_fields = ('document_type',)

    def get_urls(self):
        urls = super().get_urls()
        purchase_urls = [
            path('<int:object_id>/purchase-order/print/', self.admin_site.admin_view(self.print_purchase_order), name='warehousing_purchase_print'),
        ]
        return purchase_urls + urls

    def purchase_order_links(self, obj):
        print_url = reverse('admin:warehousing_purchase_print', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Print</a>', print_url)

    purchase_order_links.short_description = 'Purchase order'

    def _purchase_order_context(self, object_id):
        purchase = get_object_or_404(
            Purchase.objects.select_related('supplier', 'warehouse').prefetch_related('items__product'),
            pk=object_id,
        )
        items = list(purchase.items.all())
        for item in items:
            item.line_total = item.quantity * item.unit_cost
        subtotal = sum((item.line_total for item in items), start=0)
        total_vat = subtotal * purchase.vat_rate / 100
        return {
            'purchase': purchase,
            'items': items,
            'subtotal': subtotal,
            'total_vat': total_vat,
            'total': subtotal + total_vat,
            'total_quantity': sum(item.quantity for item in items),
        }

    def print_purchase_order(self, request, object_id):
        return render(request, 'admin/warehousing/purchase_order_print.html', self._purchase_order_context(object_id))

    def purchase_order_pdf(self, request, object_id):
        context = self._purchase_order_context(object_id)
        purchase = context['purchase']
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{purchase.purchase_number}.pdf"'

        document = SimpleDocTemplate(response, pagesize=A4, rightMargin=10 * mm, leftMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
        styles = getSampleStyleSheet()
        logo_path = settings.BASE_DIR / 'static' / 'images' / 'maktub_h60.png'
        brand_header = [Paragraph('<b>MAKTUB Toys</b><br/>Warehousing Document', styles['Title'])]
        if logo_path.exists():
            brand_header.insert(0, ReportLabImage(str(logo_path), width=55 * mm, height=12 * mm))
        document_header = [[brand_header, Paragraph(
            f'<para align="right"><b>ID:</b> {purchase.purchase_number}<br/>'
            f'<b>Warehouse:</b> {purchase.warehouse.name}<br/>'
            f'<b>Supplier:</b> {purchase.supplier.name}<br/>'
            f'<b>Status:</b> {purchase.status}<br/>'
            f'<b>Type:</b> INBOUND<br/>'
            f'<b>Date:</b> {purchase.ordered_at:%d %B %Y}<br/>'
            f'<b>Time:</b> {purchase.ordered_at:%H:%M}</para>',
            styles['Normal'],
        )]]
        header_table = Table(document_header, colWidths=[105 * mm, 85 * mm])
        header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        story = [
            header_table,
            Spacer(1, 3 * mm),
            Paragraph(purchase.status.upper(), styles['Title']),
            Spacer(1, 3 * mm),
        ]
        rows = [['#', 'Image', 'Product', 'UPC', 'SKU', 'Item Number', 'Count', 'Cost', 'Total']]
        for item in context['items']:
            product_image = '-'
            if item.product.images and hasattr(item.product.images, 'path'):
                image_path = item.product.images.path
                if image_path and __import__('os').path.exists(image_path):
                    product_image = ReportLabImage(image_path, width=14 * mm, height=14 * mm)
            rows.append([
                str(len(rows)), product_image, item.product.product_name, item.product.upc or '-',
                item.product.sku or '-', item.product.product_code, str(item.quantity),
                f'{item.unit_cost:.2f}', f'{item.line_total:.2f}',
            ])
        table = Table(rows, colWidths=[7 * mm, 18 * mm, 42 * mm, 24 * mm, 22 * mm, 25 * mm, 14 * mm, 18 * mm, 20 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#481616')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (5, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(table)
        story.append(Spacer(1, 5 * mm))
        signature_table = Table([
            [Paragraph('Storekeeper Signature:', styles['Normal']), Paragraph('<b>Purchase Summary</b>', styles['Normal'])],
            ['', f'Inbound Purchase Order: {purchase.purchase_number}'],
            [Paragraph('Store Manager Signature:', styles['Normal']), f'<b>Status:</b> {purchase.status}'],
            ['', f'<b>Total Count:</b> {context["total_quantity"]}'],
            ['', f'<b>Total Value:</b> {context["total"]:.2f} QAR'],
        ], colWidths=[95 * mm, 95 * mm], rowHeights=[10 * mm, 25 * mm, 10 * mm, 25 * mm, 10 * mm])
        signature_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 1), colors.HexColor('#f3f3f3')),
            ('BACKGROUND', (0, 2), (0, 3), colors.HexColor('#f3f3f3')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f3f3f3')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.white),
            ('INNERGRID', (0, 0), (-1, -1), 3, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(signature_table)
        if purchase.notes:
            story.extend([Spacer(1, 5 * mm), Paragraph(f'<b>Notes:</b> {purchase.notes}', styles['Normal'])])
        document.build(story)
        return response

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        if form.instance.status == 'Received':
            for item in form.instance.items.all():
                item.save()


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    form = ReturnItemInlineForm
    extra = 1
    fields = ('product_code', 'product', 'old_upc', 'quantity', 'unit_cost', 'notes')

    class Media:
        js = ('js/returnitem_code_sync.js',)


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'document_type', 'supplier', 'warehouse', 'status', 'created_at', 'return_document_links')
    list_filter = ('status', 'warehouse', 'supplier')
    search_fields = ('return_number', 'supplier__name', 'warehouse__name')
    inlines = [ReturnItemInline]
    fields = (
        'return_number', 'document_type', 'purchase', 'supplier', 'warehouse', 'status', 'reason',
        'storekeeper', 'agreement', 'adjustment', 'reference_number', 'vat_rate',
    )
    readonly_fields = ('document_type',)

    def get_urls(self):
        urls = super().get_urls()
        return_urls = [
            path('<int:object_id>/return-document/print/', self.admin_site.admin_view(self.print_return_document), name='warehousing_return_print'),
        ]
        return return_urls + urls

    def return_document_links(self, obj):
        print_url = reverse('admin:warehousing_return_print', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Print</a>', print_url)

    return_document_links.short_description = 'Return document'

    def _return_document_context(self, object_id):
        return_record = get_object_or_404(
            Return.objects.select_related('purchase', 'supplier', 'warehouse').prefetch_related('items__product'),
            pk=object_id,
        )
        items = list(return_record.items.all())
        for item in items:
            item.line_total = item.quantity * item.unit_cost
        subtotal = sum((item.line_total for item in items), start=0)
        total_vat = subtotal * return_record.vat_rate / 100
        return {
            'return_record': return_record,
            'items': items,
            'subtotal': subtotal,
            'total_vat': total_vat,
            'total': subtotal + total_vat,
            'total_quantity': sum(item.quantity for item in items),
        }

    def print_return_document(self, request, object_id):
        return render(request, 'admin/warehousing/purchase_return_print.html', self._return_document_context(object_id))

    def return_document_pdf(self, request, object_id):
        context = self._return_document_context(object_id)
        return_record = context['return_record']
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{return_record.return_number}.pdf"'
        document = SimpleDocTemplate(response, pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
        styles = getSampleStyleSheet()
        story = [
            Paragraph('MAKTUB Toys - Purchase Return', styles['Title']),
            Paragraph(f'<b>Return ID:</b> {return_record.return_number}', styles['Normal']),
            Paragraph(f'<b>Type:</b> {return_record.document_type}', styles['Normal']),
            Paragraph(f'<b>Supplier:</b> {return_record.supplier.name}', styles['Normal']),
            Paragraph(f'<b>Warehouse:</b> {return_record.warehouse.name}', styles['Normal']),
            Spacer(1, 5 * mm),
        ]
        rows = [['Product', 'UPC', 'SKU', 'Count', 'Unit Cost', 'Final']]
        for item in context['items']:
            rows.append([item.product.product_name, item.product.upc or '-', item.product.sku or '-', str(item.quantity), f'{item.unit_cost:.2f}', f'{item.line_total:.2f}'])
        rows.append(['', '', '', '', 'Total', f'{context["total"]:.2f} QAR'])
        table = Table(rows, colWidths=[65 * mm, 30 * mm, 30 * mm, 20 * mm, 25 * mm, 30 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#481616')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f3f3')),
            ('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(table)
        if return_record.reason:
            story.extend([Spacer(1, 5 * mm), Paragraph(f'<b>Reason:</b> {return_record.reason}', styles['Normal'])])
        document.build(story)
        return response

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        if form.instance.status == 'Completed':
            for item in form.instance.items.all():
                item.save()