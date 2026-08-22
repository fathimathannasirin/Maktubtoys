from django.db import models
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4
from Accounts.models import Account
from store.models import Product,Variation


# Create your models here.

class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    Payment_id = models.CharField(max_length=100)
    Payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.Payment_id

class Order(models.Model):
    STATUS =[
        ('New', 'New'),
        ('Accepted','Accepted'),
        ('Packed','Packed'),
        ('Ready for Preparing', 'Ready for Preparing'),
        ('Preparing', 'Preparing'),
        ('Ready for Delivery', 'Ready for Delivery'),
        ('On The Way','On The Way'),
        ('Delivered', 'Delivered'),
        ('Completed','Completed'),
        ('Return Requested', 'Return Requested'),
        ('Returned', 'Returned'),
        ('Refunded', 'Refunded'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]

    RETURN_REQUEST_DAYS = 14
    DELIVERED_STATUSES = {'Delivered', 'Completed'}
    BLOCKED_RETURN_STATUSES = {'Cancelled', 'Failed', 'Refunded', 'Returned', 'Return Requested'}
        
    PAYMENT_METHOD_CHOICES =(
        ('COD', 'Cash on Delivery'),
        ('PAYPAL', 'PayPal'),
    )
    
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(Payment,on_delete=models.SET_NULL, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    order_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField (max_length=50)
    phone = models.CharField(max_length=15)
    email = models.CharField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    street_number = models.CharField(max_length=50)
    building_number = models.CharField(max_length=50)
    zone_number = models.CharField(max_length=50)
    order_note = models.CharField(max_length=160, blank=True)
    order_total = models.FloatField()
    tax = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS, default='New')
    status_updated_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_updated_orders',
    )
    status_updated_at = models.DateTimeField(blank=True, null=True)
    ip = models.CharField(blank=True,max_length=20)
    is_ordered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    full_name.short_description = 'Full Name'

    @property
    def parcel_id(self):
        if not self.id:
            return ''
        return f'PCL{self.id:07d}'

    @property
    def delivered_reference(self):
        if self.delivered_at:
            return self.delivered_at
        if self.status in self.DELIVERED_STATUSES:
            return self.updated_at
        return None

    @property
    def return_window_expires_at(self):
        delivered_reference = self.delivered_reference
        if not delivered_reference:
            return None
        return delivered_reference + timedelta(days=self.RETURN_REQUEST_DAYS)

    @property
    def is_return_window_expired(self):
        expires_at = self.return_window_expires_at
        if not expires_at:
            return False
        return timezone.now() > expires_at

    @property
    def can_request_return(self):
        if self.status in self.BLOCKED_RETURN_STATUSES:
            return False
        if self.status not in self.DELIVERED_STATUSES:
            return False
        return not self.is_return_window_expired

    def save(self, *args, **kwargs):
        previous_status = None
        delivered_at_changed = False
        if self.pk:
            previous_status = Order.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        if self.status in self.DELIVERED_STATUSES and not self.delivered_at:
            self.delivered_at = timezone.now()
            delivered_at_changed = True

        if previous_status in self.DELIVERED_STATUSES and self.status not in self.DELIVERED_STATUSES and self.status not in {'Return Requested', 'Returned', 'Refunded'}:
            self.delivered_at = None
            delivered_at_changed = True

        update_fields = kwargs.get('update_fields')
        if update_fields is not None and delivered_at_changed:
            kwargs['update_fields'] = set(update_fields) | {'delivered_at'}

        super().save(*args, **kwargs)
    
class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment,on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    supplier = models.ForeignKey('warehousing.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_products')
    warehouse = models.ForeignKey('warehousing.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_products')
    variations = models.ManyToManyField(Variation,blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name


class PendingOrder(Order):
    class Meta:
        proxy = True
        verbose_name = 'Pending Order'
        verbose_name_plural = 'Pending Orders'


class PendingReturn(Order):
    class Meta:
        proxy = True
        verbose_name = 'Pending Return'
        verbose_name_plural = 'Pending Returns'


class Parcel(Order):
    class Meta:
        proxy = True
        verbose_name = 'Parcel'
        verbose_name_plural = 'Parcels'


class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('Return Requested', 'Return Requested'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Awaiting Product', 'Awaiting Product'),
        ('Product Received', 'Product Received'),
        ('Inspection Completed', 'Inspection Completed'),
        ('Refund Processing', 'Refund Processing'),
        ('Refund Completed', 'Refund Completed'),
    ]

    REFUND_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
    ]

    RESOLUTION_CHOICES = [
        ('manual_refund', 'Manual Refund'),
        ('store_credit', 'Store Credit'),
        ('replacement', 'Product Replacement'),
        ('none', 'No Resolution Yet'),
    ]

    RETURN_REASON_CHOICES = [
        ('Damaged Product', 'Damaged Product'),
        ('Wrong Product Received', 'Wrong Product Received'),
        ('Defective Product', 'Defective Product'),
        ('Quality Issue', 'Quality Issue'),
        ('Size/Variant Issue', 'Size/Variant Issue'),
        ('Other', 'Other'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='return_request')
    customer = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='return_requests')
    return_request_id = models.CharField(max_length=40, unique=True, editable=False)
    reason = models.CharField(max_length=100, choices=RETURN_REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='Return Requested')
    refund_status = models.CharField(max_length=16, choices=REFUND_STATUS_CHOICES, default='Pending')
    resolution_type = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, default='none')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_completed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    return_shipping_acknowledged = models.BooleanField(default=False)
    policy_terms_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Return Request'
        verbose_name_plural = 'Return Management'

    def __str__(self):
        return f"{self.return_request_id} - {self.order.order_number}"

    def _build_return_request_id(self):
        date_stamp = timezone.now().strftime('%Y%m%d')
        while True:
            candidate = f"RR-{date_stamp}-{uuid4().hex[:6].upper()}"
            if not ReturnRequest.objects.filter(return_request_id=candidate).exists():
                return candidate

    def save(self, *args, **kwargs):
        creating = self._state.adding
        previous_status = None
        previous_refund_status = None

        if not creating:
            previous = ReturnRequest.objects.filter(pk=self.pk).values('status', 'refund_status').first()
            if previous:
                previous_status = previous['status']
                previous_refund_status = previous['refund_status']

        if not self.return_request_id:
            self.return_request_id = self._build_return_request_id()

        if self.refund_status == 'Completed' and not self.refund_completed_at:
            self.refund_completed_at = timezone.now()

        super().save(*args, **kwargs)

        if creating:
            ReturnStatusHistory.objects.create(return_request=self, status=self.status, note='Return request created by customer.')
        elif previous_status and previous_status != self.status:
            ReturnStatusHistory.objects.create(return_request=self, status=self.status)

        if self.status == 'Refund Completed' and self.order.status != 'Refunded':
            self.order.status = 'Refunded'
            self.order.save(update_fields=['status', 'updated_at'])
        elif self.order.status != 'Return Requested' and self.status != 'Rejected':
            self.order.status = 'Return Requested'
            self.order.save(update_fields=['status', 'updated_at'])
        elif self.status == 'Rejected' and self.order.status == 'Return Requested':
            self.order.status = 'Completed'
            self.order.save(update_fields=['status', 'updated_at'])

        if not creating and previous_refund_status != self.refund_status and self.refund_status == 'Processing':
            ReturnStatusHistory.objects.create(return_request=self, status=self.status, note='Refund is being processed manually (COD order).')


class ReturnRequestImage(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='returns/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.return_request.return_request_id} image"


class ReturnStatusHistory(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='status_timeline')
    status = models.CharField(max_length=32)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.return_request.return_request_id} - {self.status}"
    