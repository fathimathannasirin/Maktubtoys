from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render
from django.template.response import TemplateResponse
from Accounts.models import Account
from home.models import SectionOfferBanner
from orders.models import Order
from store.models import Category, Product, ReviewRating


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