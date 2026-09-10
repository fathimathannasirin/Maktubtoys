from django.shortcuts import render, redirect, get_object_or_404
from collections import defaultdict
from pathlib import Path
from threading import Thread
from decimal import Decimal

from carts.models import CartItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import ExpressionWrapper, F, FloatField, Sum
from .forms import OrderForm, ReturnRequestForm
from .models import Order, OrderProduct, Parcel, ReturnRequest, ReturnRequestImage
from store.models import Product
from warehousing.models import ProductWarehouseStock
from django.template.loader import render_to_string
import datetime
from django.core.mail import EmailMessage, get_connection
from django.conf import settings


ALLOWED_RETURN_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


def _notify_suppliers_for_order(request, order, supplier_notifications):
    if not supplier_notifications:
        return

    connection = get_connection(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
    )

    for supplier, items in supplier_notifications.items():
        if not supplier.email:
            continue

        try:
            mail_subject = f"New order for your products: {order.order_number}"
            message = render_to_string('orders/supplier_order_notification_email.html', {
                'order': order,
                'supplier': supplier,
                'items': items,
                'admin_order_url': request.build_absolute_uri(f"/securelogin/orders/order/{order.id}/change/"),
            })
            send_email = EmailMessage(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [supplier.email],
                connection=connection,
            )
            send_email.send()
        except Exception as supplier_email_error:
            print(f"Supplier email error ({supplier.name}): {supplier_email_error}")


def _send_order_notifications_async(request, order, supplier_notifications, tracking_url):
    try:
        connection = get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
        )

        # 1. Send Customer Email
        mail_subject = 'Thank you for your order!'
        customer_message = render_to_string('orders/order_received_email.html', {
            'user': request.user,
            'order': order,
            'tracking_url': tracking_url,
        })
        send_email_customer = EmailMessage(
            mail_subject,
            customer_message,
            settings.EMAIL_HOST_USER,
            [order.email],
            connection=connection,
        )
        send_email_customer.send()

        # 2. Send Admin Notification (Using Supplier/Admin Format)
        if settings.EMAIL_HOST_USER:
            order_items = OrderProduct.objects.filter(order=order).select_related('product', 'warehouse')
            admin_subject = f"New order placed: {order.order_number}"
            admin_message = render_to_string('orders/supplier_order_notification_email.html', {
                'order': order,
                'items': [
                    {
                        'product_name': item.product.product_name,
                        'product_code': getattr(item.product, 'product_code', 'N/A'),
                        'quantity': item.quantity,
                        'warehouse': item.warehouse.name if item.warehouse else 'N/A',
                    }
                    for item in order_items
                ],
                'admin_order_url': request.build_absolute_uri(f"/securelogin/orders/order/{order.id}/change/"),
            })
            send_email_admin = EmailMessage(
                admin_subject,
                admin_message,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                connection=connection,
            )
            send_email_admin.send()

    except Exception as email_error:
        print(f"Email error: {email_error}")

    _notify_suppliers_for_order(request, order, supplier_notifications)

def _schedule_order_notifications(request, order, supplier_notifications, tracking_url):
    transaction.on_commit(
        lambda: Thread(
            target=_send_order_notifications_async,
            args=(request, order, supplier_notifications, tracking_url),
            daemon=True,
        ).start()
    )


def _warehouse_allocations(product, quantity):
    inventory_rows = list(
        ProductWarehouseStock.objects.filter(product=product, quantity__gt=0)
        .select_related('warehouse')
        .order_by('warehouse_id')
    )
    inventory_rows.sort(key=lambda row: (row.warehouse.code != 'OWN', row.warehouse_id))

    allocations = []
    remaining = quantity
    for inventory in inventory_rows:
        allocated = min(remaining, inventory.quantity)
        if allocated:
            allocations.append((inventory.warehouse, allocated))
            remaining -= allocated
        if not remaining:
            break

    if remaining and product.warehouse:
        allocations.append((product.warehouse, remaining))
        remaining = 0

    if remaining:
        raise ValueError(f'Insufficient warehouse inventory for {product.product_name}.')

    return allocations

def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = list(
        CartItem.objects.filter(user=current_user)
        .select_related('product__supplier', 'product__warehouse')
        .prefetch_related('variations')
    )

    # If the cart is empty, redirect back to store
    if not cart_items:
        return redirect('store')
    now = timezone.localtime()
    cutoff_time = datetime.time(19, 0, 0) # 7:00 PM
    delivery_type = "Same-Day Delivery"
    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(
                request, 
                f"Sorry, {item.product.product_name} has only {item.product.stock} items left in stock. Please adjust your cart quantity."
            )
            return redirect('cart')
        try:
            supplying_warehouses = _warehouse_allocations(item.product, item.quantity)
        except ValueError:
            messages.error(
                request,
                f"Sorry, {item.product.product_name} is not available in the required warehouse quantity.",
            )
            return redirect('cart')
        if any(warehouse.code != 'OWN' for warehouse, _ in supplying_warehouses) or now.time() > cutoff_time:
            delivery_type = "2-Day Delivery"
            break

    grand_total = 0
    delivery_charge = Decimal('20.0')
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    
    
    grand_total = total + delivery_charge

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            supplier_notifications = defaultdict(list)
            order_products = []
            product_updates = {}

            with transaction.atomic():
                # 1. Store all the billing information inside Order table
                data = Order()
                data.user = current_user
                data.first_name = form.cleaned_data['first_name']
                data.last_name = form.cleaned_data['last_name']
                data.phone = form.cleaned_data['phone']
                data.email = form.cleaned_data['email']
                data.address_line_1 = form.cleaned_data['address_line_1']
                data.address_line_2 = form.cleaned_data['address_line_2']
                data.street_number = form.cleaned_data['street_number']
                data.building_number = form.cleaned_data['building_number']
                data.zone_number = form.cleaned_data['zone_number']
                data.order_note = form.cleaned_data['order_note']
                data.order_total = grand_total
                data.delivery_charge = delivery_charge
                data.ip = request.META.get('REMOTE_ADDR')

                # Set Cash on Delivery Defaults
                data.payment_method = 'COD'
                data.is_ordered = True
                data.status = 'Processing'
                data.delivery_type = delivery_type
                data.save()

                # Generate order number using the current date + unique ID
                current_date = timezone.now().strftime('%Y%m%d')
                order_number = current_date + str(data.id)
                data.order_number = order_number
                data.save(update_fields=['order_number'])

                # 2. Allocate each cart line from actual warehouse inventory.
                warehouse_grouped_items = defaultdict(list)
                inventory_allocations = []
                for item in cart_items:
                    try:
                        allocations = _warehouse_allocations(item.product, item.quantity)
                    except ValueError as error:
                        messages.error(request, str(error))
                        return redirect('cart')
                    for warehouse, allocated_quantity in allocations:
                        warehouse_grouped_items[warehouse].append((item, allocated_quantity))
                        inventory_allocations.append((item.product_id, warehouse.id, allocated_quantity))

                order_products = []
                cart_item_by_product = []

                # Create one parcel per supplying warehouse.
                parcels_by_warehouse = {}
                for wh, items in warehouse_grouped_items.items():
                    parcels_by_warehouse[wh] = Parcel.objects.create(
                        order=data,
                        warehouse=wh,
                        delivery_date=wh.get_delivery_date(data.created_at),
                    )

                # 3. Move allocated quantities to OrderProduct rows.
                for item in cart_items:
                    product = item.product
                    for warehouse, warehouse_items in warehouse_grouped_items.items():
                        for grouped_item, allocated_quantity in warehouse_items:
                            if grouped_item.id != item.id:
                                continue
                            order_products.append(
                                OrderProduct(
                                    order_id=data.id,
                                    user_id=request.user.id,
                                    product_id=item.product_id,
                                    supplier=product.supplier,
                                    warehouse=warehouse,
                                    parcel=parcels_by_warehouse[warehouse],
                                    quantity=allocated_quantity,
                                    product_price=product.price,
                                    ordered=True,
                                )
                            )
                            cart_item_by_product.append(item)

                            if product.supplier and product.supplier.email:
                                supplier_notifications[product.supplier].append({
                                    'product_name': product.product_name,
                                    'product_code': product.product_code,
                                    'quantity': allocated_quantity,
                                    'warehouse': warehouse.name,
                                })

                    # Reduce total product stock once per cart line.
                    product_to_update = product_updates.setdefault(product.id, product)
                    product_to_update.stock = max(0, product_to_update.stock - item.quantity)
                    product_to_update.is_available = product_to_update.stock > 0

                for product_id, warehouse_id, allocated_quantity in inventory_allocations:
                    inventory = ProductWarehouseStock.objects.select_for_update().get(
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                    )
                    inventory.quantity = max(0, inventory.quantity - allocated_quantity)
                    inventory.save(update_fields=['quantity', 'updated_at'])

                OrderProduct.objects.bulk_create(order_products)

                for orderproduct, item in zip(order_products, cart_item_by_product):
                    orderproduct.variations.set(item.variations.all())

                Product.objects.bulk_update(product_updates.values(), ['stock', 'is_available'])

                # 4. Clear cart
                CartItem.objects.filter(id__in=[item.id for item in cart_items]).delete()

                tracking_url = request.build_absolute_uri(f'/orders/track_order/?order_number={order_number}')
                _schedule_order_notifications(request, data, supplier_notifications, tracking_url)

            # 6. REDIRECT TO SUCCESS PAGE
            return redirect(f'/orders/order_complete/?order_number={order_number}')
        else:
            # If form is invalid, stay on checkout and show errors
            context = {
                'form': form,
                'cart_items': cart_items,
                'total': total,
                'delivery_charge': delivery_charge,
                'grand_total': grand_total,
            }
            return render(request, 'store/checkout.html', context)

    return redirect('checkout')
        
def order_complete(request):
    order_number = request.GET.get('order_number')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id).select_related('supplier', 'warehouse', 'product')
        subtotal = ordered_products.aggregate(
            subtotal=Sum(
                ExpressionWrapper(
                    F('product_price') * F('quantity'),
                    output_field=FloatField(),
                )
            )
        )['subtotal'] or 0

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Order.DoesNotExist):
        return redirect('home')
    
def track_order(request):
    order_number = request.GET.get('order_number')
    if order_number:
        try:
            # Retrieve order and products
            order = Order.objects.get(order_number=order_number)
            order_products = OrderProduct.objects.filter(order_id=order.id).select_related('supplier', 'warehouse', 'product')
            
            context = {
                'order': order,
                'order_products': order_products,
            }
            return render(request, 'orders/track_order.html', context)
        except Order.DoesNotExist:
            return render(request, 'orders/track_order.html', {'error': 'Order not found.'})
    
    return render(request, 'orders/track_order.html')


def _return_eligibility_message(order):
    if order.status in order.BLOCKED_RETURN_STATUSES:
        return False, 'This order is not eligible for return requests.'
    if order.status not in order.DELIVERED_STATUSES:
        return False, 'Returns are available only after the order is delivered.'
    if order.is_return_window_expired:
        return False, 'The return period for this order has expired.'
    return True, ''


@login_required(login_url='login')
def return_request(request, order_id):
    order = get_object_or_404(Order, pk=order_id, is_ordered=True)

    if order.user_id != request.user.id and not request.user.is_staff:
        messages.error(request, 'You are not authorized to request a return for this order.')
        return redirect('my_orders')

    existing_request = ReturnRequest.objects.filter(order=order).first()
    is_eligible, eligibility_message = _return_eligibility_message(order)

    if request.method == 'POST':
        if existing_request:
            messages.warning(request, 'A return request already exists for this order.')
            return redirect('order_detail', order_id=order.order_number)

        if not is_eligible:
            messages.error(request, eligibility_message)
            return redirect('order_detail', order_id=order.order_number)

        form = ReturnRequestForm(request.POST)
        images = request.FILES.getlist('images')

        if len(images) > 5:
            form.add_error(None, 'You can upload up to 5 images only.')

        for image in images:
            extension = Path(image.name).suffix.lower()
            if extension not in ALLOWED_RETURN_IMAGE_EXTENSIONS:
                form.add_error(None, 'Only JPG, PNG, and WEBP images are allowed.')
                break

        if form.is_valid():
            return_request_obj = ReturnRequest.objects.create(
                order=order,
                customer=request.user,
                reason=form.cleaned_data['reason'],
                description=form.cleaned_data['description'],
                return_shipping_acknowledged=form.cleaned_data['return_shipping_acknowledged'],
                policy_terms_accepted=form.cleaned_data['policy_terms_accepted'],
            )

            for image in images:
                ReturnRequestImage.objects.create(return_request=return_request_obj, image=image)

            order.status = 'Return Requested'
            order.save(update_fields=['status', 'updated_at'])

            messages.success(
                request,
                'Your return request has been submitted successfully. Our team will review your request and contact you soon.'
            )
            return redirect('order_detail', order_id=order.order_number)
    else:
        form = ReturnRequestForm()

    context = {
        'order': order,
        'form': form,
        'existing_request': existing_request,
        'is_eligible': is_eligible,
        'eligibility_message': eligibility_message,
        'policy_notice_points': [
            'Returns are accepted only within 7 days of delivery.',
            'Products must be returned in their original packaging.',
            'Customers are responsible for return shipping costs.',
            'MAKTUB Toys is not responsible for transit/shipping damage.',
            'Refunds are processed only after product inspection.',
            'Refunds may take up to 7 working days after approval.',
        ],
        'return_window_days': order.RETURN_REQUEST_DAYS,
        'server_now': timezone.now(),
    }
    return render(request, 'orders/return_request.html', context)


def print_single_parcel(request, parcel_id):
    parcel = get_object_or_404(Parcel, pk=parcel_id)
    order_items = OrderProduct.objects.filter(parcel=parcel)

    context = {
        'order': parcel.order,
        'parcel': parcel,
        'order_detail': order_items,
        'is_single_parcel': True,
    }
    return render(request, 'orders/admin_invoice_pdf.html', context)

# 2. Full Multi-Parcel Order Invoice View
def print_full_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    parcels = Parcel.objects.filter(order=order).prefetch_related('items__product')

    context = {
        'order': order,
        'parcels': parcels,
        'is_single_parcel': False,
    }
    return render(request, 'orders/admin_invoice_pdf.html', context)