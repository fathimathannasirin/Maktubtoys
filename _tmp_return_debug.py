import os
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generalproduct.settings')

import django

django.setup()

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from Accounts.models import Account
from orders.models import Order, ReturnRequest

Account.objects.filter(email='return-debug@example.com').delete()
user = Account.objects.create_user(
    first_name='Return',
    last_name='Customer',
    username='returncustomerdebug',
    email='return-debug@example.com',
    password='StrongPass123',
)
user.is_active = True
user.save(update_fields=['is_active'])

order = Order.objects.create(
    user=user,
    order_number='RETDBG123',
    first_name='Return',
    last_name='Customer',
    phone='+97412345678',
    email='return-debug@example.com',
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

client = Client()
client.force_login(user)
payload = {
    'reason': 'Damaged Product',
    'description': 'The product arrived damaged.',
    'return_shipping_acknowledged': 'on',
    'policy_terms_accepted': 'on',
}
response = client.post(reverse('return_request', args=[order.id]), payload, follow=True)
print('status=', response.status_code)
print('redirect_chain=', response.redirect_chain)
print('path=', response.request.get('PATH_INFO'))
print('templates=', [template.name for template in response.templates if template.name])
print('context_keys=', list(response.context.keys()) if response.context else None)
print('return_requests=', ReturnRequest.objects.filter(order=order).count())
print('content_snippet=', response.content[:500])
