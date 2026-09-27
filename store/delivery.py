from datetime import time, timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.translation import gettext as _

OWN_WAREHOUSE_CODE = 'OWN'
OWN_DELIVERY_CHARGE = Decimal('20.00')
DELIVERY_CUTOFF_TIME = time(19, 0)
DEFAULT_SUPPLIER_DELIVERY_DAYS = 2


def is_own_warehouse(warehouse):
    return bool(warehouse) and warehouse.code == OWN_WAREHOUSE_CODE


def is_own_warehouse_product(product):
    if is_own_warehouse(getattr(product, 'warehouse', None)):
        return True
    prefetched = getattr(product, '_prefetched_objects_cache', {}).get('warehouse_stocks')
    if prefetched is not None:
        return any(
            stock.quantity > 0 and is_own_warehouse(stock.warehouse)
            for stock in prefetched
        )
    from warehousing.models import ProductWarehouseStock
    return ProductWarehouseStock.objects.filter(
        product=product,
        warehouse__code=OWN_WAREHOUSE_CODE,
        quantity__gt=0,
    ).exists()


def cart_delivery_charge(cart_items):
    if not cart_items:
        return Decimal('0')
    for item in cart_items:
        if is_own_warehouse_product(item.product):
            return OWN_DELIVERY_CHARGE
    return Decimal('0')


def get_delivery_estimate(product, ordered_at=None):
    now = timezone.localtime(ordered_at or timezone.now())
    warehouse = getattr(product, 'warehouse', None)
    is_own = is_own_warehouse(warehouse)
    is_before_cutoff = now.time() <= DELIVERY_CUTOFF_TIME

    if is_own:
        eta_date = warehouse.get_delivery_date(now)
        if is_before_cutoff:
            message = _('Same-day delivery if you order before 7:00 PM.')
        else:
            message = _('Ordered after 7:00 PM. Delivery is tomorrow.')
        return {
            'is_own': True,
            'is_free': False,
            'charge_label': _('Delivery 20 QAR'),
            'delivery_days': 0,
            'eta_date': eta_date,
            'message': message,
        }

    delivery_days = warehouse.delivery_days if warehouse else DEFAULT_SUPPLIER_DELIVERY_DAYS
    if warehouse:
        eta_date = warehouse.get_delivery_date(now)
    else:
        eta_date = now.date() + timedelta(days=delivery_days)

    if delivery_days == 1:
        message = _('Free delivery. Expected tomorrow.')
    else:
        message = _('Free delivery. Expected in %(days)s day(s).') % {'days': delivery_days}

    return {
        'is_own': False,
        'is_free': True,
        'charge_label': _('Free delivery'),
        'delivery_days': delivery_days,
        'eta_date': eta_date,
        'message': message,
    }


def order_delivery_type(warehouses, ordered_at=None):
    now = timezone.localtime(ordered_at or timezone.now())
    warehouses = [warehouse for warehouse in warehouses if warehouse]
    has_own = any(is_own_warehouse(warehouse) for warehouse in warehouses)
    others = [warehouse for warehouse in warehouses if not is_own_warehouse(warehouse)]

    if has_own and not others:
        if now.time() <= DELIVERY_CUTOFF_TIME:
            return 'Same-Day Delivery'
        return 'Next-Day Delivery'
    if others and not has_own:
        days = max(warehouse.delivery_days for warehouse in others)
        return f'{days}-Day Delivery'
    if has_own and others:
        return 'Split Delivery'
    return f'{DEFAULT_SUPPLIER_DELIVERY_DAYS}-Day Delivery'
