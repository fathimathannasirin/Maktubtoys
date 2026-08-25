import uuid

from django.apps import apps
from django.db import models
from django.db import transaction
from django.utils import timezone


def _adjust_product_stock(product_id, delta):
    if not delta:
        return

    with transaction.atomic():
        Product = apps.get_model('store', 'Product')
        product = Product.objects.select_for_update().get(pk=product_id)
        new_stock = product.stock + delta
        if new_stock < 0:
            new_stock = 0
        product.stock = new_stock
        product.save(update_fields=['stock'])


class Supplier(models.Model):
    name = models.CharField(max_length=150, unique=True)
    contact_person = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='warehouses', null=True, blank=True)
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True)
    location = models.CharField(max_length=255)
    manager_name = models.CharField(max_length=150, blank=True)
    manager_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Ordered', 'Ordered'),
        ('Received', 'Received'),
        ('Cancelled', 'Cancelled'),
    ]

    purchase_number = models.CharField(max_length=40, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='purchases')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    ordered_at = models.DateTimeField(default=timezone.now)
    expected_delivery = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.purchase_number

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = Purchase.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        if not self.purchase_number:
            self.purchase_number = f"PUR-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        super().save(*args, **kwargs)

        # When a purchase becomes received, push received quantities into stock once.
        if previous_status != 'Received' and self.status == 'Received':
            for item in self.items.select_related('product').all():
                received_qty = item.received_quantity or item.quantity
                _adjust_product_stock(item.product_id, received_qty)


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Product', on_delete=models.PROTECT, related_name='purchase_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    received_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('purchase', 'product')

    def __str__(self):
        return f"{self.purchase.purchase_number} - {self.product.product_name}"

    def save(self, *args, **kwargs):
        if self.product and hasattr(self.product, 'cost_price'):
            self.unit_cost = self.product.cost_price

        old_item = None
        old_received = 0
        old_product_id = None
        old_purchase_received = False

        if self.pk:
            old_item = PurchaseItem.objects.select_related('purchase').filter(pk=self.pk).first()
            if old_item:
                old_product_id = old_item.product_id
                old_received = old_item.received_quantity or old_item.quantity
                old_purchase_received = old_item.purchase.status == 'Received'

        super().save(*args, **kwargs)

        new_received = self.received_quantity or self.quantity
        new_purchase_received = self.purchase.status == 'Received'

        # Existing row reassigned to a new product while already received.
        if old_item and old_purchase_received and new_purchase_received and old_product_id != self.product_id:
            _adjust_product_stock(old_product_id, -old_received)
            _adjust_product_stock(self.product_id, new_received)
            return

        if new_purchase_received:
            if old_item and old_purchase_received:
                delta = new_received - old_received
            elif old_item and not old_purchase_received:
                delta = new_received
            else:
                delta = new_received
            _adjust_product_stock(self.product_id, delta)


class Return(models.Model):
    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
    ]

    return_number = models.CharField(max_length=40, unique=True, blank=True)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='returns')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='returns')
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.return_number

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = Return.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        if not self.return_number:
            self.return_number = f"RET-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        super().save(*args, **kwargs)

        # When a return is completed, remove quantities from stock once.
        if previous_status != 'Completed' and self.status == 'Completed':
            for item in self.items.select_related('product').all():
                _adjust_product_stock(item.product_id, -item.quantity)


class ReturnItem(models.Model):
    return_record = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Product', on_delete=models.PROTECT, related_name='return_items')
    quantity = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('return_record', 'product')

    def __str__(self):
        return f"{self.return_record.return_number} - {self.product.product_name}"

    def save(self, *args, **kwargs):
        old_item = None
        old_quantity = 0
        old_product_id = None
        old_return_completed = False

        if self.pk:
            old_item = ReturnItem.objects.select_related('return_record').filter(pk=self.pk).first()
            if old_item:
                old_product_id = old_item.product_id
                old_quantity = old_item.quantity
                old_return_completed = old_item.return_record.status == 'Completed'

        super().save(*args, **kwargs)

        new_return_completed = self.return_record.status == 'Completed'

        # Existing row reassigned to a new product while already completed.
        if old_item and old_return_completed and new_return_completed and old_product_id != self.product_id:
            _adjust_product_stock(old_product_id, old_quantity)
            _adjust_product_stock(self.product_id, -self.quantity)
            return

        if new_return_completed:
            if old_item and old_return_completed:
                delta = self.quantity - old_quantity
            elif old_item and not old_return_completed:
                delta = self.quantity
            else:
                delta = self.quantity

            _adjust_product_stock(self.product_id, -delta)
