from django.core.files.storage import default_storage
from django.test import TestCase

from category.models import Category
from store.models import Product


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
