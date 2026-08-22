from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.translation import override
from django.utils import timezone
from datetime import timedelta

from Accounts.models import Account
from carts.models import CartItem
from category.models import Category
from store.models import Product

from .forms import OrderForm
from .models import Order, OrderProduct, ReturnRequest


class OrderPhoneValidationTests(TestCase):
	def _valid_payload(self, phone):
		return {
			'first_name': 'Order',
			'last_name': 'User',
			'phone': phone,
			'email': 'order@example.com',
			'address_line_1': 'Doha Street',
			'address_line_2': '',
			'street_number': '10',
			'building_number': '22',
			'zone_number': '55',
			'order_note': '',
		}

	def test_order_form_accepts_local_eight_digit_phone(self):
		form = OrderForm(data=self._valid_payload('12345678'))

		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data['phone'], '+97412345678')

	def test_order_form_accepts_formatted_qatar_phone(self):
		form = OrderForm(data=self._valid_payload('+974-1234-5678'))

		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data['phone'], '+97412345678')

	def test_order_form_rejects_non_eight_digit_phone(self):
		form = OrderForm(data=self._valid_payload('12345'))

		self.assertFalse(form.is_valid())
		self.assertIn('phone', form.errors)


class PlaceOrderFlowTests(TestCase):
	def setUp(self):
		self.user = Account.objects.create_user(
			first_name='Flow',
			last_name='User',
			username='flowuser',
			email='flow@example.com',
			password='StrongPass123',
		)
		self.user.is_active = True
		self.user.save(update_fields=['is_active'])

		category = Category.objects.create(category_name='Cat', slug='cat')
		image = SimpleUploadedFile('p.jpg', b'filecontent', content_type='image/jpeg')
		self.product = Product.objects.create(
			product_name='Flow Product',
			slug='flow-product',
			price=100,
			images=image,
			stock=10,
			category=category,
		)

		CartItem.objects.create(user=self.user, product=self.product, quantity=1, is_active=True)

	def test_place_order_redirects_to_complete_and_saves_order(self):
		self.client.force_login(self.user)

		payload = {
			'first_name': 'Flow',
			'last_name': 'User',
			'phone': '12345678',
			'email': 'flow@example.com',
			'address_line_1': 'Doha Street',
			'address_line_2': '',
			'street_number': '10',
			'building_number': '22',
			'zone_number': '55',
			'order_note': '',
		}

		with override('en'):
			response = self.client.post(reverse('place_order'), payload)

		self.assertEqual(response.status_code, 302)
		self.assertIn('/orders/order_complete/?order_number=', response.url)

		order = Order.objects.get(user=self.user)
		self.assertEqual(order.phone, '+97412345678')
		self.assertTrue(order.order_number)
		self.assertTrue(order.is_ordered)

		self.assertEqual(OrderProduct.objects.filter(order=order).count(), 1)
		self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)


class ReturnRequestFlowTests(TestCase):
	def setUp(self):
		self.user = Account.objects.create_user(
			first_name='Return',
			last_name='Customer',
			username='returncustomer',
			email='return@example.com',
			password='StrongPass123',
		)
		self.user.is_active = True
		self.user.save(update_fields=['is_active'])

		self.order = Order.objects.create(
			user=self.user,
			order_number='RET12345',
			first_name='Return',
			last_name='Customer',
			phone='+97412345678',
			email='return@example.com',
			address_line_1='Doha',
			address_line_2='',
			street_number='10',
			building_number='22',
			zone_number='55',
			order_note='',
			order_total=100,
			tax=2,
			status='Completed',
			is_ordered=True,
			delivered_at=timezone.now() - timedelta(days=2),
		)

	def test_customer_can_submit_return_request_within_window(self):
		self.client.force_login(self.user)

		payload = {
			'reason': 'Damaged Product',
			'description': 'The product arrived damaged.',
			'return_shipping_acknowledged': 'on',
			'policy_terms_accepted': 'on',
		}

		response = self.client.post(reverse('return_request', args=[self.order.id]), payload, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(ReturnRequest.objects.filter(order=self.order).count(), 1)

		self.order.refresh_from_db()
		self.assertEqual(self.order.status, 'Return Requested')

	def test_return_request_blocked_when_window_expired(self):
		self.client.force_login(self.user)
		self.order.delivered_at = timezone.now() - timedelta(days=20)
		self.order.save(update_fields=['delivered_at'])

		payload = {
			'reason': 'Defective Product',
			'description': 'Late return request should fail.',
			'return_shipping_acknowledged': 'on',
			'policy_terms_accepted': 'on',
		}

		response = self.client.post(reverse('return_request', args=[self.order.id]), payload, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(ReturnRequest.objects.filter(order=self.order).count(), 0)

	def test_duplicate_return_request_is_not_allowed(self):
		self.client.force_login(self.user)
		ReturnRequest.objects.create(
			order=self.order,
			customer=self.user,
			reason='Other',
			description='Existing request',
			return_shipping_acknowledged=True,
			policy_terms_accepted=True,
		)

		payload = {
			'reason': 'Wrong Product Received',
			'description': 'Trying to submit duplicate.',
			'return_shipping_acknowledged': 'on',
			'policy_terms_accepted': 'on',
		}

		response = self.client.post(reverse('return_request', args=[self.order.id]), payload, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(ReturnRequest.objects.filter(order=self.order).count(), 1)
