from django.db import models
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
        ('On The Way','On The Way'),
        ('Completed','Completed'),
        ('Cancelled', 'Cancelled'),
    ]
        
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
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True,max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    full_name.short_description = 'Full Name'
    
class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment,on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation,blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name
    