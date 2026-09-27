from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.files.storage import default_storage
from django.test import TestCase
from django.utils import timezone

from carts.models import CartItem
from category.models import Category
from store.delivery import cart_delivery_charge, get_delivery_estimate
from store.models import Product
from warehousing.models import Warehouse


class ProductBarcodeTests(TestCase):
	def test_generate_barcode_creates_a_png_image(self):
		category = Category.objects.create(category_name='Barcode Test', slug='barcode-test')
		product = Product.objects.create(
			product_name='Barcode Product',
			slug='barcode-product',
			price=10,
			images='photos/products/test.png',
			stock=1,
			category=category,
			sku='SKU-001',
		)

		self.assertTrue(product.generate_barcode())
		product.save(update_fields=['barcode_image'])

		self.assertTrue(product.barcode_image.name.endswith('.png'))
		self.assertTrue(default_storage.exists(product.barcode_image.name))


class DeliveryRulesTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(category_name='Delivery Test', slug='delivery-test')
		self.own = Warehouse.objects.get(code='OWN')
		self.supplier_wh = Warehouse.objects.create(
			name='Supplier WH',
			code='SUP-DEL',
			location='Doha',
			delivery_days=4,
		)

	def _product(self, name, warehouse):
		return Product.objects.create(
			product_name=name,
			slug=name.lower().replace(' ', '-'),
			price=Decimal('10.00'),
			images='photos/products/test.png',
			stock=5,
			category=self.category,
			warehouse=warehouse,
		)

	def test_own_warehouse_is_charged_and_supplier_is_free(self):
		own_item = CartItem(product=self._product('Own Item', self.own), quantity=1)
		supplier_item = CartItem(product=self._product('Supplier Item', self.supplier_wh), quantity=1)
		self.assertEqual(cart_delivery_charge([own_item]), Decimal('20.00'))
		self.assertEqual(cart_delivery_charge([supplier_item]), Decimal('0'))
		self.assertEqual(cart_delivery_charge([own_item, supplier_item]), Decimal('20.00'))

	def test_supplier_delivery_uses_admin_days(self):
		product = self._product('Supplier Days', self.supplier_wh)
		estimate = get_delivery_estimate(product)
		self.assertTrue(estimate['is_free'])
		self.assertEqual(estimate['delivery_days'], 4)

	def test_own_warehouse_same_day_before_cutoff(self):
		today = timezone.localdate()
		before = timezone.make_aware(datetime.combine(today, time(18, 0)))
		after = timezone.make_aware(datetime.combine(today, time(19, 30)))
		self.assertEqual(self.own.get_delivery_date(before), today)
		self.assertEqual(self.own.get_delivery_date(after), today + timedelta(days=1))
		self.assertEqual(self.supplier_wh.get_delivery_date(after), today + timedelta(days=4))
