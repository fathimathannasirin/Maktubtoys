from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import translate_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import check_for_language, get_language_from_path
from Accounts.models import Account
from home.models import SectionOfferBanner
from orders.models import Order
from store.models import Category, Product, ReviewRating


LANGUAGE_QUERY_PARAMETER = 'language'


def _strip_language_prefix(url):
    """Remove /<lang> from a URL so it can be resolved in the default language."""
    parsed = urlsplit(url)
    path = parsed.path or '/'
    lang = get_language_from_path(path)
    if lang:
        path = path[len(f'/{lang}'):] or '/'
        if not path.startswith('/'):
            path = '/' + path
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


def set_language(request):
    """
    Switch language and redirect.

    Django's built-in view cannot translate /ar/... back to unprefixed English
    URLs when prefix_default_language=False, so the user stays on Arabic.
    """
    next_url = request.POST.get('next', request.GET.get('next'))
    if (
        next_url or request.accepts('text/html')
    ) and not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = request.META.get('HTTP_REFERER')
        if not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = '/'

    response = HttpResponseRedirect(next_url) if next_url else HttpResponse(status=204)
    if request.method == 'POST':
        lang_code = request.POST.get(LANGUAGE_QUERY_PARAMETER)
        if lang_code and check_for_language(lang_code):
            if next_url:
                next_url = _strip_language_prefix(next_url)
                next_url = translate_url(next_url, lang_code)
                response = HttpResponseRedirect(next_url)
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                lang_code,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
    return response


def home(request):
    products = Product.objects.filter(is_available=True).order_by('created_date')
    categories = Category.objects.all().select_related('parent')
    parent_categories = [category for category in categories if category.parent_id is None]

    section_offer_banners = list(
        SectionOfferBanner.objects.filter(is_active=True).select_related('category').order_by('order', 'created_at')
    )
    specific_banner_map = {
        banner.category_id: banner
        for banner in section_offer_banners
        if banner.category_id
    }
    global_banners = [banner for banner in section_offer_banners if banner.category_id is None]

    for index, parent_category in enumerate(parent_categories):
        selected_banner = specific_banner_map.get(parent_category.id)
        if selected_banner is None and global_banners:
            selected_banner = global_banners[index % len(global_banners)]
        parent_category.section_offer_banner = selected_banner

    reviews = ReviewRating.objects.filter(product_id__in=products, status=True).select_related('user')

    context = {
        'products': products,
        'categories': categories,  # Keeps your original variable intact
        'links': categories,       # Added so the {% for category in links %} sliders in index.html work!
        'parent_categories': parent_categories,
        'reviews': reviews,        # Safe from UnboundLocalError and optimized for performance
    }
    return render(request, 'index.html', context)


@staff_member_required
def admin_stats_dashboard(request):
    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(is_ordered=True)
    total_sales = paid_orders.aggregate(total=Sum('order_total'))['total'] or 0
    completed_orders = paid_orders.filter(status='Completed').count()
    pending_orders = paid_orders.exclude(status='Completed').count()
    total_customers = Account.objects.filter(is_staff=False, is_admin=False).count()
    active_products = Product.objects.filter(is_available=True).count()
    out_of_stock = Product.objects.filter(stock__lte=0).count()
    recent_orders = Order.objects.order_by('-created_at')[:8]

    context = {
        'title': 'Built-in Admin Stats Dashboard',
        'total_orders': total_orders,
        'total_sales': total_sales,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'total_customers': total_customers,
        'active_products': active_products,
        'out_of_stock': out_of_stock,
        'recent_orders': recent_orders,
    }
    return TemplateResponse(request, 'admin/stats_dashboard.html', context)