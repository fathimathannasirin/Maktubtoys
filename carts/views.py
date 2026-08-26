from django.shortcuts import render,redirect,get_object_or_404
from store.models import Product,Variation
from carts.models import Cart,CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal

# Create your views here.
def _cart_id(request):
    cart =  request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id, cart_item_id=None ):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    if product.stock <= 0:
        messages.error(request, 'Sorry, this product is out of stock!')
        return redirect('cart')
    # if the user is authenticated
    if current_user.is_authenticated:
        # Check total existing quantity of this product in user's cart
        existing_cart_items = CartItem.objects.filter(product=product, user=current_user)
        total_existing_qty = sum(i.quantity for i in existing_cart_items)
        if total_existing_qty + 1 > product.stock:
            messages.error(request, f'Cannot add more! Only {product.stock} items available in stock.')
            return redirect('cart')

        product_variation = []
        if request.method == 'POST':
            for key in request.POST:
                if key == 'csrfmiddlewaretoken': 
                    continue
                values = request.POST.getlist(key)
                for val in values:
                    try:
                        # This finds the exact variation selected
                        variation = Variation.objects.get(
                            product=product,
                            variation_category__iexact=key,
                            variation_value__iexact=val
                        )
                        product_variation.append(variation)
                    except:
                        pass

    

        is_cart_item_exits = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exits:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list =[]
            id =[]
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append (list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                index=ex_var_list.index(product_variation)
                item_id = id[index]
                item= CartItem.objects.get(product=product, id=item_id)
                if item.quantity + 1 > product.stock:
                    messages.error(request, f'Cannot add more! Only {product.stock} items available in stock.')
                    return redirect('cart')
                item.quantity += 1
                item.save()
            else: 
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)                              
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else :
            cart_item = CartItem.objects.create(
                product =product,
                quantity = 1,
                user = current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
    # id use is not authenticated
    else:
        product_variation=[]
        if request.method == 'POST':
            for key in request.POST:
                if key == 'csrfmiddlewaretoken': 
                    continue
                values = request.POST.getlist(key)
                for val in values:
                    try:
                        # This finds the exact variation selected
                        variation = Variation.objects.get(
                            product=product,
                            variation_category__iexact=key,
                            variation_value__iexact=val
                        )
                        product_variation.append(variation)
                    except:
                        pass

        # Get the cart
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        # Check total existing quantity of this product in unauthenticated cart
        existing_cart_items = CartItem.objects.filter(product=product, cart=cart)
        total_existing_qty = sum(i.quantity for i in existing_cart_items)
        if total_existing_qty + 1 > product.stock:
            messages.error(request, f'Cannot add more! Only {product.stock} items available in stock.')
            return redirect('cart')

        is_cart_item_exits = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exits:
            cart_item = CartItem.objects.filter(product=product, cart=cart)

            ex_var_list =[]
            id =[]
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append (list(existing_variation))
                id.append(item.id)
            print(ex_var_list)

            if product_variation in ex_var_list:
                index=ex_var_list.index(product_variation)
                item_id = id[index]
                item= CartItem.objects.get(product=product, id=item_id)
                if item.quantity + 1 > product.stock:
                    messages.error(request, f'Cannot add more! Only {product.stock} items available in stock.')
                    return redirect('cart')
                item.quantity += 1
                item.save()
            else: 
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)                              
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else :
            cart_item = CartItem.objects.create(
                product =product,
                quantity = 1,
                cart = cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
        


def remove_cart(request,product_id, cart_item_id):
    
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user,id=cart_item_id)
        else:
            cart= Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart,id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request,product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        if cart_items.exists():
            delivery_charge = Decimal('20.0')  # Flat Delivery Charge of 20 QAR
            grand_total = total + delivery_charge
    except ObjectDoesNotExist:
        pass 

    context= {
        'total' : total,
        'quantity': quantity,
        'cart_items':cart_items,
        'delivery_charge': delivery_charge if cart_items.exists() else 0,
        'grand_total': grand_total if cart_items.exists() else total,
    }
    return render(request, 'store/cart.html',context)

@login_required(login_url='login')
def checkout(request, total=0,quantity=0,cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        if cart_items.exists():
            delivery_charge = Decimal('20.0')  # Flat Delivery Charge of 20 QAR
            grand_total = total + delivery_charge

    except ObjectDoesNotExist:
        pass 

    context= {
        'total' : total,
        'quantity': quantity,
        'cart_items':cart_items,
        'delivery_charge': delivery_charge if cart_items.exists() else 0,
        'grand_total': grand_total if cart_items.exists() else total,
    }
    return render(request,'store/checkout.html',context)