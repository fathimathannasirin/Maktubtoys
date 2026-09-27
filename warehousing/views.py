from django.db.models import Q
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

from store.models import Product
from .models import PurchaseItem


def supplier_product_queryset(supplier_id=None, warehouse_id=None, search_term='', returnable=False):
    products = Product.objects.all()

    if returnable:
        purchase_items = PurchaseItem.objects.all()
        if supplier_id:
            purchase_items = purchase_items.filter(purchase__supplier_id=supplier_id)
        if warehouse_id:
            purchase_items = purchase_items.filter(purchase__warehouse_id=warehouse_id)
        products = products.filter(id__in=purchase_items.values_list('product_id', flat=True).distinct())
    elif supplier_id:
        products = products.filter(
            Q(supplier_id=supplier_id)
            | Q(warehouse__supplier_id=supplier_id)
            | Q(purchase_items__purchase__supplier_id=supplier_id)
        ).distinct()

    search_term = (search_term or '').strip()
    if search_term:
        products = products.filter(
            Q(product_name__icontains=search_term)
            | Q(product_code__icontains=search_term)
            | Q(sku__icontains=search_term)
            | Q(upc__icontains=search_term)
        )

    return products.order_by('product_name')


def serialize_lookup_product(product, supplier_id=None):
    last_cost = PurchaseItem.objects.filter(product=product)
    if supplier_id:
        last_cost = last_cost.filter(purchase__supplier_id=supplier_id)
    last_cost = last_cost.order_by('-id').values_list('unit_cost', flat=True).first()
    if last_cost is None:
        last_cost = product.cost_price or 0
    return {
        'id': product.id,
        'name': product.product_name,
        'code': product.product_code or '',
        'cost_price': float(last_cost or 0),
    }


@staff_member_required
def lookup_products(request):
    supplier_id = (request.GET.get('supplier_id') or '').strip()
    warehouse_id = (request.GET.get('warehouse_id') or '').strip()
    search_term = request.GET.get('q') or ''
    product_id = (request.GET.get('product_id') or '').strip()
    returnable = request.GET.get('returnable') == '1'

    if product_id:
        product = Product.objects.filter(pk=product_id).first()
        return JsonResponse({
            'products': [serialize_lookup_product(product, supplier_id or None)] if product else [],
        })

    if not supplier_id and not search_term:
        return JsonResponse({'products': [], 'message': 'Select a supplier, then type to search products.'})

    products = supplier_product_queryset(
        supplier_id=supplier_id or None,
        warehouse_id=warehouse_id or None,
        search_term=search_term,
        returnable=returnable,
    )[:40]

    data = [serialize_lookup_product(product, supplier_id or None) for product in products]
    return JsonResponse({'products': data})
