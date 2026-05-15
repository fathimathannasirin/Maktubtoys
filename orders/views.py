from django.shortcuts import render, redirect
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, OrderProduct
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import datetime
from django.core.mail import EmailMessage, get_connection
from django.conf import settings

def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart is empty, redirect back to store
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    
    # Calculation (2% Tax)
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
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
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            
            # Set Cash on Delivery Defaults
            data.payment_method = 'COD'
            data.is_ordered = True 
            data.status = 'New'
            data.save() # Save here first to generate the record ID

            # Generate order number using the current date + unique ID
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d") 
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save() # Save again with the generated order number

            # 2. Move Cart Items to Order Product table
            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = data.id
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.product.price
                orderproduct.ordered = True
                orderproduct.save()

                # Transfer variations from CartItem to OrderProduct
                product_variation = item.variations.all()
                orderproduct.variations.set(product_variation)
                orderproduct.save()

                # 3. REDUCE THE QUANTITY OF THE SOLD PRODUCTS (STOCK)
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            # 4. CLEAR CART
            CartItem.objects.filter(user=request.user).delete()

            try:
                mail_subject = 'Thank you for your order!'
                tracking_url = request.build_absolute_uri(f'/orders/track_order/?order_number={order_number}')
                
                message = render_to_string('orders/order_received_email.html', {
                    'user': request.user,
                    'order': data,
                    'tracking_url': tracking_url,
                })
                
                to_email = data.email

                # Manually setup the connection using your existing settings variables
                connection = get_connection(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                )

                send_email = EmailMessage(
                    mail_subject, 
                    message, 
                    settings.EMAIL_HOST_USER, # From email
                    [to_email],
                    connection=connection # Explicitly use this connection
                )
                send_email.send()
                
            except Exception as e:
                print(f"Email error: {e}")
            # 6. REDIRECT TO SUCCESS PAGE
            return redirect(f'/orders/order_complete/?order_number={order_number}')
        else:
            # If form is invalid, stay on checkout and show errors
            context = {
                'form': form,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'store/checkout.html', context)

    return redirect('checkout')
        
def order_complete(request):
    order_number = request.GET.get('order_number')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

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
            order_products = OrderProduct.objects.filter(order_id=order.id)
            
            context = {
                'order': order,
                'order_products': order_products,
            }
            return render(request, 'orders/track_order.html', context)
        except Order.DoesNotExist:
            return render(request, 'orders/track_order.html', {'error': 'Order not found.'})
    
    return render(request, 'orders/track_order.html')