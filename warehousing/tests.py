from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from category.models import Category
from store.models import Product
from .models import Supplier, Warehouse
from .models import Purchase, PurchaseItem, Return, ReturnItem


class WarehouseSupplierRelationTests(TestCase):
    def test_warehouse_can_be_created_under_supplier(self):
        supplier = Supplier.objects.create(name='Test Supplier')
        warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH-001',
            location='Nairobi',
            supplier=supplier,
        )

        self.assertEqual(warehouse.supplier, supplier)
        self.assertIn(warehouse, supplier.warehouses.all())


class PurchaseOrderDocumentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            'Admin', 'User', 'admin@example.com', 'admin', 'password'
        )
        category = Category.objects.create(category_name='PO Test', slug='po-test')
        product = Product.objects.create(
            product_name='PO Product', slug='po-product', price=Decimal('20.00'),
            images='photos/products/test.png', stock=1, category=category,
        )
        supplier = Supplier.objects.create(name='PO Supplier')
        warehouse = Warehouse.objects.create(name='PO Warehouse', code='PO-WH', location='Doha')
        self.purchase = Purchase.objects.create(supplier=supplier, warehouse=warehouse)
        PurchaseItem.objects.create(purchase=self.purchase, product=product, quantity=2, unit_cost=Decimal('12.50'))
        self.client.force_login(self.user)

    def test_purchase_order_print_and_pdf_are_available(self):
        print_response = self.client.get(reverse('admin:warehousing_purchase_print', args=[self.purchase.pk]))
        pdf_response = self.client.get(reverse('admin:warehousing_purchase_pdf', args=[self.purchase.pk]))

        self.assertContains(print_response, self.purchase.purchase_number)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')
        self.assertIn(self.purchase.purchase_number, pdf_response['Content-Disposition'])

    def test_purchase_return_print_and_pdf_are_available(self):
        return_record = Return.objects.create(
            purchase=self.purchase,
            supplier=self.purchase.supplier,
            warehouse=self.purchase.warehouse,
            storekeeper='Admin User',
        )
        product = self.purchase.items.get().product
        ReturnItem.objects.create(return_record=return_record, product=product, quantity=1, unit_cost=Decimal('12.50'))

        print_response = self.client.get(reverse('admin:warehousing_return_print', args=[return_record.pk]))
        pdf_response = self.client.get(reverse('admin:warehousing_return_pdf', args=[return_record.pk]))

        self.assertContains(print_response, 'OUTBOUND')
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')
        self.assertIn(return_record.return_number, pdf_response['Content-Disposition'])
