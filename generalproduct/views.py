from django.shortcuts import render,redirect
from django.http import HttpResponse
from store.models import Category,Product,ReviewRating
 
def home(request):
    products = Product.objects.filter(is_available=True).order_by('created_date')
    categories = Category.objects.filter()

    for product in products: 
        reviews = ReviewRating.objects.filter(product_id=product, status=True).select_related('user')

    context = {
        'products': products,
        'categories': categories,
        'reviews': reviews,
    }
    return render(request, 'index.html', context)
