from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from store.models import Product
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.http import HttpResponse
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from store.models import ReviewRating,ProductGallery
from store.forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from django.views.decorators.csrf import csrf_exempt


# views.py

def store(request, category_slug=None):
    categories = None
    products = None

    # Base Category Filtering (Your existing logic)
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        subcategories = categories.children.all()
        if subcategories.exists():
            products = Product.objects.filter(category__in=subcategories, is_available=True)
        else:
            products = Product.objects.filter(category=categories, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)

    # --- SIDEBAR FILTERS (Safe from Global Search) ---
    
    # 1. "Search Within Results" (Specific to the current page view)
    inner_keyword = request.GET.get('inner_keyword') # We use a unique name here
    if inner_keyword:
        products = products.filter(
            Q(description__icontains=inner_keyword) | 
            Q(product_name__icontains=inner_keyword)
        )

    # 2. Price Range Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # 3. Sorting Logic
    sort = request.GET.get('sort')
    if sort == 'latest':
        products = products.order_by('-created_date')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('id') # Default order

    product_count = products.count()
    
    # Pagination
    paginator = Paginator(products, 15)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = {
        'products': paged_products,
        'product_count': product_count,
        'all_categories': Category.objects.filter(parent=None),
    }
    return render(request, 'store/store.html', context)

from django.shortcuts import render, get_object_or_404

def product_detail(request, category_slug, product_slug):
    try:
    # This automatically handles the "DoesNotExist" error for you
        single_product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e
    
    if request.user.is_authenticated: 
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None


    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True).select_related('user')

    #product gallery

    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)


    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct' : orderproduct,
        'reviews' : reviews,
        'product_gallery' : product_gallery,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    products = Product.objects.none()
    product_count = 0
    
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            # 1. Get the base search results
            products = Product.objects.filter(
                Q(description__icontains=keyword) | 
                Q(product_name__icontains=keyword) | 
                Q(product_name_ar__icontains=keyword) | 
                Q(category__category_name__icontains=keyword) | 
                Q(product_code__icontains=keyword),
                is_available=True
            )

            # 2. Add sorting logic here (missing in your current code)
            sort = request.GET.get('sort')
            if sort == 'latest':
                products = products.order_by('-created_date')
            elif sort == 'price_low':
                products = products.order_by('price')
            elif sort == 'price_high':
                products = products.order_by('-price')
            else:
                products = products.order_by('-id')

            product_count = products.count()
            
            # 3. Pagination
            paginator = Paginator(products, 12) 
            page = request.GET.get('page')
            products = paginator.get_page(page)

    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thankyou! your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thankyou! your review has been submitted.')
                return redirect(url)
            
@csrf_exempt 
def check_unique(request):
    field = request.GET.get('field')
    value = request.GET.get('value')
    product_id = request.GET.get('product_id')

    # Ensure we have data to check
    if not field or not value:
        return JsonResponse({'exists': False})

    try:
        exists = False
        if field == 'product_name':
            qs = Product.objects.filter(product_name__iexact=value.strip())
            # If we are editing, ignore the current product's ID
            if product_id and product_id.isdigit():
                qs = qs.exclude(id=int(product_id))
            exists = qs.exists()
            
        elif field == 'product_code':
            qs = Product.objects.filter(product_code__iexact=value.strip())
            if product_id and product_id.isdigit():
                qs = qs.exclude(id=int(product_id))
            exists = qs.exists()

        return JsonResponse({'exists': exists})
    except Exception as e:
        # This prevents the 500 error and tells you what went wrong in your terminal
        print(f"Error in check_unique: {e}")
        return JsonResponse({'error': str(e)}, status=400)
    
def get_product_price(request):
    product_id = request.GET.get('product_id')
    try:
        product = Product.objects.get(id=product_id)
        # Verify if your field is 'price' or 'product_price' in store/models.py
        return JsonResponse({'price': float(product.price)}) 
    except:
        return JsonResponse({'price': 0}, status=404)
    
def get_product_data(request):
    product_id = request.GET.get('product_id')
    try:
        product = Product.objects.get(id=product_id)
        # Check if this specific product has variations defined
        has_variations = product.variation_set.exists() 
        
        return JsonResponse({
            'price': float(product.price),
            'has_variations': has_variations
        })
    except (Product.DoesNotExist, ValueError):
        return JsonResponse({'price': 0, 'has_variations': False})