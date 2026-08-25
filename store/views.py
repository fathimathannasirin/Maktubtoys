import re
from urllib.parse import urlencode

from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from django.urls import reverse
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
WORD_TO_NUM = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
}

def _convert_words_to_numbers(text):
    """'five years' -> '5 years' എന്ന രീതിയിലേക്ക് മാറ്റാൻ"""
    for word, num in WORD_TO_NUM.items():
        text = re.sub(rf'\b{word}\b', str(num), text, flags=re.IGNORECASE)
    return text

def _parse_age_search(keyword):
    if not keyword:
        return {}, ''

    cleaned_keyword = _convert_words_to_numbers(keyword.strip().lower())
    age_filters = {}
    year_unit_pattern = r'(?:years?|yrs?|yr|y)'

    range_match = re.search(rf'(\d+)\s*(?:-|to)\s*(\d+)\s*{year_unit_pattern}?', cleaned_keyword)
    if range_match:
        min_age = int(range_match.group(1))
        max_age = int(range_match.group(2))
        if min_age > max_age:
            min_age, max_age = max_age, min_age
        age_filters['min_age'] = min_age
        age_filters['max_age'] = max_age
        cleaned_keyword = cleaned_keyword.replace(range_match.group(0), ' ')

    if not age_filters:
        under_match = re.search(rf'(?:under|below|less than|upto|up to)\s*(\d+)\s*{year_unit_pattern}?', cleaned_keyword)
        if under_match:
            age_filters['age_mode'] = 'under'
            age_filters['age_value'] = int(under_match.group(1))
            cleaned_keyword = cleaned_keyword.replace(under_match.group(0), ' ')

    if not age_filters:
        above_match = re.search(rf'(?:above|over|older than|more than)\s*(\d+)\s*{year_unit_pattern}?', cleaned_keyword)
        if above_match:
            age_filters['age_mode'] = 'above'
            age_filters['age_value'] = int(above_match.group(1))
            cleaned_keyword = cleaned_keyword.replace(above_match.group(0), ' ')

    if not age_filters:
        exact_match = re.search(rf'(?:age\s*)?(\d+)\s*(?:{year_unit_pattern}(?:\s*old)?|\b)', cleaned_keyword)
        if exact_match:
            age_filters['age'] = int(exact_match.group(1))
            cleaned_keyword = cleaned_keyword.replace(exact_match.group(0), ' ')
        elif re.fullmatch(r'\d+', cleaned_keyword):
            age_filters['age'] = int(cleaned_keyword)
            cleaned_keyword = ''

    cleaned_keyword = re.sub(r'\s+', ' ', cleaned_keyword).strip()
    return age_filters, cleaned_keyword


def _querystring_without(querydict, *keys):
    updated_query = querydict.copy()
    for key in keys:
        updated_query.pop(key, None)
    return updated_query.urlencode()

def store(request, category_slug=None):
    categories = None
    selected_category = None
    selected_age = None
    selected_age_mode = None
    
    # 1. Start with base available products QuerySet
    products = Product.objects.filter(is_available=True)

    # 2. Category Filtering (Handles both URL path parameter & GET request parameter)
    category_param = category_slug or request.GET.get('category')
    
    if category_param:
        categories = get_object_or_404(Category, slug=category_param)
        selected_category = categories
        subcategories = categories.children.all()
        
        # Check if category has subcategories and filter accordingly
        if subcategories.exists():
            products = products.filter(category__in=subcategories)
        else:
            products = products.filter(category=categories)

    # 3. Age Filtering
    age_value = request.GET.get('age')
    age_mode = request.GET.get('age_mode')
    age_limit = request.GET.get('age_value')
    min_age = request.GET.get('min_age')
    max_age = request.GET.get('max_age')

    if age_value:
        try:
            selected_age = int(age_value)
        except (TypeError, ValueError):
            selected_age = None
        else:
            products = products.filter(age=selected_age)
            selected_age_mode = 'exact'
    elif age_mode == 'under' and age_limit:
        try:
            selected_age = int(age_limit)
        except (TypeError, ValueError):
            selected_age = None
        else:
            products = products.filter(age__lt=selected_age)
            selected_age_mode = 'under'
    elif age_mode == 'above' and age_limit:
        try:
            selected_age = int(age_limit)
        except (TypeError, ValueError):
            selected_age = None
        else:
            products = products.filter(age__gt=selected_age)
            selected_age_mode = 'above'
    elif min_age and max_age:
        try:
            min_age_value = int(min_age)
            max_age_value = int(max_age)
        except (TypeError, ValueError):
            min_age_value = None
            max_age_value = None
        else:
            if min_age_value > max_age_value:
                min_age_value, max_age_value = max_age_value, min_age_value
            products = products.filter(age__gte=min_age_value, age__lte=max_age_value)
            selected_age = (min_age_value, max_age_value)
            selected_age_mode = 'range'

    # 4. "Search Within Results" Sidebar Filter
    inner_keyword = request.GET.get('inner_keyword')
    products_before_keyword = products
    if inner_keyword:
        keyword_filtered_products = products.filter(
            Q(description__icontains=inner_keyword) | 
            Q(product_name__icontains=inner_keyword)
        )
        if keyword_filtered_products.exists() or selected_age_mode is None:
            products = keyword_filtered_products
        else:
            products = products_before_keyword

    # 5. Price Range Filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # 6. Sorting Logic
    sort = request.GET.get('sort')
    if sort == 'latest':
        products = products.order_by('-created_date')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('id')  # Default ordering

    # Total product count before pagination
    product_count = products.count()

    # 7. Pagination Logic (15 items per page)
    paginator = Paginator(products, 15)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Context values sent to Template
    context = {
        'products': paged_products,
        'product_count': product_count,
        'all_categories': Category.objects.filter(parent=None),
        'selected_category': selected_category,
        'selected_age': selected_age,
        'selected_age_mode': selected_age_mode,
        'sort_querystring': _querystring_without(request.GET, 'sort', 'page'),
        'page_querystring': _querystring_without(request.GET, 'page'),
    }
    
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    try:
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
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    # --- UPDATED CATEGORY FILTERING ---
    # Current product-inte category subtle aayi match cheyyaan:
    category = single_product.category
    
    # Category subtle check (Parent or same category products)
    if category.parent:
        related_products = Product.objects.filter(
            Q(category=category) | Q(category__parent=category.parent), 
            is_available=True
        ).exclude(id=single_product.id).distinct()[:10]
    else:
        subcategories = category.children.all()
        if subcategories.exists():
            related_products = Product.objects.filter(
                Q(category=category) | Q(category__in=subcategories), 
                is_available=True
            ).exclude(id=single_product.id).distinct()[:10]
        else:
            related_products = Product.objects.filter(
                category=category, 
                is_available=True
            ).exclude(id=single_product.id)[:10]

    # Featured / Recommended Products
    recommended_products = Product.objects.filter(
        is_available=True
    ).exclude(id=single_product.id).order_by('-created_date')[:10]

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'related_products': related_products,
        'recommended_products': recommended_products,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):
    products = Product.objects.none()
    product_count = 0
    
    if 'keyword' in request.GET:
        keyword = request.GET['keyword'].strip()
        if keyword:
            age_filters, cleaned_keyword = _parse_age_search(keyword)
            if age_filters:
                query_params = {'search': '1'}
                query_params.update({key: value for key, value in age_filters.items() if value not in (None, '')})
                if cleaned_keyword:
                    query_params['inner_keyword'] = cleaned_keyword
                return redirect(f"{reverse('store')}?{urlencode(query_params)}")

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
        'sort_querystring': _querystring_without(request.GET, 'sort', 'page'),
        'page_querystring': _querystring_without(request.GET, 'page'),
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


@csrf_exempt
def get_purchase_items(request):
    """API endpoint to fetch purchase items for product creation form"""
    from warehousing.models import PurchaseItem
    
    try:
        # Fetch recent purchase items that haven't been created as products yet
        purchase_items = PurchaseItem.objects.select_related(
            'purchase', 'product'
        ).filter(
            purchase__status='Received'
        ).order_by('-purchase__ordered_at')[:50]
        
        data = []
        for item in purchase_items:
            data.append({
                'id': item.id,
                'purchase_number': item.purchase.purchase_number,
                'product_name': item.product.product_name,
                'product_code': item.product.product_code,
                'unit_cost': float(item.unit_cost),
                'quantity': item.quantity,
                'received_quantity': item.received_quantity,
            })
        
        return JsonResponse({'success': True, 'items': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
