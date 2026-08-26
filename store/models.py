from django.db import models
from category.models import Category
from django.urls import reverse
from Accounts.models import Account
from django.db.models import Avg,Count

class Product(models.Model):
    product_name = models.CharField(max_length=200,unique=True)
    slug = models.SlugField(max_length=200,unique=True)
    description = models.TextField(max_length=1000,blank=True)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    images = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)
    supplier = models.ForeignKey('warehousing.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    warehouse = models.ForeignKey('warehousing.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    product_code = models.CharField(max_length=20, unique=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    margin_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name
    
    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg
    
    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = float(reviews['count'])
        return count
    
    def calculate_margin(self):
        """Calculate margin amount and percentage based on cost_price and selling price"""
        if self.cost_price and self.price:
            self.margin_amount = self.price - self.cost_price
            if self.price > 0:
                self.margin_percentage = (self.margin_amount / self.price) * 100
        return self.margin_amount, self.margin_percentage
    
    def save(self, *args, **kwargs):
        if not self.product_code:
            last_product = Product.objects.order_by('-id').first()

            if last_product and last_product.product_code:
                last_code = int(last_product.product_code.split('PD')[-1])
                new_code = last_code + 1
            else:
                new_code = 1

            self.product_code = f"GM/PD{new_code:04d}"
        
        # Auto-calculate margins
        self.calculate_margin()

        # Automatically set is_available tick if stock is more than 0
        if self.stock is not None:
            self.is_available = self.stock > 0

        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            update_fields = set(update_fields)
            if 'stock' in update_fields:
                update_fields.add('is_available')
            kwargs['update_fields'] = list(update_fields)

        super(Product, self).save(*args, **kwargs)

class VariationManager(models.Manager):
    def colors(self):
        # Use __name to look inside the VariationCategory model
        return super(VariationManager, self).filter(variation_category__name__iexact='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category__name__iexact='size', is_active=True)

class VariationCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Variation Category'
        verbose_name_plural = 'Variation Categories'

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # Change 'choices' to a ForeignKey to the new model
    variation_category = models.ForeignKey(VariationCategory, on_delete=models.CASCADE)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)
    is_multi_select = models.BooleanField(default=False)
    selection_limit = models.PositiveIntegerField(default=1)

    objects = VariationManager()

    def __str__(self):
        return f"{self.variation_category.name} : {self.variation_value}"
    
class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=1000, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject
        
class ProductGallery(models.Model):
    product = models.ForeignKey(Product,default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=500)

    def __str__(self):
        return self.product.product_name
    
    class Meta:
        verbose_name ='productgallery'
        verbose_name_plural ='product gallery'