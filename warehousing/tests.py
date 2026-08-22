from django.test import TestCase

from .models import Supplier, Warehouse


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
