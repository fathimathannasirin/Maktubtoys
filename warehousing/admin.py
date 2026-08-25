from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .forms import PurchaseItemInlineForm
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


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'name', 'code', 'location', 'manager_name', 'manager_email', 'is_active')
    search_fields = ('name', 'code', 'location', 'manager_name', 'manager_email', 'supplier__name')
    list_filter = ('is_active', 'supplier')
    autocomplete_fields = ('supplier',)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    form = PurchaseItemInlineForm
    extra = 1
    fields = ('product_code', 'product', 'quantity', 'unit_cost', 'received_quantity')

    class Media:
        js = ('js/purchaseitem_code_sync.js',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchase_number', 'supplier', 'warehouse', 'status', 'ordered_at')
    list_filter = ('status', 'warehouse', 'supplier')
    search_fields = ('purchase_number', 'supplier__name', 'warehouse__name')
    inlines = [PurchaseItemInline]


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 1


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'supplier', 'warehouse', 'status', 'created_at')
    list_filter = ('status', 'warehouse', 'supplier')
    search_fields = ('return_number', 'supplier__name', 'warehouse__name')
    inlines = [ReturnItemInline]
